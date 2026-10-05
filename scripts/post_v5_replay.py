"""Owner-approved post-fix replay on seen v5/v4 cases, NOT held-out evaluation."""

# ruff: noqa: S603, S607, T201 -- repo-scoped git; aggregate progress only.
from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import signal
import time
from pathlib import Path

from dotenv import dotenv_values
from evals.access import access
from evals.bindings import ROOT, bind
from evals.bound_execution import execute_bound
from evals.checkpoints import Checkpoints, exclusive, save
from evals.heldout import load
from evals.heldout_report import report
from evals.program_spec import ProgramSpec, serving_pin, specification, verify_envelope
from evals.serving import open_serving
from evals.studies.llm.final_run import FinalSpendGate, journal
from psycopg.conninfo import make_conninfo
from scripts.final_build_regression import implementation, unit
from scripts.post_v5_budget import CAP, RUN_ID, SCOPE, verify

from aclara.llm.client import StructuredClient
from aclara.llm.config import load_fallback_route, load_models, load_prices
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import Store

OUTPUT = ROOT / "artifacts/post-v5/replay"
LABEL = "Post-fix replay on seen cases, NOT held-out; official v4/v5 unchanged"
V5_PIN = "f6e7b15bcef3766b4933c1eb2ef95eb3118bdf46ffef6a9de6d2c1709a3ccaef"


def official_pins() -> dict[str, str]:
    paths = [
        ROOT / f"artifacts/final-program-v{version}/results.{extension}"
        for version in (4, 5)
        for extension in ("json", "md")
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


async def run(command: str) -> None:
    if os.getenv("POST_V5_REPLAY_APPROVED") != "1" or os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Owner-approved post-v5 start signal required")
    sha = implementation()
    specs = [
        ProgramSpec("test-v5", ROOT / "artifacts/evaluation-v5/customer-bindings.json", V5_PIN),
        specification("test-v4"),
    ]
    values = dotenv_values(ROOT / ".env")
    os.environ["EVAL_SERVING_DSN"] = os.getenv("EVAL_SERVING_DSN") or make_conninfo(
        host="127.0.0.1",
        port=values.get("POSTGRES_HOST_PORT") or "15432",
        dbname=values.get("POSTGRES_DB") or "aclara",
        user="aclara_app",
        password=values.get("OPS_APP_PASSWORD") or "",
    )
    serving_identity = serving_pin(specs[1])
    from scripts.azure_dev import VAULT, az
    from scripts.azure_migrate_ops import connection_string

    owner_dsn = connection_string("aclara_admin")
    verify(owner_dsn)
    os.environ["OPENROUTER_API_KEY"] = az(
        "keyvault", "secret", "show", "--vault-name", VAULT, "--name", "openrouter-api-key"
    )["value"]
    paths = [p for spec in specs for p in spec.release.iterdir() if p.is_file()]
    paths += [spec.bindings for spec in specs]
    paths += [
        ROOT / f"artifacts/charge_matcher/v1/dataset/{s}.jsonl"
        for s in ("train", "validation", "test")
    ]
    with exclusive(OUTPUT / "worker.lock"), access("post_v5_replay", paths, LABEL):
        exists = (OUTPUT / "release.json").exists()
        if exists != (command == "resume"):
            raise RuntimeError("Use start once; resume only the pinned attempt")
        header = {
            "label": LABEL,
            "implementation_sha": sha,
            "scope": SCOPE,
            "run_id": RUN_ID,
            "envelopes": {spec.suite: verify_envelope(spec) for spec in specs},
            "serving": serving_identity,
            "official_result_pins": official_pins(),
        }
        checkpoints = Checkpoints(OUTPUT, header)
        serving, store = open_serving(), None
        try:
            if not serving.temporal_quality_checked:
                raise RuntimeError("Temporal-quality serving column required")
            store = Store(connection_string("aclara_app"))
            models = load_models(ROOT / "config/models.yaml")
            models["nlu"] = models["phrase"] = models["default"]
            fallback = load_fallback_route(ROOT / "config/models.yaml", models)
            summaries, completed = {}, 0
            for spec in specs:
                suite, identities, directory = load(
                    serving, release=spec.release, binding_path=spec.bindings
                )
                if len(suite["scenarios"]) != 100:
                    raise RuntimeError("Approved replay inventory differs")
                rows = []
                for scenario in suite["scenarios"]:

                    async def execute(
                        path: Path, scenario=scenario, identities=identities, directory=directory
                    ):
                        fixture = bind(
                            scenario,
                            identities[scenario["persona"]["customer_ref"]],
                            directory,
                            serving,
                        )
                        llm = StructuredClient(
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
                        return await execute_bound(scenario, fixture, "P", llm_client=llm)

                    rows.append(
                        await unit(checkpoints, f"{spec.suite}:P:{scenario['id']}", execute)
                    )
                    completed += 1
                    save(
                        OUTPUT / "progress.json",
                        {"phase": "systems", "completed": completed, "planned": 200},
                    )
                summaries[spec.suite] = {
                    **report(rows, {**header, "system": "P", "suite": spec.suite}),
                    "failed_ids": sorted(r["id"] for r in rows if not r["passed"]),
                }
                save(OUTPUT / (spec.suite + "-results.json"), summaries[spec.suite])
            if official_pins() != header["official_result_pins"]:
                raise RuntimeError("Official result files changed")
            save(
                OUTPUT / "results.json",
                {"header": header, "suites": summaries, "budget": verify(owner_dsn)},
            )
            save(
                OUTPUT / "progress.json",
                {"phase": "COMPLETE", "completed": completed, "planned": 200},
            )
        finally:
            serving.store.close()
            if store is not None:
                store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "resume", "status"))
    args = parser.parse_args()
    if args.command == "status":
        path = OUTPUT / "progress.json"
        print(path.read_text() if path.exists() else '{"phase":"not_started"}')
        return
    started = time.time()
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        asyncio.run(run(args.command))
    except BaseException as error:
        save(
            OUTPUT / "STOPPED.json",
            {"error_type": type(error).__name__, "elapsed_seconds": time.time() - started},
        )
        raise SystemExit("Replay stopped: " + type(error).__name__) from None


if __name__ == "__main__":
    main()
