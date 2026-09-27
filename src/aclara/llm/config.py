"""Checked-in model and price configuration; secrets are environment-only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from aclara.llm.types import ModelSpec, TokenUsage


@dataclass(frozen=True, slots=True)
class Price:
    input_per_million: float
    output_per_million: float
    cache_read_per_million: float
    cache_write_per_million: float
    as_of: date
    source_url: str

    def cost(self, usage: TokenUsage) -> float:
        uncached = max(0, usage.input_tokens - usage.cache_read_tokens - usage.cache_write_tokens)
        return (
            uncached * self.input_per_million
            + usage.output_tokens * self.output_per_million
            + usage.cache_read_tokens * self.cache_read_per_million
            + usage.cache_write_tokens * self.cache_write_per_million
        ) / 1_000_000


def load_models(path: Path) -> dict[str, ModelSpec]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    models: dict[str, ModelSpec] = {}
    for name, fields in data["models"].items():
        providers = fields.get("provider_only", [])
        if not isinstance(providers, list) or any(
            not isinstance(provider, str) or not provider for provider in providers
        ):
            raise ValueError("provider_only must be a list of nonempty provider names")
        models[name] = ModelSpec(**{**fields, "provider_only": tuple(providers)})
    return models


def load_fallback_route(path: Path, models: dict[str, ModelSpec]) -> str | None:
    """Validate the selected alternate model; None disables automatic failover."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    selection = data.get("routing", {})
    if not isinstance(selection, dict):
        raise ValueError("Model routing configuration must be a mapping")
    route = selection.get("fallback_route")
    if route is None:
        return None
    if not isinstance(route, str) or route not in models:
        raise ValueError("Fallback route must name a configured model")
    if route == "default" or models[route].provider in {"mock", "recorded"}:
        raise ValueError("Fallback route must be a distinct real model")
    return route


def load_prices(path: Path) -> dict[str, Price]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        name: Price(
            as_of=date.fromisoformat(str(fields["as_of"])),
            **{key: value for key, value in fields.items() if key != "as_of"},
        )
        for name, fields in data["prices"].items()
    }
