"""Authored runner fixtures only; never read frozen releases or provider keys."""

from __future__ import annotations

import json
from pathlib import Path

import psycopg
import pytest
from evals import final_program, program_spec, rehearsal
from evals.checkpoints import Checkpoints
from scripts.final_program import error_metadata

from aclara.llm.final_run import FinalBudgetStop
from aclara.llm.types import BudgetFailure


@pytest.fixture
def spec(tmp_path, monkeypatch):
    monkeypatch.setattr(program_spec, "ROOT", tmp_path)
    monkeypatch.setenv("LLM_REHEARSAL_APPROVED", "1")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "0")
    monkeypatch.delenv("LLM_FINAL_RUN_STARTED", raising=False)
    return program_spec.specification("test-v3", rehearsal="authored")


def test_rehearsal_is_separate_local_and_cannot_read_blind_suite(spec, monkeypatch):
    monkeypatch.setattr(Path, "open", lambda *a, **k: pytest.fail("Frozen read"))
    assert spec.scope == "rehearsal/final-program/authored"
    assert spec.output.parent.name == "final-program-rehearsal"
    rehearsal.guard(spec)
    for suite, name in [("test-v4", "authored"), ("test-v3", "../escape"), ("test-v3", "a" * 41)]:
        with pytest.raises(ValueError):
            program_spec.specification(suite, rehearsal=name)
    for dsn in [
        "host=azure.example user=aclara_app",
        "host=127.0.0.1 user=postgres",
        "host=127.0.0.1 hostaddr=203.0.113.1 user=aclara_app",
    ]:
        with pytest.raises(ValueError):
            rehearsal.local(dsn)
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    with pytest.raises(RuntimeError):
        rehearsal.guard(spec)


def cases():
    return [
        dict(
            id=f"authored-{i}",
            system="B1",
            repeat=0,
            dialect="es-MX",
            judge_input=dict(
                target_locale="es-MX",
                customer_message="Consulta de ensayo",
                customer_reply="Respuesta de ensayo",
                handoff_summary="",
            ),
        )
        for i in range(3)
    ]


def test_length_failure_is_checkpointed_unpaired_and_not_replayed(spec, tmp_path, monkeypatch):
    from evals.final_report import judge_report

    from aclara.llm import final_run

    monkeypatch.setattr(final_run, "ROOT", tmp_path)
    monkeypatch.setattr(final_program, "budget_receipt", lambda *_: {"cap_usd": 0})
    points = Checkpoints(spec.output, {"authored": True})
    created = []
    original = rehearsal.client

    def client(path, spec, **kwargs):
        result = original(path, spec, **kwargs, truncate=len(created) == 1)
        created.append(result)
        return result

    monkeypatch.setattr(
        rehearsal,
        "client",
        lambda path, spec, **kw: client(path, spec, has_handoff=kw["has_handoff"]),
    )
    monkeypatch.setattr(final_program, "client_for", lambda *a, **k: pytest.fail("Paid judge"))
    rows = cases()
    selected = {r["id"] for r in rows}
    ratings = final_program.judges(rows, selected, points, None, spec)
    assert [r["status"] for r in ratings] == ["scored", "judge_failed", "scored"]
    assert ratings[1]["sonnet_scores"] is None and ratings[1]["jev_scores"] is None
    assert ratings[1]["length_failures"] == 2
    assert ratings[1]["attempt_statuses"] == ["refusal", "refusal"]
    assert all(
        c.spent_usd == 0 and next(iter(c.models.values())).max_output_tokens == 1024
        for c in created
    )
    assert judge_report(ratings, {"calibration": 0, "frozen": 3})["frozen"]["paired"] == 2
    assert final_program.judges(rows, selected, points, None, spec) == ratings
    assert len(created) == 3


@pytest.mark.parametrize(
    "error",
    [
        FinalBudgetStop("fixture"),
        BudgetFailure("fixture"),
        psycopg.OperationalError("private text"),
    ],
)
def test_budget_and_connectivity_errors_stop_without_fabricating_rating(
    spec, tmp_path, monkeypatch, error
):
    from aclara.llm import final_run

    monkeypatch.setattr(final_run, "ROOT", tmp_path)
    monkeypatch.setattr(rehearsal, "score_pair", lambda *_: (_ for _ in ()).throw(error))
    points = Checkpoints(spec.output, {"authored": True})
    with pytest.raises((FinalBudgetStop, BudgetFailure, RuntimeError)):
        final_program.judges(cases(), {"authored-0"}, points, None, spec)
    assert not list(spec.output.glob("checkpoints/*/result.json"))


def test_stop_metadata_never_contains_exception_input_values():
    outer = RuntimeError("private scenario text")
    outer.__cause__ = psycopg.OperationalError("private connection string")
    assert error_metadata(outer) == {
        "error_type": "RuntimeError",
        "cause_types": ["OperationalError"],
    }
    assert "private" not in json.dumps(error_metadata(outer))


def test_connectivity_is_not_claimed_as_budget_denial(spec, monkeypatch):
    class Gate:
        def __init__(self, *a, **k):
            pass

        def reserve(self, amount):
            raise BudgetFailure("not a cap refusal") from psycopg.OperationalError("offline")

    monkeypatch.setattr(rehearsal, "PostgresSpendGate", Gate)
    with pytest.raises(BudgetFailure):
        rehearsal.budget_denial(spec, None)


def test_objective_projection_keeps_safety_cost_and_intervals():
    from scripts.rehearse_final_program import objective

    value = {
        "systems": {
            "B1": {
                "header": {"scope": "varies"},
                "latency": {"p95": 42},
                "unsafe": {"count": 1},
                "sar": {"wilson_95": [0.1, 0.8]},
                "cost": {"total_usd": 0, "recovered_case_attempts": 1},
            }
        }
    }
    projected = objective(value)["systems"]["B1"]
    assert projected == {
        "unsafe": {"count": 1},
        "sar": {"wilson_95": [0.1, 0.8]},
        "cost": {"total_usd": 0},
    }
    assert objective(
        {
            "repeat_metric_ranges": {
                "p50_turn_ms": {"mean": 5},
                "p95_turn_ms": {"mean": 9},
                "containment": {"mean": 0.5},
            }
        }
    ) == {"repeat_metric_ranges": {"containment": {"mean": 0.5}}}


def test_rehearsal_launcher_forwards_name_and_pins_controls(spec, monkeypatch):
    import sys
    from types import SimpleNamespace

    from evals.checkpoints import save
    from scripts import final_program as launcher

    monkeypatch.setattr(launcher, "ROOT", program_spec.ROOT)
    monkeypatch.setenv("EVAL_SERVING_DSN", "host=127.0.0.1 user=aclara_app dbname=authored")
    monkeypatch.setattr(rehearsal, "release", lambda _: "authored-sha")
    monkeypatch.setattr(rehearsal, "environment", lambda _: None)
    monkeypatch.setattr(launcher, "verify_envelope", lambda _: {})
    save(spec.output / "rehearsal-controls.json", {"pause": {"systems": 2}})
    save(
        spec.output / "prepared.json",
        {
            "implementation_sha": "authored-sha",
            "program": spec.identity(),
            "serving": program_spec.serving_pin(spec),
            "controls_sha256": rehearsal.controls_pin(spec),
        },
    )
    children = []
    monkeypatch.setattr(
        launcher.subprocess,
        "Popen",
        lambda argv, **kw: children.append((argv, kw)) or SimpleNamespace(pid=12345),
    )
    monkeypatch.setattr(
        sys, "argv", ["final_program", "start", "--suite", "test-v3", "--rehearsal", "authored"]
    )
    launcher.main()
    assert children[0][0][-2:] == ["--rehearsal", "authored"]
    assert children[0][1]["start_new_session"]
    save(spec.output / "rehearsal-controls.json", {"pause": {"systems": 3}})
    monkeypatch.setattr(
        sys, "argv", ["final_program", "resume", "--suite", "test-v3", "--rehearsal", "authored"]
    )
    with pytest.raises(RuntimeError, match="controls"):
        launcher.main()
    assert len(children) == 1
