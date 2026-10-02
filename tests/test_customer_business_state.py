"""Authored bank-state regressions; no organizer data or model calls."""

from __future__ import annotations

import asyncio
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb
from test_api_security import _settings, _sign_in
from test_workflow_api import message, step_up

from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.ops.migrate import migrate
from aclara.ops.store import CUSTOMER_TABLES, Scope, Store


@pytest.fixture(params=["memory", "postgres"])
def store(request):
    dsn = os.getenv("TEST_OPS_DSN") if request.param == "postgres" else None
    if request.param == "postgres" and not dsn:
        pytest.skip("Disposable local Postgres required")
    value = Store(dsn)
    yield value
    value.close()


def test_customer_state_is_shared_only_in_trusted_customer_realm(store):
    cid = "fixture-business-" + uuid4().hex
    cases = store.customer_mapping(
        "customer_cases", dict, lambda s: s.run_id.split("_")[0], legacy="cases"
    )
    cards = store.customer_mapping(
        "customer_card_states", dict, lambda s: s.run_id.split("_")[0], legacy="card_states"
    )
    with store.transaction(Scope(cid, "owner_first", "one")):
        cases["DSP-ONE"] = {"transaction_id": "fixture-txn", "status": "received"}
        cards["card"] = {"status": "Frozen"}
    with store.transaction(Scope(cid, "owner_second", "two")):
        assert cases["DSP-ONE"]["transaction_id"] == "fixture-txn"
        assert cards["card"]["status"] == "Frozen"
        error = psycopg.errors.UniqueViolation if store.pool else ValueError
        with pytest.raises(error):
            cases["DSP-TWO"] = {"transaction_id": "fixture-txn", "status": "received"}
    for scope in (
        Scope(cid, "judge-a_visit", "one"),
        Scope(cid, "judge-b_visit", "one"),
        Scope(cid + "-other", "owner_first", "one"),
    ):
        with store.transaction(scope):
            assert not cases and not cards
    if store.pool:
        with psycopg.connect(os.environ["TEST_OPS_DSN"], autocommit=True) as db:
            for table in CUSTOMER_TABLES:
                assert db.execute(
                    sql.SQL("SELECT count(*) FROM ops.{}").format(sql.Identifier(table))
                ).fetchone() == (0,)
            flags = db.execute(
                "SELECT relrowsecurity,relforcerowsecurity FROM pg_class JOIN pg_namespace n ON n.oid=relnamespace WHERE n.nspname='ops' AND relname IN ('customer_cases','customer_card_states')"
            ).fetchall()
            assert len(flags) == 2 and all(enabled and forced for enabled, forced in flags)


def test_customer_dispute_survives_login_and_lost_response_retry(store):
    async def check():
        settings = replace(_settings(), demo_customer_id="fixture-login-" + uuid4().hex)
        ledger = TransactionRepository(
            tuple(
                replace(r, customer_id=settings.demo_customer_id)
                for r in TransactionRepository()._rows
                if r.customer_id == "demo-customer-01"
            )
        )
        app = create_app(settings, ledger, store=store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": "Bearer " + token}
            other = {"Authorization": "Bearer " + await _sign_in(client)}
            proposal, conversation = await message(
                client, headers, "No hice el cargo de Mercado Verde"
            )
            body = {"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True}
            receipt = await client.post(
                f"/chat/sessions/{conversation}/confirm", headers=headers, json=body
            )
            assert receipt.status_code == 200 and receipt.json()["verified"]
            # A second login sees the case and cannot replay this login's action.
            duplicate, _ = await message(client, other, "No hice el cargo de Mercado Verde")
            assert duplicate["outcome"] == "status_reported"
            assert duplicate["case"] == receipt.json()["case"]
            status, _ = await message(client, other, "Estado de mi caso")
            assert status["case"] == receipt.json()["case"] and status["verified"]
            assert (
                await client.get("/disputes/" + receipt.json()["case"]["case_id"], headers=other)
            ).status_code == 200
            assert (
                await client.post(
                    f"/chat/sessions/{conversation}/confirm", headers=other, json=body
                )
            ).status_code == 404
            p = app.state.sessions[token]
            app.state.sessions[token] = replace(p, otp_at=p.otp_at - timedelta(minutes=6))
            replay = await client.post(
                f"/chat/sessions/{conversation}/confirm", headers=headers, json=body
            )
            assert replay.status_code == 200 and replay.json() == receipt.json()
            conflict = await client.post(
                f"/chat/sessions/{conversation}/confirm",
                headers=headers,
                json={**body, "confirmed": False},
            )
            assert conflict.status_code == 409
            with store.transaction(Scope(p.customer_id, p.run_id, p.session_id)):
                assert len(app.state.cases) == 1

    asyncio.run(check())


@pytest.mark.parametrize("profile", ["mx-es", "co-es", "ar-es", "pt"])
def test_judge_case_and_card_realms_are_fresh_per_login_and_survive_return_and_restart(
    store, monkeypatch, profile
):
    from test_judge_profiles import application, authenticate, headers, select

    app, settings, client = application(monkeypatch, store=store)
    first = select(client, authenticate(client, settings), profile)
    auth = headers(first)
    cid = client.post("/chat/sessions", headers=auth).json()["conversation_id"]
    query = "No hice el cargo de Fixture " + profile + " por 20 USD"
    proposal = client.post(
        f"/chat/sessions/{cid}/messages", headers=auth, json={"message": query}
    ).json()
    assert proposal["outcome"] == "dispute_proposed"
    filed = client.post(
        f"/chat/sessions/{cid}/confirm",
        headers=auth,
        json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True},
    ).json()
    assert filed["verified"]
    principal = app.state.sessions[first]
    with store.transaction(Scope(principal.customer_id, principal.run_id, principal.session_id)):
        app.state.card_states["judge-product-" + profile] = {"status": "Frozen"}
    second = select(client, authenticate(client, settings), profile)
    assert (
        client.get("/disputes/" + filed["case"]["case_id"], headers=headers(second)).status_code
        == 404
    )
    assert client.get("/cards/prod_1", headers=headers(second)).json()["status"] == "Active"
    fresh_cid = client.post("/chat/sessions", headers=headers(second)).json()["conversation_id"]
    fresh = client.post(
        f"/chat/sessions/{fresh_cid}/messages", headers=headers(second), json={"message": query}
    ).json()
    assert fresh["outcome"] == "dispute_proposed"
    second_filed = client.post(
        f"/chat/sessions/{fresh_cid}/confirm",
        headers=headers(second),
        json={"proposal_hash": fresh["proposal"]["proposal_hash"], "confirmed": True},
    ).json()
    assert second_filed["verified"]
    assert second_filed["case"]["case_id"] != filed["case"]["case_id"]
    assert second_filed["case"]["transaction_handle"] == filed["case"]["transaction_handle"]
    assert (
        client.get(
            "/disputes/" + second_filed["case"]["case_id"], headers=headers(first)
        ).status_code
        == 404
    )
    # The second visitor does not revoke or acquire the first visitor's authority.
    other_profile = "pt" if profile != "pt" else "mx-es"
    returned = select(client, select(client, first, other_profile), profile)
    assert (
        client.get("/disputes/" + filed["case"]["case_id"], headers=headers(returned)).status_code
        == 200
    )
    assert client.get("/cards/prod_1", headers=headers(returned)).json()["status"] == "Frozen"
    _, _, restarted = application(monkeypatch, store=store, settings=settings)
    assert (
        restarted.get(
            "/disputes/" + filed["case"]["case_id"], headers=headers(returned)
        ).status_code
        == 200
    )
    assert (
        restarted.get("/disputes/" + filed["case"]["case_id"], headers=headers(second)).status_code
        == 404
    )
    assert restarted.get("/cards/prod_1", headers=headers(second)).json()["status"] == "Active"


def test_owner_reset_clears_customer_bank_maps_across_logins_without_touching_judge_realm(store):
    async def check():
        settings = replace(
            _settings(),
            demo_role="ops",
            allow_demo_reset=True,
            demo_customer_id="fixture-reset-" + uuid4().hex,
        )
        ledger = TransactionRepository(
            tuple(
                replace(r, customer_id=settings.demo_customer_id)
                for r in TransactionRepository()._rows
                if r.customer_id == "demo-customer-01"
            )
        )
        app = create_app(settings, ledger, store=store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            auth = {"Authorization": "Bearer " + token}
            other = {"Authorization": "Bearer " + await _sign_in(client)}
            proposal, cid = await message(client, auth, "No hice el cargo de Mercado Verde")
            body = {"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True}
            filed = (
                await client.post(f"/chat/sessions/{cid}/confirm", headers=auth, json=body)
            ).json()
            assert filed["verified"]
            principal = app.state.sessions[token]
            owner_scope = Scope(principal.customer_id, principal.run_id, principal.session_id)
            with store.transaction(owner_scope):
                app.state.card_states[ledger._rows[0].product_id] = {"status": "Frozen"}
            protected = store.customer_mapping(
                "customer_cases", dict, lambda _: "judge:authored", legacy="cases"
            )
            protected_scope = Scope(principal.customer_id, "authored-other-visit", "protected")
            with store.transaction(protected_scope):
                protected["DSP-AUTHORED-PROTECTED"] = {
                    "transaction_id": "protected",
                    "status": "received",
                }
            assert (
                await client.get("/disputes/" + filed["case"]["case_id"], headers=other)
            ).status_code == 200
            await step_up(client, auth)
            reset_proposal = (await client.post("/ops/reset/proposal", headers=auth)).json()
            reset_body = {"proposal_hash": reset_proposal["proposal_hash"], "confirmed": True}
            reset = await client.post("/ops/reset", headers=auth, json=reset_body)
            assert reset.status_code == 200 and reset.json()["remaining_operations"] == 0
            assert (
                await client.get("/ops/reset/" + reset.json()["receipt_id"], headers=auth)
            ).json() == reset.json()
            assert (
                await client.post("/ops/reset", headers=auth, json=reset_body)
            ).json() == reset.json()
            assert (
                await client.get("/disputes/" + filed["case"]["case_id"], headers=other)
            ).status_code == 404
            assert (await client.get("/cards/prod_1", headers=other)).json()["status"] == "Active"
            assert (await client.get("/me", headers=other)).status_code == 200
            with store.transaction(protected_scope):
                assert len(protected) == 1
            fresh, _ = await message(client, other, "No hice el cargo de Mercado Verde")
            assert fresh["outcome"] == "dispute_proposed"

    asyncio.run(check())


def test_frozen_card_receipt_retry_is_read_only_after_step_up_expires(store):
    async def check():
        app = create_app(_settings(), store=store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": "Bearer " + token}
            offer, _ = await message(client, headers, "Me robaron la tarjeta")
            await step_up(client, headers)
            proposal = (
                await client.post(
                    "/cards/prod_1/freeze/proposal",
                    headers=headers,
                    json={"handoff_id": offer["handoff"]["handoff_id"]},
                )
            ).json()
            body = {"proposal_hash": proposal["proposal_hash"], "confirmed": True}
            receipt = await client.post("/cards/prod_1/freeze", headers=headers, json=body)
            assert receipt.status_code == 200
            p = app.state.sessions[token]
            app.state.sessions[token] = replace(p, step_up_at=p.otp_at - timedelta(minutes=6))
            replay = await client.post("/cards/prod_1/freeze", headers=headers, json=body)
            assert replay.status_code == 200 and replay.json() == receipt.json()
            other = {"Authorization": "Bearer " + await _sign_in(client)}
            assert (await client.get("/cards/prod_1", headers=other)).json()["status"] == "Frozen"
            assert (await client.get("/accounts", headers=other)).json()[0]["status"] == "Frozen"
            assert (
                await client.post(
                    "/cards/prod_1/freeze", headers=headers, json={**body, "confirmed": False}
                )
            ).status_code == 409

    asyncio.run(check())


def test_two_replicas_recheck_customer_index_before_writing(store):
    cid = "fixture-race-" + uuid4().hex

    def attempt(number):
        replica = Store(os.environ["TEST_OPS_DSN"]) if store.pool else store
        try:
            cases = replica.customer_mapping(
                "customer_cases", dict, lambda s: "owner", legacy="cases"
            )
            with replica.transaction(Scope(cid, str(number), str(number))):
                existing = next(iter(cases), None)
                if existing:
                    return existing
                key = "DSP-" + str(number)
                cases[key] = {"transaction_id": "one-charge", "status": "received"}
                return key
        finally:
            if replica is not store:
                replica.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        ids = list(executor.map(attempt, [1, 2]))
    assert len(set(ids)) == 1


@pytest.mark.skipif(
    not os.getenv("TEST_OPS_OWNER_DSN"), reason="Disposable local Postgres required"
)
def test_populated_legacy_backfill_retains_receipts_and_separates_judge_realms():
    owner = os.environ["TEST_OPS_OWNER_DSN"]
    database = "aclara_backfill_" + uuid4().hex[:12]
    with psycopg.connect(owner, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        target = make_conninfo(owner, dbname=database)
        try:
            migrate(target)
            with psycopg.connect(target) as db:
                # Reconstruct the pre-0004 schema in this disposable DB only.
                db.execute("DROP FUNCTION ops.publish_handoff_queue(jsonb)")
                db.execute("DROP TABLE ops.realm_handoffs")
                db.execute("DROP TABLE ops.customer_cases,ops.customer_card_states")
                db.execute("UPDATE alembic_version SET version_num='0003_llm_budget'")
                db.execute("CREATE TABLE reference.demo_personas(username text,customer_id text)")
                db.execute("ALTER TABLE reference.demo_personas OWNER TO aclara_owner")
                db.execute(
                    "INSERT INTO reference.demo_personas VALUES ('fixture-signed-out','fixture')"
                )
                logged_out = hashlib.sha256(b"fixture-signed-out").hexdigest()[:12] + "_visit"
                for run, username in (
                    ("owner_one", "fixture-owner"),
                    ("owner_two", "fixture-owner"),
                    ("judge_one", "judge.fixture"),
                ):
                    db.execute(
                        "INSERT INTO ops.sessions(customer_id,run_id,sid,id,payload) VALUES ('fixture',%s,'session',%s,%s)",
                        (run, run, Jsonb({"username": username})),
                    )
                for number, run in enumerate(
                    ("owner_one", "owner_two", "judge_one", "unknown_one", logged_out)
                ):
                    payload = {
                        "case_id": "DSP-" + str(number),
                        "transaction_id": "one-charge",
                        "status": "received",
                    }
                    db.execute(
                        "INSERT INTO ops.cases(customer_id,run_id,sid,id,payload) VALUES ('fixture',%s,'session',%s,%s)",
                        (run, payload["case_id"], Jsonb(payload)),
                    )
                    db.execute(
                        "INSERT INTO ops.card_states(customer_id,run_id,sid,id,payload) VALUES ('fixture',%s,'session','card',%s)",
                        (run, Jsonb({"status": "Frozen" if number == 0 else "Active"})),
                    )
            migrate(target)
            with psycopg.connect(target) as db:
                assert db.execute("SELECT count(*) FROM ops.cases").fetchone() == (5,)
                assert db.execute("SELECT count(*) FROM ops.customer_cases").fetchone() == (5,)
                assert db.execute(
                    "SELECT count(*) FROM ops.customer_cases WHERE realm='owner' AND coalesce(payload->>'_canonical','true')='true'"
                ).fetchone() == (1,)
                assert db.execute(
                    "SELECT realm FROM ops.customer_cases ORDER BY id"
                ).fetchall() == [
                    ("owner",),
                    ("owner",),
                    ("judge:judge",),
                    ("legacy:unknown_one",),
                    ("owner",),
                ]
                assert db.execute(
                    "SELECT payload->>'status' FROM ops.customer_card_states WHERE realm='owner'"
                ).fetchone() == ("Frozen",)
                flags = db.execute(
                    "SELECT relrowsecurity,relforcerowsecurity FROM pg_class JOIN pg_namespace n ON n.oid=relnamespace WHERE n.nspname='ops' AND relkind='r'"
                ).fetchall()
                assert flags and all(enabled and forced for enabled, forced in flags)
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))
