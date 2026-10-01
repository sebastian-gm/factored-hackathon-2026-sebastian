"""Authored ES/PT prose regressions; no evaluation rows or paid calls."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from aclara.agent.contracts import ResponsePlan, TransactionView
from aclara.agent.nlg.builder import build_reply
from aclara.agent.nlg.grounding import AllowedFact, verify_draft
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec


def status_fact(status: str = "Approved") -> AllowedFact:
    return AllowedFact("status", status, "scoped_transaction_read")


def test_reported_digit_and_english_status_leak_is_rejected() -> None:
    verdict = verify_draft("La operaci3n figura como approved.", ["status"], (status_fact(),))
    assert not verdict.safe
    assert {"text_corruption", "unlocalized_enum"} <= set(verdict.violations)


@pytest.mark.parametrize(
    "identifier",
    [
        "awaiting_dispute_decision",
        "offer_dispute",
        "choose_transaction",
        "handoff_created",
        "dispute_proposed",
        "NEW_MACHINE_STATE",
        "pending_authorization",
        "_awaiting_dispute_decision",
        "_handoff__created_",
    ],
)
@pytest.mark.parametrize("language", ["es", "pt"])
def test_machine_identifiers_are_rejected_even_when_cited(identifier: str, language: str) -> None:
    text = f"El estado es {identifier}." if language == "es" else f"O status é {identifier}."
    fact = AllowedFact("state", identifier, "code_approved_state")
    for citations, facts in [([], ()), (["state"], (fact,))]:
        verdict = verify_draft(text, citations, facts)
        assert not verdict.safe and "unlocalized_enum" in verdict.violations


def test_all_response_contract_literals_are_internal_prose() -> None:
    properties = ResponsePlan.model_json_schema()["properties"]
    literals = set(properties["response_type"]["enum"]) | set(properties["outcome"]["enum"])
    for literal in literals:
        verdict = verify_draft(f"El estado es {literal}.", [], ())
        assert not verdict.safe, literal


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize(
    ("name", "fact_id"),
    [("Approved", "status"), ("Pending", "status"), ("Purchase", "transaction_type")],
)
def test_status_or_type_citation_cannot_authorize_a_same_named_merchant(
    language: str,
    name: str,
    fact_id: str,
) -> None:
    facts = (
        AllowedFact("merchant", name, "scoped_transaction_read"),
        AllowedFact(fact_id, name, "scoped_transaction_read"),
    )
    text = f"El cargo de {name}." if language == "es" else f"A cobrança em {name}."
    verdict = verify_draft(text, [fact_id], facts, known_merchants=(name,))
    assert not verdict.safe and "uncited_merchant" in verdict.violations


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("name", ["Approved", "Pending", "Purchase"])
def test_same_named_english_merchant_is_valid_with_its_own_citation(
    language: str, name: str
) -> None:
    facts = (AllowedFact("merchant", name, "scoped_transaction_read"), status_fact())
    text = (
        f"El cargo de {name} está aprobado."
        if language == "es"
        else f"A cobrança em {name} está aprovada."
    )
    assert verify_draft(text, ["merchant", "status"], facts, known_merchants=(name,)).safe


def test_merchant_citation_is_required_without_a_separate_known_names_list() -> None:
    facts = (AllowedFact("merchant", "Approved", "scoped_transaction_read"), status_fact())
    verdict = verify_draft("El cargo de Approved.", ["status"], facts)
    assert not verdict.safe and "uncited_merchant" in verdict.violations


def test_a_cited_merchant_without_provenance_cannot_exempt_an_english_enum() -> None:
    verdict = verify_draft(
        "El cargo de Approved.", ["merchant"], (AllowedFact("merchant", "Approved", ""),)
    )
    assert {"missing_source", "unlocalized_enum"} <= set(verdict.violations)


@pytest.mark.parametrize(
    "draft",
    [
        "La operaci3n está aprobada.",
        "A transa3ção está aprovada.",
        "A informa4ção está correta.",
        "El movimien7to está aprobado.",
        "A transa'#o está aprovada.",
    ],
)
def test_corrupted_words_fail_even_when_the_claimed_status_is_cited(draft: str) -> None:
    verdict = verify_draft(draft, ["status"], (status_fact(),))
    assert not verdict.safe and "text_corruption" in verdict.violations


@pytest.mark.parametrize("status", ["Approved", "Pending", "Declined", "Reversed"])
@pytest.mark.parametrize("opening", ["La operación figura como", "A transação aparece como"])
def test_raw_status_is_rejected_with_a_valid_citation(status: str, opening: str) -> None:
    verdict = verify_draft(f"{opening} {status}.", ["status"], (status_fact(status),))
    assert not verdict.safe and "unlocalized_enum" in verdict.violations


@pytest.mark.parametrize("enum", ["Purchase", "Processing", "DISPUTE_FILED", "offer_dispute"])
def test_related_english_or_machine_enums_are_not_customer_prose(enum: str) -> None:
    fact = AllowedFact("type", enum, "scoped_transaction_read")
    verdict = verify_draft(f"El resultado es {enum}.", ["type"], (fact,))
    assert not verdict.safe and "unlocalized_enum" in verdict.violations


@pytest.mark.parametrize("merchant", ["Studio3D", "B2B Market", "L0ja3D", "Pending Coffee"])
@pytest.mark.parametrize("language", ["es", "pt"])
def test_exact_cited_merchant_amount_date_and_case_reference_remain_valid(
    merchant: str,
    language: str,
) -> None:
    facts = (
        AllowedFact("merchant", merchant, "scoped_transaction_read"),
        AllowedFact("amount", "145.50", "scoped_transaction_read"),
        AllowedFact("transaction_date", "2026-06-12T00:00:00Z", "scoped_transaction_read"),
        AllowedFact("case_id", "DSP-A3B-27", "verified_case_read"),
        AllowedFact("card_suffix", "XXXX1234XXXX", "scoped_product_read"),
        status_fact(),
    )
    text = (
        f"El cargo de {merchant}, USD 145.50 del 12 jun 2026, está aprobado. "
        "Tarjeta XXXX1234XXXX; caso DSP-A3B-27."
        if language == "es"
        else f"A cobrança em {merchant}, USD 145,50 de 12 jun 2026, está aprovada. "
        "Cartão XXXX1234XXXX; caso DSP-A3B-27."
    )
    assert verify_draft(text, [f.id for f in facts], facts, known_merchants=(merchant,)).safe


def test_known_but_uncited_merchant_cannot_hide_corruption() -> None:
    fact = AllowedFact("merchant", "Studio3D", "scoped_transaction_read")
    verdict = verify_draft("El cargo de Studio3D.", [], (fact,), known_merchants=(fact.value,))
    assert not verdict.safe and "uncited_merchant" in verdict.violations


def test_merchant_exemption_does_not_hide_separate_corruption_or_english_status() -> None:
    fact = AllowedFact("merchant", "Studio3D", "scoped_transaction_read")
    verdict = verify_draft(
        "La operaci3n de Studio3D figura como approved.",
        ["merchant", "status"],
        (fact, status_fact()),
    )
    assert {"text_corruption", "unlocalized_enum"} <= set(verdict.violations)


def test_merchant_named_like_status_does_not_exempt_the_status_claim() -> None:
    fact = AllowedFact("merchant", "Approved", "scoped_transaction_read")
    assert verify_draft(
        "El cargo de Approved está pendiente.",
        ["merchant", "status"],
        (fact, status_fact("Pending")),
    ).safe
    verdict = verify_draft(
        "El cargo de Approved figura como approved.",
        ["merchant", "status"],
        (fact, status_fact()),
    )
    assert not verdict.safe and "unlocalized_enum" in verdict.violations


@pytest.mark.parametrize("language", ["es", "pt"])
def test_related_enum_inputs_are_localized_and_source_facts_stay_canonical(language: str) -> None:
    seen: list[str] = []
    facts = (
        AllowedFact("transaction_type", "Purchase", "scoped_transaction_read"),
        AllowedFact("status", "FutureEnum", "scoped_transaction_read"),
    )

    def answer(_system, context, _schema):
        seen.append(context)
        return json.dumps(
            {
                "text": "Puedes revisar el cargo."
                if language == "es"
                else "Você pode revisar a cobrança.",
                "cited_fact_ids": [],
            }
        )

    client = StructuredClient(
        {"phrase": ModelSpec("mock", "authored-enum-review")}, {}, mock_response=answer
    )
    plan = ResponsePlan(response_type="clarify", outcome="clarification", reply="")
    built = build_reply(plan, language=language, facts=facts, client=client)
    assert not built.used_template
    context = json.loads(seen[0].partition("<response_plan>")[2].partition("</response_plan>")[0])
    assert context["facts"] == [
        {"id": "transaction_type", "value": "compra"},
        {"id": "status", "value": "no disponible" if language == "es" else "indisponível"},
    ]
    assert facts[0].value == "Purchase" and facts[1].value == "FutureEnum"


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize(
    ("status", "localized"),
    [
        ("Approved", ("aprobada", "aprovada")),
        ("Pending", ("pendiente", "pendente")),
        ("Declined", ("rechazada", "recusada")),
        ("Reversed", ("reversada", "estornada")),
    ],
)
def test_phrase_receives_utf8_localized_status_and_bad_drafts_fall_back(
    language: str,
    status: str,
    localized: tuple[str, str],
) -> None:
    seen: list[dict[str, object]] = []
    labels = localized[0 if language == "es" else 1]
    approved = f"La operación está {labels}." if language == "es" else f"A transação está {labels}."
    bad = (
        f"La operaci3n figura como {status}."
        if language == "es"
        else f"A transa3ção está {status}."
    )
    txn = TransactionView(
        handle="txn_27",
        transaction_date=datetime(2026, 6, 12, tzinfo=UTC),
        transaction_type="Purchase",
        amount=145.50,
        currency="USD",
        merchant="Studio3D",
        status=status,
    )
    plan = ResponsePlan(
        response_type="explain_status", outcome="explained", reply=approved, transaction=txn
    )

    def answer(_system, context, _schema):
        raw = context.partition("<response_plan>")[2].partition("</response_plan>")[0]
        seen.append(json.loads(raw.encode("utf-8").decode("utf-8")))
        return json.dumps({"text": bad, "cited_fact_ids": ["status"]})

    client = StructuredClient(
        {"phrase": ModelSpec("mock", "authored-enum-review")}, {}, mock_response=answer
    )
    result = build_reply(plan, language=language, facts=(status_fact(status),), client=client)
    assert seen[0]["facts"] == [{"id": "status", "value": labels}]
    assert seen[0]["approved_text"] == approved  # proper accents survive JSON/UTF-8 roundtrip
    assert result.used_template and result.plan.reply == approved
    assert {"text_corruption", "unlocalized_enum"} <= set(result.violations)
    assert len(client.records) == 2
