"""Runtime settings without checked-in credentials."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime


def _bank_clock(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("BANK_CLOCK must include a timezone")
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class Settings:
    demo_username: str = ""
    demo_password: str = ""
    demo_customer_id: str = "demo-customer-01"
    llm_provider: str = "mock"
    agent_system: str = "B1"
    ops_backend: str = "memory"
    bank_clock: datetime = datetime(2026, 6, 18, 6, 0, tzinfo=UTC)

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            demo_username=os.getenv("DEMO_USERNAME", ""),
            demo_password=os.getenv("DEMO_PASSWORD", ""),
            llm_provider=os.getenv("LLM_PROVIDER", "mock"),
            agent_system=os.getenv("AGENT_SYSTEM", "B1"),
            ops_backend=os.getenv("OPS_BACKEND", "postgres" if os.getenv("PGUSER") else "memory"),
            bank_clock=_bank_clock(os.getenv("BANK_CLOCK", "2026-06-18T06:00:00Z")),
        )
