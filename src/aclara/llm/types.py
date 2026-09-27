"""Small contracts shared by provider adapters and call accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProviderName = Literal["openai_compat", "gemini", "anthropic", "mock", "recorded"]
OutputMode = Literal["json_schema", "json_mode"]


@dataclass(frozen=True, slots=True)
class ModelSpec:
    provider: ProviderName
    model_id: str
    base_url: str | None = None
    key_env: str | None = None
    output_mode: OutputMode = "json_schema"
    price_id: str | None = None
    provider_only: tuple[str, ...] = ()
    max_output_tokens: int = 1024
    reasoning_effort: Literal["max", "xhigh", "high", "medium", "low", "minimal", "none"] | None = (
        None
    )


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
    status: Literal["valid", "invalid_json", "provider_error", "refusal"]
    attempt: int
    generation_id: str | None = None


class ModelFailure(RuntimeError):
    """A model response cannot be trusted; caller should use the deterministic path."""
