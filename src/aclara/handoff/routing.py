"""Deterministic routing from contract-allowed service-agent attributes only."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from aclara.ops.store import Store
from aclara.policy.rules.guards import normalized


@dataclass(frozen=True)
class ServiceAgent:
    agent_ref: str
    agent_status: str
    agent_type: str
    languages: str
    specialty: str | None
    total_monthly_interactions: int | None

    def speaks(self, language: str) -> bool:
        return ("portugues" if language == "pt" else "espanol") in normalized(self.languages)


def interaction_count(raw: str) -> int | None:
    if not raw or raw.casefold() in {"nan", "null"}:
        return None
    try:
        value = Decimal(raw)
        if not value.is_finite() or value < 0 or value % 1:
            raise ValueError("Invalid aggregate interaction count; source value redacted")
        return int(value)
    except InvalidOperation:
        raise ValueError("Invalid aggregate interaction count; source value redacted") from None


def read_source(path: Path) -> tuple[ServiceAgent, ...]:
    """The caller supplies the allowlisted service_agents source, never a credential document."""
    if path.name != "service_agents.csv":
        raise ValueError("Expected the service_agents.csv contract source")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        result = tuple(
            ServiceAgent(
                agent_ref="agent_" + hashlib.sha256(row["agent_id"].encode()).hexdigest()[:24],
                agent_status=row["agent_status"],
                agent_type=row["agent_type"],
                languages=row["languages"],
                specialty=row["specialty"] or None,
                total_monthly_interactions=interaction_count(row["total_monthly_interactions"]),
            )
            for row in csv.DictReader(stream)
        )
    if len({a.agent_ref for a in result}) != len(result):
        raise ValueError("Agent source contains duplicate references")
    return result


def authored_agents() -> tuple[ServiceAgent, ...]:
    return tuple(
        ServiceAgent(
            f"agent_fixture_{language}_{queue}",
            "Active",
            "Digital",
            "portugués" if language == "pt" else "español",
            queue,
            10,
        )
        for language in ("es", "pt")
        for queue in ("Fraudes", "Quejas y Reclamos")
    )


class AgentDirectory:
    def __init__(self, agents: tuple[ServiceAgent, ...] | None = None, store: Store | None = None):
        self.agents = agents
        self.store = store

    def records(self) -> tuple[ServiceAgent, ...]:
        if self.agents is not None:
            return self.agents
        if self.store is None or self.store.pool is None:
            return authored_agents()
        with self.store.pool.connection() as connection:
            return tuple(
                ServiceAgent(*r)
                for r in connection.execute(
                    "SELECT agent_ref,agent_status,agent_type,languages,specialty,total_monthly_interactions FROM reference.service_agents"
                )
            )

    def route(self, language: str, reason: str) -> dict[str, Any]:
        requested = (
            "Fraudes"
            if reason == "FRD-01"
            else "Seguridad"
            if reason == "SEC-01"
            else "Quejas y Reclamos"
        )
        active = [a for a in self.records() if a.agent_status == "Active"]
        stages = [(language, requested, False, False)]
        if language == "pt" and requested == "Fraudes":
            stages += [("pt", "Quejas y Reclamos", True, False), ("es", "Fraudes", False, True)]
        elif language == "pt" and requested == "Quejas y Reclamos":
            stages += [("es", requested, False, True)]
        for lang, queue, specialty_fallback, language_fallback in stages:
            candidates = [a for a in active if a.specialty == queue and a.speaks(lang)]
            if candidates:
                selected = min(
                    candidates,
                    key=lambda a: (
                        a.agent_type not in {"Digital", "Hybrid"},
                        a.total_monthly_interactions
                        if a.total_monthly_interactions is not None
                        else float("inf"),
                        a.agent_ref,
                    ),
                )
                return {
                    "queue": queue,
                    "requested_queue": requested,
                    "language": lang,
                    "fallback_used": specialty_fallback or language_fallback,
                    "specialty_fallback": specialty_fallback,
                    "language_fallback": language_fallback,
                    "assigned_agent_ref": selected.agent_ref,
                    "routing_explanation": f"{lang} + {queue}; Active; prefer Digital/Hybrid, then least monthly interactions",
                    "assignment_pending": False,
                }
        return {
            "queue": requested,
            "requested_queue": requested,
            "language": language,
            "fallback_used": False,
            "specialty_fallback": False,
            "language_fallback": False,
            "assigned_agent_ref": None,
            "routing_explanation": "No active qualified agent; queue retained for manual assignment",
            "assignment_pending": True,
        }


def aggregates(agents: tuple[ServiceAgent, ...]) -> dict[str, Any]:
    return {
        "total_agents": len(agents),
        "active_agents": sum(a.agent_status == "Active" for a in agents),
        "pt_fraud_agents": sum(a.speaks("pt") and a.specialty == "Fraudes" for a in agents),
        "active_pt_fraud_agents": sum(
            a.speaks("pt") and a.specialty == "Fraudes" and a.agent_status == "Active"
            for a in agents
        ),
        "projection_fields": list(asdict(agents[0])) if agents else [],
    }
