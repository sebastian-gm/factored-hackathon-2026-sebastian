"""Zero-call, type-only MATCH replay of explicitly retired private dev journals.

Freeze baseline slots before the fix, then compare after it. Snapshot candidates
omit process_date, so use transaction_date's day: this is a reconstruction, not
an end-to-end counterfactual or an official conversation pass measurement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from aclara.agent.matching import MatchState
from aclara.agent.nlu.structured import ExtractedNlu, NormalizedSlots, postprocess
from aclara.bank.repository import Transaction


def _json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _source_kind(path: Path) -> str:
    # No suite loader, model client, serving database or held-out input is used.
    path = path.resolve()
    if path.name == "final-program-v3":
        return "v3-primary"
    if path.name in {"before", "after"}:
        if path.parent.name == "nlu-robustness-post-v3":
            return f"robust40-{path.name}"
        if path.parent.name == "round2-real":
            return f"robust60-{path.name}"
    raise ValueError("Only the named retired v3/robustness dev directories are allowed")


def _valid_calls(path: Path, *, field: str) -> dict[str, dict[str, Any]]:
    calls: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        call, output = value.get("call", {}), value.get(field)
        if call.get("route") == "nlu" and call.get("status") == "valid" and output:
            generation = call.get("generation_id")
            if not generation:
                raise ValueError("A valid NLU output lacks its event-alignment generation ID")
            if generation in calls:
                raise ValueError("Duplicate valid NLU generation ID")
            calls[generation] = {"id": value.get("id"), "output": output}
    return calls


def _matched_outputs(
    events: list[dict[str, Any]], calls: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Bind MATCH to the last successful call preceding its non-degraded NLU.

    Execution records may repeat earlier llm_call events. IDs, not their counts,
    align validated journal outputs. A degraded NLU never reuses an older output.
    """
    pending: dict[str, Any] | None = None
    active: dict[str, Any] | None = None
    matched = []
    for event in events:
        kind = event.get("event")
        if kind == "llm_call" and event.get("route") == "nlu":
            if event.get("status") == "valid":
                pending = calls.get(event.get("generation_id", ""))
        elif kind == "nlu":
            active = None if event.get("degraded") else pending
            pending = None
        elif kind == "match" and active is not None:
            matched.append({"output": active["output"], "recorded_action": event["action"]})
    return matched


def _candidates(row: dict[str, Any]) -> list[tuple[str, Transaction]]:
    clock = datetime.fromisoformat(row["bank_clock"].replace("Z", "+00:00"))
    candidates = []
    for handle, fact in row["trusted_facts"].items():
        day = datetime.fromisoformat(fact["transaction_date"].replace("Z", "+00:00"))
        if not clock - timedelta(days=120) <= day < clock:
            continue
        candidates.append(
            (
                handle,
                Transaction(
                    handle,
                    "authored-customer",
                    "authored-product",
                    day,
                    day.date(),
                    fact["transaction_type"],
                    float(fact["amount"]),
                    fact["currency"],
                    fact["merchant"],
                    fact["status"],
                ),
            )
        )
    return candidates


def freeze(sources: list[Path], output: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Baseline already exists; never overwrite a frozen replay")
    source_names = [_source_kind(path) for path in sources]  # validate before reads
    matcher = MatchState()
    digest = hashlib.sha256()
    frozen: list[dict[str, Any]] = []
    for root, name in zip(sources, source_names, strict=True):
        result_paths = (
            sorted(root.glob("checkpoints/*/result.json"))
            if name == "v3-primary"
            else sorted(root.glob("*.json"))
        )
        shared_calls = (
            None if name == "v3-primary" else _valid_calls(root / "calls.jsonl", field="validated")
        )
        for path in result_paths:
            row = _json(path)
            if row.get("system") != "P" or row.get("repeat") != 0:
                continue
            calls_path = (
                path.parent / "calls-1.jsonl" if name == "v3-primary" else root / "calls.jsonl"
            )
            calls = (
                (_valid_calls(calls_path, field="validated_output") if calls_path.exists() else {})
                if shared_calls is None
                else {key: value for key, value in shared_calls.items() if value["id"] == row["id"]}
            )
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
            if shared_calls is None and calls_path.exists():
                digest.update(calls_path.read_bytes())
            rows = _candidates(row)
            clock = datetime.fromisoformat(row["bank_clock"].replace("Z", "+00:00"))
            matched = []
            for item in _matched_outputs(row["events"], calls):
                raw = ExtractedNlu.model_validate(item["output"])
                slots = postprocess(raw, country=row["country"], bank_clock=clock).slots
                decision = matcher.match(slots, rows, "authored-customer", clock)
                matched.append(
                    {
                        "raw_type": raw.type_expr,
                        "slots": slots.model_dump(mode="json"),
                        "before": asdict(decision),
                        "recorded_action": item["recorded_action"],
                    }
                )
            target_ref = row["gold"].get("expected_transaction_ref")
            frozen.append(
                {
                    "set": name,
                    "id": row["id"],
                    "language": row["language"],
                    "passed": row["passed"],
                    "clock": clock.isoformat(),
                    "target": row["refs"].get(target_ref) if target_ref else None,
                    # Minimal masked snapshot; no persona IDs, utterances or reasoning.
                    "facts": row["trusted_facts"],
                    "matches": matched,
                    "raw_types": [value["output"].get("type_expr") for value in calls.values()],
                }
            )
        if shared_calls is not None:
            digest.update((root / "calls.jsonl").read_bytes())
    pins = _pins()
    payload = {"source_digest": digest.hexdigest(), "matcher_pins": pins, "cases": frozen}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "frozen_cases": len(frozen),
        "baseline_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "matcher_pins": pins,
    }


def _pins() -> dict[str, str]:
    root = Path(__file__).resolve().parents[3] / "models/charge_matcher/v2"
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in ("model.json", "metadata.json", "lightgbm.txt")
    }


def compare(baseline: Path) -> dict[str, Any]:
    from aclara.agent.nlu.transaction_types import normalize_transaction_type

    frozen = _json(baseline)
    if frozen["matcher_pins"] != _pins():
        raise ValueError("Matcher changed since baseline")
    matcher = MatchState()
    summaries: dict[str, Counter[str]] = {}
    details = []
    for case in frozen["cases"]:
        counts = summaries.setdefault(case["set"], Counter())
        counts["cases"] += 1
        counts["original_pass"] += int(case["passed"])
        raw_types = case["raw_types"]
        counts["valid_nlu_calls"] += len(raw_types)
        # Compare with the baseline slot, not just the raw model expression.
        changed_matches = []
        for match in case["matches"]:
            counts["aligned_matches"] += 1
            counts["baseline_action_agrees_saved"] += int(
                match["before"]["action"] == match["recorded_action"]
            )
            slots = NormalizedSlots.model_validate(match["slots"])
            canonical = normalize_transaction_type(match["raw_type"])
            if canonical == slots.type_expr:
                continue
            counts["changed_matches"] += 1
            rows = _candidates({"trusted_facts": case["facts"], "bank_clock": case["clock"]})
            decision = matcher.match(
                slots.model_copy(update={"type_expr": canonical}),
                rows,
                "authored-customer",
                datetime.fromisoformat(case["clock"]),
            )
            before = match["before"]
            action_changed = (before["action"], tuple(before["transaction_ids"])) != (
                decision.action,
                decision.transaction_ids,
            )
            correct_before = before["action"] == "propose" and before["transaction_ids"] == [
                case["target"]
            ]
            correct_after = decision.action == "propose" and decision.transaction_ids == (
                case["target"],
            )
            counts["action_or_target_changed"] += int(action_changed)
            counts["correct_proposal_gained"] += int(correct_after and not correct_before)
            counts["correct_proposal_lost"] += int(correct_before and not correct_after)
            baseline_agrees = before["action"] == match["recorded_action"]
            counts["concordant_correct_proposal_gained"] += int(
                correct_after and not correct_before and baseline_agrees
            )
            changed_matches.append(
                {
                    "raw_type": match["raw_type"],
                    "canonical": canonical,
                    "before": before,
                    "after": asdict(decision),
                    "recorded_action": match["recorded_action"],
                    "baseline_agrees": baseline_agrees,
                    "correct_proposal_gained": correct_after and not correct_before,
                }
            )
        if changed_matches:
            counts["changed_cases"] += 1
            counts[f"changed_cases_{case['language']}"] += 1
            counts["original_failures_with_changed_match"] += int(not case["passed"])
            counts["original_failures_gaining_correct_proposal"] += int(
                not case["passed"]
                and any(item["correct_proposal_gained"] for item in changed_matches)
            )
            counts["original_failures_with_concordant_proposal_gain"] += int(
                not case["passed"]
                and any(
                    item["correct_proposal_gained"] and item["baseline_agrees"]
                    for item in changed_matches
                )
            )
            details.append(
                {
                    "set": case["set"],
                    "id": case["id"],
                    "original_pass": case["passed"],
                    "language": case["language"],
                    "matches": changed_matches,
                }
            )
    return {
        "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
        "source_digest": frozen["source_digest"],
        "matcher_pins": _pins(),
        "summaries": summaries,
        "private_details": details,
        "cost_usd": 0,
        "limits": "Type-only reconstructed MATCH, not full conversation rescoring. process_date=transaction_date.date(); no sticky-slot or product-selection state replay.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "compare"))
    parser.add_argument("--source", type=Path, action="append", default=[])
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    artifact_root = Path(__file__).resolve().parents[3] / "artifacts"
    for destination in (args.baseline, args.report):
        if destination is not None and not destination.resolve().is_relative_to(artifact_root):
            raise ValueError("Generated replay data must stay in ignored artifacts/")
    if args.phase == "freeze":
        if not args.source:
            raise ValueError("Provide at least one explicit retired dev source")
        result = freeze(args.source, args.baseline)
    else:
        result = compare(args.baseline)
        if args.report is None or args.report.exists():
            raise ValueError("Use a new private report path")
        args.report.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    sys.stdout.write(
        json.dumps(
            {key: value for key, value in result.items() if key != "private_details"}, indent=2
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
