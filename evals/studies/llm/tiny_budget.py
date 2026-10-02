"""Owner-approved, isolated study purses; never reset an existing reservation."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from evals.studies.llm.dev_robustness import DevBudgetStop


def receipt(connection: Any, scope: str, run: str, cap: Decimal, *, prepare: bool = False) -> dict:
    with connection.transaction():
        connection.execute("SET LOCAL ROLE aclara_owner")
        if prepare:
            connection.execute(
                "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING", (scope, cap)
            )
            connection.execute(
                "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
                (scope, run, cap),
            )
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (scope,)
        ).fetchone() != (cap, False) or connection.execute(
            "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (scope,)
        ).fetchall() != [(run, cap, True)]:
            raise DevBudgetStop("Dedicated lifetime policy readback failed")
        row = connection.execute(
            "SELECT count(*),coalesce(sum(actual_usd),0),coalesce(sum(charged_usd),0),"
            "count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope=%s",
            (scope,),
        ).fetchone()
    if row is None or row[2] > cap:
        raise DevBudgetStop("Dedicated cost accounting failed")
    return dict(
        scope=scope,
        run_id=run,
        cap_usd=float(cap),
        attempts=row[0],
        known_cost_usd=float(row[1]),
        charged_with_reserves_usd=float(row[2]),
        unknown_cost_attempts=row[3],
    )
