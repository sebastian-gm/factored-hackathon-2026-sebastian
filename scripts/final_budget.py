"""Initialize/read back the approved $12 final program AFTER the owner's start signal.

Use an owner DSN through FINAL_BUDGET_OWNER_DSN; never pass credentials in argv.
Re-running preserves all reservations and cannot re-enable a tripped breaker.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal

import psycopg

from aclara.llm.final_run import RUN_ID, SCOPE, require_start


def main() -> None:
    require_start()
    with psycopg.connect(os.environ["FINAL_BUDGET_OWNER_DSN"]) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        connection.execute(
            "INSERT INTO llm.limits VALUES(%s,12,false) ON CONFLICT DO NOTHING", (SCOPE,)
        )
        connection.execute(
            "INSERT INTO llm.runs VALUES(%s,%s,12,true) ON CONFLICT DO NOTHING", (SCOPE, RUN_ID)
        )
        assert connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (SCOPE,)
        ).fetchone() == (Decimal("12"), False)
        assert connection.execute(
            "SELECT limit_usd,enabled FROM llm.runs WHERE scope=%s AND run_id=%s", (SCOPE, RUN_ID)
        ).fetchone() == (Decimal("12"), True)
        used = connection.execute(
            "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s AND run_id=%s",
            (SCOPE, RUN_ID),
        ).fetchone()[0]
    print(json.dumps({"cap_usd": 12, "reserved_or_billed_usd": float(used)}))  # noqa: T201 -- aggregate only


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit("Final budget setup failed: " + type(error).__name__) from None
