"""Saved-metadata replay uses authored fixtures, no held-out rows or provider."""

from copy import deepcopy

import pytest
from evals.studies.llm.jev_live_replay import replay

from aclara.llm.typesafe_questions import RISK_CUES


def fixture(cue: str) -> dict:
    raw = dict.fromkeys(RISK_CUES, False)
    return {
        "id": "authored.saved",
        "repeat": 0,
        "system": "P",
        "passed": False,
        "outcome": "refused_security",
        "route_checks": {"language": False},
        "events": [
            {"event": "llm_call", "route": "nlu"},
            {
                "event": "llm_call",
                "route": "nlu_risk_second_opinion",
                "cost_usd": 0.0000042,
                "judgments": {"gemini_raw_flags": raw, "union_flags": {**raw, cue: True}},
            },
        ],
    }


def test_injection_only_addition_does_not_change_routing_reason_list():
    result = replay([fixture("injection_suspected")])
    assert result["nlu_and_risk_calls"] == 2 and result["paired_risk_records"] == 1
    assert result["changed_union_records"] == 1 and result["calls_in_changed_pairs"] == 2
    assert result["changed_routing_reason_lists"] == 0
    assert result["observed_primary_passes"] == 0
    assert result["affected_metadata"][0]["saved_route_language_correct"] is False
    assert result["known_jev_risk_cost_usd"] == 0.0000042


def test_replay_exposes_an_actual_routing_change_without_inventing_passes():
    result = replay([fixture("lost_stolen")])
    assert result["changed_routing_reason_lists"] == 1
    assert result["observed_primary_passes"] == 0


def test_duplicate_attempt_and_result_fail_instead_of_double_counting():
    row = fixture("injection_suspected")
    with pytest.raises(ValueError, match="Duplicate"):
        replay([row, deepcopy(row)])


def test_missing_raw_flags_are_not_assumed_to_be_negative():
    row = fixture("injection_suspected")
    del row["events"][1]["judgments"]["gemini_raw_flags"]["legal"]
    with pytest.raises(ValueError, match="Complete boolean"):
        replay([row])
