"""Preparation checks use authored scalar fixtures only, never frozen inputs."""

from decimal import Decimal

import pytest
from scripts import v5_blind_evaluation as runner
from scripts import v5_budget as budget


def test_future_cap_retains_charges_and_unused_allowance():
    assert budget.maximum(Decimal("15.76264898"), Decimal(0)) == Decimal("17.26264898")
    assert budget.maximum(Decimal("15.86264898"), Decimal(".10")) == Decimal("17.26264898")
    for prior, charged in [("17", "0"), ("NaN", "0"), ("-1", "0"), ("15", "1.51")]:
        with pytest.raises(RuntimeError):
            budget.maximum(Decimal(prior), Decimal(charged))


def test_no_suite_merged_go_blocks_before_git_or_frozen_reads(monkeypatch):
    monkeypatch.delenv("V5_SUITE_MERGED_GO", raising=False)
    monkeypatch.setattr(runner.subprocess, "check_output", lambda *a, **k: pytest.fail("git read"))
    with pytest.raises(RuntimeError, match="suite merged GO"):
        runner.implementation()


def test_paired_primary_sar_uses_scope_not_workload_denominator():
    b1 = [
        {"id": "authored.a", "in_scope": True, "sar": False},
        {"id": "authored.b", "in_scope": False, "sar": False},
    ]
    p = [{**c, "sar": c["in_scope"]} for c in b1]
    result = runner.paired(b1, p)
    assert result["n"] == 2 and result["in_scope_n"] == 1
    assert result["difference"] == 1 and result["paired_95"] == [1, 1]
    assert result["bootstrap_draws"] == 10000 and result["seed"] == 20261001
    with pytest.raises(ValueError):
        runner.paired(b1, p[:-1])
