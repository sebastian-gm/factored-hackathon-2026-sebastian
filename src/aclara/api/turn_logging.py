"""One metadata-only JSON record per completed customer turn."""

from __future__ import annotations

import json
import logging
from typing import Any

LOGGER = logging.getLogger("aclara.turn")
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(handler)


def log_turn(
    conversation_id: str, result: dict[str, Any], events: list[dict[str, Any]], *, degraded: bool
) -> None:
    calls = [event for event in events if event.get("event") == "llm_call"]
    rules = set(result.get("policy_rules") or [])
    rules.update((result.get("case") or {}).get("policy_rules") or [])
    rules.update((result.get("proposal") or {}).get("policy_rules") or [])
    rules.update((result.get("handoff") or {}).get("reason_codes") or [])
    for event in events:
        if event.get("event") == "policy":
            rules.update(event.get("rule_ids") or [])
    LOGGER.info(
        json.dumps(
            {
                "conversation_id": conversation_id,
                "outcome": result["outcome"],
                "rule_ids": sorted(rules),
                "llm_latency_ms": sum(float(call.get("latency_ms") or 0) for call in calls),
                "llm_cost_usd": None
                if any(call.get("cost_usd") is None for call in calls)
                else sum(float(call["cost_usd"]) for call in calls),
                "degraded": degraded,
            },
            separators=(",", ":"),
        )
    )
