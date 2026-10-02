"""Independent reservations, cross-worker caps, crash exposure and least privilege."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from decimal import Decimal
from threading import Event, Lock
from time import monotonic, sleep
from uuid import uuid4

import psycopg
import pytest
from pydantic import BaseModel

from aclara.llm.client import StructuredClient
from aclara.llm.config import Price, load_prices
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
    from pathlib import Path

    from evals.program_spec import ProgramSpec

    spec = ProgramSpec("test-" + fresh, Path("authored"), "0" * 64)
    fresh = spec.scope
    prior_gate = PostgresSpendGate(store, scope=prior, run_id="fixture-run")
    prior_gate.reserve(0.10)  # Keep an unsettled exposure across preparation.
    ready = final_budget.prepare(owner, spec)
    assert ready["prior_charged_with_reserves_usd"] == 0.10
    assert ready["prior_plus_program_and_smoke_limits_usd"] == 3.20
    assert ready["attempts"] == 0
    with pytest.raises(BudgetFailure):
        prior_gate.reserve(0.001)
    current = PostgresSpendGate(store, scope=fresh, run_id=spec.run_id)
    current.reserve(2.99)
    assert final_budget.prepare(owner, spec)["charged_with_reserves_usd"] == 2.99
    with pytest.raises(BudgetFailure):
        current.reserve(0.02)
    with psycopg.connect(owner) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        connection.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (fresh,))
    with pytest.raises(RuntimeError, match="disabled"):
        final_budget.prepare(owner, spec)
    with pytest.raises(BudgetFailure):
        current.reserve(0.001)


class Answer(BaseModel):
    value: str


def test_one_client_reserves_before_parallel_network_and_keeps_exact_records(monkeypatch):
    """Simulated paid adapter only: no network, two in-flight reserves fill the cap."""
    release, two_entered, lock = Event(), Event(), Lock()
    calls = []

    class Adapter:
        def complete(self, spec, system, user, schema, key):
            with lock:
                calls.append(user)
                if len(calls) == 2:
                    two_entered.set()
            assert release.wait(5)
            return ProviderResponse(
                '{"value":"ok"}', "authored", TokenUsage(), billed_cost_usd=0.005
            )

    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("FIXTURE_MODEL_KEY", "fixture-only")
    client = StructuredClient(
        {
            "nlu": ModelSpec(
                "openai_compat",
                "authored",
                key_env="FIXTURE_MODEL_KEY",
                price_id="authored",
                max_output_tokens=10,
            )
        },
        {"authored": Price(0, 1000, 0, 0, date(2026, 10, 2), "authored")},
        budget_usd=0.02,
    )
    client._adapters["openai_compat"] = Adapter()

    def request(i):
        with client.request_records(capture_history=True):
            try:
                client.generate("nlu", "system", str(i), Answer, prompt_id=f"authored-{i}")
                assert len(client.records) == 1 and client.records[0].prompt_id == f"authored-{i}"
                return True
            except ModelFailure:
                assert not client.records
                return False

    with ThreadPoolExecutor(max_workers=10) as workers:
        futures = [workers.submit(request, i) for i in range(10)]
        try:
            assert two_entered.wait(3)
            deadline = monotonic() + 2
            while sum(f.done() for f in futures) < 8 and monotonic() < deadline:
                sleep(0.01)
            assert sum(f.done() for f in futures) == 8 and len(calls) == 2
            assert client.spent_usd == pytest.approx(0.02)
        finally:
            release.set()
        assert sum(f.result() for f in futures) == 2
    assert client.spent_usd == pytest.approx(0.01) and len(client.records) == 2


def test_previous_day_settlement_cannot_refund_a_new_days_pending_reserve(monkeypatch):
    import aclara.llm.client as module

    now = [datetime(2026, 10, 2, 23, 59, tzinfo=UTC)]

    class Clock:
        @staticmethod
        def now(tz):
            return now[0]

    entered = {key: Event() for key in ("old", "new")}
    release = {key: Event() for key in ("old", "new")}

    class Adapter:
        def complete(self, spec, system, user, schema, key):
            entered[user].set()
            assert release[user].wait(5)
            return ProviderResponse(
                '{"value":"ok"}', "authored", TokenUsage(), billed_cost_usd=0.005
            )

    monkeypatch.setattr(module, "datetime", Clock)
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("FIXTURE_MODEL_KEY", "fixture-only")
    client = StructuredClient(
        {
            "nlu": ModelSpec(
                "openai_compat",
                "authored",
                key_env="FIXTURE_MODEL_KEY",
                price_id="authored",
                max_output_tokens=10,
            )
        },
        {"authored": Price(0, 1000, 0, 0, date(2026, 10, 2), "authored")},
        budget_usd=0.02,
        daily_budget_usd=0.01,
    )
    client._adapters["openai_compat"] = Adapter()
    with ThreadPoolExecutor(max_workers=2) as workers:
        old = workers.submit(client.generate, "nlu", "system", "old", Answer, prompt_id="old")
        try:
            assert entered["old"].wait(2)
            now[0] = datetime(2026, 10, 3, tzinfo=UTC)
            new = workers.submit(client.generate, "nlu", "system", "new", Answer, prompt_id="new")
            assert entered["new"].wait(2)
            release["old"].set()
            old.result()
            with pytest.raises(ModelFailure):
                client.generate("nlu", "system", "blocked", Answer, prompt_id="blocked")
        finally:
            for event in release.values():
                event.set()
        new.result()
    assert client.spent_usd == pytest.approx(0.01)


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


def test_v4_budget_closes_v3_and_dev_preserves_reserves_and_spans_restart(
    budget_store, monkeypatch
):
    from evals.program_spec import specification
    from scripts import final_budget

    store, prior_v3, owner = budget_store
    dev = "fixture-dev-" + uuid4().hex
    with psycopg.connect(owner) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        connection.execute("INSERT INTO llm.limits VALUES(%s,1,false)", (dev,))
        connection.execute("INSERT INTO llm.runs VALUES(%s,'dev',1,true)", (dev,))
    monkeypatch.setattr(final_budget, "prior_scopes", lambda _: (prior_v3, dev))
    old = PostgresSpendGate(store, scope=prior_v3, run_id="fixture-run")
    old.reserve(0.1)
    PostgresSpendGate(store, scope=dev, run_id="dev").reserve(0.5)
    spec = specification("test-v4")
    ready = final_budget.prepare(owner, spec)
    assert ready["scope"] == "final-evaluation-v4"
    assert ready["prior_charged_with_reserves_usd"] == 0.6
    assert ready["prior_plus_program_and_smoke_limits_usd"] == 3.8
    assert ready["in_region_latency_smoke_allowance_usd"] == 0.1
    with pytest.raises(BudgetFailure):
        old.reserve(0.001)
    current = PostgresSpendGate(store, scope=spec.scope, run_id=spec.run_id)
    current.reserve(2.99)
    assert final_budget.prepare(owner, spec)["charged_with_reserves_usd"] == 2.99
    replacement = Store(os.environ["TEST_OPS_DSN"])
    try:
        restarted = PostgresSpendGate(replacement, scope=spec.scope, run_id=spec.run_id)
        with pytest.raises(BudgetFailure):
            restarted.reserve(0.02)
    finally:
        replacement.close()


def test_pre_v4_preparation_retires_prior_and_keeps_lifetime_cap_after_restart(
    budget_store, monkeypatch
):
    from scripts import pre_v4_budget

    store, prior, owner = budget_store
    fresh = "fixture-pre-v4-" + uuid4().hex
    monkeypatch.setattr(pre_v4_budget, "PRIOR_SCOPES", (prior,))
    monkeypatch.setattr(pre_v4_budget, "SCOPE", fresh)
    old = PostgresSpendGate(store, scope=prior, run_id="fixture-run")
    old.reserve(0.1)  # Unknown usage stays charged when the scope closes.
    ready = pre_v4_budget.verify(owner, prepare=True)
    assert ready["prior_charged_with_reserves_usd"] == 0.1
    assert ready["maximum_cumulative_usd"] == 5.8
    assert ready["attempts"] == 0
    with pytest.raises(BudgetFailure):
        old.reserve(0.001)
    current = PostgresSpendGate(store, scope=fresh, run_id=pre_v4_budget.RUN_ID)
    current.reserve(0.99)
    assert pre_v4_budget.verify(owner, prepare=True)["charged_with_reserves_usd"] == 0.99
    replacement = Store(os.environ["TEST_OPS_DSN"])
    try:
        restarted = PostgresSpendGate(replacement, scope=fresh, run_id=pre_v4_budget.RUN_ID)
        with pytest.raises(BudgetFailure):
            restarted.reserve(0.02)
    finally:
        replacement.close()
    with psycopg.connect(owner) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        connection.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (fresh,))
    with pytest.raises(RuntimeError, match="disabled"):
        pre_v4_budget.verify(owner, prepare=True)
    with pytest.raises(BudgetFailure):
        current.reserve(0.001)


def test_sha_bound_smoke_cap_survives_reprepare_and_cannot_reenable_breaker(budget_store):
    from scripts.release_smoke_budget import run_id, verify

    store, _, owner = budget_store
    sha = uuid4().hex + "0" * 8
    name = run_id("latency", sha)
    assert verify(owner, "latency", sha, prepare=True)["attempts"] == 0
    gate = PostgresSpendGate(store, scope="production", run_id=name)
    gate.reserve(0.0999)
    assert verify(owner, "latency", sha, prepare=True)["charged_with_reserves_usd"] == 0.0999
    with pytest.raises(BudgetFailure):
        gate.reserve(0.001)
    with psycopg.connect(owner) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        connection.execute(
            "UPDATE llm.runs SET enabled=false WHERE scope='production' AND run_id=%s", (name,)
        )
    with pytest.raises(RuntimeError, match="disabled"):
        verify(owner, "latency", sha, prepare=True)


def test_pre_v4_denied_exposure_rolls_back_closure_and_new_scope(budget_store, monkeypatch):
    from scripts import pre_v4_budget

    _, prior, owner = budget_store
    fresh = "fixture-pre-v4-denied-" + uuid4().hex
    monkeypatch.setattr(pre_v4_budget, "PRIOR_SCOPES", (prior,))
    monkeypatch.setattr(pre_v4_budget, "SCOPE", fresh)
    monkeypatch.setattr(pre_v4_budget, "CUMULATIVE_CAP", Decimal("4.19"))
    with pytest.raises(RuntimeError, match="exceeds"):
        pre_v4_budget.verify(owner, prepare=True)
    with psycopg.connect(owner) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        assert connection.execute(
            "SELECT disabled FROM llm.limits WHERE scope=%s", (prior,)
        ).fetchone() == (False,)
        assert (
            connection.execute("SELECT scope FROM llm.limits WHERE scope=%s", (fresh,)).fetchone()
            is None
        )


def test_comparison_keeps_pre_v4_open_and_never_resets_either_purse(budget_store, monkeypatch):
    from scripts import model_compare_budget, pre_v4_budget

    store, prior, owner = budget_store
    dev = "fixture-pre-v4-" + uuid4().hex
    compare = "fixture-model-compare-" + uuid4().hex
    monkeypatch.setattr(pre_v4_budget, "PRIOR_SCOPES", (prior,))
    monkeypatch.setattr(pre_v4_budget, "SCOPE", dev)
    monkeypatch.setattr(pre_v4_budget, "MODEL_COMPARE_SCOPE", compare)
    monkeypatch.setattr(model_compare_budget, "SCOPE", compare)
    pre_v4_budget.verify(owner, prepare=True)
    dev_gate = PostgresSpendGate(store, scope=dev, run_id=pre_v4_budget.RUN_ID)
    dev_gate.reserve(0.10)
    assert model_compare_budget.verify(owner, prepare=True)["attempts"] == 0
    dev_gate.reserve(0.10)  # Creating comparison must not close the other dev scope.
    compare_gate = PostgresSpendGate(store, scope=compare, run_id=model_compare_budget.RUN_ID)
    compare_gate.reserve(1.49)
    readback = model_compare_budget.verify(owner, prepare=True)
    assert readback["charged_with_reserves_usd"] == 1.49
    assert readback["pre_v4_charged_usd"] == 0.20
    replacement = Store(os.environ["TEST_OPS_DSN"])
    try:
        with pytest.raises(BudgetFailure):
            PostgresSpendGate(
                replacement, scope=compare, run_id=model_compare_budget.RUN_ID
            ).reserve(0.02)
    finally:
        replacement.close()
    with psycopg.connect(owner) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        connection.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (compare,))
    with pytest.raises(RuntimeError, match="disabled"):
        model_compare_budget.verify(owner, prepare=True)
