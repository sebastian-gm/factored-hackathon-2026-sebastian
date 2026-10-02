"""Authored zero-network checks for the additive live basic-mode signal."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.contracts import ResponsePlan
from aclara.agent.nlu.structured import ExtractedNlu, postprocess
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("failure", ["outage", "invalid_output"])
def test_failed_nlu_reply_and_recovery_expose_basic_mode(
    language: str, failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    logged: list[bool] = []
    monkeypatch.setattr("aclara.api.app.log_turn", lambda *_args, degraded: logged.append(degraded))

    async def check() -> None:
        broken = failure == "invalid_output"

        def answer(_system: str, _user: str, schema: Any) -> str:
            if broken:
                return "{}"
            return json.dumps(
                {
                    "language": language,
                    "intent": "charge_inquiry",
                    "intent_confidence": 0.99,
                    "merchant_expr": "Taller Prisma",
                    "amount_expr": "17.43",
                    "currency_expr": "USD",
                }
            )

        llm = StructuredClient(
            {r: ModelSpec("mock", "authored-degraded") for r in ("nlu", "phrase")},
            {},
            mock_response=answer,
        )
        runtime = Runtime(
            system="P",
            faults=[{"type": "llm_outage", "trigger": "nlu"}] if failure == "outage" else [],
        )
        app = create_app(_settings(), ledger(), runtime=runtime, llm_client=llm)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
            headers = {"Authorization": f"Bearer {await _sign_in(api)}"}
            text = (
                "O que é essa cobrança de Taller Prisma por 17,43 USD?"
                if language == "pt"
                else "¿Qué es el cargo de Taller Prisma por 17.43 USD?"
            )
            result, cid = await message(api, headers, text)
            assert result["degraded"] is True
            assert result["outcome"] == "explained"
            assert not result.get("case") and not result.get("proposal")
            broken = False
            recovered, _ = await message(api, headers, text, cid)
            assert recovered["degraded"] is False
            assert recovered["outcome"] == "explained"
        assert logged == [True, False]

    asyncio.run(check())


def test_contract_is_additive_and_default_is_not_degraded() -> None:
    legacy = {"response_type": "clarify", "outcome": "clarification", "reply": "¿Qué monto?"}
    assert ResponsePlan.model_validate(legacy).degraded is False
    assert ResponsePlan.model_validate({**legacy, "degraded": True}).degraded is True
    schema = create_app(_settings()).openapi()["components"]["schemas"]["ResponsePlan"]
    assert schema["properties"]["degraded"]["type"] == "boolean"
    assert "degraded" not in schema["required"]


def test_degraded_nlu_is_exposed_even_when_risk_routing_returns_early(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def check() -> None:
        app = create_app(_settings(), ledger(), runtime=Runtime(system="P"))
        nlu = postprocess(
            ExtractedNlu(
                language="es", intent="charge_inquiry", intent_confidence=0.99, legal=True
            ),
            country="MX",
            bank_clock=app.state.settings.bank_clock,
        ).model_copy(update={"degraded": True})
        monkeypatch.setattr(app.state.ai, "understand", lambda *_args, **_kwargs: nlu)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
            headers = {"Authorization": f"Bearer {await _sign_in(api)}"}
            result, _ = await message(api, headers, "¿Qué es el cargo de Taller Prisma?")
            assert result["degraded"] is True
            assert result["outcome"] == "handoff_created" and result["verified"]
            assert "ESC-02" in result["handoff"]["reason_codes"]
            assert not result.get("case") and not result.get("proposal")

    asyncio.run(check())
