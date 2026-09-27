"""Shared contract conversions and the backwards-compatible pipeline entry point."""

from __future__ import annotations

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import polars as pl
import yaml  # type: ignore[import-untyped]


def _normalize_bank_clock(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("BANK_CLOCK must include a timezone")
    return parsed.astimezone(UTC).isoformat()


SQL_TYPES = {
    "string": "VARCHAR",
    "integer": "BIGINT",
    "number": "DOUBLE",
    "boolean": "BOOLEAN",
    "date": "DATE",
    "timestamp": "TIMESTAMPTZ",
}


POLARS_TYPES: dict[str, Any] = {
    "string": pl.String,
    "integer": pl.Int64,
    "number": pl.Float64,
    "boolean": pl.Boolean,
    "date": pl.Date,
    "timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
}


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _fetchone(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    parameters: list[Any] | None = None,
) -> tuple[Any, ...]:
    result = (
        connection.execute(query).fetchone()
        if parameters is None
        else connection.execute(query, parameters).fetchone()
    )
    if result is None:
        raise RuntimeError("Expected a DuckDB result row")
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_files(source: Path, table: str) -> list[Path]:
    dimension = source / f"{table}.csv"
    paths = [dimension] if dimension.is_file() else sorted((source / table).rglob("*.csv"))
    if not paths:
        raise FileNotFoundError(f"no CSV files found for requested table {table}")
    return paths


def _read_contract(table: str) -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[3]
    with (repository_root / "contracts" / f"{table}.yaml").open(encoding="utf-8") as stream:
        contract = yaml.safe_load(stream)
    if not isinstance(contract, dict):
        raise ValueError(f"invalid contract for {table}")
    if contract.get("table") != table:
        raise ValueError(f"contract table name does not match {table}")
    return contract


def _hash_version(entries: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda row: row["relative_path"]):
        digest.update(entry["relative_path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _cast_expression(column: str, rules: dict[str, Any], normalization: dict[str, Any]) -> str:
    identifier = _sql_identifier(column)
    source = f"TRY_CAST(t.{identifier} AS {SQL_TYPES[rules['type']]})"
    if column == "country" or column == "transaction_country":
        values = normalization.get(column, {})
        cases = " ".join(
            f"WHEN t.{identifier} = {_sql_string(str(label))} THEN {_sql_string(str(code))}"
            for label, code in values.items()
        )
        return f"CASE {cases} ELSE CAST(t.{identifier} AS VARCHAR) END"
    if column == "product_type":
        values = normalization.get(column, {})
        cases = " ".join(
            f"WHEN t.{identifier} = {_sql_string(str(label))} THEN {_sql_string(str(code))}"
            for label, code in values.items()
        )
        return f"CASE {cases} ELSE CAST(t.{identifier} AS VARCHAR) END"
    return source


def _pipeline_version() -> str:
    repository = Path(__file__).resolve().parents[3]
    try:
        return subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return "working-tree"


def build(source: Path, lake: Path) -> dict[str, Any]:
    """Build a DQ-gated atomic snapshot; legacy callers use the same path as the CLI."""
    from aclara.data.snapshot import build_snapshot

    return build_snapshot(source, lake)
