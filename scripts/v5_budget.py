"""Metadata-only v5 allowance; preparation never opens a suite or calls a model."""

from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal

import psycopg
from scripts.final_day_budget import receipt as final_day_receipt
from scripts.final_day_budget import remaining, usage

SCOPE = "final-evaluation-v5"
RUN_ID = "final-program-v5"
CAP = Decimal("1.50")
CEILING = Decimal("18.00")


def maximum(prior: Decimal, charged: Decimal) -> Decimal:
    result = prior + remaining(CAP, charged)
    if not prior.is_finite() or prior < 0 or result > CEILING:
        raise RuntimeError("V5 allowance exceeds the cumulative approval")
    return result


def receipt(connection) -> dict:
    data = final_day_receipt(connection)
    # The legacy receipt counts ALL charges, but not this newer unused purse.
    live_scope, live_run, live_cap = "live-exploration/v0.9.9", "v0.9.9", Decimal(".15")
    if connection.execute(
        "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (live_scope,)
    ).fetchone() != (live_cap, False) or connection.execute(
        "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (live_scope,)
    ).fetchall() != [(live_run, live_cap, True)]:
        raise RuntimeError("Prior live allowance differs")
    prior = Decimal(data["maximum_usd"]) + remaining(
        live_cap, usage(connection, live_scope, live_run)
    )
    charged = usage(connection, SCOPE, RUN_ID)
    row = connection.execute(
        "SELECT count(*),coalesce(sum(actual_usd),0),"
        "count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope=%s",
        (SCOPE,),
    ).fetchone()
    return {
        "scope": SCOPE,
        "run_id": RUN_ID,
        "cap_usd": str(CAP),
        "attempts": row[0],
        "known_cost_usd": str(row[1]),
        "charged_with_reserves_usd": str(charged),
        "unknown_cost_attempts": row[2],
        "conservative_prior_including_v5_charges_usd": str(prior),
        "conservative_maximum_usd": str(maximum(prior, charged)),
        "cumulative_ceiling_usd": str(CEILING),
        "retained_historical_unknown_reservations": data["unknown_reservations"],
    }


def verify(dsn: str, *, prepare: bool = False) -> dict:
    with psycopg.connect(dsn) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        connection.execute("SET LOCAL ROLE aclara_owner")
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope='production' FOR UPDATE"
        ).fetchone() != (Decimal(1), False):
            raise RuntimeError("Production breaker differs")
        receipt(connection)  # Count the full future allowance BEFORE insertion.
        if prepare:
            connection.execute(
                "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING", (SCOPE, CAP)
            )
            connection.execute(
                "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
                (SCOPE, RUN_ID, CAP),
            )
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (SCOPE,)
        ).fetchone() != (CAP, False) or connection.execute(
            "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (SCOPE,)
        ).fetchall() != [(RUN_ID, CAP, True)]:
            raise RuntimeError("V5 scope missing, changed or disabled")
        return receipt(connection)


def main() -> None:
    from scripts.azure_dev import ROOT, private_write
    from scripts.azure_migrate_ops import connection_string

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--credits", choices=("before", "after"))
    args = parser.parse_args()
    try:
        if args.credits:
            if args.prepare:
                raise RuntimeError("Credit readback and scope preparation are separate")
            import httpx
            from scripts.azure_dev import VAULT, az

            key = az(
                "keyvault", "secret", "show", "--vault-name", VAULT, "--name", "openrouter-api-key"
            )["value"]
            with httpx.Client(timeout=30) as client:
                responses = [
                    client.get(
                        "https://openrouter.ai/api/v1/" + endpoint,
                        headers={"Authorization": "Bearer " + key},
                    )
                    for endpoint in ("credits", "key")
                ]
            for response in responses:
                response.raise_for_status()
            account, limits = [response.json()["data"] for response in responses]
            balance = Decimal(str(account["total_credits"])) - Decimal(str(account["total_usage"]))
            key_remaining = Decimal(str(limits["limit_remaining"]))
            if not all(value.is_finite() and value >= 0 for value in (balance, key_remaining)):
                raise RuntimeError("Invalid provider credit metadata")
            if args.credits == "before" and min(balance, key_remaining) < CAP:
                raise RuntimeError("Provider balance/key cannot cover the full v5 allowance")
            result = {
                "phase": args.credits,
                "account_remaining_usd": str(balance),
                "key_remaining_usd": str(key_remaining),
                "model_calls": 0,
            }
            private_write(
                ROOT / f"artifacts/evaluation-v5-prep/credits-{args.credits}.json",
                json.dumps(result) + "\n",
            )
            print(json.dumps(result))  # noqa: T201 -- numeric metadata only.
            return
        if args.prepare and os.getenv("V5_BUDGET_PREPARATION_APPROVED") != "1":
            raise RuntimeError("Owner preparation approval required")
        result = verify(connection_string("aclara_admin"), prepare=args.prepare)
        private_write(ROOT / "artifacts/evaluation-v5-prep/budget.json", json.dumps(result) + "\n")
    except Exception as error:
        raise SystemExit("V5 budget blocked: " + type(error).__name__) from None
    print(json.dumps(result))  # noqa: T201 -- budget metadata only.


if __name__ == "__main__":
    main()
