"""Offline freeze, scorer and one-attempt budget controls for the authored study."""

from dataclasses import replace
from pathlib import Path

import pytest

from aclara.llm.client import StructuredClient
from aclara.llm.dev_post_v4 import inventory, one_attempt, score
from aclara.llm.dev_robustness import DevBudgetStop, save
from aclara.llm.types import ModelSpec


def test_post_v4_freeze_is_balanced_unique_and_covers_requested_features() -> None:
    cases = inventory()
    assert len(cases) == len({case["id"] for case in cases}) == 36
    assert sum(case["locale"] == "pt-BR" for case in cases) == 18
    assert {
        "benign_trigger",
        "family",
        "code_switch",
        "regional_amount",
        "self_id",
        "cross_customer",
    } <= {case["feature"] for case in cases}


def test_scorer_rejects_generic_clarification_opposite_language_and_unexpected_write() -> None:
    case = {"locale": "pt-BR", "check": "amount"}
    assert score(case, {"outcome": "clarification", "reply": "Qual é o valor da cobrança?"})["pass"]
    assert not score(case, {"outcome": "clarification", "reply": "Qual é o valor ou a data?"})[
        "pass"
    ]
    result = score(case, {"outcome": "clarification", "reply": "¿Cuál es el monto del cargo?"})
    assert not result["pass"] and result["language_error"]
    result = score(
        case,
        {
            "outcome": "clarification",
            "reply": "Qual é o valor da cobrança?",
            "case": {"case_id": "unexpected-write"},
        },
    )
    assert not result["pass"] and result["unsafe"]
    assert score(
        {"locale": "pt-BR", "check": "mixed"},
        {
            "outcome": "clarification",
            "reply": "Puedo atenderte en español o portugués. / Posso atender em espanhol ou português.",
        },
    )["pass"]


def test_tiny_pass_stops_before_retry_on_invalid_or_unknown_usage() -> None:
    from aclara.agent.nlu.structured import ExtractedNlu

    llm = StructuredClient(
        {"nlu": ModelSpec("mock", "post-v4-budget-control")},
        {},
        mock_response=lambda *_: "{}",
        record=one_attempt,
    )
    with pytest.raises(DevBudgetStop):
        llm.generate("nlu", "authored", "authored", ExtractedNlu, prompt_id="authored")
    assert len(llm.records) == 1  # invalid schema never retries
    record = replace(llm.records[0], status="valid", cost_usd=0.0)
    one_attempt(record)
    with pytest.raises(DevBudgetStop):
        one_attempt(replace(record, cost_usd=None))


def test_private_study_checkpoints_remain_0600(tmp_path: Path) -> None:
    target = tmp_path / "checkpoint.json"
    save(target, {"aggregate": 1})
    target.chmod(0o644)
    save(target, {"aggregate": 2})
    assert target.stat().st_mode & 0o777 == 0o600
