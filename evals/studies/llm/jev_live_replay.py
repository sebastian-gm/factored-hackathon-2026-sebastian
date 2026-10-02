"""Aggregate saved risk-union metadata; no inference, suite access or rescoring."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from aclara.agent.conversation import risk_reasons
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.llm.typesafe_questions import RISK_CUES


def _flags(value: object) -> dict[str, bool]:
    if (
        not isinstance(value, dict)
        or set(value) != set(RISK_CUES)
        or any(type(v) is not bool for v in value.values())
    ):
        raise ValueError("Complete boolean primary and union flags required")
    return cast(dict[str, bool], value)


def replay(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    affected: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    paired = reason_changes = primary_passes = 0
    known_jev_cost = 0.0
    for row in rows:
        if row.get("system") != "P":
            continue
        identity = (row["id"], row["repeat"])
        if identity in seen:
            raise ValueError("Duplicate saved execution; do not count attempt and result twice")
        seen.add(identity)
        primary_passes += row["repeat"] == 0 and row["passed"]
        for call in row["events"]:
            if call.get("event") != "llm_call":
                continue
            counts[call["route"]] += 1
            if call["route"] != "nlu_risk_second_opinion":
                continue
            if call.get("cost_usd") is not None:
                known_jev_cost += call["cost_usd"]
            judgments = call.get("judgments") or {}
            raw = _flags(judgments.get("primary_raw_flags", judgments.get("gemini_raw_flags")))
            union = _flags(judgments.get("union_flags"))
            paired += 1
            changed = [cue for cue in RISK_CUES if raw[cue] != union[cue]]
            # Replay only the code's cue-to-reason map. Intent and all other
            # evidence stay identical; neither objective gold nor scores change.
            before = risk_reasons(
                ExtractedNlu.model_validate(
                    {"language": "es", "intent": "charge_inquiry", "intent_confidence": 1, **raw}
                )
            )
            after = risk_reasons(
                ExtractedNlu.model_validate(
                    {"language": "es", "intent": "charge_inquiry", "intent_confidence": 1, **union}
                )
            )
            reason_changes += before != after
            if changed:
                affected.append(
                    {
                        "case_id": row["id"],
                        "repeat": row["repeat"],
                        "changed_cues": changed,
                        "observed_outcome": row["outcome"],
                        "observed_passed": row["passed"],
                        "saved_route_language_correct": row.get("route_checks", {}).get("language"),
                    }
                )
    return {
        "p_executions": len(seen),
        "primary_executions": sum(repeat == 0 for _, repeat in seen),
        "observed_primary_passes": primary_passes,
        "call_counts": dict(sorted(counts.items())),
        "all_p_calls": sum(counts.values()),
        "nlu_and_risk_calls": counts["nlu"] + counts["nlu_risk_second_opinion"],
        "paired_risk_records": paired,
        "changed_union_records": len(affected),
        "calls_in_changed_pairs": 2 * len(affected),
        "changed_routing_reason_lists": reason_changes,
        "affected_metadata": sorted(affected, key=lambda r: (r["case_id"], r["repeat"])),
        "known_jev_risk_cost_usd": round(known_jev_cost, 12),
        "boundary": "saved flags and cue-to-reason map only; no suite rerun or rescore",
    }


def saved_report(checkpoints: Path) -> dict[str, Any]:
    rows = []
    hashes = []
    for path in sorted(checkpoints.glob("*/result.json")):
        raw = path.read_bytes()
        row = json.loads(raw)
        if row.get("system") == "P":
            rows.append(row)
            hashes.append(sha256(raw).hexdigest())
    if not rows:
        raise ValueError("No saved P execution results; never substitute a fresh run")
    report = replay(rows)
    report["saved_p_results_digest"] = sha256("\n".join(sorted(hashes)).encode()).hexdigest()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoints", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(saved_report(args.checkpoints), indent=2, sort_keys=True))  # noqa: T201


if __name__ == "__main__":
    main()
