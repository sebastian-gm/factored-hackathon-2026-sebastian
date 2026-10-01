"""Offline protections for scoped paired comparison, normalization and replay."""

from __future__ import annotations

import asyncio
import json
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest

from aclara.agent.nlu import structured
from aclara.llm import dev_model_compare as study
from aclara.llm import providers
from aclara.llm.client import StructuredClient
from aclara.llm.dev_latency import retry_analysis
from aclara.llm.dev_prompt_study import comparison_sample
from aclara.llm.dev_robustness import DevBudgetStop, ThresholdGate
from aclara.llm.types import ProviderResponse, TokenUsage
from aclara.llm.typesafe import TypedJudgments
from aclara.llm.typesafe_questions import RISK_CUES


def test_candidates_share_prompt_boundary_timeouts_fallback_and_privacy_pins() -> None:
    gemini, _, fallback = study.candidate_config("gemini")
    sol, prices, sol_fallback = study.candidate_config("sol")
    assert fallback == sol_fallback == "fallback_grok_4_20"
    assert sol["nlu"] == sol["phrase"]
    assert sol["nlu"].provider_only == ("azure",)
    assert sol["nlu"].price_ceiling == (2.0, 10.0)
    assert sol["nlu"].reasoning_effort == "low"
    assert prices[sol["nlu"].price_id or ""].input_per_million == 2.0
    assert prices[sol["nlu"].price_id or ""].output_per_million == 10.0
    for field in (
        "output_mode",
        "max_output_tokens",
        "timeout_seconds",
        "first_attempt_timeout_seconds",
    ):
        assert getattr(sol["nlu"], field) == getattr(gemini["nlu"], field)
    assert gemini["nlu"].model_id == study.GEMINI
    assert sol["nlu"].model_id == study.SOL
    with pytest.raises(ValueError):
        study.candidate_config("unapproved")


class _Row:
    def __init__(self, value: Any):
        self.value = value

    def fetchone(self) -> Any:
        return self.value


class _Connection:
    def __init__(self, cap: Decimal, charged: Decimal):
        self.cap, self.charged = cap, charged
        self.params: list[Any] = []
        self.committed = False

    @contextmanager
    def transaction(self):
        yield
        self.committed = True

    def execute(self, query: str, params: Any = None) -> _Row:
        self.params.append(params)
        if "daily_usd" in query:
            return _Row((self.cap, False))
        if "limit_usd" in query:
            return _Row((self.cap, True))
        if "sum(charged_usd)" in query:
            return _Row((self.charged,))
        if "llm.reserve" in query:
            return _Row((uuid4(),))
        return _Row((True,))


def test_comparison_cap_reserves_exact_run_and_retains_unknown_cost() -> None:
    connection = _Connection(Decimal("1.50"), Decimal("1.49"))
    gate = ThresholdGate(
        cast(Any, connection), scope=study.SCOPE, run_id=study.RUN_ID, cap=study.CAP, stop=study.CAP
    )
    reservation = gate.reserve(0.01)
    assert connection.committed
    assert connection.params[-1] == (study.SCOPE, study.RUN_ID, Decimal("0.01"))
    gate.settle(reservation, None)
    assert connection.params[-1][1] is None
    with pytest.raises(DevBudgetStop):
        gate.reserve(0.01000001)
    # Parameterization cannot relax the earlier $0.90 shared-dev stop by default.
    with pytest.raises(DevBudgetStop):
        ThresholdGate(cast(Any, _Connection(Decimal(1), Decimal("0.90")))).reserve(0.001)


@pytest.mark.parametrize(
    ("cap", "stop"), [("NaN", "1"), ("1", "Infinity"), ("1", "1.5"), ("0", "0")]
)
def test_invalid_budget_policy_rejected_before_any_query(cap: str, stop: str) -> None:
    with pytest.raises(ValueError):
        ThresholdGate(cast(Any, None), cap=Decimal(cap), stop=Decimal(stop))


def test_opening_annotations_are_independent_and_do_not_use_final_corrected_amount() -> None:
    truth = study.load_slot_truth(comparison_sample())
    assert len(truth) == 50
    assert sum(r["slots"] is not None for r in truth.values()) == 48
    assert truth["round2.br1.detail-correction"]["slots"]["amount_value"] == "40"
    assert truth["round2.co.currency-change"]["slots"]["currency"] == "COP"
    assert truth["round2.co.two-charges"]["slots"] is None
    assert (
        truth["test-v3.ambiguous_unsupported.047.clarify_currency_retains_intent"]["slots"][
            "currency"
        ]
        is None
    )


def test_populated_slot_f1_penalizes_wrong_missing_and_hallucinated_values() -> None:
    gold = {
        "merchant_expr": "Café Lápacho",
        "amount_value": "40",
        "currency": "BRL",
        "date_start": None,
    }
    assert study.slot_counts(
        {
            "merchant_expr": "cafe lapacho",
            "amount_value": "40.0",
            "currency": "USD",
            "date_start": "2026-06-16",
        },
        gold,
    ) == {"tp": 2, "fp": 2, "fn": 1}
    assert study.slot_counts(None, gold) == {"tp": 0, "fp": 0, "fn": 3}


def test_opted_in_sol_retains_same_jev_union_and_primary_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models, prices, _ = study.candidate_config("sol")
    client = StructuredClient(models, prices, budget_usd=1, risk_second_opinion_enabled=True)

    class Adapter:
        def complete(self, *_args: Any) -> ProviderResponse:
            return ProviderResponse(
                '{"language":"pt","intent":"charge_inquiry","intent_confidence":0.9}',
                study.SOL,
                TokenUsage(100, 20),
            )

    client._adapters["openai_compat"] = cast(Any, Adapter())
    probabilities = {cue: 0.0 for cue in RISK_CUES}
    probabilities["injection_suspected"] = 0.8
    monkeypatch.setattr(
        structured,
        "_ask_jev_risks",
        lambda *_: TypedJudgments("jev-1.13.0", {}, probabilities, {}, 100, 0, 1.0, 0.0000042),
    )
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-fixture")
    monkeypatch.setenv("TYPESAFE_API_KEY", "unit-fixture")
    result = structured.understand(
        "Não reconheço a cobrança",
        country="BR",
        bank_clock=datetime(2026, 6, 18, tzinfo=UTC),
        client=client,
    )
    assert result.extracted.injection_suspected
    risk = client.records[-1]
    assert risk.provider == "typesafe"
    assert risk.judgments is not None
    assert risk.judgments["primary_model_id"] == study.SOL
    assert not risk.judgments["primary_raw_flags"]["injection_suspected"]
    assert risk.judgments["union_flags"]["injection_suspected"]


def _attempt(
    route: str, status: str, attempt: int, ms: float, cost: float | None
) -> dict[str, Any]:
    return {
        "id": "synthetic-case",
        "candidate": "gemini",
        "provider": "openai_compat",
        "prompt_id": "nlu@v5.1",
        "route": route,
        "status": status,
        "attempt": attempt,
        "latency_ms": ms,
        "cost_usd": cost,
    }


def test_latency_replay_groups_failed_attempts_and_does_not_invent_cost() -> None:
    calls = [
        _attempt("nlu", "provider_error", 1, 6000, None),
        _attempt("nlu", "valid", 2, 2500, 0.001),
        {**_attempt("nlu_risk_second_opinion", "valid", 1, 500, 0.000004), "provider": "typesafe"},
        _attempt("nlu", "valid", 1, 3500, 0.001),
    ]
    result = retry_analysis(calls)
    assert result["serial_requests"] == 2
    assert result["requests_with_retry_or_fallback"] == 1
    h3 = result["hedge_counterfactual"]["3"]
    assert h3["triggered_first_attempts"] == 2 and h3["new_duplicate_requests"] == 1
    assert h3["optimistic_request_latency"]["p50_ms"] == 4500
    assert h3["measured_hedge_cost_usd"] is None
    h4 = result["hedge_counterfactual"]["4"]
    assert h4["new_duplicate_requests"] == 0
    assert h4["optimistic_request_latency"]["p50_ms"] == 5000


def test_resume_never_repeats_completed_or_interrupted_conversations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cases = comparison_sample()[:1]
    truth = study.load_slot_truth(comparison_sample())
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "0")
    monkeypatch.setattr(
        study, "load_dotenv", lambda *_args, **_kw: pytest.fail("Mock read local credentials")
    )
    monkeypatch.setattr(study, "OUTPUT", tmp_path / "paired")
    monkeypatch.setattr(study, "comparison_sample", lambda: cases)
    monkeypatch.setattr(study, "load_slot_truth", lambda _cases: truth)
    monkeypatch.setattr(study, "pins", lambda _cases: {"unchanged": True})
    first = asyncio.run(study.run(real=False))
    output = tmp_path / "mock"
    assert first["complete_pairs"] == 1
    before = {p.name: p.read_bytes() for p in output.glob("*.started.json")}
    second = asyncio.run(study.run(real=False, resume=True))
    assert second["complete_pairs"] == 1
    assert before == {p.name: p.read_bytes() for p in output.glob("*.started.json")}
    (output / f"sol.{cases[0].scenario['id']}.json").unlink()
    interrupted = asyncio.run(study.run(real=False, resume=True))
    assert interrupted["complete_pairs"] == 0
    assert not (output / f"sol.{cases[0].scenario['id']}.json").exists()
    previous_summary = (output / "summary.json").read_bytes()
    monkeypatch.setattr(study, "pins", lambda _cases: {"unchanged": False})
    with pytest.raises(RuntimeError, match="identical code"):
        asyncio.run(study.run(real=False, resume=True))
    assert (output / "summary.json").read_bytes() == previous_summary
    assert json.loads((output / "launch.json").read_text())["pins"] == {"unchanged": True}


def test_no_jev_call_on_mock_route_even_when_study_opted_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models, prices, _ = study.candidate_config("sol")
    client = StructuredClient(
        {k: replace(s, provider="mock") for k, s in models.items()},
        prices,
        risk_second_opinion_enabled=True,
    )
    monkeypatch.setattr(
        structured, "_ask_jev_risks", lambda *_: pytest.fail("Mock used a paid provider")
    )
    structured.understand(
        "Não reconheço", country="BR", bank_clock=datetime(2026, 6, 18, tzinfo=UTC), client=client
    )
    assert not client.records


def test_catalog_excludes_unapproved_non_zdr_or_more_expensive_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-fixture")
    rows = [
        {
            "model_id": model,
            "tag": provider,
            "status": 0,
            "supported_parameters": [
                "response_format",
                "structured_outputs",
                "max_tokens",
                "max_completion_tokens",
            ],
            "pricing": {"prompt": input_price, "completion": output_price},
        }
        for model, provider, input_price, output_price in (
            (study.GEMINI, "google-vertex/global", "0.0000005", "0.000003"),
            (study.SOL, "azure", "0.000002", "0.00001"),
        )
    ]
    monkeypatch.setattr(
        study, "urlopen", lambda *_args, **_kw: BytesIO(json.dumps({"data": rows}).encode())
    )
    assert study.require_catalog()["paid_calls"] == 0
    rows[1]["tag"] = "openai/flex"
    with pytest.raises(DevBudgetStop):
        study.require_catalog()
    rows[1]["tag"] = "azure"
    rows[1]["pricing"]["completion"] = "0.000011"
    with pytest.raises(DevBudgetStop):
        study.require_catalog()


def test_exhausted_free_health_check_fails_before_inference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-fixture")
    monkeypatch.setattr(
        study,
        "urlopen",
        lambda *_args, **_kw: BytesIO(b'{"data":{"total_credits":0,"total_usage":1}}'),
    )
    with pytest.raises(DevBudgetStop, match="exhausted"):
        study.require_credits()


def test_sol_payload_caps_total_completion_and_never_records_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = study.candidate_config("sol")[0]["nlu"]
    captured: dict[str, Any] = {}

    def respond(request: Any, **_kw: Any) -> BytesIO:
        captured.update(json.loads(request.data))
        return BytesIO(
            json.dumps(
                {
                    "model": study.SOL,
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"content": "{}", "reasoning": "DO-NOT-RETAIN"},
                        }
                    ],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0.0004},
                }
            ).encode()
        )

    monkeypatch.setattr(providers, "urlopen", respond)
    result = providers.OpenAICompat().complete(
        spec, "NLU", "synthetic input", structured.ExtractedNlu, "unit-fixture"
    )
    assert captured["max_completion_tokens"] == 2048 and "max_tokens" not in captured
    assert captured["provider"] == {
        "only": ["azure"],
        "allow_fallbacks": False,
        "zdr": True,
        "data_collection": "deny",
        "require_parameters": True,
        "max_price": {"prompt": 2.0, "completion": 10.0, "request": 0},
    }
    assert captured["reasoning"] == {"effort": "low"}
    assert result.text == "{}" and "DO-NOT-RETAIN" not in repr(result)
    assert result.billed_cost_usd == 0.0004
