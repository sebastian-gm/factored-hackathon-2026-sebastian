"""Versioned rule catalog; unimplemented policies are explicitly marked."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml  # type: ignore[import-untyped]


@dataclass(frozen=True)
class Rule:
    id: str
    es: str
    pt: str
    en: str
    parameters: dict[str, int | float | str]
    status: str
    enforcement: list[str]
    tests: list[str]


@lru_cache(maxsize=1)
def catalog() -> tuple[str, tuple[Rule, ...]]:
    data = yaml.safe_load((Path(__file__).resolve().parents[4] / "config/policy.yaml").read_text())
    return str(data["version"]), tuple(Rule(**row) for row in data["rules"])


def rule(identifier: str) -> Rule:
    return next(row for row in catalog()[1] if row.id == identifier)
