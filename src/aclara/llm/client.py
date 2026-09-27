"""Pydantic boundary, bounded retry, budget and metadata-only call records."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime
from hashlib import sha256
from threading import RLock
from time import perf_counter
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ValidationError

from aclara.llm.config import Price
from aclara.llm.providers import Anthropic, Gemini, Mock, OpenAICompat, Provider, Recorded
from aclara.llm.types import (
    BudgetFailure,
    CallRecord,
    ModelFailure,
    ModelSpec,
    ProviderResponse,
    SpendGate,
    TokenUsage,
)

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
        response_record: Callable[[CallRecord, dict[str, Any] | None], None] | None = None,
        budget_usd: float | None = 0.0,
        daily_budget_usd: float | None = None,
        spend_gate: SpendGate | None = None,
        call_timeout_seconds: float | None = None,
        fallback_routes: dict[str, str] | None = None,
    ) -> None:
        if budget_usd is None and spend_gate is None:
            raise ValueError("Unbounded local budget requires a durable spend gate")
        self.spend_gate = spend_gate
        self.call_timeout_seconds = call_timeout_seconds
        self._deadline: float | None = None
        self._lock = RLock()
        self.models = models
        self.fallback_routes = fallback_routes or {}
        for route, alternate in self.fallback_routes.items():
            if route not in models or alternate not in models or route == alternate:
                raise ValueError("Fallback must name a distinct configured route")
        self.prices = prices
        self.mock_configured = mock_response is not None
        self.records: list[CallRecord] = []
        self._record = record
        self._response_record = response_record
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
        attempted = [
            record
            for record in self.records
            if record.provider != "typesafe" and record.status != "skipped"
        ]
        if not attempted:
            return None
        return sum(r.status == "valid" for r in attempted) / len(attempted)

    def reserve_external_judgment(
        self, reserve_usd: float, *, primary_floor_usd: float = 0.05
    ) -> str | None:
        """Reserve budget for a concurrent typed judgment before its network call."""
        with self._lock:
            if os.getenv("LLM_REAL_CALLS_APPROVED") != "1" or reserve_usd <= 0:
                raise ModelFailure("Real typed judgments need owner approval and a reserve")
            today = datetime.now(UTC).date()
            if today != self._daily_date:
                self._daily_date, self._daily_spend_usd = today, 0.0
            if (
                self.budget_usd is not None
                and (
                    self.budget_usd <= 0
                    or self.spent_usd + reserve_usd + primary_floor_usd > self.budget_usd
                )
            ) or self._daily_spend_usd + reserve_usd + primary_floor_usd > self.daily_budget_usd:
                raise ModelFailure("Insufficient shared LLM budget for typed judgment")
            reservation = self.spend_gate.reserve(reserve_usd) if self.spend_gate else None
            self.spent_usd += reserve_usd
            self._daily_spend_usd += reserve_usd
            return reservation

    def finish_external_judgment(
        self, record: CallRecord, *, reserve_usd: float = 0.0, reservation: str | None = None
    ) -> None:
        """Persist cost and evidence through the existing execution-record path."""
        with self._lock:
            if record.cost_usd is not None:
                adjustment = record.cost_usd - reserve_usd
                self.spent_usd += adjustment
                self._daily_spend_usd += adjustment
            self.records.append(record)
            if self._record:
                self._record(record)
            if self._response_record:
                self._response_record(record, record.judgments)
            if reservation is not None and self.spend_gate:
                self.spend_gate.settle(reservation, record.cost_usd)

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
        # Reserve/retry accounting is serialized for this application instance.
        with self._lock:
            self._deadline = (
                perf_counter() + self.call_timeout_seconds if self.call_timeout_seconds else None
            )
            first_record = len(self.records)
            try:
                return self._generate(
                    route, system, user, schema, prompt_id=prompt_id, prompt_hash=prompt_hash
                )
            except BudgetFailure:
                raise
            except ModelFailure:
                alternate = self.fallback_routes.get(route)
                if alternate is None or len(self.records) == first_record:
                    raise
                return self._generate(
                    alternate, system, user, schema, prompt_id=prompt_id, prompt_hash=prompt_hash
                )
            finally:
                self._deadline = None

    def _generate(
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
            if self.budget_usd is not None and self.budget_usd <= 0:
                raise ModelFailure("A positive run budget is required for real calls")
            if not spec.price_id or spec.price_id not in self.prices:
                raise ModelFailure("No verified price for selected model")
            price = self.prices[spec.price_id]
            spec = replace(spec, price_ceiling=(price.input_per_million, price.output_per_million))
            if (self.budget_usd is not None and self.spent_usd >= self.budget_usd) or (
                self._daily_spend_usd >= self.daily_budget_usd
            ):
                raise ModelFailure("LLM budget reached")
            estimated_input = len(system.encode("utf-8")) + len(user.encode("utf-8"))
            estimated_input += len(json.dumps(schema.model_json_schema()).encode("utf-8"))
            estimated_input += 1024  # Conservative chat/schema framing allowance.
            reserve = price.cost(
                TokenUsage(input_tokens=estimated_input, output_tokens=spec.max_output_tokens)
            )
            if (self.budget_usd is not None and self.spent_usd + reserve > self.budget_usd) or (
                self._daily_spend_usd + reserve > self.daily_budget_usd
            ):
                raise ModelFailure("Insufficient LLM budget for a bounded call")
        key = os.getenv(spec.key_env, "") if spec.key_env else ""
        digest = prompt_hash or sha256(system.encode("utf-8")).hexdigest()
        for attempt in (1, 2):
            if self._deadline is not None:
                remaining = self._deadline - perf_counter()
                if remaining <= 0:
                    raise ModelFailure("Model call deadline reached")
                spec = replace(
                    spec, timeout_seconds=max(1, min(spec.timeout_seconds, int(remaining)))
                )
            if reserve and (
                (self.budget_usd is not None and self.spent_usd + reserve > self.budget_usd)
                or self._daily_spend_usd + reserve > self.daily_budget_usd
            ):
                raise ModelFailure("Insufficient LLM budget for another bounded attempt")
            reservation = self.spend_gate.reserve(reserve) if reserve and self.spend_gate else None
            started = perf_counter()
            response: ProviderResponse | None = None
            parsed: T | None = None
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
                if cost is None and reserve:
                    # Charge the conservative reserve to the budget, but do not report it
                    # as a billed per-call cost when the provider returned no usage.
                    self.spent_usd += reserve
                    self._daily_spend_usd += reserve
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
                    generation_id=response.generation_id if response else None,
                )
                self.records.append(call)
                if self._record:
                    self._record(call)
                if self._response_record:
                    self._response_record(call, parsed.model_dump(mode="json") if parsed else None)
                if reservation is not None and self.spend_gate:
                    self.spend_gate.settle(reservation, cost)
            if spec.provider not in {"mock", "recorded"} and (
                (self.budget_usd is not None and self.spent_usd >= self.budget_usd)
                or self._daily_spend_usd >= self.daily_budget_usd
            ):
                raise ModelFailure("LLM run budget reached")
        raise ModelFailure("Model validation failed twice")

    def _cost(self, spec: ModelSpec, response: ProviderResponse | None) -> float | None:
        if spec.provider in {"mock", "recorded"}:
            return 0.0
        if response is None:
            return None
        if response.billed_cost_usd is not None:
            return response.billed_cost_usd
        if not response.usage_known:
            return None
        price = self.prices.get(spec.price_id or "")
        return price.cost(response.usage) if price else None
