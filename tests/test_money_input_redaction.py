"""Authored regional money inputs; identifiers never become monetary evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import BaseModel

from aclara.agent.matching import MatchState
from aclara.agent.nlg.grounding import redact_for_model, scan_dlp
from aclara.agent.nlu.structured import ExtractedNlu, postprocess, understand
from aclara.bank.repository import Transaction
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec

CLOCK = datetime(2026, 6, 18, tzinfo=UTC)
MONEY = [
    ("CO", "No reconozco el cargo de 1.250.000,00 pesos.", "1250000.00"),
    ("CO", "El cargo fue de COP 123.456.789,50.", "123456789.50"),
    ("CO", "El consumo es de 12500000 pesos.", "12500000"),
    ("CL", "No reconozco la compra de $ 2.350.000,50.", "2350000.50"),
    ("CL", "La compra fue de CLP 12500000.", "12500000"),
    ("AR", "El consumo es de 12.500.000,25 ARS.", "12500000.25"),
    ("MX", "No hice la compra de $12,500,000.25.", "12500000.25"),
    ("MX", "La compra es de MXN 12500000.", "12500000"),
    ("BR", "Não reconheço a compra de R$ 12.500.000,25.", "12500000.25"),
    ("BR", "A compra foi de 12500000 reais.", "12500000"),
    ("CO", "El consumo es de 123.456.789,50.", "123456789.50"),
    # Exact Azure smoke formatter: f'{amount:.2f} {currency}'.
    ("CO", "1000000.00 COP", "1000000.00"),
    ("CL", "1000000.00 CLP", "1000000.00"),
    ("AR", "1000000.00 ARS", "1000000.00"),
    ("MX", "1000000.00 MXN", "1000000.00"),
    ("BR", "1000000.00 BRL", "1000000.00"),
    ("CO", "12500000 COP", "12500000"),
    ("CL", "12500000 CLP", "12500000"),
    ("AR", "12500000 ARS", "12500000"),
    ("MX", "12500000 MXN", "12500000"),
    ("BR", "12500000 BRL", "12500000"),
]


@pytest.mark.parametrize(("country", "message", "expected"), MONEY)
def test_regional_money_cannot_exempt_input_digit_runs(country, message, expected):
    assert not scan_dlp(redact_for_model(message))


@pytest.mark.parametrize(("country", "message", "expected"), MONEY)
@pytest.mark.parametrize("model_amount", [None, "1.25"])
def test_raw_amount_recovery_does_not_depend_on_provider_extraction(
    monkeypatch, country, message, expected, model_amount
):
    seen = []

    def reply(_system: str, user: str, _schema: type[BaseModel]) -> str:
        seen.append(user)
        return json.dumps(
            dict(
                language="pt" if country == "BR" else "es",
                intent="charge_inquiry",
                intent_confidence=0.95,
                amount_expr=model_amount,
            )
        )

    # Even a future more restrictive provider redactor must not erase local evidence.
    monkeypatch.setattr("aclara.agent.nlu.structured.redact_for_model", lambda _: "[REDACTED]")
    client = StructuredClient(
        {"nlu": ModelSpec(provider="mock", model_id="fixture")}, {}, mock_response=reply
    )
    result = understand(message, country=country, bank_clock=CLOCK, client=client)
    assert "[REDACTED]" in seen[0] and message not in seen[0]
    assert result.slots.amount_value == Decimal(expected)
    assert result.clarification != "amount"


@pytest.mark.parametrize(("country", "message", "expected"), MONEY)
def test_rules_fallback_keeps_the_complete_amount(country, message, expected):
    result = understand(message, country=country, bank_clock=CLOCK)
    assert result.slots.amount_value == Decimal(expected)


@pytest.mark.parametrize(
    ("text", "identifier"),
    [
        ("COP 20; teléfono 3001234567", "3001234567"),
        ("Mi celular es +57 300 123 4567; el cargo fue de 20 pesos", "+57 300 123 4567"),
        ("CLP 20; mi RUT es 12.345.678-K", "12.345.678-K"),
        ("ARS 20; DNI 12.345.678", "12.345.678"),
        ("MXN 20; tarjeta 4111 1111 1111 1111", "4111 1111 1111 1111"),
        ("BRL 20; meu CPF é 123.456.789-01", "123.456.789-01"),
        ("COP 20; cédula 1.234.567.890", "1.234.567.890"),
        ("DNI 12500000 pesos", "12500000"),
        ("Teléfono 123.456.789 COP", "123.456.789"),
        ("CPF 12345678901 reais", "12345678901"),
        ("Tarjeta 4111111111111111 USD", "4111111111111111"),
        ("4111111111111111 pesos", "4111111111111111"),
        ("+55 11 91234-5678 BRL", "+55 11 91234-5678"),
        ("CPF BRL 12345678901", "12345678901"),
        ("DNI $ 12.345.678", "12.345.678"),
        ("Telefone R$ 123.456.789", "123.456.789"),
        ("Meu documento é 12500000 reais", "12500000"),
        ("+123456789 COP", "123456789"),
        ("Mi teléfono de contacto es 300.123.456", "300.123.456"),
        ("Contacta al 300.123.456", "300.123.456"),
        ("Meu telefone de contato é 300.123.456", "300.123.456"),
        ("Entre em contato pelo 300.123.456", "300.123.456"),
        ("Meu celular para contato é 300.123.456 BRL", "300.123.456"),
        ("WhatsApp de contacto: 300.123.456 COP", "300.123.456"),
        ("Llame al 300.123.456 COP", "300.123.456"),
        ("Ligue para 300.123.456 BRL", "300.123.456"),
        ("4111.1111.1111.1111 USD", "4111.1111.1111.1111"),
        ("4111.1111.1111.1111 y 234 USD", "4111.1111.1111.1111"),
    ],
)
def test_identifier_evidence_wins_over_currency_context(text, identifier):
    redacted = redact_for_model(text)
    assert identifier not in redacted and "[REDACTED]" in redacted


@pytest.mark.parametrize(
    "message",
    ["Mi DNI es 12500000 pesos", "Meu CPF é 12345678901 reais", "Teléfono 123.456.789 COP"],
)
def test_raw_recovery_never_treats_an_identifier_as_money(message):
    extracted = ExtractedNlu(language="es", intent="charge_inquiry", intent_confidence=0.9)
    assert (
        postprocess(extracted, country="CO", bank_clock=CLOCK, message=message).slots.amount_value
        is None
    )
    assert understand(message, country="CO", bank_clock=CLOCK).slots.amount_value is None


def test_two_different_amounts_are_not_collapsed_into_the_first_one():
    message = "Veo dos cargos: 12500000 pesos y 23500000 pesos."
    extracted = ExtractedNlu(language="es", intent="charge_inquiry", intent_confidence=0.9)
    assert (
        postprocess(extracted, country="CO", bank_clock=CLOCK, message=message).slots.amount_value
        is None
    )
    assert understand(message, country="CO", bank_clock=CLOCK).slots.amount_value is None


@pytest.mark.parametrize("unit", ["mil", "millones", "palos", "lucas"])
def test_numeric_unit_context_cannot_exempt_model_digit_runs(unit):
    message = f"El monto es de 12500000 {unit}."
    assert "12500000" not in redact_for_model(message)


def test_identifiers_and_amount_are_masked_and_only_separate_clause_money_is_recovered():
    message = "Mi DNI es 12.345.678; la compra fue de 12500000 pesos."
    redacted = redact_for_model(message)
    assert "12.345.678" not in redacted and "12500000" not in redacted
    assert understand(message, country="AR", bank_clock=CLOCK).slots.amount_value == Decimal(
        12500000
    )


@pytest.mark.parametrize(
    "identifier", ["3001234567", "12500000", "4111111111111111", "123.456.789-01"]
)
def test_unqualified_identifiers_still_redact(identifier):
    assert "[REDACTED]" in redact_for_model(identifier)


@pytest.mark.parametrize(
    ("country", "expression", "expected"),
    [
        ("CO", "12 mil pesos", "12000"),
        ("CO", "2 millones de pesos", "2000000"),
        ("CL", "1 millón de pesos", "1000000"),
        ("CL", "3 lucas", "3000"),
        ("CL", "2 palos", "2000000"),
        ("BR", "2 milhões de reais", "2000000"),
    ],
)
def test_raw_numeric_units_keep_their_multiplier(country, expression, expected):
    assert understand(
        f"No reconozco la compra de {expression}", country=country, bank_clock=CLOCK
    ).slots.amount_value == Decimal(expected)


def test_grouped_digits_in_a_recognized_merchant_are_not_an_amount_override():
    message = "El cargo fue de 125 en Comercio 1.234."
    extracted = ExtractedNlu(
        language="es",
        intent="charge_inquiry",
        intent_confidence=0.9,
        amount_expr="125",
        merchant_expr="Comercio 1.234",
    )
    assert postprocess(
        extracted, country="CO", bank_clock=CLOCK, message=message
    ).slots.amount_value == Decimal(125)


@pytest.mark.parametrize(
    ("country", "currency"), [("CO", "COP"), ("AR", "ARS"), ("MX", "MXN"), ("BR", "BRL")]
)
def test_raw_amount_recovery_reaches_match_like_canonical_ledger_evidence(country, currency):
    extracted = ExtractedNlu(
        language="pt" if country == "BR" else "es",
        intent="charge_inquiry",
        intent_confidence=0.95,
        merchant_expr="Comercio Modelo",
        currency_expr=currency,
        date_expr="2026-06-15",
        type_expr="compra",
    )
    message = f"La compra fue de 12.500.000,25 {currency} en Comercio Modelo."
    result = postprocess(extracted, country=country, bank_clock=CLOCK, message=message)
    day = datetime(2026, 6, 15, tzinfo=UTC)
    rows = [
        (
            f"txn_{i}",
            Transaction(
                f"authored-{i}",
                "authored-customer",
                "authored-card",
                day,
                day.date(),
                "Purchase",
                amount,
                currency,
                "Comercio Modelo",
                "Approved",
            ),
        )
        for i, amount in enumerate((12500000.25, 23500000.50), 1)
    ]
    decision = MatchState().match(result.slots, rows, "authored-customer", CLOCK)
    reference = postprocess(
        extracted.model_copy(update={"amount_expr": "12500000.25"}),
        country=country,
        bank_clock=CLOCK,
    )
    assert result.slots == reference.slots and result.slots.amount_value == Decimal("12500000.25")
    # Large same-merchant twins may still need a choice under the existing learned
    # matcher. Fix input evidence without weakening that conservative decision.
    assert decision == MatchState().match(reference.slots, rows, "authored-customer", CLOCK)


@pytest.mark.parametrize(
    "message",
    [
        "300.123.456",
        "Mi teléfono de contacto es 300.123.456",
        "Contacta al 300.123.456",
        "Meu telefone de contato é 300.123.456",
        "Contato pelo 300.123.456",
    ],
)
def test_grouped_phone_without_monetary_context_is_not_amount_evidence(message):
    redacted = redact_for_model(message)
    assert "300.123.456" not in redacted and "[REDACTED]" in redacted
    missing = ExtractedNlu(language="es", intent="charge_inquiry", intent_confidence=0.95)
    assert (
        postprocess(missing, country="CO", bank_clock=CLOCK, message=message).slots.amount_value
        is None
    )
    assert understand(message, country="CO", bank_clock=CLOCK).slots.amount_value is None


@pytest.mark.parametrize(
    ("country", "message", "first", "currency"),
    [
        ("CO", "Veo dos cargos de 125 y 234 pesos.", "125", "pesos"),
        ("BR", "Vejo duas compras de 125 e 234 reais.", "125", "reais"),
        ("CO", "125 y 234 pesos.", "125", "pesos"),
        ("BR", "125 e 234 reais.", "125", "reais"),
        ("CO", "12500000 y 23400000 pesos.", "12500000", "pesos"),
        ("BR", "12500000 e 23400000 reais.", "12500000", "reais"),
    ],
)
@pytest.mark.parametrize("selected", [True, False])
def test_shared_currency_clears_competing_model_amounts(
    country, message, first, currency, selected
):
    extracted = ExtractedNlu(
        language="pt" if country == "BR" else "es",
        intent="charge_inquiry",
        intent_confidence=0.95,
        amount_expr=first if selected else None,
        currency_expr=currency,
    )
    result = postprocess(extracted, country=country, bank_clock=CLOCK, message=message)
    assert result.slots.amount_value is None
    assert result.extracted.amount_expr is None and result.clarification == "amount"
    assert understand(message, country=country, bank_clock=CLOCK).slots.amount_value is None
    if len(first) >= 8:
        assert first not in redact_for_model(message)


@pytest.mark.parametrize(
    "message",
    [
        "El cargo de 123.456.789,50",
        "La compra fue por 123.456.789,50",
        "A cobrança é de 123.456.789,50",
        "O valor é 123.456.789,50",
        "A transação de 123.456.789,50",
        "La transacción de 123.456.789,50",
    ],
)
def test_amount_cues_allow_grouped_money_without_a_currency_code(message):
    assert "123.456.789" not in redact_for_model(message)
    assert understand(message, country="CO", bank_clock=CLOCK).slots.amount_value == Decimal(
        "123456789.50"
    )


@pytest.mark.parametrize(
    "message",
    [
        "El cargo es de 1000000.00 COP; mi teléfono de contacto es 300.123.456",
        "A compra é de 1000000.00 BRL; meu telefone de contato é 300.123.456",
    ],
)
def test_contact_and_money_are_masked_and_local_recovery_keeps_separate_clauses(message):
    redacted = redact_for_model(message)
    assert "1000000" not in redacted and "300.123.456" not in redacted
    assert understand(message, country="CO", bank_clock=CLOCK).slots.amount_value == Decimal(
        "1000000.00"
    )
