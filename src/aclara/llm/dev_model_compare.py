"""Paired, checkpointed P comparison on the owner-approved frozen dev sample.

Application defaults, production budgets, prompts and orchestration stay intact.
The only real-call scope is dev-gate/model-compare; no held-out discovery.
"""

# ruff: noqa: T201, S603, S607 -- aggregate CLI output and fixed repository git.
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
from collections import Counter
from dataclasses import asdict, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from html import unescape
from importlib import import_module
from time import perf_counter
from typing import Any, TypeVar
from urllib.request import Request, urlopen

import psycopg
from dotenv import load_dotenv
from pydantic import BaseModel

from aclara.agent.nlu.rules import detect_language_evidence, normalize_text
from aclara.agent.nlu.structured import ExtractedNlu, postprocess
from aclara.llm.client import StructuredClient
from aclara.llm.config import Price, load_fallback_route, load_models, load_prices
from aclara.llm.dev_latency import retry_analysis
from aclara.llm.dev_prompt_study import StudyCase, comparison_sample, inventory_hash
from aclara.llm.dev_robustness import DevBudgetStop, ThresholdGate, save, summarize
from aclara.llm.dev_robustness_cases import ROOT
from aclara.llm.types import BudgetFailure, CallRecord, ModelSpec

SCOPE, RUN_ID, CAP = "dev-gate/model-compare", "model-compare", Decimal("1.50")
OUTPUT = ROOT / "artifacts/dev-model-compare/paired"
GEMINI, SOL = "google/gemini-3-flash-preview", "openai/gpt-6.1-sol"
COMPARISON_ATTEMPT_SECONDS, COMPARISON_CALL_SECONDS = 30, 65
T = TypeVar("T", bound=BaseModel)
TRUTH = ROOT / "src/aclara/llm/dev_model_compare_slots.json"


def candidate_config(candidate: str) -> tuple[dict[str, ModelSpec], dict[str, Price], str | None]:
    models = load_models(ROOT / "config/models.yaml")
    prices = load_prices(ROOT / "config/pricing.yaml")
    # Ability comparison: neither arm inherits the serving route's short first
    # attempt. Report deadline failures separately from semantic/model errors.
    spec = replace(
        models["default"],
        price_ceiling=(0.5, 3.0),
        timeout_seconds=COMPARISON_ATTEMPT_SECONDS,
        first_attempt_timeout_seconds=None,
    )
    if spec.model_id != GEMINI or spec.provider_only != ("google-vertex/global",):
        raise ValueError("Selected Gemini configuration changed; re-review study pins")
    if candidate == "sol":
        spec = replace(
            spec,
            model_id=SOL,
            price_id="study-gpt-6.1-sol-azure",
            provider_only=("azure",),
            price_ceiling=(2.0, 10.0),
            reasoning_effort="low",
            max_tokens_parameter="max_completion_tokens",
        )
        # Conservative cache estimate; billed per-call usage.cost wins.
        prices[spec.price_id or ""] = Price(
            2.0,
            10.0,
            2.0,
            2.0,
            date(2026, 9, 30),
            "https://openrouter.ai/api/v1/models/openai/gpt-6.1-sol/endpoints",
        )
    elif candidate != "gemini":
        raise ValueError("Unknown approved candidate")
    models["nlu"] = models["phrase"] = spec
    fallback = load_fallback_route(ROOT / "config/models.yaml", models)
    return models, prices, fallback


def budget_receipt(connection: psycopg.Connection[Any]) -> dict[str, Any]:
    with connection.transaction():
        return _budget_receipt(connection)


def _budget_receipt(connection: psycopg.Connection[Any]) -> dict[str, Any]:
    connection.execute("SET LOCAL ROLE aclara_owner")
    if connection.execute(
        "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (SCOPE,)
    ).fetchone() != (CAP, False):
        raise DevBudgetStop("Confirmed comparison scope changed or disabled")
    if connection.execute(
        "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (SCOPE,)
    ).fetchall() != [(RUN_ID, CAP, True)]:
        raise DevBudgetStop("Comparison must share one lifetime-capped run")
    row = connection.execute(
        "SELECT count(*),coalesce(sum(actual_usd),0),coalesce(sum(charged_usd),0),"
        "count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope=%s",
        (SCOPE,),
    ).fetchone()
    total = connection.execute(
        "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations"
    ).fetchone()
    remaining_dev = connection.execute(
        "SELECT greatest(0,%s-coalesce(sum(charged_usd),0)) FROM llm.reservations WHERE scope=%s",
        (Decimal("0.90"), "dev-gate/pre-v4"),
    ).fetchone()
    assert row and total and remaining_dev
    # Retain all unknown costs and the other open dev scope. The lead allocates
    # future final/smoke caps; already-charged future work must not be counted twice.
    maximum = total[0] + max(Decimal(0), CAP - row[2]) + remaining_dev[0]
    if row[2] > CAP or maximum > Decimal("12"):
        raise DevBudgetStop("Comparison exposure would violate cumulative approval")
    return {
        "scope": SCOPE,
        "run_id": RUN_ID,
        "cap_usd": float(CAP),
        "attempts": row[0],
        "known_cost_usd": float(row[1]),
        "charged_with_reserves_usd": float(row[2]),
        "unknown_cost_attempts": row[3],
        "all_scopes_charged_usd": float(total[0]),
        "conservative_maximum_usd": float(maximum),
        "planning_maximum_with_additional_3_20_usd": float(maximum + Decimal("3.20")),
    }


def require_credits() -> None:
    """Free health metadata only; do not save or print keys/balances."""
    try:
        with urlopen(
            Request(
                "https://openrouter.ai/api/v1/credits",
                headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]},
            ),
            timeout=20,
        ) as response:
            data = json.load(response)["data"]
        available = Decimal(str(data["total_credits"])) > Decimal(str(data["total_usage"]))
    except Exception:
        raise DevBudgetStop("Free provider-health check unavailable; no inference") from None
    if not available:
        raise DevBudgetStop("Provider account credits exhausted; no inference")


def guard_attempt(record: CallRecord) -> None:
    """Stop after journaling one unknown bill, before any retry or fallback.

    Never replace unknown usage with zero or release its durable reservation.
    BudgetFailure also lets the concurrent Jev result settle before NLU exits.
    """
    if record.cost_usd is None and record.status != "skipped":
        raise BudgetFailure("Unknown provider cost; stop comparison before more calls")
    if record.stop_reason in {
        "http_401",
        "provider_401",  # credential/entitlement failures
        "http_402",
        "provider_402",  # exhausted credits, including HTTP-200 envelopes
        "http_403",
        "provider_403",  # forbidden or provider/account budget limits
        "http_429",
        "provider_429",  # quota/rate limits: never burn comparison retries
    }:
        raise BudgetFailure("Provider account, credit or quota failure; stop comparison")


def require_catalog() -> dict[str, Any]:
    """Fresh free ZDR catalog verification; cheaper non-ZDR routes never qualify."""
    try:
        with urlopen(
            Request(
                "https://openrouter.ai/api/v1/endpoints/zdr",
                headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]},
            ),
            timeout=20,
        ) as response:
            raw = response.read()
        rows = json.loads(raw)["data"]
        for name in ("gemini", "sol"):
            spec = candidate_config(name)[0]["nlu"]
            matches = [
                r
                for r in rows
                if r["model_id"] == spec.model_id
                and r["tag"] in spec.provider_only
                and r.get("status") == 0
            ]
            if len(matches) != 1 or not {
                "response_format",
                "structured_outputs",
                spec.max_tokens_parameter,
            } <= set(matches[0]["supported_parameters"]):
                raise ValueError("Approved ZDR structured-output route unavailable")
            price = matches[0]["pricing"]
            assert spec.price_ceiling is not None
            if any(
                Decimal(str(price[key])) * 1_000_000 > Decimal(str(ceiling))
                for key, ceiling in zip(("prompt", "completion"), spec.price_ceiling, strict=True)
            ):
                raise ValueError("Approved route exceeds pinned token prices")
    except Exception:
        raise DevBudgetStop("Free ZDR/catalog verification failed; no inference") from None
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "zdr_catalog_sha256": sha256(raw).hexdigest(),
        "paid_calls": 0,
    }


def pins(cases: list[StudyCase]) -> dict[str, Any]:
    names = [
        "config/models.yaml",
        "config/pricing.yaml",
        "prompts/nlu/v5.md",
        "prompts/phrase/v2.md",
        "evals/reactive.py",
        "evals/bound_execution.py",
        "evals/metrics.py",
        "evals/bindings.py",
        "evals/observations.py",
        "evals/runner.py",
        "src/aclara/llm/dev_model_compare_50.manifest.json",
        "src/aclara/llm/dev_model_compare_slots.json",
        "src/aclara/llm/dev_model_compare_slots.sha256",
    ]
    names += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "src/aclara").rglob("*.py"))]
    return {
        "sample_sha256": inventory_hash(cases),
        "files": {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in names},
        "candidates": {
            name: asdict(candidate_config(name)[0]["nlu"]) for name in ("gemini", "sol")
        },
        "risk_union": "same Jev questions and 0.5 threshold in both arms",
        "order": "alternate first model per pair; frozen round-robin cases; sequential case-runs",
        "logical_call_seconds": COMPARISON_CALL_SECONDS,
        "unknown_cost_policy": "stop on first unknown; retain reserve; no paid retry/fallback",
    }


def slot_counts(actual: dict[str, Any] | None, gold: dict[str, Any]) -> dict[str, int]:
    """Exact normalized populated-slot micro F1; null/null is not a true positive."""
    tp = fp = fn = 0
    for key, expected in gold.items():
        predicted = (actual or {}).get(key)
        if key == "merchant_expr":
            predicted = normalize_text(predicted).strip() if predicted else None
            expected = normalize_text(expected).strip() if expected else None
        if key == "amount_value":
            predicted = Decimal(str(predicted)) if predicted is not None else None
            expected = Decimal(str(expected)) if expected is not None else None
        if predicted == expected and expected is not None:
            tp += 1
        else:
            fp += predicted is not None
            fn += expected is not None
    return {"tp": tp, "fp": fp, "fn": fn}


def load_slot_truth(cases: list[StudyCase]) -> dict[str, Any]:
    raw = TRUTH.read_bytes()
    if sha256(raw).hexdigest() != TRUTH.with_suffix(".sha256").read_text().split()[0]:
        raise ValueError("Independent opening-slot annotation freeze changed")
    data: dict[str, Any] = json.loads(raw)
    if data["sample_sha256"] != inventory_hash(cases) or set(data["cases"]) != {
        c.scenario["id"] for c in cases
    }:
        raise ValueError("Independent opening-slot annotations differ from frozen sample")
    annotations: dict[str, Any] = data["cases"]
    return annotations  # separate annotations never modify scenario gold


class ComparisonClient(StructuredClient):
    """Record first logical NLU's normalized slots without changing its result."""

    first_nlu_attempted = False
    first_slots: dict[str, Any] | None = None
    request_index = 0
    country: str | None = None
    bank_clock = datetime(2026, 6, 18, 6, tzinfo=UTC)

    def generate(
        self,
        route: str,
        system: str,
        user: str,
        schema: type[T],
        *,
        prompt_id: str,
        prompt_hash: str | None = None,
    ) -> T:
        self.request_index += 1
        first = route == "nlu" and not self.first_nlu_attempted
        if first:
            self.first_nlu_attempted = True
        result = super().generate(
            route, system, user, schema, prompt_id=prompt_id, prompt_hash=prompt_hash
        )
        if first and isinstance(result, ExtractedNlu):
            match = re.search(r"<customer_message>\n(.*?)\n</customer_message>", user, re.S)
            self.first_slots = postprocess(
                result,
                country=self.country,
                bank_clock=self.bank_clock,
                message=unescape(match[1]) if match else None,
            ).slots.model_dump(mode="json")
        return result


def report(items: list[dict[str, Any]], calls: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = import_module("evals.metrics")
    by_candidate = {m: {r["id"] for r in items if r["candidate"] == m} for m in ("gemini", "sol")}
    paired = set.intersection(*by_candidate.values())
    result: dict[str, Any] = {"complete_pairs": len(paired), "planned_pairs": 50, "arms": {}}
    for candidate in ("gemini", "sol"):
        rows = [r for r in items if r["candidate"] == candidate]
        arm_calls = [c for c in calls if c["candidate"] == candidate]
        # All attempts, including an interrupted case, stay in the cost denominator.
        slices = {}
        for language in ("all", "es", "pt"):
            selected = [
                r
                for r in rows
                if r["id"] in paired and (language == "all" or r["language"] == language)
            ]
            slot = Counter({"tp": 0, "fp": 0, "fn": 0})
            for row in selected:
                slot.update(row.get("opening_slots", {}))
            denominator = 2 * slot["tp"] + slot["fp"] + slot["fn"]
            slice_calls = [
                c for c in arm_calls if language == "all" or c.get("language") == language
            ]
            attempted_ids = {c["id"] for c in slice_calls} | {
                r["id"] for r in rows if language == "all" or r["language"] == language
            }
            known_cost = sum(c["cost_usd"] or 0 for c in slice_calls)
            slices[language] = {
                "objective": metrics.aggregate(selected, {"dev_only": True}),
                "objective_pass": metrics.proportion(
                    sum(bool(r["passed"]) for r in selected), len(selected)
                ),
                "opening_slot_counts": dict(slot),
                "opening_slot_f1": 2 * slot["tp"] / denominator if denominator else None,
                "opening_slot_cases": sum("opening_slots" in r for r in selected),
                "slot_nlu_unreached": sum(r.get("opening_nlu_unreached", False) for r in selected),
                "confident_reply_language_error_cases": metrics.proportion(
                    sum(bool(r["reply_language_errors"]) for r in selected), len(selected)
                ),
                "reply_language_uncertain": sum(r["reply_language_uncertain"] for r in selected),
                "all_attempts": {
                    "attempted_cases": len(attempted_ids),
                    "known_cost_usd": known_cost,
                    "known_cost_per_attempted_case_usd": known_cost / len(attempted_ids)
                    if attempted_ids
                    else None,
                    "unknown_cost_attempts": sum(c["cost_usd"] is None for c in slice_calls),
                    "retry_latency": retry_analysis(slice_calls),
                },
            }
        result["arms"][candidate] = {
            "completed": len(rows),
            "attempted_cases": len({c["id"] for c in arm_calls} | {r["id"] for r in rows}),
            "sets": dict(Counter(r["study_set"] for r in rows)),
            "paired_slices": slices,
            "attempts": summarize(rows, arm_calls, planned=50),
            "retry_latency": retry_analysis(arm_calls),
            "fallback_cases": sum(
                any(c["route"].startswith("fallback_") and c["id"] == r["id"] for c in arm_calls)
                for r in rows
            ),
        }
    return result


async def run(*, real: bool, resume: bool = False) -> dict[str, Any]:
    cases = comparison_sample()
    truth = load_slot_truth(cases)
    study_pins = pins(cases)
    output = OUTPUT if real else OUTPUT.with_name("mock")
    if real:
        load_dotenv(ROOT / ".env", override=False)
    if os.getenv("LLM_PROVIDER", "mock") != "mock":
        raise RuntimeError("Global app must remain mock")
    if real:
        if os.getenv("LLM_REAL_CALLS_APPROVED") != "1" or not os.getenv("TYPESAFE_API_KEY"):
            raise RuntimeError("Scoped real calls need owner approval and both local keys")
        if subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
        ).strip():
            raise RuntimeError("Commit comparison implementation before real calls")
        require_credits()
        catalog = require_catalog()
        dsn = import_module("scripts.azure_migrate_ops").connection_string("aclara_admin")
        connection = psycopg.connect(dsn, autocommit=True)
    else:
        catalog = {"paid_calls": 0}
        if os.getenv("LLM_REAL_CALLS_APPROVED") != "0":
            raise RuntimeError("Mock check requires approval disabled")
        connection = None
    calls: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    error_type = None
    interrupted = None
    stage_ready = False
    try:
        initial = budget_receipt(connection) if connection else {"paid_calls": 0}
        if output.exists():
            if not resume or json.loads((output / "launch.json").read_text())["pins"] != json.loads(
                json.dumps(study_pins)
            ):
                raise RuntimeError(
                    "Existing stage: explicit resume with identical code/data/config pins only"
                )
            calls = (
                [
                    json.loads(line)["call"]
                    for line in (output / "calls.jsonl").read_text().splitlines()
                ]
                if (output / "calls.jsonl").exists()
                else []
            )
        else:
            if resume:
                raise RuntimeError("No stage to resume")
            output.mkdir(parents=True, mode=0o700)
            save(
                output / "launch.json",
                {
                    "pins": study_pins,
                    "initial_budget": initial,
                    "catalog": catalog,
                    "scope": SCOPE if real else None,
                    "run_id": RUN_ID if real else None,
                    "sha": subprocess.check_output(
                        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
                    ).strip(),
                },
            )
        stage_ready = True
        current: StudyCase
        candidate: str
        client: ComparisonClient

        def journal(record: CallRecord, parsed: dict[str, Any] | None) -> None:
            call = {
                **asdict(record),
                "id": current.scenario["id"],
                "candidate": candidate,
                "request_index": client.request_index,
                "group": current.group,
                "language": current.scenario["language"],
            }
            calls.append(call)
            with os.fdopen(
                os.open(output / "calls.jsonl", os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600), "w"
            ) as stream:
                stream.write(json.dumps({"call": call, "validated": parsed}) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            guard_attempt(record)

        bound = import_module("evals.bound_execution").execute_bound
        bind = import_module("evals.bindings").bind
        legacy = import_module("evals.reactive").execute
        for index, current in enumerate(cases):
            for candidate in ("gemini", "sol") if index % 2 == 0 else ("sol", "gemini"):
                case_file = output / f"{candidate}.{current.scenario['id']}.json"
                started_file = case_file.with_suffix(".started.json")
                if case_file.exists():
                    items.append(json.loads(case_file.read_text()))
                    continue
                if started_file.exists():
                    # An interrupted paid conversation is never silently billed again.
                    continue
                if connection:
                    budget_receipt(connection)
                models, prices, fallback = candidate_config(candidate)
                if not real:
                    models = {
                        k: replace(s, provider="mock", key_env=None) for k, s in models.items()
                    }
                    fallback = None
                client = ComparisonClient(
                    models,
                    prices,
                    budget_usd=None if real else 0,
                    daily_budget_usd=float(CAP),
                    spend_gate=ThresholdGate(
                        connection, scope=SCOPE, run_id=RUN_ID, cap=CAP, stop=CAP
                    )
                    if connection
                    else None,
                    response_record=journal,
                    call_timeout_seconds=COMPARISON_CALL_SECONDS,
                    fallback_routes={"nlu": fallback, "phrase": fallback} if fallback else None,
                    risk_second_opinion_enabled=True,
                )
                client.country = current.binding["selector"]["country"] if current.binding else "MX"
                client.bank_clock = datetime.fromisoformat(
                    current.scenario.get("bank_clock", "2026-06-18T06:00:00Z").replace(
                        "Z", "+00:00"
                    )
                )
                interrupted = {"candidate": candidate, "id": current.scenario["id"]}
                save(started_file, interrupted)
                call_start = len(calls)
                started = perf_counter()
                row = (
                    await bound(
                        current.scenario,
                        bind(current.scenario, current.binding),
                        "P",
                        llm_client=client,
                    )
                    if current.binding
                    else await legacy(current.scenario, "P", llm_client=client)
                )
                row.setdefault("case_ms", (perf_counter() - started) * 1000)
                merchants = tuple(
                    r["merchant_name"]
                    for r in row.get("trusted_facts", {}).values()
                    if r.get("merchant_name")
                )
                evidence = [
                    detect_language_evidence(r.get("reply", ""), ignored_terms=merchants)
                    for r in row["responses"]
                ]
                row.update(
                    candidate=candidate,
                    study_set=current.group,
                    tags=[current.group],
                    cost_usd=sum(c["cost_usd"] or 0 for c in calls[call_start:]),
                    unknown_cost_attempts=sum(c["cost_usd"] is None for c in calls[call_start:]),
                    reply_language_errors=sum(
                        e not in {"uncertain", row["language"]} for e in evidence
                    ),
                    reply_language_uncertain=evidence.count("uncertain"),
                )
                annotation = truth[current.scenario["id"]]
                if annotation["slots"] is not None:
                    row["opening_slots"] = slot_counts(client.first_slots, annotation["slots"])
                row["opening_nlu_unreached"] = not client.first_nlu_attempted
                save(case_file, row)
                items.append(row)
                interrupted = None
                print(
                    json.dumps(
                        {
                            "mode": "real" if real else "mock",
                            "completed": len(items),
                            "planned": 100,
                        }
                    ),
                    flush=True,
                )
    except Exception as exc:
        if not stage_ready:
            raise
        error_type = type(exc).__name__
    finally:
        budget = budget_receipt(connection) if connection else {"paid_calls": 0}
        if connection:
            connection.close()
    result = {
        **report(items, calls),
        "error_type": error_type,
        "interrupted": interrupted,
        "budget_readback": budget,
    }
    if output.exists():
        save(output / "summary.json", result)
    if pins(comparison_sample()) != study_pins:
        raise RuntimeError("Pinned study code/data/config changed during execution")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        result = asyncio.run(run(real=args.real, resume=args.resume))
    except Exception as exc:
        raise SystemExit("Development comparison stopped: " + type(exc).__name__) from None
    print(json.dumps({k: v for k, v in result.items() if k != "arms"}, indent=2))
    if result["error_type"] or result["complete_pairs"] != 50:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
