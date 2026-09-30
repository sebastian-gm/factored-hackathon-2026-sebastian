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
                    json={"message": "No hice el cargo de Mercado Verde"},
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
                assert len(app.state.executions) == 4
                assert any(
                    r.get("outcome") == "handoff_verified" for r in app.state.executions.values()
                )
                assert len(app.state.turns) == 3
                assert len(app.state.conversations) == 1
            with fourth.transaction(Scope(scope.customer_id, str(uuid4()), scope.sid)):
                assert not app.state.cases and not app.state.handoffs
        finally:
            fourth.close()

    asyncio.run(check())


def test_freeze_api_and_step_up_survive_app_restart(dsn: str) -> None:
    from test_api_security import _settings, _sign_in
    from test_workflow_api import step_up

    async def check() -> None:
        first = Store(dsn)
        app = create_app(_settings(), store=first)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            await step_up(client, headers)
            proposal = (
                await client.post("/cards/prod_1/freeze/proposal", headers=headers, json={})
            ).json()
        first.close()
        second = Store(dsn)
        app = create_app(_settings(), store=second)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/cards/prod_1/freeze",
                headers=headers,
                json={"proposal_hash": proposal["proposal_hash"], "confirmed": True},
            )
            assert response.status_code == 200, response.text
            handoff = response.json()["handoff"]["handoff_id"]
        second.close()
        third = Store(dsn)
        try:
            app = create_app(_settings(), store=third)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                assert (await client.get("/cards/prod_1", headers=headers)).json()[
                    "status"
                ] == "Frozen"
                packet = (await client.get(f"/handoffs/{handoff}", headers=headers)).json()
                assert packet["freeze_outcome"] == "verified"
                assert packet["route"]["queue"] == "Fraudes"
        finally:
            third.close()

    asyncio.run(check())


def test_session_security_cues_survive_restart_and_another_tab(dsn: str) -> None:
    from test_api_security import _settings, _sign_in
    from test_workflow_api import message

    async def check() -> None:
        first = Store(dsn)
        app = create_app(_settings(), store=first)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            result, tab = await message(
                client,
                headers,
                "Quiero ver la cuenta de mi esposo. Voy a reclamar al regulador.",
            )
            assert not result["session_ended"]
            principal = app.state.sessions[token]
            scope = Scope(principal.customer_id, principal.run_id, principal.session_id)
        first.close()
        second = Store(dsn)
        try:
            app = create_app(_settings(), store=second)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                result, another_tab = await message(client, headers, "Soy el esposo del titular")
                assert another_tab != tab and result["session_ended"]
                assert {"SEC-01", "AUTH-03", "ESC-02"} <= set(result["handoff"]["reason_codes"])
                assert result["handoff"]["conversation_id"] == another_tab
                assert (await client.get("/me", headers=headers)).status_code == 401
            with second.transaction(scope):
                state = app.state.executions["security_state"]
                assert state["attempts"] == 2 and state["cues"] == ["ESC-02"]
                assert (
                    app.state.handoffs[result["handoff"]["handoff_id"]]["reason_codes"]
                    == result["handoff"]["reason_codes"]
                )
        finally:
            second.close()

    asyncio.run(check())


def test_reference_routing_is_read_only_for_api(dsn: str) -> None:
    from aclara.handoff.routing import AgentDirectory

    with psycopg.connect(os.environ["TEST_OPS_OWNER_DSN"]) as owner:
        owner.execute(
            "INSERT INTO reference.service_agents VALUES ('agent_fixture_pt_fraud','Active','Digital','portugués','Fraudes',3)"
        )
    store = Store(dsn)
    try:
        directory = AgentDirectory(store=store)
        assert directory.route("pt", "FRD-01")["assigned_agent_ref"] == "agent_fixture_pt_fraud"
        with (
            psycopg.connect(dsn, autocommit=True) as connection,
            pytest.raises(psycopg.errors.InsufficientPrivilege),
        ):
            connection.execute("DELETE FROM reference.service_agents")
    finally:
        store.close()


def test_staff_claim_and_reset_are_durable_with_audit_retained(dsn: str) -> None:
    from dataclasses import replace

    from test_api_security import _settings, _sign_in
    from test_workflow_api import message, step_up

    async def check():
        settings = replace(_settings(), demo_role="ops", allow_demo_reset=True)
        first = Store(dsn)
        app = create_app(settings, store=first)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            result, _ = await message(client, headers, "Quiero un agente")
            key = result["handoff"]["handoff_id"]
            claimed = await client.post(
                f"/agent/handoffs/{key}/claim",
                headers=headers,
                json={"expected_version": 1, "idempotency_key": "durable_claim_01"},
            )
            assert claimed.status_code == 200
            principal = app.state.sessions[token]
            scope = Scope(principal.customer_id, principal.run_id, principal.session_id)
        first.close()
        second = Store(dsn)
        app = create_app(settings, store=second)
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                assert (
                    await client.get(f"/agent/handoffs/{key}", headers=headers)
                ).json() == claimed.json()
                await step_up(client, headers)
                proposal = (await client.post("/ops/reset/proposal", headers=headers)).json()
                result = await client.post(
                    "/ops/reset",
                    headers=headers,
                    json={"proposal_hash": proposal["proposal_hash"], "confirmed": True},
                )
                assert result.status_code == 200 and result.json()["remaining_operations"] == 0
                assert (await client.get("/agent/handoffs", headers=headers)).json() == []
            with psycopg.connect(dsn) as db:
                context(db, scope)
                entries = db.execute(
                    "SELECT sequence,canonical,prev_hash,row_hash FROM ops.audit_log ORDER BY sequence"
                ).fetchall()
                assert entries and verify(
                    entries, (scope.customer_id, scope.run_id, scope.sid)
                ) == len(entries)
                assert any("workspace_reset" in row[1] for row in entries)
        finally:
            second.close()

    asyncio.run(check())


def test_clarification_handoff_is_terminal_after_restart(dsn: str):
    from test_api_security import _settings, _sign_in
    from test_dev_acceptance import ledger
    from test_workflow_api import message

    async def check():
        first_store = Store(dsn)
        first = create_app(_settings(), ledger(True), store=first_store)
        async with AsyncClient(
            transport=ASGITransport(app=first), base_url="http://test"
        ) as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            _, conv = await message(client, headers, "No reconozco una compra")
            await message(client, headers, "El primero o el segundo", conv)
            result, _ = await message(client, headers, "No puedo elegir", conv)
            packet_id = result["handoff"]["handoff_id"]
        first_store.close()
        second_store = Store(dsn)
        try:
            second = create_app(_settings(), ledger(True), store=second_store)
            async with AsyncClient(
                transport=ASGITransport(app=second), base_url="http://test"
            ) as client:
                result, _ = await message(
                    client, headers, "No reconozco el cargo de Taller Prisma", conv
                )
                assert result["handoff"]["handoff_id"] == packet_id
                assert result["verified"]
                principal = second.state.sessions[token]
                with second_store.transaction(
                    Scope(principal.customer_id, principal.run_id, principal.session_id)
                ):
                    assert not second.state.cases
                    assert len(second.state.handoffs) == 1
        finally:
            second_store.close()

    asyncio.run(check())


def test_offer_and_cross_customer_strikes_survive_postgres_restart(dsn: str):
    from test_api_security import _settings, _sign_in
    from test_dev_acceptance import ledger
    from test_workflow_api import message

    async def check():
        from httpx import ASGITransport, AsyncClient

        settings = _settings()
        first_store = Store(dsn)
        app = create_app(settings, ledger(), store=first_store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            offer, conv = await message(client, headers, "No reconozco el cargo de Taller Prisma")
            assert offer["response_type"] == "offer_dispute"
        first_store.close()
        second_store = Store(dsn)
        app = create_app(settings, ledger(), store=second_store)
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                proposal, _ = await message(client, headers, "No fui yo", conv)
                assert proposal["outcome"] == "dispute_proposed"
                assert proposal["transaction"]["handle"] == offer["transaction"]["handle"]
                first, _ = await message(client, headers, "Quiero ver la cuenta de mi esposo")
                assert not first["session_ended"]
                denied = await client.post(
                    f"/chat/sessions/{conv}/confirm",
                    headers=headers,
                    json={
                        "proposal_hash": proposal["proposal"]["proposal_hash"],
                        "confirmed": True,
                    },
                )
                assert denied.status_code == 409
            second_store.close()
            second_store = Store(dsn)
            app = create_app(settings, ledger(), store=second_store)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                second, _ = await message(client, headers, "Soy el esposo del titular")
                assert second["session_ended"] and second["verified"]
                assert set(second["handoff"]["reason_codes"]) == {"SEC-01", "AUTH-03"}
                assert (await client.get("/me", headers=headers)).status_code == 401
        finally:
            second_store.close()

    asyncio.run(check())
