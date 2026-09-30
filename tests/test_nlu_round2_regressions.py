"""Fresh authored regressions after the immutable round-two baseline."""

from datetime import UTC, date, datetime

import pytest

from aclara.agent.nlu.structured import ExtractedNlu, parse_relative_date, postprocess

CLOCK = datetime(2026, 6, 18, 6, tzinfo=UTC)


@pytest.mark.parametrize(
    "message",
    [
        "Gracias, prefiero no abrir una disputa; déjalo así, por favor.",
        "Obrigada, prefiro não abrir contestação; pode deixar como está.",
    ],
)
def test_declining_an_offer_does_not_claim_to_remember_the_purchase(message: str) -> None:
    result = postprocess(
        ExtractedNlu(
            language="pt" if message.startswith("Obrigada") else "es",
            intent="charge_inquiry",
            intent_confidence=0.95,
            recognition="recognized",
            customer_confirms="yes",
        ),
        country="BR",
        bank_clock=CLOCK,
        awaiting_recognition=True,
        message=message,
    )
    assert result.extracted.recognition == "unsure"
    assert result.extracted.customer_confirms is None


@pytest.mark.parametrize(
    "message",
    [
        "Ya me acordé, la compra era mía. Prefiero no abrir una disputa.",
        "Agora lembrei, essa compra foi minha. Prefiro não abrir contestação.",
    ],
)
def test_real_recognition_remains_recognition_when_the_customer_also_declines(message: str) -> None:
    result = postprocess(
        ExtractedNlu(
            language="pt" if message.startswith("Agora") else "es",
            intent="charge_inquiry",
            intent_confidence=0.95,
            recognition="recognized",
            customer_confirms="yes",
        ),
        country="BR",
        bank_clock=CLOCK,
        awaiting_recognition=True,
        message=message,
    )
    assert result.extracted.recognition == "recognized"


@pytest.mark.parametrize(
    ("expression", "currency", "clarification"),
    [
        ("setenta reais", "BRL", None),
        ("setenta dólares", "USD", None),
        ("setenta contos", "BRL", None),
        ("setenta lucas", None, "currency"),
    ],
)
def test_spoken_amount_units_are_not_dropped_when_currency_slot_is_missing(
    expression: str, currency: str | None, clarification: str | None
) -> None:
    result = postprocess(
        ExtractedNlu(
            language="pt",
            intent="charge_inquiry",
            intent_confidence=0.9,
            amount_expr=expression,
        ),
        country="BR",
        bank_clock=CLOCK,
    )
    assert result.slots.currency == currency
    assert result.clarification == clarification


@pytest.mark.parametrize("expression", ["el trece de mayo", "dia treze de maio"])
def test_explicit_day_in_words_is_an_exact_day_month_expression(expression: str) -> None:
    assert parse_relative_date(expression, CLOCK) == (date(2026, 5, 13), date(2026, 5, 13))


@pytest.mark.parametrize(
    "expression",
    ["treinta y dos de mayo", "trinta e dois de maio", "trece", "treze", "trece de agosto"],
)
def test_impossible_or_missing_month_or_future_without_year_remains_unresolved(
    expression: str,
) -> None:
    assert parse_relative_date(expression, CLOCK) is None
