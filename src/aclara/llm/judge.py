"""Blinded, subjective-only Sonnet judge with bounded paid-call checkpoints."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aclara.agent.nlg.grounding import redact_for_model
from aclara.llm.client import StructuredClient
from aclara.llm.final_run import client_for, journal, open_budget_store, require_start
from aclara.llm.judge_validation import ARTIFACTS, DIMENSIONS, SHEET
from aclara.llm.prompts import Prompt, data_block, load_prompt
from aclara.llm.round_one import ROOT, _catalog, _local_key
from aclara.llm.types import ModelFailure
from aclara.ops.store import Store

MODEL_ID = "anthropic/claude-sonnet-5"
PROVIDER_ONLY = ("google-vertex/global",)
PROMPT = ROOT / "prompts/judge/v1.md"
SMOKE_OUTPUT = ARTIFACTS / "smoke-results.json"
FULL_OUTPUT = ARTIFACTS / "judge-results-50.json"
FULL_CSV = ARTIFACTS / "judge-results-50.csv"
SMOKE_MAX_USD = 0.49
SMOKE_CASES = 3
LOGGER = logging.getLogger(__name__)


class JudgeScores(BaseModel):
    """Only subjective ordinal scores; no explanation or objective outcome fields."""

    model_config = ConfigDict(extra="forbid", strict=True)

    language_register: int = Field(ge=1, le=5)
    clarity: int = Field(ge=1, le=5)
    empathy: int = Field(ge=1, le=5)
    handoff_usefulness: int | None = Field(ge=1, le=5)


def _private_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    pending.replace(path)


def _read_samples(path: Path) -> tuple[list[dict[str, str]], str]:
    raw = path.read_bytes()
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 50 or len({row["sample_id"] for row in rows}) != 50:
        raise ValueError("Judge calibration requires 50 unique synthetic samples")
    required = {
        "sample_id",
        "target_locale",
        "customer_message",
        "customer_reply",
        "handoff_summary",
    }
    if any(not required.issubset(row) for row in rows):
        raise ValueError("Human-review sheet is missing judge input fields")
    return rows, sha256(raw).hexdigest()


def _smoke_sample(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for group in ("es-MX", "pt-BR", "mixed"):
        selected.append(next(row for row in rows if row["language_group"] == group))
    return selected


def _score(client: StructuredClient, row: dict[str, str], prompt: Prompt) -> JudgeScores:
    handoff = row["handoff_summary"].strip() or None
    content = {
        "target_locale": row["target_locale"],
        "customer_message": redact_for_model(row["customer_message"]),
        "customer_reply": redact_for_model(row["customer_reply"]),
        "handoff_summary": redact_for_model(handoff) if handoff is not None else None,
    }
    scored = client.generate(
        MODEL_ID,
        prompt.text,
        data_block("record", json.dumps(content, ensure_ascii=False), max_chars=8000),
        JudgeScores,
        prompt_id=f"{prompt.id}@{prompt.version}",
        prompt_hash=prompt.content_hash,
    )
    if (scored.handoff_usefulness is None) != (handoff is None):
        raise ModelFailure("Judge handoff score does not match summary presence")
    return scored


def _known_cost(results: list[dict[str, Any]]) -> float:
    return sum(
        float(attempt["cost_usd"])
        for result in results
        for attempt in result["attempts"]
        if attempt["cost_usd"] is not None
    )


def _unknown_attempts(results: list[dict[str, Any]]) -> int:
    return sum(attempt["cost_usd"] is None for result in results for attempt in result["attempts"])


def _full_csv(results: list[dict[str, Any]]) -> None:
    if len(results) != 50 or any(result["status"] != "valid" for result in results):
        return
    path = FULL_CSV
    pending = path.with_suffix(".tmp")
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("sample_id", *DIMENSIONS))
        writer.writeheader()
        writer.writerows(
            {"sample_id": result["sample_id"], **result["scores"]} for result in results
        )
    pending.replace(path)


def run(
    *, smoke: bool, budget_usd: float, sheet_path: Path = SHEET, final_store: Store | None = None
) -> dict[str, Any]:
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Process-local owner approval gate is required")
    if smoke:
        if os.getenv("JUDGE_SMOKE_APPROVED") != "1" or not 0 < budget_usd <= SMOKE_MAX_USD:
            raise RuntimeError("Smoke requires its process-local approval and a sub-$0.50 cap")
    elif os.getenv("LLM_JUDGE_FULL_RUN_APPROVED") != "1" or budget_usd <= 0:
        raise RuntimeError("Full paid judge calibration requires a separate owner approval")
    if not smoke:
        require_start()
        if final_store is None:
            raise RuntimeError("Full judge requires the shared final-program budget")
    rows, sheet_hash = _read_samples(sheet_path)
    selected = _smoke_sample(rows) if smoke else rows
    prompt = load_prompt(PROMPT)
    output = SMOKE_OUTPUT if smoke else FULL_OUTPUT
    data: dict[str, Any]
    if output.exists():
        data = json.loads(output.read_text(encoding="utf-8"))
        if data["sheet_sha256"] != sheet_hash or data["prompt_sha256"] != prompt.content_hash:
            raise RuntimeError("Judge sheet/prompt changed after checkpoint creation")
    else:
        data = {
            "model_id": MODEL_ID,
            "provider_only": list(PROVIDER_ONLY),
            "sheet_sha256": sheet_hash,
            "prompt_sha256": prompt.content_hash,
            "subjective_only": True,
            "mode": "smoke" if smoke else "full",
            "results": [],
        }
    results: list[dict[str, Any]] = data["results"]
    done = {result["sample_id"] for result in results}
    if len(done) == len(selected):
        return data
    remaining = budget_usd - _known_cost(results) - 0.05 * _unknown_attempts(results)
    if remaining <= 0:
        raise RuntimeError("Judge budget exhausted by prior attempts")
    if final_store is not None:
        client = client_for(
            "openrouter_sonnet",
            final_store,
            judge=True,
            response_record=journal(output.with_suffix(".calls.jsonl")),
        )
    else:
        models, prices = _catalog((MODEL_ID,))
        spec = replace(
            models[MODEL_ID],
            provider_only=PROVIDER_ONLY,
            max_output_tokens=256,
            timeout_seconds=60,
        )
        os.environ["OPENROUTER_API_KEY"] = _local_key()
        client = StructuredClient(
            {MODEL_ID: spec},
            {MODEL_ID: prices[MODEL_ID]},
            budget_usd=remaining,
            daily_budget_usd=remaining,
        )
    for row in selected:
        if row["sample_id"] in done:
            continue
        first = len(client.records)
        scores: dict[str, int | None] | None = None
        status = "valid"
        try:
            scores = _score(client, row, prompt).model_dump()
        except ModelFailure:
            status = "no_valid_final"
        attempts = [
            {
                "status": record.status,
                "stop_reason": record.stop_reason,
                "input_tokens": record.input_tokens,
                "output_tokens": record.output_tokens,
                "latency_ms": record.latency_ms,
                "cost_usd": record.cost_usd,
                "served_model_id": record.model_id,
                "generation_id": record.generation_id,
            }
            for record in client.records[first:]
        ]
        if not attempts:
            raise RuntimeError("No judge attempt recorded; preserve the budget checkpoint")
        results.append(
            {
                "sample_id": row["sample_id"],
                "scores": scores,
                "status": status,
                "attempts": attempts,
            }
        )
        _private_write(output, data)
        if _known_cost(results) + 0.05 * _unknown_attempts(results) >= budget_usd:
            raise RuntimeError("Judge budget cap reached")
    if not smoke:
        _full_csv(results)
    return data


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--smoke", action="store_true")
    choices.add_argument("--full", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=SMOKE_MAX_USD)
    args = parser.parse_args()
    store = open_budget_store() if args.full else None
    try:
        data = run(smoke=args.smoke, budget_usd=args.budget_usd, final_store=store)
    finally:
        if store:
            store.close()
    results = data["results"]
    LOGGER.info(
        f"Judge {data['mode']}: {sum(row['status'] == 'valid' for row in results)}/{len(results)} valid; "
        f"known per-call cost ${_known_cost(results):.6f}; unknown-cost attempts {_unknown_attempts(results)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
