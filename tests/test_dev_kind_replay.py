"""Authored alignment and input-boundary checks for the zero-call dev replay."""

import json
import os
import stat
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from evals.studies.llm import dev_kind_replay
from evals.studies.llm.dev_kind_replay import _matched_outputs, _source_kind, freeze


@pytest.fixture
def permissive_umask() -> Iterator[None]:
    previous = os.umask(0)
    try:
        yield
    finally:
        os.umask(previous)


@pytest.mark.usefixtures("permissive_umask")
def test_frozen_baseline_is_created_owner_only(tmp_path: Path) -> None:
    source = tmp_path / "final-program-v3"
    source.mkdir()
    target = tmp_path / "baseline.json"
    freeze([source], target)
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert json.loads(target.read_text())["cases"] == []


@pytest.mark.usefixtures("permissive_umask")
def test_cli_report_is_created_owner_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Exercise the actual CLI writer with an authored comparison; no dev data.
    package_file = tmp_path / "evals/studies/llm/dev_kind_replay.py"
    monkeypatch.setattr(dev_kind_replay, "__file__", str(package_file))
    monkeypatch.setattr(
        dev_kind_replay, "compare", lambda _path: {"cost_usd": 0, "private_details": []}
    )
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    baseline, report = artifacts / "baseline.json", artifacts / "report.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["dev_kind_replay", "compare", "--baseline", str(baseline), "--report", str(report)],
    )
    dev_kind_replay.main()
    assert stat.S_IMODE(report.stat().st_mode) == 0o600
    assert json.loads(report.read_text())["cost_usd"] == 0


def test_private_writer_keeps_existing_snapshot_intact(tmp_path: Path) -> None:
    target = tmp_path / "existing.json"
    target.write_text("authored frozen bytes")
    with pytest.raises(FileExistsError):
        dev_kind_replay._write_private_json(target, {"replacement": True})
    assert target.read_text() == "authored frozen bytes"


def test_private_writer_sets_owner_rights_under_restrictive_umask(tmp_path: Path) -> None:
    target = tmp_path / "private.json"
    previous = os.umask(0o777)
    try:
        dev_kind_replay._write_private_json(target, {"authored": True})
    finally:
        os.umask(previous)
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert json.loads(target.read_text()) == {"authored": True}


def test_alignment_uses_current_generation_despite_repeated_call_events() -> None:
    calls = {
        "old": {"output": {"type_expr": "compra"}},
        "current": {"output": {"type_expr": "saque"}},
    }
    events = [
        {"event": "llm_call", "route": "nlu", "status": "valid", "generation_id": "old"},
        {"event": "nlu", "degraded": False},
        {"event": "match", "action": "choose"},
        # Runtime emits earlier call records again, followed by the current call.
        {"event": "llm_call", "route": "nlu", "status": "valid", "generation_id": "old"},
        {"event": "llm_call", "route": "nlu", "status": "valid", "generation_id": "current"},
        {"event": "nlu", "degraded": False},
        {"event": "match", "action": "propose"},
        {"event": "llm_call", "route": "nlu", "status": "model_failure"},
        {"event": "nlu", "degraded": True},
        {"event": "match", "action": "abstain"},
    ]
    matched = _matched_outputs(events, calls)
    assert matched == [
        {"output": {"type_expr": "compra"}, "recorded_action": "choose"},
        {"output": {"type_expr": "saque"}, "recorded_action": "propose"},
    ]


def test_replay_rejects_unapproved_source_before_reading(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="retired"):
        freeze([tmp_path / "unapproved-suite"], tmp_path / "baseline.json")


def test_replay_never_overwrites_a_frozen_baseline(tmp_path: Path) -> None:
    target = tmp_path / "baseline.json"
    target.write_text("authored freeze")
    with pytest.raises(ValueError, match="never overwrite"):
        freeze([], target)
    assert target.read_text() == "authored freeze"


@pytest.mark.parametrize(
    ("path", "name"),
    [
        ("artifacts/final-program-v3", "v3-primary"),
        ("artifacts/nlu-robustness-post-v3/after", "robust40-after"),
        ("artifacts/dev-pre-v4/round2-real/before", "robust60-before"),
    ],
)
def test_replay_names_only_explicit_retired_dev_directories(path: str, name: str) -> None:
    assert _source_kind(Path(path)) == name
