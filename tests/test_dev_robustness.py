"""No-network protection for the authored freeze and shared durable threshold."""

from contextlib import contextmanager
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from aclara.llm.dev_robustness import (
    DevBudgetStop,
    ThresholdGate,
    canonical_freeze,
    check_reserve,
    money,
)
from aclara.llm.dev_robustness_cases import validate


def test_authored_freeze_remains_structurally_valid() -> None:
    assert validate()["n"] == 40


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1])
def test_invalid_cost_cannot_reserve(value: float) -> None:
    with pytest.raises(DevBudgetStop):
        money(value)


def test_round_up_and_threshold() -> None:
    assert money(0.000000001) == Decimal("0.00000001")
    check_reserve(Decimal("0.89"), Decimal("0.01"))
    with pytest.raises(DevBudgetStop):
        check_reserve(Decimal("0.89"), Decimal("0.01000001"))


class FakeConnection:
    def __init__(self, charged: Decimal):
        self.charged = charged
        self.queries: list[str] = []
        self.params: list[Any] = []
        self.committed = False

    @contextmanager
    def transaction(self):
        yield
        self.committed = True

    def execute(self, query: str, params: Any = None):
        self.queries.append(query)
        self.params.append(params)
        result = (True,)
        if "daily_usd" in query:
            result = (Decimal("1"), False)
        elif "limit_usd" in query:
            result = (Decimal("1"), True)
        elif "sum(charged_usd)" in query:
            result = (self.charged,)
        elif "llm.reserve" in query:
            result = (uuid4(),)
        return FakeRow(result)


class FakeRow:
    def __init__(self, result: Any):
        self.result = result

    def fetchone(self):
        return self.result


def test_threshold_under_scope_lock_commits_before_call() -> None:
    connection: Any = FakeConnection(Decimal("0.88"))
    assert ThresholdGate(connection).reserve(0.01)
    assert connection.committed
    assert "FOR UPDATE" in connection.queries[1]
    assert "llm.reserve" in connection.queries[-1]


def test_shared_threshold_denial_never_calls_reserve() -> None:
    connection: Any = FakeConnection(Decimal("0.899"))
    with pytest.raises(DevBudgetStop):
        ThresholdGate(connection).reserve(0.01)
    assert not any("llm.reserve" in q for q in connection.queries)


def test_pre_v4_reservations_use_only_approved_scope_and_run() -> None:
    connection: Any = FakeConnection(Decimal("0"))
    gate = ThresholdGate(connection, scope="dev-gate/pre-v4", run_id="pre-v4")
    reservation = gate.reserve(0.01)
    assert connection.params[1] == ("dev-gate/pre-v4",)
    assert connection.params[2] == ("dev-gate/pre-v4", "pre-v4")
    assert connection.params[3] == ("dev-gate/pre-v4",)
    assert connection.params[4] == ("dev-gate/pre-v4", "pre-v4", Decimal("0.01"))
    gate.settle(reservation, None)
    assert connection.params[-1][1] is None  # unknown usage keeps the durable reserve


def test_json_saved_freeze_histogram_remains_equal_without_editing_fixture_bytes() -> None:
    report = {"cases_sha256": "unchanged", "scripted_messages": {3: 42, 4: 18}}
    saved = {"cases_sha256": "unchanged", "scripted_messages": {"3": 42, "4": 18}}
    assert canonical_freeze(report) == saved
    assert canonical_freeze(saved) == saved
