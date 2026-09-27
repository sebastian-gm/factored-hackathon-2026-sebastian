"""Metadata-only baseline diagnosis and revised-prompt comparison.

Run with process-local LLM_REAL_CALLS_APPROVED=1 after owner approval. The
checkpoint is ignored by Git and contains synthetic case IDs, labels, and
per-call metadata, never messages or model output.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from threading import Lock
from typing import Any, cast

from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.nlu.structured import ExtractedNlu, postprocess
from aclara.llm.client import StructuredClient
from aclara.llm.comparison import _percentile, _slot_pairs
from aclara.llm.prompts import data_block, load_prompt
from aclara.llm.round_one import CAP_USD, MODEL_IDS, ROOT, _cases, _catalog, _local_key
from aclara.llm.types import ModelFailure

LOGGER = logging.getLogger(__name__)
ARTIFACTS = ROOT / "artifacts/ai-round-one"
REVISED_MODELS = tuple(model_id for model_id in MODEL_IDS if not model_id.startswith("qwen/"))
ORIGINAL_COST_FILES = ("pilot.json", "summary.json")
FOLLOWUP_COST_FILES = ("baseline-diagnostic.json", "revised.json")


def _recorded_cost(path: Path) -> float:
    if not path.exists():
        return 0.0
    data = json.loads(path.read_text(encoding="utf-8"))
    if path.name in ORIGINAL_COST_FILES:
        return float(data["client_recorded_cost_usd"])
    return sum(
        float(record["cost_usd"])
        for observation in data["observations"]
        for record in observation["attempts"]
        if record["cost_usd"] is not None
    )


def cumulative_cost() -> float:
    return sum(
        _recorded_cost(ARTIFACTS / name) for name in (*ORIGINAL_COST_FILES, *FOLLOWUP_COST_FILES)
    )


def _write(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    pending.replace(path)


def _summaries(
    observations: list[dict[str, Any]], model_ids: tuple[str, ...]
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        grouped[str(observation["model_id"])].append(observation)
    rows: list[dict[str, object]] = []
    for model_id in model_ids:
        cases = grouped[model_id]
        if not cases:
            continue
        attempts = [attempt for case in cases for attempt in case["attempts"]]
        tp = sum(int(case["slot_tp"]) for case in cases)
        fp = sum(int(case["slot_fp"]) for case in cases)
        fn = sum(int(case["slot_fn"]) for case in cases)
        latencies = [float(sum(float(a["latency_ms"]) for a in case["attempts"])) for case in cases]
        costs = [attempt["cost_usd"] for attempt in attempts]
        rows.append(
            {
                "model": model_id,
                "cases": len(cases),
                "intent_accuracy": sum(
                    case["predicted_intent"] == case["gold_intent"] for case in cases
                )
                / len(cases),
                "slot_f1": 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0,
                "valid_json_all_attempts": sum(a["status"] == "valid" for a in attempts)
                / len(attempts),
                "valid_final_cases": sum(case["predicted_intent"] is not None for case in cases),
                "attempts": len(attempts),
                "attempt_statuses": {
                    status: sum(a["status"] == status for a in attempts)
                    for status in ("valid", "invalid_json", "refusal", "provider_error")
                },
                "stop_reasons": {
                    reason: sum(a["stop_reason"] == reason for a in attempts)
                    for reason in sorted({str(a["stop_reason"]) for a in attempts})
                },
                "p50_latency_ms": median(latencies),
                "p95_latency_ms": _percentile(latencies, 0.95),
                "cost_per_case_usd": (
                    sum(float(cost) for cost in costs) / len(cases)
                    if all(cost is not None for cost in costs)
                    else None
                ),
            }
        )
    return rows


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("baseline-diagnostic", "revised"))
    parser.add_argument("--pilot", action="store_true", help="Run only the first case per model")
    args = parser.parse_args()
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Process-local owner approval gate is required")
    os.environ["OPENROUTER_API_KEY"] = _local_key()
    cases, suite_hash = _cases()
    if args.pilot:
        cases = cases[:1]
    model_ids = MODEL_IDS if args.phase == "baseline-diagnostic" else REVISED_MODELS
    prompt_path = ROOT / (
        "prompts/nlu/v1.md" if args.phase == "baseline-diagnostic" else "prompts/nlu/v2.md"
    )
    prompt = load_prompt(prompt_path)
    models, prices = _catalog(model_ids)
    if args.phase == "revised":
        for model_id in model_ids:
            models[model_id] = replace(models[model_id], max_output_tokens=2048)
        deepseek = model_ids[0]
        models[deepseek] = replace(
            models[deepseek], provider_only=("wafer/fast",), reasoning_effort="low"
        )
    output = ARTIFACTS / f"{args.phase}.json"
    data: dict[str, object] = (
        json.loads(output.read_text(encoding="utf-8"))
        if output.exists()
        else {
            "phase": args.phase,
            "suite_sha256": suite_hash,
            "suite_reviewed": False,
            "prompt_version": prompt.version,
            "prompt_hash": prompt.content_hash,
            "models": list(model_ids),
            "deepseek_provider_only": list(models[model_ids[0]].provider_only),
            "deepseek_reasoning_effort": models[model_ids[0]].reasoning_effort,
            "max_output_tokens": models[model_ids[0]].max_output_tokens,
            "observations": [],
        }
    )
    if data["suite_sha256"] != suite_hash or data["prompt_hash"] != prompt.content_hash:
        raise RuntimeError("Suite or prompt changed during checkpointed evaluation")
    observations = cast(list[dict[str, Any]], data["observations"])
    done = {(str(item["model_id"]), str(item["case_id"])) for item in observations}
    remaining = CAP_USD - cumulative_cost()
    if remaining <= 0:
        raise RuntimeError("Cumulative approved $5 cap reached")
    lock = Lock()
    # Independent model budgets sum to at most the remaining approved cap.
    model_budget = min(0.25, remaining / len(model_ids))

    def run_model(model_id: str) -> None:
        client = StructuredClient(
            {model_id: models[model_id]},
            {model_id: prices[model_id]},
            budget_usd=model_budget,
            daily_budget_usd=model_budget,
        )
        LOGGER.info("%s: %s", args.phase, model_id)
        for case in cases:
            if (model_id, case.case_id) in done:
                continue
            prior = len(client.records)
            predicted: str | None = None
            gold_slots = _slot_pairs(case.gold_slots, case.scored_slot_keys)
            predicted_slots: set[tuple[str, str]] = set()
            try:
                extracted = client.generate(
                    model_id,
                    prompt.text,
                    data_block("customer_message", redact_for_model(case.message)),
                    ExtractedNlu,
                    prompt_id=f"{prompt.id}@{prompt.version}",
                    prompt_hash=prompt.content_hash,
                )
                result = postprocess(extracted, country=case.country, bank_clock=case.bank_clock)
                predicted = result.extracted.intent
                predicted_slots = _slot_pairs(result.slots.model_dump(), case.scored_slot_keys)
            except ModelFailure:
                pass
            records = client.records[prior:]
            if not records:
                raise RuntimeError(
                    "No model attempt recorded; stop rather than hide a budget failure"
                )
            attempts = [
                {
                    "status": record.status,
                    "stop_reason": record.stop_reason,
                    "latency_ms": record.latency_ms,
                    "cost_usd": record.cost_usd,
                    "input_tokens": record.input_tokens,
                    "output_tokens": record.output_tokens,
                    "served_model_id": record.model_id,
                    "generation_id": record.generation_id,
                }
                for record in records
            ]
            if any(attempt["cost_usd"] is None for attempt in attempts):
                raise RuntimeError(
                    "Per-call cost missing; stop rather than infer from key-level usage"
                )
            with lock:
                observations.append(
                    {
                        "model_id": model_id,
                        "case_id": case.case_id,
                        "gold_intent": case.gold_intent,
                        "predicted_intent": predicted,
                        "slot_tp": len(predicted_slots & gold_slots),
                        "slot_fp": len(predicted_slots - gold_slots),
                        "slot_fn": len(gold_slots - predicted_slots),
                        "attempts": attempts,
                    }
                )
                data["rows"] = _summaries(observations, model_ids)
                data["updated_at_utc"] = datetime.now(UTC).isoformat()
                _write(output, data)
                if cumulative_cost() >= CAP_USD:
                    raise RuntimeError("Cumulative approved $5 cap reached")
        LOGGER.info(
            "  complete: %d/32; cumulative response cost $%.6f",
            sum(o["model_id"] == model_id for o in observations),
            cumulative_cost(),
        )

    with ThreadPoolExecutor(max_workers=len(model_ids)) as executor:
        futures = [executor.submit(run_model, model_id) for model_id in model_ids]
        for future in futures:
            future.result()
    LOGGER.info("Saved metadata-only diagnostics to %s", output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
