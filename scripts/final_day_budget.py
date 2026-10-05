"""Final-day approval accounting. Metadata only; no model or customer reads."""

from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal

import psycopg
from scripts.go_live_budget import allocation
from scripts.release_smoke_budget import CEILING

RUN_ID = "final-build"
SCOPES = {"regression/final-build/v4": Decimal(".30"), "live-exploration/final-day": Decimal(".40")}
ANCHOR = "edd30702f32b21af17fc353d0ee410e67b2e932b"
CLOSED_RUNS = (
    ("production", "pre-v4-release-" + ANCHOR, Decimal(".10")),
    ("go-live/2026-10-03/lead", "2026-10-03", Decimal(".10")),
)
LEAD = ("release/v0.9.1/lead", "v0.9.1", Decimal(".10"))


def remaining(cap: Decimal, charged: Decimal) -> Decimal:
    if not charged.is_finite() or charged < 0 or charged > cap:
        raise RuntimeError("Invalid or excessive purse exposure")
    return cap - charged


def usage(connection, scope: str, run: str) -> Decimal:
    return connection.execute(
        "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s AND run_id=%s",
        (scope, run),
    ).fetchone()[0]


def receipt(connection) -> dict:
    data = allocation(connection, ANCHOR)
    closed_unused = Decimal(0)
    for scope, run, cap in CLOSED_RUNS:
        if connection.execute(
            "SELECT limit_usd,enabled FROM llm.runs WHERE scope=%s AND run_id=%s", (scope, run)
        ).fetchone() != (cap, False):
            raise RuntimeError("Historical disabled purse differs")
        closed_unused += remaining(cap, usage(connection, scope, run))
    scope, run, cap = LEAD
    if connection.execute(
        "SELECT limit_usd,enabled FROM llm.runs WHERE scope=%s AND run_id=%s", (scope, run)
    ).fetchone() != (cap, True):
        raise RuntimeError("Existing lead purse differs")
    lead_unused = remaining(cap, usage(connection, scope, run))
    lanes = {}
    unused = Decimal(0)
    for scope, cap in SCOPES.items():
        charged = usage(connection, scope, RUN_ID)
        capacity = remaining(cap, charged)
        unused += capacity
        lanes[scope] = {
            "run_id": RUN_ID,
            "cap_usd": str(cap),
            "charged_usd": str(charged),
            "remaining_usd": str(capacity),
        }
    maximum = Decimal(data["maximum_usd"]) - closed_unused + lead_unused + unused
    if maximum > CEILING:
        raise RuntimeError("Final-day conservative cumulative ceiling exceeded")
    return {
        **data,
        "maximum_usd": str(maximum),
        "ceiling_usd": str(CEILING),
        "new_scopes": lanes,
        "disabled_unused_excluded_usd": str(closed_unused),
        "lead_unused_usd": str(lead_unused),
    }


def verify(dsn: str, *, prepare: bool = False) -> dict:
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        # Serialize setup with the existing production policy; never change it.
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope='production' FOR UPDATE"
        ).fetchone() != (Decimal(1), False):
            raise RuntimeError("Production USD1/day policy differs")
        receipt(connection)  # Include full future allowances before insertion.
        for scope, cap in SCOPES.items():
            if prepare:
                connection.execute(
                    "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING",
                    (scope, cap),
                )
                connection.execute(
                    "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
                    (scope, RUN_ID, cap),
                )
            if connection.execute(
                "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (scope,)
            ).fetchone() != (cap, False) or connection.execute(
                "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (scope,)
            ).fetchall() != [(RUN_ID, cap, True)]:
                raise RuntimeError("Final-day scope differs, missing or disabled")
        return receipt(connection)


def main() -> None:
    from scripts.azure_dev import ROOT, private_write
    from scripts.azure_migrate_ops import connection_string

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare and os.getenv("FINAL_DAY_BUDGET_APPROVED") != "1":
            raise RuntimeError("Owner final-day approval required")
        data = verify(connection_string("aclara_admin"), prepare=args.prepare)
        private_write(ROOT / "artifacts/final-day/budget.json", json.dumps(data) + "\n")
    except Exception as error:
        raise SystemExit("Final-day budget failed: " + type(error).__name__) from None
    print(json.dumps(data))  # noqa: T201 -- aggregate metadata only.


if __name__ == "__main__":
    main()
