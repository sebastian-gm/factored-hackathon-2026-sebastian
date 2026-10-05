"""Authored approval boundaries; no suite, provider or Azure access."""

from decimal import Decimal
from uuid import uuid4

import pytest
from scripts import final_day_budget as budget


def test_approved_full_new_allowances_fit_without_releasing_reserves():
    assert sum(budget.SCOPES.values()) == Decimal(".70")
    assert Decimal("14.91264898") + sum(budget.SCOPES.values()) < budget.CEILING == Decimal(18)
    assert budget.remaining(Decimal(".30"), Decimal(".02")) == Decimal(".28")
    for bad in ("NaN", "Infinity", "-.01", ".30000001"):
        with pytest.raises(RuntimeError):
            budget.remaining(Decimal(".30"), Decimal(bad))


def test_preparation_is_idempotent_and_cannot_reenable(budget_store, monkeypatch):
    import psycopg

    from aclara.llm.types import BudgetFailure
    from aclara.ops.budget import PostgresSpendGate

    store, owner = budget_store
    scope = "authored-final-day-" + uuid4().hex
    monkeypatch.setattr(budget, "SCOPES", {scope: Decimal(".30")})
    monkeypatch.setattr(budget, "receipt", lambda _: {"maximum_usd": "15.61"})
    assert budget.verify(owner, prepare=True) == budget.verify(owner, prepare=True)
    gate = PostgresSpendGate(store, scope=scope, run_id=budget.RUN_ID)
    token = gate.reserve(0.25)
    budget.verify(owner, prepare=True)
    with pytest.raises(BudgetFailure):
        gate.reserve(0.06)
    with psycopg.connect(owner) as db:
        db.execute("SET LOCAL ROLE aclara_owner")
        db.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (scope,))
    with pytest.raises(RuntimeError, match="disabled"):
        budget.verify(owner, prepare=True)
    with psycopg.connect(owner) as db:
        db.execute("SET LOCAL ROLE aclara_owner")
        assert db.execute(
            "SELECT settled,charged_usd FROM llm.reservations WHERE id=%s", (token,)
        ).fetchone() == (False, Decimal(".25"))


@pytest.fixture
def budget_store():
    import os

    import psycopg

    from aclara.ops.store import Store

    app, owner = os.getenv("TEST_OPS_DSN"), os.getenv("TEST_OPS_OWNER_DSN")
    if not app or not owner:
        pytest.skip("Disposable Postgres required")
    with psycopg.connect(owner) as db:
        db.execute("SET LOCAL ROLE aclara_owner")
        old = db.execute("SELECT daily_usd FROM llm.limits WHERE scope='production'").fetchone()[0]
        db.execute("UPDATE llm.limits SET daily_usd=1 WHERE scope='production'")
    store = Store(app)
    try:
        yield store, owner
    finally:
        store.close()
        with psycopg.connect(owner) as db:
            db.execute("SET LOCAL ROLE aclara_owner")
            db.execute("UPDATE llm.limits SET daily_usd=%s WHERE scope='production'", (old,))
