"""Production configuration must not send customer text to TypeSafe."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from test_api_security import _settings

from aclara.agent.ai import AgentAI
from aclara.agent.nlu import structured
from aclara.agent.runtime import Runtime
from aclara.llm import config
from aclara.llm.types import ProviderResponse, TokenUsage


@pytest.mark.parametrize("language", ["es", "pt"])
def test_production_gemini_config_never_calls_typesafe(
    monkeypatch: pytest.MonkeyPatch, language: str
) -> None:
    # Local fake adapters only; exercise the real production route/config wiring.
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("LLM_MODEL_ROUTE", "default")
    monkeypatch.setenv("LLM_RUN_BUDGET_USD", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "authored-fixture")
    monkeypatch.setenv("TYPESAFE_API_KEY", "authored-fixture")
    typed_calls: list[str] = []

    def typed(message: str, _key: str) -> Any:
        typed_calls.append(message)
        raise AssertionError("Production must never send this message to TypeSafe")

    class PrimaryFixture:
        def complete(self, *_args: Any) -> ProviderResponse:
            return ProviderResponse(
                '{"language":"' + language + '","intent":"charge_inquiry",'
                '"intent_confidence":0.99,"injection_suspected":true}',
                "google/gemini-3-flash-preview",
                TokenUsage(100, 20),
            )

    monkeypatch.setattr(structured, "_ask_jev_risks", typed)
    ai = AgentAI(replace(_settings(), llm_provider="openai_compat"), Runtime(system="P"))
    ai.client._adapters["openai_compat"] = PrimaryFixture()
    result = ai.understand("Cargo de prueba", datetime(2026, 10, 1, tzinfo=UTC), country="CO")
    assert not typed_calls
    assert not ai.client.risk_second_opinion_enabled
    assert not result.degraded and result.extracted.injection_suspected
    assert [r.provider for r in ai.client.records] == ["openai_compat"]
    assert not any(e.get("provider") == "typesafe" for e in ai.runtime.events)


@pytest.mark.parametrize("value", [None, False, True])
def test_risk_union_config_requires_explicit_boolean(tmp_path: Path, value: bool | None) -> None:
    path = tmp_path / "models.yaml"
    path.write_text(
        "models: {}\n"
        if value is None
        else f"routing:\n  risk_second_opinion_enabled: {str(value).lower()}\n"
    )
    assert config.load_risk_second_opinion_enabled(path) is (value is True)


@pytest.mark.parametrize("value", ['"false"', '"true"', "0", "1", "[]", "null"])
def test_malformed_risk_union_config_fails_closed(tmp_path: Path, value: str) -> None:
    path = tmp_path / "models.yaml"
    path.write_text(f"routing:\n  risk_second_opinion_enabled: {value}\n")
    with pytest.raises(ValueError, match="boolean"):
        config.load_risk_second_opinion_enabled(path)
