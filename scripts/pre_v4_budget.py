"""Prepare the owner-approved shared pre-v4 dev scope; no provider or suite access."""

from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal

import psycopg

SCOPE = "dev-gate/pre-v4"
RUN_ID = "pre-v4"
CAP = Decimal("1.00")
CUMULATIVE_CAP = Decimal("12.00")
FUTURE_V4_MAX = Decimal("3.00")
RELEASE_SMOKE_MAX = Decimal("0.10")
LATENCY_SMOKE_MAX = Decimal("0.10")
MODEL_COMPARE_SCOPE = "dev-gate/model-compare"
MODEL_COMPARE_RUN_ID = "model-compare"
MODEL_COMPARE_CAP = Decimal("1.50")
PRIOR_SCOPES = (
    "final-evaluation",
    "dev-gate/option-a",
    "final-evaluation-v2",
    "dev-gate/after-v2",
    "final-evaluation-v3",
    "dev-gate/post-v3",
)


def check_exposure(prior: Decimal) -> None:
    if (
        not prior.is_finite()
        or prior < 0
        or prior + CAP + MODEL_COMPARE_CAP + FUTURE_V4_MAX + RELEASE_SMOKE_MAX + LATENCY_SMOKE_MAX
        > CUMULATIVE_CAP
    ):
        raise RuntimeError("Prior exposure plus both dev caps, v4 and smoke caps exceeds approval")


def receipt(connection: psycopg.Connection) -> dict:
    prior = Decimal("0")
    for scope in PRIOR_SCOPES:
        if connection.execute(
            "SELECT disabled FROM llm.limits WHERE scope=%s", (scope,)
        ).fetchone() != (True,):
            raise RuntimeError("Prior evaluation/dev scopes must be closed to new calls")
        row = connection.execute(
            "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s", (scope,)
        ).fetchone()
        assert row is not None
        prior += row[0]
    production = connection.execute(
        "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope='production'"
    ).fetchone()
    assert production is not None
    prior += production[0]  # Conservative: retain historical smokes/service charges too.
    comparison = connection.execute(
        "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s",
        (MODEL_COMPARE_SCOPE,),
    ).fetchone()
    assert comparison is not None
    prior += comparison[0]
    check_exposure(prior)
    if connection.execute(
        "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (SCOPE,)
    ).fetchone() != (CAP, False):
        raise RuntimeError("Pre-v4 dev policy changed or disabled")
    if connection.execute(
        "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (SCOPE,)
    ).fetchall() != [(RUN_ID, CAP, True)]:
        raise RuntimeError("All paid dev calls must share the single lifetime-capped run")
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
        "historical_production_charged_with_reserves_usd": float(production[0]),
        "model_compare_charged_with_reserves_usd": float(comparison[0]),
        "model_compare_allowance_usd": float(MODEL_COMPARE_CAP),
        "cumulative_charged_with_reserves_usd": float(prior + row[2]),
        "future_v4_limit_usd": float(FUTURE_V4_MAX),
        "release_smoke_allowance_usd": float(RELEASE_SMOKE_MAX),
        "in_region_latency_smoke_allowance_usd": float(LATENCY_SMOKE_MAX),
        "maximum_cumulative_usd": float(
            prior + CAP + MODEL_COMPARE_CAP + FUTURE_V4_MAX + RELEASE_SMOKE_MAX + LATENCY_SMOKE_MAX
        ),
        "future_v4_run_authorized": False,
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
    from scripts.azure_dev import ROOT, private_write
    from scripts.azure_migrate_ops import connection_string

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare and os.getenv("PRE_V4_BUDGET_PREPARATION_APPROVED") != "1":
            raise RuntimeError("Durable dev scope preparation needs owner approval")
        result = verify(connection_string("aclara_admin"), prepare=args.prepare)
        private_write(ROOT / "artifacts/pre-v4-dev/budget.json", json.dumps(result) + "\n")
    except Exception as error:
        raise SystemExit("Pre-v4 budget setup failed: " + type(error).__name__) from None
    print(json.dumps(result))  # noqa: T201 -- aggregate metadata only.


if __name__ == "__main__":
    main()
