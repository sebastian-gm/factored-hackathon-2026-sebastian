"""Pre-fix, project-authored multi-turn development fixtures; no held-out inputs."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from importlib import import_module
from pathlib import Path
from typing import Any

import jsonschema  # type: ignore[import-untyped]
import yaml  # type: ignore[import-untyped]

from aclara.llm.dev_robustness_cases import ROOT, digest_scenarios
from aclara.llm.dev_robustness_cases import scenario as base_scenario

CASES = Path(__file__).with_name("dev_robustness_round2_60.yaml")
MANIFEST = Path(__file__).with_name("dev_robustness_round2_60.manifest.json")
FEATURES = {
    "multi_turn",
    "detail_correction",
    "two_unrelated_charges",
    "charge_plus_case_status",
    "vague_then_specific",
    "emotion_without_distress",
    "code_switching",
    "regional_slang",
    "amount_words",
    "currency_confusion",
    "polite_offer_refusal",
    "recognition_after_offer",
    "relative_dates",
    "merchant_twins",
    "embedded_injection",
    "typos",
}


def identity(case: dict[str, Any]) -> dict[str, Any]:
    """Chile describes the utterance only; its authored bank fixture uses MX rules."""
    return {
        "customer_id": "round2-authored-" + case["id"],
        "product_id": "round2-card-" + case["id"],
        "selector": {
            "country": {"es-CO": "CO", "es-AR": "AR", "es-CL": "MX", "pt-BR": "BR"}[case["locale"]],
            "segment": "Basic",
        },
    }


def scenario(case: dict[str, Any], clock: str) -> dict[str, Any]:
    """Materialize independent gold without consulting product responses."""
    result = base_scenario(case, clock)
    result["turns"] = [{"message": message} for message in case["messages"]]
    result["max_turns"] = 5
    result["reactive_replies"]["clarify"] = [{"message": case["messages"][-1]}]
    result["reactive_replies"]["offer_dispute"] = [{"message": case["messages"][-1]}]
    rows = {
        "target": {
            "merchant": case["merchant"],
            "currency": case["currency"],
            "amount": case["amount"],
            "date": case["date"],
        },
        **{row["ref"]: row for row in case.get("twins", [])},
    }
    rates = {"USD": 1.0, "BRL": 0.2, "COP": 0.00025, "ARS": 0.001, "MXN": 0.05}
    # A twin may be another merchant or currency; the old forty-case builder's
    # same-merchant/same-currency assumptions must not change retroactively.
    result["overlays"] = [row for row in result["overlays"] if row["kind"] != "fx"]
    for overlay in result["overlays"]:
        if overlay["kind"] != "transaction":
            continue
        row = rows[overlay["record_ref"]]
        currency = row.get("currency", case["currency"])
        overlay["values"].update(
            merchant_name=row.get("merchant", case["merchant"]),
            currency=currency,
            amount_usd=row["amount"] * rates[currency],
        )
    fx_pairs = sorted(
        {(row.get("currency", case["currency"]), row["date"]) for row in rows.values()}
    )
    for index, (currency, day) in enumerate(fx_pairs):
        result["overlays"].append(
            {
                "kind": "fx",
                "record_ref": f"round2-fx-{index}",
                "origin": "project_generated",
                "values": {
                    "currency": currency,
                    "business_date": day,
                    "rate_date": day,
                    "usd_per_unit": rates[currency],
                    "available": True,
                    "fallback": False,
                },
            }
        )
    if "charge_plus_case_status" in case["tags"]:
        result["overlays"].append(
            {
                "kind": "case",
                "record_ref": "other-case",
                "origin": "project_generated",
                "values": {
                    "customer_ref": "persona",
                    "transaction_ref": "other",
                    "status": "received",
                    "created_at": "2026-06-15T18:00:00Z",
                },
            }
        )
        result["gold"]["required_actions"] += [
            {"type": "report_case", "target_ref": "other-case"},
            {"type": "verify_readback", "target_ref": "other-case"},
        ]
    if "two_unrelated_charges" in case["tags"]:
        result["gold"]["required_actions"].append({"type": "explain_status", "target_ref": "other"})
    result["gold"]["written_rule_basis"] = case["rule_basis"]
    return result


def materialize() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    data = yaml.safe_load(CASES.read_text())
    cases: list[dict[str, Any]] = data["cases"]
    return cases, [scenario(case, data["bank_clock"]) for case in cases]


def validate(*, verify_manifest: bool = True) -> dict[str, Any]:
    """Structural validation only: never executes B1/P or opens another suite."""
    cases, scenarios = materialize()
    if len(cases) != 60 or len({case["id"] for case in cases}) != 60:
        raise ValueError("Expected sixty unique authored conversations")
    locales = Counter(case["locale"] for case in cases)
    if locales != {"es-CO": 10, "es-AR": 10, "es-CL": 10, "pt-BR": 30}:
        raise ValueError("Pre-registered locale balance changed")
    families = Counter(case["family"] for case in cases)
    if len(families) != 10 or set(families.values()) != {6}:
        raise ValueError("Expected ten independently specified families of six variants")
    if {tag for case in cases for tag in case["tags"]} != FEATURES:
        raise ValueError("Pre-registered robustness coverage changed")
    if any(not 3 <= len(case["messages"]) <= 4 for case in cases):
        raise ValueError("Each conversation requires three/four scripted customer messages")
    if len({message for case in cases for message in case["messages"]}) != sum(
        len(case["messages"]) for case in cases
    ):
        raise ValueError("Messages must be newly authored and unique within this set")
    schema = json.loads((ROOT / "contracts/interfaces/scenario-suite.schema.json").read_text())
    schema.pop("oneOf")
    validator = jsonschema.Draft202012Validator({**schema, "$ref": "#/$defs/ScenarioV2"})
    bind = import_module("evals.bindings").bind
    validate_gold = import_module("evals.observations").validate_gold
    for case, built in zip(cases, scenarios, strict=True):
        validator.validate(built)
        fixture = bind(built, identity(case))
        validate_gold(built["gold"], fixture.refs, fixture.protected)
        if fixture.input_warnings:
            raise ValueError("Authored transaction/FX fixtures disagree")
    hashes = {
        "cases_sha256": hashlib.sha256(CASES.read_bytes()).hexdigest(),
        "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "base_builder_sha256": hashlib.sha256(
            CASES.with_name("dev_robustness_cases.py").read_bytes()
        ).hexdigest(),
        "materialized_sha256": digest_scenarios(scenarios),
    }
    if verify_manifest and any(
        json.loads(MANIFEST.read_text())[key] != value for key, value in hashes.items()
    ):
        raise ValueError("Pre-fix round-two freeze changed")
    return {
        **hashes,
        "n": len(cases),
        "locales": dict(locales),
        "families": dict(families),
        "features": dict(Counter(tag for case in cases for tag in case["tags"])),
        "outcomes": dict(Counter(case["outcome"] for case in cases)),
        "scripted_messages": dict(Counter(len(case["messages"]) for case in cases)),
    }
