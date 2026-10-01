"""Authored cumulative-cap boundaries; no keys, provider or suite access."""

from decimal import Decimal

import pytest
from scripts.release_smoke_budget import check_exposure


def test_current_exposure_matches_the_existing_shared_dev_preflight():
    total = Decimal("6.99994254")
    dev = Decimal("0.87148777")
    assert check_exposure(total, dev) == Decimal("11.82845477")
    # More dev reservations move within its existing full $1 allowance. They
    # are still charged and do not expand the $12 maximum or reset history.
    assert check_exposure(total + Decimal(".02"), dev + Decimal(".02")) == Decimal("11.82845477")


def test_unknown_dev_reserves_count_with_the_same_full_cap_as_known_charges():
    # The caller uses charged_usd, including unknowns, never sum(actual_usd).
    assert check_exposure(Decimal("7.00"), Decimal("1.00")) == Decimal("11.70")
    # Historical/comparison/production exposure is never removed as dev spend.
    with pytest.raises(RuntimeError, match="exceeds approval"):
        check_exposure(Decimal("7.01"), Decimal(".50"))


@pytest.mark.parametrize("dev", [Decimal("0"), Decimal(".50"), Decimal("1")])
def test_exact_ceiling_passes_and_one_cent_above_is_denied(dev):
    assert check_exposure(Decimal("6.30") + dev, dev) == Decimal("12.00")
    with pytest.raises(RuntimeError, match="exceeds approval"):
        check_exposure(Decimal("6.31") + dev, dev)


@pytest.mark.parametrize(
    "total,dev",
    [
        ("NaN", "0"),
        ("Infinity", "0"),
        ("0", "NaN"),
        ("0", "Infinity"),
        ("-1", "0"),
        ("1", "-.01"),
        ("1", "1.01"),
        (".50", ".51"),
    ],
)
def test_invalid_or_overspent_dev_exposure_fails_closed(total, dev):
    with pytest.raises(RuntimeError, match="Invalid"):
        check_exposure(Decimal(total), Decimal(dev))
