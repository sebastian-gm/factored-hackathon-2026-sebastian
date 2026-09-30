"""No-network protection for the authored freeze and shared durable threshold."""

from contextlib import contextmanager
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from aclara.llm.dev_robustness import DevBudgetStop, ThresholdGate, check_reserve, money
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
        self.committed = False

    @contextmanager
    def transaction(self):
        yield
        self.committed = True

    def execute(self, query: str, params: Any = None):
        self.queries.append(query)
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
