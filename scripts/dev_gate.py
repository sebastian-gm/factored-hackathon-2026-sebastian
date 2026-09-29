"""Option A synthetic-only acceptance with one shared durable $1 spend cap.

Does not import the final program, access frozen inputs, or deploy anything.
Checkpoints contain schema-validated dev evidence only, never model thinking.
"""

# ruff: noqa: T201, S603, S607 -- fixed repo-scoped git; aggregate-only CLI output.
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

import psycopg
import yaml
from evals.reactive import execute

from aclara.agent.nlu.rules import classify_nlu, extract_amount, normalize_text
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.bank.repository import TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.llm.config import load_fallback_route, load_models, load_prices
from aclara.llm.types import BudgetFailure, CallRecord, ModelFailure, ModelSpec, SpendGate
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import Store

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "evals/dev_scenarios_v2.yaml"
CONFIRMATION = ROOT / "src/aclara/llm/dev_confirmation_20.yaml"
OUTPUT = ROOT / "artifacts/option-a-dev"
SCOPE = "dev-gate/option-a"
RUN_ID = "option-a"


class DevBudgetStop(RuntimeError):
    """Fail closed: a shared budget error cannot be scored as model fallback."""


class DevSpendGate:
    def __init__(self, gate: SpendGate):
        self.gate = gate

    def reserve(self, amount_usd: float) -> str:
        try:
            return self.gate.reserve(amount_usd)
        except BudgetFailure as exc:
            raise DevBudgetStop("Shared dev budget unavailable or exhausted") from exc

    def settle(self, reservation: str, actual_usd: float | None) -> None:
        try:
            self.gate.settle(reservation, actual_usd)
        except BudgetFailure as exc:
            raise DevBudgetStop("Settlement failed; reservation retained") from exc


def save(path: Path, value: dict) -> None:
    pending = path.with_suffix(".tmp")
    with os.fdopen(os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)


def journal(path: Path):
    def write(record: CallRecord, structured: dict | None) -> None:
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "w") as stream:
            stream.write(
                json.dumps({"call": asdict(record), "validated_output": structured}) + "\n"
            )
            stream.flush()
            os.fsync(stream.fileno())

    return write


def mock_client() -> StructuredClient:
    """Message-only dev diagnostic; never receives scenario IDs or gold labels."""
    merchants = sorted({row.merchant_name for row in TransactionRepository()._rows})

    def answer(_system, user, schema):
        if schema is not ExtractedNlu:
            raise ModelFailure("Diagnostic uses deterministic grounded phrasing")
        message = user.partition("<customer_message>")[2].partition("</customer_message>")[0]
        frame = classify_nlu(message)
        amount = extract_amount(message)
        intent = frame.intent.value
        if intent == "fraud":
            intent = "card_lost_or_fraud"
        return json.dumps(
            {
                "language": frame.language,
                "intent": intent,
                "intent_confidence": frame.confidence,
                "merchant_expr": next(
                    (name for name in merchants if normalize_text(name) in normalize_text(message)),
                    None,
                ),
                "amount_expr": str(amount) if amount is not None else None,
                "currency_expr": "USD"
                if any(term in normalize_text(message) for term in ("dolar", "usd"))
                else None,
            }
        )

    return StructuredClient(
        {
            route: ModelSpec(provider="mock", model_id="dev-structured-mock")
            for route in ("nlu", "phrase")
        },
        {},
        mock_response=answer,
    )


def real_client(
    store: Store, output: Path, *, scope: str = SCOPE, run_id: str = RUN_ID
) -> StructuredClient:
    models = load_models(ROOT / "config/models.yaml")
    models["nlu"] = models["phrase"] = models["default"]
    fallback = load_fallback_route(ROOT / "config/models.yaml", models)
    return StructuredClient(
        models,
        load_prices(ROOT / "config/pricing.yaml"),
        budget_usd=None,
        daily_budget_usd=1,
        spend_gate=DevSpendGate(PostgresSpendGate(store, scope=scope, run_id=run_id)),
        fallback_routes={"nlu": fallback, "phrase": fallback} if fallback else None,
        call_timeout_seconds=45,
        response_record=journal(output),
    )


def budget_status(dsn: str, *, scope: str = SCOPE, run_id: str = RUN_ID) -> dict:
    with psycopg.connect(dsn) as connection:
        # Read-only owner access; never reset, raise, or re-enable the shared cap.
        limit = connection.execute(
            "SELECT daily_usd, disabled FROM llm.limits WHERE scope=%s", (scope,)
        ).fetchone()
        run = connection.execute(
            "SELECT limit_usd, enabled FROM llm.runs WHERE scope=%s AND run_id=%s", (scope, run_id)
        ).fetchone()
        if not limit or not run or float(limit[0]) != 1 or float(run[0]) != 1:
            raise DevBudgetStop("Expected shared $1 dev scope is absent or changed")
        used = connection.execute(
            "SELECT coalesce(sum(charged_usd),0), count(*) FROM llm.reservations WHERE scope=%s AND run_id=%s",
            (scope, run_id),
        ).fetchone()
        assert used is not None
        return {
            "scope": scope,
            "run_id": run_id,
            "cap_usd": 1,
            "charged_usd": float(used[0]),
            "attempts": used[1],
            "enabled": not limit[1] and run[1],
        }


def summarize(items: list[dict], complete: bool) -> dict:
    groups = {}
    for group in sorted({item["group"] for item in items}):
        rows = [item for item in items if item["group"] == group]
        groups[group] = {
            "n": len(rows),
            "passed": sum(bool(r.get("passed")) for r in rows),
            "errors": sum(bool(r.get("error_type") or r.get("execution_error")) for r in rows),
            "by_language": {
                language: {
                    "n": sum(r["language"] == language for r in rows),
                    "passed": sum(bool(r.get("passed")) for r in rows if r["language"] == language),
                }
                for language in ("es", "pt")
            },
            "faults_declared": sum(r.get("faults_declared", 0) for r in rows),
            "faults_fired": sum(r.get("faults_fired", 0) for r in rows),
        }
    unsafe = Counter(
        key for item in items for key, value in item.get("unsafe", {}).items() if value
    )
    forbidden = sum(bool(item.get("forbidden_observed")) for item in items)
    valid = {
        g: any(
            call["route"] == "nlu" and call["status"] == "valid" and call["provider"] != "mock"
            for i in items
            if i["group"] == g
            for call in i.get("calls", [])
        )
        for g in groups
    }
    passed = (
        complete
        and groups.get("dev", {}).get("passed", 0) >= 18
        and groups.get("confirmation", {}).get("passed", 0) >= 17
        and groups.get("faults", {}).get("passed", 0) == 12
        and groups.get("faults", {}).get("faults_fired", 0) == 12
        and not unsafe
        and not forbidden
        and all(not group["errors"] for group in groups.values())
        and all(valid.values())
    )
    return {
        "complete": complete,
        "gate_passed": passed,
        "groups": groups,
        "unsafe": dict(unsafe),
        "forbidden_writes_or_actions": forbidden,
        "real_nlu_present": valid,
        "known_cost_usd": sum(c["cost_usd"] or 0 for i in items for c in i.get("calls", [])),
        "charged_this_process_usd": sum(i.get("charged_usd", 0) for i in items),
        "unknown_cost_attempts": sum(
            c["cost_usd"] is None for i in items for c in i.get("calls", [])
        ),
    }


def attempt_output(
    output_root: Path, *, mode: str, profile: str, attempt: int, input_hashes: dict[str, str]
) -> Path:
    """Preserve the first run and allow one explicitly requested after-v2 follow-up."""
    if attempt not in {1, 2}:
        raise ValueError("Only the original run and one follow-up are supported")
    name = "gate-real" if mode == "real" else "gate-structured-mock"
    if attempt == 2:
        if profile != "after-v2" or mode != "real":
            raise ValueError("The follow-up is only authorized for the real after-v2 gate")
        first = output_root / "gate-real"
        launch = json.loads((first / "launch.json").read_text())
        result = json.loads((first / "results.json").read_text())
        if (
            launch.get("profile") != "after-v2"
            or launch.get("mode") != "real"
            or launch.get("scope") != "dev-gate/after-v2"
            or launch.get("run_id") != "after-v2"
            or launch.get("planned") != 52
            or result.get("complete") is not True
            or result.get("gate_passed") is not False
            or result.get("sha") != launch.get("sha")
            or {key: group.get("n") for key, group in result.get("groups", {}).items()}
            != {"dev": 20, "confirmation": 20, "faults": 12}
        ):
            raise ValueError("Follow-up requires the completed unsuccessful first gate")
        if input_hashes != launch.get("input_hashes"):
            raise ValueError("Follow-up must preserve both dev and confirmation inputs")
        name = "gate-real-followup"
    output = output_root / name
    if output.exists():
        raise FileExistsError("This gate attempt already exists; do not repeat it")
    return output


async def run(mode: str, *, profile: str = "option-a", attempt: int = 1) -> dict:
    if profile not in {"option-a", "after-v2", "post-v3"}:
        raise ValueError("Unknown dev gate profile")
    from scripts.after_v2_budget import RUN_ID as AFTER_RUN
    from scripts.after_v2_budget import SCOPE as AFTER_SCOPE
    from scripts.post_v3_budget import RUN_ID as POST_V3_RUN
    from scripts.post_v3_budget import SCOPE as POST_V3_SCOPE

    scope, run_id = {
        "after-v2": (AFTER_SCOPE, AFTER_RUN),
        "post-v3": (POST_V3_SCOPE, POST_V3_RUN),
    }.get(profile, (SCOPE, RUN_ID))
    output_root = {
        "after-v2": ROOT / "artifacts/after-v2-dev",
        "post-v3": ROOT / "artifacts/post-v3-dev",
    }.get(profile, OUTPUT)
    real = mode == "real"
    if real and os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Owner approval required")
    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if (
        real
        and subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
        ).strip()
    ):
        raise RuntimeError("Real acceptance requires a clean committed candidate")
    dev = yaml.safe_load(DEV.read_text())["scenarios"]
    cases = [("dev" if not s.get("faults") else "faults", s) for s in dev]
    hashes = {"dev": hashlib.sha256(DEV.read_bytes()).hexdigest()}
    if real:
        if profile in {"after-v2", "post-v3"}:
            from aclara.llm.dev_offer_scenarios import CASES, load_offer_scenarios

            confirmation = load_offer_scenarios()
            confirmation_path = CASES
            expected_hash = "47e4278b017e70b679f977807e00b970aa7d67114eb68f1a168b15549c1aed2e"
        else:
            confirmation = yaml.safe_load(CONFIRMATION.read_text())["scenarios"]
            confirmation_path = CONFIRMATION
            expected_hash = "5a828ca67ffa836b29fcb6799064738c3111f990526c12a497951ee0de223ffe"
        if (
            len(confirmation) != 20
            or Counter(s["language"] for s in confirmation) != {"es": 10, "pt": 10}
            or any(s.get("faults") for s in confirmation)
        ):
            raise ValueError("Confirmation set structure changed")
        hashes["confirmation"] = hashlib.sha256(confirmation_path.read_bytes()).hexdigest()
        if hashes["confirmation"] != expected_hash:
            raise ValueError("Confirmation bytes changed since the pre-fix freeze")
        cases += [("confirmation", s) for s in confirmation]
    output = attempt_output(
        output_root, mode=mode, profile=profile, attempt=attempt, input_hashes=hashes
    )
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "launch.json",
        {
            "sha": sha,
            "mode": mode,
            "profile": profile,
            "attempt": attempt,
            "scope": scope,
            "run_id": run_id,
            "input_hashes": hashes,
            "planned": len(cases),
        },
    )
    store = None
    owner_dsn = None
    items: list[dict[str, Any]] = []
    completed = False
    try:
        if real:
            from scripts.azure_dev import VAULT, az
            from scripts.azure_migrate_ops import connection_string

            owner_dsn = connection_string("aclara_admin")
            before = budget_status(owner_dsn, scope=scope, run_id=run_id)
            save(output / "budget-before.json", before)
            if not before["enabled"]:
                raise DevBudgetStop("Shared scope disabled")
            store = Store(connection_string("aclara_app"))
            for name, secret in (
                ("OPENROUTER_API_KEY", "openrouter-api-key"),
                ("TYPESAFE_API_KEY", "typesafe-api-key"),
            ):
                os.environ[name] = az(
                    "keyvault", "secret", "show", "--vault-name", VAULT, "--name", secret
                )["value"]
        for index, (group, scenario) in enumerate(cases):
            client = (
                real_client(store, output / "calls.jsonl", scope=scope, run_id=run_id)
                if store
                else mock_client()
            )
            item = {
                "id": scenario["id"],
                "language": scenario["language"],
                "group": group,
                "faults_declared": len(scenario.get("faults", [])),
            }
            try:
                item.update(await execute(scenario, "P", llm_client=client, require_faults=False))
            except (DevBudgetStop, BudgetFailure):
                item["error_type"] = "budget_stop"
                raise
            except Exception as exc:
                item["error_type"] = type(exc).__name__
            finally:
                item["calls"] = [asdict(record) for record in client.records]
                item["charged_usd"] = client.spent_usd
                save(output / f"case-{index:03d}.json", item)
                items.append(item)
                save(
                    output / "progress.json",
                    {"completed": len(items), "planned": len(cases), "phase": group, "sha": sha},
                )
            print(
                json.dumps({"phase": group, "completed": len(items), "planned": len(cases)}),
                flush=True,
            )
        completed = True
    finally:
        if store:
            store.close()
        report = {"sha": sha, "mode": mode, "attempt": attempt, **summarize(items, completed)}
        if owner_dsn:
            report["shared_budget"] = budget_status(owner_dsn, scope=scope, run_id=run_id)
        save(output / "results.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("mock", "real"))
    parser.add_argument(
        "--profile", choices=("option-a", "after-v2", "post-v3"), default="option-a"
    )
    parser.add_argument("--attempt", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    try:
        result = asyncio.run(run(args.mode, profile=args.profile, attempt=args.attempt))
        print(json.dumps(result))
        if args.mode == "real" and not result["gate_passed"]:
            raise SystemExit(1)
    except Exception as exc:
        raise SystemExit("Dev gate stopped: " + type(exc).__name__) from None


if __name__ == "__main__":
    main()
