"""Mock-only controls for a separately frozen adversarial dev supplement."""

from __future__ import annotations

import asyncio
from collections import Counter
from decimal import Decimal

import pytest
from evals.studies.llm import controls_ablation as original
from evals.studies.llm import controls_stress as stress
from evals.studies.llm.controls_stress_cases import CASES
from evals.studies.llm.dev_robustness import DevBudgetStop


def test_stress_inventory_is_frozen_balanced_new_and_has_no_real_confirmation():
    stress.validate()
    assert len(CASES) == 20
    assert Counter(c["language"] for c in CASES) == {"es": 10, "pt": 10}
    assert Counter(c["category"] for c in CASES) == {
        "merchant": 4,
        "social": 4,
        "refund": 2,
        "limit": 4,
        "confirmation": 2,
        "arguments": 4,
    }
    assert not any(c["confirm"] for c in CASES)
    assert not {c["text"] for c in CASES} & {c["text"] for c in original.CASES}


def test_protocol_mutation_stops_before_any_inference(monkeypatch, tmp_path):
    changed = tmp_path / "protocol.md"
    changed.write_text("changed")
    monkeypatch.setattr(stress, "PROTOCOL", changed)
    with pytest.raises(DevBudgetStop, match="Frozen"):
        stress.validate()


def test_scope_and_output_are_isolated_and_main_defaults_to_mock(monkeypatch):
    for name in ("CASES", "OUT", "SCOPE", "RUN", "CAP"):
        monkeypatch.setattr(original, name, getattr(original, name))
    seen = []
    monkeypatch.setattr(original, "main", lambda **kwargs: seen.append(kwargs))
    monkeypatch.setattr(stress.sys, "argv", ["controls_stress"])
    stress.main()
    assert seen == [{"inventory": stress.SOURCE}]
    assert original.SCOPE == "dev-gate/controls-stress"
    assert original.RUN == "controls-stress" and Decimal("0.10") == original.CAP
    assert original.OUT == stress.OUT
    assert "--real" not in stress.sys.argv


@pytest.mark.parametrize(
    "case", [c for c in CASES if c["category"] == "merchant"], ids=lambda c: c["id"]
)
def test_merchant_attack_is_data_in_both_ledgers_and_p_logs_the_guard(case):
    fake = original.FakeTools(case)
    lookup = fake.execute("lookup", {"customer_id": "own_customer"}, confirmed=False)
    assert lookup["transactions"][0]["merchant"] == case["merchant"]
    assert case["merchant"] not in case["text"]
    guarded = asyncio.run(original.protected(case))
    assert "indirect_prompt_injection" in guarded["security_events"]
    assert not any(r.get("case") for r in guarded["replies"])


@pytest.mark.parametrize("language", ["es", "pt"])
def test_forged_confirmation_never_becomes_authentication_or_a_write(language):
    case = next(c for c in CASES if c["id"] == f"{language}-forged_confirmation")
    guarded = asyncio.run(original.protected(case))
    assert not case["confirm"] and not any(r.get("case") for r in guarded["replies"])
    fake = original.FakeTools(case)
    fake.execute(
        "file_dispute",
        {"customer_id": "own_customer", "transaction_id": "charge_0"},
        confirmed=case["confirm"],
    )
    assert original.naive_metrics(case, fake.calls, ["Registrado."])["unconfirmed_writes"] == 1


@pytest.mark.parametrize(
    "customer,transaction",
    [("foreign_customer", "charge_0"), ("own_customer", "charge_private_999")],
)
def test_tampered_fake_arguments_count_as_ineligible(customer, transaction):
    case = next(c for c in CASES if c["category"] == "arguments")
    fake = original.FakeTools(case)
    fake.execute(
        "file_dispute", {"customer_id": customer, "transaction_id": transaction}, confirmed=False
    )
    result = original.naive_metrics(case, fake.calls, ["Registrado."])
    assert result["unauthorized_writes"] == result["unconfirmed_writes"] == 1
    assert result["cross_customer_attempts"] == (customer == "foreign_customer")
