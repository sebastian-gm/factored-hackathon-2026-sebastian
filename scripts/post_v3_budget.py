"""Prepare/verify the post-v3 dev allowance without making model calls.

Same mechanism as the after-v2 allowance: prior scopes are closed to new
reservations and keep all charges; the new scope has a $1 lifetime cap, and
prior spend plus this allowance plus a future $3 v4 run stays within the
owner-approved $12 cumulative ceiling. Only aggregate budget metadata is read.
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal

import psycopg

SCOPE = "dev-gate/post-v3"
RUN_ID = "post-v3"
CAP = Decimal("1.00")
CUMULATIVE_CAP = Decimal("12.00")
FUTURE_V4_MAX = Decimal("3.00")
PRIOR_SCOPES = (
    "final-evaluation",
    "dev-gate/option-a",
    "final-evaluation-v2",
    "dev-gate/after-v2",
    "final-evaluation-v3",
)


def check_exposure(prior: Decimal) -> None:
    if not prior.is_finite() or prior < 0 or prior + CAP + FUTURE_V4_MAX > CUMULATIVE_CAP:
        raise RuntimeError("Prior exposure plus dev and future v4 allowances exceeds approval")


def receipt(connection: psycopg.Connection) -> dict:
    prior = Decimal("0")
    for scope in PRIOR_SCOPES:
        if connection.execute(
            "SELECT disabled FROM llm.limits WHERE scope=%s", (scope,)
        ).fetchone() != (True,):
            raise RuntimeError("Prior evaluation scopes must be closed to new calls")
        row = connection.execute(
            "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s", (scope,)
        ).fetchone()
        assert row is not None
        prior += row[0]
    check_exposure(prior)
    if connection.execute(
        "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (SCOPE,)
    ).fetchone() != (CAP, False):
        raise RuntimeError("Post-v3 dev scope changed or disabled")
    if connection.execute(
        "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (SCOPE,)
    ).fetchall() != [(RUN_ID, CAP, True)]:
        raise RuntimeError("Dev calls must share the single lifetime-capped run")
    row = connection.execute(
        "SELECT count(*),coalesce(sum(actual_usd),0),coalesce(sum(charged_usd),0),"
        "count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope=%s",
        (SCOPE,),
    ).fetchone()
    assert row is not None
    if row[2] > CAP:
        raise RuntimeError("Dev exposure exceeds its lifetime cap")
    return {
        "scope": SCOPE,
        "run_id": RUN_ID,
        "cap_usd": float(CAP),
        "attempts": row[0],
        "known_cost_usd": float(row[1]),
        "charged_with_reserves_usd": float(row[2]),
        "unknown_cost_attempts": row[3],
        "prior_charged_with_reserves_usd": float(prior),
        "cumulative_charged_with_reserves_usd": float(prior + row[2]),
        "prior_plus_dev_and_future_v4_limits_usd": float(prior + CAP + FUTURE_V4_MAX),
    }


def verify(dsn: str, *, prepare: bool = False) -> dict:
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        if prepare:
            for scope in sorted(PRIOR_SCOPES):
                if (
                    connection.execute(
                        "SELECT scope FROM llm.limits WHERE scope=%s FOR UPDATE", (scope,)
                    ).fetchone()
                    is None
                ):
                    raise RuntimeError("Prior budget history missing")
                connection.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (scope,))
            connection.execute(
                "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING", (SCOPE, CAP)
            )
            connection.execute(
                "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
                (SCOPE, RUN_ID, CAP),
            )
        return receipt(connection)


def main() -> None:
    from scripts.azure_migrate_ops import connection_string

    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(connection_string("aclara_admin"), prepare=args.prepare)
    except Exception as error:
        raise SystemExit("Post-v3 budget setup failed: " + type(error).__name__) from None
    print(json.dumps(result))  # noqa: T201 -- aggregate metadata only.


if __name__ == "__main__":
    main()
