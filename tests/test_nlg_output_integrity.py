"""New authored regressions for customer prose; no saved evaluation rows."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from aclara.agent.contracts import ResponsePlan, TransactionView
from aclara.agent.nlg.builder import build_reply
from aclara.agent.nlg.grounding import AllowedFact, scan_dlp, verify_draft
from aclara.agent.nlu.rules import detect_language_evidence
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec


def transaction() -> TransactionView:
    return TransactionView(
        handle="txn_27",
        transaction_date=datetime(2026, 6, 12, tzinfo=UTC),
        transaction_type="Purchase",
        amount=40,
        currency="USD",
        merchant="Comercio de Prueba",
        status="Approved",
    )


def client(text: str, fact_ids: list[str]) -> StructuredClient:
    return StructuredClient(
        {"phrase": ModelSpec("mock", "authored-output-integrity")},
        {},
        mock_response=lambda _s, _u, _t: json.dumps({"text": text, "cited_fact_ids": fact_ids}),
    )


@pytest.mark.parametrize("handle", ["txn_27", "prod_4", "card_19", "cust_8", "TXN_27"])
def test_internal_handles_are_forbidden_even_with_valid_fact_citation(handle: str) -> None:
    fact = AllowedFact("handle", handle, "scoped_transaction_read")
    draft = f"La referencia interna es {handle}."
    assert "internal_handle" in scan_dlp(draft)
    verdict = verify_draft(draft, [fact.id], (fact,))
    assert not verdict.safe and "internal_handle" in verdict.violations


@pytest.mark.parametrize(
    "draft",
    [
        "Entendo sua preocupa'#o.",
        "Entiendo tu preocupaci\ufffdn.",
        "La operaciÃ³n estÃ¡ lista.",
        "A informaÃ§Ã£o estÃ¡ disponÃ­vel.",
        "Revisa el cargoâ€™s.",
        "Tu consulta est\x01 lista.",
    ],
)
def test_corrupted_customer_text_is_rejected_without_a_language_dependency(draft: str) -> None:
    assert "text_corruption" in scan_dlp(draft)
    assert not verify_draft(draft, [], ()).safe


@pytest.mark.parametrize(
    "draft",
    [
        "¿Cómo va tu solicitud? Entiendo tu preocupación.",
        "Entendo sua preocupação. Você pode revisar a cobrança.",
        "Ângelo, a informação está disponível. NÃO precisamos de mais dados.",
        "Mensaje en dos líneas.\nPuedes revisarlo.\tGracias.",
    ],
)
def test_valid_es_pt_accents_and_whitespace_are_not_corruption(draft: str) -> None:
    assert "text_corruption" not in scan_dlp(draft)


@pytest.mark.parametrize(
    ("language", "approved", "draft"),
    [
        (
            "es",
            "El comercio confirmó el cargo.",
            "Você pode revisar a cobrança e falar com o estabelecimento.",
        ),
        (
            "pt",
            "O estabelecimento confirmou a cobrança.",
            "Puedes revisar el cargo y hablar con el comercio.",
        ),
    ],
)
def test_phrase_v2_and_language_guard_reject_confident_opposite_language(
    language: str, approved: str, draft: str
) -> None:
    assert detect_language_evidence(draft) != language
    plan = ResponsePlan(
        response_type="clarify",
        outcome="clarification",
        reply="",
        transaction=transaction(),
    )
    result = build_reply(plan, language=language, country="AR", client=client(draft, []))
    assert result.used_template and result.plan.reply != draft
    assert "language_mismatch" in result.violations


@pytest.mark.parametrize(
    ("draft", "fact_ids", "facts", "violation"),
    [
        (
            "El cargo tiene referencia txn_27.",
            ["handle"],
            (AllowedFact("handle", "txn_27", "scoped_transaction_read"),),
            "internal_handle",
        ),
        ("Entiendo tu preocupa'#o.", [], (), "text_corruption"),
    ],
)
def test_bad_model_drafts_retry_then_fall_back_to_clean_approved_reply(
    draft: str, fact_ids: list[str], facts: tuple[AllowedFact, ...], violation: str
) -> None:
    plan = ResponsePlan(
        response_type="clarify",
        outcome="clarification",
        reply="",
        transaction=transaction(),
    )
    llm = client(draft, fact_ids)
    result = build_reply(plan, language="es", facts=facts, client=llm)
    assert result.used_template and result.plan.reply != draft
    assert violation in result.violations
    assert len(llm.records) == 2


def test_approved_reply_is_also_checked_even_without_a_model() -> None:
    plan = ResponsePlan(
        response_type="clarify", outcome="clarification", reply="Revisa el producto prod_4."
    )
    with pytest.raises(ValueError, match="sensitive content"):
        build_reply(plan, language="es")


def test_verified_customer_case_reference_remains_allowed() -> None:
    fact = AllowedFact("case_id", "DSP-TEST-27", "verified_case_read")
    assert verify_draft("Consulta el caso DSP-TEST-27.", [fact.id], (fact,)).safe
