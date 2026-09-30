"""Budgeted P prompt study over five explicitly allowlisted development sets.

The retired v3 scenarios use their complete authored overlays and synthetic
identities with the same declared country/segment, not an official serving run.
No source customer row or held-out input is required by this development adapter.
"""

# ruff: noqa: T201, S603, S607 -- aggregate CLI output and fixed local git command.
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib import import_module
from itertools import zip_longest
from typing import Any, TypeVar

import psycopg
import yaml  # type: ignore[import-untyped]
from dotenv import load_dotenv
from pydantic import BaseModel

from aclara.llm.client import StructuredClient
from aclara.llm.config import load_fallback_route, load_models, load_prices
from aclara.llm.dev_offer_scenarios import load_offer_scenarios
from aclara.llm.dev_robustness import STOP, DevBudgetStop, ThresholdGate, save, summarize
from aclara.llm.dev_robustness_cases import ROOT, identity, materialize, validate
from aclara.llm.dev_robustness_round2_cases import identity as round_two_identity
from aclara.llm.dev_robustness_round2_cases import materialize as round_two_materialize
from aclara.llm.dev_robustness_round2_cases import validate as round_two_validate
from aclara.llm.prompts import Prompt, load_prompt
from aclara.llm.types import CallRecord

SCOPE, RUN_ID = "dev-gate/pre-v4", "pre-v4"
T = TypeVar("T", bound=BaseModel)


class PromptStudyClient(StructuredClient):
    """Development injection boundary; application/default prompt stays unchanged."""

    nlu_prompt: Prompt | None = None

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
        if route == "nlu" and self.nlu_prompt is not None:
            system = self.nlu_prompt.text
            prompt_id = f"{self.nlu_prompt.id}@{self.nlu_prompt.version}"
            prompt_hash = self.nlu_prompt.content_hash
        return super().generate(
            route, system, user, schema, prompt_id=prompt_id, prompt_hash=prompt_hash
        )


@dataclass(frozen=True)
class StudyCase:
    group: str
    scenario: dict[str, Any]
    binding: dict[str, Any] | None = None


def inputs() -> list[StudyCase]:
    """Round-robin ordering gives every set coverage before a shared-budget stop."""
    validate()
    round_two_validate()
    dev = yaml.safe_load((ROOT / "evals/dev_scenarios_v2.yaml").read_text())["scenarios"]
    groups = {
        "dev20": [StudyCase("dev20", s) for s in dev if not s.get("faults")],
        "confirmation20": [StudyCase("confirmation20", s) for s in load_offer_scenarios()],
    }
    cases, scenarios = materialize()
    groups["robustness40"] = [
        StudyCase("robustness40", s, identity(c)) for c, s in zip(cases, scenarios, strict=True)
    ]
    cases, scenarios = round_two_materialize()
    groups["round2_60"] = [
        StudyCase("round2_60", s, round_two_identity(c))
        for c, s in zip(cases, scenarios, strict=True)
    ]
    retired: list[StudyCase] = []
    # Literal directory and filenames: no suite discovery or authoring-tool imports.
    for name in (
        "scenarios-normal.yaml",
        "scenarios-ambiguous_unsupported.yaml",
        "scenarios-human_required.yaml",
        "scenarios-security_robustness.yaml",
    ):
        data = yaml.safe_load((ROOT / "evals/suites/test-v3" / name).read_text())
        for scenario in data["scenarios"]:
            overlays = {o["kind"]: o["values"] for o in scenario["overlays"]}
            if not {"customer_status", "prior_complaint_count_90d"} <= overlays["customer"].keys():
                raise ValueError("Retired dev case requires undeclared source customer facts")
            if not {"product_type", "product_status"} <= overlays["product"].keys():
                raise ValueError("Retired dev case requires undeclared source product facts")
            binding = {
                "customer_id": "dev-v3-" + scenario["id"],
                "product_id": "dev-v3-product-" + scenario["id"],
                "selector": scenario["persona"]["selector"],
            }
            retired.append(StudyCase("v3_100", scenario, binding))
    groups["v3_100"] = retired
    if {k: len(v) for k, v in groups.items()} != {
        "dev20": 20,
        "confirmation20": 20,
        "robustness40": 40,
        "round2_60": 60,
        "v3_100": 100,
    }:
        raise ValueError("Five-set development inventory changed")
    result = [c for group in zip_longest(*groups.values()) for c in group if c is not None]
    if len({c.scenario["id"] for c in result}) != 240:
        raise ValueError("Development IDs overlap")
    return result


def inventory_hash(cases: list[StudyCase]) -> str:
    return sha256(json.dumps([asdict(c) for c in cases], sort_keys=True).encode()).hexdigest()


async def run(version: str) -> dict[str, Any]:
    cases = inputs()
    digest = inventory_hash(cases)
    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
    ).strip():
        raise RuntimeError("Real study requires a clean committed tree")
    prompt = load_prompt(ROOT / "prompts/nlu" / ("v5.md" if version == "v5.1" else "v5_2.md"))
    output = ROOT / "artifacts/dev-pre-v4/lean" / version
    if output.exists():
        raise FileExistsError("Preserve previous paid evidence; no overwrite or implicit rerun")
    load_dotenv(ROOT / ".env", override=False)
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1" or os.getenv("LLM_PROVIDER", "mock") != "mock":
        raise RuntimeError("Scoped real client needs approval; global app must remain mock")
    if not all(os.getenv(k) for k in ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY")):
        raise RuntimeError("Both approved local keys are required")
    dsn = import_module("scripts.azure_migrate_ops").connection_string("aclara_admin")
    verify = import_module("scripts.pre_v4_budget").verify
    initial = verify(dsn)
    if initial["charged_with_reserves_usd"] >= float(STOP):
        raise DevBudgetStop("Shared exposure reached stop")
    output.mkdir(parents=True, mode=0o700)
    save(
        output / "launch.json",
        {
            "sha": sha,
            "scope": SCOPE,
            "run_id": RUN_ID,
            "stop_usd": float(STOP),
            "prompt": asdict(prompt),
            "inventory_sha256": digest,
            "planned": dict(Counter(c.group for c in cases)),
            "v3_binding": "complete_authored_overlays_synthetic_identity_not_official_serving",
            "initial_budget": initial,
            "file_hashes": {
                name: sha256((ROOT / name).read_bytes()).hexdigest()
                for name in (
                    "config/models.yaml",
                    "config/pricing.yaml",
                    "src/aclara/agent/nlu/structured.py",
                    "src/aclara/agent/nlg/grounding.py",
                    "prompts/phrase/v2.md",
                    "evals/metrics.py",
                )
            },
        },
    )
    calls: list[dict[str, Any]] = []
    current: StudyCase | None = None

    def journal(record: CallRecord, parsed: dict[str, Any] | None) -> None:
        assert current is not None
        call = asdict(record)
        calls.append({**call, "group": current.group, "id": current.scenario["id"]})
        with os.fdopen(
            os.open(output / "calls.jsonl", os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600), "w"
        ) as stream:
            stream.write(
                json.dumps(
                    {
                        "id": current.scenario["id"],
                        "group": current.group,
                        "call": call,
                        "validated": parsed,
                    }
                )
                + "\n"
            )
            stream.flush()
            os.fsync(stream.fileno())

    models = load_models(ROOT / "config/models.yaml")
    models["nlu"] = models["phrase"] = models["default"]
    fallback = load_fallback_route(ROOT / "config/models.yaml", models)
    completed: list[dict[str, Any]] = []
    error_type = None
    with psycopg.connect(dsn, autocommit=True) as connection:
        client = PromptStudyClient(
            models,
            load_prices(ROOT / "config/pricing.yaml"),
            budget_usd=None,
            daily_budget_usd=1,
            spend_gate=ThresholdGate(connection, scope=SCOPE, run_id=RUN_ID),
            response_record=journal,
            call_timeout_seconds=45,
            fallback_routes={"nlu": fallback, "phrase": fallback} if fallback else None,
        )
        client.nlu_prompt = prompt
        bind = import_module("evals.bindings").bind
        bound = import_module("evals.bound_execution").execute_bound
        legacy = import_module("evals.reactive").execute
        try:
            for current in cases:
                start = len(calls)
                result = (
                    await bound(
                        current.scenario,
                        bind(current.scenario, current.binding),
                        "P",
                        llm_client=client,
                    )
                    if current.binding is not None
                    else await legacy(current.scenario, "P", llm_client=client)
                )
                result.update(
                    study_set=current.group,
                    tags=[current.group],
                    cost_usd=sum(c["cost_usd"] or 0 for c in calls[start:]),
                    unknown_cost_attempts=sum(c["cost_usd"] is None for c in calls[start:]),
                )
                save(output / (current.scenario["id"] + ".json"), result)
                completed.append(result)
                print(
                    json.dumps({"prompt": version, "completed": len(completed), "planned": 240}),
                    flush=True,
                )
        except Exception as exc:
            error_type = type(exc).__name__
    result = {
        "sha": sha,
        "prompt": version,
        "inventory_sha256": digest,
        **summarize(completed, calls, planned=240),
        "set_counts": dict(Counter(r["study_set"] for r in completed)),
        "set_passed": dict(Counter(r["study_set"] for r in completed if r["passed"])),
        "error_type": error_type,
        "interrupted_case": current.scenario["id"] if current and error_type else None,
        "budget_readback": verify(dsn),
    }
    save(output / "summary.json", result)
    if inventory_hash(inputs()) != digest:
        raise RuntimeError("Development inputs changed during execution")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", choices=("v5.1", "v5.2"))
    args = parser.parse_args()
    try:
        result = asyncio.run(run(args.version))
    except Exception as exc:
        raise SystemExit("Dev prompt study failed: " + type(exc).__name__) from None
    print(json.dumps({k: v for k, v in result.items() if k != "failures"}, indent=2))
    if not result["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
