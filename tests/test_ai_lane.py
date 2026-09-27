"""Fixture-only checks for model failure, localization, and reply safety."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import cast

import pytest
from pydantic import BaseModel, ConfigDict

from aclara.agent.ai import AgentAI
from aclara.agent.contracts import ResponsePlan
from aclara.agent.nlg.builder import build_reply
from aclara.agent.nlg.grounding import AllowedFact, redact_for_model, scan_dlp, verify_draft
from aclara.agent.nlu.structured import (
    ExtractedNlu,
    parse_amount,
    parse_relative_date,
    postprocess,
    resolve_currency,
    understand,
)
from aclara.agent.runtime import Runtime
from aclara.llm.client import StructuredClient
from aclara.llm.comparison import ComparisonCase, evaluate_model, markdown_table
from aclara.llm.config import Price, load_models, load_prices
from aclara.llm.prompts import Prompt
from aclara.llm.providers import OpenAICompat
from aclara.llm.round_one import _cases
from aclara.llm.types import ModelFailure, ModelSpec, ProviderResponse, TokenUsage
from aclara.settings import Settings


class _Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str


class _OptionalAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str | None = None


def test_openrouter_request_uses_strict_schema_and_privacy_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: int) -> BytesIO:
        observed["body"] = json.loads(request.data)  # type: ignore[attr-defined]
        observed["timeout"] = timeout
        return BytesIO(
            b'{"id":"gen-fixture","model":"served-model","choices":[{"message":{"content":"{\\"value\\":null}"},"finish_reason":"stop"}],"usage":{"prompt_tokens":12,"completion_tokens":4,"cost":0.000123}}'
        )

    monkeypatch.setattr("aclara.llm.providers.urlopen", fake_urlopen)
    response = OpenAICompat().complete(
        ModelSpec(
            provider="openai_compat",
            model_id="candidate",
            base_url="https://openrouter.ai/api/v1",
        ),
        "system",
        "fixture",
        _OptionalAnswer,
        "test-key",
    )
    body = observed["body"]
    assert isinstance(body, dict)
    assert body["provider"] == {"data_collection": "deny", "zdr": True, "require_parameters": True}
    schema = body["response_format"]["json_schema"]["schema"]
    assert schema["required"] == ["value"]
    assert "default" not in schema["properties"]["value"]
    assert response.model_id == "served-model"
    assert response.usage.input_tokens == 12
    assert response.billed_cost_usd == 0.000123
    assert response.generation_id == "gen-fixture"
    assert observed["timeout"] == 20


def test_openrouter_provider_pin_and_output_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: int) -> BytesIO:
        observed["body"] = json.loads(request.data)  # type: ignore[attr-defined]
        observed["timeout"] = timeout
        return BytesIO(
            b'{"choices":[{"message":{"content":"{\\"value\\":\\"ok\\"}"},"finish_reason":"stop"}],"usage":{"cost":0.001}}'
        )

    monkeypatch.setattr("aclara.llm.providers.urlopen", fake_urlopen)
    OpenAICompat().complete(
        ModelSpec(
            provider="openai_compat",
            model_id="deepseek/example",
            base_url="https://openrouter.ai/api/v1",
            provider_only=("wafer/fast",),
            max_output_tokens=2048,
            reasoning_effort="low",
            timeout_seconds=60,
        ),
        "system",
        "fixture",
        _Answer,
        "test-key",
    )
    body = observed["body"]
    assert isinstance(body, dict)
    assert body["provider"]["only"] == ["wafer/fast"]
    assert body["provider"]["allow_fallbacks"] is False
    assert body["max_tokens"] == 2048
    assert body["reasoning"] == {"effort": "low"}
    assert observed["timeout"] == 60


def test_round_one_uses_all_current_synthetic_dev_scenarios() -> None:
    cases, suite_hash = _cases()
    assert len(cases) == 32
    assert len(suite_hash) == 64
    assert all(
        case.scored_slot_keys == ("amount_value", "currency", "merchant_expr") for case in cases
    )
    assert sum(case.gold_intent == "dispute_charge" for case in cases) == 2
    assert sum(bool(case.gold_slots) for case in cases) == 15


def test_sebastian_recognition_rule_and_independent_hard_dev_suite() -> None:
    from collections import Counter

    from aclara.agent.nlu.rules import classify_nlu
    from aclara.llm.round_two import load_cases, sample_for

    assert classify_nlu("No reconozco esta compra").intent.value == "charge_inquiry"
    assert classify_nlu("No fui yo quien compró esto").intent.value == "dispute_charge"
    assert classify_nlu("Não reconheço essa cobrança").intent.value == "charge_inquiry"
    assert classify_nlu("Não autorizei essa cobrança").intent.value == "dispute_charge"
    cases, metadata, suite_hash = load_cases()
    assert len(cases) == 150
    assert len(suite_hash) == 64
    assert Counter(case.country for case in cases) == {
        "MX": 30,
        "CO": 30,
        "AR": 30,
        "BR": 30,
        "": 30,
    }
    assert len(sample_for("anthropic/claude-opus-5", cases)) == 30
    old_cases, _ = _cases()
    assert not {case.message for case in cases} & {case.message for case in old_cases}
    assert {tag for tags in metadata.values() for tag in tags["tags"]} >= {
        "slang",
        "false_friend",
        "code_switch",
        "vague_date",
        "vague_amount",
        "pesos",
        "injection",
    }


def test_round_two_wilson_interval_handles_zero_and_perfect_success() -> None:
    from aclara.llm.round_two_report import wilson

    assert wilson(0, 150)[0] == 0
    assert 0 < wilson(0, 150)[1] < 0.03
    assert 0.97 < wilson(150, 150)[0] < 1
    assert wilson(150, 150)[1] == 1


def test_openrouter_billed_cost_takes_priority_over_catalog_estimate() -> None:
    spec = ModelSpec(provider="openai_compat", model_id="candidate", price_id="candidate")
    price = Price(1.0, 1.0, 1.0, 1.0, datetime(2026, 9, 26, tzinfo=UTC).date(), "test")
    client = StructuredClient({"candidate": spec}, {"candidate": price})
    response = ProviderResponse("{}", "candidate", TokenUsage(100, 100), billed_cost_usd=0.000123)
    assert client._cost(spec, response) == 0.000123


def test_same_case_comparison_reports_aggregate_metrics() -> None:
    clock = datetime(2026, 6, 18, 6, tzinfo=UTC)
    cases = [
        ComparisonCase(
            "No reconozco 250 dólares",
            "CO",
            clock,
            "dispute_charge",
            {"amount_value": "250", "currency": "USD"},
            "es",
        ),
        ComparisonCase(
            "Não reconheço 300 reais",
            "BR",
            clock,
            "dispute_charge",
            {"amount_value": "300", "currency": "BRL"},
            "pt",
        ),
    ]
    answers = iter(
        [
            '{"language":"es","intent":"dispute_charge","intent_confidence":0.9,"amount_expr":"250","currency_expr":"dólares"}',
            '{"language":"pt","intent":"dispute_charge","intent_confidence":0.9,"amount_expr":"300","currency_expr":"reais"}',
        ]
    )
    client = StructuredClient(
        {"candidate": ModelSpec(provider="mock", model_id="fixture-model")},
        {},
        mock_response=lambda _s, _u, _t: next(answers),
    )
    prompt = Prompt("nlu", "v1", "nlu", "system", "hash")
    row = evaluate_model("candidate", cases, client, prompt)
    assert row.cases == 2
    assert row.intent_accuracy == 1.0
    assert row.slot_f1 == 1.0
    assert row.valid_json_rate == 1.0
    assert row.cost_per_case_usd == 0.0
    assert "fixture-model" in markdown_table([row])


def test_structured_retry_records_invalid_output_without_content() -> None:
    responses = iter(['{"wrong":"shape"}', '{"value":"ok"}'])
    client = StructuredClient(
        {"nlu": ModelSpec(provider="mock", model_id="mock")},
        {},
        mock_response=lambda _s, _u, _t: next(responses),
    )
    result = client.generate("nlu", "system", "fixture", _Answer, prompt_id="nlu@v1")
    assert result.value == "ok"
    assert [record.status for record in client.records] == ["invalid_json", "valid"]
    assert client.valid_json_rate == 0.5
    assert "fixture" not in repr(client.records)


def test_json_validity_counts_truncated_attempts() -> None:
    class TruncateOnce:
        calls = 0

        def complete(
            self,
            spec: ModelSpec,
            system: str,
            user: str,
            schema: type[BaseModel],
            key: str,
        ) -> ProviderResponse:
            self.calls += 1
            if self.calls == 1:
                return ProviderResponse("", spec.model_id, TokenUsage(output_tokens=1024), "length")
            return ProviderResponse('{"value":"ok"}', spec.model_id, TokenUsage(), "stop")

    client = StructuredClient({"nlu": ModelSpec(provider="mock", model_id="mock")}, {})
    client._adapters["mock"] = TruncateOnce()
    assert client.generate("nlu", "system", "fixture", _Answer, prompt_id="nlu@v1").value == "ok"
    assert [record.status for record in client.records] == ["refusal", "valid"]
    assert client.valid_json_rate == 0.5


def test_real_call_requires_approval_before_adapter_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LLM_REAL_CALLS_APPROVED", raising=False)
    client = StructuredClient(
        {
            "nlu": ModelSpec(
                provider="openai_compat",
                model_id="example/model",
                key_env="OPENROUTER_API_KEY",
                base_url="https://openrouter.ai/api/v1",
                price_id="example",
            )
        },
        {},
    )
    with pytest.raises(ModelFailure, match="disabled"):
        client.generate("nlu", "system", "fixture", _Answer, prompt_id="nlu@v1")
    assert client.records == []


def test_budget_reserve_blocks_a_real_call_before_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    client = StructuredClient(
        {
            "nlu": ModelSpec(
                provider="openai_compat",
                model_id="fixture",
                key_env="OPENROUTER_API_KEY",
                base_url="https://openrouter.ai/api/v1",
                price_id="fixture",
            )
        },
        {
            "fixture": Price(
                1.0,
                1.0,
                1.0,
                1.0,
                datetime(2026, 9, 26, tzinfo=UTC).date(),
                "https://example.test/pricing",
            )
        },
        budget_usd=0.000001,
    )
    with pytest.raises(ModelFailure, match="Insufficient"):
        client.generate("nlu", "system", "fixture", _Answer, prompt_id="nlu@v1")
    assert client.records == []


def test_unknown_provider_bill_uses_budget_reserve_without_reporting_case_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingAdapter:
        def complete(
            self,
            spec: ModelSpec,
            system: str,
            user: str,
            schema: type[BaseModel],
            key: str,
        ) -> ProviderResponse:
            raise ModelFailure("Synthetic provider failure")

    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture-only")
    client = StructuredClient(
        {
            "nlu": ModelSpec(
                provider="openai_compat",
                model_id="fixture",
                key_env="OPENROUTER_API_KEY",
                price_id="fixture",
            )
        },
        {
            "fixture": Price(
                1.0,
                1.0,
                1.0,
                1.0,
                datetime(2026, 9, 26, tzinfo=UTC).date(),
                "https://example.test/pricing",
            )
        },
        budget_usd=0.1,
    )
    client._adapters["openai_compat"] = FailingAdapter()
    with pytest.raises(ModelFailure, match="Synthetic provider failure"):
        client.generate("nlu", "system", "fixture", _Answer, prompt_id="nlu@v2")
    assert len(client.records) == 2
    assert all(record.cost_usd is None for record in client.records)
    assert client.spent_usd > 0  # Conservative guard, not a billed per-case cost.
    assert client.valid_json_rate == 0.0


def test_local_models_and_dated_prices_are_loadable() -> None:
    models = load_models(Path("config/models.yaml"))
    prices = load_prices(Path("config/pricing.yaml"))
    assert models["nlu"].provider == "mock"
    assert models["phrase"].provider == "mock"
    assert models["default"].provider == "openai_compat"
    assert models["default"].model_id == "google/gemini-3-flash-preview"
    assert models["default"].price_id in prices
    assert models["openrouter_qwen"].key_env == "OPENROUTER_API_KEY"
    assert all(price.source_url.startswith("https://") for price in prices.values())


def test_selected_route_applies_only_when_real_provider_is_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LLM_MODEL_ROUTE", raising=False)
    runtime = cast(Runtime, object())  # Constructor only stores the runtime.
    mock = AgentAI(Settings(llm_provider="mock"), runtime)
    assert mock.client.models["nlu"].provider == "mock"
    assert mock.client.models["phrase"].provider == "mock"
    selected = AgentAI(Settings(llm_provider="openai_compat"), runtime)
    assert selected.client.models["nlu"].model_id == "google/gemini-3-flash-preview"
    assert selected.client.models["phrase"].model_id == "google/gemini-3-flash-preview"


def test_deterministic_normalization_and_currency_clarification() -> None:
    clock = datetime(2026, 6, 18, 6, tzinfo=UTC)
    assert parse_relative_date("anteayer", clock) == (
        datetime(2026, 6, 15, tzinfo=UTC).date(),
        datetime(2026, 6, 15, tzinfo=UTC).date(),
    )
    assert str(parse_amount("dos? 2 palos", "CO")) == "2000000"
    assert str(parse_amount("3 lucas", "AR")) == "3000"
    assert str(parse_amount("4 contos", "BR")) == "4000"
    assert str(parse_amount("1.234,56 reais", "BR")) == "1234.56"
    assert str(parse_amount("dos lucas", "AR")) == "2000"
    assert resolve_currency("500 pesos", "MX") == (None, True)
    assert resolve_currency("500 pesos", "CO") == ("COP", False)
    result = postprocess(
        ExtractedNlu(
            language="es",
            intent="dispute_charge",
            intent_confidence=0.9,
            amount_expr="500",
            currency_expr="pesos",
            date_expr="anteayer",
        ),
        country="MX",
        bank_clock=clock,
    )
    assert result.clarification == "currency"
    assert result.slots.date_start == datetime(2026, 6, 15, tzinfo=UTC).date()


def test_false_friend_and_degraded_path() -> None:
    clock = datetime(2026, 6, 18, 6, tzinfo=UTC)
    result = postprocess(
        ExtractedNlu(
            language="pt",
            intent="charge_inquiry",
            intent_confidence=0.9,
            merchant_expr="cargo",
            out_of_scope_topic="job",
        ),
        country="BR",
        bank_clock=clock,
    )
    assert result.frame.intent.value == "out_of_scope"
    fallback = understand("Não reconheço essa cobrança", country="BR", bank_clock=clock)
    assert fallback.degraded
    assert fallback.frame.intent.value == "charge_inquiry"
    assert (
        understand(
            "No fui yo quien hizo la compra", country="CO", bank_clock=clock
        ).frame.intent.value
        == "dispute_charge"
    )
    client = StructuredClient(
        {"nlu": ModelSpec(provider="mock", model_id="mock")},
        {},
        mock_response=lambda _s, _u, _t: (
            '{"language":"es","intent":"out_of_scope","intent_confidence":0.8}'
        ),
    )
    human = understand(
        "Quiero hablar con una persona", country="CO", bank_clock=clock, client=client
    )
    assert human.frame.intent.value == "human_request"


def test_grounding_and_dlp_force_template_fallback() -> None:
    facts = (AllowedFact(id="F1", value="USD 250.00 Mercado Verde txn_2", source="fixture"),)
    assert verify_draft(
        "Vi USD 250.00 em Mercado Verde.", ["F1"], facts, known_merchants=("Mercado Verde",)
    ).safe
    unsafe = verify_draft(
        "Vi USD 900.00 em Mercado Verde.", ["F1"], facts, known_merchants=("Mercado Verde",)
    )
    assert "uncited_number" in unsafe.violations
    assert "uncited_number" in verify_draft("Vi USD 25.00.", ["F1"], facts).violations
    assert "negated_status" in scan_dlp("No fue aprobada.")
    assert "email" in scan_dlp("Escreva para pessoa@example.com")
    assert "pessoa@example.com" not in redact_for_model("Escreva para pessoa@example.com")
    responses = iter(
        [
            '{"text":"Vi USD 900.00.","cited_fact_ids":["F1"]}',
            '{"text":"Vi USD 901.00.","cited_fact_ids":["F1"]}',
        ]
    )
    client = StructuredClient(
        {"phrase": ModelSpec(provider="mock", model_id="mock")},
        {},
        mock_response=lambda _s, _u, _t: next(responses),
    )
    plan = ResponsePlan(response_type="clarify", outcome="clarification", reply="")
    built = build_reply(plan, language="pt", facts=facts, client=client)
    assert built.used_template
    assert "900" not in built.plan.reply
    assert "uncited_number" in built.violations
