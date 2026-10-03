"""Bounded full-turn admission; one session is serialized across API workers."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import psycopg
from fastapi import HTTPException

from aclara.ops.store import Scope, Store


@dataclass
class SessionQueue:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    users: int = 0


class SessionTurns:
    def __init__(self, store: Store, *, parallel: int = 5, pending: int = 64):
        self.store = store
        self.capacity = asyncio.Semaphore(parallel)
        self.limit = pending
        self.waiting = 0
        self.sessions: dict[Scope, SessionQueue] = {}

    @asynccontextmanager
    async def hold(self, scope: Scope) -> AsyncIterator[None]:
        # Event-loop-owned counters: no await between admission and increment.
        if self.waiting >= self.limit:
            raise HTTPException(503, "Turn capacity reached; retry after this turn completes")
        self.waiting += 1
        queue = self.sessions.setdefault(scope, SessionQueue())
        queue.users += 1
        try:
            async with queue.lock, self.capacity:
                if self.store.pool is None:
                    yield
                else:
                    # Empty conninfo is valid: Azure supplies libpq's PG* variables.
                    if self.store.dsn is None:
                        raise PermissionError("Session serialization requires runtime storage")
                    # A dedicated autocommit connection holds only the session
                    # advisory lock, never a customer transaction or pooled slot.
                    # Closing on cancellation/process death releases the lock.
                    connection = await psycopg.AsyncConnection.connect(
                        self.store.dsn, autocommit=True, connect_timeout=5
                    )
                    try:
                        privileged = await (
                            await connection.execute(
                                "SELECT rolsuper OR rolbypassrls OR pg_has_role(current_user,'aclara_owner','MEMBER') FROM pg_roles WHERE rolname=current_user"
                            )
                        ).fetchone()
                        if not privileged or privileged[0]:
                            raise PermissionError("Turn locks require the non-owner runtime role")
                        try:
                            await asyncio.wait_for(
                                connection.execute(
                                    "SELECT pg_advisory_lock(hashtextextended(%s,0))",
                                    (
                                        json.dumps(
                                            [
                                                "chat-turn",
                                                scope.customer_id,
                                                scope.run_id,
                                                scope.sid,
                                            ]
                                        ),
                                    ),
                                ),
                                timeout=120,
                            )
                        except TimeoutError as exc:
                            raise HTTPException(503, "Session turn wait timed out") from exc
                        yield
                    finally:
                        # Autocommit has no transaction to roll back; close is
                        # local and releases the advisory lock even on cancel.
                        await connection.close()
        finally:
            queue.users -= 1
            self.waiting -= 1
            if queue.users == 0:
                del self.sessions[scope]
