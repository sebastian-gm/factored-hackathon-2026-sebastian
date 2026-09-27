"""Checks that lane interface snapshots stay aligned with runtime models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from aclara.agent.contracts import NluFrame, ResponsePlan, TransactionView
from aclara.agent.nlu import Intent
from aclara.api.app import app
from aclara.evals.schema import ScenarioSuite

ROOT = Path(__file__).resolve().parents[1]
INTERFACES = ROOT / "contracts" / "interfaces"


def test_openapi_snapshot_matches_fastapi_routes() -> None:
    snapshot = json.loads((INTERFACES / "openapi.json").read_text(encoding="utf-8"))
    assert snapshot == app.openapi()


def test_scenario_contract_snapshot_validates_the_suite() -> None:
    payload = yaml.safe_load((ROOT / "evals" / "dev_scenarios.yaml").read_text(encoding="utf-8"))
    suite = ScenarioSuite.model_validate(payload)
    snapshot = json.loads((INTERFACES / "scenario-suite.schema.json").read_text(encoding="utf-8"))
    legacy = ScenarioSuite.model_json_schema()
    assert snapshot["$defs"]["ScenarioSuiteV1"] == {
        key: value for key, value in legacy.items() if key != "$defs"
    }
    for name, definition in legacy["$defs"].items():
        assert snapshot["$defs"][name] == definition
    assert len(suite.scenarios) == 32


def test_versioned_scenario_schema_accepts_v1_and_reactive_v2() -> None:
    # JSON Schema is an authoring dependency; the runtime remains on v1 until
    # the lead implements v2. Run with `uv run --with jsonschema pytest ...`.
    jsonschema = pytest.importorskip("jsonschema")
    snapshot = json.loads((INTERFACES / "scenario-suite.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(snapshot)
    validator = jsonschema.Draft202012Validator(snapshot, format_checker=jsonschema.FormatChecker())
    validator.validate(yaml.safe_load((ROOT / "evals/dev_scenarios.yaml").read_text()))
    scenario = {
        "id": "pt.normal.fixture",
        "language": "pt",
        "turns": [{"message": "Não reconheço esta compra."}],
        "expected": "dispute_filed",
    }
    payload = {
        "version": 2,
        "description": "Project-generated schema fixture",
        "scenarios": [scenario],
    }
    validator.validate(payload)  # All v2 metadata is additive and optional.
    scenario.update(
        persona={"customer_ref": "test-persona-001", "split": "test"},
        bank_clock="2026-06-18T06:00:00Z",
        faults=[],
        reactive_replies={
            "choose_txn": [{"choose_ref": "target"}],
            "confirm_action": [{"confirm": True}],
            "default": [{"message": "Não sei."}],
        },
        gold={
            "outcome": "dispute_filed",
            "expected_transaction_ref": "target",
            "required_actions": [{"type": "create_dispute", "target_ref": "target"}],
            "forbidden_actions": ["promise_refund"],
            "must_escalate": False,
            "reason_codes": ["DSP-01", "DSP-02", "DSP-07"],
            "required_handoff_fields": [],
            "must_not_disclose": ["persona.document_number"],
            "in_scope": True,
            "written_rule_basis": "Approved Purchase, age 10 days, USD 80; brief section 9.",
        },
    )
    validator.validate(payload)
    scenario["persona"]["split"] = "train"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(payload)
    scenario["persona"]["split"] = "test"
    scenario["bank_clock"] = "2026-06-18T06:00:00"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(payload)
    scenario["bank_clock"] = "2026-06-18T06:00:00Z"
    scenario["gold"]["reason_codes"] = ["INVENTED-01"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(payload)


def test_nlu_frame_is_typed_and_bounded() -> None:
    frame = NluFrame(language="es", intent=Intent.DISPUTE_CHARGE, confidence=0.93)
    assert frame.intent is Intent.DISPUTE_CHARGE
    with pytest.raises(ValidationError):
        NluFrame(language="en", intent=Intent.DISPUTE_CHARGE, confidence=1.1)


def test_response_plan_requires_verified_readback() -> None:
    with pytest.raises(ValidationError, match="successful read-back"):
        ResponsePlan(
            response_type="report_case",
            outcome="dispute_filed",
            reply="Dispute filed",
            case={
                "case_id": "DSP-TEST",
                "transaction_handle": "txn_1",
                "status": "received",
                "policy_rules": ["D-01"],
                "created_at": "2026-06-18T06:00:00Z",
            },
            verified=False,
        )


def test_serving_contract_matches_api_transaction_view() -> None:
    contract = yaml.safe_load((INTERFACES / "serving_transaction.yaml").read_text(encoding="utf-8"))
    assert list(contract["columns"]) == list(TransactionView.model_fields)
    assert {"customer_id", "product_id", "transaction_id"}.isdisjoint(contract["columns"])


def test_gold_contract_requires_owned_join_and_never_exposes_sensitive_fields() -> None:
    contract = yaml.safe_load(
        (INTERFACES / "gold_transaction_facts.yaml").read_text(encoding="utf-8")
    )
    assert contract["layer"] == "gold"
    assert contract["primary_key"] == ["transaction_id"]
    assert any("customer_id = transactions.customer_id" in rule for rule in contract["joins"])
    assert all(
        column["llm_exposure"] in {"never", "masked"} for column in contract["columns"].values()
    )
