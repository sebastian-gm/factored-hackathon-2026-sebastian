"""Authored budget/checkpoint tests; never read suites, bindings or provider credentials."""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from evals.checkpoints import Checkpoints
from scripts import post_v5_budget
from scripts.final_build_regression import unit


def test_retired_budget_keeps_charges_and_unused_new_cap_in_one_conservative_total(monkeypatch):
    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, sql, params=()):
            if sql.startswith("SELECT daily_usd"):
                row = (
                    (Decimal("1.50"), True)
                    if params[0] == post_v5_budget.V5_SCOPE
                    else (Decimal(".80"), False)
                )
            elif sql.startswith("SELECT run_id"):
                rows = (
                    [(post_v5_budget.V5_RUN, Decimal("1.50"), False)]
                    if params[0] == post_v5_budget.V5_SCOPE
                    else [(post_v5_budget.RUN_ID, Decimal(".80"), True)]
                )
                return SimpleNamespace(fetchall=lambda: rows)
            elif sql.startswith("SELECT count"):
                row = (2, Decimal(".10"), 1)
            else:
                row = None
            return SimpleNamespace(fetchone=lambda: row)

    monkeypatch.setattr(post_v5_budget.psycopg, "connect", lambda _: Connection())
    monkeypatch.setattr(
        post_v5_budget,
        "final_day_receipt",
        lambda _: {"maximum_usd": "16", "unknown_reservations": 75},
    )
    values = {
        post_v5_budget.SCOPE: Decimal(".30"),
        post_v5_budget.V5_SCOPE: Decimal(".32"),
        "live-exploration/v0.9.9": Decimal(".08"),
    }
    monkeypatch.setattr(post_v5_budget, "usage", lambda _, scope, run: values[scope])
    result = post_v5_budget.verify("authored")
    assert result["conservative_maximum_usd"] == "16.57"
    assert result["retired_unused_v5_usd"] == "1.18"
    assert result["unknown_cost_attempts"] == 1
    assert result["retained_historical_unknown_reservations"] == 75
    values[post_v5_budget.SCOPE] = Decimal(".81")
    with pytest.raises(RuntimeError):
        post_v5_budget.verify("authored")


def test_cached_replay_does_not_repeat_provider_calls(tmp_path):
    import asyncio

    async def check():
        calls = 0
        checkpoints = Checkpoints(tmp_path, {"sha": "authored"})

        async def execute(_):
            nonlocal calls
            calls += 1
            return {"passed": True}

        first = await unit(checkpoints, "authored", execute)
        assert first == await unit(checkpoints, "authored", execute)
        assert calls == 1 and first["cost_usd"] == 0

    asyncio.run(check())
