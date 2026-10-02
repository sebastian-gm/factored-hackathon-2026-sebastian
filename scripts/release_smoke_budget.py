"""Prepare fresh SHA-bound production smoke purses without resetting any history."""

from __future__ import annotations

import argparse
import json
import os
import re
from decimal import Decimal

import psycopg
from scripts.pre_v4_budget import MODEL_COMPARE_CAP, MODEL_COMPARE_SCOPE, PRIOR_SCOPES
from scripts.pre_v4_budget import SCOPE as DEV_SCOPE

CAP = Decimal("0.10")
# Sebastian approved +$3 on 2026-10-02; historical evaluation caps stay unchanged.
CEILING = Decimal("15.00")
DEV_CAP = Decimal("1.00")


def check_exposure(total: Decimal, dev_charged: Decimal) -> Decimal:
    """Include pre-v4 spend inside its full allowance, retaining every reserve."""
    if (
        not total.is_finite()
        or not dev_charged.is_finite()
        or dev_charged < 0
        or dev_charged > DEV_CAP
        or total < dev_charged
    ):
        raise RuntimeError("Invalid cumulative or pre-v4 exposure")
    # Align pre_v4_budget.receipt: its prior excludes current pre-v4 charges,
    # then includes that purse's entire $1 (spent + still available). Comparison
    # charges AND its full future allowance remain conservatively included.
    maximum = total - dev_charged + DEV_CAP + MODEL_COMPARE_CAP + Decimal("3") + CAP * 2
    if maximum > CEILING:
        raise RuntimeError("Cumulative exposure plus dev, v4 and both smoke caps exceeds approval")
    return maximum


def run_id(kind: str, sha: str) -> str:
    if kind not in {"release", "latency"} or not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("Smoke kind and full implementation SHA required")
    return f"pre-v4-{kind}-{sha}"


def verify(dsn: str, kind: str, sha: str, *, prepare: bool = False) -> dict:
    name = run_id(kind, sha)
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope='production' FOR UPDATE"
        ).fetchone() != (Decimal("3"), False):
            raise RuntimeError("Ordinary production daily breaker changed or disabled")
        scopes = (*PRIOR_SCOPES, DEV_SCOPE, MODEL_COMPARE_SCOPE, "production")
        row = connection.execute(
            "SELECT coalesce(sum(charged_usd),0),"
            "coalesce(sum(charged_usd) FILTER(WHERE scope=%s),0) "
            "FROM llm.reservations WHERE scope=ANY(%s)",
            (DEV_SCOPE, list(scopes)),
        ).fetchone()
        assert row is not None
        # Both sums use one snapshot. This is only arithmetic: no reservation,
        # charge, allowance, policy or unknown-cost classification is changed.
        maximum = check_exposure(row[0], row[1])
        if prepare:
            connection.execute(
                "INSERT INTO llm.runs VALUES('production',%s,%s,true) ON CONFLICT DO NOTHING",
                (name, CAP),
            )
        if connection.execute(
            "SELECT limit_usd,enabled FROM llm.runs WHERE scope='production' AND run_id=%s",
            (name,),
        ).fetchone() != (CAP, True):
            raise RuntimeError("SHA-bound smoke policy missing, changed or disabled")
        usage = connection.execute(
            "SELECT count(*),coalesce(sum(actual_usd),0),coalesce(sum(charged_usd),0),"
            "count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations "
            "WHERE scope='production' AND run_id=%s",
            (name,),
        ).fetchone()
        assert usage is not None
        if usage[2] > CAP:
            raise RuntimeError("Smoke exposure exceeds the lifetime cap")
        return {
            "scope": "production",
            "run_id": name,
            "implementation_sha": sha,
            "cap_usd": float(CAP),
            "attempts": usage[0],
            "known_cost_usd": float(usage[1]),
            "charged_with_reserves_usd": float(usage[2]),
            "unknown_cost_attempts": usage[3],
            "all_prior_charged_with_reserves_usd": float(row[0]),
            "pre_v4_charged_with_reserves_usd": float(row[1]),
            "conservative_maximum_cumulative_usd": float(maximum),
        }


def main() -> None:
    from scripts.azure_dev import ROOT, private_write
    from scripts.azure_migrate_ops import connection_string

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("release", "latency"))
    parser.add_argument("--sha", required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare and os.getenv("SMOKE_BUDGET_PREPARATION_APPROVED") != "1":
            raise RuntimeError("Smoke preparation requires owner release approval")
        result = verify(
            connection_string("aclara_admin"), args.kind, args.sha, prepare=args.prepare
        )
        private_write(
            ROOT / f"artifacts/azure/{result['run_id']}-budget.json", json.dumps(result) + "\n"
        )
    except Exception as error:
        raise SystemExit("Smoke budget setup failed: " + type(error).__name__) from None
    print(json.dumps(result))  # noqa: T201 -- aggregate metadata only.


if __name__ == "__main__":
    main()
