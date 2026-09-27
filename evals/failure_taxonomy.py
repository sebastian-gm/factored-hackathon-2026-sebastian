"""Reduce saved scored observations to counts; never read prompts or invoke a system."""

# ruff: noqa: T201 -- aggregate counts only.
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from evals.access import ROOT, access


def present(packet: dict, path: str) -> bool:
    value: Any = packet
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value is not None


def reduce_cases(cases: list[dict]) -> dict:
    failures: dict[str, list[dict]] = {
        "forbidden_write": [c for c in cases if c["unsafe"]["unauthorized_action"]],
        "failed_workload": [c for c in cases if not c["passed"]],
        "missing_handoff": [c for c in cases if c["gold"]["must_escalate"] and not c["handoff"]],
        "incomplete_handoff": [
            c
            for c in cases
            if c["handoff"] and c["gold"]["required_handoff_fields"] and c["completeness"] != 1
        ],
        "outcome_mismatch": [c for c in cases if c["outcome"] != c["gold"]["outcome"]],
        "missing_action": [c for c in cases if c["missing_actions"]],
        "route_mismatch": [c for c in cases if c["routing_correct"] is False],
    }

    def counts(rows: list[dict], field: str) -> dict:
        return dict(sorted(Counter(c[field] for c in rows).items()))

    result = {}
    for name, rows in failures.items():
        result[name] = {
            "n": len(rows),
            **{field: counts(rows, field) for field in ("category", "language", "outcome")},
            "rule_id": dict(
                sorted(Counter(r for c in rows for r in c["gold"]["reason_codes"]).items())
            ),
            "gold_outcome": dict(sorted(Counter(c["gold"]["outcome"] for c in rows).items())),
        }
    result["missing_packet_fields"] = dict(
        sorted(
            Counter(
                key
                for c in cases
                if c["handoff"]
                for key in c["gold"]["required_handoff_fields"]
                if not present(c.get("observed_handoff") or {}, key)
            ).items()
        )
    )
    result["missing_action_types"] = dict(
        sorted(Counter(a["type"] for c in cases for a in c["missing_actions"]).items())
    )
    result["forbidden_write_plan_sequences"] = dict(
        sorted(
            Counter(
                ">".join(r["response_type"] for r in c["responses"])
                for c in failures["forbidden_write"]
            ).items()
        )
    )
    # Structural contradictions can be flagged without inspecting an utterance or
    # a transaction. They are review candidates, never corrected gold labels.
    result["suspected_gold_contract_conflicts"] = dict(
        sorted(
            Counter(
                r
                for c in cases
                for r in c["gold"]["reason_codes"]
                if {a["type"] for a in c["gold"]["required_actions"]}
                & set(c["gold"]["forbidden_actions"])
            ).items()
        )
    )
    return result


def main() -> None:
    source = ROOT / "artifacts/heldout/run-01-measurement-v2/cases.jsonl"
    with access(
        "aggregate_failure_taxonomy",
        [source],
        "Handoff 08 aggregate-only diagnosis; no frozen-suite execution",
    ):
        cases = [json.loads(line) for line in source.read_text().splitlines()]
        report = {
            "source": "run-01 measurement-v2; saved observations only",
            "system_calls": 0,
            "counts_overlap": True,
            "systems": {
                system: reduce_cases(
                    [c for c in cases if c["system"] == system and c["repeat"] == 0]
                )
                for system in ("B1", "P")
            },
        }
    output = Path("docs/evaluation/run01-failure-taxonomy.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
