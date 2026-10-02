"""One pinned, resumable final program. Importing this module opens no frozen data."""

# ruff: noqa: T201 -- progress counts only.
from __future__ import annotations

import asyncio
import csv
import hashlib
import io
import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import yaml

from aclara.llm.config import load_models, load_prices
from aclara.llm.prompts import load_prompt
from aclara.llm.types import BudgetFailure, ModelFailure
from aclara.ops.store import Store
from evals import rehearsal
from evals.access import access
from evals.bindings import ROOT, bind
from evals.bound_execution import execute_bound
from evals.checkpoints import Checkpoints, atomic_write, save
from evals.heldout import failed, load
from evals.program_spec import (
    WORKLOAD,
    ProgramSpec,
    selections,
    serving_pin,
    specification,
    verify_envelope,
)
from evals.serving import open_serving
from evals.studies.llm.dual_judge import jev_judge_adapter, score_pair
from evals.studies.llm.final_run import (
    FinalBudgetStop,
    client_for,
    journal,
    open_budget_store,
    require_start,
)
from evals.studies.llm.judge_validation import DIMENSIONS

V3 = specification("test-v3")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def budget_receipt(spec: ProgramSpec = V3) -> dict:
    if spec.rehearsal:
        return rehearsal.receipt(spec)
    from scripts.final_budget import verify

    return verify(os.environ["FINAL_BUDGET_OWNER_DSN"], spec)


def judge_ids(scenarios: list[dict], repeat_ids: set[str]) -> set[str]:
    chosen = set()
    for category, count in [
        ("normal", 18),
        ("ambiguous_unsupported", 10),
        ("human_required", 10),
        ("security_robustness", 12),
    ]:
        rows = [s["id"] for s in scenarios if s["id"] in repeat_ids and s["category"] == category]
        if len(rows) < count:
            raise ValueError("Predeclared judge stratum is incomplete")
        chosen.update(
            sorted(
                rows, key=lambda value: hashlib.sha256(("judge-v1:" + value).encode()).hexdigest()
            )[:count]
        )
    return chosen


def wording(case: dict) -> dict:
    return case.get("judge_input") or {
        "target_locale": case["dialect"],
        "customer_message": "",
        "customer_reply": "",
        "handoff_summary": "",
    }


def human_sheet(output: Path, rows: list[dict]) -> None:
    # Deterministic round-robin locale sample; blind to system and objective gold.
    grouped = {}
    for row in rows:
        grouped.setdefault(row["target_locale"], []).append(row)
    chosen = []
    ordered = {
        k: sorted(
            v, key=lambda r: hashlib.sha256(("human20-v1:" + r["sample_id"]).encode()).hexdigest()
        )
        for k, v in sorted(grouped.items())
    }
    while len(chosen) < min(20, len(rows)):
        for group in ordered.values():
            if group and len(chosen) < 20:
                chosen.append(group.pop(0))
    path = output / "human-judge-20.csv"
    if path.exists():
        return  # Never overwrite Sebastian's ratings on resume.
    fields = [
        "sample_id",
        "target_locale",
        "customer_message",
        "customer_reply",
        "handoff_summary",
        *(f"human_{d}" for d in DIMENSIONS),
        "human_notes",
    ]
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(chosen)
    atomic_write(path, stream.getvalue())


async def execute(suite, identities, directory, serving, store, checkpoints, repeat_ids, spec=V3):
    cases = []
    planned = 2 * len(suite["scenarios"]) + 2 * len(repeat_ids)
    for system, repeat, route in WORKLOAD:
        if spec.rehearsal:
            route = None  # Exercise the same workload/checkpoints with deterministic B1 only.
        for scenario in suite["scenarios"]:
            if repeat and scenario["id"] not in repeat_ids:
                continue
            key = f"{system}:{repeat}:{scenario['id']}"
            cached = checkpoints.read(key)
            if cached is not None:
                cases.append(cached)
                continue
            path = checkpoints.begin(key)
            if spec.rehearsal:
                rehearsal.hook(spec, "systems", len(cases), before=True)
            client = (
                client_for(
                    route,
                    store,
                    response_record=journal(path),
                    budget_scope=spec.scope,
                    budget_run_id=spec.run_id,
                )
                if route
                else None
            )
            try:
                fixture = bind(
                    scenario, identities[scenario["persona"]["customer_ref"]], directory, serving
                )
                result = await execute_bound(
                    scenario, fixture, "P" if route else "B1", repeat, llm_client=client
                )
                result["system"] = system
            except FinalBudgetStop:
                raise
            except Exception as error:
                raise RuntimeError(
                    "Case execution failed; stop without advancing checkpoint"
                ) from error
            calls = [r["call"] for r in checkpoints.calls(key)]
            result.update(
                cost_usd=sum(c["cost_usd"] or 0 for c in calls),
                unknown_cost_attempts=sum(c["cost_usd"] is None for c in calls),
                recovered_attempts=len(list(checkpoints.directory(key).glob("attempt-*.json"))) - 1,
            )
            cases.append(checkpoints.finish(key, result))
            save(
                checkpoints.root / "progress.json",
                {
                    "phase": "systems",
                    "completed": len(cases),
                    "planned": planned,
                    "at": datetime.now(UTC).isoformat(),
                    "budget": budget_receipt(spec),
                },
            )
            if spec.rehearsal:
                rehearsal.hook(spec, "systems", len(cases))
    return cases


def judges(cases, selected, checkpoints, store, spec=V3):
    rows = []  # No new calibration or frontier calls in the approved v3 workload.
    for case in cases:
        if case["system"] not in {"B1", "P"} or case["repeat"] or case["id"] not in selected:
            continue
        row = wording(case)
        sample_id = hashlib.sha256(f"judge:{case['system']}:{case['id']}".encode()).hexdigest()[:20]
        rows.append({**row, "sample_id": sample_id, "cohort": "frozen"})
    human_sheet(checkpoints.root, [r for r in rows if r["cohort"] == "frozen"])
    # Mapping stays private; the models and human sheet do not receive system or objective gold.
    save(checkpoints.root / "judge-inputs.json", rows)
    ratings = []
    for row in rows:
        key = "judge:" + row["sample_id"]
        cached = checkpoints.read(key)
        if cached is not None:
            ratings.append(cached)
            continue
        path = checkpoints.begin(key)
        truncate = (
            rehearsal.hook(spec, "judges", len(ratings), before=True) if spec.rehearsal else False
        )
        client = (
            rehearsal.client(
                path, spec, has_handoff=bool(row["handoff_summary"].strip()), truncate=truncate
            )
            if spec.rehearsal
            else client_for(
                "openrouter_sonnet",
                store,
                judge=True,
                response_record=journal(path),
                budget_scope=spec.scope,
                budget_run_id=spec.run_id,
            )
        )
        try:
            if not row["customer_reply"]:
                result = {"status": "not_scored", "reason": "no_delivered_reply"}
            else:
                if spec.rehearsal:
                    result = rehearsal.score_pair(row, client)
                else:
                    with jev_judge_adapter() as adapter:
                        result = score_pair(
                            row,
                            sonnet_client=client,
                            jev_adapter=adapter,
                            prompt=load_prompt(ROOT / "prompts/judge/v1.md"),
                        )
                result["status"] = "scored"
        except (FinalBudgetStop, BudgetFailure):
            raise
        except ModelFailure as error:
            # The client already exhausted its bounded attempts. Preserve a failed
            # item, never invent scores or replay it on resume; keep primary reports.
            result = {
                "status": "judge_failed",
                "error_type": type(error).__name__,
                "sonnet_scores": None,
                "jev_scores": None,
                "attempt_statuses": [record.status for record in client.records],
                "length_failures": sum(
                    record.stop_reason in {"length", "max_tokens"} for record in client.records
                ),
            }
        except Exception as error:
            raise RuntimeError(
                "Judge execution failed; stop without advancing checkpoint"
            ) from error
        result.update(
            sample_id=row["sample_id"], cohort=row["cohort"], target_locale=row["target_locale"]
        )
        ratings.append(checkpoints.finish(key, result))
        save(
            checkpoints.root / "progress.json",
            {
                "phase": "judges",
                "completed": len(ratings),
                "planned": len(rows),
                "at": datetime.now(UTC).isoformat(),
                "budget": budget_receipt(spec),
            },
        )
        if spec.rehearsal:
            rehearsal.hook(spec, "judges", len(ratings))
    return ratings


def saved_cases(suite: dict, repeat_ids: set[str], checkpoints: Checkpoints) -> list[dict]:
    results = []
    for system, repeat, _ in WORKLOAD:
        for scenario in suite["scenarios"]:
            if repeat and scenario["id"] not in repeat_ids:
                continue
            key = f"{system}:{repeat}:{scenario['id']}"
            result = checkpoints.read(key)
            if result is None:
                result = failed(scenario, system, repeat, FinalBudgetStop("Program stopped"))
                result["cost_usd"] = sum(
                    row["call"]["cost_usd"] or 0 for row in checkpoints.calls(key)
                )
            results.append(result)
    return results


def main(output: Path, sha: str, spec: ProgramSpec = V3) -> None:
    if spec.rehearsal:
        rehearsal.guard(spec)
    else:
        require_start()
    serving_connection = serving_pin(spec)
    # All frozen reads, including pin verification on resume, are inside the access ledger.
    paths = sorted(p for p in spec.release.iterdir() if p.is_file())
    paths += [spec.bindings]
    paths += [
        ROOT / f"artifacts/charge_matcher/v1/dataset/{split}.jsonl"
        for split in ("train", "validation", "test")
    ]
    with access(
        "final_program",
        paths,
        "Owner-approved zero-spend retired-v3 rehearsal"
        if spec.rehearsal
        else "Owner-approved final program; pinned start/resume, no tuning",
    ):
        serving = open_serving()
        try:
            store = Store(os.environ["EVAL_BUDGET_DSN"]) if spec.rehearsal else open_budget_store()
        except BaseException:
            serving.store.close()
            raise
        try:
            if spec.rehearsal:
                rehearsal.budget_denial(spec, store)
            verify_envelope(spec)
            suite, identities, directory = load(
                serving, release=spec.release, binding_path=spec.bindings
            )
            repeat_ids, selected = selections(suite, spec.release)
            pins = {
                "implementation_sha": sha,
                "inputs": {str(p.relative_to(ROOT)): digest(p) for p in paths},
                "dataset_version": serving.dataset_version,
                "budget_scope": spec.scope,
                "budget_run_id": spec.run_id,
                "program": spec.identity(),
                "serving": serving_connection,
                **({"controls_sha256": rehearsal.controls_pin(spec)} if spec.rehearsal else {}),
            }
            checkpoints = Checkpoints(output, pins)
            header = {
                **pins,
                "workload": f"After fixes, fresh suite {spec.suite}: 100 organizer-ledger scenarios with declared overlays; B1 100/P-Gemini 160, two extra passes on 30 preselected cases; Sonnet frontier OFF",
                "suite": spec.suite,
                "frontier_enabled": False,
                "judge_planned": {"calibration": 0, "frozen": 60},
                "disclosure": "Candidate fixes use seen prior evaluations and dev evidence; prior official results remain unchanged; this suite is independent",
                "preflight_disclosure": (
                    "V4 attempt 1 passed structural and identity/ownership preflight, then stopped with KeyError before systems: 0 cases, 0 paid attempts, USD 0. Its directory and stop receipt are preserved as final-program-v4-attempt1. The owner authorized an evaluation-only selection-interface fix and fresh start under the same USD 3 lifetime scope; product, prompts, config and frozen inputs are unchanged."
                    if spec.suite == "test-v4" and not spec.rehearsal
                    else None
                ),
                "model": "google/gemini-3-flash-preview + jev-1.13.0 risk union",
                "resolved_models": {
                    k: asdict(v) for k, v in load_models(ROOT / "config/models.yaml").items()
                },
                "prompt_versions": {
                    name: digest(ROOT / path)
                    for name, path in {
                        "nlu-v5.1": "prompts/nlu/v5.md",
                        "phrase-v2": "prompts/phrase/v2.md",
                        "judge-v1": "prompts/judge/v1.md",
                        "jev": "src/aclara/llm/typesafe_questions.py",
                    }.items()
                },
                "price_table_dates": {
                    k: str(v.as_of) for k, v in load_prices(ROOT / "config/pricing.yaml").items()
                },
                "price_table_sha256": digest(ROOT / "config/pricing.yaml"),
                "policy_version": yaml.safe_load((ROOT / "config/policy.yaml").read_text())[
                    "version"
                ],
                "matcher_version": "v2",
                "matcher_checksums": json.loads(
                    (ROOT / "models/charge_matcher/v2/checksums.json").read_text()
                ),
                "cost_assumptions": "USD; suite lifetime cap $3 including retries, judges and retained unknown reserves; cumulative prior/dev/program plus $0.10 release-smoke allowance <= $12",
                "monthly_infrastructure_estimate_usd": 34.63,
                "source_rls": "forced customer RLS, organizer serving, 120-day window",
                "serving_location": "local" if spec.suite == "test-v4" else "legacy",
                "latency_scope": "local serving SQL plus remote model/provider and durable budget calls; excludes workstation-to-Azure serving hops"
                if spec.suite == "test-v4"
                else "legacy Azure serving",
                "operational_storage": "isolated fresh in-memory state per case; durable production separately tested",
                "human_label_review": "pending; model-generated PT/MX/AR wording is a limitation",
            }
            if spec.rehearsal:
                header.update(
                    workload="DEV REHEARSAL: retired v3, B1-only 260 runs; repeats and mock-client judges",
                    model="B1 deterministic fallback only; identical synthetic judge scores",
                    disclosure="Operational rehearsal only; no new official evaluation or vendor agreement claim",
                    resolved_models={},
                    cost_assumptions="No paid providers; isolated local durable $0 lifetime cap; positive reservations denied",
                    serving_location="local",
                    latency_scope="Rehearsal wall-clock only; not real-model latency",
                    rehearsal=True,
                    p_system_label="B1-repeated",
                )
            from evals.final_report import write_report

            try:
                cases = asyncio.run(
                    execute(
                        suite, identities, directory, serving, store, checkpoints, repeat_ids, spec
                    )
                )
                if len({case["run_id"] for case in cases}) != len(cases):
                    raise RuntimeError("Case isolation failed")
                ratings = judges(cases, selected, checkpoints, store, spec)
            except FinalBudgetStop:
                cases = saved_cases(suite, repeat_ids, checkpoints)
                ratings = [
                    json.loads(path.read_text())
                    for path in output.glob("checkpoints/*/result.json")
                    if "sample_id" in json.loads(path.read_text())
                ]
                write_report(
                    output,
                    cases,
                    ratings,
                    repeat_ids,
                    {**header, "completion": "partial: durable budget stop"},
                    budget_receipt(spec),
                )
                raise
            write_report(
                output,
                cases,
                ratings,
                repeat_ids,
                {**header, "completion": "complete"},
                budget_receipt(spec),
            )
            save(
                output / "COMPLETE.json",
                {
                    "completed_cases": len(cases),
                    "judge_items": len(ratings),
                    "implementation_sha": sha,
                    "budget": budget_receipt(spec),
                    "at": datetime.now(UTC).isoformat(),
                },
            )
            (output / "STOPPED.json").unlink(missing_ok=True)
            print(
                json.dumps(
                    {"state": "complete", "case_runs": len(cases), "judge_items": len(ratings)}
                ),
                flush=True,
            )
        finally:
            serving.store.close()
            store.close()
