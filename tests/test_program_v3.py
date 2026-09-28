"""Independent authored metadata only. Never opens a frozen suite or paid route."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from evals import program_spec


def test_preparation_checks_only_envelope_and_binding(tmp_path, monkeypatch):
    directory = tmp_path / "release"
    directory.mkdir()
    binding = tmp_path / "binding.json"
    binding.write_text('{"fixture":true}')
    binding.chmod(0o600)
    provenance = directory / "provenance.json"
    provenance.write_text(
        json.dumps({"bindings_audit": {"private_bindings_sha256": program_spec.digest(binding)}})
    )
    manifest = directory / "MANIFEST.sha256"
    manifest.write_text(
        program_spec.digest(provenance)
        + "  provenance.json\n"
        + "0" * 64
        + "  scenarios-fixture.yaml\n"
    )
    monkeypatch.setattr(program_spec, "RELEASE", directory)
    monkeypatch.setattr(program_spec, "BINDINGS", binding)
    monkeypatch.setattr(program_spec, "MANIFEST_SHA256", program_spec.digest(manifest))
    read = Path.open

    def allowed(path, *args, **kwargs):
        if path.name not in {"binding.json", "provenance.json", "MANIFEST.sha256"}:
            pytest.fail("Preparation accessed a scenario/selection")
        return read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", allowed)
    assert program_spec.verify_envelope()["binding_sha256"] == program_spec.digest(binding)
    binding.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="binding"):
        program_spec.verify_envelope()


def test_independent_preselections_are_used_without_reselecting(tmp_path):
    rows = [
        {"id": f"fixture-{i}", "category": category}
        for category, offset, count in (
            ("normal", 0, 35),
            ("ambiguous_unsupported", 35, 20),
            ("human_required", 55, 20),
            ("security_robustness", 75, 25),
        )
        for i in range(offset, offset + count)
    ]
    for i, row in enumerate(rows):
        row["language"] = "es" if i < 48 else "pt" if i < 96 else "mixed"
    repeats, judges = [r["id"] for r in rows[:30]], [r["id"] for r in rows[30:60]]
    for name, ids in (("repeat-selection.json", repeats), ("judge-selection.json", judges)):
        (tmp_path / name).write_text(json.dumps({"scenario_ids": ids}))
    assert program_spec.selections({"scenarios": rows}, tmp_path) == (set(repeats), set(judges))
    (tmp_path / "judge-selection.json").write_text(json.dumps({"scenario_ids": ["absent"] * 30}))
    with pytest.raises(ValueError, match="preselected"):
        program_spec.selections({"scenarios": rows}, tmp_path)


def test_generic_manifest_rejects_changed_payload_before_parse(tmp_path):
    (tmp_path / "scenarios-fixture.yaml").write_text("changed")
    (tmp_path / "MANIFEST.sha256").write_text(
        hashlib.sha256(b"original").hexdigest() + "  scenarios-fixture.yaml\n"
    )
    with pytest.raises(ValueError, match="checksum"):
        program_spec.load_payloads(tmp_path)


def test_v3_frontier_cannot_be_enabled_through_final_client(monkeypatch):
    from aclara.llm.final_run import client_for
    from aclara.ops.store import Store

    monkeypatch.setenv("LLM_FINAL_RUN_STARTED", "1")
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    with pytest.raises(ValueError, match="approved"):
        client_for("openrouter_sonnet", Store())


def test_v3_report_does_not_invent_frontier_or_calibration(tmp_path, monkeypatch):
    from evals import final_report, heldout_report
    from test_bound_evaluation import authored, run

    monkeypatch.setattr(final_report, "DRAWS", 10)
    monkeypatch.setattr(heldout_report, "DRAWS", 10)
    base = run(authored())
    cases = [
        {**base, "system": system, "repeat": repeat} for system, repeat, _ in program_spec.WORKLOAD
    ]
    header = {
        "workload": "authored only",
        "model": "mock",
        "implementation_sha": "fixture",
        "prompt_versions": {},
        "price_table_dates": {},
        "cost_assumptions": "zero",
        "monthly_infrastructure_estimate_usd": 0,
        "judge_planned": {"calibration": 0, "frozen": 60},
    }
    result = final_report.write_report(tmp_path, cases, [], {base["id"]}, header, {})
    assert set(result["systems"]) == {"B1", "P-Gemini"}
    assert result["judges"]["calibration"]["planned"] == 0
    assert result["judges"]["frozen"]["planned"] == 60
