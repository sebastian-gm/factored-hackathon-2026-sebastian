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
    return {name: ModelSpec(**fields) for name, fields in data["models"].items()}


def load_prices(path: Path) -> dict[str, Price]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        name: Price(
            as_of=date.fromisoformat(str(fields["as_of"])),
            **{key: value for key, value in fields.items() if key != "as_of"},
        )
        for name, fields in data["prices"].items()
    }
