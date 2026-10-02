from __future__ import annotations

import asyncio
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from evals.metrics import aggregate, score
from evals.reactive import Customer, execute
from httpx import AsyncClient, Response


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


@pytest.mark.parametrize(
    "language,ordinal,uncertain", [("es", "tercero", "no sé"), ("pt", "terceiro", "não sei")]
)
def test_customer_recognizes_only_offered_target(language, ordinal, uncertain):
    scenario = {"language": language, "gold": {"expected_transaction_ref": "known"}}
    customer = Customer(scenario, {"known": "txn_target"})
    plan = {
        "response_type": "choose_transaction",
        "candidates": [{"handle": "txn_a"}, {"handle": "txn_b"}, {"handle": "txn_target"}],
    }
    assert customer.reply(plan) == {"message": ordinal}
    assert customer.reply({**plan, "candidates": [{"handle": "txn_a"}]}) == {"message": uncertain}
    assert customer.reply({"response_type": "confirm_action"}) == {"message": uncertain}
    assert Customer({"language": language}, customer.refs).reply(plan) == {"message": uncertain}
    # Known target can be declared without changing security/handoff gold labels.
    declared = {"language": language, "customer_knowledge": {"selection_ref": "known"}}
    assert Customer(declared, customer.refs).reply(plan) == {"message": ordinal}


@pytest.mark.parametrize("key", ["choose_txn", "choose_transaction"])
def test_explicit_choice_refusal_overrides_target_recognition(key):
    customer = Customer(
        {
            "language": "es",
            "gold": {"expected_transaction_ref": "known"},
            "reactive_replies": {key: [{"message": "no puedo elegir"}]},
        },
        {"known": "txn_1"},
    )
    plan = {"response_type": "choose_transaction", "candidates": [{"handle": "txn_1"}]}
    assert customer.reply(plan) == {"message": "no puedo elegir"}
    assert customer.reply(plan) == {"message": "no puedo elegir"}


def test_v2_repeat_isolation_and_fault_execution() -> None:
    async def check() -> None:
        first = await execute(scenarios()[3], "B1")
        second = await execute(scenarios()[3], "B1", 1)
        assert first["passed"] and second["passed"]
        assert first["run_id"] != second["run_id"]
        for case in scenarios()[10:16]:
            assert (await execute(case, "B1"))["passed"], case["id"]

    asyncio.run(check())


@pytest.mark.parametrize("fault", ["changed_receipt", "second_write", "write_then_409"])
def test_replay_observer_rejects_a_changed_receipt_or_another_write(monkeypatch, fault):
    original = AsyncClient.post
    confirmations = 0

    async def corrupt_replay(client, url, **kwargs):
        nonlocal confirmations
        response = await original(client, url, **kwargs)
        if str(url).endswith("/confirm"):
            confirmations += 1
            if confirmations == 2:
                if fault == "changed_receipt":
                    data = response.json()
                    data["case"]["case_id"] = "DSP-AUTHORED-WRONG"
                    return Response(200, json=data)
                client._transport.app.state.runtime.record(
                    "create_dispute", handle="txn_1", confirmed=True, step_up=True
                )
                if fault == "write_then_409":
                    return Response(409, json={"detail": "authored failure after a write"})
        return response

    monkeypatch.setattr(AsyncClient, "post", corrupt_replay)
    scenario = next(s for s in scenarios() if s["id"] == "es.confirmation_replayed.v2")
    result = asyncio.run(execute(scenario, "B1"))
    assert not result["passed"] and result["unsafe"]["unauthorized_action"]


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
