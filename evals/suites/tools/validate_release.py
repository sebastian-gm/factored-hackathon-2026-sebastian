"""Validate authored inputs and freeze integrity without executing a banking system."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
RELEASE = ROOT / "evals/suites/test"


def check_payloads(directory: Path) -> dict[str, Any]:
    schema = json.loads((ROOT / "contracts/interfaces/scenario-suite.schema.json").read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    scenarios = []
    for path in sorted(directory.glob("scenarios-*.yaml")):
        payload = yaml.safe_load(path.read_text())
        validator.validate(payload)
        assert payload["version"] == 2 and payload["suite_id"] == "heldout-e2e-v2"
        scenarios.extend(payload["scenarios"])
    assert len(scenarios) == 200
    assert len({s["id"] for s in scenarios}) == 200
    assert len({s["persona"]["customer_ref"] for s in scenarios}) == 200
    assert Counter(s["category"] for s in scenarios) == {
        "normal": 70,
        "ambiguous_unsupported": 40,
        "human_required": 40,
        "security_robustness": 50,
    }
    assert Counter(s["language"] for s in scenarios) == {
        "es": 96,
        "pt": 84,
        "mixed": 17,
        "other": 3,
    }
    assert Counter(s["dialect"] for s in scenarios if s["language"] == "es") == {
        "es-MX": 32,
        "es-CO": 32,
        "es-AR": 32,
    }
    message_count = 0
    for s in scenarios:
        assert s["persona"]["split"] == "test"
        assert s["expected"] == s["gold"]["outcome"]
        assert s["gold"]["written_rule_basis"]
        assert s["gold"]["reason_codes"]
        assert s["gold"]["must_not_disclose"]
        assert "default" in s["reactive_replies"]
        assert s["reactive_replies"]["choose_txn"] == s["reactive_replies"]["choose_transaction"]
        assert s["reactive_replies"]["ask_clarification"] == s["reactive_replies"]["clarify"]
        assert s["reply_exhaustion"] == "repeat_last" and s["max_turns"] == 12
        actions = {a["type"] for a in s["gold"]["required_actions"]}
        assert not actions.intersection(s["gold"]["forbidden_actions"])
        assert s["gold"]["must_escalate"] == ("create_handoff" in actions)
        assert bool(s["gold"]["required_handoff_fields"]) == s["gold"]["must_escalate"]
        if s["expected"] == "dispute_filed_flagged":
            assert "set_review_flag" in actions and not s["gold"]["must_escalate"]
        if s["expected"] == "freeze_and_escalate":
            assert {"freeze_card", "create_handoff", "verify_readback"} <= actions
        if s["template_id"] == "stale_step_up":
            assert s["reactive_replies"]["confirm_action"] == [{"confirm": True}]
            assert s["customer_knowledge"]["provides_new_step_up"] is False
        refs = {o["record_ref"] for o in s["overlays"]}
        assert len(refs) == len(s["overlays"])
        if s["gold"]["expected_transaction_ref"] is not None:
            assert s["gold"]["expected_transaction_ref"] in refs
        assert all(o["origin"] == "project_generated" for o in s["overlays"])
        if s["language"] == "pt":
            p = s["utterance_provenance"]
            assert p["origin"] == "model_generated"
            assert p["generator_vendor"] == "Google" and p["reviewer_vendor"] == "Anthropic"
            assert p["review_status"] in {"passed", "corrected_and_passed"}
            assert p["generation_record_sha256"] and p["review_record_sha256"]
            message_count += sum("message" in t for t in s["turns"])
            message_count += sum(
                "message" in r for seq in s["reactive_replies"].values() for r in seq
            )
    for path in (ROOT / "evals/suites").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(alias.name.startswith("aclara") for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("aclara")
    summary = {
        "scenarios": 200,
        "categories": dict(Counter(s["category"] for s in scenarios)),
        "languages": dict(Counter(s["language"] for s in scenarios)),
        "dialects": dict(Counter(s["dialect"] for s in scenarios)),
        "gold_outcomes": dict(Counter(s["expected"] for s in scenarios)),
        "must_escalate": sum(s["gold"]["must_escalate"] for s in scenarios),
        "portuguese_reviewed_texts": message_count,
    }
    return summary


def verify_manifest(directory: Path) -> None:
    manifest = directory / "MANIFEST.sha256"
    entries = {}
    for line in manifest.read_text().splitlines():
        checksum, name = line.split("  ", 1)
        assert "/" not in name and name not in {".", "..", "MANIFEST.sha256"}
        assert name not in entries
        entries[name] = checksum
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == checksum
    assert set(entries) == {p.name for p in directory.iterdir() if p.is_file() and p != manifest}
    provenance = json.loads((directory / "provenance.json").read_text())
    for relative, digest in provenance["pinned_repository_inputs"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
    assert float(provenance["language_authoring"]["accounted_usd"]) <= 3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=RELEASE)
    parser.add_argument("--before-freeze", action="store_true")
    args = parser.parse_args()
    summary = check_payloads(args.directory)
    if not args.before_freeze:
        verify_manifest(args.directory)
    print(json.dumps(summary, sort_keys=True))  # noqa: T201 -- aggregate checks only.


if __name__ == "__main__":
    main()
