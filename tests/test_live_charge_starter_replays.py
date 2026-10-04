"""Synthetic replays: recorded intent/flags/slot shape, reconstructed raw extraction.
Owner explanation: charge_inquiry, unfamiliar=False, recognition=None; ES merchant
placeholder / PT missing merchant, no degradation or NLU clarification. Raw
confidence, amount, dates and risk flags below are reconstructions, not owner input.
Unknown-origin starters separately replay JE-05/17's inquiry/unfamiliar=True.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any, Literal

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from test_api_security import _settings, _sign_in
from test_workflow_api import message

from aclara.agent.contracts import HandoffView, Intent
from aclara.agent.nlu.structured import ExtractedNlu, postprocess
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import Customer, Transaction, TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec
from aclara.ops.store import Scope

Language = Literal["es", "pt"]
CLOCK = datetime(2026, 6, 18, 6, tzinfo=UTC)
STARTERS = {
    "es": "No reconozco la compra de Papelaria Prisma por 64.25 USD. ¿Qué es este cargo?",
    "pt": "Não reconheço a compra de Papelaria Prisma no valor de 64.25 USD. O que é essa cobrança?",
}


def _observation(language: Language) -> dict[str, Any]:
    payload = json.loads("""{
        "intent": "charge_inquiry", "intent_confidence": 0.99,
        "merchant_expr": "Papelaria Prisma", "amount_expr": "64.25",
        "currency_expr": "USD", "unfamiliar_charge": false}""")
    return {**payload, "language": language}


def _application(
    language: Language,
    observations: list[dict[str, Any]],
    *,
    missing_merchant: bool = False,
    process_day: int = 15,
) -> FastAPI:
    payloads = iter(observations)

    def respond(_system: str, _user: str, schema: type[BaseModel]) -> str:
        assert schema is ExtractedNlu
        return json.dumps(next(payloads), ensure_ascii=False)

    fields = json.loads("""{
        "record_id": "authored-starter", "customer_id": "demo-customer-01",
        "product_id": "authored-card", "transaction_type": "Purchase",
        "amount": 64.25, "currency": "USD", "transaction_status": "Approved"}""")
    row = Transaction(
        **fields,
        transaction_date=datetime(2026, 6, 15, 9, tzinfo=UTC),
        process_date=date(2026, 6, process_day),
        merchant_name="" if missing_merchant else "Papelaria Prisma",
    )
    repository = TransactionRepository(
        (row,),
        customers=(Customer(row.customer_id, country="MX"),),
        policy_fields={row.record_id: {"missing_fields": ("merchant_name",)}}
        if missing_merchant
        else {},
    )
    llm = StructuredClient(
        {route: ModelSpec("mock", "authored-starter-replay") for route in ("nlu", "phrase")},
        {},
        mock_response=respond,
        budget_usd=0,
        daily_budget_usd=0,
        risk_second_opinion_enabled=False,
    )
    settings = replace(
        _settings(),
        demo_locale="pt-BR" if language == "pt" else "es-MX",
        llm_provider="mock",
        ops_backend="memory",
        bank_clock=CLOCK,
    )
    return create_app(settings, repository, Runtime(system="P"), llm)


def _no_financial_writes(app: FastAPI, headers: dict[str, str]) -> bool:
    principal = app.state.sessions[headers["Authorization"].removeprefix("Bearer ")]
    with app.state.store.transaction(
        Scope(principal.customer_id, principal.run_id, principal.session_id)
    ):
        return not app.state.cases and not app.state.card_states


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize(
    "merchant", [None, "", " \t", "—", "  —  ", "Cargo", "Papelaria-Prisma", "Loja — Sul"]
)
def test_placeholder_normalization_preserves_raw_observation_and_other_slots(
    language: Language, merchant: str | None
) -> None:
    raw = ExtractedNlu.model_validate(
        {**_observation(language), "merchant_expr": merchant, "date_expr": "2026-06-15"}
    )
    result = postprocess(raw, country="MX", bank_clock=CLOCK)
    absent = merchant is None or merchant.strip() in {"", "—"}
    assert result.slots.merchant_expr == (None if absent else merchant)
    assert result.extracted == raw
    assert result.slots.model_dump(mode="json", exclude={"merchant_expr"}) == json.loads("""{
        "amount_value": "64.25", "currency": "USD", "date_start": "2026-06-15",
        "date_end": "2026-06-15", "type_expr": null, "product_hint": null,
        "country_expr": null, "count_expr": null}""")
    false_friend = language == "pt" and merchant == "Cargo"
    assert result.frame.intent == (Intent.OUT_OF_SCOPE if false_friend else Intent.CHARGE_INQUIRY)
    assert result.frame.confidence == (0.5 if false_friend else 0.99)
    assert result.extracted.recognition is None and not result.extracted.unfamiliar_charge
    assert result.clarification is None and not result.degraded


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("process_day", [14, 15])
def test_missing_bank_merchant_and_display_process_date_difference_stay_blocked(
    language: Language, process_day: int
) -> None:
    async def check() -> None:
        payload = {
            **_observation(language),
            "merchant_expr": "—" if language == "es" else None,
            "date_expr": "2026-06-15",
        }
        app = _application(language, [payload], missing_merchant=True, process_day=process_day)
        text = (
            "Quiero consultar la compra de — por 64.25 USD del 2026-06-15."
            if language == "es"
            else "Quero consultar a compra por 64.25 USD em 2026-06-15."
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            response, _ = await message(client, headers, text)
            assert response["response_type"] == ("offer_human" if process_day == 15 else "clarify")
            assert not response.get("proposal") and not response.get("case")
            if process_day == 15:
                handoff = response["handoff"]
                assert response["verified"] and "BRD-01" in handoff["reason_codes"]
                read = await client.get("/handoffs/" + handoff["handoff_id"], headers=headers)
                public = {k: v for k, v in read.json().items() if k in HandoffView.model_fields}
                assert read.status_code == 200
                assert HandoffView.model_validate(public) == HandoffView.model_validate(handoff)
            assert _no_financial_writes(app, headers) and app.state.ai.client.spent_usd == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_real_merchant_no_date_starter_explains_offers_and_requires_separate_confirmation(
    language: Language,
) -> None:
    async def check() -> None:
        observations = [
            _observation(language),
            {**_observation(language), "unfamiliar_charge": True},
            {**_observation(language), "recognition": "unsure", "customer_confirms": "yes"},
            {**_observation(language), "recognition": "denied"},
        ]
        app = _application(language, observations)
        neutral = (
            "Explícame la compra de Papelaria Prisma por 64.25 USD."
            if language == "es"
            else "Explique a compra de Papelaria Prisma no valor de 64.25 USD."
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            explained, cid = await message(client, headers, neutral)
            assert explained["response_type"] == "explain_status"
            offered, _ = await message(client, headers, STARTERS[language], cid)
            assert offered["response_type"] == "offer_dispute"
            assert offered["transaction"]["handle"] == explained["transaction"]["handle"]
            assert not offered.get("proposal") and not offered.get("case")
            assent, _ = await message(client, headers, "Sí" if language == "es" else "Sim", cid)
            assert assent["response_type"] in {"clarify", "offer_dispute"}
            denial = (
                "No fui yo; quiero disputarlo."
                if language == "es"
                else "Não fui eu; quero contestar."
            )
            proposal, _ = await message(client, headers, denial, cid)
            assert proposal["response_type"] == "confirm_action"
            for path, body in [
                ("messages", {"message": "Sí" if language == "es" else "Sim"}),
                ("confirm", {"proposal_hash": "0" * 64, "confirmed": True}),
            ]:
                result = await client.post(
                    f"/chat/sessions/{cid}/{path}", headers=headers, json=body
                )
                assert result.status_code == 409
            cancelled = await client.post(
                f"/chat/sessions/{cid}/confirm",
                headers=headers,
                json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": False},
            )
            assert cancelled.status_code == 200 and cancelled.json()["response_type"] == "cancelled"
            assert _no_financial_writes(app, headers) and app.state.ai.client.spent_usd == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize(
    "guard", ["human_requested", "legal", "other_customer_reference", "fresh", "low_confidence"]
)
def test_fresh_starter_confidence_and_independent_guard_controls(
    language: Language, guard: str
) -> None:
    async def check() -> None:
        payload = _observation(language)
        fresh = guard in {"fresh", "low_confidence"}
        if fresh:
            payload.update(
                unfamiliar_charge=True, intent_confidence=0.1 if guard == "low_confidence" else 0.99
            )
        else:
            payload.update(merchant_expr="—", **{guard: True})
        app = _application(language, [payload])
        text = STARTERS[language] if fresh else "Consulta / consulte: — 64.25 USD."
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            response, _ = await message(client, headers, text)
            expected = {"other_customer_reference": "refuse", "fresh": "offer_dispute"}
            assert response["response_type"] == expected.get(guard, "offer_human")
            assert not response.get("proposal") and not response.get("case")
            if guard == "fresh":
                assert response["outcome"] == "awaiting_dispute_decision"
                assert response["transaction"]["merchant"] == "Papelaria Prisma"
                amount = "64,25" if language == "pt" else "64.25"
                assert "Papelaria Prisma" in response["reply"] and amount in response["reply"]
                assert ("aprovada" if language == "pt" else "aprobado") in response["reply"]
            if guard == "low_confidence":
                assert "ESC-04" in response["handoff"]["reason_codes"]
            assert _no_financial_writes(app, headers) and app.state.ai.client.spent_usd == 0

    asyncio.run(check())
