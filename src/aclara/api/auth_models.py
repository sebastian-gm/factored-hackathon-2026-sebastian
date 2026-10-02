"""Durable authentication records; customer authority stays server-side."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class JudgeReference:
    run_id: str
    session_id: str
    digest: str
    binding_hash: str


@dataclass(frozen=True, slots=True)
class Principal:
    session_id: str
    run_id: str
    customer_id: str
    username: str
    otp_at: datetime
    expires_at: datetime
    step_up_at: datetime | None = None
    capability_digest: str = ""
    role: str = "customer"
    locale: str = "es-MX"
    judge_reference: JudgeReference | None = None
    judge_profile: str | None = None
    judge_active_digest: str = ""
    judge_revision: int = 0
