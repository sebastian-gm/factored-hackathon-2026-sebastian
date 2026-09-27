"""Allowlisted glass-box metadata: no prompt, output, identity or model thinking."""

from __future__ import annotations

import math
import re
from typing import Any

RISK_KEYS = frozenset(
    {"lost_stolen", "regulator", "legal", "distress", "injection_suspected", "human_requested"}
)
FLAG_MAPS = frozenset({"gemini_raw_flags", "jev_threshold_flags", "union_flags"})
PROBABILITY_MAPS = frozenset({"gemini_raw_probabilities", "jev_raw_probabilities"})


def judgments_projection(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    result: dict[str, Any] = {}
    for key in FLAG_MAPS | PROBABILITY_MAPS:
        value = raw.get(key)
        if value is None and key in raw:
            result[key] = None
        elif isinstance(value, dict):
            result[key] = {
                cue: probability
                for cue, probability in value.items()
                if cue in RISK_KEYS
                and (
                    probability is None
                    or (key in FLAG_MAPS and isinstance(probability, bool))
                    or (
                        key in PROBABILITY_MAPS
                        and type(probability) in {int, float}
                        and math.isfinite(probability)
                        and 0 <= probability <= 1
                    )
                )
            }
    threshold = raw.get("threshold")
    if (
        isinstance(threshold, (int, float))
        and not isinstance(threshold, bool)
        and math.isfinite(threshold)
        and 0 <= threshold <= 1
    ):
        result["threshold"] = threshold
    if isinstance(raw.get("primary_failed"), bool):
        result["primary_failed"] = raw["primary_failed"]
    degradation = raw.get("degradation")
    if (
        degradation is None
        or isinstance(degradation, str)
        and re.fullmatch(r"[A-Za-z_]{1,80}", degradation)
    ):
        result["degradation"] = degradation
    return result or None
