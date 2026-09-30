"""Authored parser regressions; not held-out rows or output-informed gold."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from aclara.agent.nlu.structured import parse_amount, parse_relative_date

CLOCK = datetime(2026, 6, 18, 6, tzinfo=UTC)


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("ciento cuarenta dólares", 140),
        ("cento e quarenta reais", 140),
        ("doscientos treinta y cuatro USD", 234),
        ("duzentos e trinta e quatro BRL", 234),
        ("ochenta y cinco dólares", 85),
        ("oitenta e cinco reais", 85),
        ("dieciséis dólares", 16),
        ("dezesseis reais", 16),
        ("mil doscientos dólares", 1200),
        ("mil e duzentos reais", 1200),
        ("veintiún mil quinientos dólares", 21500),
        ("vinte e um mil e quinhentos reais", 21500),
        ("cien USD", 100),
        ("cem reais", 100),
        ("cero dólares", 0),
        ("zero reais", 0),
    ],
)
def test_whole_spoken_amounts(expression: str, expected: int) -> None:
    assert parse_amount(expression) == Decimal(expected)


@pytest.mark.parametrize(
    "expression",
    [
        "dos compras de noventa dólares",
        "dois pagamentos de noventa reais",
        "dos o tres",
        "dois ou três",
        "ciento",
        "cento",
        "cien cincuenta",
        "cem cinquenta",
        "treinta cuarenta",
        "trinta quarenta",
        "menos veinte",
        "uns cem",
        "como cien",
        "ciento cincuenta mil millones",
        "cien cien",
        "cinco y cinco",
    ],
)
def test_ambiguous_or_malformed_words_do_not_return_partial_small_number(expression: str) -> None:
    assert parse_amount(expression) is None


@pytest.mark.parametrize(
    "expression", ["terça-feira passada", "na terça passada", "el martes pasado"]
)
def test_previous_weekday_uses_bank_business_day(expression: str) -> None:
    assert parse_relative_date(expression, CLOCK) == (date(2026, 6, 16), date(2026, 6, 16))


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("el 12 de junio", date(2026, 6, 12)),
        ("dia 12 de junho", date(2026, 6, 12)),
        ("12 de junio de 2025", date(2025, 6, 12)),
        ("12 de junho de 2025", date(2025, 6, 12)),
    ],
)
def test_stated_day_and_month_are_not_an_amount(expression: str, expected: date) -> None:
    assert parse_relative_date(expression, CLOCK) == (expected, expected)


@pytest.mark.parametrize(
    "expression", ["31 de febrero", "31 de fevereiro", "junio", "junho", "algum dia", "el martes"]
)
def test_invalid_or_unspecified_date_stays_unresolved(expression: str) -> None:
    assert parse_relative_date(expression, CLOCK) is None
