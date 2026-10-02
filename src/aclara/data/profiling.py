"""Aggregate-only missingness and duplicate fingerprints; never return record keys."""

# ruff: noqa: S608 -- identifiers are quoted; predicates and keys are repository-defined.
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import duckdb

from aclara.data.pipeline import _fetchone, _read_contract, _sql_identifier

BUSINESS_KEYS: dict[str, tuple[str, ...]] = {
    "customers": ("document_number",),
    "products": ("product_number",),
    "service_agents": ("employee_code",),
    "daily_exchange_rates": ("date", "source_currency", "target_currency"),
    "transactions": (
        "customer_id",
        "product_id",
        "transaction_date",
        "transaction_type",
        "amount",
        "currency",
        "merchant_name",
    ),
    "call_center_interactions": (
        "customer_id",
        "agent_id",
        "interaction_date",
        "channel",
        "interaction_type",
    ),
    "complaints": ("customer_id", "creation_date", "case_type", "category", "subcategory"),
    "satisfaction_surveys": ("interaction_id", "customer_id", "survey_type"),
    "call_transcripts": ("interaction_id",),
    "digital_events": (
        "session_id",
        "event_date",
        "event_type",
        "event_category",
        "channel",
        "action",
        "element_id",
        "product_id",
    ),
    "branches": ("branch_code",),
    "marketing_campaigns": ("campaign_name", "start_date", "end_date", "campaign_type"),
    "campaign_sends": ("campaign_id", "customer_id", "send_date", "send_channel"),
}


def column_null_profile(db: duckdb.DuckDBPyConnection, table: str) -> list[dict[str, Any]]:
    """SQL NULLs after contract conversion, with every column's row denominator."""
    columns = _read_contract(table)["columns"]
    expressions = []
    for name, rules in columns.items():
        field = _sql_identifier(name)
        expressions += [
            f"count(*) FILTER (WHERE {field} IS NULL)",
            f"count(*) FILTER (WHERE {field} IS NOT NULL AND trim({field})='')"
            if rules["type"] == "string"
            else "0",
        ]
    values = _fetchone(
        db, f"SELECT count(*),{','.join(expressions)} FROM silver.{_sql_identifier(table)}"
    )
    rows = int(values[0])
    return [
        {
            "table": table,
            "column": name,
            "rows": rows,
            "nullable": rules.get("nullable", True),
            "nulls": int(values[1 + 2 * index]),
            "null_rate": int(values[1 + 2 * index]) / rows if rows else None,
            "blank_nonnull": int(values[2 + 2 * index]),
        }
        for index, (name, rules) in enumerate(columns.items())
    ]


def duplicate_counts(
    db: duckdb.DuckDBPyConnection, relation: str, columns: Sequence[str], *, where: str = "TRUE"
) -> dict[str, int]:
    """Count excess records, not all members, without exposing a duplicate key."""
    keys = ",".join(_sql_identifier(name) for name in columns)
    groups, excess, members = _fetchone(
        db,
        f"SELECT count(*),coalesce(sum(n-1),0),coalesce(sum(n),0) FROM (SELECT count(*) n FROM {relation} WHERE {where} GROUP BY {keys} HAVING count(*)>1)",
    )
    return {"groups": int(groups), "excess_rows": int(excess), "member_rows": int(members)}


def duplicate_profile(
    db: duckdb.DuckDBPyConnection,
    table: str,
    columns: Sequence[str],
    primary_key: Sequence[str],
    *,
    schema: str = "silver",
) -> dict[str, Any]:
    relation = f"{_sql_identifier(schema)}.{_sql_identifier(table)}"
    pk = duplicate_counts(db, relation, primary_key)
    # Unique PKs logically rule out exact full-row duplicates, without a wide GROUP BY.
    exact = duplicate_counts(db, relation, columns) if pk["excess_rows"] else dict(pk)
    # Dates/currencies in composite natural keys are event facts, not regenerated IDs.
    surrogate_ids = {name for name in primary_key if name.endswith("_id")}
    payload = [name for name in columns if name not in {*surrogate_ids, "process_date"}]
    result: dict[str, Any] = {
        "primary_key": pk,
        "exact_record": exact,
        "payload_without_id_or_partition_date": duplicate_counts(db, relation, payload),
        "business_key_columns": list(BUSINESS_KEYS[table]),
        "business_key": duplicate_counts(db, relation, BUSINESS_KEYS[table]),
    }
    if table == "digital_events":
        keys = ("customer_id", "event_date", "event_type", "channel", "action", "product_id")
        result["cross_session_event_columns"] = list(keys)
        result["cross_session_event"] = duplicate_counts(
            db, relation, keys, where="customer_id IS NOT NULL"
        )
    return result
