"""Small metadata-only DeepSeek provider-speed probe for round three."""

from __future__ import annotations

import logging
import os
from dataclasses import replace
from statistics import median
from typing import Any

from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.llm.client import StructuredClient
from aclara.llm.prompts import data_block, load_prompt
from aclara.llm.types import ModelFailure
from evals.studies.llm.round_one import _catalog, _local_key
from evals.studies.llm.round_three import (
    ARTIFACTS,
    CAP_USD,
    PROMPT,
    _write,
    cumulative_cost,
    load_cases,
)

MODEL_ID = "deepseek/deepseek-v4-flash-0731"
PROVIDERS = ("wafer/fast", "deepinfra/fp8", "open-inference/fp8")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if (ARTIFACTS / "provider-probes.json").exists():
        raise RuntimeError("Provider probe checkpoint already exists; do not overwrite paid usage")
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Process-local owner approval gate is required")
    os.environ["OPENROUTER_API_KEY"] = _local_key()
    cases, _, suite_hash = load_cases()
    prompt = load_prompt(PROMPT)
    models, prices = _catalog((MODEL_ID,))
    data: dict[str, Any] = {
        "suite_sha256": suite_hash,
        "prompt_hash": prompt.content_hash,
        "model_id": MODEL_ID,
        "reasoning_effort": "none",
        "observations": [],
    }
    observations: list[dict[str, Any]] = []
    for provider in PROVIDERS:
        spec = replace(
            models[MODEL_ID],
            provider_only=(provider,),
            reasoning_effort="none",
            max_output_tokens=2048,
            timeout_seconds=45,
        )
        client = StructuredClient({MODEL_ID: spec}, {MODEL_ID: prices[MODEL_ID]}, budget_usd=0.03)
        for case in cases[:3]:
            if cumulative_cost() >= CAP_USD - 0.35:
                raise RuntimeError("Approved cumulative cap guard reached")
            first = len(client.records)
            valid = True
            try:
                client.generate(
                    MODEL_ID,
                    prompt.text,
                    data_block("customer_message", redact_for_model(case.message)),
                    ExtractedNlu,
                    prompt_id=f"{prompt.id}@{prompt.version}",
                    prompt_hash=prompt.content_hash,
                )
            except ModelFailure:
                valid = False
            attempts = [
                {
                    "status": record.status,
                    "latency_ms": record.latency_ms,
                    "cost_usd": record.cost_usd,
                    "generation_id": record.generation_id,
                }
                for record in client.records[first:]
            ]
            observations.append(
                {
                    "provider": provider,
                    "case_id": case.case_id,
                    "valid": valid,
                    "attempts": attempts,
                }
            )
            data["observations"] = observations
            _write(ARTIFACTS / "provider-probes.json", data)
        times = [
            sum(float(a["latency_ms"]) for a in o["attempts"]) / 1000
            for o in observations
            if o["provider"] == provider
        ]
        logging.info(
            "%s: %d/3 valid, median %.2fs",
            provider,
            sum(bool(o["valid"]) for o in observations if o["provider"] == provider),
            median(times),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
