"""Map the pre-fix-frozen semantic offer cases to dev reactive scenarios."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[3]
CASES = ROOT / "evals/studies/llm/dev_explain_offer_20.yaml"
MANIFEST = ROOT / "evals/studies/llm/dev_explain_offer_20.sha256"


def load_offer_scenarios() -> list[dict[str, Any]]:
    """Fail closed if the frozen authored cases change; never derive gold from code."""
    raw = CASES.read_bytes()
    expected_hash = MANIFEST.read_text(encoding="utf-8").split()[0]
    if sha256(raw).hexdigest() != expected_hash:
        raise ValueError("Frozen offer confirmation cases changed")
    source: dict[str, Any] = yaml.safe_load(raw)
    if source.get("version") != 1 or source.get("status") != "frozen_before_v5":
        raise ValueError("Unexpected offer confirmation source version")
    cases: list[dict[str, Any]] = source["cases"]
    if len(cases) != 20 or len({case["id"] for case in cases}) != 20:
        raise ValueError("Offer confirmation inventory must contain 20 unique cases")
    target = str(source["fixture_transaction_ref"])
    scenarios: list[dict[str, Any]] = []
    for case in cases:
        language = case["language"]
        outcome = case["expected_path"]
        dispute = outcome == "dispute_after_offer"
        if language not in {"es", "pt"} or outcome not in {
            "dispute_after_offer",
            "resolved_by_explanation",
        }:
            raise ValueError("Invalid frozen offer case semantics")
        gold_outcome = "dispute_filed" if dispute else "resolved_by_explanation"
        required_actions = [
            {"type": "explain_status", "target_ref": target},
            {"type": "offer_dispute", "target_ref": target},
        ]
        if dispute:
            required_actions.append({"type": "create_dispute", "target_ref": target})
        scenarios.append(
            {
                "id": case["id"],
                "language": language,
                "persona": {"customer_ref": f"fixture-persona-{language}", "split": "test"},
                "bank_clock": "2026-06-18T06:00:00Z",
                "max_turns": 8,
                "turns": [{"message": case["opening"]}],
                "expected": gold_outcome,
                "customer_knowledge": {"selection_ref": target},
                "reactive_replies": {
                    "offer_dispute": [{"message": case["after_offer"]}],
                    "choose_transaction": [{"choose_ref": target}],
                    "confirm_action": [{"confirm": True}],
                    "default": [{"message": "não sei" if language == "pt" else "no sé"}],
                },
                "gold": {
                    "outcome": gold_outcome,
                    "expected_transaction_ref": target,
                    "required_actions": required_actions,
                    "forbidden_actions": ["promise_refund"]
                    if dispute
                    else ["promise_refund", "create_dispute"],
                    "must_escalate": False,
                    "reason_codes": ["DSP-01", "DSP-02", "DSP-07"] if dispute else [],
                    "required_handoff_fields": [],
                    "must_not_disclose": [],
                    "in_scope": True,
                    "written_rule_basis": (
                        "ADR-0015 and conversation-policy-v3 §1–2; independent semantic "
                        "case frozen before implementation."
                    ),
                },
            }
        )
    return scenarios


def load_offer_suite() -> dict[str, Any]:
    """Provide the standard dev-suite wrapper to the lead-owned gate/validator."""
    return {
        "version": 2,
        "description": "Frozen after-v2 ES/PT explain-offer confirmation cases; dev only.",
        "scenarios": load_offer_scenarios(),
    }
