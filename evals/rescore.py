"""Recompute measurement aggregates from preserved observations; never invokes a system."""

# ruff: noqa: S603, S607, T201 -- fixed read-only Git argv; aggregate CLI output only.
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from evals.bindings import ROOT
from evals.heldout import private_write
from evals.heldout_report import comparison, report
from evals.metrics import score


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if not all(p.is_relative_to(ROOT / "artifacts") for p in (source, output)) or output.exists():
        raise ValueError("Use a new ignored artifact directory and preserve the original run")
    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    header = json.loads((source / "access.json").read_text())
    files = sorted(source.glob("*-cases.jsonl"))
    header["measurement_revision"] = {
        "scorer_sha": sha,
        "reason": "Correct generic created-state and explanation target observations; unchanged labels, system outputs and actions; no system rerun",
        "source_hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    }
    cases = [score(json.loads(line)) for path in files for line in path.read_text().splitlines()]
    private_write(output / "access.json", json.dumps(header, indent=2) + "\n")
    private_write(
        output / "cases.jsonl", "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases)
    )
    b1 = [c for c in cases if c["system"] == "B1"]
    proposed = [c for c in cases if c["system"] == "P" and c["repeat"] == 0]
    repeats = [c for c in cases if c["repeat"] > 0]
    for system, rows in (("B1", b1), ("P-mock", proposed)):
        print(json.dumps({"measurement_reporting": system, "system_rerun": False}), flush=True)
        private_write(
            output / f"{system}-aggregates.json",
            json.dumps(report(rows, {**header, "system": system}), indent=2) + "\n",
        )
    repeat_ids = set(
        json.loads((ROOT / "evals/suites/test/repeat-selection.json").read_text())["scenario_ids"]
    )
    private_write(
        output / "comparison-aggregates.json",
        json.dumps(comparison(b1, proposed, repeats, repeat_ids), indent=2) + "\n",
    )
    print(json.dumps({"observations_rescored": len(cases), "system_reruns": 0, "cost_usd": 0}))


if __name__ == "__main__":
    main()
