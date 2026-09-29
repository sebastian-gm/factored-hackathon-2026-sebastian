"""Independent reservations, cross-worker caps, crash exposure and least privilege."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import psycopg
import pytest
from pydantic import BaseModel

from aclara.llm.client import StructuredClient
from aclara.llm.config import load_prices
from aclara.llm.types import BudgetFailure, ModelFailure, ModelSpec, ProviderResponse, TokenUsage
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import Scope, Store


@pytest.fixture
def budget_store():
    dsn, owner = os.getenv("TEST_OPS_DSN"), os.getenv("TEST_OPS_OWNER_DSN")
    if not dsn or not owner:
        pytest.skip("Disposable local Postgres required")
    scope = "fixture-" + uuid4().hex
    with psycopg.connect(owner) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        connection.execute("INSERT INTO llm.limits VALUES(%s,0.30,false)", (scope,))
        connection.execute("INSERT INTO llm.runs VALUES(%s,'fixture-run',0.10,true)", (scope,))
    store = Store(dsn)
    try:
        yield store, scope, owner
    finally:
        store.close()


def test_concurrent_clients_share_daily_cap_and_cannot_edit_policy(budget_store):
    store, scope, _ = budget_store

    def reserve(_):
        try:
            return PostgresSpendGate(store, scope=scope).reserve(0.1)
        except BudgetFailure:
            return None

    with ThreadPoolExecutor(max_workers=4) as workers:
        tokens = list(workers.map(reserve, range(12)))
    assert len([token for token in tokens if token]) == 3
    assert len(set(token for token in tokens if token)) == 3
    with store.pool.connection() as connection:
        for statement in (
            "SELECT * FROM llm.limits",
            "UPDATE llm.limits SET daily_usd=999",
            "DELETE FROM llm.reservations",
            "INSERT INTO llm.runs VALUES('production','attack',999,true)",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                connection.execute(statement)


def test_reservation_survives_rollback_restart_and_run_cap_spans_days(budget_store):
    store, scope, owner = budget_store
    gate = PostgresSpendGate(store, scope=scope, run_id="fixture-run")
    with pytest.raises(RuntimeError), store.transaction(Scope("fixture", "run", "sid")):
        token = gate.reserve(0.06)
        raise RuntimeError("request failed after external call")
    # A new pool represents a replacement worker. The prior reservation remains.
    with Store(os.environ["TEST_OPS_DSN"]).pool as pool:
        replacement = Store()
        replacement.pool = pool
        restarted = PostgresSpendGate(replacement, scope=scope, run_id="fixture-run")
        with pytest.raises(BudgetFailure):
            restarted.reserve(0.06)
        restarted.settle(token, 0.02)
        restarted.settle(token, 0.02)  # Idempotent settlement.
        with pytest.raises(BudgetFailure):
            restarted.settle(token, 0.01)
        unknown = restarted.reserve(0.07)
        restarted.settle(unknown, None)
        with pytest.raises(BudgetFailure):
            restarted.reserve(0.02)
    with psycopg.connect(owner) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        assert connection.execute(
            "SELECT sum(charged_usd) FROM llm.reservations WHERE scope=%s", (scope,)
        ).fetchone() == (Decimal("0.09"),)
        connection.execute("UPDATE llm.reservations SET day=day-1 WHERE scope=%s", (scope,))
    with pytest.raises(BudgetFailure):
        gate.reserve(0.02)  # Run cap cannot be reset by crossing midnight.
    PostgresSpendGate(store, scope=scope).reserve(0.30)  # New UTC daily allowance.


def test_unexpected_cost_disables_scope_and_unknown_scope_fails_closed(budget_store):
    store, scope, _ = budget_store
    gate = PostgresSpendGate(store, scope=scope)
    token = gate.reserve(0.01)
    with pytest.raises(BudgetFailure):
        gate.settle(token, 0.02)
    with pytest.raises(BudgetFailure):
        gate.reserve(0.01)
    with pytest.raises(BudgetFailure):
        PostgresSpendGate(store, scope="unconfigured").reserve(0.01)
    with pytest.raises(ValueError):
        PostgresSpendGate(Store())


def test_v3_preparation_closes_prior_scopes_and_never_resets_breaker(budget_store, monkeypatch):
    from scripts import final_budget

    store, prior, owner = budget_store
    fresh = "fixture-v3-" + uuid4().hex
    monkeypatch.setattr(final_budget, "PRIOR_SCOPES", (prior,))
    monkeypatch.setattr(final_budget, "SCOPE", fresh)
    prior_gate = PostgresSpendGate(store, scope=prior, run_id="fixture-run")
    prior_gate.reserve(0.10)  # Keep an unsettled exposure across preparation.
    ready = final_budget.prepare(owner)
    assert ready["prior_charged_with_reserves_usd"] == 0.10
    assert ready["prior_plus_v3_and_smoke_limits_usd"] == 3.20
    assert ready["attempts"] == 0
    with pytest.raises(BudgetFailure):
        prior_gate.reserve(0.001)
    current = PostgresSpendGate(store, scope=fresh, run_id=final_budget.RUN_ID)
    current.reserve(2.99)
    assert final_budget.prepare(owner)["charged_with_reserves_usd"] == 2.99
    with pytest.raises(BudgetFailure):
        current.reserve(0.02)
    with psycopg.connect(owner) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        connection.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (fresh,))
    with pytest.raises(RuntimeError, match="disabled"):
        final_budget.prepare(owner)
    with pytest.raises(BudgetFailure):
        current.reserve(0.001)


class Answer(BaseModel):
    value: str


def test_every_paid_attempt_reserves_before_call_and_settles(monkeypatch):
    from pathlib import Path

    events = []

    class Gate:
        def reserve(self, amount):
            assert amount > 0
            events.append("reserve")
            return "fixture-token"

        def settle(self, reservation, amount):
            assert reservation == "fixture-token"
            events.append("settle-known" if amount is not None else "settle-unknown")

    class Adapter:
        def complete(self, *args):
            assert events[-1] == "reserve"
            events.append("call")
            if events.count("call") == 1:
                raise ModelFailure("unknown billing")
            return ProviderResponse('{"value":"ok"}', "fixture", TokenUsage(10, 2))

    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("FIXTURE_MODEL_KEY", "fixture-only")
    client = StructuredClient(
        {
            "nlu": ModelSpec(
                "openai_compat", "fixture", key_env="FIXTURE_MODEL_KEY", price_id="gemini-2.5-flash"
            )
        },
        load_prices(Path("config/pricing.yaml")),
        budget_usd=None,
        spend_gate=Gate(),
    )
    client._adapters["openai_compat"] = Adapter()
    assert client.generate("nlu", "system", "fixture", Answer, prompt_id="fixture").value == "ok"
    assert events == ["reserve", "call", "settle-unknown", "reserve", "call", "settle-known"]

    class Denied(Gate):
        def reserve(self, amount):
            raise BudgetFailure("reached")

    client.spend_gate = Denied()
    with pytest.raises(BudgetFailure):
        client.generate("nlu", "system", "fixture", Answer, prompt_id="fixture")
    assert events.count("call") == 2


def test_unknown_usage_keeps_reserve_and_deadline_stops_retry(monkeypatch):
    from pathlib import Path

    clock = [0.0]
    charges = []
    calls = []

    class Gate:
        def reserve(self, amount):
            return "fixture"

        def settle(self, reservation, actual):
            charges.append(actual)

    class Adapter:
        def complete(self, spec, *args):
            calls.append(spec.timeout_seconds)
            if len(calls) == 1:
                return ProviderResponse(
                    '{"value":"ok"}', "fixture", TokenUsage(), usage_known=False
                )
            clock[0] += 46
            raise ModelFailure("fixture timeout")

    monkeypatch.setattr("aclara.llm.client.perf_counter", lambda: clock[0])
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("FIXTURE_MODEL_KEY", "fixture-only")
    client = StructuredClient(
        {
            "nlu": ModelSpec(
                "openai_compat", "fixture", key_env="FIXTURE_MODEL_KEY", price_id="gemini-2.5-flash"
            )
        },
        load_prices(Path("config/pricing.yaml")),
        budget_usd=None,
        spend_gate=Gate(),
        call_timeout_seconds=45,
    )
    client._adapters["openai_compat"] = Adapter()
    client.generate("nlu", "system", "fixture", Answer, prompt_id="fixture")
    assert client.records[0].cost_usd is None and client.spent_usd > 0
    with pytest.raises(ModelFailure, match="deadline"):
        client.generate("nlu", "system", "fixture", Answer, prompt_id="fixture")
    assert charges == [None, None] and len(calls) == 2


def test_slow_first_attempt_is_abandoned_early_and_retried_with_full_timeout(monkeypatch):
    from pathlib import Path

    timeouts = []

    class Adapter:
        def complete(self, spec, *args):
            timeouts.append(spec.timeout_seconds)
            if len(timeouts) == 1:
                raise ModelFailure("first attempt timed out")
            return ProviderResponse('{"value":"ok"}', "fixture", TokenUsage(10, 2))

    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("FIXTURE_MODEL_KEY", "fixture-only")
    client = StructuredClient(
        {
            "nlu": ModelSpec(
                "openai_compat",
                "fixture",
                key_env="FIXTURE_MODEL_KEY",
                price_id="gemini-2.5-flash",
                timeout_seconds=20,
                first_attempt_timeout_seconds=6,
            )
        },
        load_prices(Path("config/pricing.yaml")),
        budget_usd=1,
    )
    client._adapters["openai_compat"] = Adapter()
    assert client.generate("nlu", "system", "fixture", Answer, prompt_id="fixture").value == "ok"
    assert timeouts == [6, 20]
    assert [record.attempt for record in client.records] == [1, 2]
