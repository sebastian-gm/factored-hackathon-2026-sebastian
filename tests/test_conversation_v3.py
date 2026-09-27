"""New authored dev regressions; no frozen confirmation/evaluation rows."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message, step_up

from aclara.agent.contracts import DisputeCaseView
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec
from aclara.ops.store import Store


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize(
    "language,opening,reply",
    [
        ("es", "No reconozco el cargo de Taller Prisma", "No fui yo, quiero disputar"),
        ("pt", "Não reconheço a cobrança de Taller Prisma", "Não fui eu, quero contestar"),
    ],
)
def test_offer_denial_otp_and_verified_commit(system, language, opening, reply):
    async def check():
        store = Store()
        settings = _settings()
        repo = ledger()
        app = create_app(settings, repo, runtime=Runtime(system=system), store=store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            offer, conv = await message(client, headers, opening)
            assert offer["response_type"] == "offer_dispute"
            assert offer["outcome"] == "awaiting_dispute_decision"
            assert offer["transaction"]["merchant"] == "Taller Prisma"
            assert not offer["proposal"] and not app.state.cases
            assert (
                await client.post(
                    f"/chat/sessions/{conv}/confirm",
                    headers=headers,
                    json={"proposal_hash": "0" * 64, "confirmed": True},
                )
            ).status_code == 409
        # Recreate the application over persisted serialized state before denial.
        app = create_app(settings, repo, runtime=Runtime(system=system), store=store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            proposal, _ = await message(client, headers, reply, conv)
            assert proposal["outcome"] == "dispute_proposed"
            assert proposal["transaction"]["handle"] == offer["transaction"]["handle"]
            principal = app.state.sessions[token]
            app.state.sessions[token] = replace(
                principal, otp_at=datetime.now(UTC) - timedelta(minutes=11)
            )
            payload = {"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True}
            assert (
                await client.post(f"/chat/sessions/{conv}/confirm", headers=headers, json=payload)
            ).status_code == 401
            await step_up(client, headers)
            result = await client.post(
                f"/chat/sessions/{conv}/confirm", headers=headers, json=payload
            )
            assert result.status_code == 200, result.text
            assert result.json()["verified"] and result.json()["outcome"] == "dispute_filed"
            record = await client.get(
                "/disputes/" + result.json()["case"]["case_id"], headers=headers
            )
            assert DisputeCaseView.model_validate(record.json()) == DisputeCaseView.model_validate(
                result.json()["case"]
            )

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize(
    "opening,recognized",
    [
        ("No reconozco el cargo de Taller Prisma", "Ah, ya me acordé, fui yo quien pagó"),
        ("Não reconheço a cobrança de Taller Prisma", "Já lembrei, fui eu que comprei"),
    ],
)
def test_recognition_resolves_and_isolated_assent_never_files(system, opening, recognized):
    async def check():
        app = create_app(_settings(), ledger(), runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            offer, conv = await message(client, headers, opening)
            resolved, _ = await message(client, headers, recognized, conv)
            assert resolved["outcome"] == "explained"
            assert resolved["transaction"]["handle"] == offer["transaction"]["handle"]
            _, conv = await message(client, headers, opening)
            first, _ = await message(client, headers, "sim", conv)
            assert first["outcome"] == "clarification"
            second, _ = await message(client, headers, "no", conv)
            assert second["handoff"]["reason_codes"] == ["ESC-04"]
            assert not app.state.cases

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
def test_status_pending_denial_and_changed_target(system):
    async def check():
        repo = ledger(two=True)
        repo._rows = (replace(repo._rows[0], transaction_status="Pending"), repo._rows[1])
        app = create_app(_settings(), repo, runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            status, _ = await message(client, headers, "Estado del cargo de Taller Prisma")
            assert status["outcome"] == "explained"
            offer, conv = await message(client, headers, "No reconozco el cargo de Taller Prisma")
            assert offer["response_type"] == "offer_dispute"
            denial, _ = await message(client, headers, "No fui yo", conv)
            assert denial["outcome"] == "explained" and denial["policy_rules"] == ["TXN-01"]
            _, conv = await message(client, headers, "No reconozco el cargo de Taller Prisma")
            changed, _ = await message(
                client, headers, "Otro cargo: no hice la compra de Estudio Nube por 38.61 USD", conv
            )
            assert changed["transaction"]["merchant"] == "Estudio Nube"
            assert changed["outcome"] == "dispute_proposed"
            assert not app.state.cases

    asyncio.run(check())


def test_structured_risk_union_and_cross_customer_restart():
    async def check():
        def response(_s, _u, schema):
            if schema is ExtractedNlu:
                return json.dumps(
                    {
                        "language": "es",
                        "intent": "human_request",
                        "intent_confidence": 0.99,
                        "human_requested": True,
                        "distress": True,
                        "legal": True,
                        "lost_stolen": True,
                    }
                )
            return "{}"

        llm = StructuredClient(
            {r: ModelSpec("mock", "risk-fixture") for r in ("nlu", "phrase")},
            {},
            mock_response=response,
        )
        store = Store()
        settings = _settings()
        app = create_app(
            settings, ledger(), runtime=Runtime(system="P"), llm_client=llm, store=store
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            result, _ = await message(client, headers, "Necesito ayuda")
            assert set(result["handoff"]["reason_codes"]) == {
                "FRD-01",
                "AUTH-02",
                "ESC-02",
                "ESC-03",
                "ESC-01",
            }
            assert result["handoff"]["primary_reason"] == "FRD-01"
            assert result["handoff"]["priority"] == "high"
            refused, _ = await message(client, headers, "Consulta la cuenta de mi esposa")
            assert refused["outcome"] == "refused_security" and not refused["session_ended"]
        app = create_app(settings, ledger(), store=store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            second, _ = await message(client, headers, "Consulta la cuenta de mi esposo")
            assert second["session_ended"] and second["verified"]
            assert set(second["handoff"]["reason_codes"]) == {"SEC-01", "AUTH-03"}
            assert second["outcome"] == "refused_security"
            assert (await client.get("/me", headers=headers)).status_code == 401
            actions = {e["event"] for e in app.state.runtime.events}
            assert {"refuse_request", "log_security_event", "end_session"} <= actions

    asyncio.run(check())
