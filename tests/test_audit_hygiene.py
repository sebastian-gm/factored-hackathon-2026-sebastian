"""Authored post-v4 regressions; mock models and no organizer data."""

from __future__ import annotations

import ast
import asyncio
import json
import logging
from contextlib import nullcontext
from contextvars import ContextVar
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_judge_access import configured
from test_workflow_api import message, step_up

from aclara.api.app import create_app
from aclara.api.turn_logging import LOGGER, log_turn
from aclara.bank.serving import Persona, ServingRepository
from aclara.llm.types import BudgetFailure
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import CustomerRecordMap, Scope, Store


@pytest.mark.parametrize("alias", ["judge.private-reviewer", "reviewer-private"])
def test_public_personas_exclude_staff_and_any_configured_judge_alias(alias):
    async def check():
        settings = replace(
            configured(),
            judge_persona=json.dumps({"username": alias, "source_username": "authored.owner"}),
        )
        if not alias.startswith("judge."):
            with pytest.raises(ValueError, match="Invalid or unavailable Key Vault judge persona"):
                create_app(settings)
            return
        app = create_app(settings)
        app.state.personas.update(
            {
                "staff-authored": Persona("staff-authored", "fixture", "es-MX", "agent"),
                "ops-authored": Persona("ops-authored", "fixture", "es-MX", "ops"),
                "judge.hidden": Persona("judge.hidden", "fixture", "es-MX", "customer"),
            }
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.get("/personas")
        assert response.status_code == 200
        assert [p["username"] for p in response.json()] == ["authored.owner"]

    asyncio.run(check())


def test_login_receipt_exposes_exact_35_minute_expiry():
    async def check():
        app = create_app(_settings())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            before = datetime.now(UTC)
            token = await _sign_in(c)
            session = app.state.sessions[token]
            assert 34 * 60 < (session.expires_at - before).total_seconds() < 36 * 60
            # API expiry is used by the BFF instead of an independent shorter cookie.
            login = (
                await c.post(
                    "/auth/login",
                    json={
                        "username": app.state.settings.demo_username,
                        "password": app.state.settings.demo_password,
                    },
                )
            ).json()
            pre = {"X-Preauth-Token": login["preauth_token"]}
            sms = (await c.get(f"/auth/challenges/{login['challenge_id']}/sms", headers=pre)).json()
            receipt = (
                await c.post(
                    "/auth/otp/verify",
                    headers=pre,
                    json={"challenge_id": login["challenge_id"], "code": sms["code"]},
                )
            ).json()
            assert (
                datetime.fromisoformat(receipt["expires_at"])
                == app.state.sessions[receipt["access_token"]].expires_at
            )

    asyncio.run(check())


def test_freeze_readback_failure_is_explicit_and_rolls_back(monkeypatch):
    async def check():
        app = create_app(_settings())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            headers = {"Authorization": "Bearer " + await _sign_in(c)}
            offer, _ = await message(c, headers, "Me robaron la tarjeta")
            await step_up(c, headers)
            proposal = (
                await c.post(
                    "/cards/prod_1/freeze/proposal",
                    headers=headers,
                    json={"handoff_id": offer["handoff"]["handoff_id"]},
                )
            ).json()
            original = CustomerRecordMap.__getitem__

            def bad_read(mapping, key):
                if mapping.table == "customer_card_states":
                    return {"status": "Active"}
                return original(mapping, key)

            with monkeypatch.context() as patch:
                patch.setattr(CustomerRecordMap, "__getitem__", bad_read)
                response = await c.post(
                    "/cards/prod_1/freeze",
                    headers=headers,
                    json={"proposal_hash": proposal["proposal_hash"], "confirmed": True},
                )
            assert response.status_code == 503
            assert response.json()["detail"] == "Freeze readback failed"
            assert (await c.get("/cards/prod_1", headers=headers)).json()["status"] == "Active"

    asyncio.run(check())


@pytest.mark.parametrize("unknown", [False, True])
def test_turn_log_contains_only_metadata_and_preserves_unknown_cost(unknown):
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(json.loads(record.getMessage()))

    handler = Capture()
    LOGGER.addHandler(handler)
    try:
        log_turn(
            "authored-conversation",
            {
                "outcome": "explained",
                "policy_rules": ["TXN-02"],
                "text": "AUTHORED_PRIVATE_CUSTOMER_TEXT",
                "case": {"policy_rules": ["AUTH-01"]},
                "proposal": {"policy_rules": ["DSP-02"]},
                "handoff": {"reason_codes": ["ESC-01"]},
            },
            [
                {
                    "event": "llm_call",
                    "latency_ms": 12.5,
                    "cost_usd": None if unknown else 0.001,
                    "message": "AUTHORED_PRIVATE_CUSTOMER_TEXT",
                },
                {"event": "policy", "rule_ids": ["TXN-01"]},
            ],
            degraded=unknown,
        )
    finally:
        LOGGER.removeHandler(handler)
    assert records == [
        {
            "conversation_id": "authored-conversation",
            "outcome": "explained",
            "rule_ids": ["AUTH-01", "DSP-02", "ESC-01", "TXN-01", "TXN-02"],
            "llm_latency_ms": 12.5,
            "llm_cost_usd": None if unknown else 0.001,
            "degraded": unknown,
        }
    ]


@pytest.mark.parametrize("method", ["init", "personas", "directory", "snapshot"])
def test_serving_reads_fail_explicitly_without_a_connection(method):
    clock = _settings().bank_clock
    store = SimpleNamespace(
        pool=object(),
        current=ContextVar("authored-empty-serving-unit", default=None),
        transaction=lambda _: nullcontext(),
        _unit=lambda: SimpleNamespace(connection=None),
    )
    with pytest.raises(psycopg.OperationalError, match="Serving connection unavailable"):
        if method == "init":
            ServingRepository(store, clock)
        else:
            repository = object.__new__(ServingRepository)
            repository.store = store
            repository.bank_clock = clock
            if method == "snapshot":
                repository.snapshot("authored-customer", clock)
            else:
                getattr(repository, method)()


@pytest.mark.parametrize("method", ["reserve", "settle"])
def test_budget_pool_loss_fails_closed_with_the_reserve_retained(method):
    store = Store()
    pool = Mock()
    store.pool = pool
    gate = PostgresSpendGate(store)
    store.pool = None
    with pytest.raises(BudgetFailure, match="Durable model"):
        if method == "reserve":
            gate.reserve(0.01)
        else:
            gate.settle("00000000-0000-0000-0000-000000000000", 0)
    pool.connection.assert_not_called()


@pytest.mark.parametrize(
    "path,method", [("/auth/judge/profiles", "GET"), ("/auth/judge/profile", "POST")]
)
def test_missing_judge_controller_cannot_list_or_switch_profiles(path, method):
    async def check():
        app = create_app(_settings())
        route = next(route for route in app.routes if getattr(route, "path", None) == path)
        # Force the impossible post-dependency state, without real credentials.
        dependency = route.dependant.dependencies[0].call
        app.dependency_overrides[dependency] = lambda: object()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.request(
                method, path, **({"json": {"profile_id": "mx-es"}} if method == "POST" else {})
            )
        assert response.status_code == 404
        assert response.json()["detail"] == "Judge profiles unavailable"

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_lost_recognition_target_never_proposes_or_files(language, monkeypatch):
    async def check():
        app = create_app(_settings(), ledger())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            principal = app.state.sessions[token]
            headers = {"Authorization": "Bearer " + token}
            opening = (
                "Não reconheço a cobrança de Taller Prisma por 17.43 USD"
                if language == "pt"
                else "No reconozco el cargo de Taller Prisma por 17.43 USD"
            )
            offer, cid = await message(client, headers, opening)
            assert offer["response_type"] == "offer_dispute"

            def lost_target(*_args):
                app.state.conversations[cid].offer_handle = None
                return False

            monkeypatch.setattr("aclara.api.app.changes_target", lost_target)
            denied = "Eu não fiz essa compra" if language == "pt" else "Yo no hice esa compra"
            response = await client.post(
                f"/chat/sessions/{cid}/messages", headers=headers, json={"message": denied}
            )
            assert response.status_code == 503
            assert response.json()["detail"] == "Dispute offer context unavailable"
            with app.state.store.transaction(
                Scope(principal.customer_id, principal.run_id, principal.session_id)
            ):
                assert not app.state.cases
                assert app.state.conversations[cid].proposal is None
                assert app.state.conversations[cid].offer_handle == offer["transaction"]["handle"]

    asyncio.run(check())


def test_completed_turns_and_freeze_retries_log_once_after_readback():
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(json.loads(record.getMessage()))

    async def check():
        app = create_app(_settings(), ledger())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            await message(client, headers, "¿Qué es el cargo de Taller Prisma?")
            proposal, cid = await message(client, headers, "No hice el cargo de Taller Prisma")
            for _ in range(2):
                confirmed = await client.post(
                    f"/chat/sessions/{cid}/confirm",
                    headers=headers,
                    json={
                        "proposal_hash": proposal["proposal"]["proposal_hash"],
                        "confirmed": True,
                    },
                )
                assert confirmed.status_code == 200 and confirmed.json()["verified"]
            offer, freeze_cid = await message(client, headers, "Me robaron la tarjeta")
            await step_up(client, headers)
            freeze = (
                await client.post(
                    "/cards/prod_1/freeze/proposal",
                    headers=headers,
                    json={"handoff_id": offer["handoff"]["handoff_id"]},
                )
            ).json()
            for _ in range(2):
                receipt = await client.post(
                    "/cards/prod_1/freeze",
                    headers=headers,
                    json={"proposal_hash": freeze["proposal_hash"], "confirmed": True},
                )
                assert receipt.status_code == 200 and receipt.json()["card"]["verified"]
            assert [r["outcome"] for r in records] == [
                "explained",
                "dispute_proposed",
                "dispute_filed",
                "dispute_filed",
                "handoff_created",
                "handoff_created",
                "handoff_created",
            ]
            assert all(r["conversation_id"] == freeze_cid for r in records[-3:])
            assert all(r["llm_latency_ms"] == r["llm_cost_usd"] == 0 for r in records)
            assert all(
                set(r)
                == {
                    "conversation_id",
                    "outcome",
                    "rule_ids",
                    "llm_latency_ms",
                    "llm_cost_usd",
                    "degraded",
                }
                for r in records
            )

    handler = Capture()
    LOGGER.addHandler(handler)
    try:
        asyncio.run(check())
    finally:
        LOGGER.removeHandler(handler)


def test_action_policy_storage_and_budget_guards_do_not_use_assert():
    root = Path(__file__).resolve().parents[1] / "src/aclara"
    paths = [*root.joinpath("api").glob("*.py"), root / "bank/serving.py", root / "ops/budget.py"]
    assert not [
        (path.name, node.lineno)
        for path in paths
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.Assert)
    ]
