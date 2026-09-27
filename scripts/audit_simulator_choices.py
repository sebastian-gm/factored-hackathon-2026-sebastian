"""Owner-authorized static choice-coverage audit; counts only, no execution or bindings.

All scenarios are conservatively included as potentially reaching MATCH. Static
structure cannot predict NLU routing. Only reference identities, reply structure,
and overlay kinds are consulted; no gold outcome or conversation text is examined.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml
from evals.access import access
from evals.reactive import Customer

ROOT = Path(__file__).resolve().parents[1]


def coverage(scenarios: list[dict]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for scenario in scenarios:
        counts["scenarios_conservatively_in_scope"] += 1
        refs = {
            overlay["record_ref"]: f"txn_{i}"
            for i, overlay in enumerate(scenario.get("overlays", []))
            if overlay["kind"] == "transaction"
        }
        target = scenario.get("customer_knowledge", {}).get("selection_ref") or (
            scenario.get("gold") or {}
        ).get("expected_transaction_ref")
        table = scenario.get("reactive_replies", {})
        explicit = table.get("choose_transaction", table.get("choose_txn"))
        if explicit is not None:
            counts["explicit_choice_behavior"] += 1
            if explicit and all(reply.get("choose_ref") in refs for reply in explicit):
                counts["explicit_choice_resolves_to_transaction_overlay"] += 1
                if target and all(reply.get("choose_ref") == target for reply in explicit):
                    counts["explicit_choice_matches_expected_target"] += 1
            else:
                counts["explicit_behavior_preserved_not_statically_proven"] += 1
                counts[
                    "explicit_nonselection_with_target"
                    if target
                    else "explicit_nonselection_without_target"
                ] += 1
            continue
        if target and target in refs:
            # Exercise the same Customer used by both adapters, at every rank.
            customer = Customer(scenario, refs)
            for index in range(3):
                candidates = [{"handle": f"other_{i}"} for i in range(3)]
                candidates[index] = {"handle": refs[target]}
                reply = customer.reply(
                    {"response_type": "choose_transaction", "candidates": candidates}
                )
                expected = (
                    ("primeiro", "segundo", "terceiro")
                    if scenario["language"] == "pt"
                    else ("primero", "segundo", "tercero")
                )
                assert reply == {"message": expected[index]}
            counts["generic_fix_supplies_choice_when_target_offered"] += 1
        elif target:
            counts["target_requires_private_binding_not_audited"] += 1
        else:
            counts["no_target_no_explicit_choice_remains_uncertain"] += 1
    return dict(sorted(counts.items()))


def main() -> None:
    paths = sorted((ROOT / "evals/suites/test").glob("scenarios-*.yaml"))
    if len(paths) != 4:
        raise ValueError("Unexpected frozen suite layout")
    with access(
        "static-choice-coverage",
        paths,
        "Owner-authorized aggregate-only simulator audit before v2; no outcomes, text, or bindings",
    ):
        before = {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}
        scenarios = [s for p in paths for s in yaml.safe_load(p.read_text())["scenarios"]]
        result = coverage(scenarios)
        assert before == {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}
    output = ROOT / "artifacts/option-a-dev/frozen-choice-coverage.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))  # noqa: T201 -- counts only, explicitly authorized.


if __name__ == "__main__":
    main()
