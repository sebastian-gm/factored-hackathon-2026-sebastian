"""Prepare v2's cumulative budget without starting evaluation; verify on start/resume.

Only aggregate spend is read. No frozen inputs or abandoned v1 files are opened.
Preparation closes prior v1/dev scopes to new calls and preserves every reserve.
"""

from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal

import psycopg

from aclara.llm.final_run import RUN_ID, SCOPE, require_start

CAP = Decimal("11.87")
CUMULATIVE_CAP = Decimal("12.00")
PRIOR_SCOPES = ("final-evaluation", "dev-gate/option-a")


def check_exposure(prior: Decimal, cap: Decimal) -> None:
    if not prior.is_finite() or prior < 0 or cap != CAP or prior + cap > CUMULATIVE_CAP:
        raise RuntimeError("Prior exposure plus v2 limit exceeds the approved cumulative ceiling")


def receipt(connection: psycopg.Connection) -> dict:
    prior = Decimal("0")
    for scope in PRIOR_SCOPES:
        policy = connection.execute(
            "SELECT disabled FROM llm.limits WHERE scope=%s", (scope,)
        ).fetchone()
        if policy != (True,):
            raise RuntimeError("Prior budget scopes must remain closed to new calls")
        row = connection.execute(
            "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s", (scope,)
        ).fetchone()
        assert row is not None
        prior += row[0]
    limit = connection.execute(
        "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (SCOPE,)
    ).fetchone()
    run = connection.execute(
        "SELECT limit_usd,enabled FROM llm.runs WHERE scope=%s AND run_id=%s", (SCOPE, RUN_ID)
    ).fetchone()
    if limit != (CAP, False) or run != (CAP, True):
        raise RuntimeError("Prepared v2 policy is absent, changed, or disabled")
    check_exposure(prior, run[0])
    row = connection.execute(
        "SELECT count(*),coalesce(sum(actual_usd),0),coalesce(sum(charged_usd),0),count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope=%s AND run_id=%s",
        (SCOPE, RUN_ID),
    ).fetchone()
    assert row is not None
    if row[2] > CAP:
        raise RuntimeError("V2 exposure exceeds its cap")
    return {
        "scope": SCOPE,
        "run_id": RUN_ID,
        "cap_usd": float(CAP),
        "cumulative_cap_usd": float(CUMULATIVE_CAP),
        "prior_charged_with_reserves_usd": float(prior),
        "prior_plus_v2_limit_usd": float(prior + CAP),
        "attempts": row[0],
        "known_cost_usd": float(row[1]),
        "charged_with_reserves_usd": float(row[2]),
        "cumulative_charged_with_reserves_usd": float(prior + row[2]),
        "unknown_cost_attempts": row[3],
    }


def prepare(dsn: str) -> dict:
    """Owner-approved preparation only. Does not enable any provider or worker."""
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        # Same policy rows used by llm.reserve/settle: serialize with in-flight
        # callers, stop new prior-phase reservations, and preserve their charges.
        for scope in sorted(PRIOR_SCOPES):
            if (
                connection.execute(
                    "SELECT scope FROM llm.limits WHERE scope=%s FOR UPDATE", (scope,)
                ).fetchone()
                is None
            ):
                raise RuntimeError("Prior budget history is missing")
            connection.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (scope,))
        connection.execute(
            "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING", (SCOPE, CAP)
        )
        connection.execute(
            "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
            (SCOPE, RUN_ID, CAP),
        )
        return receipt(connection)


def verify(dsn: str) -> dict:
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        return receipt(connection)


def main() -> None:
    require_start()
    result = verify(os.environ["FINAL_BUDGET_OWNER_DSN"])
    print(json.dumps(result))  # noqa: T201 -- aggregate budget only.


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare:
            from evals.checkpoints import save
            from scripts.azure_dev import ROOT
            from scripts.azure_migrate_ops import connection_string

            result = prepare(connection_string("aclara_admin"))
            save(ROOT / "artifacts/final-program-v2/prepared-budget.json", result)
            print(json.dumps(result))  # noqa: T201 -- no provider call or frozen access.
        else:
            main()
    except Exception as error:
        raise SystemExit("Final budget setup failed: " + type(error).__name__) from None
