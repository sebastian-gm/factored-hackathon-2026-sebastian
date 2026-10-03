"""Authored privacy-first payload and local-money recovery regressions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import BaseModel

from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.nlu.structured import understand
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec

CLOCK = datetime(2026, 6, 18, tzinfo=UTC)
LEAKS = [
    ("CO", "Mi teléfono personal es 300.123.456 COP", "300.123.456"),
    ("BR", "Meu telefone pessoal é 300.123.456 BRL", "300.123.456"),
    ("AR", "Mi DNI termina por 123456789", "123456789"),
    ("CO", "Mi cuenta es COP 123456789", "123456789"),
    ("CO", "Mi teléfono de contacto es 300.123.456", "300.123.456"),
    ("CO", "Contacta al 300.123.456", "300.123.456"),
    ("BR", "Minha conta é BRL 123456789", "123456789"),
    ("BR", "Meu CPF termina por 12345678901", "12345678901"),
    ("BR", "Entre em contato pelo 300.123.456 BRL", "300.123.456"),
    ("CL", "Mi RUT es 12.345.678-K CLP", "12.345.678-K"),
    ("CO", "Mi cédula es 123456789 COP", "123456789"),
    ("BR", "Meu número pessoal é 123456789 BRL", "123456789"),
    ("MX", "Mi tarjeta es 4111 1111 1111 1111 MXN", "4111 1111 1111 1111"),
    ("BR", "O cartão é 4111111111111111 BRL", "4111111111111111"),
    ("CO", "COP 123456789 es mi teléfono personal", "123456789"),
    ("BR", "BRL 123456789 é meu telefone pessoal", "123456789"),
    ("AR", "Mi DNI personal es $ 12.345.678", "12.345.678"),
]


def mock_client(amount: str | None, country: str, seen: list[str]) -> StructuredClient:
    def reply(_system: str, user: str, _schema: type[BaseModel]) -> str:
        seen.append(user)
        return json.dumps(
            dict(
                language="pt" if country == "BR" else "es",
                intent="charge_inquiry",
                intent_confidence=0.95,
                amount_expr=amount,
                currency_expr="BRL" if country == "BR" else "COP",
            )
        )

    return StructuredClient(
        {"nlu": ModelSpec(provider="mock", model_id="fixture")}, {}, mock_response=reply
    )


@pytest.mark.parametrize(("country", "message", "identifier"), LEAKS)
@pytest.mark.parametrize("model_amount", [None, "123456789"])
def test_identifiers_never_reach_model_or_become_amount_slots(
    country, message, identifier, model_amount
):
    seen: list[str] = []
    result = understand(
        message,
        country=country,
        bank_clock=CLOCK,
        client=mock_client(model_amount, country, seen),
    )
    assert len(seen) == 1
    assert identifier not in seen[0] and "[REDACTED]" in seen[0]
    assert result.slots.amount_value is None
    assert result.extracted.amount_expr is None
    assert result.clarification == "amount"
    assert understand(message, country=country, bank_clock=CLOCK).slots.amount_value is None


@pytest.mark.parametrize(
    ("country", "message", "expected"),
    [
        ("CO", "1000000.00 COP", "1000000.00"),
        ("CL", "1000000.00 CLP", "1000000.00"),
        ("AR", "1000000.00 ARS", "1000000.00"),
        ("MX", "1000000.00 MXN", "1000000.00"),
        ("BR", "1000000.00 BRL", "1000000.00"),
        ("CO", "$1.250.000,00", "1250000.00"),
        ("BR", "R$1.250.000,00", "1250000.00"),
    ],
)
def test_money_uses_original_privacy_filters_and_is_recovered_in_code(country, message, expected):
    seen: list[str] = []
    result = understand(
        message,
        country=country,
        bank_clock=CLOCK,
        client=mock_client("0.00", country, seen),
    )
    assert redact_for_model(message) in seen[0]
    if "1000000.00" in message:
        assert "[REDACTED]" in seen[0] and "1000000" not in seen[0]
    assert result.slots.amount_value == Decimal(expected)
    assert understand(message, country=country, bank_clock=CLOCK).slots.amount_value == Decimal(
        expected
    )


@pytest.mark.parametrize(
    ("country", "message"),
    [
        ("CO", "125 y 234 pesos"),
        ("CO", "Veo dos cargos de 125 y 234 pesos."),
        ("BR", "Vejo duas compras de 125 e 234 reais."),
        ("CO", "La compra fue de 12500000 COP y 23400000 COP."),
        ("BR", "A compra foi de 12500000 BRL e 23400000 BRL."),
    ],
)
def test_multiple_amounts_clear_even_a_model_selected_value(country, message):
    result = understand(
        message,
        country=country,
        bank_clock=CLOCK,
        client=mock_client("125", country, []),
    )
    assert result.slots.amount_value is None
    assert result.extracted.amount_expr is None
    assert result.clarification == "amount"
    assert understand(message, country=country, bank_clock=CLOCK).slots.amount_value is None


@pytest.mark.parametrize(
    "message",
    [
        "Mi teléfono personal es 300.123.456 y la compra es COP 12500000.",
        "A compra é BRL 12500000 e meu telefone pessoal é 300.123.456.",
        "El cargo de 12500000 pesos termina en mi cuenta.",
        "El número del cargo es COP 12500000.",
        "A compra é BRL 12500000 e o número termina aqui.",
    ],
)
def test_identifier_cues_anywhere_in_the_amount_clause_block_recovery(message):
    result = understand(
        message,
        country="CO",
        bank_clock=CLOCK,
        client=mock_client("12500000", "CO", []),
    )
    assert result.slots.amount_value is None
    assert result.clarification == "amount"


def test_restored_redaction_has_no_currency_exemption():
    assert "1000000" not in redact_for_model("1000000.00 COP")
    assert "300.123.456" not in redact_for_model("300.123.456 COP")
    assert "123456789" not in redact_for_model("COP 123456789")
