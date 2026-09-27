from __future__ import annotations

import asyncio
from copy import deepcopy

import pytest
from evals.reactive import execute
from scripts.dev_gate import DevBudgetStop, DevSpendGate, mock_client, summarize
from test_evaluation import scenarios

from aclara.llm.types import BudgetFailure


@pytest.mark.parametrize("system", ["B1", "P"])
def test_explicit_no_choice_fixture_hands_off_without_write(system):
    # Authored dev fixture: the customer cannot recognize any offered charge,
    # even though it has a known reference. This must override generic selection.
    scenario = deepcopy(next(s for s in scenarios() if s["id"] == "es.exhausted.v2"))
    scenario["turns"] = [{"message": "No hice una compra de 250 dólares"}]
    scenario["customer_knowledge"] = {"selection_ref": "fixture-txn-003"}
    scenario["reactive_replies"]["choose_txn"] = [{"message": "no puedo elegir"}]
    result = asyncio.run(
        execute(scenario, system, llm_client=mock_client() if system == "P" else None)
    )
    assert result["passed"]
    assert result["responses"][0]["response_type"] == "choose_transaction"
    assert result["outcome"] == "escalated"
    assert not any(e["event"] in {"create_dispute", "freeze_card"} for e in result["events"])


def test_unreached_fault_is_failed_with_trace_when_diagnosing():
    scenario = deepcopy(scenarios()[0])
    scenario["faults"] = [{"type": "confirmation_tampered", "trigger": "confirm_action"}]
    result = asyncio.run(execute(scenario, "B1", require_faults=False))
    assert result["responses"]
    assert result["faults_declared"] == 1 and result["faults_fired"] == 0
    assert result["execution_error"] == "unreached_fault"
    assert not result["passed"]
    with pytest.raises(ValueError, match="unreached"):
        asyncio.run(execute(scenario, "B1"))


def test_budget_failure_is_hard_stop_and_never_reset():
    class Denied:
        def reserve(self, amount_usd):
            raise BudgetFailure("denied")

        def settle(self, reservation, actual_usd):
            raise BudgetFailure("unavailable")

    gate = DevSpendGate(Denied())
    with pytest.raises(DevBudgetStop):
        gate.reserve(0.01)
    with pytest.raises(DevBudgetStop):
        gate.settle("opaque-reservation", None)


def test_incomplete_or_mock_gate_cannot_pass():
    assert not summarize([], False)["gate_passed"]
    assert not summarize([], True)["gate_passed"]
