from decimal import Decimal

import pytest
from scripts.after_v2_budget import check_exposure


def test_prior_reserves_count_against_dev_and_future_v3_allowances():
    check_exposure(Decimal("3.07369789"))
    check_exposure(Decimal("8.00"))
    for prior in ("8.00000001", "-0.01", "NaN", "Infinity"):
        with pytest.raises(RuntimeError):
            check_exposure(Decimal(prior))
