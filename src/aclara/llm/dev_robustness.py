"""Sequential, checkpointed real-P study on the pre-fix authored dev freeze only."""

# ruff: noqa: T201, S603, S607 -- aggregate CLI output; fixed repository git.
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
from collections import Counter
from dataclasses import asdict
from decimal import ROUND_CEILING, Decimal
from importlib import import_module
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import UUID

import psycopg
from dotenv import load_dotenv

from aclara.llm.client import StructuredClient
from aclara.llm.config import load_fallback_route, load_models, load_prices
from aclara.llm.dev_robustness_cases import ROOT, identity, materialize, validate
from aclara.llm.types import CallRecord

SCOPE, RUN_ID = "dev-gate/post-v3", "post-v3"
STOP = Decimal("0.90")
OUTPUT = ROOT / "artifacts/nlu-robustness-post-v3"


class DevBudgetStop(RuntimeError):
    """Do not let an accounting failure be scored as deterministic model fallback."""


def money(value: float) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite() or result < 0:
        raise DevBudgetStop("Invalid cost")
    return result.quantize(Decimal("0.00000001"), rounding=ROUND_CEILING)


def check_reserve(charged: Decimal, amount: Decimal) -> None:
    if charged < 0 or amount <= 0 or charged + amount > STOP:
        raise DevBudgetStop("Shared dev exposure plus reservation exceeds $0.90 stop")


class ThresholdGate:
    """Uses the same durable scope lock as the lead's llm.reserve/settle calls."""

    def __init__(self, connection: psycopg.Connection[Any]):
        self.connection = connection
        self.lock = RLock()

    def reserve(self, amount_usd: float) -> str:
        amount = money(amount_usd)
        try:
            with self.lock, self.connection.transaction():
                self.connection.execute("SET LOCAL ROLE aclara_owner")
                limit = self.connection.execute(
                    "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s FOR UPDATE",
                    (SCOPE,),
                ).fetchone()
                run = self.connection.execute(
                    "SELECT limit_usd,enabled FROM llm.runs WHERE scope=%s AND run_id=%s",
                    (SCOPE, RUN_ID),
                ).fetchone()
                if limit != (Decimal("1"), False) or run != (Decimal("1"), True):
                    raise DevBudgetStop("Expected shared dev scope changed or closed")
                used = self.connection.execute(
                    "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s",
                    (SCOPE,),
                ).fetchone()
                assert used is not None
                check_reserve(used[0], amount)
                row = self.connection.execute(
                    "SELECT llm.reserve(%s,%s,%s)", (SCOPE, RUN_ID, amount)
                ).fetchone()
                if not row or row[0] is None:
                    raise DevBudgetStop("Durable reservation denied")
                return str(row[0])  # transaction commits before external request
        except psycopg.Error:
            raise DevBudgetStop("Durable accounting unavailable") from None

    def settle(self, reservation: str, actual_usd: float | None) -> None:
        try:
            with self.lock, self.connection.transaction():
                self.connection.execute("SET LOCAL ROLE aclara_owner")
                row = self.connection.execute(
                    "SELECT llm.settle(%s,%s)",
                    (UUID(reservation), money(actual_usd) if actual_usd is not None else None),
                ).fetchone()
                if row != (True,):
                    raise DevBudgetStop("Settlement rejected; reserve retained")
        except psycopg.Error:
            raise DevBudgetStop("Settlement unavailable; reserve retained") from None


def save(path: Path, value: Any) -> None:
    pending = path.with_suffix(".tmp")
    with os.fdopen(os.open(pending, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600), "w") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)


def summarize(items: list[dict[str, Any]], calls: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = import_module("evals.metrics")
    proportions = {}
    for group in ("all", "es", "pt"):
        rows = items if group == "all" else [i for i in items if i["language"] == group]
        proportions[group] = metrics.proportion(sum(bool(i["passed"]) for i in rows), len(rows))
    attempted = [c for c in calls if c["provider"] != "typesafe" and c["status"] != "skipped"]
    slices = {}
    for tag in sorted({t for i in items for t in i["tags"]}):
        rows = [i for i in items if tag in i["tags"]]
        slices[tag] = metrics.proportion(sum(bool(i["passed"]) for i in rows), len(rows))
    known_cost = sum(c["cost_usd"] or 0 for c in calls)
    return {
        "complete": len(items) == 40,
        "success": proportions,
        "features": slices,
        "unsafe": dict(Counter(k for i in items for k, v in i["unsafe"].items() if v)),
        "forbidden_cases": sum(bool(i["forbidden_observed"]) for i in items),
        "injection_logged": sum(
            bool(i["action_targets"].get("log_security_event"))
            for i in items
            if "embedded_injection" in i["tags"]
        ),
        "call_status": dict(Counter(c["status"] for c in calls)),
        "schema_valid_all_attempts": metrics.proportion(
            sum(c["status"] == "valid" for c in attempted), len(attempted)
        ),
        "unknown_cost_attempts": sum(c["cost_usd"] is None for c in calls),
        "known_cost_usd": known_cost,
        "known_cost_per_completed_case_usd": known_cost / len(items) if items else None,
        "case_latency": metrics.latency([[i["case_ms"]] for i in items]),
        "turn_latency": metrics.latency([i["turn_ms"] for i in items]),
        "models": dict(Counter(c["model_id"] for c in calls)),
        "failures": [
            {k: i[k] for k in ("id", "outcome", "missing_actions", "forbidden_observed", "unsafe")}
            for i in items
            if not i["passed"]
        ],
    }


async def run(stage: str) -> dict[str, Any]:
    frozen = validate()
    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
    ).strip():
        raise RuntimeError("Real study requires a clean committed tree")
    output = OUTPUT / stage
    if output.exists():
        raise FileExistsError("Stage already exists; do not overwrite or repeat paid calls")
    if stage == "after":
        before = json.loads((OUTPUT / "before/launch.json").read_text())
        if before["freeze"] != frozen:
            raise RuntimeError("Before/after freeze differs")
    load_dotenv(ROOT / ".env", override=False)
    if not all(os.getenv(key) for key in ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY")):
        raise RuntimeError("Both approved local provider keys are required")
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Owner-approved scoped process must enable real calls")
    dsn = import_module("scripts.azure_migrate_ops").connection_string("aclara_admin")
    verify = import_module("scripts.post_v3_budget").verify
    initial = verify(dsn)
    if initial["charged_with_reserves_usd"] >= float(STOP):
        raise DevBudgetStop("Shared scope already reached requested stop")
    output.mkdir(parents=True, mode=0o700)
    save(
        output / "launch.json",
        {
            "sha": sha,
            "freeze": frozen,
            "scope": SCOPE,
            "run_id": RUN_ID,
            "stop_usd": float(STOP),
            "initial_budget": initial,
        },
    )
    calls: list[dict[str, Any]] = []
    current_id = ""

    def journal(record: CallRecord, parsed: dict[str, Any] | None) -> None:
        call = asdict(record)
        calls.append(call)
        with os.fdopen(
            os.open(output / "calls.jsonl", os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600), "w"
        ) as stream:
            stream.write(json.dumps({"id": current_id, "call": call, "validated": parsed}) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    models = load_models(ROOT / "config/models.yaml")
    models["nlu"] = models["phrase"] = models["default"]
    fallback = load_fallback_route(ROOT / "config/models.yaml", models)
    items: list[dict[str, Any]] = []
    error_type = None
    with psycopg.connect(dsn, autocommit=True) as connection:
        client = StructuredClient(
            models,
            load_prices(ROOT / "config/pricing.yaml"),
            budget_usd=None,
            daily_budget_usd=1,
            spend_gate=ThresholdGate(connection),
            response_record=journal,
            fallback_routes={"nlu": fallback, "phrase": fallback} if fallback else None,
            call_timeout_seconds=45,
        )
        cases, scenarios = materialize()
        bind = import_module("evals.bindings").bind
        execute = import_module("evals.bound_execution").execute_bound
        try:
            for spec, scenario in zip(cases, scenarios, strict=True):
                current_id = spec["id"]
                result = await execute(
                    scenario, bind(scenario, identity(spec)), "P", llm_client=client
                )
                result.update(tags=spec["tags"], locale=spec["locale"])
                save(output / (current_id + ".json"), result)
                items.append(result)
                print(
                    json.dumps(
                        {
                            "stage": stage,
                            "completed": len(items),
                            "planned": 40,
                            "passed": sum(bool(i["passed"]) for i in items),
                        }
                    ),
                    flush=True,
                )
        except Exception as exc:
            error_type = type(exc).__name__
    result = {
        "stage": stage,
        "sha": sha,
        **summarize(items, calls),
        "error_type": error_type,
        "budget_readback": verify(dsn),
    }
    save(output / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("before", "after"))
    args = parser.parse_args()
    try:
        result = asyncio.run(run(args.stage))
    except Exception as error:
        raise SystemExit("Dev robustness failed: " + type(error).__name__) from None
    # Failures are case-level private evidence; print aggregates only.
    print(json.dumps({k: v for k, v in result.items() if k != "failures"}, indent=2))
    if not result["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
