"""Assemble reviewed authoring output; freezing is explicit and refuses overwrite."""

# ruff: noqa: T201 -- CLI reports aggregate authoring checks only.
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from portuguese_authoring import digest, text_items
from validate_release import check_payloads, verify_manifest

ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / "artifacts/evaluation-authoring"
STAGE = PRIVATE / "release-stage"
RELEASE = ROOT / "evals/suites/test"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    assert json.loads(path.read_text()) == value


def replace_text(scenario: dict[str, Any], key: str, value: str) -> None:
    bits = key.split(".")
    if bits[0] == "turns":
        scenario["turns"][int(bits[1])]["message"] = value
    else:
        scenario["reactive_replies"][bits[1]][int(bits[2])]["message"] = value


def tokens(text: str) -> list[str]:
    return sorted(re.findall(r"\{\{[^{}]+\}\}", text))


def numbers(text: str) -> list[Decimal]:
    return sorted(Decimal(x.replace(",", ".")) for x in re.findall(r"(?<!\w)\d+(?:[.,]\d+)?", text))


def subset(scenarios: list[dict[str, Any]], counts: tuple[int, ...], seed: str) -> list[str]:
    selected = []
    categories = ["normal", "ambiguous_unsupported", "human_required", "security_robustness"]
    for category, n in zip(categories, counts, strict=True):
        group = [s for s in scenarios if s["category"] == category]
        group.sort(key=lambda s: hashlib.sha256((seed + s["id"]).encode()).hexdigest())
        selected.extend(s["id"] for s in group[:n])
    return selected


def assemble() -> None:
    suite = json.loads((PRIVATE / "draft-suite.json").read_text())
    by_id = {s["id"]: s for s in suite["scenarios"]}
    completed = set()
    corrections = []
    audit = []
    for batch in range(14):
        gen = json.loads((PRIVATE / f"pt-generate-{batch:02}.json").read_text())
        initial_review = json.loads((PRIVATE / f"pt-review-{batch:02}.json").read_text())
        prior_by_id = {item["id"]: item for item in initial_review["content"]["items"]}
        review = json.loads((PRIVATE / f"pt-review_protected-{batch:02}.json").read_text())
        assert gen["response_model"].startswith("google/") and review["response_model"].startswith(
            "anthropic/"
        )
        generation = {item["id"]: item for item in gen["content"]["items"]}
        reviewed = review["content"]["items"]
        assert {item["id"] for item in reviewed} == set(generation)
        for item in reviewed:
            scenario = by_id[item["id"]]
            assert scenario["language"] == "pt"
            original = {x["key"]: x["text"] for x in text_items(scenario)}
            assert sorted(x["key"] for x in item["texts"]) == sorted(original)
            for result in item["texts"]:
                key, text = result["key"], result["text"]
                source = original[key]
                merchant = scenario["customer_knowledge"]["remembered_merchant"]
                if merchant:
                    text = text.replace("{{merchant}}", merchant)
                assert tokens(text) == tokens(source), (scenario["id"], key, "placeholder drift")
                assert numbers(text) == numbers(source), (scenario["id"], key, "numeric drift")
                if merchant and merchant in source:
                    assert merchant in text
                replace_text(scenario, key, text)
            for old, new in [
                ("choose_txn", "choose_transaction"),
                ("ask_clarification", "clarify"),
            ]:
                scenario["reactive_replies"][new] = copy.deepcopy(scenario["reactive_replies"][old])
            changed = {x["key"]: x["text"] for x in text_items(scenario)} != {
                x["key"]: x["text"] for x in generation[item["id"]]["texts"]
            }
            scenario["utterance_provenance"] = {
                "origin": "model_generated",
                "generator_vendor": "Google",
                "generator_model": gen["response_model"],
                "reviewer_vendor": "Anthropic",
                "reviewer_model": review["response_model"],
                "review_status": "corrected_and_passed" if changed else "passed",
                "generation_record_sha256": digest(generation[item["id"]]),
                "review_record_sha256": digest(item),
                "human_review_status": "pending",
            }
            completed.add(item["id"])
            if scenario["utterance_provenance"]["review_status"] == "corrected_and_passed":
                corrections.append(item["id"])
            audit.append(
                {
                    "id": item["id"],
                    "status": "corrected" if changed else "passed",
                    "vendor_reported_status": item["status"],
                    "issues": prior_by_id[item["id"]]["issues"] + item["issues"],
                    "text_count": len(item["texts"]),
                }
            )
    assert len(completed) == 84
    STAGE.mkdir(parents=True, exist_ok=True)
    for category in ("normal", "ambiguous_unsupported", "human_required", "security_robustness"):
        payload = {key: value for key, value in suite.items() if key != "scenarios"}
        payload["scenarios"] = [s for s in suite["scenarios"] if s["category"] == category]
        (STAGE / f"scenarios-{category}.yaml").write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100)
        )
    coverage = check_payloads(STAGE)
    write_json(STAGE / "coverage.json", coverage)
    write_json(
        STAGE / "review-selection.json",
        {
            "independent_human_labeling_status": "pending",
            "n": 40,
            "seed": "human-review-v1:",
            "scenario_ids": subset(suite["scenarios"], (14, 8, 8, 10), "human-review-v1:"),
        },
    )
    write_json(
        STAGE / "repeat-selection.json",
        {
            "n": 100,
            "seed": "repeat-v1:",
            "scenario_ids": subset(suite["scenarios"], (35, 20, 20, 25), "repeat-v1:"),
        },
    )
    write_json(
        STAGE / "language-review.json",
        {
            "reviewed_portuguese_scenarios": 84,
            "reviewed_texts": sum(x["text_count"] for x in audit),
            "corrected_scenarios": len(corrections),
            "reviews": audit,
            "normalization": "Merchant placeholders are restored literally from the fictional fixture; current and future response-plan aliases share identical reviewed replies.",
            "human_portuguese_review": "pending; no fluent reviewer available",
        },
    )
    ledger = json.loads((PRIVATE / "budget-ledger.json").read_text())
    assert len(ledger["calls"]) == 42 and all(c["status"] == "validated" for c in ledger["calls"])
    cost = sum(Decimal(c["accounted_usd"]) for c in ledger["calls"])
    assert cost <= Decimal("3")
    prices = json.loads((PRIVATE / "model-prices.json").read_text())
    tracked = {}
    for path in [
        ROOT / "contracts/interfaces/scenario-suite.schema.json",
        ROOT / "docs/evaluation/eval-protocol.md",
        ROOT / "docs/evaluation/adapter-handoff.md",
        ROOT / "evals/suites/authoring-templates.yaml",
        *sorted((ROOT / "evals/suites/tools").glob("*.py")),
    ]:
        tracked[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    provenance = {
        "suite_id": "heldout-e2e-v2",
        "prepared_at": datetime.now(UTC).isoformat(),
        "version_history": json.loads((PRIVATE / "version-history.json").read_text()),
        "policy_source": suite["policy_source"],
        "dataset_version": suite["dataset_version"],
        "gold_authority": "Written brief section 9 plus authored fixture conditions; never policy-engine outputs.",
        "bindings_audit": json.loads((PRIVATE / "binding-audit.json").read_text()),
        "billing_verification": json.loads((PRIVATE / "billing-verification.json").read_text()),
        "language_authoring": {
            "cap_usd": "3.00",
            "accounted_usd": str(cost),
            "calls": 42,
            "generator": "google/gemini-2.5-flash",
            "reviewer": "anthropic/claude-haiku-4.5",
            "prompt_tokens": sum(c["prompt_tokens"] for c in ledger["calls"]),
            "completion_tokens": sum(c["completion_tokens"] for c in ledger["calls"]),
            "prices_checked_at": prices["checked_at"],
            "price_source": prices["source"],
            "thinking_persisted": False,
            "organizer_records_sent": False,
        },
        "pinned_repository_inputs": tracked,
        "limitations": [
            "Human dual labeling of 40 cases is pending; no kappa claimed.",
            "Portuguese has model cross-checks, not fluent-human validation.",
            "Lead-owned organizer binding, richer overlay and fault adaptation pending; no held-out system runs performed.",
            "Controlled fictional overlays are not representative historical traffic.",
        ],
    }
    write_json(STAGE / "provenance.json", provenance)
    assert all(path.stat().st_size < 512 * 1024 for path in STAGE.iterdir() if path.is_file())
    print(
        json.dumps(
            {
                "staged_scenarios": 200,
                "reviewed_pt": 84,
                "corrected_pt": len(corrections),
                "authoring_cost_usd": str(cost),
            }
        )
    )  # noqa: T201


def freeze() -> None:
    if RELEASE.exists():
        raise RuntimeError(
            "release directory already exists; create a new suite version instead of overwriting"
        )
    check_payloads(STAGE)
    shutil.copytree(STAGE, RELEASE)
    entries = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in sorted(RELEASE.iterdir())
        if path.is_file()
    ]
    (RELEASE / "MANIFEST.sha256").write_text("\n".join(entries) + "\n")
    verify_manifest(RELEASE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    assemble()
    if args.freeze:
        freeze()


if __name__ == "__main__":
    main()
