"""Authored regressions for deterministic fallback identification."""

from datetime import UTC, date, datetime

import pytest

from aclara.agent.selection import candidates
from aclara.bank.repository import Transaction


def row(handle: str, amount: float, merchant: str) -> tuple[str, Transaction]:
    return handle, Transaction(
        handle,
        "fixture-customer",
        "fixture-card",
        datetime(2026, 6, 10, tzinfo=UTC),
        date(2026, 6, 10),
        "Purchase",
        amount,
        "USD",
        merchant,
        "Approved",
    )


@pytest.mark.parametrize("blank", ["", " "])
def test_blank_merchant_does_not_corrupt_amount_or_numeric_merchant_match(blank):
    rows = [row("target", 80, "Tienda 123"), row("blank", 15, blank), row("blank2", 20, "")]
    selected, needs_choice = candidates(
        "Quiero consultar un cargo de 80.00 USD en Tienda 123 el 2026-06-10", rows
    )
    assert [handle for handle, _ in selected] == ["target"]
    assert not needs_choice


def test_blank_merchant_does_not_supply_positive_identification():
    selected, needs_choice = candidates("No reconozco un cargo", [row("blank", 15, "")])
    assert len(selected) == 1
    assert needs_choice  # A sole scoped row is not permission to propose it.
