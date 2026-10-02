"""Customer-safe handoff packet construction."""

from __future__ import annotations

import secrets
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from aclara.handoff.context import refresh_summary
from aclara.handoff.routing import AgentDirectory
from aclara.policy.reasons import handoff_reasons


def create_packet(
    language: str, reason_code: str | Iterable[str], directory: AgentDirectory | None = None
) -> dict[str, Any]:
    reasons = handoff_reasons(reason_code)
    primary = reasons[0]
    packet = {
        "schema_version": "1.0",
        "handoff_id": f"HO-{secrets.token_hex(4).upper()}",
        "created_at": datetime.now(UTC).isoformat(),
        "reason_codes": list(reasons),
        "primary_reason": primary,
        "priority": "high" if {"FRD-01", "ESC-02"}.intersection(reasons) else "normal",
        "route": (directory or AgentDirectory()).route(language, primary),
        "verified_facts": [],
        "actions_taken": [],
        "open_questions": [],
    }
    refresh_summary(packet)
    return packet
