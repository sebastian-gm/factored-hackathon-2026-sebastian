"""Trusted per-run controls and metadata traces, never accepted from HTTP clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


class InjectedFailure(RuntimeError):
    pass


@dataclass
class Runtime:
    run_id: str = field(default_factory=lambda: str(uuid4()))
    system: str = "B1"
    country: str = "MX"
    faults: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    fired: set[int] = field(default_factory=set)

    def record(self, event: str, **values: Any) -> None:
        self.events.append({"event": event, **values})

    def fault(self, kind: str, trigger: str) -> bool:
        aliases = {
            "after_proposal_before_confirmation": "confirm_action",
            "after_verified_first_intake": "verified_intake",
            "verify_dispute_case": "read_back",
            "search_transactions": "MATCH",
            "nlu_every_call": "nlu",
        }
        for index, item in enumerate(self.faults):
            if (
                (index not in self.fired or item.get("parameters", {}).get("persistent", False))
                and item["type"] == kind
                and aliases.get(item["trigger"], item["trigger"])
                in {trigger, "always", "first_turn"}
            ):
                self.fired.add(index)
                self.record(
                    "fault",
                    kind=kind,
                    trigger=trigger,
                    declaration=index,
                    persistent=bool(item.get("parameters", {}).get("persistent", False)),
                )
                return True
        return False

    def checkpoint(self, trigger: str) -> None:
        for kind in ("tool_failure", "database_timeout", "connection_reset"):
            if self.fault(kind, trigger):
                raise InjectedFailure(kind)
