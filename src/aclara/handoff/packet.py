"""Customer-safe handoff packet construction."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any


def create_packet(language: str, reason_code: str) -> dict[str, Any]:
    spanish = language == "es"
    return {
        "schema_version": "1.0",
        "handoff_id": f"HO-{secrets.token_hex(4).upper()}",
        "created_at": datetime.now(UTC).isoformat(),
        "reason_codes": [reason_code],
        "priority": "high" if reason_code in {"FRD-01", "ESC-02"} else "normal",
        "route": {
            "queue": "Fraudes" if reason_code == "FRD-01" else "Quejas y Reclamos",
            "language": language,
            "fallback_used": False,
        },
        "request_summary": {
            "text": "Solicitud derivada para revisión humana."
            if spanish
            else "Solicitação encaminhada para análise humana.",
            "generated_by": {"model": "rules", "prompt": "none"},
            "label": "rule_based_summary",
        },
        "verified_facts": [],
        "actions_taken": [],
        "open_questions": [],
    }
