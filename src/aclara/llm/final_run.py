"""Explicit-start final routes sharing one durable cumulative budget, including judge."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from aclara.llm.client import StructuredClient
from aclara.llm.config import load_fallback_route, load_models, load_prices
from aclara.llm.types import BudgetFailure, CallRecord, SpendGate
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import Store

ROOT = Path(__file__).resolve().parents[3]
SCOPE = "final-evaluation-v3"
RUN_ID = "final-program-v3"


class FinalBudgetStop(RuntimeError):
    """Abort the evaluation rather than count budget denial as a model fallback."""


def require_start() -> None:
    if any(os.getenv(name) != "1" for name in ("LLM_FINAL_RUN_STARTED", "LLM_REAL_CALLS_APPROVED")):
        raise RuntimeError("Final evaluation requires Sebastian's explicit start signal")


class FinalSpendGate:
    def __init__(self, gate: SpendGate):
        self.gate = gate

    def reserve(self, amount_usd: float) -> str:
        try:
            return self.gate.reserve(amount_usd)
        except BudgetFailure as exc:
            raise FinalBudgetStop("Final cumulative budget unavailable or exhausted") from exc

    def settle(self, reservation: str, actual_usd: float | None) -> None:
        try:
            self.gate.settle(reservation, actual_usd)
        except BudgetFailure as exc:
            raise FinalBudgetStop("Final cost settlement failed; reservation retained") from exc


def journal(path: Path) -> Callable[[CallRecord, dict[str, Any] | None], None]:
    path = path.resolve()
    if not path.is_relative_to(ROOT / "artifacts"):
        raise ValueError("Provider output must remain in ignored artifacts")
    path.parent.mkdir(parents=True, exist_ok=True)

    def write(record: CallRecord, structured: dict[str, Any] | None) -> None:
        # Only schema-validated content, never raw provider envelopes or reasoning.
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(
                json.dumps({"call": asdict(record), "validated_output": structured}) + "\n"
            )
            stream.flush()
            os.fsync(stream.fileno())

    return write


def client_for(
    route: str,
    store: Store,
    *,
    response_record: Callable[[CallRecord, dict[str, Any] | None], None] | None = None,
    judge: bool = False,
) -> StructuredClient:
    require_start()
    if (judge and route != "openrouter_sonnet") or (not judge and route != "default"):
        raise ValueError("Route is outside the approved final program")
    models = load_models(ROOT / "config/models.yaml")
    spec = models[route]
    fallback = (
        load_fallback_route(ROOT / "config/models.yaml", models) if route == "default" else None
    )
    if judge:
        models = {spec.model_id: replace(spec, max_output_tokens=256)}
    else:
        models["nlu"] = models["phrase"] = spec
    return StructuredClient(
        models,
        load_prices(ROOT / "config/pricing.yaml"),
        budget_usd=None,
        daily_budget_usd=12,
        spend_gate=FinalSpendGate(PostgresSpendGate(store, scope=SCOPE, run_id=RUN_ID)),
        fallback_routes={"nlu": fallback, "phrase": fallback} if fallback else None,
        call_timeout_seconds=45,
        response_record=response_record,
    )


def open_budget_store() -> Store:
    require_start()
    dsn = os.getenv("EVAL_BUDGET_DSN")
    if not dsn:
        raise RuntimeError(
            "Pin EVAL_BUDGET_DSN to the same final-program database for every process"
        )
    return Store(dsn)
