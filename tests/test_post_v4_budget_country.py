"""Zero-network API probes for post-v4 budget failure and trusted country."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_workflow_api import message

from aclara.agent.nlu.structured import NluResult
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import Customer, TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.llm.config import Price
from aclara.llm.types import BudgetFailure, ModelSpec


class DeniedGate:
    def __init__(self, reason: str):
        self.reason, self.attempts = reason, 0

    def reserve(self, amount_usd: float) -> str:
        self.attempts += 1
        raise BudgetFailure(self.reason)

    def settle(self, reservation: str, actual_usd: float | None) -> None:
        raise AssertionError("No reservation was granted")


class NeverCalled:
    def complete(self, *args: Any) -> Any:
        raise AssertionError("An exhausted/disabled gate must prevent every provider call")


@pytest.mark.parametrize("reason", ["exhausted", "already disabled"])
@pytest.mark.parametrize("risk_enabled", [False, True])
@pytest.mark.parametrize(
    ("text", "localized"),
    [
        ("¿Qué es este cargo de Café Central?", "capacidad limitada"),
        ("O que é essa cobrança de Café Central?", "capacidade limitada"),
    ],
)
def test_denied_budget_returns_localized_degraded_200_without_any_model_call(
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
    risk_enabled: bool,
    text: str,
    localized: str,
) -> None:
    # Fake credentials plus a fail-on-call adapter; no real-model request exists.
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("AUDIT_ONLY_FAKE_KEY", "authored-fixture")
    monkeypatch.setenv("TYPESAFE_API_KEY", "authored-fixture")
    monkeypatch.setattr(
        "aclara.agent.nlu.structured._ask_jev_risks",
        lambda *_: pytest.fail("A denied budget must not start a typed provider call"),
    )
    gate = DeniedGate(reason)
    spec = ModelSpec(
        "openai_compat", "authored-budget-route", key_env="AUDIT_ONLY_FAKE_KEY", price_id="fixture"
    )
    llm = StructuredClient(
        {r: spec for r in ("nlu", "phrase")},
        {"fixture": Price(0.5, 3, 0.5, 0.5, date(2026, 10, 1), "authored")},
        budget_usd=None,
        spend_gate=gate,
        risk_second_opinion_enabled=risk_enabled,
    )
    llm._adapters["openai_compat"] = NeverCalled()

    async def check() -> None:
        app = create_app(_settings(), runtime=Runtime(system="P"), llm_client=llm)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            for _ in range(2):
                result, _ = await message(client, headers, text)
                assert localized in result["reply"]
                assert not result.get("case") and not result.get("proposal")
            assert (await client.get("/me", headers=headers)).status_code == 200
        assert gate.attempts == 2 and not llm.records
        assert any(e["event"] == "nlu" and e["degraded"] for e in app.state.runtime.events)

    asyncio.run(check())


@pytest.mark.parametrize(
    ("country", "expression", "expected", "currency"),
    [
        ("CO", "2 palos", Decimal("2000000"), "COP"),
        ("AR", "4 lucas", Decimal("4000"), "ARS"),
    ],
)
def test_real_app_nlu_uses_authenticated_customer_country_without_runtime_mutation(
    country: str,
    expression: str,
    expected: Decimal,
    currency: str,
) -> None:
    row = replace(
        TransactionRepository()._rows[0],
        merchant_name="Mercado Ensayo",
        amount=float(expected),
        currency=currency,
    )
    ledger = TransactionRepository(
        (row,),
        customers=(Customer(row.customer_id, country=country),),
        policy_fields={row.record_id: {"amount_usd": 80}},
    )
    llm = StructuredClient(
        {r: ModelSpec("mock", "authored-country") for r in ("nlu", "phrase")},
        {},
        mock_response=lambda *_: json.dumps(
            {
                "language": "es",
                "dialect_hint": "MX",
                "intent": "charge_inquiry",
                "intent_confidence": 0.99,
                "amount_expr": expression,
                "currency_expr": "pesos",
                "merchant_expr": row.merchant_name,
                "country_expr": "MX",
            }
        ),
    )

    async def check() -> None:
        runtime = Runtime(system="P", country="MX")
        app = create_app(_settings(), ledger, runtime=runtime, llm_client=llm)
        seen: list[NluResult] = []
        original = app.state.ai.understand

        def capture(*args: Any, **kwargs: Any) -> NluResult:
            parsed = original(*args, **kwargs)
            seen.append(parsed)
            return parsed

        app.state.ai.understand = capture
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            await message(
                client, headers, f"No hice esta compra de {expression} pesos en Mercado Ensayo"
            )
        assert len(seen) == 1
        assert seen[0].slots.amount_value == expected and seen[0].slots.currency == currency
        assert runtime.country == "MX"  # request context never mutates the shared runtime

    asyncio.run(check())
