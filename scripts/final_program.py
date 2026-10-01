"""Start/resume the detached final program only after Sebastian's explicit go."""

# ruff: noqa: S603, S607, T201 -- fixed repo-scoped subprocesses, aggregate output only.
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from evals import rehearsal
from evals.checkpoints import atomic_write, exclusive, save
from evals.program_spec import (
    ProgramSpec,
    add_arguments,
    serving_pin,
    specification,
    verify_envelope,
)

from aclara.llm.final_run import require_start

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def release() -> str:
    if git("status", "--porcelain") or git("branch", "--show-current") != "main":
        raise RuntimeError("Final program requires a clean main checkout")
    sha = git("rev-parse", "HEAD")
    if sha != git("rev-parse", "origin/main"):
        raise RuntimeError("Main and origin/main differ")
    evidence = json.loads((ROOT / "artifacts/azure/jev-release.json").read_text())
    if evidence["implementation_sha"] != sha or not all(
        evidence.get(key) for key in ("controls_verified", "real_smoke_verified", "ci_verified")
    ):
        raise RuntimeError("The final release has not passed its deployed acceptance gates")
    return sha


def environment(spec: ProgramSpec) -> None:
    if spec.rehearsal:
        rehearsal.environment(spec)
        return
    serving_pin(spec)
    # Credentials are fetched in memory in the child, never placed in argv/log/files.
    from scripts.azure_dev import VAULT, az
    from scripts.azure_migrate_ops import connection_string

    for name, secret in (
        ("OPENROUTER_API_KEY", "openrouter-api-key"),
        ("TYPESAFE_API_KEY", "typesafe-api-key"),
    ):
        os.environ[name] = az(
            "keyvault", "secret", "show", "--vault-name", VAULT, "--name", secret
        )["value"]
    os.environ["FINAL_BUDGET_OWNER_DSN"] = connection_string("aclara_admin")
    os.environ["EVAL_BUDGET_DSN"] = connection_string("aclara_app")
    if spec.suite != "test-v4":
        os.environ["EVAL_SERVING_DSN"] = os.environ["EVAL_BUDGET_DSN"]
    os.environ["FINAL_RUN_START_APPROVED"] = "1"


def worker(spec: ProgramSpec) -> None:
    output = spec.output
    authorize(spec)
    if spec.rehearsal:
        environment(spec)
    with exclusive(output / "worker.lock"):
        sha = implementation(spec)
        launch = json.loads((output / "launch.json").read_text())
        if (
            launch["implementation_sha"] != sha
            or launch.get("program") != spec.identity()
            or launch.get("serving") != serving_pin(spec)
            or (spec.rehearsal and launch.get("controls_sha256") != rehearsal.controls_pin(spec))
        ):
            raise RuntimeError("Restore the pinned release before resuming")
        atomic_write(output / "worker.pid", str(os.getpid()) + "\n")
        (output / "STOPPED.json").unlink(missing_ok=True)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        worker_started = time.time()

        def terminate(_signum, _frame):
            raise InterruptedError("Worker stopped; preserve checkpoints and reservations")

        def watchdog(_signum, _frame):
            progress = output / "progress.json"
            last = max(worker_started, progress.stat().st_mtime if progress.exists() else 0)
            started = datetime.fromisoformat(launch["started_at"]).timestamp()
            if time.time() - last >= 900 or time.time() - started >= (
                10800 if spec.suite == "test-v4" else 12600
            ):
                raise TimeoutError("Progress or total wall-clock limit reached")

        signal.signal(signal.SIGTERM, terminate)
        signal.signal(signal.SIGALRM, watchdog)
        signal.setitimer(signal.ITIMER_REAL, 30, 30)
        try:
            environment(spec)
            from evals.final_program import main as evaluate
            from scripts.final_budget import main as initialize_budget

            if spec.rehearsal:
                rehearsal.receipt(spec)
            else:
                initialize_budget(spec)  # Validate the cap; never reset or re-enable it.
            from evals.final_program import budget_receipt

            previous = output / "progress.json"
            if previous.exists():
                prior = json.loads(previous.read_text())["budget"]
                current = budget_receipt(spec)
                if (
                    current["attempts"] < prior["attempts"]
                    or current["charged_with_reserves_usd"] < prior["charged_with_reserves_usd"]
                ):
                    raise RuntimeError(
                        "Durable spend history regressed; do not resume against a reset database"
                    )
            evaluate(output, sha, spec)
        except BaseException as error:
            save(
                output / "STOPPED.json",
                {
                    **error_metadata(error),
                    "resume": "python -m scripts.final_program resume --suite "
                    + spec.suite
                    + (" --rehearsal " + spec.rehearsal if spec.rehearsal else ""),
                },
            )
            print(json.dumps({"state": "stopped", "error_type": type(error).__name__}), flush=True)
            raise SystemExit(1) from None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            (output / "worker.pid").unlink(missing_ok=True)


def authorize(spec: ProgramSpec) -> None:
    if spec.rehearsal:
        rehearsal.guard(spec)
    else:
        require_start()


def implementation(spec: ProgramSpec) -> str:
    return rehearsal.release(spec) if spec.rehearsal else release()


def error_metadata(error: BaseException) -> dict:
    """Only exception classes; messages can echo credentials or scenario inputs."""
    names = []
    seen = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        names.append(type(current).__name__)
        current = current.__cause__
    return {"error_type": names[0], "cause_types": names[1:]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "start", "resume", "status", "_worker"])
    add_arguments(parser)
    parser.add_argument("--rehearsal", help="Zero-spend retired-v3 rehearsal in isolated artifacts")
    args = parser.parse_args()
    spec = specification(args.suite, args.bindings, args.manifest_pin, args.rehearsal)
    output = spec.output
    if args.action == "status":
        for name in ("prepared.json", "progress.json", "STOPPED.json", "COMPLETE.json"):
            path = output / name
            if path.exists():
                print(path.read_text())
        return
    if args.action == "prepare":
        from scripts.azure_migrate_ops import connection_string
        from scripts.final_budget import verify

        sha = implementation(spec)
        if (output / "launch.json").exists():
            raise RuntimeError("Preparation cannot modify a launched program")
        budget = (
            rehearsal.prepare(spec)
            if spec.rehearsal
            else verify(connection_string("aclara_admin"), spec)
        )
        receipt = {
            "state": "prepared_not_started",
            "implementation_sha": sha,
            "suite": spec.suite,
            "program": spec.identity(),
            "serving": serving_pin(spec),
            **verify_envelope(spec),
            "workload": {
                "B1": 100,
                "P-Gemini": 160,
                "repeat_scenarios": 30,
                "judge_scenarios": 30,
                "dual_judge_items": 60,
                "frontier": False,
                "calibration_items": 0,
            },
            "budget": budget,
        }
        if spec.rehearsal:
            receipt["controls_sha256"] = rehearsal.controls_pin(spec)
            receipt["workload"]["routes"] = "B1 only; mock judges; no model comparison"
        save(output / "prepared.json", receipt)
        print(json.dumps(receipt))
        return
    authorize(spec)
    if args.action == "_worker":
        worker(spec)
        return
    if spec.rehearsal:
        environment(spec)
    sha = implementation(spec)
    prepared = json.loads((output / "prepared.json").read_text())
    if prepared.get("program") != spec.identity() or prepared.get("serving") != serving_pin(spec):
        raise RuntimeError("Restore the prepared program and serving connection")
    if spec.rehearsal and prepared.get("controls_sha256") != rehearsal.controls_pin(spec):
        raise RuntimeError("Restore the prepared rehearsal controls")
    if prepared["implementation_sha"] != sha or any(
        prepared[k] != v for k, v in verify_envelope(spec).items()
    ):
        raise RuntimeError("Restore the prepared release and frozen input pins")
    with exclusive(output / "launcher.lock"), exclusive(output / "worker.lock"):
        launch = output / "launch.json"
        if args.action == "start":
            if launch.exists():
                raise RuntimeError("Existing program: use resume, never reset artifacts/budget")
            save(
                launch,
                {
                    "implementation_sha": sha,
                    "budget_run": spec.run_id,
                    "program": spec.identity(),
                    "serving": serving_pin(spec),
                    "started_at": datetime.now(UTC).isoformat(),
                    **({"controls_sha256": rehearsal.controls_pin(spec)} if spec.rehearsal else {}),
                },
            )
        elif not launch.exists() or json.loads(launch.read_text())["implementation_sha"] != sha:
            raise RuntimeError("Resume requires the existing pinned release")
        if (output / "COMPLETE.json").exists():
            print("Program already complete; no requests sent.")
            return
        fd = os.open(output / "worker.log", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        # Child waits briefly for launcher to release its worker lock.
    with os.fdopen(fd, "a") as log:
        child = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "scripts.final_program",
                "_worker",
                "--suite",
                spec.suite,
                "--bindings",
                spec.identity()["bindings"],
                "--manifest-pin",
                spec.manifest_pin,
                *(["--rehearsal", spec.rehearsal] if spec.rehearsal else []),
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
            close_fds=True,
        )
    print(
        json.dumps(
            {
                "pid": child.pid,
                "artifacts": str(output.relative_to(ROOT)),
                "implementation_sha": sha,
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit("Final program blocked: " + type(error).__name__) from None
