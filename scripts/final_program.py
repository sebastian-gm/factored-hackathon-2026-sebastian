"""Start/resume the detached final program only after Sebastian's explicit go."""

# ruff: noqa: S603, S607, T201 -- fixed repo-scoped subprocesses, aggregate output only.
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

from evals.checkpoints import atomic_write, exclusive, save

from aclara.llm.final_run import RUN_ID, require_start

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / RUN_ID


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


def environment() -> None:
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
    os.environ["EVAL_SERVING_DSN"] = os.environ["EVAL_BUDGET_DSN"]
    os.environ["FINAL_RUN_START_APPROVED"] = "1"


def worker() -> None:
    require_start()
    with exclusive(OUTPUT / "worker.lock"):
        sha = release()
        launch = json.loads((OUTPUT / "launch.json").read_text())
        if launch["implementation_sha"] != sha:
            raise RuntimeError("Restore the pinned release before resuming")
        atomic_write(OUTPUT / "worker.pid", str(os.getpid()) + "\n")
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        try:
            environment()
            from evals.final_program import main as evaluate
            from scripts.final_budget import main as initialize_budget

            initialize_budget()  # Validate the prepared cap; never reset or re-enable it.
            from evals.final_program import budget_receipt

            previous = OUTPUT / "progress.json"
            if previous.exists():
                prior = json.loads(previous.read_text())["budget"]
                current = budget_receipt()
                if (
                    current["attempts"] < prior["attempts"]
                    or current["charged_with_reserves_usd"] < prior["charged_with_reserves_usd"]
                ):
                    raise RuntimeError(
                        "Durable spend history regressed; do not resume against a reset database"
                    )
            evaluate(OUTPUT, sha)
        except BaseException as error:
            save(
                OUTPUT / "STOPPED.json",
                {
                    "error_type": type(error).__name__,
                    "resume": "python -m scripts.final_program resume",
                },
            )
            print(json.dumps({"state": "stopped", "error_type": type(error).__name__}), flush=True)
            raise SystemExit(1) from None
        finally:
            (OUTPUT / "worker.pid").unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "resume", "status", "_worker"])
    args = parser.parse_args()
    if args.action == "status":
        for name in ("progress.json", "STOPPED.json", "COMPLETE.json"):
            path = OUTPUT / name
            if path.exists():
                print(path.read_text())
        return
    require_start()
    if args.action == "_worker":
        worker()
        return
    sha = release()
    with exclusive(OUTPUT / "launcher.lock"), exclusive(OUTPUT / "worker.lock"):
        launch = OUTPUT / "launch.json"
        if args.action == "start":
            if launch.exists():
                raise RuntimeError("Existing program: use resume, never reset artifacts/budget")
            save(launch, {"implementation_sha": sha, "budget_run": RUN_ID})
        elif not launch.exists() or json.loads(launch.read_text())["implementation_sha"] != sha:
            raise RuntimeError("Resume requires the existing pinned release")
        if (OUTPUT / "COMPLETE.json").exists():
            print("Program already complete; no requests sent.")
            return
        fd = os.open(OUTPUT / "worker.log", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        # Child waits briefly for launcher to release its worker lock.
    with os.fdopen(fd, "a") as log:
        child = subprocess.Popen(
            [sys.executable, "-m", "scripts.final_program", "_worker"],
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
                "artifacts": str(OUTPUT.relative_to(ROOT)),
                "implementation_sha": sha,
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit("Final program blocked: " + type(error).__name__) from None
