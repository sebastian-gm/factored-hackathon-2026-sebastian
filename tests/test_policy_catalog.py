from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from scripts.generate_policy_catalog import render

from aclara.bank.repository import TransactionRepository
from aclara.policy.engine import evaluate
from aclara.policy.rules import catalog
from aclara.settings import Settings


def test_catalog_matches_brief_ids_and_real_test_references() -> None:
    schema = json.loads(Path("contracts/scenario-v2-definitions.json").read_text())
    identifiers = schema["GoldLabels"]["properties"]["reason_codes"]["items"]["enum"]
    _, rules = catalog()
    assert len(rules) == len({r.id for r in rules})
    assert {r.id for r in rules} == set(identifiers)
    for rule in rules:
        for test in rule.tests:
            path, name = test.split("::")
            assert f"def {name}(" in (Path("tests") / path).read_text()
    assert Path("docs/policy-catalog.md").read_text() == render()


def test_pending_age_and_dispute_boundaries() -> None:
    clock = Settings().bank_clock
    row = TransactionRepository()._rows[0]
    business_day = (clock - timedelta(hours=6, microseconds=1)).date()

    def decide(**changes):
        return evaluate(replace(row, **changes), clock, is_dispute=True)

    assert decide(
        transaction_status="Pending", process_date=business_day - timedelta(days=14)
    ).rule_ids == ("TXN-01",)
    assert decide(
        transaction_status="Pending", process_date=business_day - timedelta(days=15)
    ).rule_ids == ("TXN-02",)
    assert decide(process_date=business_day - timedelta(days=91)).rule_ids == ("DSP-01",)
    assert decide(process_date=business_day - timedelta(days=85)).rule_ids == ("BRD-01",)
    assert decide(amount=950).rule_ids == ("BRD-01",)
    assert decide(amount=1051).rule_ids == ("DSP-07",)
    assert decide(currency="BRL").rule_ids == ("BRD-01",)
    assert decide(transaction_type="Adjustment").rule_ids == ("DSP-03",)
    assert decide(transaction_type="Transfer").rule_ids == ("DSP-04",)
    assert decide().decision == "eligible"
