"""Authored fixtures only: resume, pinning, aggregate metrics and blinded judge sheets."""

from __future__ import annotations

import asyncio
import csv
import json
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from evals.checkpoints import Checkpoints, exclusive
from evals.final_program import execute, human_sheet, judge_ids
from evals.final_report import write_report
from test_bound_evaluation import authored, run


def test_atomic_resume_skips_completed_and_preserves_interrupted_journal(tmp_path, monkeypatch):
    import evals.final_program as program

    scenarios = [
        dict(authored(), id=f"authored-{i}", persona={"customer_ref": "fixture"}) for i in range(2)
    ]
    from aclara.llm import final_run

    monkeypatch.setattr(final_run, "ROOT", tmp_path)
    checkpoint_root = tmp_path / "artifacts" / "fixture"
    checkpoints = Checkpoints(checkpoint_root, {"release": "authored-only"})
    calls = []

    async def interrupted(scenario, fixture, system, repeat, **kwargs):
        calls.append((scenario["id"], system, repeat))
        if len(calls) == 2:
            raise KeyboardInterrupt()
        return {"id": scenario["id"], "run_id": str(uuid4()), "repeat": repeat}

    monkeypatch.setattr(program, "bind", lambda *_: None)
    monkeypatch.setattr(program, "client_for", lambda *_, **kwargs: None)
    monkeypatch.setattr(program, "budget_receipt", lambda: {"fixture": True})
    monkeypatch.setattr(program, "execute_bound", interrupted)
    args = (
        {"scenarios": scenarios},
        {"fixture": {}},
        None,
        None,
        None,
        checkpoints,
        {"authored-0", "authored-1"},
    )
    with pytest.raises(KeyboardInterrupt):
        asyncio.run(execute(*args))
    first = checkpoints.read("B1:0:authored-0")
    assert first and checkpoints.read("B1:0:authored-1") is None
    results = asyncio.run(execute(*args))
    assert len(results) == 8 and len({r["run_id"] for r in results}) == 8
    assert results[0] == first
    assert calls.count(("authored-0", "B1", 0)) == 1
    assert results[1]["recovered_attempts"] == 1
    before = len(calls)
    assert asyncio.run(execute(*args)) == results
    assert len(calls) == before
    with pytest.raises(ValueError, match="pins differ"):
        Checkpoints(checkpoint_root, {"release": "changed"})
    with exclusive(tmp_path / "lock"), pytest.raises(BlockingIOError), exclusive(tmp_path / "lock"):
        pass


def test_final_start_gate_precedes_any_frozen_access(monkeypatch, tmp_path):
    from evals.final_program import main

    monkeypatch.delenv("LLM_FINAL_RUN_STARTED", raising=False)
    monkeypatch.setattr(Path, "iterdir", lambda *_: pytest.fail("Frozen path accessed before gate"))
    with pytest.raises(RuntimeError, match="explicit start"):
        main(tmp_path, "fixture")


def test_v3_uses_separate_paths_and_conservative_cumulative_cap():
    from scripts.final_budget import CAP, check_exposure
    from scripts.final_program import OUTPUT

    from aclara.llm.final_run import RUN_ID, SCOPE

    assert OUTPUT.name == RUN_ID == "final-program-v3"
    assert SCOPE == "final-evaluation-v3"
    assert Decimal("3.00") == CAP
    check_exposure(Decimal("3.35037557"), CAP)
    check_exposure(Decimal("8.90"), CAP)
    with pytest.raises(RuntimeError, match="ceiling"):
        check_exposure(Decimal("8.90000001"), CAP)
    with pytest.raises(RuntimeError):
        check_exposure(Decimal("NaN"), CAP)


def test_judge_selection_and_20_item_sheet_are_blinded_and_preserved(tmp_path):
    rows = [
        {"id": f"fixture-{category}-{i}", "category": category}
        for category in ("normal", "ambiguous_unsupported", "human_required", "security_robustness")
        for i in range(25)
    ]
    selected = judge_ids(rows, {r["id"] for r in rows})
    assert len(selected) == 50
    inputs = [
        {
            "sample_id": f"blind-{i}",
            "target_locale": "es-MX" if i % 2 else "pt-BR",
            "customer_message": "Pregunta de ensayo",
            "customer_reply": "Respuesta de ensayo",
            "handoff_summary": "",
            "system": "private",
            "gold": "private",
        }
        for i in range(40)
    ]
    human_sheet(tmp_path, inputs)
    path = tmp_path / "human-judge-20.csv"
    with path.open() as stream:
        sheet = list(csv.DictReader(stream))
    assert len(sheet) == 20
    assert all(not r["human_clarity"] and "system" not in r and "gold" not in r for r in sheet)
    original = path.read_text() + "\n"
    path.write_text(original)
    human_sheet(tmp_path, inputs)
    assert path.read_text() == original


def test_results_cover_protocol_and_repeated_pairs(tmp_path, monkeypatch):
    import evals.final_report as reports
    import evals.heldout_report as heldout

    monkeypatch.setattr(reports, "DRAWS", 100)
    monkeypatch.setattr(heldout, "DRAWS", 100)
    base = run(authored())
    rows = []
    for system, repeat in [("B1", 0), ("P", 0), ("P", 1), ("P", 2), ("P-Sonnet", 0)]:
        row = deepcopy(base)
        row.update(system=system, repeat=repeat, run_id=str(uuid4()), cost_usd=0.01)
        rows.append(row)
    header = {
        "workload": "authored fixture",
        "model": "mock",
        "implementation_sha": "fixture",
        "prompt_versions": {},
        "price_table_dates": {},
        "cost_assumptions": "mock",
        "monthly_infrastructure_estimate_usd": 34.63,
    }
    scores = {"language_register": 4, "clarity": 4, "empathy": 4, "handoff_usefulness": None}
    ratings = [
        {"cohort": "frozen", "sample_id": "fixture", "sonnet_scores": scores, "jev_scores": scores}
    ]
    result = write_report(tmp_path, rows, ratings, {base["id"]}, header, {"cap_usd": 12})
    assert result == json.loads((tmp_path / "results.json").read_text())
    metrics = result["systems"]["P-Gemini"]
    assert metrics["sar_in_scope"]["wilson_95"]
    assert metrics["latency"]["case"]["case_bootstrap_95"]
    assert metrics["cost"]["per_sar_bootstrap_95"]
    assert len(metrics["unsafe"]) == 8
    assert metrics["slices"]["language"]["es"]["insufficient_sample"]
    assert result["paired_comparison"]["flip_rate"]["count"] == 0
    assert result["judges"]["frozen"]["paired"] == 1
    assert "Price-table dates" in (tmp_path / "results.md").read_text()
