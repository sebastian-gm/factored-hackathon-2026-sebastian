from __future__ import annotations

import asyncio
from copy import deepcopy
from pathlib import Path

import yaml
from evals.metrics import aggregate, score
from evals.reactive import Customer, execute


def scenarios() -> list[dict]:
    return yaml.safe_load(Path("evals/dev_scenarios_v2.yaml").read_text())["scenarios"]


def test_customer_reacts_to_plan_and_exhausts_deterministically() -> None:
    customer = Customer(
        {
            "language": "pt",
            "reactive_replies": {
                "ask_amount": [{"message": "80"}],
                "choose_txn": [{"choose_ref": "target"}],
            },
        },
        {"target": "txn_2"},
    )
    assert customer.reply({"type": "ask_amount"}) == {"message": "80"}
    assert customer.reply({"type": "ask_amount"}) == {"message": "80"}
    assert customer.reply(
        {
            "response_type": "choose_transaction",
            "candidates": [{"handle": "txn_1"}, {"handle": "txn_2"}],
        }
    ) == {"message": "segundo"}
    assert customer.reply({"type": "unknown"}) == {"message": "não sei"}


def test_v2_repeat_isolation_and_fault_execution() -> None:
    async def check() -> None:
        first = await execute(scenarios()[3], "B1")
        second = await execute(scenarios()[3], "B1", 1)
        assert first["passed"] and second["passed"]
        assert first["run_id"] != second["run_id"]
        for case in scenarios()[10:16]:
            assert (await execute(case, "B1"))["passed"], case["id"]

    asyncio.run(check())


def test_gold_denominators_and_unsafe_scoring_are_independent() -> None:
    async def check() -> None:
        normal = await execute(scenarios()[3], "B1")
        human = await execute(scenarios()[5], "B1")
        incorrect = deepcopy(normal)
        incorrect["gold"]["expected_transaction_ref"] = "txn_2"
        incorrect = score(incorrect)
        assert incorrect["unsafe"]["materially_incorrect_outcome"]
        assert not incorrect["sar"]
        unverified = deepcopy(normal)
        unverified["readback"] = False
        assert score(unverified)["unsafe"]["reported_not_verified"]
        report = aggregate([normal, human, incorrect], {})
        assert report["sar_in_scope"]["count"] == 1
        assert report["sar_in_scope"]["denominator"] == 3
        assert report["sar_eligible"]["denominator"] == 2
        assert report["escalation_recall"]["rate"] == 1
        assert report["unsafe"]["materially_incorrect_outcome"]["count"] == 1
        assert report["unsafe"]["unauthorized_disclosure"]["upper_95"] == 1
        assert report["latency"]["case"]["p95_ms"] > 0

    asyncio.run(check())


def test_eval_gold_never_imports_policy() -> None:
    import ast

    for path in Path("evals").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("aclara.policy")
            if isinstance(node, ast.Import):
                assert all(not alias.name.startswith("aclara.policy") for alias in node.names)
