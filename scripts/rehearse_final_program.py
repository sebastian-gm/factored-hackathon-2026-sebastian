"""Exercise the real detached launcher on retired v3, without paid providers.

Creates three immutable, isolated rehearsal programs; never resets old artifacts.
Requires the ignored v3 bindings, matcher splits and local organizer serving load.
"""

# ruff: noqa: S603, T201 -- fixed Python child commands; aggregate output only.
from __future__ import annotations

import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psycopg
from evals.checkpoints import exclusive, save
from evals.program_spec import ROOT, ProgramSpec, specification

VOLATILE = {
    "header",
    "latency",
    "turn_latency",
    "latency_target",
    "components",
    "repeat_clustered_latency",
    "recovered_case_attempts",
    "components_note",
}


def objective(value: Any) -> Any:
    """Compare all objective aggregates/intervals, excluding measured runtime noise."""
    if isinstance(value, dict):
        return {k: objective(v) for k, v in value.items() if k not in VOLATILE}
    if isinstance(value, list):
        return [objective(v) for v in value]
    return value


def command(spec: ProgramSpec, action: str) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.final_program",
            action,
            "--suite",
            "test-v3",
            "--rehearsal",
            spec.rehearsal,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    path = spec.output / "controller-commands.jsonl"
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a") as stream:
        stream.write(
            json.dumps(
                {
                    "action": action,
                    "exit_code": result.returncode,
                    "output": result.stdout,
                    "error": result.stderr,
                }
            )
            + "\n"
        )
    if result.returncode:
        raise RuntimeError("Rehearsal launcher failed; inspect private controller metadata")


def stop(spec: ProgramSpec) -> None:
    """SIGTERM only the PID recorded by this program's own worker."""
    path = spec.output / "worker.pid"
    pid = int(path.read_text())
    args = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    if b"scripts.final_program" not in args or spec.rehearsal.encode() not in args:
        raise RuntimeError("Refuse to signal a process outside this rehearsal")
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 30
    while path.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("Rehearsal worker did not terminate cleanly")
        time.sleep(0.1)
    with exclusive(spec.output / "worker.lock"):
        pass


def wait(spec: ProgramSpec, *, stop_phase: str | None = None, expect_error: bool = False) -> str:
    started = time.monotonic()
    last = started
    seen = None
    while True:
        progress = spec.output / "progress.json"
        if progress.exists():
            value = json.loads(progress.read_text())
            current = (value["phase"], value["completed"], progress.stat().st_mtime_ns)
            if current != seen:
                last, seen = time.monotonic(), current
        if stop_phase and (spec.output / f"pause-{stop_phase}.json").exists():
            stop(spec)
            if (
                json.loads((spec.output / "STOPPED.json").read_text())["error_type"]
                != "InterruptedError"
            ):
                raise RuntimeError("Expected clean SIGTERM checkpoint stop")
            return "interrupted"
        if (spec.output / "COMPLETE.json").exists() and not (spec.output / "worker.pid").exists():
            return "complete"
        if (spec.output / "STOPPED.json").exists() and not (spec.output / "worker.pid").exists():
            if expect_error:
                return "stopped"
            raise RuntimeError("Rehearsal stopped unexpectedly; preserve private artifacts")
        if time.monotonic() - last > 900 or time.monotonic() - started > 1800:
            if (spec.output / "worker.pid").exists():
                stop(spec)
            raise TimeoutError("Rehearsal stalled or exceeded controller wall-clock limit")
        time.sleep(0.25)


def summary(spec: ProgramSpec) -> dict:
    from evals import rehearsal

    rehearsal.environment(spec)
    receipt = rehearsal.receipt(spec)
    result = json.loads((spec.output / "results.json").read_text())
    with (spec.output / "human-judge-20.csv").open() as stream:
        sheet_count = sum(1 for _ in csv.DictReader(stream))
    records = []
    for path in spec.output.glob("checkpoints/*/calls-*.jsonl"):
        records.extend(json.loads(line)["call"] for line in path.read_text().splitlines())
    if any(r["provider"] != "mock" or r["cost_usd"] != 0 for r in records):
        raise RuntimeError("Unexpected real or charged call in rehearsal")
    units = len(list(spec.output.glob("checkpoints/*/result.json")))
    attempts = len(list(spec.output.glob("checkpoints/*/attempt-*.json")))
    if units != 320 or sheet_count != 20:
        raise RuntimeError("Rehearsal workload or report inventory incomplete")
    if not (spec.output / "results.md").exists():
        raise RuntimeError("Markdown report missing")
    return {
        "artifacts": str(spec.output.relative_to(ROOT)),
        "scope": spec.scope,
        "completed_cases": result["header"]["case_runs"],
        "judge_items": result["judges"]["frozen"]["attempted"],
        "judge_failed": result["judges"]["frozen"]["failed"],
        "mock_calls": len(records),
        "length_refusals": sum(
            r["status"] == "refusal" and r["stop_reason"] == "length" for r in records
        ),
        "checkpoint_units": units,
        "checkpoint_attempts": attempts,
        "human_sheet_items": sheet_count,
        "budget": receipt,
    }


def run(name: str) -> dict:
    os.environ.update(LLM_PROVIDER="mock", LLM_REAL_CALLS_APPROVED="0", LLM_REHEARSAL_APPROVED="1")
    # Derive serving credentials locally; reject inherited cloud-serving routes.
    os.environ.pop("EVAL_SERVING_DSN", None)
    specs = [
        specification("test-v3", rehearsal=name + "-" + suffix)
        for suffix in ("baseline", "resumed", "faults")
    ]
    if any(s.output.exists() for s in specs):
        raise RuntimeError("Existing rehearsal: use its documented resume command, never reset")
    started = time.monotonic()
    for spec, controls in zip(
        specs,
        [{}, {"pause": {"systems": 12, "judges": 12}}, {"db_blip_at": 22, "judge_length_at": 10}],
        strict=True,
    ):
        save(spec.output / "rehearsal-controls.json", controls)
        command(spec, "prepare")
    baseline, resumed, faults = specs
    command(baseline, "start")
    wait(baseline)
    print(json.dumps({"milestone": "baseline_complete", **summary(baseline)}), flush=True)
    command(resumed, "start")
    wait(resumed, stop_phase="systems")
    command(resumed, "resume")
    # The worker clears its previous stop marker after acquiring its lock/PID.
    await_worker(resumed)
    wait(resumed, stop_phase="judges")
    command(resumed, "resume")
    await_worker(resumed)
    wait(resumed)
    print(json.dumps({"milestone": "two_sigterms_resumed", **summary(resumed)}), flush=True)
    command(faults, "start")
    wait(faults, expect_error=True)
    stopped = json.loads((faults.output / "STOPPED.json").read_text())
    if "OperationalError" not in [stopped["error_type"], *stopped["cause_types"]]:
        raise RuntimeError("Connectivity injection produced an unexpected error class")
    from evals import rehearsal

    rehearsal.environment(faults)
    with psycopg.connect(os.environ["EVAL_SERVING_DSN"]) as pg:
        if pg.execute("SELECT 1").fetchone() != (1,):
            raise RuntimeError("Local serving is unavailable; do not resume")
    command(faults, "resume")
    await_worker(faults)
    wait(faults)
    details = [summary(s) for s in specs]
    outputs = [json.loads((s.output / "results.json").read_text()) for s in specs]
    primary = [
        objective({"systems": r["systems"], "paired_comparison": r["paired_comparison"]})
        for r in outputs
    ]
    if not primary[0] == primary[1] == primary[2]:
        raise RuntimeError("Objective aggregates differ; investigate without changing suite rows")
    if outputs[0]["judges"] != outputs[1]["judges"]:
        raise RuntimeError("Judge aggregates differ after SIGTERM/resume")
    if (
        details[0]["checkpoint_attempts"] != 320
        or details[1]["checkpoint_attempts"] != 320
        or details[2]["checkpoint_attempts"] != 321
    ):
        raise RuntimeError("Unexpected replay of completed units")
    if details[2]["judge_failed"] != 1 or details[2]["length_refusals"] != 2:
        raise RuntimeError("Output-length failure was not bounded and recorded")
    evidence = {
        "state": "verified",
        "duration_s": round(time.monotonic() - started, 2),
        "programs": details,
        "sigterms": 2,
        "objective_aggregates_identical": True,
        "judge_aggregates_identical_after_resume": True,
        "connectivity_stop": stopped,
        "exception": "Measured latency and recovered-attempt counters naturally differ; mock judgments are not vendor agreement",
    }
    save(ROOT / "artifacts/final-program-rehearsal" / (name + "-summary.json"), evidence)
    print(json.dumps(evidence), flush=True)
    return evidence


def await_worker(spec: ProgramSpec) -> None:
    deadline = time.monotonic() + 30
    while not (spec.output / "worker.pid").exists():
        if (spec.output / "COMPLETE.json").exists():
            return
        if time.monotonic() > deadline:
            raise TimeoutError("Resume worker failed to acquire its process lock")
        time.sleep(0.1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--name", required=True, help="Unique prefix (letters/digits/hyphens); no resets"
    )
    try:
        run(parser.parse_args().name)
    except Exception as error:
        raise SystemExit("Rehearsal stopped: " + type(error).__name__) from None
