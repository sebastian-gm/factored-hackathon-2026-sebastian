"""Actual Postgres integration; scripts/test_postgres creates a disposable local DB."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient
from psycopg import sql
from scripts.verify_audit_chain import verify

from aclara.api.app import create_app
from aclara.ops.store import TABLES, Scope, Store
from aclara.settings import Settings


@pytest.fixture
def dsn() -> str:
    value = os.getenv("TEST_OPS_DSN")
    if not value:
        pytest.skip("Disposable local Postgres required")
    return value


def context(connection, scope) -> None:
    for key, value in zip(
        ("app.customer_id", "app.run_id", "app.sid"),
        (scope.customer_id, scope.run_id, scope.sid),
        strict=True,
    ):
        connection.execute("SELECT set_config(%s,%s,true)", (key, value))


def test_forced_rls_tables_views_functions_autocommit_and_reuse(dsn: str) -> None:
    store = Store(dsn)
    a = Scope("fixture-a", str(uuid4()), "session-a")
    b = Scope("fixture-b", a.run_id, "session-b")
    try:
        for scope in (a, b):
            with store.transaction(scope):
                for table in TABLES - {"sessions", "otp_challenges", "demo_identities"}:
                    store.mapping(table, dict)["sample"] = {"owner": scope.customer_id}
        with psycopg.connect(dsn, autocommit=True) as db:
            assert db.execute(
                "SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user"
            ).fetchone() == (False, False)
            for relation in ("cases", "case_view"):
                assert db.execute(
                    sql.SQL("SELECT count(*) FROM ops.{}").format(sql.Identifier(relation))
                ).fetchone() == (0,)
            assert db.execute("SELECT ops.case_count()").fetchone() == (0,)
            with db.transaction():
                context(db, a)
                assert db.execute("SELECT count(*) FROM ops.case_view").fetchone() == (1,)
                assert db.execute("SELECT ops.case_count()").fetchone() == (1,)
                assert db.execute(
                    "SELECT count(*) FROM ops.cases WHERE customer_id=%s", (b.customer_id,)
                ).fetchone() == (0,)
                with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
                    db.execute(
                        "INSERT INTO ops.cases(customer_id,run_id,sid,id,payload) VALUES (%s,%s,%s,'attack','{}')",
                        (b.customer_id, a.run_id, a.sid),
                    )
            # Same physical connection, transaction-local context removed.
            assert db.execute("SELECT ops.case_count()").fetchone() == (0,)
            db.execute("SELECT set_config('app.customer_id',%s,true)", (a.customer_id,))
            assert db.execute("SELECT ops.case_count()").fetchone() == (0,)
            flags = db.execute(
                "SELECT relrowsecurity,relforcerowsecurity FROM pg_class JOIN pg_namespace n ON n.oid=relnamespace WHERE n.nspname='ops' AND relkind='r'"
            ).fetchall()
            assert flags and all(enabled and forced for enabled, forced in flags)
        for scope in (
            Scope(a.customer_id, "different-run", a.sid),
            Scope(a.customer_id, a.run_id, "different-session"),
            Scope("", "", ""),
        ):
            with store.transaction(scope):
                assert not store.mapping("cases", dict)
    finally:
        store.close()


def test_transaction_rollback_concurrent_chain_and_append_only(dsn: str) -> None:
    scope = Scope("fixture-chain", str(uuid4()), "session")
    store = Store(dsn)
    try:
        with pytest.raises(RuntimeError), store.transaction(scope):
            store.mapping("cases", dict)["rollback"] = {"status": "received"}
            raise RuntimeError("injected")
        with store.transaction(scope):
            assert "rollback" not in store.mapping("cases", dict)

        def append(index):
            replica = Store(dsn)
            try:
                with replica.transaction(scope):
                    replica.mapping("cases", dict)[str(index)] = {"status": "received"}
            finally:
                replica.close()

        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(append, range(6)))
        with psycopg.connect(dsn) as db:
            context(db, scope)
            rows = db.execute(
                "SELECT sequence,canonical,prev_hash,row_hash FROM ops.audit_log ORDER BY sequence"
            ).fetchall()
            assert verify(rows, (scope.customer_id, scope.run_id, scope.sid)) == 6
            with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
                db.execute("UPDATE ops.audit_log SET canonical='{}'")
            with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
                db.execute("DELETE FROM ops.audit_log")
            damaged = list(rows)
            sequence, canonical, previous, digest = damaged[2]
            payload = json.loads(canonical)
            payload["event"] = {"action": "tampered"}
            damaged[2] = (sequence, json.dumps(payload), previous, digest)
            with pytest.raises(ValueError, match="integrity"):
                verify(damaged, (scope.customer_id, scope.run_id, scope.sid))
    finally:
        store.close()


def test_api_session_proposal_case_handoff_and_execution_survive_restart(dsn: str) -> None:
    async def check() -> None:
        settings = Settings(
            demo_username="fixture",
            demo_password=secrets.token_urlsafe(32),
            demo_customer_id="fixture-restart",
        )
        # Use the existing authored ledger under the configured fixture customer.
        from dataclasses import replace

        from aclara.bank.repository import TransactionRepository

        ledger = TransactionRepository(
            tuple(
                replace(row, customer_id=settings.demo_customer_id)
                for row in TransactionRepository()._rows
                if row.customer_id == "demo-customer-01"
            )
        )
        first = Store(dsn)
        app = create_app(settings, ledger, store=first)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login = (
                await client.post(
                    "/auth/login",
                    json={"username": settings.demo_username, "password": settings.demo_password},
                )
            ).json()
            pre = {"X-Preauth-Token": login["preauth_token"]}
            code = (
                await client.get(f"/auth/challenges/{login['challenge_id']}/sms", headers=pre)
            ).json()["code"]
        first.close()
        second = Store(dsn)
        app = create_app(settings, ledger, store=second)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = (
                await client.post(
                    "/auth/otp/verify",
                    headers=pre,
                    json={"challenge_id": login["challenge_id"], "code": code},
                )
            ).json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            cid = (await client.post("/chat/sessions", headers=headers)).json()["conversation_id"]
            proposal = (
                await client.post(
                    f"/chat/sessions/{cid}/messages",
                    headers=headers,
                    json={"message": "No reconozco el cargo de Mercado Verde"},
                )
            ).json()
            principal = app.state.sessions[token]
            scope = Scope(principal.customer_id, principal.run_id, principal.session_id)
        second.close()
        third = Store(dsn)
        app = create_app(settings, ledger, store=third)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            result = await client.post(
                f"/chat/sessions/{cid}/confirm",
                headers=headers,
                json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True},
            )
            assert result.status_code == 200 and result.json()["verified"]
            case_id = result.json()["case"]["case_id"]
            handoff = (
                await client.post(
                    f"/chat/sessions/{cid}/messages",
                    headers=headers,
                    json={"message": "Quiero hablar con una persona"},
                )
            ).json()["handoff"]["handoff_id"]
            with third.transaction(scope):
                app.state.card_states["card_1"] = {"status": "frozen"}
        third.close()
        fourth = Store(dsn)
        app = create_app(settings, ledger, store=fourth)
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                assert (
                    await client.get(f"/disputes/{case_id}", headers=headers)
                ).status_code == 200
                assert (
                    await client.get(f"/handoffs/{handoff}", headers=headers)
                ).status_code == 200
                replay = await client.post(
                    f"/chat/sessions/{cid}/confirm",
                    headers=headers,
                    json={
                        "proposal_hash": proposal["proposal"]["proposal_hash"],
                        "confirmed": True,
                    },
                )
                assert replay.status_code == 409
            with fourth.transaction(scope):
                assert app.state.card_states["card_1"]["status"] == "frozen"
                assert len(app.state.cases) == 1
                assert len(app.state.executions) == 3
                assert len(app.state.turns) == 3
                assert len(app.state.conversations) == 1
            with fourth.transaction(Scope(scope.customer_id, str(uuid4()), scope.sid)):
                assert not app.state.cases and not app.state.handoffs
        finally:
            fourth.close()

    asyncio.run(check())
