"""Authored mock concurrency checks; no organizer inputs or provider calls."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from threading import Event
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.ops.store import Scope, Store


@pytest.mark.parametrize("postgres", [False, True])
def test_five_sessions_release_storage_during_nlu(postgres: bool) -> None:
    import os

    dsn = os.getenv("TEST_OPS_DSN") if postgres else None
    if postgres and not dsn:
        pytest.skip("Disposable local Postgres required")

    async def check() -> None:
        store = Store(dsn)
        customer_id = "fixture-concurrent-" + uuid4().hex
        repository = TransactionRepository(
            tuple(replace(row, customer_id=customer_id) for row in ledger()._rows)
        )
        app = create_app(
            replace(_settings(), demo_customer_id=customer_id),
            repository,
            Runtime(system="P"),
            store=store,
        )
        entered, release = Event(), Event()
        original = app.state.ai.understand
        calls = []

        def understand(*args, **kwargs):
            assert store.current.get() is None
            calls.append(args[0])
            entered.set()
            assert release.wait(5), "Test did not release inference"
            return original(*args, **kwargs)

        app.state.ai.understand = understand
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers, ids = [], []
            for _ in range(5):
                header = {"Authorization": f"Bearer {await _sign_in(client)}"}
                headers.append(header)
                ids.append(
                    (await client.post("/chat/sessions", headers=header)).json()["conversation_id"]
                )
            pending = [
                asyncio.create_task(
                    client.post(
                        f"/chat/sessions/{cid}/messages",
                        headers=header,
                        json={"message": "¿Qué es el cargo de Taller Prisma?"},
                    )
                )
                for cid, header in zip(ids, headers, strict=True)
            ]
            try:
                assert await asyncio.to_thread(entered.wait, 2)
                # Other authenticated reads are responsive while the provider waits.
                for header in headers:
                    for path in ("/healthz", "/me", "/transactions"):
                        assert (
                            await asyncio.wait_for(client.get(path, headers=header), 1)
                        ).status_code == 200
                # A different request's trace must not contaminate the suspended turn.
                with app.state.runtime.turn():
                    app.state.runtime.record("unrelated_request")
            finally:
                release.set()
            results = await asyncio.wait_for(asyncio.gather(*pending), 15)
            assert all(r.status_code == 200 and r.json()["outcome"] == "explained" for r in results)
            assert len(calls) == 5
            for header, cid in zip(headers, ids, strict=True):
                token = header["Authorization"].removeprefix("Bearer ")
                principal = app.state.sessions[token]
                with store.transaction(
                    Scope(principal.customer_id, principal.run_id, principal.session_id)
                ):
                    events = [
                        e
                        for record in app.state.executions.values()
                        if record.get("conversation_id") == cid
                        for e in record["events"]
                    ]
                assert sum(e["event"] == "nlu" for e in events) == 1
                assert not any(e["event"] == "unrelated_request" for e in events)
        if store.pool:
            store.pool.close()

    asyncio.run(check())


def test_policy_reads_case_created_by_another_login_during_inference() -> None:
    async def check() -> None:
        store = Store()
        app = create_app(_settings(), ledger(), Runtime(system="P"), store=store)
        other = create_app(_settings(), ledger(), Runtime(system="B1"), store=store)
        entered, release = Event(), Event()
        original = app.state.ai.understand

        def understand(*args, **kwargs):
            entered.set()
            assert release.wait(5)
            return original(*args, **kwargs)

        app.state.ai.understand = understand
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            cid = (await client.post("/chat/sessions", headers=headers)).json()["conversation_id"]
            pending = asyncio.create_task(
                client.post(
                    f"/chat/sessions/{cid}/messages",
                    headers=headers,
                    json={"message": "Yo no hice el cargo de Taller Prisma"},
                )
            )
            try:
                assert await asyncio.to_thread(entered.wait, 2)
                async with AsyncClient(
                    transport=ASGITransport(app=other), base_url="http://test"
                ) as second:
                    other_headers = {"Authorization": f"Bearer {await _sign_in(second)}"}
                    proposal, other_cid = await message(
                        second, other_headers, "Yo no hice el cargo de Taller Prisma"
                    )
                    receipt = await second.post(
                        f"/chat/sessions/{other_cid}/confirm",
                        headers=other_headers,
                        json={
                            "proposal_hash": proposal["proposal"]["proposal_hash"],
                            "confirmed": True,
                        },
                    )
                    assert receipt.status_code == 200 and receipt.json()["verified"]
            finally:
                release.set()
            result = await pending
            assert result.status_code == 200
            assert result.json()["outcome"] == "status_reported"
            assert result.json()["case"] == receipt.json()["case"]
            assert len(app.state.cases) == 1

    asyncio.run(check())


def test_cancelled_request_waits_for_shared_adapter_without_committing_actions() -> None:
    async def check() -> None:
        app = create_app(_settings(), ledger(), Runtime(system="P"))
        entered, release = Event(), Event()
        original = app.state.ai.understand
        calls = []

        def understand(*args, **kwargs):
            calls.append(args[0])
            entered.set()
            assert release.wait(5)
            return original(*args, **kwargs)

        app.state.ai.understand = understand
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            cid = (await client.post("/chat/sessions", headers=headers)).json()["conversation_id"]
            path = f"/chat/sessions/{cid}/messages"
            first = asyncio.create_task(
                client.post(
                    path, headers=headers, json={"message": "No hice el cargo de Taller Prisma"}
                )
            )
            try:
                assert await asyncio.to_thread(entered.wait, 2)
                first.cancel()
                second = asyncio.create_task(
                    client.post(
                        path,
                        headers=headers,
                        json={"message": "¿Qué es el cargo de Taller Prisma?"},
                    )
                )
                await asyncio.sleep(0.02)
                first.cancel()
                await asyncio.sleep(0.02)
                assert len(calls) == 1 and not first.done()
            finally:
                release.set()
            with pytest.raises(asyncio.CancelledError):
                await first
            assert (await second).json()["outcome"] == "explained"
            assert len(calls) == 2 and not app.state.cases
            assert len(app.state.executions) == 1

    asyncio.run(check())


@pytest.mark.parametrize(
    "change,expected", [("logout", 401), ("expiry", 401), ("conversation", 409)]
)
def test_revalidate_after_inference(change: str, expected: int) -> None:
    async def check() -> None:
        app = create_app(_settings(), ledger(), Runtime(system="P"))
        entered, release = Event(), Event()
        original = app.state.ai.understand

        def understand(*args, **kwargs):
            assert app.state.store.current.get() is None
            entered.set()
            assert release.wait(5)
            return original(*args, **kwargs)

        app.state.ai.understand = understand
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            principal = app.state.sessions[token]
            headers = {"Authorization": f"Bearer {token}"}
            cid = (await client.post("/chat/sessions", headers=headers)).json()["conversation_id"]
            pending = asyncio.create_task(
                client.post(
                    f"/chat/sessions/{cid}/messages",
                    headers=headers,
                    json={"message": "Yo no hice el cargo de Taller Prisma"},
                )
            )
            try:
                assert await asyncio.to_thread(entered.wait, 2)
                if change == "logout":
                    assert (await client.post("/auth/logout", headers=headers)).status_code == 200
                elif change == "expiry":
                    app.state.sessions[token] = replace(
                        principal, expires_at=datetime.now(UTC) - timedelta(seconds=1)
                    )
                else:
                    with app.state.store.transaction(
                        Scope(principal.customer_id, principal.run_id, principal.session_id)
                    ):
                        app.state.conversations[cid].rounds += 1
            finally:
                release.set()
            response = await pending
            assert response.status_code == expected
            with app.state.store.transaction(
                Scope(principal.customer_id, principal.run_id, principal.session_id)
            ):
                assert app.state.conversations[cid].proposal is None
                assert not app.state.cases and not app.state.executions

    asyncio.run(check())
