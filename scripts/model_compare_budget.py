"""Prepare the approved model-comparison purse without calling any provider."""

from __future__ import annotations

import argparse
import json
import os

import psycopg
from scripts import pre_v4_budget

SCOPE = pre_v4_budget.MODEL_COMPARE_SCOPE
RUN_ID = pre_v4_budget.MODEL_COMPARE_RUN_ID
CAP = pre_v4_budget.MODEL_COMPARE_CAP


def verify(dsn: str, *, prepare: bool = False) -> dict:
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        # Use the same policy-row lock as reserve; never reopen/reset either purse.
        connection.execute(
            "SELECT scope FROM llm.limits WHERE scope=%s FOR UPDATE", (pre_v4_budget.SCOPE,)
        )
        if prepare:
            connection.execute(
                "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING", (SCOPE, CAP)
            )
            connection.execute(
                "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
                (SCOPE, RUN_ID, CAP),
            )
        connection.execute("SELECT scope FROM llm.limits WHERE scope=%s FOR UPDATE", (SCOPE,))
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (SCOPE,)
        ).fetchone() != (CAP, False) or connection.execute(
            "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (SCOPE,)
        ).fetchall() != [(RUN_ID, CAP, True)]:
            raise RuntimeError("Comparison policy missing, changed, disabled or not a single run")
        remaining = pre_v4_budget.receipt(connection)  # Also checks the open pre-v4 purse.
        usage = connection.execute(
            "SELECT count(*),coalesce(sum(actual_usd),0),coalesce(sum(charged_usd),0),"
            "count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope=%s",
            (SCOPE,),
        ).fetchone()
        assert usage is not None
        if usage[2] > CAP:
            raise RuntimeError("Model-comparison exposure exceeds its lifetime cap")
        return {
            "scope": SCOPE,
            "run_id": RUN_ID,
            "cap_usd": float(CAP),
            "attempts": usage[0],
            "known_cost_usd": float(usage[1]),
            "charged_with_reserves_usd": float(usage[2]),
            "unknown_cost_attempts": usage[3],
            "pre_v4_scope": remaining["scope"],
            "pre_v4_run_id": remaining["run_id"],
            "pre_v4_charged_usd": remaining["charged_with_reserves_usd"],
            "historical_charged_usd": remaining["prior_charged_with_reserves_usd"],
            "conservative_maximum_cumulative_usd": remaining["maximum_cumulative_usd"],
            "future_v4_authorized": False,
        }


def main() -> None:
    from scripts.azure_dev import ROOT, private_write
    from scripts.azure_migrate_ops import connection_string

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare and os.getenv("MODEL_COMPARE_BUDGET_PREPARATION_APPROVED") != "1":
            raise RuntimeError("Model-comparison budget preparation requires owner approval")
        result = verify(connection_string("aclara_admin"), prepare=args.prepare)
        private_write(ROOT / "artifacts/model-compare/budget.json", json.dumps(result) + "\n")
    except Exception as error:
        raise SystemExit("Model comparison budget failed: " + type(error).__name__) from None
    print(json.dumps(result))  # noqa: T201 -- aggregate budget metadata only.


if __name__ == "__main__":
    main()
