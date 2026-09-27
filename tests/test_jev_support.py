"""Offline parallel risk union and paired subjective-judge checks."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from threading import Event
from typing import Any, cast

import pytest

from aclara.agent.nlu import structured
from aclara.llm.client import StructuredClient
from aclara.llm.config import Price
from aclara.llm.dual_judge import agreement_report, score_pair
from aclara.llm.prompts import load_prompt
from aclara.llm.types import ModelSpec, ProviderResponse, TokenUsage
from aclara.llm.typesafe import ScoreJudgment, TypedJudgments, TypeSafeAdapter
from aclara.llm.typesafe_questions import RISK_CUES


class _GeminiFixture:
    def __init__(self, started: Event, *, injection: bool = False) -> None:
        self.started = started
        self.injection = injection

    def complete(self, *_args: Any) -> ProviderResponse:
        self.started.set()
        value = str(self.injection).lower()
        return ProviderResponse(
            text=(
                '{"language":"es","intent":"charge_inquiry","intent_confidence":0.9,'
                f'"injection_suspected":{value}' + "}"
            ),
            model_id="google/gemini-3-flash-preview",
            usage=TokenUsage(input_tokens=100, output_tokens=20),
        )


def _client(started: Event, *, injection: bool = False) -> StructuredClient:
    spec = ModelSpec(
        provider="openai_compat",
        model_id="google/gemini-3-flash-preview",
        key_env="OPENROUTER_API_KEY",
        price_id="fixture",
    )
    price = Price(0.5, 3.0, 0.5, 0.5, date(2026, 9, 27), "fixture")
    client = StructuredClient({"nlu": spec}, {"fixture": price}, budget_usd=1.0)
    client._adapters["openai_compat"] = cast(Any, _GeminiFixture(started, injection=injection))
    return client


def _risks(*, injection: float, distress: float = 0.0) -> TypedJudgments:
    probabilities = {name: 0.0 for name in RISK_CUES}
    probabilities.update(injection_suspected=injection, distress=distress)
    return TypedJudgments("jev-1.13.0", {}, probabilities, {}, 1000, 0, 12.0, 0.000042)


def test_jev_risks_run_parallel_union_and_record_raw_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = Event()
    client = _client(started)
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture")
    monkeypatch.setenv("TYPESAFE_API_KEY", "fixture")

    def ask(_message: str, _key: str) -> TypedJudgments:
        assert started.wait(1), "Gemini and Jev must overlap"
        return _risks(injection=0.8, distress=0.9)

    monkeypatch.setattr(structured, "_ask_jev_risks", ask)
    result = structured.understand(
        "No reconozco el cargo",
        country="CL",
        bank_clock=datetime(2026, 9, 27, tzinfo=UTC),
        client=client,
    )
    assert not result.degraded
    assert result.extracted.injection_suspected and result.extracted.distress
    assert result.frame.intent.value == "charge_inquiry"
    record = client.records[-1]
    assert record.provider == "typesafe" and record.status == "valid"
    assert record.judgments is not None
    assert record.judgments["gemini_raw_flags"]["injection_suspected"] is False
    assert record.judgments["gemini_raw_probabilities"]["injection_suspected"] is None
    assert record.judgments["jev_raw_probabilities"]["injection_suspected"] == 0.8
    assert record.judgments["union_flags"]["injection_suspected"] is True
    assert client.spent_usd == pytest.approx(0.000152)
    assert client.valid_json_rate == 1.0  # Typed Jev calls are not JSON-schema attempts.
    assert asdict(record)["judgments"]["jev_raw_probabilities"]["distress"] == 0.9


def test_jev_failure_logs_degradation_and_keeps_gemini_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(Event(), injection=True)
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture")
    monkeypatch.setenv("TYPESAFE_API_KEY", "fixture")

    def fail(_message: str, _key: str) -> TypedJudgments:
        raise TimeoutError("synthetic timeout")

    monkeypatch.setattr(structured, "_ask_jev_risks", fail)
    result = structured.understand(
        "Revisa el cargo", country="CL", bank_clock=datetime(2026, 9, 27, tzinfo=UTC), client=client
    )
    assert not result.degraded and result.extracted.injection_suspected
    record = client.records[-1]
    assert record.status == "provider_error"
    assert record.judgments is not None
    assert record.judgments["degradation"] == "typesafe_timeout"
    assert record.judgments["union_flags"]["injection_suspected"] is True
    assert client.spent_usd >= 0.01  # Unknown-cost Jev attempt retains its reserve.


def test_missing_jev_key_keeps_gemini_result_and_records_degradation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(Event(), injection=True)
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture")
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    result = structured.understand(
        "Revisa el cargo", country="CL", bank_clock=datetime(2026, 9, 27, tzinfo=UTC), client=client
    )
    assert not result.degraded and result.extracted.injection_suspected
    assert client.records[-1].judgments is not None
    assert client.records[-1].status == "skipped"
    assert client.records[-1].judgments["degradation"] == "missing_typesafe_key"
    assert client.records[-1].judgments["union_flags"]["injection_suspected"] is True


def test_paired_judge_and_human_report_without_paid_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    sonnet = StructuredClient(
        {"anthropic/claude-sonnet-5": ModelSpec(provider="mock", model_id="fixture")},
        {},
        budget_usd=1.0,
        mock_response=lambda *_: (
            '{"language_register":4,"clarity":4,"empathy":4,"handoff_usefulness":4}'
        ),
    )

    class JevFixture:
        def ask(self, _state: dict[str, Any], _questions: dict[str, Any]) -> TypedJudgments:
            scores = {
                name: ScoreJudgment(3.0, {3: 1.0}, 1.0)
                for name in ("language_register", "clarity", "empathy", "handoff_usefulness")
            }
            return TypedJudgments("jev-1.13.0", {}, {}, scores, 100, 0, 10.0, 0.0000042)

    row = {
        "target_locale": "es-CL",
        "customer_message": "¿Qué es este cargo?",
        "customer_reply": "Te explico el cargo.",
        "handoff_summary": "Consulta sobre cargo; explicar y ofrecer disputa.",
    }
    monkeypatch.delenv("FINAL_RUN_START_APPROVED", raising=False)
    with pytest.raises(RuntimeError, match="explicit final-run start"):
        score_pair(
            row,
            sonnet_client=sonnet,
            jev_adapter=cast(TypeSafeAdapter, JevFixture()),
            prompt=load_prompt(Path("prompts/judge/v1.md")),
        )
    monkeypatch.setenv("FINAL_RUN_START_APPROVED", "1")
    result = score_pair(
        row,
        sonnet_client=sonnet,
        jev_adapter=cast(TypeSafeAdapter, JevFixture()),
        prompt=load_prompt(Path("prompts/judge/v1.md")),
    )
    assert result["sonnet_scores"]["clarity"] == result["jev_scores"]["clarity"] == 4
    assert result["jev_attempt"]["cost_usd"] == pytest.approx(0.0000042)
    scores = {"one": result["sonnet_scores"], "two": result["sonnet_scores"]}
    other = {"one": result["jev_scores"], "two": result["jev_scores"]}
    report = agreement_report(scores, other, human=scores, require_human_n=2)
    assert report["jev_vs_sonnet"]["clarity"]["paired_n"] == 2
    assert report["sonnet_vs_human"]["clarity"]["exact_agreement"] == 1.0
    with pytest.raises(ValueError, match="Complete paired human"):
        agreement_report(scores, other, human={"one": result["sonnet_scores"]})


def test_external_judgment_uses_durable_gate_and_journal(monkeypatch):
    from aclara.llm.final_run import FinalBudgetStop, FinalSpendGate
    from aclara.llm.types import BudgetFailure

    class Gate:
        def __init__(self):
            self.calls = []

        def reserve(self, amount):
            self.calls.append(("reserve", amount))
            return str(len(self.calls))

        def settle(self, token, actual):
            self.calls.append(("settle", actual))

    gate = Gate()
    client = _client(Event())
    client.budget_usd = None
    client.spend_gate = gate
    records = []
    client._response_record = lambda call, result: records.append((call, result))
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture")
    monkeypatch.setenv("TYPESAFE_API_KEY", "fixture")
    monkeypatch.setattr(structured, "_ask_jev_risks", lambda *_: _risks(injection=0.9))
    structured.understand(
        "Cargo de ensayo", country="MX", bank_clock=datetime.now(UTC), client=client
    )
    assert [c[0] for c in gate.calls] == ["reserve", "reserve", "settle", "settle"]
    assert gate.calls[-1][1] == 0.000042
    assert records[-1][0].provider == "typesafe"
    assert records[-1][1]["union_flags"]["injection_suspected"] is True

    class Denied:
        def reserve(self, amount):
            raise BudgetFailure("fixture exhausted")

        def settle(self, token, actual):
            raise AssertionError("No request permitted")

    client.spend_gate = FinalSpendGate(Denied())
    before = len(client.records)
    with pytest.raises(FinalBudgetStop):
        structured.understand("Cargo", country="MX", bank_clock=datetime.now(UTC), client=client)
    assert len(client.records) == before
