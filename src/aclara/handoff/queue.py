"""Masked realm queue; operational session and bank/customer RLS stay unchanged."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from psycopg.pq import TransactionStatus
from psycopg.types.json import Jsonb

from aclara.ops.store import Scope, Store

ACTIVE: ContextVar[tuple[Store, str, bool] | None] = ContextVar("handoff_queue", default=None)


def access(store: Store, realm: str) -> bool:
    current = ACTIVE.get()
    if current is None or current[:2] != (store, realm):
        raise PermissionError("Explicit matching queue context required")
    return current[2]


@contextmanager
def context(store: Store, realm: str, *, staff: bool) -> Iterator[None]:
    unit = store._unit()
    if not realm or ACTIVE.get() is not None:
        raise PermissionError("Queue realm required")
    if unit.connection:
        for key, value in (
            ("app.handoff_realm", realm),
            ("app.handoff_staff", "yes" if staff else "no"),
        ):
            unit.connection.execute("SELECT set_config(%s,%s,true)", (key, value))
        unit.connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("handoff:" + realm,)
        )
    token = ACTIVE.set((store, realm, staff))
    try:
        yield
    finally:
        ACTIVE.reset(token)
        if unit.connection and unit.connection.info.transaction_status != TransactionStatus.INERROR:
            unit.connection.execute("SELECT set_config('app.handoff_realm','',true)")
            unit.connection.execute("SELECT set_config('app.handoff_staff','no',true)")


def read(store: Store, realm: str, key: str | None = None) -> list[dict[str, Any]]:
    unit = store._unit()
    staff = access(store, realm)
    if unit.connection:
        rows = unit.connection.execute(
            "SELECT payload,status,claimed_by,version FROM ops.realm_handoffs "
            "WHERE (%s::text IS NULL OR id=%s) ORDER BY id",
            (key, key),
        ).fetchall()
        return [
            payload | dict(status=status, claimed_by=by, version=version)
            for payload, status, by, version in rows
        ]
    scope = Scope("realm-queue", realm, "queue")
    return [
        dict(value["payload"])
        for (stored, table, ident), value in store.memory.items()
        if stored == scope
        and table == "realm_handoffs"
        and (key is None or ident == key)
        and (staff or value["owner"] == unit.scope.customer_id)
    ]


def publish(store: Store, realm: str, packet: dict[str, Any]) -> None:
    unit = store._unit()
    if access(store, realm):
        raise PermissionError("Only a customer can publish a packet")
    key = packet["handoff_id"]
    if unit.connection:
        unit.connection.execute("SELECT ops.publish_handoff_queue(%s)", (Jsonb(packet),))
    else:
        storage_key = (Scope("realm-queue", realm, "queue"), "realm_handoffs", key)
        previous = store.memory.get(storage_key)
        if previous is None:
            store.memory[storage_key] = dict(owner=unit.scope.customer_id, payload=dict(packet))
        elif previous["owner"] != unit.scope.customer_id:
            raise PermissionError("Only the source customer can refresh a packet")
        elif {
            k: v
            for k, v in previous["payload"].items()
            if k not in {"status", "claimed_by", "version"}
        } != {k: v for k, v in packet.items() if k not in {"status", "claimed_by", "version"}}:
            stored = previous["payload"]
            store.memory[storage_key] = previous | dict(
                payload=packet
                | dict(
                    status=stored["status"],
                    claimed_by=stored["claimed_by"],
                    version=stored["version"] + 1,
                )
            )
    store.audit(dict(action="publish_handoff_queue", handoff_id=key))


def claim(store: Store, realm: str, key: str, by: str, version: int) -> None:
    unit = store._unit()
    if not access(store, realm):
        raise PermissionError("Staff queue context required")
    if unit.connection:
        changed = unit.connection.execute(
            "UPDATE ops.realm_handoffs SET status='claimed',claimed_by=%s,version=version+1 "
            "WHERE id=%s AND status='waiting' AND version=%s RETURNING id",
            (by, key, version),
        ).fetchone()
        if not changed:
            raise ValueError("Handoff version changed")
    else:
        stored = store.memory[(Scope("realm-queue", realm, "queue"), "realm_handoffs", key)]
        record = stored["payload"]
        if record["status"] != "waiting" or record["version"] != version:
            raise ValueError("Handoff version changed")
        store.memory[(Scope("realm-queue", realm, "queue"), "realm_handoffs", key)] = stored | dict(
            payload=record | dict(status="claimed", claimed_by=by, version=version + 1)
        )
    store.audit(dict(action="claim_handoff_queue", handoff_id=key, claimed_by=by))
