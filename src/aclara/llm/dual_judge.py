"""Subjective-only Sonnet/Jev pair for the gated final judge step."""

from __future__ import annotations

import csv
import logging
import math
import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

from typesafe_sdk import RetryPolicy, TypeSafeClient

from aclara.agent.nlg.grounding import redact_for_model
from aclara.llm.client import StructuredClient
from aclara.llm.final_run import require_start
from aclara.llm.judge import FULL_CSV, JEV_FULL_CSV, _score
from aclara.llm.judge_validation import DIMENSIONS, SHEET, _rating, quadratic_weighted_kappa
from aclara.llm.prompts import Prompt
from aclara.llm.types import CallRecord
from aclara.llm.typesafe import MODEL_ID as JEV_MODEL_ID
from aclara.llm.typesafe import TypedJudgments, TypeSafeAdapter
from aclara.llm.typesafe_questions import QUESTION_SOURCE_HASH, QUESTION_VERSION, judge_questions

LOGGER = logging.getLogger(__name__)
JEV_JUDGE_RESERVE_USD = 0.01


@contextmanager
def jev_judge_adapter() -> Iterator[TypeSafeAdapter]:
    """Open the pinned no-retry second judge only after the final start signal."""
    require_start()
    key = os.getenv("TYPESAFE_API_KEY")
    if not key:
        raise RuntimeError("The TypeSafe key is unavailable to the final judge")
    with TypeSafeClient(
        api_key=key,
        model=JEV_MODEL_ID,
        retry=RetryPolicy(max_retries=0),
        timeout=20.0,
    ) as raw:
        yield TypeSafeAdapter(raw)


def _jev_scores(result: TypedJudgments, *, has_handoff: bool) -> dict[str, int | None]:
    expected = set(DIMENSIONS) if has_handoff else set(DIMENSIONS) - {"handoff_usefulness"}
    if set(result.scores) != expected:
        raise ValueError("Jev did not return every applicable rubric dimension")
    scores: dict[str, int | None] = {
        name: min(5, max(1, 1 + math.floor(value.score + 0.5)))
        for name, value in result.scores.items()
    }
    if not has_handoff:
        scores["handoff_usefulness"] = None
    return scores


def score_pair(
    row: dict[str, str],
    *,
    sonnet_client: StructuredClient,
    jev_adapter: TypeSafeAdapter,
    prompt: Prompt,
) -> dict[str, Any]:
    """Score one blinded reply with both judges; caller persists usage under its $12 gate."""
    require_start()
    if row.get("system_id") == "sonnet":
        raise ValueError("Do not self-judge a Sonnet system reply with Sonnet")
    first = len(sonnet_client.records)
    sonnet = _score(sonnet_client, row, prompt)
    sonnet_attempts = sonnet_client.records[first:]
    if not sonnet_attempts:
        raise RuntimeError("Sonnet judge made no recorded attempt")
    handoff = row["handoff_summary"].strip() or None
    state = {
        "target_locale": row["target_locale"],
        "customer_message": redact_for_model(row["customer_message"]),
        "customer_reply": redact_for_model(row["customer_reply"]),
        "handoff_summary": redact_for_model(handoff) if handoff else None,
    }
    jev_result: TypedJudgments | None = None
    jev_scores: dict[str, int | None] | None = None
    degradation: str | None = None
    reservation = sonnet_client.reserve_external_judgment(
        JEV_JUDGE_RESERVE_USD, primary_floor_usd=0.0
    )
    started = perf_counter()
    try:
        jev_result = jev_adapter.ask(state, judge_questions(has_handoff=handoff is not None))
        jev_scores = _jev_scores(jev_result, has_handoff=handoff is not None)
    except Exception as exc:
        degradation = type(exc).__name__
        LOGGER.warning("Jev subjective judge degraded: %s", degradation)
    jev_record = CallRecord(
        route="subjective_judge_second_opinion",
        provider="typesafe",
        model_id=JEV_MODEL_ID,
        prompt_id=QUESTION_VERSION,
        prompt_hash=QUESTION_SOURCE_HASH,
        input_tokens=(jev_result.input_tokens or 0) if jev_result else 0,
        output_tokens=(jev_result.output_tokens or 0) if jev_result else 0,
        cache_read_tokens=0,
        cache_write_tokens=0,
        latency_ms=jev_result.latency_ms if jev_result else (perf_counter() - started) * 1000,
        cost_usd=jev_result.cost_usd if jev_result else None,
        stop_reason=None,
        status="valid" if jev_scores is not None else "provider_error",
        attempt=1,
        judgments={
            "scores": jev_scores,
            "raw_scores": {
                name: {"zero_based_expected": value.score, "probabilities": value.probabilities}
                for name, value in jev_result.scores.items()
            }
            if jev_result
            else None,
            "degradation": degradation,
            "subjective_only": True,
        },
    )
    sonnet_client.finish_external_judgment(
        jev_record, reserve_usd=JEV_JUDGE_RESERVE_USD, reservation=reservation
    )
    return {
        "sonnet_scores": sonnet.model_dump(),
        "jev_scores": jev_scores,
        "jev_raw_scores": jev_record.judgments["raw_scores"] if jev_record.judgments else None,
        "sonnet_attempts": [
            {
                "model_id": attempt.model_id,
                "cost_usd": attempt.cost_usd,
                "latency_ms": attempt.latency_ms,
                "status": attempt.status,
            }
            for attempt in sonnet_attempts
        ],
        "jev_attempt": {
            "model_id": jev_record.model_id,
            "cost_usd": jev_record.cost_usd,
            "latency_ms": jev_record.latency_ms,
            "status": jev_record.status,
            "degradation": degradation,
        },
    }


def _agreement(
    left: Mapping[str, Mapping[str, int | None]],
    right: Mapping[str, Mapping[str, int | None]],
) -> dict[str, Any]:
    if set(left) != set(right):
        raise ValueError("Judge sample IDs differ")
    dimensions: dict[str, Any] = {}
    for name in DIMENSIONS:
        pairs = [
            (a, b)
            for sample_id in sorted(left)
            if (a := left[sample_id][name]) is not None
            and (b := right[sample_id][name]) is not None
        ]
        dimensions[name] = {
            "paired_n": len(pairs),
            "exact_agreement": sum(a == b for a, b in pairs) / len(pairs) if pairs else None,
            "within_one": sum(abs(a - b) <= 1 for a, b in pairs) / len(pairs) if pairs else None,
            "quadratic_weighted_kappa": quadratic_weighted_kappa(pairs),
        }
    return dimensions


def agreement_report(
    sonnet: Mapping[str, Mapping[str, int | None]],
    jev: Mapping[str, Mapping[str, int | None]],
    *,
    human: Mapping[str, Mapping[str, int | None]] | None = None,
    require_human_n: int = 50,
) -> dict[str, Any]:
    """Report judge-to-judge and, after human completion, each judge-to-human agreement."""
    out: dict[str, Any] = {"jev_vs_sonnet": _agreement(sonnet, jev)}
    if human is not None:
        if len(human) != require_human_n or set(human) != set(sonnet):
            raise ValueError("Complete paired human sample is required for agreement claims")
        sonnet_human = _agreement(sonnet, human)
        jev_human = _agreement(jev, human)
        for name in DIMENSIONS:
            expected = sum(row[name] is not None for row in sonnet.values())
            if (
                sonnet_human[name]["paired_n"] != expected
                or jev_human[name]["paired_n"] != expected
            ):
                raise ValueError("Complete paired human ratings are required for agreement claims")
        out["sonnet_vs_human"] = sonnet_human
        out["jev_vs_human"] = jev_human
    return out


def calibration_agreement(
    *,
    human_path: Path = SHEET,
    sonnet_path: Path = FULL_CSV,
    jev_path: Path = JEV_FULL_CSV,
) -> dict[str, Any]:
    """Read the ignored 50-row sheets; refuse judge-to-human claims until fully paired."""

    def read(path: Path, *, human: bool) -> dict[str, dict[str, int | None]]:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != 50 or len({row["sample_id"] for row in rows}) != 50:
            raise ValueError("Judge calibration needs 50 unique paired sample IDs")
        return {
            row["sample_id"]: {
                name: _rating(row[("human_" if human else "") + name]) for name in DIMENSIONS
            }
            for row in rows
        }

    return agreement_report(
        read(sonnet_path, human=False),
        read(jev_path, human=False),
        human=read(human_path, human=True),
    )
