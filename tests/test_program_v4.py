"""Authored envelopes/clients only: never opens a release or calls a provider."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from evals import program_spec
from evals.checkpoints import Checkpoints, save
from scripts import final_program

LOCAL = "host=127.0.0.1 port=15432 dbname=authored user=aclara_app password=authored-only"


def test_suite_configuration_is_pure_pinned_and_separates_history(monkeypatch):
    monkeypatch.setattr(
        Path, "open", lambda *_a, **_k: pytest.fail("configuration read frozen data")
    )
    v4 = program_spec.specification("test-v4")
    v3 = program_spec.specification("test-v3")
    assert v4.scope == "final-evaluation-v4" and v4.run_id == "final-program-v4"
    assert v4.output != v3.output and v4.bindings != v3.bindings
    assert v4.manifest_pin.startswith("309c3aa2")
    with pytest.raises(ValueError, match="pin"):
        program_spec.specification("test-v4", manifest_pin="0" * 64)
    with pytest.raises(ValueError, match="artifacts"):
        program_spec.specification("test-v4", bindings="/outside/bindings.json")
    with pytest.raises(ValueError):
        program_spec.specification("test-v1")


@pytest.mark.parametrize(
    "dsn",
    [
        None,
        "host=azure.example user=aclara_app dbname=fixture",
        "host=127.0.0.1 hostaddr=203.0.113.1 user=aclara_app dbname=fixture",
        "host=127.0.0.1 user=postgres dbname=fixture",
        "host=127.0.0.1 user=aclara_app dbname=fixture service=remote",
    ],
)
def test_local_serving_rejects_remote_owner_or_implicit_routes(monkeypatch, dsn):
    if dsn is None:
        monkeypatch.delenv("EVAL_SERVING_DSN", raising=False)
    else:
        monkeypatch.setenv("EVAL_SERVING_DSN", dsn)
    with pytest.raises(ValueError):
        program_spec.serving_pin(program_spec.specification("test-v4"))


def test_environment_preserves_local_serving_and_fetches_only_in_memory(monkeypatch):
    from scripts import azure_dev, azure_migrate_ops

    monkeypatch.setenv("EVAL_SERVING_DSN", LOCAL)
    monkeypatch.setattr(azure_dev, "az", lambda *_: {"value": "authored-only"})
    monkeypatch.setattr(azure_migrate_ops, "connection_string", lambda _: "authored-budget")
    final_program.environment(program_spec.specification("test-v4"))
    assert program_spec.serving_pin(program_spec.specification("test-v4"))["location"] == "local"
    assert __import__("os").environ["EVAL_SERVING_DSN"] == LOCAL
    assert __import__("os").environ["EVAL_BUDGET_DSN"] == "authored-budget"
    assert "password" not in program_spec.serving_pin(program_spec.specification("test-v4"))


def test_launcher_forwards_immutable_config_and_refuses_reset_or_endpoint_change(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(program_spec, "ROOT", tmp_path)
    monkeypatch.setattr(final_program, "ROOT", tmp_path)
    monkeypatch.setenv("EVAL_SERVING_DSN", LOCAL)
    monkeypatch.setenv("LLM_FINAL_RUN_STARTED", "1")
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setattr(final_program, "release", lambda: "authored-sha")
    monkeypatch.setattr(final_program, "verify_envelope", lambda _: {"binding_sha256": "authored"})
    spec = program_spec.specification("test-v4")
    save(
        spec.output / "prepared.json",
        {
            "implementation_sha": "authored-sha",
            "program": spec.identity(),
            "serving": program_spec.serving_pin(spec),
            "binding_sha256": "authored",
        },
    )
    children = []

    def child(argv, **kwargs):
        children.append((argv, kwargs))
        return SimpleNamespace(pid=12345)

    monkeypatch.setattr(final_program.subprocess, "Popen", child)
    monkeypatch.setattr(sys, "argv", ["final_program", "start", "--suite", "test-v4"])
    final_program.main()
    assert len(children) == 1 and children[0][1]["start_new_session"]
    assert children[0][0][-6:] == [
        "--suite",
        "test-v4",
        "--bindings",
        spec.identity()["bindings"],
        "--manifest-pin",
        spec.manifest_pin,
    ]
    with pytest.raises(RuntimeError, match="resume"):
        final_program.main()
    monkeypatch.setattr(sys, "argv", ["final_program", "resume", "--suite", "test-v4"])
    final_program.main()
    assert len(children) == 2
    monkeypatch.setenv("EVAL_SERVING_DSN", LOCAL.replace("15432", "15433"))
    with pytest.raises(RuntimeError, match="connection"):
        final_program.main()
    assert len(children) == 2
    assert json.loads((spec.output / "launch.json").read_text())["program"] == spec.identity()


def test_v4_client_and_judge_share_the_same_scope_with_1024_cap(monkeypatch):
    from aclara.llm import final_run

    monkeypatch.setenv("LLM_FINAL_RUN_STARTED", "1")
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    gates = []

    def gate(store, **kwargs):
        gates.append(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(final_run, "PostgresSpendGate", gate)
    spec = program_spec.specification("test-v4")
    common = dict(budget_scope=spec.scope, budget_run_id=spec.run_id)
    system = final_run.client_for("default", None, **common)
    judge = final_run.client_for("openrouter_sonnet", None, judge=True, **common)
    assert gates == [{"scope": spec.scope, "run_id": spec.run_id}] * 2
    assert list(judge.models.values())[0].max_output_tokens == 1024
    assert system.spend_gate is not None


def test_v4_reserves_prior_v3_and_dev_in_cumulative_math():
    from scripts.final_budget import CAP, check_exposure, prior_scopes

    assert {"final-evaluation-v3", "dev-gate/post-v3"} <= set(
        prior_scopes(program_spec.specification("test-v4"))
    )
    check_exposure(Decimal("4.54283516"), CAP)
    check_exposure(Decimal("8.90"), CAP)
    with pytest.raises(RuntimeError):
        check_exposure(Decimal("8.90000001"), CAP)


def test_checkpoint_pins_reject_suite_changes(tmp_path):
    v3, v4 = [program_spec.specification(s) for s in ("test-v3", "test-v4")]
    Checkpoints(tmp_path, {"program": v4.identity()})
    with pytest.raises(ValueError, match="pins differ"):
        Checkpoints(tmp_path, {"program": v3.identity()})


def test_explicit_envelope_reads_no_scenarios_or_selections(tmp_path, monkeypatch):
    monkeypatch.setattr(program_spec, "ROOT", tmp_path)
    directory = tmp_path / "evals/suites/test-v4"
    directory.mkdir(parents=True)
    binding = tmp_path / "artifacts/binding.json"
    binding.parent.mkdir()
    binding.write_text('{"authored_fixture":true}')
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
        + "  scenarios-authored.yaml\n"
    )
    spec = program_spec.ProgramSpec("test-v4", binding, program_spec.digest(manifest))
    original_open = Path.open

    def allowed(path, *args, **kwargs):
        if path not in {binding, provenance, manifest}:
            pytest.fail("envelope opened a scenario or selection")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", allowed)
    assert program_spec.verify_envelope(spec)["manifest_sha256"] == spec.manifest_pin
