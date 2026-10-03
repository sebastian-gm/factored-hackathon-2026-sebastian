"""Full-turn ordering across workers and cleanup, authored local storage only."""

import asyncio
import os
from dataclasses import replace
from threading import Event
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from psycopg.conninfo import conninfo_to_dict
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger

from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.ops.store import Scope, Store
from aclara.ops.turns import SessionTurns


@pytest.mark.parametrize("backend", ["memory", "dsn", "environment"])
def test_same_session_orders_full_turns_even_across_postgres_workers(backend, monkeypatch):
    postgres = backend != "memory"
    dsn = os.getenv("TEST_OPS_DSN") if postgres else None
    if postgres and not dsn:
        pytest.skip("Disposable local Postgres required")
    if backend == "environment":
        # Azure's Store("") resolves its connection from libpq's PG* environment.
        # Use this disposable test DB, never the shell's inherited database.
        options = conninfo_to_dict(dsn)
        for name in list(os.environ):
            if name.startswith("PG"):
                monkeypatch.delenv(name)
        for key, name in {
            "host": "PGHOST",
            "port": "PGPORT",
            "user": "PGUSER",
            "password": "PGPASSWORD",
            "dbname": "PGDATABASE",
            "sslmode": "PGSSLMODE",
            "sslrootcert": "PGSSLROOTCERT",
        }.items():
            if key in options:
                monkeypatch.setenv(name, options[key])
        dsn = ""

    async def check():
        store = Store(dsn)
        other_store = Store(dsn) if postgres else store
        customer = "fixture-turn-" + uuid4().hex
        settings = replace(_settings(), demo_customer_id=customer)
        repository = TransactionRepository(
            tuple(replace(r, customer_id=customer) for r in ledger()._rows)
        )
        app = create_app(settings, repository, Runtime(system="P"), store=store)
        other = (
            create_app(settings, repository, Runtime(system="P"), store=other_store)
            if postgres
            else app
        )
        entered, release, second_entered = Event(), Event(), Event()
        first_understand, next_understand = app.state.ai.understand, other.state.ai.understand
        count = 0

        def first(*args, **kwargs):
            nonlocal count
            count += 1
            if count == 1:
                entered.set()
                assert release.wait(5)
            else:
                second_entered.set()
            return first_understand(*args, **kwargs)

        def second(*args, **kwargs):
            second_entered.set()
            return next_understand(*args, **kwargs)

        app.state.ai.understand = first
        if postgres:
            other.state.ai.understand = second
        try:
            async with (
                AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api,
                AsyncClient(transport=ASGITransport(app=other), base_url="http://test") as next_api,
            ):
                token = await _sign_in(api)
                headers = {"Authorization": "Bearer " + token}
                cid = (await api.post("/chat/sessions", headers=headers)).json()["conversation_id"]
                path = f"/chat/sessions/{cid}/messages"
                body = {"message": "¿Qué es el cargo de Taller Prisma?"}
                pending = asyncio.create_task(api.post(path, headers=headers, json=body))
                try:
                    assert await asyncio.to_thread(entered.wait, 2)
                    following = asyncio.create_task(next_api.post(path, headers=headers, json=body))
                    await asyncio.sleep(0.05)
                    assert not second_entered.is_set() and not following.done()
                finally:
                    release.set()
                results = await asyncio.gather(pending, following)
                assert all(r.status_code == 200 for r in results)
                assert second_entered.is_set()
                p = app.state.sessions[token]
                with store.transaction(Scope(p.customer_id, p.run_id, p.session_id)):
                    assert len(app.state.executions) == 2
                assert not app.state.session_turns.sessions
        finally:
            store.close()
            if other_store is not store:
                other_store.close()

    asyncio.run(check())


def test_cancelled_waiter_releases_admission_and_session_entries():
    async def check():
        guard = SessionTurns(Store(), parallel=1, pending=2)
        scope = Scope("authored", "run", "sid")
        entered, release = asyncio.Event(), asyncio.Event()

        async def first():
            async with guard.hold(scope):
                entered.set()
                await release.wait()

        async def queued():
            async with guard.hold(scope):
                raise AssertionError("Cancelled waiter acquired the session")

        one = asyncio.create_task(first())
        await entered.wait()
        two = asyncio.create_task(queued())
        await asyncio.sleep(0)
        two.cancel()
        with pytest.raises(asyncio.CancelledError):
            await two
        release.set()
        await one
        assert guard.waiting == 0 and not guard.sessions

    asyncio.run(check())


def test_postgres_cancel_releases_both_waiting_and_held_advisory_locks():
    dsn = os.getenv("TEST_OPS_DSN")
    if not dsn:
        pytest.skip("Disposable local Postgres required")

    async def check():
        store = Store(dsn)
        first, second = SessionTurns(store), SessionTurns(store)
        scope = Scope("fixture-cancel", uuid4().hex, "sid")
        entered = asyncio.Event()

        async def hold(guard):
            async with guard.hold(scope):
                entered.set()
                await asyncio.Event().wait()

        try:
            owner = asyncio.create_task(hold(first))
            await asyncio.wait_for(entered.wait(), 2)
            entered.clear()
            waiter = asyncio.create_task(hold(second))
            await asyncio.sleep(0.05)
            assert not entered.is_set()
            waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(waiter, 2)
            owner.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(owner, 2)
            async with asyncio.timeout(2), second.hold(scope):
                pass
            assert first.waiting == second.waiting == 0
            assert not first.sessions and not second.sessions
        finally:
            store.close()

    asyncio.run(check())
