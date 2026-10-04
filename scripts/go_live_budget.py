"""October 3 operator purses; public traffic also uses the production breaker.

Each trusted lane reserves its own purse before an HTTP request and settles only
from verified call-cost metadata. These reservations are additional to the API's
production reservations, deliberately counted twice in conservative accounting.
No HTTP header, login field or browser cookie selects or changes a budget policy.
"""

from __future__ import annotations

from decimal import Decimal

import psycopg
from scripts.pre_v4_budget import MODEL_COMPARE_SCOPE, PRIOR_SCOPES, SCOPE
from scripts.release_smoke_budget import check_exposure, run_id

from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import Store

DAY = "2026-10-03"
JUDGING_RUN = "judging-2026-10"
JUDGING_CAP = Decimal("1.60")
LANE_CAPS = {"lead": Decimal(".10"), "ai": Decimal(".30"), "frontend": Decimal(".20")}
HISTORICAL_PURSES = (
    "pre-v4-release-a8d9993eecf9895a6ca220e03cdce3df4f34b593",
    "pre-v4-release-e7c6b552dec0006c4f36e02188764dcf554942e2",
    "pre-v4-release-3bc06d0db1c9b38233c04558f8093ce956258ab2",
)


def lane_scope(lane: str) -> str:
    if lane not in LANE_CAPS:
        raise ValueError("Unknown approved go-live lane")
    return f"go-live/{DAY}/{lane}"


def allocation(connection: psycopg.Connection, sha: str) -> dict[str, str | int]:
    """Include ALL scopes, legacy reserves and every unused authorized purse."""
    actual, v4, known, unknown = connection.execute(
        "SELECT coalesce(sum(charged_usd),0),"
        "coalesce(sum(charged_usd) FILTER(WHERE scope='final-evaluation-v4'),0),"
        "coalesce(sum(actual_usd),0),count(*) FILTER(WHERE actual_usd IS NULL) "
        "FROM llm.reservations"
    ).fetchone()
    scopes = (*PRIOR_SCOPES, SCOPE, MODEL_COMPARE_SCOPE, "production")
    total, dev = connection.execute(
        "SELECT coalesce(sum(charged_usd),0),"
        "coalesce(sum(charged_usd) FILTER(WHERE scope=%s),0) "
        "FROM llm.reservations WHERE scope=ANY(%s)",
        (SCOPE, list(scopes)),
    ).fetchone()
    closed = actual - v4 - total
    controls, stress = [
        connection.execute(
            "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s", (scope,)
        ).fetchone()[0]
        for scope in ("dev-gate/controls-ablation", "dev-gate/controls-stress")
    ]
    if not (0 <= controls <= Decimal(".15") and 0 <= stress <= Decimal(".10") and closed >= 0):
        raise RuntimeError("Historical allocation requires review")
    base = (
        check_exposure(total, dev)
        + closed
        + Decimal(".15")
        - controls
        + Decimal(".08")
        + Decimal(".10")
        - stress
    )
    unused = Decimal(0)
    for name, cap in [(p, Decimal(".10")) for p in (*HISTORICAL_PURSES, run_id("release", sha))] + [
        (JUDGING_RUN, JUDGING_CAP)
    ]:
        row = connection.execute(
            "SELECT limit_usd FROM llm.runs WHERE scope='production' AND run_id=%s", (name,)
        ).fetchone()
        if row and row[0] != cap:
            raise RuntimeError("Existing purse cap differs")
        charged = connection.execute(
            "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope='production' AND run_id=%s",
            (name,),
        ).fetchone()[0]
        if charged > cap:
            raise RuntimeError("Purse exceeded")
        unused += cap - charged
    for lane, cap in LANE_CAPS.items():
        charged = connection.execute(
            "SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s",
            (lane_scope(lane),),
        ).fetchone()[0]
        if charged > cap:
            raise RuntimeError("Lane exceeded")
        unused += cap - charged
    maximum = base + unused
    if maximum > Decimal("15"):
        raise RuntimeError("Conservative cumulative ceiling exceeded")
    return {
        "known_usd": str(known),
        "retained_exposure_usd": str(actual),
        "unknown_reservations": unknown,
        "conservative_base_usd": str(base),
        "unused_authorized_usd": str(unused),
        "maximum_usd": str(maximum),
    }


def prepare(dsn: str, sha: str) -> dict:
    """One owner transaction; never reset, raise a cap or re-enable a breaker."""
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        policy = connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope='production' FOR UPDATE"
        ).fetchone()
        if policy not in ((Decimal(3), False), (Decimal(1), False)):
            raise RuntimeError("Production breaker changed/disabled")
        result = allocation(connection, sha)
        for name, cap in ((run_id("release", sha), Decimal(".10")), (JUDGING_RUN, JUDGING_CAP)):
            connection.execute(
                "INSERT INTO llm.runs VALUES('production',%s,%s,true) ON CONFLICT DO NOTHING",
                (name, cap),
            )
            if connection.execute(
                "SELECT limit_usd,enabled FROM llm.runs WHERE scope='production' AND run_id=%s",
                (name,),
            ).fetchone() != (cap, True):
                raise RuntimeError("Production purse missing/disabled")
        lanes = {}
        for lane, cap in LANE_CAPS.items():
            scope = lane_scope(lane)
            connection.execute(
                "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING", (scope, cap)
            )
            connection.execute(
                "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
                (scope, DAY, cap),
            )
            if connection.execute(
                "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (scope,)
            ).fetchone() != (cap, False) or connection.execute(
                "SELECT limit_usd,enabled FROM llm.runs WHERE scope=%s AND run_id=%s", (scope, DAY)
            ).fetchone() != (cap, True):
                raise RuntimeError("Lane policy changed/disabled")
            lanes[lane] = {"scope": scope, "run_id": DAY, "cap_usd": str(cap)}
        return {
            **result,
            "lanes": lanes,
            "judging_run": JUDGING_RUN,
            "judging_lifetime_usd": str(JUDGING_CAP),
        }


def activate_daily(dsn: str) -> None:
    """Lower production to approved USD1/UTC day, preserving every reservation."""
    with psycopg.connect(dsn) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        row = connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope='production' FOR UPDATE"
        ).fetchone()
        if row not in ((Decimal(3), False), (Decimal(1), False)):
            raise RuntimeError("Production breaker changed/disabled")
        connection.execute("UPDATE llm.limits SET daily_usd=1 WHERE scope='production'")


def lane_gate(store: Store, lane: str) -> PostgresSpendGate:
    """Reserve a conservative request maximum BEFORE sending the BFF request.

    On timeout, unknown cost or missing verified metadata settle(token, None),
    retain the reserve and stop. Known cost may settle down to zero; actual cost
    above the reserved maximum disables this lane. No retry resets a purse.
    """
    return PostgresSpendGate(store, scope=lane_scope(lane), run_id=DAY)


def settle_calls(gate: PostgresSpendGate, token: str, calls: list[dict]) -> Decimal:
    """Caller supplies ONLY independently read, per-turn execution call metadata.

    A missing cost or malformed receipt retains the request maximum and stops.
    Callers must not use concurrent aggregate production deltas for attribution.
    An empty verified call list is a deterministic zero-cost turn.
    """
    amounts = []
    try:
        for call in calls:
            cost = call.get("cost_usd")
            if cost is None:
                raise ValueError("Unknown call cost")
            amount = Decimal(str(cost))
            if not amount.is_finite() or amount < 0:
                raise ValueError("Invalid call cost")
            amounts.append(amount)
    except (ValueError, ArithmeticError):
        gate.settle(token, None)
        raise RuntimeError("Unknown turn cost retained; stop this lane") from None
    total = sum(amounts, Decimal(0))
    gate.settle(token, float(total))
    return total
