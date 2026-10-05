"""Authored runner observations; never open v4 inputs or official outputs."""

import asyncio
import json

import pytest
from evals.checkpoints import Checkpoints
from scripts.final_build_regression import FLAGGED, LABEL, summarize, unit


def test_flagged_subset_and_safety_report_are_independent_of_case_prose():
    rows = [
        {
            "id": "v4.019",
            "system": "P",
            "passed": False,
            "unsafe": {"reported_not_verified": True},
            "forbidden_observed": ["report_unverified_action"],
            "cost_usd": 0.001,
        },
        {
            "id": "authored-other",
            "system": "P",
            "passed": True,
            "unsafe": {},
            "forbidden_observed": [],
            "cost_usd": 0.002,
        },
    ]
    report = summarize(rows)
    assert len(FLAGGED) == 8
    assert report["label"] == LABEL
    assert report["systems"]["P"]["all"]["passed"] == 1
    assert report["systems"]["P"]["flagged_subset"]["safety_gates"]["reported_not_verified"] == 1
    assert report["systems"]["P"]["all"]["model_cost_usd"] == "0.003"
    assert set(report["systems"]["P"]["all"]) == {
        "cases",
        "passed",
        "safety_gates",
        "forbidden_predicates",
        "failed_ids",
        "model_cost_usd",
    }


def test_resume_reuses_completed_unit_and_accumulates_interrupted_costs(tmp_path):
    checkpoints = Checkpoints(tmp_path, {"release": "authored"})
    calls = []

    async def execute(path):
        calls.append(path)
        path.write_text(json.dumps({"call": {"cost_usd": 0.001}}) + "\n")
        if len(calls) == 1:
            raise InterruptedError("authored interruption")
        return {"passed": True}

    with pytest.raises(InterruptedError):
        asyncio.run(unit(checkpoints, "authored", execute))
    result = asyncio.run(unit(Checkpoints(tmp_path, {"release": "authored"}), "authored", execute))
    assert result["cost_usd"] == 0.002
    assert asyncio.run(unit(checkpoints, "authored", execute)) == result
    assert len(calls) == 2
    assert checkpoints.directory("authored").joinpath("result.json").stat().st_mode & 0o777 == 0o600


def test_unknown_cost_stops_without_claiming_a_completed_case(tmp_path):
    checkpoints = Checkpoints(tmp_path, {"release": "authored"})

    async def execute(path):
        path.write_text(json.dumps({"call": {"cost_usd": None}}) + "\n")
        return {"passed": True}

    with pytest.raises(RuntimeError, match="Unknown cost"):
        asyncio.run(unit(checkpoints, "authored", execute))
    assert checkpoints.read("authored") is None
