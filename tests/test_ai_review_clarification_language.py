"""Authored mock regressions for PR #62 findings 1 and 3; no paid/frozen input."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.contracts import ResponsePlan, TransactionView
from aclara.agent.nlg.builder import build_reply
from aclara.agent.nlg.grounding import AllowedFact
from aclara.agent.nlu.rules import detect_language, detect_language_evidence
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec


def phrase_client(text: str, seen: list[str]) -> StructuredClient:
    def answer(_system, user, _schema):
        seen.append(user)
        return json.dumps({"text": text, "cited_fact_ids": []})

    return StructuredClient(
        {route: ModelSpec("mock", "authored-review") for route in ("nlu", "phrase")},
        {},
        mock_response=answer,
    )


def test_language_help_cannot_be_replaced_by_a_generic_safe_draft() -> None:
    async def check() -> None:
        seen: list[str] = []
        llm = phrase_client("¿Puedes indicar el monto o la fecha?", seen)
        app = create_app(_settings(), ledger(), runtime=Runtime(system="P"), llm_client=llm)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, _ = await message(client, headers, "Please help me understand a charge.")
        assert result["response_type"] == "clarify"
        assert "español" in result["reply"] and "português" in result["reply"]
        assert not seen and not llm.records  # language-help is deterministic

    asyncio.run(check())


@pytest.mark.parametrize(
    "reply",
    [
        "¿Ahora reconoces el cargo, o quieres disputarlo?",
        "Agora você reconhece a cobrança ou quer contestá-la?",
        "Puedo atenderte en español o portugués. / Posso atender em espanhol ou português.",
    ],
)
def test_code_supplied_clarification_remains_exact(reply: str) -> None:
    seen: list[str] = []
    plan = ResponsePlan(response_type="clarify", outcome="clarification", reply=reply)
    result = build_reply(
        plan,
        language="pt" if reply.startswith("Agora") else "es",
        client=phrase_client("Indica el monto.", seen),
    )
    assert result.plan.reply == reply and result.used_template
    assert not seen


@pytest.mark.parametrize(
    "text",
    [
        "¿Qué es el cargo de Booking.com?",
        "Quiero hablar con una persona por mi tarjeta SIM.",
        "Necesito hablar con un agente sobre el cargo de Sim.com.",
    ],
)
def test_domains_and_sim_do_not_change_spanish_routing(text: str) -> None:
    assert detect_language(text) == "es"


@pytest.mark.parametrize("text", ["Informe valor.", "Sim", "com", "Booking.com"])
def test_insufficient_evidence_is_explicitly_uncertain(text: str) -> None:
    assert detect_language_evidence(text) == "uncertain"


@pytest.mark.parametrize("text", ["Informe valor e moeda.", "A transação foi aprovada."])
def test_short_pt_has_distinctive_context(text: str) -> None:
    assert detect_language_evidence(text) == "pt"


def test_conflicting_evidence_is_uncertain() -> None:
    assert detect_language_evidence("Quiero falar com uma pessoa") == "uncertain"


def test_sim_request_keeps_spanish_handoff_through_mock_api() -> None:
    async def check() -> None:
        seen: list[str] = []
        app = create_app(
            _settings(),
            ledger(),
            runtime=Runtime(system="P"),
            llm_client=phrase_client("Indica el monto.", seen),
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, _ = await message(
                client, headers, "Quiero hablar con una persona por mi tarjeta SIM."
            )
        assert result["handoff"]["route"]["language"] == "es"
        assert not seen

    asyncio.run(check())


def test_short_valid_pt_draft_is_not_retried_or_rejected() -> None:
    seen: list[str] = []
    plan = ResponsePlan(response_type="clarify", outcome="clarification", reply="")
    result = build_reply(plan, language="pt", client=phrase_client("Informe valor e moeda.", seen))
    assert result.plan.reply == "Informe valor e moeda."
    assert not result.used_template and not result.violations
    assert len(seen) == 1


def test_uncertain_short_draft_does_not_default_to_opposite_language() -> None:
    seen: list[str] = []
    plan = ResponsePlan(response_type="clarify", outcome="clarification", reply="")
    result = build_reply(plan, language="pt", client=phrase_client("Informe valor.", seen))
    assert result.plan.reply == "Informe valor." and not result.violations
    assert len(seen) == 1


def test_rephrasing_context_contains_actual_approved_reply() -> None:
    seen: list[str] = []
    transaction = TransactionView(
        handle="fixture-txn-001",
        transaction_date=datetime(2026, 6, 10, tzinfo=UTC),
        transaction_type="Purchase",
        amount=80,
        currency="USD",
        merchant="Mercado Ensayo",
        status="Pending",
    )
    approved = "El comercio todavía está procesando el cargo. Si lo identificas, puedes revisarlo."
    plan = ResponsePlan(
        response_type="explain_status",
        outcome="explained",
        reply=approved,
        transaction=transaction,
    )
    build_reply(plan, language="es", client=phrase_client(approved, seen))
    context = json.loads(seen[0].partition("<response_plan>")[2].partition("</response_plan>")[0])
    assert context["approved_text"] == approved


@pytest.mark.parametrize(
    ("language", "draft"),
    [
        ("es", "Pode fornecer mais detalhes?"),
        ("pt", "Puedes indicar la moneda y el monto?"),
    ],
)
def test_confident_opposite_language_is_still_rejected(language: str, draft: str) -> None:
    seen: list[str] = []
    plan = ResponsePlan(response_type="clarify", outcome="clarification", reply="")
    built = build_reply(plan, language=language, client=phrase_client(draft, seen))
    assert built.used_template and "language_mismatch" in built.violations
    assert built.plan.reply != draft


def test_known_merchant_name_is_not_language_evidence() -> None:
    seen: list[str] = []
    # The whole trusted merchant name must be removed, even when it contains
    # distinctive words from the opposite language. Facts still require citation.
    merchant = "Quero Agora"
    transaction = TransactionView(
        handle="fixture-txn-001",
        transaction_date=datetime(2026, 6, 10, tzinfo=UTC),
        transaction_type="Purchase",
        amount=80,
        currency="USD",
        merchant=merchant,
        status="Approved",
    )
    plan = ResponsePlan(
        response_type="explain_status",
        outcome="explained",
        reply="El comercio confirmó la operación.",
        transaction=transaction,
    )
    fact = AllowedFact("merchant", merchant, "scoped_transaction_read")

    def answer(_s, user, _t):
        seen.append(user)
        return json.dumps(
            {
                "text": "El cargo de Quero Agora corresponde a una compra.",
                "cited_fact_ids": ["merchant"],
            }
        )

    llm = StructuredClient(
        {"phrase": ModelSpec("mock", "merchant-language")}, {}, mock_response=answer
    )
    built = build_reply(plan, language="es", facts=(fact,), client=llm)
    assert not built.used_template and not built.violations and len(seen) == 1
