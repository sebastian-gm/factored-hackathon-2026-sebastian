"""Authored budget arithmetic only; no suite or provider reads."""

from decimal import Decimal

import pytest
from evals.program_spec import specification
from scripts import final_budget, pre_v4_budget


def test_pre_v4_reserves_both_smokes_and_future_v4_in_cumulative_cap():
    pre_v4_budget.check_exposure(Decimal("4.54283516"))
    pre_v4_budget.check_exposure(Decimal("7.80"))
    for prior in ("7.80000001", "-0.01", "NaN", "Infinity"):
        with pytest.raises(RuntimeError):
            pre_v4_budget.check_exposure(Decimal(prior))


def test_final_preparation_closes_pre_v4_and_counts_both_smoke_caps():
    assert pre_v4_budget.SCOPE in final_budget.prior_scopes(specification("test-v4"))
    assert pre_v4_budget.SCOPE not in final_budget.prior_scopes(specification("test-v3"))
    final_budget.check_exposure(Decimal("8.80"), final_budget.CAP, smoke_allowance=Decimal(".20"))
    with pytest.raises(RuntimeError):
        final_budget.check_exposure(
            Decimal("8.80000001"), final_budget.CAP, smoke_allowance=Decimal(".20")
        )
