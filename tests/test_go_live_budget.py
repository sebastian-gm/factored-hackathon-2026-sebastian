"""Authored durable purses only; no model or Azure requests."""

from decimal import Decimal
from uuid import uuid4

import psycopg
import pytest
from scripts import go_live_budget as budget

from aclara.llm.types import BudgetFailure


def test_lane_names_and_total():
    assert sum(budget.LANE_CAPS.values()) == Decimal(".60")
    assert budget.lane_scope("ai") == "go-live/2026-10-03/ai"
    with pytest.raises(ValueError):
        budget.lane_scope("browser-supplied")


def test_lane_reservation_before_call_survives_restart_and_cannot_reset(budget_store, monkeypatch):
    store, scope, owner = budget_store
    monkeypatch.setattr(budget, "lane_scope", lambda _: scope)
    monkeypatch.setattr(budget, "DAY", "fixture-run")
    gate = budget.lane_gate(store, "lead")
    token = gate.reserve(0.06)
    # No HTTP call can proceed when its maximum cannot fit; unknowns remain held.
    with pytest.raises(BudgetFailure):
        budget.lane_gate(store, "lead").reserve(0.06)
    gate.settle(token, 0.01)
    next_token = gate.reserve(0.08)
    gate.settle(next_token, None)
    with pytest.raises(BudgetFailure):
        gate.reserve(0.02)
    with psycopg.connect(owner) as db:
        db.execute("SET LOCAL ROLE aclara_owner")
        assert db.execute(
            "SELECT sum(charged_usd) FROM llm.reservations WHERE scope=%s", (scope,)
        ).fetchone() == (Decimal(".09"),)


@pytest.fixture
def budget_store():
    import os

    from aclara.ops.store import Store

    app, owner = os.getenv("TEST_OPS_DSN"), os.getenv("TEST_OPS_OWNER_DSN")
    if not app or not owner:
        pytest.skip("Disposable Postgres required")
    scope = "authored-go-live-" + uuid4().hex
    with psycopg.connect(owner) as db:
        db.execute("SET LOCAL ROLE aclara_owner")
        db.execute("INSERT INTO llm.limits VALUES(%s,.10,false)", (scope,))
        db.execute("INSERT INTO llm.runs VALUES(%s,'fixture-run',.10,true)", (scope,))
    store = Store(app)
    try:
        yield store, scope, owner
    finally:
        store.close()


def test_verified_call_settlement_retains_unknown_and_never_uses_shared_deltas():
    class Gate:
        def __init__(self):
            self.values = []

        def settle(self, token, value):
            self.values.append((token, value))

    gate = Gate()
    assert budget.settle_calls(
        gate, "authored", [{"cost_usd": 0.005}, {"cost_usd": 0.001}]
    ) == Decimal(".006")
    assert gate.values == [("authored", 0.006)]
    assert budget.settle_calls(gate, "zero", []) == 0
    with pytest.raises(RuntimeError, match="retained"):
        budget.settle_calls(gate, "unknown", [{"cost_usd": None}])
    assert gate.values[-1] == ("unknown", None)


def test_prepare_preserves_reserves_and_refuses_reenable(budget_store, monkeypatch):
    store, fixture_scope, owner = budget_store
    monkeypatch.setattr(budget, "allocation", lambda *_: {"maximum_usd": "14.96"})
    monkeypatch.setattr(budget, "LANE_CAPS", {"lead": Decimal(".10")})
    monkeypatch.setattr(budget, "lane_scope", lambda _: fixture_scope)
    monkeypatch.setattr(budget, "DAY", "fixture-run")
    monkeypatch.setattr(budget, "JUDGING_RUN", "authored-judging-" + uuid4().hex)
    sha = uuid4().hex + "0" * 8
    assert budget.prepare(owner, sha)["lanes"]["lead"]["cap_usd"] == "0.10"
    token = budget.lane_gate(store, "lead").reserve(0.09)
    assert budget.prepare(owner, sha)["maximum_usd"] == "14.96"
    with pytest.raises(BudgetFailure):
        budget.lane_gate(store, "lead").reserve(0.02)
    with psycopg.connect(owner) as db:
        db.execute("SET LOCAL ROLE aclara_owner")
        db.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (fixture_scope,))
    with pytest.raises(RuntimeError, match="disabled"):
        budget.prepare(owner, sha)
    # Unknown reserve was not removed or settled by re-preparation.
    with psycopg.connect(owner) as db:
        db.execute("SET LOCAL ROLE aclara_owner")
        assert db.execute(
            "SELECT settled,charged_usd FROM llm.reservations WHERE id=%s", (token,)
        ).fetchone() == (False, Decimal(".09"))
