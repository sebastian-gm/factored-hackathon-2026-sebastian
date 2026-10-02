"""Checkpointed, metadata-only round-two NLU comparison on synthetic dev cases."""

from __future__ import annotations

import argparse
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from threading import Lock
from time import sleep
from typing import Any

import yaml  # type: ignore[import-untyped]

from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.nlu.structured import ExtractedNlu, postprocess
from aclara.llm.client import StructuredClient
from aclara.llm.prompts import data_block, load_prompt
from aclara.llm.types import ModelFailure
from evals.studies.llm.comparison import ComparisonCase, _slot_pairs
from evals.studies.llm.round_one import ROOT, _catalog, _local_key
from evals.studies.llm.round_one_followup import cumulative_cost as round_one_cost

LOGGER = logging.getLogger(__name__)
SUITE = ROOT / "evals/studies/llm/dev_150.yaml"
PROMPT = ROOT / "prompts/nlu/v3.md"
ARTIFACTS = ROOT / "artifacts/ai-round-two"
CAP_USD = 10.0
SAFETY_RESERVE_USD = 0.30
MODEL_IDS = (
    "google/gemini-2.5-flash-lite",
    "google/gemini-3.5-flash-lite",
    "google/gemini-3-flash-preview",
    "x-ai/grok-4.3",
    "anthropic/claude-haiku-4.5",
    "anthropic/claude-sonnet-5",
    "anthropic/claude-opus-5",
)
OPUS_SAMPLE_IDS = frozenset(
    {
        "mx.03",
        "mx.04",
        "mx.15",
        "mx.22",
        "mx.24",
        "mx.27",
        "co.01",
        "co.08",
        "co.17",
        "co.19",
        "co.20",
        "co.23",
        "ar.07",
        "ar.12",
        "ar.16",
        "ar.18",
        "ar.21",
        "ar.25",
        "br.10",
        "br.13",
        "br.14",
        "br.15",
        "br.24",
        "br.30",
        "mix.05",
        "mix.08",
        "mix.17",
        "mix.20",
        "mix.21",
        "mix.26",
    }
)
SCORED_SLOTS = ("amount_value", "currency", "merchant_expr", "date_expr")
MODEL_BUDGETS_USD = (0.25, 0.50, 0.60, 1.00, 1.00, 2.00, 1.50)


def load_cases() -> tuple[list[ComparisonCase], dict[str, dict[str, Any]], str]:
    source = SUITE.read_bytes()
    suite = yaml.safe_load(source)
    if not isinstance(suite, dict) or suite.get("version") != 1:
        raise ValueError("Unexpected NLU dev suite version")
    entries = suite["cases"]
    if not isinstance(entries, list) or len(entries) != 150:
        raise ValueError("Round-two NLU dev suite must have exactly 150 cases")
    cases: list[ComparisonCase] = []
    metadata: dict[str, dict[str, Any]] = {}
    for item in entries:
        case_id = str(item["id"])
        if case_id in metadata or item["source"] != "team_authored_unreviewed":
            raise ValueError("Duplicate case or unverified source marker")
        country = str(item["country"])
        language = str(item["language"])
        if language not in {"es", "pt", "mixed"} or country not in {"MX", "CO", "AR", "BR", ""}:
            raise ValueError("Invalid country/language label")
        message = str(item["message"])
        slots = {str(key): str(value) for key, value in item["gold_slots"].items()}
        if any(key not in SCORED_SLOTS for key in slots):
            raise ValueError("Unknown scored slot")
        cases.append(
            ComparisonCase(
                message=message,
                country=country,
                bank_clock=datetime(2026, 6, 18, 6, tzinfo=UTC),
                gold_intent=str(item["gold_intent"]),
                gold_slots=slots,
                language=language,
                scored_slot_keys=SCORED_SLOTS,
                case_id=case_id,
            )
        )
        metadata[case_id] = {"tags": item["tags"], "language": language, "country": country}
    if len({case.message for case in cases}) != 150:
        raise ValueError("Duplicate dev utterance")
    return cases, metadata, sha256(source).hexdigest()


def sample_for(model_id: str, cases: list[ComparisonCase]) -> list[ComparisonCase]:
    if model_id != "anthropic/claude-opus-5":
        return cases
    return [case for case in cases if case.case_id in OPUS_SAMPLE_IDS]


def _read(path: Path) -> dict[str, Any] | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pending.chmod(0o600)
    pending.replace(path)


def _cost(data: dict[str, Any] | None) -> float:
    if data is None:
        return 0.0
    return sum(float(a["cost_usd"]) for o in data["observations"] for a in o["attempts"])


def cumulative_cost() -> float:
    return round_one_cost() + sum(
        _cost(_read(ARTIFACTS / name))
        for name in ("pilot.json", "haiku-first-pass.json", "full.json")
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--model", choices=MODEL_IDS, help="Resume one model from the checkpoint")
    args = parser.parse_args()
    cases, metadata, suite_hash = load_cases()
    prompt = load_prompt(PROMPT)
    models, prices = _catalog(MODEL_IDS)
    for model_id in MODEL_IDS:
        models[model_id] = replace(models[model_id], max_output_tokens=2048)
    haiku = "anthropic/claude-haiku-4.5"
    models[haiku] = replace(
        models[haiku], provider_only=("amazon-bedrock/global",), timeout_seconds=60
    )
    if args.dry_run:
        LOGGER.info(
            "Unreviewed 150-case suite SHA-256 %s; prompt SHA-256 %s",
            suite_hash,
            prompt.content_hash,
        )
        LOGGER.info(
            "Prior per-call spend $%.6f; hard cumulative cap $%.2f", round_one_cost(), CAP_USD
        )
        for model_id in MODEL_IDS:
            price = prices[model_id]
            LOGGER.info(
                "%s: %d cases, $%g/M input, $%g/M output",
                model_id,
                len(sample_for(model_id, cases)),
                price.input_per_million,
                price.output_per_million,
            )
        return 0
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Process-local owner approval gate is required")
    os.environ["OPENROUTER_API_KEY"] = _local_key()
    path = ARTIFACTS / ("pilot.json" if args.pilot else "full.json")
    data = _read(path)
    if data is None:
        data = {
            "suite_sha256": suite_hash,
            "suite_reviewed": False,
            "prompt_hash": prompt.content_hash,
            "prompt_version": prompt.version,
            "models": list(MODEL_IDS),
            "opus_sample_ids": sorted(OPUS_SAMPLE_IDS),
            "max_output_tokens": 2048,
            "haiku_provider_only": ["amazon-bedrock/global"],
            "cap_usd": CAP_USD,
            "model_choice": None,
            "observations": [],
        }
    if data["suite_sha256"] != suite_hash or data["prompt_hash"] != prompt.content_hash:
        raise RuntimeError("Suite or prompt changed during checkpointed evaluation")
    observations = data["observations"]
    done = {(o["model_id"], o["case_id"]) for o in observations}
    remaining = CAP_USD - cumulative_cost() - SAFETY_RESERVE_USD
    selected_models = [
        (model_id, budget)
        for model_id, budget in zip(MODEL_IDS, MODEL_BUDGETS_USD, strict=True)
        if args.model is None or args.model == model_id
    ]
    if sum(budget for _, budget in selected_models) > remaining:
        raise RuntimeError("Allocated model budgets exceed the approved cumulative cap guard")
    lock = Lock()

    def run_model(model_id: str, model_budget: float) -> None:
        selected = sample_for(model_id, cases)
        if args.pilot:
            selected = selected[:1]
        LOGGER.info("%s: %d cases", model_id, len(selected))
        client = StructuredClient(
            {model_id: models[model_id]},
            {model_id: prices[model_id]},
            budget_usd=model_budget,
            daily_budget_usd=model_budget,
        )
        for index, case in enumerate(selected, 1):
            if (model_id, case.case_id) in done:
                continue
            prior = len(client.records)
            predicted: str | None = None
            predicted_language: str | None = None
            predicted_slots: set[tuple[str, str]] = set()
            injection_suspected: bool | None = None
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
                predicted_language = result.extracted.language
                injection_suspected = result.extracted.injection_suspected
                slot_values = result.slots.model_dump()
                slot_values["date_expr"] = result.extracted.date_expr
                predicted_slots = _slot_pairs(slot_values, SCORED_SLOTS)
            except ModelFailure as exc:
                cause = exc.__cause__
                LOGGER.warning(
                    "%s %s no final response: %s; provider cause=%s; http_status=%s",
                    model_id,
                    case.case_id,
                    exc,
                    type(cause).__name__ if cause else "none",
                    getattr(cause, "code", "none"),
                )
            if len(client.records) == prior:
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
                for record in client.records[prior:]
            ]
            if any(attempt["cost_usd"] is None for attempt in attempts):
                raise RuntimeError("Per-call cost missing; stop rather than infer key-level usage")
            gold_slots = _slot_pairs(case.gold_slots, SCORED_SLOTS)
            with lock:
                observations.append(
                    {
                        "model_id": model_id,
                        "case_id": case.case_id,
                        "gold_intent": case.gold_intent,
                        "predicted_intent": predicted,
                        "gold_language": case.language,
                        "predicted_language": predicted_language,
                        "tags": metadata[case.case_id]["tags"],
                        "injection_suspected": injection_suspected,
                        "slot_tp": len(predicted_slots & gold_slots),
                        "slot_fp": len(predicted_slots - gold_slots),
                        "slot_fn": len(gold_slots - predicted_slots),
                        "attempts": attempts,
                    }
                )
                data["updated_at_utc"] = datetime.now(UTC).isoformat()
                _write(path, data)
                if cumulative_cost() >= CAP_USD:
                    raise RuntimeError("Approved $10 cumulative cap reached")
                if index % 20 == 0 or args.pilot:
                    LOGGER.info(
                        "  %s %d/%d; cumulative per-call spend $%.6f",
                        model_id,
                        index,
                        len(selected),
                        cumulative_cost(),
                    )
            if model_id == "anthropic/claude-haiku-4.5":
                sleep(3)  # Keep the pinned ZDR route well below likely provider rate limits.

    with ThreadPoolExecutor(max_workers=len(selected_models)) as executor:
        futures = [
            executor.submit(run_model, model_id, budget) for model_id, budget in selected_models
        ]
        for future in futures:
            future.result()
    LOGGER.info(
        "Complete: %d model-case results; cumulative per-call spend $%.6f",
        len(observations),
        cumulative_cost(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
