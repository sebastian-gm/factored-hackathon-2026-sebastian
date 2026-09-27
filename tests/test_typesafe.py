"""Offline TypeSafe typed-judgment and shared-budget checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from typesafe_sdk import SystemOneResponse, TypeSafeClient

from aclara.llm.typesafe import TypeSafeAdapter, _normalize
from aclara.llm.typesafe_questions import INTENT_LABELS, RISK_CUES, judge_questions, nlu_questions
from aclara.llm.typesafe_report import expected_calibration_error


def test_typesafe_adapter_accepts_typed_answers_and_usage_only() -> None:
    response = SystemOneResponse.model_validate(
        {
            "model": "jev-1.13.0",
            "usage": {"input_tokens": 1000, "output_tokens": 8},
            "answers": {
                "intent": {
                    "type": "choice",
                    "choice": "dispute_charge",
                    "confidence": 0.75,
                    "probabilities": {"dispute_charge": 0.8, "charge_inquiry": 0.2},
                },
                "injection_suspected": {"type": "noul", "noul": 0.1},
                "clarity": {
                    "type": "score",
                    "score": 2.5,
                    "confidence": 0.5,
                    "legend": {2: "understandable", 3: "clear"},
                    "probabilities": {2: 0.5, 3: 0.5},
                },
            },
        }
    )
    result = _normalize(response, 12.0)
    assert result.choices["intent"].choice == "dispute_charge"
    assert result.nouls["injection_suspected"] == 0.1
    assert result.scores["clarity"].score == 2.5
    assert result.cost_usd == pytest.approx(0.000042)
    assert result.latency_ms == 12.0
    with pytest.raises(ValueError, match="different model"):
        _normalize(response.model_copy(update={"model": "unplanned-model"}), 12.0)


def test_typesafe_questions_match_reviewed_intents_and_subjective_rubric() -> None:
    questions = nlu_questions()
    assert set(questions) == {"intent", *RISK_CUES}
    assert set(questions["intent"].criteria) == set(INTENT_LABELS)
    assert set(judge_questions(has_handoff=True)) == {
        "language_register",
        "clarity",
        "empathy",
        "handoff_usefulness",
    }
    assert set(judge_questions(has_handoff=False)) == {
        "language_register",
        "clarity",
        "empathy",
    }
    assert all(
        len(question.criteria) == 5 for question in judge_questions(has_handoff=True).values()
    )
    adapter = TypeSafeAdapter(cast(TypeSafeClient, object()))
    with pytest.raises(ValueError, match="typed judgment"):
        adapter.ask({"customer_message": "synthetic"}, {})


def test_ece_and_cross_vendor_cap_are_deterministic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from aclara.llm import typesafe_eval

    assert expected_calibration_error([(0.9, True), (0.9, False)]) == pytest.approx(0.4)
    paths = {name: tmp_path / f"{name}.json" for name in typesafe_eval.CHECKPOINTS}
    monkeypatch.setattr(typesafe_eval, "CHECKPOINTS", paths)
    paths["baseline"].write_text(
        json.dumps(
            {
                "observations": [
                    {"attempts": [{"provider": "openrouter", "cost_usd": 0.941}]},
                    {"attempts": [{"provider": "typesafe", "cost_usd": None}]},
                ]
            }
        ),
        encoding="utf-8",
    )
    known, unknown, guarded = typesafe_eval.exposure()
    assert (known, unknown, guarded) == pytest.approx((0.941, 1, 0.951))
    with pytest.raises(RuntimeError, match="cap"):
        typesafe_eval._budget("baseline")
