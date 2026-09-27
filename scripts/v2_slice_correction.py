"""Offline reporting correction over saved v2 observations; never executes a case."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from evals.access import access
from evals.heldout_report import correct_handoff
from evals.metrics import proportion

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/final-program-v2"
OUTPUT = ROOT / "artifacts/final-program-v2-corrections"
DIMENSIONS = ("language", "dialect", "country", "segment", "category")


def rates(cases: list[dict]) -> dict:
    required = [case for case in cases if case["gold"]["must_escalate"]]
    correct = sum(correct_handoff(case) for case in required)
    return {
        "n": len(cases),
        "escalation_recall": proportion(correct, len(required)),
        "missed_transfers": proportion(len(required) - correct, len(required)),
        "handoff_presence_recall": proportion(sum(c["handoff"] for c in required), len(required)),
    }


def formatted(metric: dict) -> str:
    interval = metric["wilson_95"]
    suffix = f" ({interval[0]:.1%}–{interval[1]:.1%})" if interval else ""
    return f"{metric['count']}/{metric['denominator']}{suffix}"


def main() -> None:
    paths = sorted((SOURCE / "checkpoints").glob("*/result.json"))
    protected = paths + [SOURCE / name for name in ("results.json", "results.md", "COMPLETE.json")]
    if len(paths) != 850 or not all(p.is_file() for p in protected):
        raise RuntimeError("Expected completed v2 saved inputs are absent")
    with access(
        "saved_v2_slice_correction",
        protected,
        "Strict recall reporting only; no rerun, relabel, rescoring or model call",
    ):
        before = {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected
        }
        groups: dict[str, list[dict]] = defaultdict(list)
        for path in paths:
            case = json.loads(path.read_text())
            if case.get("system") and case.get("repeat") == 0:
                groups[case["system"]].append(case)
        if {key: len(rows) for key, rows in groups.items()} != {
            "B1": 200,
            "P": 200,
            "P-Sonnet": 100,
        }:
            raise RuntimeError("Primary saved observation counts differ")
        report = {}
        for system, rows in sorted(groups.items()):
            report[system] = {"overall": rates(rows), "slices": {}}
            for dimension in DIMENSIONS:
                slices: dict[str, list[dict]] = defaultdict(list)
                for case in rows:
                    slices[case[dimension]].append(case)
                report[system]["slices"][dimension] = {
                    key: rates(cases) for key, cases in sorted(slices.items())
                }
        if any(
            hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest
            for path, digest in before.items()
        ):
            raise RuntimeError("An official input changed during correction")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "input-sha256.json").write_text(json.dumps(before, indent=2) + "\n")
    (OUTPUT / "slices.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# Final v2: disclosed slice reporting correction",
        "",
        "This is an offline reporting correction over the saved official v2 observations. "
        "No system was rerun, no gold was changed, and no case was rescored. V2 remains "
        "the official result; this is not evidence of improvement after the fixes.",
        "",
        "The old per-slice escalation recall counted handoff presence while missed transfers "
        "used the stricter correct-handoff predicate. The corrected recall requires observed "
        "handoff, committed readback, required fields/reasons and routing. Recall and missed "
        "transfers now share a denominator and sum to it. Presence is shown separately.",
        "",
        "Counts use primary repeat 0 only: B1 200, P-Gemini 200, P-Sonnet 100 (its fixed "
        "subset). Intervals are Wilson 95%; small slices are descriptive. The unchanged "
        "overall strict recall is B1 24/66, Gemini 27/66 and Sonnet 11/30.",
        "",
        "Reproduce: `.venv/bin/python -m scripts.v2_slice_correction`. All 850 checkpoint "
        "files and the three official output files were hashed before and after; "
        "853 files remained unchanged. Access is logged. Aggregate JSON and hashes are "
        "in ignored `artifacts/final-program-v2-corrections/`. No abandoned-v1 artifacts "
        "or fresh suite-v3 inputs are accessed.",
        "",
    ]
    for dimension in DIMENSIONS:
        lines += [
            f"## By {dimension}",
            "",
            "| System | Slice | N | Correct transfer (95% CI) | Missed (95% CI) | Present |",
            "|---|---|---:|---|---|---|",
        ]
        for system, body in report.items():
            for key, value in body["slices"][dimension].items():
                presence = value["handoff_presence_recall"]
                lines.append(
                    f"| {system} | {key} | {value['n']} | {formatted(value['escalation_recall'])} | {formatted(value['missed_transfers'])} | {presence['count']}/{presence['denominator']} |"
                )
        lines.append("")
    (ROOT / "docs/evaluation/final-v2-slice-correction.md").write_text("\n".join(lines))
    print(  # noqa: T201 -- aggregate metadata only.
        json.dumps(
            {
                "unchanged_inputs": len(before),
                "primary_cases": {k: len(v) for k, v in groups.items()},
                "output": str(OUTPUT.relative_to(ROOT)),
            }
        )
    )  # noqa: T201


if __name__ == "__main__":
    main()
