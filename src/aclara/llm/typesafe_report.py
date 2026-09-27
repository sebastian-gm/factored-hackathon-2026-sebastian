"""Aggregate-only Gemini-v4/Jev NLU and three-item subjective judge report."""

from __future__ import annotations

import json
from collections import Counter
from statistics import median
from typing import Any, cast

from aclara.llm.judge import SMOKE_OUTPUT
from aclara.llm.judge_validation import DIMENSIONS, quadratic_weighted_kappa
from aclara.llm.typesafe_eval import CHECKPOINTS, exposure
from aclara.llm.typesafe_questions import RISK_CUES


def expected_calibration_error(pairs: list[tuple[float, bool]], *, bins: int = 10) -> float | None:
    """Fixed-width ECE on valid finals; confidence is not a correctness guarantee."""
    if not pairs:
        return None
    if bins < 2:
        raise ValueError("ECE requires at least two bins")
    total = 0.0
    for index in range(bins):
        bucket = [
            (confidence, correct)
            for confidence, correct in pairs
            if min(bins - 1, int(confidence * bins)) == index
        ]
        if bucket:
            accuracy = sum(correct for _, correct in bucket) / len(bucket)
            confidence = sum(value for value, _ in bucket) / len(bucket)
            total += len(bucket) / len(pairs) * abs(accuracy - confidence)
    return total


def _percentile(values: list[float], proportion: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    point = (len(ordered) - 1) * proportion
    low = int(point)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (point - low)


def _flag(row: dict[str, Any], cue: str, *, jev: bool) -> bool:
    if row["predicted_intent"] is None:
        return False
    if jev:
        return float(row["risk_probabilities"][cue]) >= 0.5
    return bool(row["risk_flags"][cue])


def _nlu_slice(rows: list[dict[str, Any]], *, jev: bool) -> dict[str, Any]:
    finals = [row for row in rows if row["predicted_intent"] is not None]
    attempts = [attempt for row in rows for attempt in row["attempts"]]
    injection_tp = sum(
        row["gold_injection"] and _flag(row, "injection_suspected", jev=jev) for row in rows
    )
    injection_fp = sum(
        not row["gold_injection"] and _flag(row, "injection_suspected", jev=jev) for row in rows
    )
    calibration = [
        (float(row["intent_probability"]), row["predicted_intent"] == row["gold_intent"])
        for row in finals
        if row["intent_probability"] is not None
    ]
    return {
        "n": len(rows),
        "valid_finals": len(finals),
        "intent_correct": sum(row["predicted_intent"] == row["gold_intent"] for row in rows),
        "intent_accuracy": sum(row["predicted_intent"] == row["gold_intent"] for row in rows)
        / len(rows)
        if rows
        else None,
        "ece_10_bin_valid_finals": expected_calibration_error(calibration),
        "calibration_n": len(calibration),
        "injection_gold": sum(row["gold_injection"] for row in rows),
        "injection_tp": injection_tp,
        "injection_fn": sum(row["gold_injection"] for row in rows) - injection_tp,
        "injection_fp": injection_fp,
        "injection_tn": sum(not row["gold_injection"] for row in rows) - injection_fp,
        "risk_flag_counts": {
            cue: sum(_flag(row, cue, jev=jev) for row in rows) for cue in RISK_CUES
        },
        "p50_case_latency_ms": median(
            [sum(float(a["latency_ms"]) for a in row["attempts"]) for row in rows]
        )
        if rows
        else None,
        "p95_case_latency_ms": _percentile(
            [sum(float(a["latency_ms"]) for a in row["attempts"]) for row in rows], 0.95
        ),
        "known_cost_usd": sum(float(a["cost_usd"]) for a in attempts if a["cost_usd"] is not None),
        "unknown_cost_attempts": sum(a["cost_usd"] is None for a in attempts),
        "all_attempts": len(attempts),
        "valid_attempts": sum(a["status"] == "valid" for a in attempts),
    }


def _judge_report(jev_rows: list[dict[str, Any]]) -> dict[str, Any]:
    sonnet = json.loads(SMOKE_OUTPUT.read_text(encoding="utf-8"))["results"]
    left = {row["sample_id"]: row for row in sonnet}
    right = {row["sample_id"]: row for row in jev_rows}
    if len(left) != 3 or len(right) != 3 or set(left) != set(right):
        raise RuntimeError("Judge smoke samples are not paired")
    dimensions: dict[str, Any] = {}
    for name in DIMENSIONS:
        pairs = [
            (left[sample_id]["scores"][name], right[sample_id]["scores"][name])
            for sample_id in sorted(left)
            if left[sample_id]["scores"][name] is not None
            and right[sample_id]["scores"][name] is not None
        ]
        dimensions[name] = {
            "paired_n": len(pairs),
            "exact_agreement": sum(a == b for a, b in pairs) / len(pairs) if pairs else None,
            "within_one": sum(abs(a - b) <= 1 for a, b in pairs) / len(pairs) if pairs else None,
            "quadratic_weighted_kappa": quadratic_weighted_kappa(pairs),
        }
    sonnet_cost = sum(float(a["cost_usd"] or 0) for row in sonnet for a in row["attempts"])
    jev_attempts = [a for row in jev_rows for a in row["attempts"]]
    return {
        "n": 3,
        "dimensions": dimensions,
        "sonnet_known_per_call_cost_usd_prior_smoke": sonnet_cost,
        "jev_known_usage_cost_usd": sum(
            float(a["cost_usd"]) for a in jev_attempts if a["cost_usd"] is not None
        ),
        "jev_unknown_cost_attempts": sum(a["cost_usd"] is None for a in jev_attempts),
        "jev_p50_latency_ms": median(float(a["latency_ms"]) for a in jev_attempts),
    }


def report() -> dict[str, Any]:
    checkpoints = {
        stage: cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        for stage, path in CHECKPOINTS.items()
    }
    baseline = checkpoints["baseline"]["observations"]
    jev = checkpoints["jev"]["observations"]
    judge = checkpoints["judge"]["observations"]
    if len(baseline) != 150 or len(jev) != 150 or len(judge) != 3:
        raise RuntimeError("Jev report requires the complete 150/150/3 synthetic comparison")
    if len({row["case_id"] for row in baseline}) != 150 or {row["case_id"] for row in baseline} != {
        row["case_id"] for row in jev
    }:
        raise RuntimeError("Gemini/Jev dev case IDs do not align")
    if checkpoints["baseline"]["suite_sha256"] != checkpoints["jev"]["suite_sha256"]:
        raise RuntimeError("Gemini/Jev dev suite hashes do not align")
    known, unknown, guarded = exposure()
    out: dict[str, Any] = {
        "suite_cases": 150,
        "suite_reviewed": False,
        "gemini_model_id": "google/gemini-3-flash-preview",
        "jev_model_id": "jev-1.13.0",
        "question_version": checkpoints["jev"]["question_version"],
        "threshold_for_noul_flags": 0.5,
        "ece_bins": 10,
        "models": {},
        "judge": _judge_report(judge),
        "new_known_per_call_cost_usd": known,
        "new_unknown_cost_attempts": unknown,
        "new_guarded_exposure_usd": guarded,
        "new_approved_cap_usd": 1.0,
    }
    for name, rows, is_jev in (("gemini_v4", baseline, False), ("jev", jev, True)):
        out["models"][name] = {
            language: _nlu_slice(
                rows if language == "all" else [r for r in rows if r["language"] == language],
                jev=is_jev,
            )
            for language in ("all", "es", "pt", "mixed")
        }
        out["models"][name]["served_models"] = dict(
            Counter(a["served_model_id"] for row in rows for a in row["attempts"])
        )
    return out
