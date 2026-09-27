"""Authored mocks only: these tests never load frozen inputs or call providers."""

import json

import pytest
from test_llm_budget import Answer

from aclara.llm.client import StructuredClient
from aclara.llm.config import Price
from aclara.llm.final_run import FinalBudgetStop, FinalSpendGate, client_for, journal
from aclara.llm.types import BudgetFailure, ModelFailure, ModelSpec, ProviderResponse, TokenUsage
from aclara.ops.store import Store


def test_final_start_gate_precedes_frozen_access(monkeypatch):
    from evals import heldout

    monkeypatch.delenv("LLM_FINAL_RUN_STARTED", raising=False)
    monkeypatch.setattr("sys.argv", ["heldout", "--run", "--final"])
    monkeypatch.setattr(heldout, "open_serving", lambda: pytest.fail("must not open serving"))
    monkeypatch.setattr(heldout, "load", lambda _: pytest.fail("must not open frozen input"))
    with pytest.raises(RuntimeError, match="start signal"):
        heldout.main()
    with pytest.raises(RuntimeError, match="start signal"):
        client_for("default", Store())


def test_fallback_shares_reservations_and_budget_failure_is_fatal(monkeypatch, tmp_path):
    from datetime import date

    from aclara.llm import final_run

    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("FIXTURE_KEY", "fixture")
    monkeypatch.setattr(final_run, "ROOT", tmp_path)
    attempts = []
    settled = []

    class Gate:
        left = 3

        def reserve(self, amount):
            if self.left == 0:
                raise BudgetFailure("cap")
            self.left -= 1
            return "reservation"

        def settle(self, token, amount):
            settled.append(amount)

    class Adapter:
        def complete(self, spec, *_):
            assert spec.price_ceiling == (1, 1)
            attempts.append(spec.model_id)
            if spec.model_id == "primary":
                raise ModelFailure("fixture")
            return ProviderResponse('{"value":"ok"}', "alternate", TokenUsage(10, 2))

    path = tmp_path / "artifacts/calls.jsonl"
    client = StructuredClient(
        {
            route: ModelSpec("openai_compat", route, key_env="FIXTURE_KEY", price_id="fixture")
            for route in ("primary", "alternate")
        },
        {"fixture": Price(1, 1, 1, 1, date(2026, 9, 27), "https://fixture.invalid")},
        budget_usd=None,
        spend_gate=FinalSpendGate(Gate()),
        fallback_routes={"primary": "alternate"},
        response_record=journal(path),
    )
    client._adapters["openai_compat"] = Adapter()
    assert client.generate("primary", "system", "user", Answer, prompt_id="fixture").value == "ok"
    assert attempts == ["primary", "primary", "alternate"]
    assert settled[:2] == [None, None] and settled[2] > 0
    with pytest.raises(FinalBudgetStop):
        client.generate("primary", "system", "user", Answer, prompt_id="fixture")
    assert len(attempts) == 3
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert [r["validated_output"] for r in rows] == [None, None, {"value": "ok"}]
    assert path.stat().st_mode & 0o777 == 0o600
