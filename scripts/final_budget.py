"""Prepare a suite-specific cumulative budget without starting evaluation; verify on start/resume.

Only aggregate spend is read. No frozen inputs or abandoned v1 files are opened.
Preparation closes prior evaluation/dev scopes and preserves every reserve.
"""

from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal

import psycopg
from evals.program_spec import ProgramSpec, add_arguments, specification

from aclara.llm.final_run import require_start

V3 = specification("test-v3")

CAP = Decimal("3.00")
CUMULATIVE_CAP = Decimal("12.00")
RELEASE_SMOKE_ALLOWANCE = Decimal("0.10")
PRIOR_SCOPES = ("final-evaluation", "dev-gate/option-a", "final-evaluation-v2", "dev-gate/after-v2")


def check_exposure(prior: Decimal, cap: Decimal) -> None:
    if (
        not prior.is_finite()
        or prior < 0
        or cap != CAP
        or prior + cap + RELEASE_SMOKE_ALLOWANCE > CUMULATIVE_CAP
    ):
        raise RuntimeError(
            "Prior exposure plus program and release smoke limits exceeds the approved cumulative ceiling"
        )


def prior_scopes(spec: ProgramSpec) -> tuple[str, ...]:
    return PRIOR_SCOPES + (
        ("final-evaluation-v3", "dev-gate/post-v3") if spec.suite == "test-v4" else ()
    )


def receipt(connection: psycopg.Connection, spec: ProgramSpec = V3) -> dict:
    prior = Decimal("0")
    for scope in prior_scopes(spec):
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
        "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (spec.scope,)
    ).fetchone()
    runs = connection.execute(
        "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (spec.scope,)
    ).fetchall()
    if limit != (CAP, False) or runs != [(spec.run_id, CAP, True)]:
        raise RuntimeError(
            "Prepared program policy is absent, changed, disabled, or not a single lifetime run"
        )
    check_exposure(prior, CAP)
    row = connection.execute(
        "SELECT count(*),coalesce(sum(actual_usd),0),coalesce(sum(charged_usd),0),count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope=%s AND run_id=%s",
        (spec.scope, spec.run_id),
    ).fetchone()
    assert row is not None
    if row[2] > CAP:
        raise RuntimeError("Program exposure exceeds its cap")
    return {
        "scope": spec.scope,
        "run_id": spec.run_id,
        "cap_usd": float(CAP),
        "cumulative_cap_usd": float(CUMULATIVE_CAP),
        "prior_charged_with_reserves_usd": float(prior),
        "release_smoke_allowance_usd": float(RELEASE_SMOKE_ALLOWANCE),
        "prior_plus_program_and_smoke_limits_usd": float(prior + CAP + RELEASE_SMOKE_ALLOWANCE),
        "attempts": row[0],
        "known_cost_usd": float(row[1]),
        "charged_with_reserves_usd": float(row[2]),
        "cumulative_charged_with_reserves_usd": float(prior + row[2]),
        "unknown_cost_attempts": row[3],
    }


def prepare(dsn: str, spec: ProgramSpec = V3) -> dict:
    """Owner-approved preparation only. Does not enable any provider or worker."""
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        # Same policy rows used by llm.reserve/settle: serialize with in-flight
        # callers, stop new prior-phase reservations, and preserve their charges.
        for scope in sorted(prior_scopes(spec)):
            if (
                connection.execute(
                    "SELECT scope FROM llm.limits WHERE scope=%s FOR UPDATE", (scope,)
                ).fetchone()
                is None
            ):
                raise RuntimeError("Prior budget history is missing")
            connection.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (scope,))
        connection.execute(
            "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING", (spec.scope, CAP)
        )
        connection.execute(
            "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
            (spec.scope, spec.run_id, CAP),
        )
        return receipt(connection, spec)


def verify(dsn: str, spec: ProgramSpec = V3) -> dict:
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        return receipt(connection, spec)


def main(spec: ProgramSpec = V3) -> None:
    require_start()
    result = verify(os.environ["FINAL_BUDGET_OWNER_DSN"], spec)
    print(json.dumps(result))  # noqa: T201 -- aggregate budget only.


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    add_arguments(parser)
    args = parser.parse_args()
    spec = specification(args.suite, args.bindings, args.manifest_pin)
    try:
        if args.prepare:
            if os.getenv("FINAL_BUDGET_PREPARATION_APPROVED") != "1":
                raise RuntimeError("Budget preparation requires separate owner release approval")
            from evals.checkpoints import save
            from scripts.azure_migrate_ops import connection_string

            result = prepare(connection_string("aclara_admin"), spec)
            save(spec.output / "prepared-budget.json", result)
            print(json.dumps(result))  # noqa: T201 -- no provider call or frozen access.
        else:
            main(spec)
    except Exception as error:
        raise SystemExit("Final budget setup failed: " + type(error).__name__) from None
