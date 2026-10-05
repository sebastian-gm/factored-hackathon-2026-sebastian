"""Prepared single-pass v5 wrapper. Frozen reads require the later suite-merged GO."""

# ruff: noqa: S603, S607, T201 -- repository-scoped git; sanitized progress only.
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import signal
import subprocess
import time

import numpy as np
from dotenv import dotenv_values
from evals.access import access
from evals.bindings import ROOT, bind
from evals.bound_execution import execute_bound
from evals.checkpoints import Checkpoints, atomic_write, exclusive, save
from evals.heldout import load
from evals.heldout_report import DRAWS, SEED, report
from evals.metrics import UNSAFE
from evals.observations import FORBIDDEN
from evals.program_spec import ProgramSpec, serving_pin, verify_envelope
from evals.serving import open_serving
from evals.studies.llm.final_run import FinalSpendGate, journal, require_start
from psycopg.conninfo import make_conninfo
from scripts.final_build_regression import unit
from scripts.v5_budget import CAP, RUN_ID, SCOPE, verify

from aclara.llm.client import StructuredClient
from aclara.llm.config import load_fallback_route, load_models, load_prices
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import Store

OUTPUT = ROOT / "artifacts/final-program-v5"


def implementation() -> str:
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()

    if os.getenv("V5_SUITE_MERGED_GO") != "1":
        raise RuntimeError("Wait for the owner's v5 suite merged GO")
    require_start()
    if git("status", "--porcelain") or git("branch", "--show-current") != "main":
        raise RuntimeError("A clean main checkout is required")
    sha = git("rev-parse", "HEAD")
    if sha != git("rev-parse", "origin/main") or git(
        "diff", "--stat", "v1.0.0", "HEAD", "--", "src", "apps", "prompts", "config", "infra"
    ):
        raise RuntimeError("Main differs from origin or from the frozen v1 product")
    return sha


def paired(b1: list[dict], p: list[dict]) -> dict:
    """Same primary single-run SAR bootstrap as v4; no fictitious repeats."""
    b, proposed = {c["id"]: c for c in b1}, {c["id"]: c for c in p}
    if len(b) != len(b1) or len(proposed) != len(p) or b.keys() != proposed.keys():
        raise ValueError("Paired inventory differs")
    ids = [i for i in sorted(b) if b[i]["in_scope"]]
    if any(b[i]["in_scope"] != proposed[i]["in_scope"] for i in b):
        raise ValueError("Paired gold scope differs")
    values = np.array([int(proposed[i]["sar"]) - int(b[i]["sar"]) for i in ids], dtype=float)
    if not len(values):
        return {"n": len(b), "in_scope_n": 0, "difference": None, "paired_95": None}
    rng = np.random.default_rng(SEED)
    samples = values[rng.integers(0, len(values), (DRAWS, len(values)))].mean(axis=1)
    return {
        "n": len(b),
        "in_scope_n": len(values),
        "difference": float(values.mean()),
        "paired_95": np.quantile(samples, [0.025, 0.975]).tolist(),
        "bootstrap_draws": DRAWS,
        "seed": SEED,
    }


async def run(args) -> None:
    sha = implementation()  # No frozen reads before this authorization check.
    bindings = (ROOT / args.bindings).resolve()
    if not bindings.is_relative_to(ROOT / "artifacts"):
        raise ValueError("Bindings must stay in ignored artifacts")
    spec = ProgramSpec(args.suite, bindings, args.manifest_pin)
    values = dotenv_values(ROOT / ".env")
    os.environ["EVAL_SERVING_DSN"] = os.getenv("EVAL_SERVING_DSN") or make_conninfo(
        host="127.0.0.1",
        port=values.get("POSTGRES_HOST_PORT") or "15432",
        dbname=values.get("POSTGRES_DB") or "aclara",
        user="aclara_app",
        password=values.get("OPS_APP_PASSWORD") or "",
    )
    # Reuse v4's strict local/non-owner endpoint validation without changing it.
    local = serving_pin(ProgramSpec("test-v4", bindings, args.manifest_pin))
    from scripts.azure_dev import VAULT, az
    from scripts.azure_migrate_ops import connection_string

    owner_dsn = connection_string("aclara_admin")
    verify(owner_dsn)
    os.environ["OPENROUTER_API_KEY"] = az(
        "keyvault", "secret", "show", "--vault-name", VAULT, "--name", "openrouter-api-key"
    )["value"]
    paths = [p for p in spec.release.iterdir() if p.is_file()] + [bindings]
    paths += [
        ROOT / f"artifacts/charge_matcher/v1/dataset/{s}.jsonl"
        for s in ("train", "validation", "test")
    ]
    with (
        exclusive(OUTPUT / "worker.lock"),
        access(
            "v5_blind_evaluation",
            paths,
            "Owner-authorized independent v5; unchanged v1 product, no tuning",
        ),
    ):
        if (OUTPUT / "release.json").exists():
            raise RuntimeError(
                "Existing attempt: no automatic replay; request infrastructure recovery"
            )
        envelope = verify_envelope(spec)
        serving = open_serving()
        store = None
        try:
            if not serving.temporal_quality_checked:
                raise RuntimeError("Temporal-quality serving column required")
            suite, identities, directory = load(
                serving, release=spec.release, binding_path=bindings
            )
            if len(suite["scenarios"]) != 100:
                raise ValueError("Approved workload requires 100 cases")
            store = Store(connection_string("aclara_app"))
            models = load_models(ROOT / "config/models.yaml")
            models["nlu"] = models["phrase"] = models["default"]
            fallback = load_fallback_route(ROOT / "config/models.yaml", models)
            header = {
                "suite": args.suite,
                "implementation_sha": sha,
                "product_sha": subprocess.check_output(
                    ["git", "-C", str(ROOT), "rev-parse", "v1.0.0^{commit}"], text=True
                ).strip(),
                **envelope,
                "serving": local,
                "dataset_version": serving.dataset_version,
                "model": models["default"].model_id,
                "fallback": models[fallback].model_id if fallback else None,
                "scope": SCOPE,
                "run_id": RUN_ID,
                "official_v4_unchanged": True,
                "label": "Independent blind v5 check on final build; one pass per system",
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in paths
                },
                "repeats": 0,
                "judges": 0,
            }
            checkpoints = Checkpoints(OUTPUT, header)
            rows = []
            for system in ("B1", "P"):
                for scenario in suite["scenarios"]:

                    async def execute(path, scenario=scenario, system=system):
                        fixture = bind(
                            scenario,
                            identities[scenario["persona"]["customer_ref"]],
                            directory,
                            serving,
                        )
                        client = (
                            StructuredClient(
                                models,
                                load_prices(ROOT / "config/pricing.yaml"),
                                budget_usd=None,
                                daily_budget_usd=float(CAP),
                                spend_gate=FinalSpendGate(
                                    PostgresSpendGate(store, scope=SCOPE, run_id=RUN_ID)
                                ),
                                fallback_routes={"nlu": fallback, "phrase": fallback}
                                if fallback
                                else None,
                                call_timeout_seconds=45,
                                response_record=journal(path),
                            )
                            if system == "P"
                            else None
                        )
                        return await execute_bound(scenario, fixture, system, llm_client=client)

                    rows.append(await unit(checkpoints, f"{system}:0:{scenario['id']}", execute))
                    save(
                        OUTPUT / "progress.json",
                        {"phase": "systems", "completed": len(rows), "planned": 200},
                    )
            systems = {}
            for system in ("B1", "P"):
                cases = [c for c in rows if c["system"] == system]
                systems[system] = report(cases, {**header, "system": system})
                systems[system]["failed_ids"] = sorted(c["id"] for c in cases if not c["passed"])
                systems[system]["unsafe_ids"] = {
                    k: sorted(c["id"] for c in cases if c["unsafe"][k]) for k in UNSAFE
                }
                systems[system]["forbidden_ids"] = {
                    k: sorted(c["id"] for c in cases if k in c["forbidden_observed"])
                    for k in sorted(FORBIDDEN)
                }
            budget = verify(owner_dsn)
            results = {
                "header": header,
                "systems": systems,
                "paired_comparison": paired(
                    [c for c in rows if c["system"] == "B1"],
                    [c for c in rows if c["system"] == "P"],
                ),
                "durable_budget": budget,
            }
            save(OUTPUT / "results.json", results)
            atomic_write(
                OUTPUT / "results.md",
                "# Independent blind v5 check\n\nOfficial v4 unchanged.\n\n```json\n"
                + json.dumps(results, indent=2)
                + "\n```\n",
            )
            save(OUTPUT / "progress.json", {"phase": "COMPLETE", "completed": 200, "planned": 200})
        finally:
            serving.store.close()
            if store is not None:
                store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "status"))
    parser.add_argument("--suite", choices=("test-v5",), required=True)
    parser.add_argument("--bindings", default="artifacts/evaluation-v5/customer-bindings.json")
    parser.add_argument("--manifest-pin", required=True)
    args = parser.parse_args()
    if args.command == "status":
        path = OUTPUT / "progress.json"
        print(path.read_text() if path.exists() else '{"phase":"not_started"}')
        return
    if len(args.manifest_pin) != 64 or any(c not in "0123456789abcdef" for c in args.manifest_pin):
        raise SystemExit("Invalid manifest pin")
    started = time.time()

    def stop(_signum, _frame):
        raise InterruptedError("Preserve checkpoints; no automatic replay")

    def watchdog(_signum, _frame):
        progress = OUTPUT / "progress.json"
        last = max(started, progress.stat().st_mtime if progress.exists() else 0)
        if time.time() - last >= 900 or time.time() - started >= 10800:
            raise TimeoutError("Stall or wall-clock limit")

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGALRM, watchdog)
    signal.setitimer(signal.ITIMER_REAL, 30, 30)
    try:
        asyncio.run(run(args))
    except BaseException as error:
        import traceback

        save(
            OUTPUT / "STOPPED.json",
            {
                "error_class": type(error).__name__,
                "frames": [
                    {"function": frame.name, "line": frame.lineno}
                    for frame in traceback.extract_tb(error.__traceback__)
                ],
            },
        )
        raise SystemExit("V5 stopped: " + type(error).__name__) from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    main()
