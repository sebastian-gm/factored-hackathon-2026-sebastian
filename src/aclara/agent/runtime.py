"""Trusted per-run controls and metadata traces, never accepted from HTTP clients."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from threading import RLock
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
    capture_history: bool = True  # Explicit offline/evaluation runtimes only.
    _history: list[dict[str, Any]] = field(default_factory=list, repr=False)
    fired: set[int] = field(default_factory=set)
    _lock: Any = field(default_factory=RLock, repr=False)
    _turn: ContextVar[list[dict[str, Any]] | None] = field(
        default_factory=lambda: ContextVar("runtime_turn", default=None), repr=False
    )

    @property
    def events(self) -> list[dict[str, Any]]:
        current = self._turn.get()
        return current if current is not None else self._history

    def record(self, event: str, **values: Any) -> None:
        item = {"event": event, **values}
        current = self._turn.get()
        if current is not None:
            current.append(item)
        if current is None or self.capture_history:
            with self._lock:
                self._history.append(item)

    @contextmanager
    def turn(self) -> Iterator[None]:
        """Independent HTTP traces; to_thread inherits this request's buffer."""
        token = self._turn.set([])
        try:
            yield
        finally:
            self._turn.reset(token)

    def trace(self, cursor: int = 0) -> list[dict[str, Any]]:
        current = self._turn.get()
        return list(current if current is not None else self._history[cursor:])

    def fault(self, kind: str, trigger: str) -> bool:
        with self._lock:
            return self._fault(kind, trigger)

    def _fault(self, kind: str, trigger: str) -> bool:
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
