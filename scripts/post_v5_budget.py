"""Owner-approved post-v5 replay purse; retain every historical reservation."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal

import psycopg
from scripts.final_day_budget import receipt as final_day_receipt
from scripts.final_day_budget import remaining, usage
from scripts.v5_budget import CAP as V5_CAP
from scripts.v5_budget import RUN_ID as V5_RUN
from scripts.v5_budget import SCOPE as V5_SCOPE

SCOPE = "regression/post-v5"
RUN_ID = "post-v5-final-build"
CAP = Decimal(".80")


def verify(dsn: str, *, prepare: bool = False) -> dict:
    with psycopg.connect(dsn) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        connection.execute("SET LOCAL ROLE aclara_owner")
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope='production' FOR UPDATE"
        ).fetchone() != (Decimal(1), False):
            raise RuntimeError("Production daily breaker differs")
        if prepare:
            connection.execute("UPDATE llm.limits SET disabled=true WHERE scope=%s", (V5_SCOPE,))
            connection.execute(
                "UPDATE llm.runs SET enabled=false WHERE scope=%s AND run_id=%s", (V5_SCOPE, V5_RUN)
            )
            connection.execute(
                "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING", (SCOPE, CAP)
            )
            connection.execute(
                "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
                (SCOPE, RUN_ID, CAP),
            )
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (V5_SCOPE,)
        ).fetchone() != (V5_CAP, True) or connection.execute(
            "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (V5_SCOPE,)
        ).fetchall() != [(V5_RUN, V5_CAP, False)]:
            raise RuntimeError("V5 purse is not retired intact")
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (SCOPE,)
        ).fetchone() != (CAP, False) or connection.execute(
            "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (SCOPE,)
        ).fetchall() != [(RUN_ID, CAP, True)]:
            raise RuntimeError("Post-v5 purse differs")
        prior = final_day_receipt(connection)
        charged = usage(connection, SCOPE, RUN_ID)
        retired = remaining(V5_CAP, usage(connection, V5_SCOPE, V5_RUN))
        live_unused = remaining(
            Decimal(".15"), usage(connection, "live-exploration/v0.9.9", "v0.9.9")
        )
        maximum = Decimal(prior["maximum_usd"]) + live_unused + remaining(CAP, charged)
        if maximum > Decimal(18):
            raise RuntimeError("Cumulative ceiling exceeded")
        counts = connection.execute(
            "SELECT count(*),coalesce(sum(actual_usd),0),"
            "count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope=%s",
            (SCOPE,),
        ).fetchone()
        return {
            "scope": SCOPE,
            "run_id": RUN_ID,
            "cap_usd": str(CAP),
            "charged_with_reserves_usd": str(charged),
            "known_cost_usd": str(counts[1]),
            "attempts": counts[0],
            "unknown_cost_attempts": counts[2],
            "retired_unused_v5_usd": str(retired),
            "conservative_maximum_usd": str(maximum),
            "ceiling_usd": "18.00",
            "retained_historical_unknown_reservations": prior["unknown_reservations"],
        }


def main() -> None:
    from scripts.azure_dev import ROOT, VAULT, az, private_write
    from scripts.azure_migrate_ops import connection_string

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--credits", choices=("before", "after"))
    args = parser.parse_args()
    try:
        if args.credits:
            import httpx

            key = az(
                "keyvault", "secret", "show", "--vault-name", VAULT, "--name", "openrouter-api-key"
            )["value"]
            with httpx.Client(timeout=30) as client:
                replies = [
                    client.get(
                        "https://openrouter.ai/api/v1/" + endpoint,
                        headers={"Authorization": "Bearer " + key},
                    )
                    for endpoint in ("credits", "key")
                ]
            for reply in replies:
                reply.raise_for_status()
            account, limits = [reply.json()["data"] for reply in replies]
            balance = Decimal(str(account["total_credits"])) - Decimal(str(account["total_usage"]))
            key_remaining = Decimal(str(limits["limit_remaining"]))
            if not all(v.is_finite() and v >= 0 for v in (balance, key_remaining)):
                raise RuntimeError("Invalid provider credits")
            if args.credits == "before" and min(balance, key_remaining) < CAP:
                raise RuntimeError("Provider credits below approved purse")
            result = {"account_usd": str(balance), "key_usd": str(key_remaining), "model_calls": 0}
            filename = "credits-" + args.credits
        else:
            result = verify(connection_string("aclara_admin"), prepare=args.prepare)
            filename = "budget"
        private_write(ROOT / f"artifacts/post-v5/{filename}.json", json.dumps(result) + "\n")
    except Exception as error:
        raise SystemExit("Post-v5 budget blocked: " + type(error).__name__) from None
    print(json.dumps(result))  # noqa: T201 -- numeric metadata only.


if __name__ == "__main__":
    main()
