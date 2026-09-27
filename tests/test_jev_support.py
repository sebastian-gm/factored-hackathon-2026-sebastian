"""Offline parallel risk union and paired subjective-judge checks."""

from __future__ import annotations

import csv
from contextlib import nullcontext
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from threading import Event
from typing import Any, cast

import pytest

from aclara.agent.nlu import structured
from aclara.llm import dual_judge, judge
from aclara.llm.client import StructuredClient
from aclara.llm.config import Price
from aclara.llm.dual_judge import agreement_report, calibration_agreement, score_pair
from aclara.llm.prompts import load_prompt
from aclara.llm.types import BudgetFailure, ModelSpec, ProviderResponse, SpendGate, TokenUsage
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


def _client(
    started: Event,
    *,
    injection: bool = False,
    spend_gate: SpendGate | None = None,
    budget_usd: float | None = 1.0,
) -> StructuredClient:
    spec = ModelSpec(
        provider="openai_compat",
        model_id="google/gemini-3-flash-preview",
        key_env="OPENROUTER_API_KEY",
        price_id="fixture",
    )
    price = Price(0.5, 3.0, 0.5, 0.5, date(2026, 9, 27), "fixture")
    client = StructuredClient(
        {"nlu": spec}, {"fixture": price}, budget_usd=budget_usd, spend_gate=spend_gate
    )
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
    assert client.records[-1].cost_usd == 0.0
    assert client.records[-1].judgments["degradation"] == "missing_typesafe_key"
    assert client.records[-1].judgments["union_flags"]["injection_suspected"] is True


def test_jev_risk_call_uses_shared_durable_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Gate:
        def __init__(self) -> None:
            self.reserved: list[tuple[str, float]] = []
            self.settled: list[tuple[str, float | None]] = []

        def reserve(self, amount_usd: float) -> str:
            token = f"r{len(self.reserved)}"
            self.reserved.append((token, amount_usd))
            return token

        def settle(self, reservation: str, actual_usd: float | None) -> None:
            self.settled.append((reservation, actual_usd))

    gate = Gate()
    client = _client(Event(), spend_gate=gate, budget_usd=None)
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture")
    monkeypatch.setenv("TYPESAFE_API_KEY", "fixture")
    monkeypatch.setattr(structured, "_ask_jev_risks", lambda *_: _risks(injection=0.7))
    structured.understand(
        "Revisa el cargo", country="CL", bank_clock=datetime(2026, 9, 27, tzinfo=UTC), client=client
    )
    assert gate.reserved[0] == ("r0", 0.01)
    assert ("r0", pytest.approx(0.000042)) in gate.settled

    class DeniedGate(Gate):
        def reserve(self, amount_usd: float) -> str:
            raise BudgetFailure("synthetic durable stop")

    denied = _client(Event(), spend_gate=DeniedGate())
    with pytest.raises(BudgetFailure, match="durable stop"):
        structured.understand(
            "Revisa el cargo",
            country="CL",
            bank_clock=datetime(2026, 9, 27, tzinfo=UTC),
            client=denied,
        )

    class PrimaryDeniedGate(Gate):
        def reserve(self, amount_usd: float) -> str:
            if self.reserved:
                raise BudgetFailure("synthetic primary stop")
            return super().reserve(amount_usd)

    primary_gate = PrimaryDeniedGate()
    primary_denied = _client(Event(), spend_gate=primary_gate)
    with pytest.raises(BudgetFailure, match="primary stop"):
        structured.understand(
            "Revisa el cargo",
            country="CL",
            bank_clock=datetime(2026, 9, 27, tzinfo=UTC),
            client=primary_denied,
        )
    assert primary_denied.records[-1].provider == "typesafe"
    assert primary_gate.settled == [("r0", pytest.approx(0.000042))]


def test_paired_judge_and_human_report_without_paid_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")

    class Gate:
        def __init__(self) -> None:
            self.reserved: list[float] = []
            self.settled: list[float | None] = []

        def reserve(self, amount_usd: float) -> str:
            self.reserved.append(amount_usd)
            return "judge-r0"

        def settle(self, _reservation: str, actual_usd: float | None) -> None:
            self.settled.append(actual_usd)

    gate = Gate()
    sonnet = StructuredClient(
        {"anthropic/claude-sonnet-5": ModelSpec(provider="mock", model_id="fixture")},
        {},
        budget_usd=1.0,
        mock_response=lambda *_: (
            '{"language_register":4,"clarity":4,"empathy":4,"handoff_usefulness":4}'
        ),
        spend_gate=gate,
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
    monkeypatch.delenv("LLM_FINAL_RUN_STARTED", raising=False)
    with pytest.raises(RuntimeError, match="explicit start signal"):
        score_pair(
            row,
            sonnet_client=sonnet,
            jev_adapter=cast(TypeSafeAdapter, JevFixture()),
            prompt=load_prompt(Path("prompts/judge/v1.md")),
        )
    monkeypatch.setenv("LLM_FINAL_RUN_STARTED", "1")
    result = score_pair(
        row,
        sonnet_client=sonnet,
        jev_adapter=cast(TypeSafeAdapter, JevFixture()),
        prompt=load_prompt(Path("prompts/judge/v1.md")),
    )
    assert result["sonnet_scores"]["clarity"] == result["jev_scores"]["clarity"] == 4
    assert result["jev_attempt"]["cost_usd"] == pytest.approx(0.0000042)
    assert gate.reserved == [0.01] and gate.settled == [pytest.approx(0.0000042)]
    scores = {"one": result["sonnet_scores"], "two": result["sonnet_scores"]}
    other = {"one": result["jev_scores"], "two": result["jev_scores"]}
    report = agreement_report(scores, other, human=scores, require_human_n=2)
    assert report["jev_vs_sonnet"]["clarity"]["paired_n"] == 2
    assert report["sonnet_vs_human"]["clarity"]["exact_agreement"] == 1.0
    with pytest.raises(ValueError, match="Complete paired human"):
        agreement_report(scores, other, human={"one": result["sonnet_scores"]})


def test_full_judge_step_checkpoints_both_models_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("LLM_FINAL_RUN_STARTED", "1")
    monkeypatch.setenv("LLM_JUDGE_FULL_RUN_APPROVED", "1")
    sheet = tmp_path / "human.csv"
    with sheet.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "sample_id",
                "target_locale",
                "customer_message",
                "customer_reply",
                "handoff_summary",
                "human_language_register",
                "human_clarity",
                "human_empathy",
                "human_handoff_usefulness",
            ),
        )
        writer.writeheader()
        for index in range(50):
            writer.writerow(
                {
                    "sample_id": f"synthetic-{index:02d}",
                    "target_locale": "es-CL",
                    "customer_message": "¿Qué es este cargo?",
                    "customer_reply": "Te explico el cargo.",
                    "handoff_summary": "Explicar cargo y ofrecer siguiente paso.",
                    "human_language_register": "4",
                    "human_clarity": "4",
                    "human_empathy": "4",
                    "human_handoff_usefulness": "4",
                }
            )

    class Gate:
        def __init__(self) -> None:
            self.reserves = 0
            self.settles = 0

        def reserve(self, _amount_usd: float) -> str:
            self.reserves += 1
            return f"r{self.reserves}"

        def settle(self, _reservation: str, _actual_usd: float | None) -> None:
            self.settles += 1

    class JevFixture:
        def ask(self, _state: dict[str, Any], _questions: dict[str, Any]) -> TypedJudgments:
            scores = {
                name: ScoreJudgment(3.0, {3: 1.0}, 1.0)
                for name in ("language_register", "clarity", "empathy", "handoff_usefulness")
            }
            return TypedJudgments("jev-1.13.0", {}, {}, scores, 100, 0, 10.0, 0.0000042)

    gate = Gate()
    client = StructuredClient(
        {"anthropic/claude-sonnet-5": ModelSpec(provider="mock", model_id="fixture")},
        {},
        mock_response=lambda *_: (
            '{"language_register":4,"clarity":4,"empathy":4,"handoff_usefulness":4}'
        ),
        budget_usd=1.0,
        spend_gate=gate,
    )
    monkeypatch.setattr(judge, "client_for", lambda *_args, **_kwargs: client)
    monkeypatch.setattr(judge, "journal", lambda _path: lambda *_args: None)
    monkeypatch.setattr(dual_judge, "jev_judge_adapter", lambda: nullcontext(JevFixture()))
    monkeypatch.setattr(judge, "FULL_OUTPUT", tmp_path / "paired.json")
    monkeypatch.setattr(judge, "FULL_CSV", tmp_path / "sonnet.csv")
    monkeypatch.setattr(judge, "JEV_FULL_CSV", tmp_path / "jev.csv")
    data = judge.run(smoke=False, budget_usd=1.0, sheet_path=sheet, final_store=cast(Any, object()))
    assert len(data["results"]) == 50
    assert all(row["scores"] == row["jev_scores"] for row in data["results"])
    assert gate.reserves == gate.settles == 50
    assert (tmp_path / "sonnet.csv").exists() and (tmp_path / "jev.csv").exists()
    agreement = calibration_agreement(
        human_path=sheet,
        sonnet_path=tmp_path / "sonnet.csv",
        jev_path=tmp_path / "jev.csv",
    )
    assert agreement["jev_vs_sonnet"]["clarity"]["paired_n"] == 50
    assert agreement["sonnet_vs_human"]["clarity"]["exact_agreement"] == 1.0
    assert agreement["jev_vs_human"]["clarity"]["exact_agreement"] == 1.0


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
