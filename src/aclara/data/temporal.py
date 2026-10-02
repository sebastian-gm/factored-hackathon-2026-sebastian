"""Fail closed on operational temporal facts; retain analytical history."""

# ruff: noqa: S608 -- all predicates and identifiers are repository-defined.
from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from aclara.data.pipeline import _fetchone, _sql_identifier, _sql_string

CUSTOMER_SAFE = "c.last_updated < as_of"
PRODUCT_SAFE = """p.last_updated < as_of AND
p.opening_date <= (as_of-INTERVAL 6 HOUR-INTERVAL 1 MICROSECOND)::DATE"""
TRANSACTION_SAFE = """t.customer_id=p.customer_id AND
t.transaction_date::DATE>=p.opening_date AND t.process_date>=p.opening_date AND
t.process_date=(t.transaction_date-INTERVAL 6 HOUR)::DATE"""
WINDOW = "t.transaction_date>=as_of-INTERVAL 120 DAY AND t.transaction_date<as_of"


def register_temporal_exports(db: duckdb.DuckDBPyConnection, gold: Path) -> None:
    """Temporary views keep the source warehouse strictly read-only."""
    for table in ("customers", "products", "transactions"):
        db.execute(
            f"CREATE OR REPLACE TEMP VIEW {_sql_identifier('served_' + table)} AS SELECT * FROM read_parquet({_sql_string(str(gold / (table + '.parquet')))})"
        )


def temporal_profile(db: duckdb.DuckDBPyConnection, clock: str) -> dict[str, Any]:
    """Aggregate eligibility flags, counting the union once per transaction."""
    db.execute("SET TimeZone='UTC'")
    db.execute(
        "CREATE OR REPLACE TEMP TABLE temporal_clock AS SELECT ?::TIMESTAMPTZ as_of", [clock]
    )
    safe = f"({CUSTOMER_SAFE}) AND ({PRODUCT_SAFE}) AND ({TRANSACTION_SAFE})"
    total, blocked, before_open, bad_date, customer_future, product_future = _fetchone(
        db,
        f"""SELECT count(*),count(*) FILTER (WHERE NOT ({safe})),
        count(*) FILTER (WHERE t.transaction_date::DATE<p.opening_date OR t.process_date<p.opening_date),
        count(*) FILTER (WHERE t.process_date<>(t.transaction_date-INTERVAL 6 HOUR)::DATE),
        count(*) FILTER (WHERE NOT ({CUSTOMER_SAFE})),
        count(*) FILTER (WHERE NOT ({PRODUCT_SAFE}))
        FROM silver.transactions t JOIN silver.products p USING(product_id)
        JOIN silver.customers c ON t.customer_id=c.customer_id CROSS JOIN temporal_clock
        WHERE {WINDOW}""",
    )
    return {
        "version": 1,
        "window_rows": total,
        "blocked_transaction_rows": blocked,
        "eligible_transaction_rows": total - blocked,
        "window_before_open": before_open,
        "window_business_date_mismatch": bad_date,
        "window_untrusted_customer_state": customer_future,
        "window_untrusted_product_state": product_future,
        "treatment": "exclude from operational gold; retain silver and historical matcher ledger",
    }


def validate_temporal_exports(db: duckdb.DuckDBPyConnection, clock: str) -> dict[str, int]:
    """Read actual served_* Parquets against silver before any bank connection.

    The caller registers served_customers/products/transactions. Authority fields
    must match eligible source facts; checking IDs alone would miss altered dates
    and statuses. Return counts only, never offending records or keys.
    """
    db.execute("SET TimeZone='UTC'")
    db.execute(
        "CREATE OR REPLACE TEMP TABLE temporal_clock AS SELECT ?::TIMESTAMPTZ as_of", [clock]
    )
    queries = {
        "customers": f"""SELECT count(*) FROM served_customers g
            LEFT JOIN silver.customers c USING(customer_id) CROSS JOIN temporal_clock
            WHERE c.customer_id IS NULL OR NOT ({CUSTOMER_SAFE})
            OR g.customer_status IS DISTINCT FROM c.customer_status""",
        "products": f"""SELECT count(*) FROM served_products g
            LEFT JOIN silver.products p USING(product_id)
            LEFT JOIN silver.customers c ON p.customer_id=c.customer_id
            LEFT JOIN served_customers gc ON g.customer_id=gc.customer_id
            CROSS JOIN temporal_clock
            WHERE p.product_id IS NULL OR c.customer_id IS NULL OR gc.customer_id IS NULL
            OR NOT (({CUSTOMER_SAFE}) AND ({PRODUCT_SAFE}))
            OR g.customer_id IS DISTINCT FROM p.customer_id
            OR g.product_status IS DISTINCT FROM p.product_status
            OR g.opening_date IS DISTINCT FROM p.opening_date""",
        "transactions": f"""SELECT count(*) FROM served_transactions g
            LEFT JOIN silver.transactions t USING(transaction_id)
            LEFT JOIN silver.products p ON t.product_id=p.product_id
            LEFT JOIN silver.customers c ON t.customer_id=c.customer_id
            LEFT JOIN served_customers gc ON g.customer_id=gc.customer_id
            LEFT JOIN served_products gp ON g.product_id=gp.product_id
            CROSS JOIN temporal_clock
            WHERE t.transaction_id IS NULL OR p.product_id IS NULL OR c.customer_id IS NULL
            OR gc.customer_id IS NULL OR gp.product_id IS NULL
            OR NOT (({CUSTOMER_SAFE}) AND ({PRODUCT_SAFE}) AND ({TRANSACTION_SAFE}) AND ({WINDOW}))
            OR g.customer_id IS DISTINCT FROM t.customer_id
            OR g.product_id IS DISTINCT FROM t.product_id
            OR g.transaction_date IS DISTINCT FROM t.transaction_date
            OR g.process_date IS DISTINCT FROM t.process_date""",
    }
    counts = {table: int(_fetchone(db, query)[0]) for table, query in queries.items()}
    if any(counts.values()):
        raise ValueError("temporal serving preflight failed; rebuild eligible operational gold")
    return counts
