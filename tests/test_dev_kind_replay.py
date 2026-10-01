"""Authored alignment and input-boundary checks for the zero-call dev replay."""

from pathlib import Path

import pytest

from aclara.llm.dev_kind_replay import _matched_outputs, _source_kind, freeze


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
