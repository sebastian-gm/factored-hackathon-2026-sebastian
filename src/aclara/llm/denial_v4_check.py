"""Paired v3/v4 synthetic denial check; no held-out or human spot-check inputs."""

from __future__ import annotations

import argparse
import json
import logging
import os
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.llm.client import StructuredClient
from aclara.llm.prompts import data_block, load_prompt
from aclara.llm.round_one import ROOT, _catalog, _local_key
from aclara.llm.types import ModelFailure

MODEL_ID = "google/gemini-3-flash-preview"
PROVIDER_ONLY = ("google-vertex/global",)
SUITE = ROOT / "src/aclara/llm/dev_denial_v4.yaml"
OUTPUT = ROOT / "artifacts/ai-denial-v4/check.json"
CHALLENGE_SUITE = ROOT / "src/aclara/llm/dev_denial_v4_challenge.yaml"
CHALLENGE_OUTPUT = ROOT / "artifacts/ai-denial-v4/challenge.json"
PROMPTS = (ROOT / "prompts/nlu/v3.md", ROOT / "prompts/nlu/v4.md")
CAP_USD = 0.49
UNKNOWN_RESERVE_USD = 0.025
NEXT_CALL_GUARD_USD = 0.05
LOGGER = logging.getLogger(__name__)


def load_cases(*, challenge: bool = False) -> tuple[list[dict[str, str]], str]:
    raw = (CHALLENGE_SUITE if challenge else SUITE).read_bytes()
    payload = yaml.safe_load(raw)
    if payload.get("version") != 1 or payload.get("source") != "team_authored_unreviewed":
        raise ValueError("Unexpected synthetic denial dev suite")
    rows = payload["cases"]
    per_group = 8 if challenge else 12
    if len(rows) != 2 * per_group or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Denial dev suite size or uniqueness mismatch")
    if Counter(row["group"] for row in rows) != {"denial": per_group, "inquiry": per_group}:
        raise ValueError("Denial and inquiry cases must be balanced")
    if len({row["message"] for row in rows}) != len(rows):
        raise ValueError("Duplicate development utterance")
    for row in rows:
        if row["gold_intent"] != (
            "dispute_charge" if row["group"] == "denial" else "charge_inquiry"
        ):
            raise ValueError("Synthetic case group and intent disagree")
    return rows, sha256(raw).hexdigest()


def _private_write(value: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    pending = output.with_suffix(".tmp")
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    pending.replace(output)


def _exposure(observations: list[dict[str, Any]]) -> tuple[float, int]:
    attempts = [attempt for row in observations for attempt in row["attempts"]]
    known = sum(float(a["cost_usd"]) for a in attempts if a["cost_usd"] is not None)
    unknown = sum(a["cost_usd"] is None for a in attempts)
    return known, unknown


def summary(data: dict[str, Any], prior: dict[str, Any] | None = None) -> dict[str, Any]:
    observations = data["observations"]
    known, unknown = _exposure(observations)
    by_prompt: dict[str, Any] = {}
    for version in ("v3", "v4"):
        selected = [row for row in observations if row["prompt_version"] == version]
        confusion = Counter((row["gold_intent"], row["predicted_intent"]) for row in selected)
        by_prompt[version] = {
            "completed": len(selected),
            "correct": sum(row["gold_intent"] == row["predicted_intent"] for row in selected),
            "denials_correct": sum(
                row["gold_intent"] == "dispute_charge"
                and row["predicted_intent"] == "dispute_charge"
                for row in selected
            ),
            "inquiries_correct": sum(
                row["gold_intent"] == "charge_inquiry"
                and row["predicted_intent"] == "charge_inquiry"
                for row in selected
            ),
            "no_valid_final": sum(row["predicted_intent"] is None for row in selected),
            "confusion": {f"{gold}->{pred}": n for (gold, pred), n in sorted(confusion.items())},
        }
    all_attempts = [a for row in observations for a in row["attempts"]]
    prior_known, prior_unknown = _exposure(prior["observations"]) if prior else (0.0, 0)
    return {
        "planned": 2 * int(data.get("case_count", 24)),
        "observed": len(observations),
        "model_id": data["model_id"],
        "provider_only": data["provider_only"],
        "by_prompt": by_prompt,
        "all_attempts": len(all_attempts),
        "valid_json_attempts": sum(a["status"] == "valid" for a in all_attempts),
        "known_per_call_cost_usd": round(known, 9),
        "unknown_cost_attempts": unknown,
        "guarded_exposure_usd": round(known + unknown * UNKNOWN_RESERVE_USD, 9),
        "cumulative_guarded_exposure_usd": round(
            known + prior_known + (unknown + prior_unknown) * UNKNOWN_RESERVE_USD, 9
        ),
        "cap_usd": CAP_USD,
    }


def run(*, challenge: bool = False) -> dict[str, Any]:
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1" or os.getenv("NLU_DENIAL_V4_APPROVED") != "1":
        raise RuntimeError("This paid dev check needs process-local owner approval flags")
    cases, suite_hash = load_cases(challenge=challenge)
    output = CHALLENGE_OUTPUT if challenge else OUTPUT
    prior: dict[str, Any] | None = (
        json.loads(OUTPUT.read_text(encoding="utf-8")) if challenge and OUTPUT.exists() else None
    )
    if challenge and (prior is None or len(prior["observations"]) != 48):
        raise RuntimeError("The complete first paired check is required before challenge calls")
    prior_known, prior_unknown = _exposure(prior["observations"]) if prior else (0.0, 0)
    prompts = {path.stem: load_prompt(path) for path in PROMPTS}
    prompt_hashes = {name: prompt.content_hash for name, prompt in prompts.items()}
    if prior is not None and prior["prompt_hashes"] != prompt_hashes:
        raise RuntimeError("First paired check used different prompt bytes")
    data: dict[str, Any] = (
        json.loads(output.read_text(encoding="utf-8"))
        if output.exists()
        else {
            "suite_sha256": suite_hash,
            "prompt_hashes": prompt_hashes,
            "model_id": MODEL_ID,
            "provider_only": list(PROVIDER_ONLY),
            "cap_usd": CAP_USD,
            "case_count": len(cases),
            "observations": [],
        }
    )
    if (
        data["suite_sha256"] != suite_hash
        or data["prompt_hashes"] != prompt_hashes
        or data["model_id"] != MODEL_ID
        or data["provider_only"] != list(PROVIDER_ONLY)
        or data["cap_usd"] != CAP_USD
        or int(data.get("case_count", 24)) != len(cases)
    ):
        raise RuntimeError("Paired dev-check inputs changed after checkpoint creation")
    observations = cast(list[dict[str, Any]], data["observations"])
    known, unknown = _exposure(observations)
    remaining = CAP_USD - prior_known - known - UNKNOWN_RESERVE_USD * (prior_unknown + unknown)
    if remaining < NEXT_CALL_GUARD_USD and len(observations) < 2 * len(cases):
        raise RuntimeError("Dev-check hard cap cannot reserve another logical call")
    models, prices = _catalog((MODEL_ID,))
    spec = replace(
        models[MODEL_ID], provider_only=PROVIDER_ONLY, max_output_tokens=2048, timeout_seconds=30
    )
    os.environ["OPENROUTER_API_KEY"] = _local_key()
    client = StructuredClient(
        {MODEL_ID: spec},
        {MODEL_ID: prices[MODEL_ID]},
        budget_usd=remaining,
        daily_budget_usd=remaining,
    )
    done = {(row["case_id"], row["prompt_version"]) for row in observations}
    for case in cases:
        for version, prompt in prompts.items():
            if (case["id"], version) in done:
                continue
            known, unknown = _exposure(observations)
            if (
                prior_known
                + known
                + (prior_unknown + unknown) * UNKNOWN_RESERVE_USD
                + NEXT_CALL_GUARD_USD
                > CAP_USD
            ):
                raise RuntimeError("Dev-check hard cap cannot reserve another logical call")
            first = len(client.records)
            predicted: str | None = None
            try:
                extracted = client.generate(
                    MODEL_ID,
                    prompt.text,
                    data_block("customer_message", redact_for_model(case["message"])),
                    ExtractedNlu,
                    prompt_id=f"{prompt.id}@{prompt.version}",
                    prompt_hash=prompt.content_hash,
                )
                predicted = extracted.intent
            except ModelFailure:
                pass
            attempts = [
                {
                    "status": record.status,
                    "model_id": record.model_id,
                    "cost_usd": record.cost_usd,
                    "input_tokens": record.input_tokens,
                    "output_tokens": record.output_tokens,
                    "latency_ms": record.latency_ms,
                }
                for record in client.records[first:]
            ]
            if not attempts:
                raise RuntimeError("No model attempt was recorded; preserve checkpoint")
            observations.append(
                {
                    "case_id": case["id"],
                    "group": case["group"],
                    "gold_intent": case["gold_intent"],
                    "prompt_version": version,
                    "predicted_intent": predicted,
                    "attempts": attempts,
                }
            )
            _private_write(data, output)
    return summary(data, prior)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", action="store_true", help="Use the separately approved sub-$0.50 dev cap"
    )
    parser.add_argument("--challenge", action="store_true", help="Use the contrastive second suite")
    args = parser.parse_args()
    if not args.run:
        cases, suite_hash = load_cases(challenge=args.challenge)
        LOGGER.info(
            "Synthetic dev cases: %d; paired calls: %d; suite SHA-256: %s",
            len(cases),
            len(cases) * 2,
            suite_hash,
        )
        LOGGER.info("No paid call made. Hard cap if run: $%.2f", CAP_USD)
        return 0
    LOGGER.info("%s", json.dumps(run(challenge=args.challenge), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
