"""Cost-bearing acceptance attempts cannot overwrite evidence or reset their scope."""

import json

import pytest
from scripts.dev_gate import attempt_output


@pytest.fixture
def first_attempt(tmp_path):
    first = tmp_path / "gate-real"
    first.mkdir()
    launch = {
        "profile": "after-v2",
        "mode": "real",
        "scope": "dev-gate/after-v2",
        "run_id": "after-v2",
        "planned": 52,
        "sha": "original-candidate",
        "input_hashes": {"dev": "authored-dev-hash", "confirmation": "frozen-dev-hash"},
    }
    result = {
        "complete": True,
        "gate_passed": False,
        "sha": launch["sha"],
        "groups": {"dev": {"n": 20}, "confirmation": {"n": 20}, "faults": {"n": 12}},
    }
    (first / "launch.json").write_text(json.dumps(launch))
    (first / "results.json").write_text(json.dumps(result))
    return tmp_path, launch, result


def test_followup_preserves_first_attempt_and_cannot_repeat(first_attempt):
    root, launch, _ = first_attempt
    before = {p.name: p.read_bytes() for p in (root / "gate-real").iterdir()}
    args = dict(mode="real", profile="after-v2", attempt=2, input_hashes=launch["input_hashes"])
    output = attempt_output(root, **args)
    assert output == root / "gate-real-followup"
    output.mkdir()
    with pytest.raises(FileExistsError):
        attempt_output(root, **args)
    with pytest.raises(FileExistsError):
        attempt_output(root, **{**args, "attempt": 1})
    assert before == {p.name: p.read_bytes() for p in (root / "gate-real").iterdir()}


@pytest.mark.parametrize(
    "change", ["incomplete", "passed", "partial", "wrong_scope", "changed_inputs"]
)
def test_followup_rejects_invalid_predecessor_or_changed_inputs(first_attempt, change):
    root, launch, result = first_attempt
    hashes = dict(launch["input_hashes"])
    if change == "incomplete":
        result["complete"] = False
    elif change == "passed":
        result["gate_passed"] = True
    elif change == "partial":
        result["groups"]["confirmation"]["n"] = 19
    elif change == "wrong_scope":
        launch["scope"] = "new-allowance"
    elif change == "changed_inputs":
        hashes["confirmation"] = "edited"
    (root / "gate-real/launch.json").write_text(json.dumps(launch))
    (root / "gate-real/results.json").write_text(json.dumps(result))
    with pytest.raises(ValueError):
        attempt_output(root, mode="real", profile="after-v2", attempt=2, input_hashes=hashes)


def test_followup_does_not_enable_other_profiles_or_extra_attempts(tmp_path):
    for mode, profile, attempt in (
        ("mock", "after-v2", 2),
        ("real", "option-a", 2),
        ("real", "after-v2", 3),
    ):
        with pytest.raises(ValueError):
            attempt_output(tmp_path, mode=mode, profile=profile, attempt=attempt, input_hashes={})
