"""Authored post-v4 regressions; mock models and no organizer data."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_judge_access import configured
from test_workflow_api import message, step_up

from aclara.api.app import create_app
from aclara.api.turn_logging import LOGGER, log_turn
from aclara.bank.serving import Persona
from aclara.ops.store import CustomerRecordMap


def test_public_personas_exclude_staff_and_any_configured_judge_alias():
    async def check():
        settings = replace(
            configured(),
            judge_persona=json.dumps(
                {"username": "judge.private-reviewer", "source_username": "authored.owner"}
            ),
        )
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
