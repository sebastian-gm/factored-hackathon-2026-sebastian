"""Checkpointed synthetic Gemini-v4/Jev comparison and Jev judge smoke."""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, cast

from dotenv import dotenv_values
from typesafe_sdk import RetryPolicy, TypeSafeClient

from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.llm.client import StructuredClient
from aclara.llm.config import load_models, load_prices
from aclara.llm.prompts import data_block, load_prompt
from aclara.llm.types import ModelFailure
from aclara.llm.typesafe import INPUT_USD_PER_MILLION, MODEL_ID, TypeSafeAdapter
from aclara.llm.typesafe_questions import (
    INTENT_LABELS,
    QUESTION_VERSION,
    RISK_CUES,
    judge_questions,
    nlu_questions,
)
from evals.studies.llm.judge import SMOKE_OUTPUT, _read_samples, _smoke_sample
from evals.studies.llm.judge_validation import SHEET
from evals.studies.llm.round_one import ROOT
from evals.studies.llm.round_two import load_cases

ARTIFACTS = ROOT / "artifacts/typesafe"
CHECKPOINTS = {
    "baseline": ARTIFACTS / "gemini-v4-150.json",
    "jev": ARTIFACTS / "jev-150.json",
    "judge": ARTIFACTS / "jev-judge-smoke.json",
}
PROMPT = ROOT / "prompts/nlu/v4.md"
QUESTION_SOURCE = ROOT / "src/aclara/llm/typesafe_questions.py"
CAP_USD = 1.0
UNKNOWN_RESERVES = {"openrouter": 0.025, "typesafe": 0.01}
NEXT_GUARDS = {"baseline": 0.05, "jev": 0.01, "judge": 0.01}
LOGGER = logging.getLogger(__name__)


def _private_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".tmp")
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    pending.replace(path)


def _checkpoint(stage: str, *, suite_hash: str, prompt_hash: str) -> dict[str, Any]:
    path = CHECKPOINTS[stage]
    questions_hash = sha256(QUESTION_SOURCE.read_bytes()).hexdigest()
    expected = {
        "stage": stage,
        "suite_sha256": suite_hash,
        "prompt_sha256": prompt_hash,
        "question_version": QUESTION_VERSION,
        "questions_sha256": questions_hash,
        "cap_usd": CAP_USD,
    }
    if path.exists():
        data = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        if any(data.get(key) != value for key, value in expected.items()):
            raise RuntimeError("TypeSafe comparison input changed after checkpoint creation")
        return data
    return {**expected, "observations": []}


def exposure() -> tuple[float, int, float]:
    """Known per-call cost, unknown attempts, and guarded cumulative exposure."""
    known = 0.0
    unknown = 0
    reserve = 0.0
    for path in CHECKPOINTS.values():
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data["observations"]:
            for attempt in row["attempts"]:
                cost = attempt["cost_usd"]
                if cost is None:
                    unknown += 1
                    reserve += UNKNOWN_RESERVES[attempt["provider"]]
                else:
                    known += float(cost)
    return known, unknown, known + reserve


def _budget(stage: str) -> float:
    _, _, guarded = exposure()
    if guarded + NEXT_GUARDS[stage] > CAP_USD:
        raise RuntimeError("Combined OpenRouter/TypeSafe $1 cap cannot reserve the next call")
    return CAP_USD - guarded


def _local_secret(name: str) -> str:
    value = dotenv_values(ROOT / ".env").get(name)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Local {name} is unavailable")
    return value


def _approved() -> None:
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1" or os.getenv("TYPESAFE_EVAL_APPROVED") != "1":
        raise RuntimeError("This paid comparison needs its process-local owner approval gates")


def baseline(*, limit: int) -> dict[str, Any]:
    _approved()
    cases, metadata, suite_hash = load_cases()
    prompt = load_prompt(PROMPT)
    data = _checkpoint("baseline", suite_hash=suite_hash, prompt_hash=prompt.content_hash)
    rows: list[dict[str, Any]] = data["observations"]
    done = {row["case_id"] for row in rows}
    models = load_models(ROOT / "config/models.yaml")
    prices = load_prices(ROOT / "config/pricing.yaml")
    spec = models["default"]
    if spec.model_id != "google/gemini-3-flash-preview" or spec.provider_only != (
        "google-vertex/global",
    ):
        raise RuntimeError("Gemini v4 baseline route is not pinned as planned")
    os.environ["OPENROUTER_API_KEY"] = _local_secret("OPENROUTER_API_KEY")
    client = StructuredClient(
        {"baseline": spec}, prices, budget_usd=_budget("baseline"), daily_budget_usd=CAP_USD
    )
    for case in cases[:limit]:
        if case.case_id in done:
            continue
        _budget("baseline")
        first = len(client.records)
        predicted: str | None = None
        confidence: float | None = None
        flags: dict[str, bool] = {}
        try:
            result = client.generate(
                "baseline",
                prompt.text,
                data_block("customer_message", redact_for_model(case.message)),
                ExtractedNlu,
                prompt_id=f"{prompt.id}@{prompt.version}",
                prompt_hash=prompt.content_hash,
            )
            predicted = result.intent
            confidence = result.intent_confidence
            flags = {cue: bool(getattr(result, cue)) for cue in RISK_CUES}
        except ModelFailure:
            pass
        attempts = [
            {
                "provider": "openrouter",
                "status": record.status,
                "served_model_id": record.model_id,
                "input_tokens": record.input_tokens,
                "output_tokens": record.output_tokens,
                "latency_ms": record.latency_ms,
                "cost_usd": record.cost_usd,
            }
            for record in client.records[first:]
        ]
        if not attempts:
            raise RuntimeError("No Gemini attempt recorded; preserve the budget checkpoint")
        rows.append(
            {
                "case_id": case.case_id,
                "language": case.language,
                "gold_intent": case.gold_intent,
                "gold_injection": "injection" in metadata[case.case_id]["tags"],
                "predicted_intent": predicted,
                "intent_probability": confidence,
                "risk_flags": flags,
                "attempts": attempts,
            }
        )
        _private_write(CHECKPOINTS["baseline"], data)
    return data


def _jev_attempt(result: Any) -> dict[str, Any]:
    return {
        "provider": "typesafe",
        "status": "valid",
        "served_model_id": result.model_id,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "latency_ms": result.latency_ms,
        "cost_usd": result.cost_usd,
    }


def jev(*, limit: int) -> dict[str, Any]:
    _approved()
    cases, metadata, suite_hash = load_cases()
    data = _checkpoint("jev", suite_hash=suite_hash, prompt_hash=load_prompt(PROMPT).content_hash)
    rows: list[dict[str, Any]] = data["observations"]
    done = {row["case_id"] for row in rows}
    price = load_prices(ROOT / "config/pricing.yaml")[MODEL_ID]
    if price.input_per_million != INPUT_USD_PER_MILLION or price.output_per_million != 0:
        raise RuntimeError("Pinned Jev usage price differs from the adapter")
    consecutive_errors = 0
    with TypeSafeClient(
        api_key=_local_secret("TYPESAFE_API_KEY"),
        model=MODEL_ID,
        retry=RetryPolicy(max_retries=0),
        timeout=20.0,
    ) as raw:
        adapter = TypeSafeAdapter(raw)
        for case in cases[:limit]:
            if case.case_id in done:
                continue
            _budget("jev")
            started = perf_counter()
            predicted: str | None = None
            probability: float | None = None
            distribution: dict[str, float] = {}
            cues: dict[str, float] = {}
            try:
                result = adapter.ask(
                    {"customer_message": redact_for_model(case.message)}, nlu_questions()
                )
                choice = result.choices["intent"]
                if set(choice.probabilities) != set(INTENT_LABELS):
                    raise ValueError("Jev intent distribution is missing a configured option")
                predicted = choice.choice
                probability = choice.probabilities[predicted]
                distribution = choice.probabilities
                cues = {name: result.nouls[name] for name in RISK_CUES}
                attempts = [_jev_attempt(result)]
                consecutive_errors = 0
            except Exception as exc:
                attempts = [
                    {
                        "provider": "typesafe",
                        "status": "provider_error",
                        "error_type": type(exc).__name__,
                        "served_model_id": MODEL_ID,
                        "input_tokens": None,
                        "output_tokens": None,
                        "latency_ms": (perf_counter() - started) * 1000,
                        "cost_usd": None,
                    }
                ]
                consecutive_errors += 1
            rows.append(
                {
                    "case_id": case.case_id,
                    "language": case.language,
                    "gold_intent": case.gold_intent,
                    "gold_injection": "injection" in metadata[case.case_id]["tags"],
                    "predicted_intent": predicted,
                    "intent_probability": probability,
                    "intent_distribution": distribution,
                    "risk_probabilities": cues,
                    "attempts": attempts,
                }
            )
            _private_write(CHECKPOINTS["jev"], data)
            if consecutive_errors >= 3:
                raise RuntimeError("Three consecutive Jev errors; inspect ignored checkpoint")
    return data


def judge() -> dict[str, Any]:
    _approved()
    sonnet = json.loads(SMOKE_OUTPUT.read_text(encoding="utf-8"))
    samples, sheet_hash = _read_samples(SHEET)
    if sonnet["sheet_sha256"] != sheet_hash:
        raise RuntimeError("The prior Sonnet smoke used different human-sheet bytes")
    selected = _smoke_sample(samples)
    expected_ids = {row["sample_id"] for row in selected}
    if (
        len(sonnet["results"]) != 3
        or {row["sample_id"] for row in sonnet["results"]} != expected_ids
    ):
        raise RuntimeError("Sonnet and Jev judge smoke sample IDs differ")
    if any(row["status"] != "valid" for row in sonnet["results"]):
        raise RuntimeError("Sonnet judge smoke is not fully valid")
    data = _checkpoint("judge", suite_hash=sheet_hash, prompt_hash=sonnet["prompt_sha256"])
    rows: list[dict[str, Any]] = data["observations"]
    done = {row["sample_id"] for row in rows}
    consecutive_errors = 0
    with TypeSafeClient(
        api_key=_local_secret("TYPESAFE_API_KEY"),
        model=MODEL_ID,
        retry=RetryPolicy(max_retries=0),
        timeout=20.0,
    ) as raw:
        adapter = TypeSafeAdapter(raw)
        for sample in selected:
            if sample["sample_id"] in done:
                continue
            _budget("judge")
            handoff = sample["handoff_summary"].strip() or None
            state = {
                "target_locale": sample["target_locale"],
                "customer_message": redact_for_model(sample["customer_message"]),
                "customer_reply": redact_for_model(sample["customer_reply"]),
                "handoff_summary": redact_for_model(handoff) if handoff else None,
            }
            started = perf_counter()
            scores: dict[str, int | None] | None = None
            expected: dict[str, float] = {}
            try:
                result = adapter.ask(state, judge_questions(has_handoff=handoff is not None))
                expected = {name: 1 + value.score for name, value in result.scores.items()}
                scores = {
                    name: min(5, max(1, 1 + math.floor(value.score + 0.5)))
                    for name, value in result.scores.items()
                }
                if handoff is None:
                    scores["handoff_usefulness"] = None
                attempts = [_jev_attempt(result)]
                consecutive_errors = 0
            except Exception as exc:
                attempts = [
                    {
                        "provider": "typesafe",
                        "status": "provider_error",
                        "error_type": type(exc).__name__,
                        "served_model_id": MODEL_ID,
                        "input_tokens": None,
                        "output_tokens": None,
                        "latency_ms": (perf_counter() - started) * 1000,
                        "cost_usd": None,
                    }
                ]
                consecutive_errors += 1
            rows.append(
                {
                    "sample_id": sample["sample_id"],
                    "scores": scores,
                    "expected_scores": expected,
                    "attempts": attempts,
                }
            )
            _private_write(CHECKPOINTS["judge"], data)
            if consecutive_errors >= 3:
                raise RuntimeError("Three consecutive Jev judge errors; inspect ignored checkpoint")
    return data


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("typesafe_sdk").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=(*CHECKPOINTS, "report"), required=True)
    parser.add_argument(
        "--limit", type=int, default=None, help="Pilot a prefix, then resume all cases"
    )
    args = parser.parse_args()
    if args.stage == "report":
        from evals.studies.llm.typesafe_report import report

        LOGGER.info("%s", json.dumps(report(), sort_keys=True))
        return 0
    max_cases = 3 if args.stage == "judge" else 150
    limit = max_cases if args.limit is None else args.limit
    if not 1 <= limit <= max_cases:
        raise ValueError("Stage limit is outside its fixed suite")
    if args.stage == "baseline":
        data = baseline(limit=limit)
    elif args.stage == "jev":
        data = jev(limit=limit)
    else:
        data = judge()
    known, unknown, guarded = exposure()
    LOGGER.info(
        "Stage %s: %d saved; known per-call cost $%.6f; unknown attempts %d; guarded $%.6f/$%.2f",
        args.stage,
        len(data["observations"]),
        known,
        unknown,
        guarded,
        CAP_USD,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
