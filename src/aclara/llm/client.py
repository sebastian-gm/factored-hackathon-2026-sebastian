"""Pydantic boundary, bounded retry, budget and metadata-only call records."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import UTC, date, datetime
from hashlib import sha256
from time import perf_counter
from typing import Literal, TypeVar

from pydantic import BaseModel, ValidationError

from aclara.llm.config import Price
from aclara.llm.providers import Anthropic, Gemini, Mock, OpenAICompat, Provider, Recorded
from aclara.llm.types import CallRecord, ModelFailure, ModelSpec, ProviderResponse, TokenUsage

T = TypeVar("T", bound=BaseModel)


class StructuredClient:
    """Every attempt emits a record, including failed parses and provider errors."""

    def __init__(
        self,
        models: dict[str, ModelSpec],
        prices: dict[str, Price],
        *,
        mock_response: Callable[[str, str, type[BaseModel]], str] | None = None,
        cassettes: dict[str, str] | None = None,
        record: Callable[[CallRecord], None] | None = None,
        budget_usd: float = 0.0,
        daily_budget_usd: float | None = None,
    ) -> None:
        self.models = models
        self.prices = prices
        self.mock_configured = mock_response is not None
        self.records: list[CallRecord] = []
        self._record = record
        self.budget_usd = budget_usd
        self.spent_usd = 0.0
        self.daily_budget_usd = (
            daily_budget_usd
            if daily_budget_usd is not None
            else float(os.getenv("LLM_DAILY_BUDGET_USD", "10"))
        )
        self._daily_date: date = datetime.now(UTC).date()
        self._daily_spend_usd = 0.0
        self._adapters: dict[str, Provider] = {
            "openai_compat": OpenAICompat(),
            "gemini": Gemini(),
            "anthropic": Anthropic(),
            "mock": Mock(mock_response or (lambda _s, _u, _t: "{}")),
            "recorded": Recorded(cassettes or {}),
        }

    @property
    def valid_json_rate(self) -> float | None:
        attempts = [r for r in self.records if r.status in {"valid", "invalid_json"}]
        if not attempts:
            return None
        return sum(r.status == "valid" for r in attempts) / len(attempts)

    def generate(
        self,
        route: str,
        system: str,
        user: str,
        schema: type[T],
        *,
        prompt_id: str,
        prompt_hash: str | None = None,
    ) -> T:
        spec = self.models[route]
        reserve = 0.0
        if spec.provider not in {"mock", "recorded"}:
            today = datetime.now(UTC).date()
            if today != self._daily_date:
                self._daily_date, self._daily_spend_usd = today, 0.0
            if os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
                raise ModelFailure("Real model calls are disabled until owner approval")
            if not spec.key_env or not os.getenv(spec.key_env):
                raise ModelFailure(f"Missing local environment variable {spec.key_env}")
            if self.budget_usd <= 0:
                raise ModelFailure("A positive run budget is required for real calls")
            if not spec.price_id or spec.price_id not in self.prices:
                raise ModelFailure("No verified price for selected model")
            if self.spent_usd >= self.budget_usd or self._daily_spend_usd >= self.daily_budget_usd:
                raise ModelFailure("LLM budget reached")
            estimated_input = len(system.encode("utf-8")) + len(user.encode("utf-8"))
            estimated_input += len(json.dumps(schema.model_json_schema()).encode("utf-8"))
            reserve = self.prices[spec.price_id].cost(
                TokenUsage(input_tokens=estimated_input, output_tokens=1024)
            )
            if self.spent_usd + reserve > self.budget_usd or (
                self._daily_spend_usd + reserve > self.daily_budget_usd
            ):
                raise ModelFailure("Insufficient LLM budget for a bounded call")
        key = os.getenv(spec.key_env, "") if spec.key_env else ""
        digest = prompt_hash or sha256(system.encode("utf-8")).hexdigest()
        for attempt in (1, 2):
            if (
                attempt > 1
                and spec.provider not in {"mock", "recorded"}
                and (
                    self.spent_usd + reserve > self.budget_usd
                    or self._daily_spend_usd + reserve > self.daily_budget_usd
                )
            ):
                raise ModelFailure("Insufficient LLM budget for a retry")
            started = perf_counter()
            response: ProviderResponse | None = None
            status: Literal["valid", "invalid_json", "provider_error", "refusal"] = "provider_error"
            try:
                response = self._adapters[spec.provider].complete(spec, system, user, schema, key)
                stop = (response.stop_reason or "").lower()
                if any(
                    reason in stop
                    for reason in ("refusal", "max_tokens", "safety", "content_filter", "length")
                ):
                    status = "refusal"
                    raise ModelFailure("Model refused or truncated its reply")
                try:
                    parsed = schema.model_validate_json(response.text)
                except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                    status = "invalid_json"
                    raise ModelFailure("Model returned invalid structured output") from exc
                status = "valid"
                return parsed
            except ModelFailure:
                if attempt == 2:
                    raise
            finally:
                cost = self._cost(spec, response)
                if cost is not None:
                    self.spent_usd += cost
                    if spec.provider not in {"mock", "recorded"}:
                        self._daily_spend_usd += cost
                usage = response.usage if response else None
                call = CallRecord(
                    route=route,
                    provider=spec.provider,
                    model_id=response.model_id if response else spec.model_id,
                    prompt_id=prompt_id,
                    prompt_hash=digest,
                    input_tokens=usage.input_tokens if usage else 0,
                    output_tokens=usage.output_tokens if usage else 0,
                    cache_read_tokens=usage.cache_read_tokens if usage else 0,
                    cache_write_tokens=usage.cache_write_tokens if usage else 0,
                    latency_ms=(perf_counter() - started) * 1000,
                    cost_usd=cost,
                    stop_reason=response.stop_reason if response else None,
                    status=status,
                    attempt=attempt,
                )
                self.records.append(call)
                if self._record:
                    self._record(call)
            if spec.provider not in {"mock", "recorded"} and (
                self.spent_usd >= self.budget_usd or self._daily_spend_usd >= self.daily_budget_usd
            ):
                raise ModelFailure("LLM run budget reached")
        raise ModelFailure("Model validation failed twice")

    def _cost(self, spec: ModelSpec, response: ProviderResponse | None) -> float | None:
        if response is None or spec.provider in {"mock", "recorded"}:
            return 0.0
        if response.billed_cost_usd is not None:
            return response.billed_cost_usd
        price = self.prices.get(spec.price_id or "")
        return price.cost(response.usage) if price else None
