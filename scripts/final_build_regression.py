"""Owner-approved post-v4 regression, NOT a new held-out evaluation.

One P pass and one zero-cost B1 pass; the known eight flagged cases run first.
Official suites, bindings, final-program outputs and model prompts are unchanged.
"""

# ruff: noqa: S603, S607, T201 -- fixed repo-scoped git; aggregate progress only.
from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from evals.access import access
from evals.bindings import ROOT, bind
from evals.bound_execution import execute_bound
from evals.checkpoints import Checkpoints, exclusive, save
from evals.heldout import load
from evals.metrics import UNSAFE
from evals.program_spec import serving_pin, specification, verify_envelope
from evals.serving import open_serving
from evals.studies.llm.final_run import FinalSpendGate, journal
from scripts.final_day_budget import RUN_ID, verify

from aclara.llm.client import StructuredClient
from aclara.llm.config import load_fallback_route, load_models, load_prices
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import Store

SCOPE = "regression/final-build/v4"
OUTPUT = ROOT / "artifacts/final-build-regression"
LABEL = "Regression replay on the final build, NOT a new held-out evaluation"
FLAGGED = frozenset(
    {"v4.005", "v4.019", "v4.020", "v4.021", "v4.022", "v4.039", "v4.040", "v4.061"}
)


def implementation() -> str:
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()

    if git("status", "--porcelain") or git("branch", "--show-current") != "main":
        raise RuntimeError("Regression requires clean main")
    sha = git("rev-parse", "HEAD")
    if sha != git("rev-parse", "origin/main"):
        raise RuntimeError("Regression main differs from origin")
    return sha


def environment(real: bool) -> Store | None:
    if not real:
        return None
    if os.getenv("LLM_REGRESSION_APPROVED") != "1" or os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Owner-approved regression start signal required")
    from scripts.azure_dev import VAULT, az
    from scripts.azure_migrate_ops import connection_string

    os.environ["OPENROUTER_API_KEY"] = az(
        "keyvault", "secret", "show", "--vault-name", VAULT, "--name", "openrouter-api-key"
    )["value"]
    verify(connection_string("aclara_admin"))
    return Store(connection_string("aclara_app"))


def client(store: Store, path: Path) -> StructuredClient:
    models = load_models(ROOT / "config/models.yaml")
    fallback = load_fallback_route(ROOT / "config/models.yaml", models)
    models["nlu"] = models["phrase"] = models["default"]
    return StructuredClient(
        models,
        load_prices(ROOT / "config/pricing.yaml"),
        budget_usd=None,
        daily_budget_usd=0.30,
        spend_gate=FinalSpendGate(PostgresSpendGate(store, scope=SCOPE, run_id=RUN_ID)),
        fallback_routes={"nlu": fallback, "phrase": fallback} if fallback else None,
        call_timeout_seconds=45,
        response_record=journal(path),
    )


def summarize(rows: list[dict]) -> dict:
    def group(cases):
        forbidden = Counter(value for case in cases for value in case["forbidden_observed"])
        return {
            "cases": len(cases),
            "passed": sum(bool(case["passed"]) for case in cases),
            "safety_gates": {
                key: sum(bool(case["unsafe"].get(key)) for case in cases) for key in UNSAFE
            },
            "forbidden_predicates": dict(sorted(forbidden.items())),
            "failed_ids": sorted(case["id"] for case in cases if not case["passed"]),
            "model_cost_usd": str(
                sum((Decimal(str(case["cost_usd"])) for case in cases), Decimal(0))
            ),
        }

    return {
        "label": LABEL,
        "official_v4_unchanged": True,
        "systems": {
            system: {
                "all": group([r for r in rows if r["system"] == system]),
                "flagged_subset": group(
                    [r for r in rows if r["system"] == system and r["id"] in FLAGGED]
                ),
            }
            for system in ("P", "B1")
        },
    }


async def unit(checkpoints: Checkpoints, key: str, execute) -> dict:
    cached = checkpoints.read(key)
    if cached is not None:
        return cached
    path = checkpoints.begin(key)
    result = await execute(path)
    calls = [row["call"] for row in checkpoints.calls(key)]
    if any(c["cost_usd"] is None for c in calls):
        raise RuntimeError("Unknown cost retained; stop regression")
    amounts = [Decimal(str(c["cost_usd"])) for c in calls]
    if any(not amount.is_finite() or amount < 0 for amount in amounts):
        raise RuntimeError("Invalid call cost; preserve reservations")
    result["cost_usd"] = float(sum(amounts, Decimal(0)))
    return checkpoints.finish(key, result)


async def run(output: Path, mode: str, real: bool) -> None:
    spec = specification("test-v4")
    sha = implementation()
    serving_identity = serving_pin(spec)
    envelope = verify_envelope(spec)
    if mode == "start" and (output / "release.json").exists():
        raise RuntimeError("Existing attempt: use resume, never start again")
    if mode == "resume" and not (output / "release.json").exists():
        raise RuntimeError("No pinned attempt to resume")
    pins = {
        "sha": sha,
        "label": LABEL,
        "real": real,
        "envelope": envelope,
        "serving": serving_identity,
        "scope": SCOPE,
        "run_id": RUN_ID,
    }
    # Local forced-RLS serving reads avoid workstation-to-Azure ledger latency.
    serving = open_serving()
    store = None
    try:
        if not serving.temporal_quality_checked:
            raise RuntimeError("Final build requires the temporal-quality serving column")
        pins["serving_identity"] = serving.identity
        checkpoints = Checkpoints(output, pins)
        save(output / "serving-pin.json", serving.identity)
        store = environment(real)
        paths = [p for p in spec.release.iterdir() if p.is_file()] + [spec.bindings]
        paths += [
            ROOT / f"artifacts/charge_matcher/v1/dataset/{name}.jsonl"
            for name in ("train", "validation", "test")
        ]
        with access("final_build_regression", paths, LABEL + "; owner handoff 20, no tuning"):
            suite, identities, directory = load(
                serving, release=spec.release, binding_path=spec.bindings
            )
            scenarios = suite["scenarios"]
            if len(scenarios) != 100 or not {s["id"] for s in scenarios} >= FLAGGED:
                raise RuntimeError("Approved regression inventory differs")
            rows = []
            ordered = sorted(scenarios, key=lambda s: (s["id"] not in FLAGGED, s["id"]))
            for system in ("P", "B1"):
                for scenario in ordered:

                    async def execute(path, scenario=scenario, system=system):
                        fixture = bind(
                            scenario,
                            identities[scenario["persona"]["customer_ref"]],
                            directory,
                            serving,
                        )
                        llm = client(store, path) if store is not None and system == "P" else None
                        return await execute_bound(scenario, fixture, system, llm_client=llm)

                    result = await unit(checkpoints, f"{system}:{scenario['id']}", execute)
                    rows.append(result)
                    progress = {
                        "phase": "systems",
                        "completed": len(rows),
                        "planned": 200,
                        "at": datetime.now(UTC).isoformat(),
                        "model_cost_usd": summarize(rows)["systems"]["P"]["all"]["model_cost_usd"],
                    }
                    save(output / "progress.json", progress)
                    if len(rows) % 10 == 0:
                        print(json.dumps(progress), flush=True)
            results = {**summarize(rows), **pins, "completed_at": datetime.now(UTC).isoformat()}
            save(output / "results.json", results)  # Aggregates + case IDs only.
            save(output / "progress.json", {**progress, "phase": "COMPLETE"})
            print(json.dumps(results), flush=True)
    finally:
        serving.store.close()
        if store is not None:
            store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "resume", "status"))
    parser.add_argument("--real", action="store_true")
    args = parser.parse_args()
    output = OUTPUT if args.real else ROOT / "artifacts/final-build-regression-mock"
    if args.command == "status":
        path = output / "progress.json"
        print(path.read_text() if path.exists() else '{"phase":"not_started"}')
        return
    launch = output / "launch.json"
    started = time.time()
    origin = (
        datetime.fromisoformat(json.loads(launch.read_text())["started_at"]).timestamp()
        if launch.exists()
        else started
    )
    acquired = False

    def terminate(_signum, _frame):
        raise InterruptedError("Preserve checkpoints and reservations")

    def watchdog(_signum, _frame):
        path = output / "progress.json"
        last = max(started, path.stat().st_mtime if path.exists() else 0)
        if time.time() - last >= 900 or time.time() - origin >= 10800:
            raise TimeoutError("Regression stalled or exceeded three hours")

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGALRM, watchdog)
    signal.setitimer(signal.ITIMER_REAL, 30, 30)
    try:
        with exclusive(output / "worker.lock"):
            acquired = True
            if not launch.exists():
                save(launch, {"started_at": datetime.now(UTC).isoformat()})
            save(
                output / "worker.json",
                {"pid": os.getpid(), "started_at": datetime.now(UTC).isoformat()},
            )
            asyncio.run(run(output, args.command, args.real))
    except Exception as error:
        # Never echo exception inputs, scenario text, tokens or connection strings.
        if acquired:
            save(
                output / "STOPPED.json",
                {"error_class": type(error).__name__, "at": datetime.now(UTC).isoformat()},
            )
        raise SystemExit("Regression stopped: " + type(error).__name__) from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    main()
