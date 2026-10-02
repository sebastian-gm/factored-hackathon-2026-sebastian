"""Commit global spend reservations independently of customer workflow transactions."""

from __future__ import annotations

import math
from decimal import ROUND_CEILING, Decimal
from uuid import UUID

from psycopg import Error
from psycopg_pool import PoolTimeout

from aclara.llm.types import BudgetFailure
from aclara.ops.store import Store


def _money(value: float) -> Decimal:
    if not math.isfinite(value) or value < 0:
        raise BudgetFailure("Invalid model cost")
    return Decimal(str(value)).quantize(Decimal("0.00000001"), rounding=ROUND_CEILING)


class PostgresSpendGate:
    def __init__(self, store: Store, *, scope: str = "production", run_id: str | None = None):
        if store.pool is None:
            raise ValueError("Real runtime calls require durable Postgres accounting")
        self.store, self.scope, self.run_id = store, scope, run_id

    def reserve(self, amount_usd: float) -> str:
        pool = self.store.pool
        if pool is None:
            raise BudgetFailure("Durable model budget unavailable")
        try:
            # Separate connection: commits before the external request, even when the
            # enclosing customer action later rolls back or the worker disappears.
            with pool.connection() as connection:
                row = connection.execute(
                    "SELECT llm.reserve(%s,%s,%s)",
                    (self.scope, self.run_id, _money(amount_usd)),
                ).fetchone()
        except (Error, PoolTimeout) as exc:
            raise BudgetFailure("Durable model budget unavailable") from exc
        if not row or row[0] is None:
            raise BudgetFailure("Durable model budget reached or disabled")
        return str(row[0])

    def settle(self, reservation: str, actual_usd: float | None) -> None:
        pool = self.store.pool
        if pool is None:
            raise BudgetFailure("Durable model settlement unavailable; reserve retained")
        try:
            with pool.connection() as connection:
                row = connection.execute(
                    "SELECT llm.settle(%s,%s)",
                    (UUID(reservation), _money(actual_usd) if actual_usd is not None else None),
                ).fetchone()
        except (Error, PoolTimeout) as exc:
            raise BudgetFailure("Durable model settlement unavailable; reserve retained") from exc
        if row != (True,):
            raise BudgetFailure("Model settlement exceeded reservation or was inconsistent")
