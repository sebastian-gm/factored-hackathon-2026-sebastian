"""Preserve serving facts and mark temporal uncertainty for the policy gate."""

# ruff: noqa: S608 -- all predicates and identifiers are repository-defined.
from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from aclara.data.pipeline import _fetchone, _sql_identifier, _sql_string

WINDOW = "t.transaction_date>=as_of-INTERVAL 120 DAY AND t.transaction_date<as_of"
TEMPORAL_REASONS = (
    "before_product_open",
    "after_bank_clock",
    "product_updated_after_clock",
    "customer_updated_after_clock",
)
TEMPORAL_PREDICATES = (
    "t.transaction_date::DATE<p.opening_date OR t.process_date<p.opening_date",
    "t.transaction_date>=as_of",
    "p.last_updated>=as_of",
    "c.last_updated>=as_of",
)


def temporal_reason_sql() -> str:
    """First applicable reason in contract order; NULL passes these four checks."""
    clauses = " ".join(
        f"WHEN {predicate} THEN '{reason}'"
        for reason, predicate in zip(TEMPORAL_REASONS, TEMPORAL_PREDICATES, strict=True)
    )
    return f"CASE {clauses} ELSE NULL::VARCHAR END"


def register_temporal_exports(db: duckdb.DuckDBPyConnection, gold: Path) -> None:
    """Temporary views keep the source warehouse strictly read-only."""
    for table in ("customers", "products", "transactions"):
        db.execute(
            f"CREATE OR REPLACE TEMP VIEW {_sql_identifier('served_' + table)} AS SELECT * FROM read_parquet({_sql_string(str(gold / (table + '.parquet')))})"
        )


def temporal_profile(db: duckdb.DuckDBPyConnection, clock: str) -> dict[str, Any]:
    """Count flags and overlapping findings; never remove analytical/serving rows."""
    db.execute("SET TimeZone='UTC'")
    db.execute(
        "CREATE OR REPLACE TEMP TABLE temporal_clock AS SELECT ?::TIMESTAMPTZ as_of", [clock]
    )
    counts = _fetchone(
        db,
        f"""SELECT count(*),count(*) FILTER (WHERE ({temporal_reason_sql()}) IS NOT NULL),
        {",".join(f"count(*) FILTER (WHERE {predicate})" for predicate in TEMPORAL_PREDICATES)},
        count(*) FILTER (WHERE t.process_date<>(t.transaction_date-INTERVAL 6 HOUR)::DATE)
        FROM silver.transactions t JOIN silver.products p USING(product_id)
        JOIN silver.customers c ON t.customer_id=c.customer_id CROSS JOIN temporal_clock
        WHERE {WINDOW}""",
    )
    primary_counts = _fetchone(
        db,
        f"""SELECT {",".join(f"count(*) FILTER (WHERE reason='{reason}')" for reason in TEMPORAL_REASONS)}
        FROM (SELECT {temporal_reason_sql()} reason
        FROM silver.transactions t JOIN silver.products p USING(product_id)
        JOIN silver.customers c ON t.customer_id=c.customer_id CROSS JOIN temporal_clock
        WHERE {WINDOW})""",
    )
    return {
        "version": 2,
        "window_rows": counts[0],
        "flagged_transaction_rows": counts[1],
        "unflagged_transaction_rows": counts[0] - counts[1],
        "findings": dict(zip(TEMPORAL_REASONS, counts[2:6], strict=True)),
        "primary_reason_counts": dict(zip(TEMPORAL_REASONS, primary_counts, strict=True)),
        "window_business_date_mismatch_warning": counts[6],
        "treatment": "retain all serving-window rows; flags require lead-owned automation handoff",
    }


def _different_fields(expressions: dict[str, str]) -> str:
    """Null-safe comparison with repository-defined source expressions."""
    return " OR ".join(
        f"g.{_sql_identifier(field)} IS DISTINCT FROM ({expression})"
        for field, expression in expressions.items()
    )


def validate_temporal_exports(db: duckdb.DuckDBPyConnection, clock: str) -> dict[str, int]:
    """Verify complete row sets, authority fields and flags before a bank connection.

    Flagged facts remain valid serving data. Missing/cleared/incorrect flags and
    removed, duplicated or changed non-lineage projection fields fail the load.
    Source-equivalence covers customers/products/transactions; other serving
    tables and the five underscore-prefixed lineage fields are outside this
    preflight. Return aggregates only.
    """
    db.execute("SET TimeZone='UTC'")
    db.execute(
        "CREATE OR REPLACE TEMP TABLE temporal_clock AS SELECT ?::TIMESTAMPTZ as_of", [clock]
    )
    columns = {row[0]: row[1] for row in db.execute("DESCRIBE served_transactions").fetchall()}
    if columns.get("temporal_quality_reason") != "VARCHAR":
        raise ValueError("temporal serving preflight failed; nullable text reason column required")
    # Every non-lineage field in these three serving projections is compared.
    # FX expressions deliberately read silver rates, never gold/cached FX values.
    customer_fields = {field: f"c.{field}" for field in ("country", "segment", "customer_status")}
    product_fields = {
        field: f"p.{field}"
        for field in ("customer_id", "product_type", "currency", "product_status", "opening_date")
    }
    transaction_fields = {
        field: f"t.{field}"
        for field in (
            "customer_id",
            "product_id",
            "transaction_date",
            "process_date",
            "transaction_type",
            "transaction_category",
            "amount",
            "currency",
            "amount_usd",
            "channel",
            "merchant_name",
            "merchant_category",
            "transaction_country",
            "transaction_status",
            "fraud_score",
        )
    }
    transaction_fields.update(
        {
            "customer_country": "c.country",
            "product_status": "p.product_status",
            "amount_usd_recomputed": "CASE WHEN t.currency='USD' THEN t.amount ELSE t.amount*f.exchange_rate END::DOUBLE",
            "fx_date": "CASE WHEN t.currency='USD' THEN t.process_date ELSE f.date END::DATE",
            "fx_nearest_prior": "coalesce(t.currency<>'USD' AND f.date<t.process_date,false)::BOOLEAN",
            "foreign_transaction": "(t.transaction_country<>c.country)::BOOLEAN",
            "temporal_quality_reason": temporal_reason_sql(),
        }
    )
    queries = {
        "customers": f"""SELECT count(*) FROM served_customers g
            LEFT JOIN silver.customers c USING(customer_id)
            WHERE c.customer_id IS NULL OR {_different_fields(customer_fields)}""",
        "products": f"""SELECT count(*) FROM served_products g
            LEFT JOIN silver.products p USING(product_id)
            WHERE p.product_id IS NULL OR {_different_fields(product_fields)}""",
        "transactions": f"""SELECT count(*) FROM served_transactions g
            LEFT JOIN silver.transactions t USING(transaction_id)
            LEFT JOIN silver.products p ON t.product_id=p.product_id
            LEFT JOIN silver.customers c ON t.customer_id=c.customer_id
            ASOF LEFT JOIN (SELECT * FROM silver.daily_exchange_rates WHERE target_currency='USD') f
              ON t.currency=f.source_currency AND t.process_date>=f.date
            CROSS JOIN temporal_clock
            WHERE t.transaction_id IS NULL OR p.product_id IS NULL OR c.customer_id IS NULL
            OR NOT ({WINDOW}) OR {_different_fields(transaction_fields)}""",
    }
    counts = {table: int(_fetchone(db, query)[0]) for table, query in queries.items()}
    for table, key in (
        ("customers", "customer_id"),
        ("products", "product_id"),
        ("transactions", "transaction_id"),
    ):
        expected = (
            f"SELECT {key} FROM silver.transactions t CROSS JOIN temporal_clock WHERE {WINDOW}"
            if table == "transactions"
            else f"SELECT {key} FROM silver.{table}"
        )
        actual = f"SELECT {key} FROM served_{table}"
        counts[table] += int(
            _fetchone(
                db,
                f"SELECT count(*) FROM (({actual} EXCEPT ALL {expected}) UNION ALL ({expected} EXCEPT ALL {actual}))",
            )[0]
        )
    if any(counts.values()):
        raise ValueError(
            "temporal serving preflight failed; rebuild complete, correctly flagged gold"
        )
    return counts
