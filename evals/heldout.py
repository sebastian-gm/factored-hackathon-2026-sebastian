"""Frozen-suite preflight/execution. Source rows and per-case traces stay ignored."""

# ruff: noqa: T201, S603, S607 -- aggregate output; fixed read-only git argv scoped to ROOT.
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import yaml

from aclara.bank.serving import ServingRepository
from aclara.handoff.routing import AgentDirectory
from aclara.llm.config import load_models, load_prices
from evals.access import access
from evals.bindings import ROOT, bind, private_bindings
from evals.bound_execution import execute_bound
from evals.heldout_report import comparison, report
from evals.metrics import score
from evals.observations import validate_gold
from evals.serving import open_serving
from evals.studies.llm.final_run import (
    FinalBudgetStop,
    client_for,
    journal,
    open_budget_store,
    require_start,
)
from evals.suites.tools.validate_release import check_payloads, verify_manifest


def private_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(data)


def load(
    serving: ServingRepository, *, release: Path | None = None, binding_path: Path | None = None
) -> tuple[dict, dict, AgentDirectory]:
    if release is None:
        release = ROOT / "evals/suites/test"
        summary = check_payloads(release)
        verify_manifest(release)
        print(json.dumps(summary, sort_keys=True))
        parts = [yaml.safe_load(p.read_text()) for p in sorted(release.glob("scenarios-*.yaml"))]
        suite = {**parts[0], "scenarios": [c for part in parts for c in part["scenarios"]]}
    else:
        from evals.program_spec import load_payloads

        suite = load_payloads(release)
    provenance = json.loads((release / "provenance.json").read_text())
    identities = private_bindings(suite, provenance, serving, path=binding_path)
    directory = serving.directory()
    warnings: Counter[str] = Counter()
    for s in suite["scenarios"]:
        fixture = bind(s, identities[s["persona"]["customer_ref"]], directory, serving)
        warnings.update(fixture.input_warnings)
        validate_gold(s["gold"], fixture.refs, fixture.protected)
        for turn in s["turns"]:
            if "message" in turn:
                fixture.render(turn["message"])
    print(
        json.dumps(
            {
                "preflight": "passed",
                "cases": len(suite["scenarios"]),
                "identity_partition_ownership": "verified",
                "benchmark_overlap": 0,
                "input_warnings": dict(warnings),
                "private_binding_sha": provenance["bindings_audit"]["private_bindings_sha256"],
            }
        )
    )
    return suite, identities, directory


def failed(s: dict, system: str, repeat: int, error: Exception) -> dict:
    selector = s["persona"]["selector"]
    return score(
        {
            "id": s["id"],
            "run_id": str(uuid4()),
            "system": system,
            "repeat": repeat,
            "gold": s["gold"],
            "responses": [],
            "refs": {},
            "events": [],
            "turn_ms": [],
            "case_ms": 0,
            "readback": False,
            "verified_refs": [],
            "http_denied": False,
            "unsafe": {},
            "cost_usd": 0,
            "language": s["language"],
            "dialect": s["dialect"],
            "country": selector["country"],
            "segment": selector["segment"],
            "category": s["category"],
            "execution_status": "not_executed",
            "execution_error": type(error).__name__,
            "not_executed_reason": "adapter_error:" + type(error).__name__,
        }
    )


async def run(
    suite: dict,
    identities: dict,
    directory: AgentDirectory,
    output: Path,
    serving: ServingRepository,
    *,
    final: bool = False,
    budget_store=None,
) -> None:
    if final:
        require_start()
        if budget_store is None:
            raise ValueError("A shared final-program budget store is required")
    if subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
    ).strip():
        raise ValueError("Freeze a clean implementation commit before held-out execution")
    if output.exists():
        raise ValueError("Use a new output directory; prior test access must be preserved")
    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    manifest = hashlib.sha256((ROOT / "evals/suites/test/MANIFEST.sha256").read_bytes()).hexdigest()
    repeat_ids = set(
        json.loads((ROOT / "evals/suites/test/repeat-selection.json").read_text())["scenario_ids"]
    )
    metadata = {
        "implementation_sha": sha,
        "manifest_sha256": manifest,
        "started_at": datetime.now(UTC).isoformat(),
        "provider": "openai_compat" if final else "mock",
        "resolved_models": {
            k: asdict(v) for k, v in load_models(ROOT / "config/models.yaml").items()
        }
        if final
        else {},
        "model": "google/gemini-3-flash-preview"
        if final
        else "unconfigured_mock_deterministic_fallback",
        "dataset_version": suite["dataset_version"],
        "policy_version": yaml.safe_load((ROOT / "config/policy.yaml").read_text())["version"],
        "prompt_versions": {
            name: hashlib.sha256(
                (ROOT / f"prompts/{name}/{'v4' if name == 'nlu' else 'v1'}.md").read_bytes()
            ).hexdigest()
            for name in ("nlu", "phrase")
        },
        "matcher_version": "v2" if final else "rules fallback (mock NLU unavailable)",
        "matcher_checksums": json.loads(
            (ROOT / "models/charge_matcher/v2/checksums.json").read_text()
        ),
        "price_table_dates": {
            key: str(price.as_of)
            for key, price in load_prices(ROOT / "config/pricing.yaml").items()
        },
        "price_table_sha256": hashlib.sha256(
            (ROOT / "config/pricing.yaml").read_bytes()
        ).hexdigest(),
        "monthly_infrastructure_estimate_usd": 34.63,
        "workload": "heldout-e2e-v2 organizer serving base plus declared fictional overlays",
        "source_kind": "organizer_serving_with_declared_overlays",
        "source_rls": "forced customer RLS on every base read",
        "operational_storage": "isolated in-memory per case; persistence tested separately",
        "human_label_review": "pending",
        "language_review": "model generated, cross-vendor PT review; no fluent-human PT review",
        "cost_assumptions": "Known call costs plus conservative durable unknown reserves; final cumulative cap USD 12"
        if final
        else "Mock USD 0",
    }
    private_write(output / "access.json", json.dumps(metadata, indent=2) + "\n")
    all_cases = []
    workload = [("B1", 0, None), ("P", 0, "default"), ("P", 1, "default"), ("P", 2, "default")]
    if final:
        workload.append(("P-Sonnet", 0, "openrouter_sonnet"))
    for system, repeat, route in workload:
        selected = [
            s
            for s in suite["scenarios"]
            if (repeat == 0 and system != "P-Sonnet") or s["id"] in repeat_ids
        ]
        cases = []
        for index, scenario in enumerate(selected, 1):
            model_client = (
                client_for(
                    route,
                    budget_store,
                    response_record=journal(output / "calls" / f"{system}-{repeat}-{index}.jsonl"),
                )
                if final and route
                else None
            )
            try:
                fixture = bind(
                    scenario, identities[scenario["persona"]["customer_ref"]], directory, serving
                )
                result = await execute_bound(
                    scenario, fixture, "P" if route else "B1", repeat, llm_client=model_client
                )
                result["system"] = system
            except FinalBudgetStop:
                private_write(
                    output / "STOPPED.json",
                    json.dumps(
                        {
                            "reason": "durable_budget",
                            "system": system,
                            "repeat": repeat,
                            "attempted": index,
                        }
                    ),
                )
                raise
            except Exception as error:
                result = failed(scenario, system, repeat, error)
            if model_client is not None:
                result["cost_usd"] = sum(c.cost_usd or 0 for c in model_client.records)
                result["unknown_cost_attempts"] = sum(
                    c.cost_usd is None for c in model_client.records
                )
                result["accounted_cost_usd"] = model_client.spent_usd
            cases.append(result)
            private_write(
                output / f"{system}-{repeat}-cases.jsonl",
                "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases),
            )
            if index % 25 == 0:
                print(
                    json.dumps(
                        {
                            "system": system,
                            "repeat": repeat,
                            "attempted": index,
                            "total": len(selected),
                        }
                    ),
                    flush=True,
                )
        private_write(
            output / f"{system}-{repeat}-cases.jsonl",
            "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases),
        )
        all_cases.extend(cases)
    if len({c["run_id"] for c in all_cases}) != len(all_cases):
        raise ValueError("Run isolation failed")
    b1 = [c for c in all_cases if c["system"] == "B1"]
    proposed = [c for c in all_cases if c["system"] == "P" and c["repeat"] == 0]
    repeats = [c for c in all_cases if c["repeat"] > 0]
    groups = [("B1", b1), ("P-Gemini" if final else "P-mock", proposed)]
    if final:
        groups.append(("P-Sonnet", [c for c in all_cases if c["system"] == "P-Sonnet"]))
    for system, cases in groups:
        print(json.dumps({"reporting": system, "bootstrap_draws": 10000}), flush=True)
        aggregate = report(cases, {**metadata, "system": system})
        private_write(output / f"{system}-aggregates.json", json.dumps(aggregate, indent=2) + "\n")
    paired = comparison(b1, proposed, repeats, repeat_ids)
    private_write(output / "comparison-aggregates.json", json.dumps(paired, indent=2) + "\n")
    print(
        json.dumps(
            {
                "completed": len(all_cases),
                "systems": dict(Counter(c["system"] for c in all_cases)),
                "model_cost_usd": sum(c["cost_usd"] for c in all_cases),
                "artifact_directory": str(output.relative_to(ROOT)),
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument(
        "--final", action="store_true", help="Approved real routes; requires explicit start signal"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/heldout/run-01")
    args = parser.parse_args()
    if args.final:
        require_start()
        if not args.run:
            raise ValueError("--final requires --run")
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "artifacts"):
        raise ValueError("Private output must remain under ignored artifacts")
    paths = sorted(p for p in (ROOT / "evals/suites/test").iterdir() if p.is_file())
    paths += [ROOT / "artifacts/evaluation-authoring/customer-bindings.json"]
    paths += [
        ROOT / f"artifacts/charge_matcher/v1/dataset/{split}.jsonl"
        for split in ("train", "validation", "test")
    ]
    budget_store = open_budget_store() if args.final else None
    serving = open_serving()
    try:
        with access(
            "final_program" if args.final else "full_diagnostic" if args.run else "preflight",
            paths,
            "Explicit frozen access; serving ownership, overlays and hashes; no gold edits",
        ):
            suite, identities, directory = load(serving)
            if args.run:
                asyncio.run(
                    run(
                        suite,
                        identities,
                        directory,
                        output,
                        serving,
                        final=args.final,
                        budget_store=budget_store,
                    )
                )
    finally:
        serving.store.close()
        if budget_store:
            budget_store.close()


if __name__ == "__main__":
    main()
