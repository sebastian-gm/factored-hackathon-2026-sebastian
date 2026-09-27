"""Aggregate-only replay of the risk union on saved paired dev calls."""

from __future__ import annotations

import json
from statistics import median
from typing import Any

from aclara.llm.typesafe_eval import CHECKPOINTS
from aclara.llm.typesafe_questions import RISK_CUES


def _percentile(values: list[float], proportion: float) -> float:
    ordered = sorted(values)
    point = (len(ordered) - 1) * proportion
    low = int(point)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (point - low)


def union_report() -> dict[str, Any]:
    baseline = json.loads(CHECKPOINTS["baseline"].read_text(encoding="utf-8"))
    jev = json.loads(CHECKPOINTS["jev"].read_text(encoding="utf-8"))
    if baseline["suite_sha256"] != jev["suite_sha256"]:
        raise RuntimeError("Paired risk replay requires the same dev-suite hash")
    gemini_rows = baseline["observations"]
    jev_rows = {row["case_id"]: row for row in jev["observations"]}
    if (
        len(gemini_rows) != 150
        or len(jev_rows) != 150
        or {row["case_id"] for row in gemini_rows} != set(jev_rows)
    ):
        raise RuntimeError("Paired risk replay requires all 150 unique cases")
    flags = {name: {"gemini": 0, "jev": 0, "union": 0} for name in RISK_CUES}
    injection_tp = injection_fp = 0
    paired_max_ms: list[float] = []
    for row in gemini_rows:
        other = jev_rows[row["case_id"]]
        for cue in RISK_CUES:
            gemini_flag = bool(row["risk_flags"][cue])
            jev_flag = float(other["risk_probabilities"][cue]) >= 0.5
            union_flag = gemini_flag or jev_flag
            flags[cue]["gemini"] += gemini_flag
            flags[cue]["jev"] += jev_flag
            flags[cue]["union"] += union_flag
            if cue == "injection_suspected":
                injection_tp += bool(row["gold_injection"] and union_flag)
                injection_fp += bool(not row["gold_injection"] and union_flag)
        paired_max_ms.append(
            max(
                sum(float(attempt["latency_ms"]) for attempt in row["attempts"]),
                sum(float(attempt["latency_ms"]) for attempt in other["attempts"]),
            )
        )
    return {
        "n": 150,
        "injection_gold": sum(row["gold_injection"] for row in gemini_rows),
        "injection_union_tp": injection_tp,
        "injection_union_fp": injection_fp,
        "risk_flag_counts": flags,
        "paired_parallel_latency_proxy_p50_ms": median(paired_max_ms),
        "paired_parallel_latency_proxy_p95_ms": _percentile(paired_max_ms, 0.95),
        "latency_is_replay_proxy_not_live_parallel_measurement": True,
    }
