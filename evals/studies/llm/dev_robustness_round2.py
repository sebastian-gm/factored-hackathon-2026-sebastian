"""Zero-spend execution of the frozen round-two fixtures; no paid entry point."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import Counter
from importlib import import_module
from pathlib import Path
from typing import Any

from evals.studies.llm.dev_robustness_cases import ROOT
from evals.studies.llm.dev_robustness_round2_cases import identity, materialize, validate


def save(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        path.chmod(0o600)
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


async def mock() -> dict[str, Any]:
    """Exercise the real in-memory P state machine with deterministic mock NLU."""
    if os.environ.get("LLM_PROVIDER", "mock") != "mock" or os.environ.get(
        "LLM_REAL_CALLS_APPROVED", "0"
    ) not in {"0", ""}:
        raise RuntimeError("This entry point requires mock provider and no paid-call approval")
    freeze = validate()
    output = ROOT / "artifacts/dev-pre-v4/round2-mock"
    if output.exists():
        raise FileExistsError("Preserve prior mock evidence; do not overwrite it")
    output.mkdir(parents=True, mode=0o700)
    execute = import_module("evals.bound_execution").execute_bound
    bind = import_module("evals.bindings").bind
    cases, scenarios = materialize()
    results: list[dict[str, Any]] = []
    for case, scenario in zip(cases, scenarios, strict=True):
        result = await execute(scenario, bind(scenario, identity(case)), "P")
        if result.get("cost_usd", 0) != 0:
            raise RuntimeError("Mock execution unexpectedly reported a nonzero model cost")
        result["authored_locale"] = case["locale"]
        result["authored_family"] = case["family"]
        save(output / (case["id"] + ".json"), result)
        results.append(result)
    if validate() != freeze:
        raise ValueError("Frozen fixtures changed during mock execution")
    summary = summarize(results, freeze)
    save(output / "summary.json", summary)
    return summary


def summarize(results: list[dict[str, Any]], freeze: dict[str, Any]) -> dict[str, Any]:
    """Unsafe is a map of boolean findings; the map's existence is not a failure."""
    slices = {}
    for language in ("all", "es", "pt"):
        rows = [row for row in results if language == "all" or row["language"] == language]
        slices[language] = {
            "n": len(rows),
            "passed": sum(bool(row["passed"]) for row in rows),
            "unsafe": sum(any(row["unsafe"].values()) for row in rows),
        }
    summary: dict[str, Any] = {
        "mode": "mock_only_not_real_model_accuracy",
        "n": len(results),
        "cases_sha256": freeze["cases_sha256"],
        "materialized_sha256": freeze["materialized_sha256"],
        "slices": slices,
        "outcomes": dict(Counter(row["outcome"] for row in results)),
        "execution_errors": dict(
            Counter(row["execution_error"] for row in results if row.get("execution_error"))
        ),
        "case_cost_usd": sum(row.get("cost_usd", 0) for row in results),
        "paid_calls": 0,
    }
    return summary


def main() -> int:
    sys.stdout.write(json.dumps(asyncio.run(mock()), indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
