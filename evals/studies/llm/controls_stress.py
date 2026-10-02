"""Pre-registered, post-ablation adversarial dev supplement; no runtime imports here."""

# ruff: noqa: T201 -- numeric aggregate reporting only.
from __future__ import annotations

import json
import sys
from collections import Counter
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from evals.studies.llm import controls_ablation as study
from evals.studies.llm.controls_stress_cases import CASES
from evals.studies.llm.dev_robustness import DevBudgetStop, save

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name("controls_stress_cases.py")
PROTOCOL = ROOT / "docs/evaluation/controls-ablation-stress-protocol.md"
OUT = ROOT / "artifacts/controls-stress"
SCOPE, RUN, CAP = "dev-gate/controls-stress", "controls-stress", Decimal("0.10")


def validate() -> None:
    manifest = json.loads(SOURCE.with_suffix(".manifest.json").read_text())
    if (
        sha256(SOURCE.read_bytes()).hexdigest() != manifest["sha256"]
        or sha256(PROTOCOL.read_bytes()).hexdigest() != manifest["protocol_sha256"]
        or len(CASES) != manifest["cases"]
        or len({case["id"] for case in CASES}) != len(CASES)
        or any(
            sum(case["language"] == lang for case in CASES) != manifest[lang]
            for lang in ("es", "pt")
        )
    ):
        raise DevBudgetStop("Frozen supplement inventory/protocol changed")


def configure() -> None:
    """Separate CLI process; never reuse the first study's scope/checkpoints."""
    study.CASES, study.OUT = CASES, OUT
    study.SCOPE, study.RUN, study.CAP = SCOPE, RUN, CAP


def report() -> dict:
    """Fixed scorer, aggregate only; never rewrite either arm's raw checkpoint."""
    rows = json.loads((OUT / "real.json").read_text())
    cases = {case["id"]: case for case in CASES}
    if len({row["id"] for row in rows}) != len(rows) or any(row["id"] not in cases for row in rows):
        raise DevBudgetStop("Unexpected/duplicate stress output")
    summary = {
        arm: {metric: sum(row[arm][metric] for row in rows) for metric in study.METRICS}
        for arm in ("P", "naive")
    }
    merchants = [row for row in rows if cases[row["id"]]["category"] == "merchant"]
    result = dict(
        completed_pairs=len(rows),
        planned_pairs=len(CASES),
        metrics=summary,
        language_metrics={
            lang: {
                arm: {
                    metric: sum(
                        row[arm][metric] for row in rows if cases[row["id"]]["language"] == lang
                    )
                    for metric in study.METRICS
                }
                for arm in ("P", "naive")
            }
            for lang in ("es", "pt")
        },
        p_outcomes=dict(
            Counter(
                reply.get("outcome", "missing") for row in rows for reply in row["P"]["replies"]
            )
        ),
        merchant_cases_completed=len(merchants),
        naive_merchant_lookups=sum(
            any(call["name"] == "lookup" for call in row["naive"]["calls"]) for row in merchants
        ),
        p_merchant_guard_events=sum(
            "indirect_prompt_injection" in row["P"].get("security_events", []) for row in merchants
        ),
        naive_tool_calls=sum(len(row["naive"]["calls"]) for row in rows),
        budget=json.loads((OUT / "budget-after.json").read_text()),
    )
    save(OUT / "report.json", result)
    print(json.dumps(result))
    return result


def main() -> None:
    validate()
    configure()
    if "--report" in sys.argv:
        report()
    else:
        study.main(inventory=SOURCE)


if __name__ == "__main__":
    main()
