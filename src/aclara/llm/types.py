"""Small contracts shared by provider adapters and call accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

ProviderName = Literal["openai_compat", "gemini", "anthropic", "mock", "recorded", "typesafe"]
OutputMode = Literal["json_schema", "json_mode"]


@dataclass(frozen=True, slots=True)
class ModelSpec:
    provider: ProviderName
    model_id: str
    base_url: str | None = None
    key_env: str | None = None
    output_mode: OutputMode = "json_schema"
    price_id: str | None = None
    price_ceiling: tuple[float, float] | None = None
    provider_only: tuple[str, ...] = ()
    max_output_tokens: int = 1024
    max_tokens_parameter: Literal["max_tokens", "max_completion_tokens"] = "max_tokens"
    reasoning_effort: Literal["max", "xhigh", "high", "medium", "low", "minimal", "none"] | None = (
        None
    )
    timeout_seconds: int = 20
    # Sequential retry: the slow first attempt has a shorter timeout and the
    # second uses the full limit. This does not launch a concurrent hedge.
    first_attempt_timeout_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    text: str
    model_id: str
    usage: TokenUsage
    stop_reason: str | None = None
    usage_known: bool = True
    billed_cost_usd: float | None = None
    generation_id: str | None = None


@dataclass(frozen=True, slots=True)
class CallRecord:
    route: str
    provider: ProviderName
    model_id: str
    prompt_id: str
    prompt_hash: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    latency_ms: float
    cost_usd: float | None
    stop_reason: str | None
    status: Literal["valid", "invalid_json", "provider_error", "refusal", "skipped"]
    attempt: int
    generation_id: str | None = None
    judgments: dict[str, Any] | None = None


class ModelFailure(RuntimeError):
    """A model response cannot be trusted; caller should use the deterministic path."""


class BudgetFailure(ModelFailure):
    """Budget denial must not invoke a retry or alternate model."""


class SpendGate(Protocol):
    def reserve(self, amount_usd: float) -> str: ...

    def settle(self, reservation: str, actual_usd: float | None) -> None: ...
