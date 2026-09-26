"""Aggregate-only P1 ingestion, contract promotion, and data checks."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandera.polars as pa
import polars as pl
import yaml  # type: ignore[import-untyped]

LOGGER = logging.getLogger("aclara.data")
TABLES = ("customers", "products", "transactions")
BANK_CLOCK = "2026-06-18T06:00:00+00:00"
SOURCE_END_DATE = "2026-06-17"
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
EXPECTED: dict[str, tuple[Any, str]] = {
    "customers.rows": (150_000, "exact"),
    "customers.files": (1, "exact"),
    "customers.source_header_variant_count": (1, "exact"),
    "customers.source_unknown_column_count": (0, "exact"),
    "products.rows": (400_000, "exact"),
    "products.files": (1, "exact"),
    "products.source_header_variant_count": (1, "exact"),
    "products.source_unknown_column_count": (0, "exact"),
    "products.duplicate_product_numbers": (6, "exact"),
    "transactions.rows": (4_425_008, "exact"),
    "transactions.files": (1_097, "exact"),
    "transactions.source_header_variant_count": (1, "exact"),
    "transactions.source_unknown_column_count": (0, "exact"),
    "customers.duplicate_primary_keys": (0, "exact"),
    "products.duplicate_primary_keys": (0, "exact"),
    "transactions.duplicate_primary_keys": (0, "exact"),
    "transactions.orphan_customer_rows": (0, "exact"),
    "transactions.orphan_product_rows": (0, "exact"),
    "transactions.product_owner_mismatch_rows": (0, "exact"),
    "transactions.fraud_score_gt_30_rows": (2_373, "exact"),
    "transactions.fraud_score_gt_30_not_labeled_fraud": (0, "exact"),
    "transactions.mxn_rows": (0, "exact"),
    "transactions.active_product_share": (1.0, "ratio_0.0001"),
    "transactions.process_date_minus_6h_match_share": (0.999988, "ratio_0.0001"),
    "transactions.process_date_minus_6h_match_share_by_customer_country.AR": (
        0.999988,
        "ratio_0.0001",
    ),
    "transactions.process_date_minus_6h_match_share_by_customer_country.CO": (
        0.999988,
        "ratio_0.0001",
    ),
    "transactions.process_date_minus_6h_match_share_by_customer_country.MX": (
        0.999988,
        "ratio_0.0001",
    ),
    "transactions.before_product_opening_rows": (827_610, "exact"),
    "customers.last_updated_after_source_end": (9_316, "exact"),
    "customers.last_updated_max_date": ("2027-06-15", "exact"),
    "products.last_updated_after_source_end": (25_113, "exact"),
    "products.last_updated_max_date": ("2027-06-15", "exact"),
    "transactions.rows_last_120_days": (494_755, "exact"),
    "transactions.rows_last_365_days": (1_483_415, "exact"),
    "transactions.atm_purchases_rows": (325_993, "exact"),
    "transactions.pos_deposits_rows": (213_678, "exact"),
    "transactions.fraud_rows": (4_316, "exact"),
    "transactions.latest_transaction_utc": ("2026-06-18 05:59:41+00", "exact"),
    "transactions.business_date_range": (["2023-06-17", "2026-06-17"], "exact"),
    "transactions.candidate_counts_last_120_days.median": (3.0, "exact"),
    "transactions.candidate_counts_last_120_days.p90": (8.0, "exact"),
    "transactions.candidate_counts_last_120_days.max": (28, "exact"),
    "transactions.candidate_counts_last_120_days.customers_with_none": (26_475, "exact"),
    "transactions.candidate_counts_all.median": (29.0, "exact"),
    "transactions.candidate_counts_all.p90": (59.0, "exact"),
    "transactions.candidate_counts_all.max": (150, "exact"),
    "transactions.candidate_counts_all.customers_with_none": (15_485, "exact"),
    "transactions.pending_rows_over_14_days_last_120_days": (8_741, "exact"),
    "transactions.pending_rows_last_120_days": (9_963, "exact"),
    "transactions.merchant_name_distinct_purchases": (24, "exact"),
    "transactions.source_country_counts.Mexico": (40_515, "exact"),
    "transactions.raw_mexico_label_rows_for_mx_customers": (18_412, "exact"),
    "transactions.fraud_null_score_rows": (891, "exact"),
    "transactions.fraud_score_27_to_30_rows": (353_682, "exact"),
    "transactions.fraud_score_27_to_30_fraud_rows": (111, "exact"),
    "transactions.fraud_score_gt_30_share_of_scored_fraud": (0.69, "ratio_0.02"),
    "transactions.fraud_score_gt_30_share_of_all_fraud": (0.55, "ratio_0.02"),
    "transactions.has_settlement_expiry_reversal_timestamps": (False, "exact"),
    "customers.country_share.MX": (0.499, "ratio_0.005"),
    "customers.country_share.CO": (0.302, "ratio_0.005"),
    "customers.country_share.AR": (0.199, "ratio_0.005"),
    "customers.segment_share.Basic": (0.60, "ratio_0.01"),
    "customers.segment_share.Plus": (0.25, "ratio_0.01"),
    "customers.segment_share.Premium": (0.10, "ratio_0.01"),
    "customers.segment_share.Student": (0.05, "ratio_0.01"),
    "customers.status_share.Active": (0.85, "ratio_0.01"),
    "customers.status_share.Inactive": (0.10, "ratio_0.01"),
    "customers.status_share.Suspended": (0.03, "ratio_0.005"),
    "customers.status_share.Closed": (0.02, "ratio_0.005"),
    "customers.detected_accent_null_share": (0.30, "ratio_0.01"),
    "customers.credit_score_null_share": (0.15, "ratio_0.01"),
    "customers.credit_score_range": ([422, 850], "exact"),
    "customers.mexican_document_type_dni_share": (1.0, "ratio_0.0001"),
    "products.status_share.Active": (0.85, "ratio_0.01"),
    "products.status_share.Blocked": (0.05, "ratio_0.01"),
    "products.status_share.Closed": (0.08, "ratio_0.01"),
    "products.status_share.Suspended": (0.02, "ratio_0.005"),
    "transactions.status_share.Approved": (0.92, "ratio_0.01"),
    "transactions.status_share.Declined": (0.05, "ratio_0.01"),
    "transactions.status_share.Pending": (0.02, "ratio_0.01"),
    "transactions.status_share.Reversed": (0.01, "ratio_0.005"),
    "transactions.type_share.Purchase": (0.24, "ratio_0.01"),
    "transactions.type_share.Withdrawal": (0.22, "ratio_0.01"),
    "transactions.type_share.Transfer": (0.20, "ratio_0.01"),
    "transactions.type_share.Payment": (0.17, "ratio_0.01"),
    "transactions.type_share.Deposit": (0.14, "ratio_0.01"),
    "transactions.type_share.Adjustment": (0.03, "ratio_0.01"),
    "transactions.merchant_name_null_share": (0.77, "ratio_0.02"),
    "transactions.transaction_category_null_share": (0.61, "ratio_0.02"),
    "transactions.amount_usd_quantiles_disputable.p50": (320.0, "approx_0.05"),
    "transactions.amount_usd_quantiles_disputable.p75": (472.0, "approx_0.05"),
    "transactions.amount_usd_quantiles_disputable.p90": (1_265.0, "approx_0.05"),
    "transactions.amount_usd_quantiles_disputable.p95": (1_633.0, "approx_0.05"),
    "transactions.amount_usd_quantiles_disputable.p99": (1_927.0, "approx_0.05"),
    "transactions.purchase_amount_usd_max": (500.0, "approx_0.05"),
    "transactions.withdrawal_amount_usd_max": (500.0, "approx_0.05"),
    "transactions.payment_amount_usd_median": (1_026.0, "approx_0.05"),
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


def _scalar(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    parameters: list[Any] | None = None,
) -> Any:
    return _fetchone(connection, query, parameters)[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _header_and_count(path: Path) -> tuple[list[str], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader, [])
        row_count = sum(1 for _ in reader)
    return header, row_count


def _source_files(source: Path, table: str) -> list[Path]:
    dimension = source / f"{table}.csv"
    candidates = [dimension] if dimension.is_file() else sorted((source / table).rglob("*.csv"))
    if not candidates:
        raise FileNotFoundError(f"no CSV files found for requested table {table}")
    return candidates


def _read_contract(table: str) -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[3]
    with (repository_root / "contracts" / f"{table}.yaml").open(encoding="utf-8") as stream:
        contract = yaml.safe_load(stream)
    if not isinstance(contract, dict):
        raise ValueError(f"invalid contract for {table}")
    if contract.get("table") != table:
        raise ValueError(f"contract table name does not match {table}")
    return contract


def _read_previous_manifest(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    previous = duckdb.connect(":memory:")
    try:
        rows = previous.execute(
            "SELECT relative_path, sha256, first_seen FROM read_parquet(?)", [str(path)]
        ).fetchall()
    finally:
        previous.close()
    return {
        str(relative): {"sha256": str(digest), "first_seen": str(first_seen)}
        for relative, digest, first_seen in rows
    }


def _hash_version(entries: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda row: row["relative_path"]):
        digest.update(entry["relative_path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _schema_check(
    table: str,
    contract: dict[str, Any],
    source_files: list[Path],
    source_root: Path,
) -> dict[str, Any]:
    required = {
        column
        for column, rules in contract["columns"].items()
        if not bool(rules.get("nullable", True))
    }
    expected_columns = set(contract["columns"])
    missing_files = 0
    unknown_columns: set[str] = set()
    header_hashes: dict[Path, str] = {}
    source_columns: set[str] = set()
    for path in source_files:
        with path.open("rb") as stream:
            first_line = stream.readline().lstrip(b"\xef\xbb\xbf")
        header_hashes[path] = hashlib.sha256(first_line).hexdigest()
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            columns = set(next(csv.reader(stream), []))
        source_columns.update(columns)
        if required - columns:
            missing_files += 1
        unknown_columns.update(columns - expected_columns)
    if missing_files:
        raise ValueError(f"{table}: {missing_files} source objects miss required contract columns")
    return {
        "missing_required_files": missing_files,
        "unknown_columns": sorted(unknown_columns),
        "source_columns": sorted(source_columns),
        "header_hashes": header_hashes,
        "source_root": source_root,
    }


def _make_manifest(
    files_by_table: dict[str, list[Path]],
    schema_metadata: dict[str, dict[str, Any]],
    source_root: Path,
    previous: dict[str, dict[str, Any]],
    lake: Path,
) -> tuple[str, list[dict[str, Any]]]:
    current: list[dict[str, Any]] = []
    first_seen = datetime.now(UTC).isoformat()
    for table, paths in files_by_table.items():
        headers = schema_metadata[table]["header_hashes"]
        for path in paths:
            relative = path.relative_to(source_root).as_posix()
            digest = _sha256(path)
            previous_entry = previous.get(relative)
            status = "new" if previous_entry is None else "unchanged"
            if previous_entry is not None and previous_entry["sha256"] != digest:
                status = "changed"
            _, row_count = _header_and_count(path)
            current.append(
                {
                    "relative_path": relative,
                    "table_name": table,
                    "size_bytes": path.stat().st_size,
                    "mtime_ns": path.stat().st_mtime_ns,
                    "sha256": digest,
                    "header_sha256": headers[path],
                    "row_count": row_count,
                    "first_seen": previous_entry["first_seen"] if previous_entry else first_seen,
                    "last_seen": first_seen,
                    "status": status,
                }
            )
    version = _hash_version(current)
    all_rows = list(current)
    current_names = {entry["relative_path"] for entry in current}
    for relative, entry in previous.items():
        if relative not in current_names:
            all_rows.append(
                {
                    "relative_path": relative,
                    "table_name": relative.split("/", maxsplit=1)[0].removesuffix(".csv"),
                    "size_bytes": 0,
                    "mtime_ns": 0,
                    "sha256": entry["sha256"],
                    "header_sha256": "",
                    "row_count": 0,
                    "first_seen": entry["first_seen"],
                    "last_seen": first_seen,
                    "status": "removed",
                }
            )
    manifest_path = lake / "_meta" / "manifest.parquet"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            "CREATE TABLE manifest (relative_path VARCHAR, table_name VARCHAR, size_bytes BIGINT, "
            "mtime_ns BIGINT, sha256 VARCHAR, header_sha256 VARCHAR, row_count BIGINT, "
            "first_seen VARCHAR, last_seen VARCHAR, status VARCHAR, dataset_version VARCHAR)",
        )
        connection.executemany(
            "INSERT INTO manifest VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    item["relative_path"],
                    item["table_name"],
                    item["size_bytes"],
                    item["mtime_ns"],
                    item["sha256"],
                    item["header_sha256"],
                    item["row_count"],
                    item["first_seen"],
                    item["last_seen"],
                    item["status"],
                    version,
                )
                for item in all_rows
            ],
        )
        manifest_target = str(manifest_path.resolve()).replace("'", "''")
        connection.execute(
            f"COPY manifest TO '{manifest_target}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        connection.close()
    bronze_root = lake / "bronze" / f"dataset_version={version}"
    for paths in files_by_table.values():
        for path in paths:
            target = bronze_root / path.relative_to(source_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or _sha256(target) != _sha256(path):
                shutil.copy2(path, target)
                if _sha256(target) != _sha256(path):
                    raise OSError("bronze copy verification failed")
    return version, all_rows


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


def _promote_silver(
    connection: duckdb.DuckDBPyConnection,
    table: str,
    files: list[Path],
    contract: dict[str, Any],
    source_root: Path,
    manifest: list[dict[str, Any]],
    version: str,
    lake: Path,
    pipeline_version: str,
) -> tuple[Path, int]:
    selected_manifest = {
        item["relative_path"]: item
        for item in manifest
        if item["status"] != "removed" and item["table_name"] == table
    }
    metadata = {item["relative_path"]: item for item in selected_manifest.values()}
    file_list = [str(path.resolve()) for path in files]
    relation = connection.read_csv(
        file_list,  # type: ignore[arg-type]  # DuckDB accepts a list of input files at runtime.
        header=True,
        all_varchar=True,
        union_by_name=True,
        filename=True,
        hive_partitioning=False,
    )
    raw_view = f"raw_{table}"
    relation.create_view(raw_view, replace=True)
    connection.execute(
        "CREATE OR REPLACE TEMP TABLE source_meta (filename VARCHAR, relative_path VARCHAR, sha256 VARCHAR)"
    )
    connection.executemany(
        "INSERT INTO source_meta VALUES (?, ?, ?)",
        [
            (
                str(path.resolve()),
                path.relative_to(source_root).as_posix(),
                metadata[path.relative_to(source_root).as_posix()]["sha256"],
            )
            for path in files
        ],
    )
    contract_columns: dict[str, dict[str, Any]] = contract["columns"]
    table_columns = {row[0] for row in connection.execute(f"DESCRIBE {raw_view}").fetchall()}
    projections: list[str] = []
    for column, rules in contract_columns.items():
        if column not in table_columns:
            continue
        expression = _cast_expression(column, rules, contract.get("normalization", {}))
        projections.append(f"{expression} AS {_sql_identifier(column)}")
    projections.extend(
        [
            "m.relative_path AS _source_file",
            "m.sha256 AS _source_sha256",
            f"{_sql_string(version)} AS _dataset_version",
            "CURRENT_TIMESTAMP AS _ingested_at",
            f"{_sql_string(pipeline_version)} AS _pipeline_version",
        ]
    )
    source_sql = ",\n        ".join(projections)
    silver_select = (
        f"SELECT {source_sql} FROM {raw_view} t "
        "JOIN source_meta m ON CAST(t.filename AS VARCHAR) = m.filename"
    )
    directory = lake / "silver" / table / f"dataset_version={version}"
    if directory.exists():
        shutil.rmtree(directory)
    directory.parent.mkdir(parents=True, exist_ok=True)
    target_sql = str(directory.resolve()).replace("'", "''")
    if table == "transactions":
        silver_select = (
            f"SELECT base.*, year(base.process_date) AS silver_year, month(base.process_date) AS silver_month "
            f"FROM ({silver_select}) base"
        )
        connection.execute(
            f"COPY ({silver_select}) TO '{target_sql}' "
            "(FORMAT PARQUET, PARTITION_BY (silver_year, silver_month), COMPRESSION ZSTD)"
        )
    else:
        directory.mkdir(parents=True, exist_ok=True)
        connection.execute(
            f"COPY ({silver_select}) TO '{target_sql}/data.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    parquet_files = sorted(directory.rglob("*.parquet"))
    if not parquet_files:
        raise RuntimeError(f"silver promotion created no Parquet files for {table}")
    row_count = sum(
        int(_scalar(connection, "SELECT count(*) FROM read_parquet(?)", [str(path)]))
        for path in parquet_files
    )
    _validate_sample(table, contract, directory)
    return directory, row_count


def _validate_sample(table: str, contract: dict[str, Any], directory: Path) -> None:
    files = sorted(directory.rglob("*.parquet"))
    sample = pl.read_parquet([str(path) for path in files], hive_partitioning=True).head(2_000)
    columns = {
        name: pa.Column(
            POLARS_TYPES[rules["type"]],
            nullable=bool(rules.get("nullable", True)),
        )
        for name, rules in contract["columns"].items()
        if name in sample.columns
    }
    columns.update(
        {
            "_source_file": pa.Column(pl.String, nullable=False),
            "_source_sha256": pa.Column(pl.String, nullable=False),
            "_dataset_version": pa.Column(pl.String, nullable=False),
            "_ingested_at": pa.Column(POLARS_TYPES["timestamp"], nullable=False),
            "_pipeline_version": pa.Column(pl.String, nullable=False),
        }
    )
    pa.DataFrameSchema(columns, strict=False).validate(sample)
    LOGGER.info("Pandera schema validated for %s sample (%d rows)", table, sample.height)


def _query_metrics(
    connection: duckdb.DuckDBPyConnection,
    version: str,
    silver_dirs: dict[str, Path],
    files_by_table: dict[str, list[Path]],
    source_root: Path,
    contracts: dict[str, dict[str, Any]],
    schema_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    profile: dict[str, Any] = {"dataset_version": version, "bank_clock": BANK_CLOCK, "tables": {}}

    def count(query: str) -> int:
        return int(_scalar(connection, query))

    for table, directory in silver_dirs.items():
        parquet_files = [str(path) for path in sorted(directory.rglob("*.parquet"))]
        connection.read_parquet(parquet_files).create_view(f"silver_{table}", replace=True)
        profile["tables"][table] = {
            "rows": count(f"SELECT count(*) FROM silver_{table}"),
            "files": len(files_by_table[table]),
            "source_header_variant_count": len(
                set(schema_metadata[table]["header_hashes"].values())
            ),
            "source_unknown_column_count": len(schema_metadata[table]["unknown_columns"]),
        }
    profile["contract_dq"] = {
        table: _required_null_counts(connection, table, contracts[table]) for table in TABLES
    }

    connection.execute(
        "CREATE OR REPLACE TEMP VIEW dim_customers AS SELECT * FROM silver_customers"
    )
    connection.execute("CREATE OR REPLACE TEMP VIEW dim_products AS SELECT * FROM silver_products")
    customer = profile["tables"]["customers"]
    customer.update(
        {
            "unique_customer_ids": count("SELECT count(DISTINCT customer_id) FROM dim_customers"),
            "duplicate_primary_keys": count(
                "SELECT count(*) - count(DISTINCT customer_id) FROM dim_customers"
            ),
            "country_share": _group_share(connection, "dim_customers", "country"),
            "segment_share": _group_share(connection, "dim_customers", "segment"),
            "status_share": _group_share(connection, "dim_customers", "customer_status"),
            "detected_accent_null_share": _null_share(
                connection, "dim_customers", "detected_accent"
            ),
            "postal_code_null_share": _null_share(connection, "dim_customers", "postal_code"),
            "credit_score_null_share": _null_share(connection, "dim_customers", "credit_score"),
            "credit_score_range": list(
                _fetchone(
                    connection, "SELECT min(credit_score), max(credit_score) FROM dim_customers"
                )
            ),
            "mexican_document_type_dni_share": _ratio(
                connection,
                "SELECT count(*) FILTER (WHERE document_type = 'DNI')::DOUBLE "
                "/ NULLIF(count(*), 0) FROM dim_customers WHERE country = 'MX'",
            ),
            "last_updated_after_source_end": count(
                f"SELECT count(*) FROM dim_customers WHERE CAST(last_updated AS DATE) > DATE '{SOURCE_END_DATE}'"
            ),
            "last_updated_max_date": _scalar(
                connection, "SELECT CAST(max(last_updated) AS DATE)::VARCHAR FROM dim_customers"
            ),
        }
    )
    product = profile["tables"]["products"]
    product.update(
        {
            "unique_product_ids": count("SELECT count(DISTINCT product_id) FROM dim_products"),
            "duplicate_primary_keys": count(
                "SELECT count(*) - count(DISTINCT product_id) FROM dim_products"
            ),
            "duplicate_product_numbers": count(
                "SELECT count(*) - count(DISTINCT product_number) FROM dim_products"
            ),
            "status_share": _group_share(connection, "dim_products", "product_status"),
            "product_type_share": _group_share(connection, "dim_products", "product_type"),
            "mxn_rows": count("SELECT count(*) FROM dim_products WHERE currency = 'MXN'"),
            "last_updated_after_source_end": count(
                f"SELECT count(*) FROM dim_products WHERE CAST(last_updated AS DATE) > DATE '{SOURCE_END_DATE}'"
            ),
            "last_updated_max_date": _scalar(
                connection, "SELECT CAST(max(last_updated) AS DATE)::VARCHAR FROM dim_products"
            ),
        }
    )
    tx = profile["tables"]["transactions"]
    connection.execute(
        "CREATE OR REPLACE TEMP VIEW joined_transactions AS "
        "SELECT t.*, p.customer_id AS product_customer_id, p.product_status, p.opening_date, "
        "p.last_updated AS product_last_updated, c.country AS customer_country "
        "FROM silver_transactions t LEFT JOIN dim_products p ON t.product_id = p.product_id "
        "LEFT JOIN dim_customers c ON t.customer_id = c.customer_id",
    )
    tx.update(
        {
            "unique_transaction_ids": count(
                "SELECT count(DISTINCT transaction_id) FROM silver_transactions"
            ),
            "duplicate_primary_keys": count(
                "SELECT count(*) - count(DISTINCT transaction_id) FROM silver_transactions"
            ),
            "status_share": _group_share(connection, "silver_transactions", "transaction_status"),
            "type_share": _group_share(connection, "silver_transactions", "transaction_type"),
            "country_share": _group_share(connection, "silver_transactions", "transaction_country"),
            "source_country_counts": _group_count(
                connection, "raw_transactions", "transaction_country"
            ),
            "raw_mexico_label_rows_for_mx_customers": count(
                "SELECT count(*) FROM raw_transactions r JOIN dim_customers c "
                "ON r.customer_id = c.customer_id "
                "WHERE r.transaction_country = 'Mexico' AND c.country = 'MX'"
            ),
            "foreign_country_rows": count(
                "SELECT count(*) FROM joined_transactions "
                "WHERE transaction_country IS DISTINCT FROM customer_country"
            ),
            "channel_type_pair_count": count(
                "SELECT count(*) FROM (SELECT DISTINCT channel, transaction_type FROM silver_transactions)"
            ),
            "amount_usd_null_share": _null_share(connection, "silver_transactions", "amount_usd"),
            "merchant_name_null_share": _null_share(
                connection, "silver_transactions", "merchant_name"
            ),
            "transaction_category_null_share": _null_share(
                connection, "silver_transactions", "transaction_category"
            ),
            "merchant_name_distinct_purchases": count(
                "SELECT count(DISTINCT merchant_name) FROM silver_transactions "
                "WHERE transaction_type = 'Purchase' AND merchant_name IS NOT NULL"
            ),
            "amount_usd_quantiles_disputable": _amount_quantiles(connection),
            "purchase_amount_usd_max": _scalar(
                connection,
                "SELECT max(amount_usd) FROM silver_transactions "
                "WHERE transaction_type = 'Purchase' AND amount_usd IS NOT NULL",
            ),
            "withdrawal_amount_usd_max": _scalar(
                connection,
                "SELECT max(amount_usd) FROM silver_transactions "
                "WHERE transaction_type = 'Withdrawal' AND amount_usd IS NOT NULL",
            ),
            "payment_amount_usd_median": _scalar(
                connection,
                "SELECT quantile_cont(amount_usd, 0.5) FROM silver_transactions "
                "WHERE transaction_type = 'Payment' AND amount_usd IS NOT NULL",
            ),
            "mxn_rows": count("SELECT count(*) FROM silver_transactions WHERE currency = 'MXN'"),
            "fraud_rows": count("SELECT count(*) FROM silver_transactions WHERE is_fraud"),
            "fraud_score_null_share": _null_share(connection, "silver_transactions", "fraud_score"),
            "fraud_score_gt_30_rows": count(
                "SELECT count(*) FROM silver_transactions WHERE fraud_score > 30"
            ),
            "fraud_score_gt_30_not_labeled_fraud": count(
                "SELECT count(*) FROM silver_transactions WHERE fraud_score > 30 AND NOT is_fraud"
            ),
            "fraud_null_score_rows": count(
                "SELECT count(*) FROM silver_transactions WHERE is_fraud AND fraud_score IS NULL"
            ),
            "fraud_score_27_to_30_rows": count(
                "SELECT count(*) FROM silver_transactions WHERE fraud_score > 27 AND fraud_score <= 30"
            ),
            "fraud_score_27_to_30_fraud_rows": count(
                "SELECT count(*) FROM silver_transactions "
                "WHERE fraud_score > 27 AND fraud_score <= 30 AND is_fraud"
            ),
            "fraud_score_gt_30_share_of_scored_fraud": _ratio(
                connection,
                "SELECT count(*) FILTER (WHERE fraud_score > 30 AND is_fraud)::DOUBLE "
                "/ NULLIF(count(*) FILTER (WHERE is_fraud AND fraud_score IS NOT NULL), 0) "
                "FROM silver_transactions",
            ),
            "fraud_score_gt_30_share_of_all_fraud": _ratio(
                connection,
                "SELECT count(*) FILTER (WHERE fraud_score > 30 AND is_fraud)::DOUBLE "
                "/ NULLIF(count(*) FILTER (WHERE is_fraud), 0) FROM silver_transactions",
            ),
            "orphan_customer_rows": count(
                "SELECT count(*) FROM silver_transactions t "
                "LEFT JOIN dim_customers c USING (customer_id) WHERE c.customer_id IS NULL"
            ),
            "orphan_product_rows": count(
                "SELECT count(*) FROM joined_transactions WHERE product_status IS NULL"
            ),
            "product_owner_mismatch_rows": count(
                "SELECT count(*) FROM joined_transactions "
                "WHERE product_customer_id IS DISTINCT FROM customer_id"
            ),
            "active_product_share": _ratio(
                connection,
                "SELECT count(*) FILTER (WHERE product_status = 'Active')::DOUBLE / NULLIF(count(*), 0) FROM joined_transactions",
            ),
            "before_product_opening_rows": count(
                "SELECT count(*) FROM joined_transactions "
                "WHERE CAST(transaction_date AS DATE) < opening_date"
            ),
            "rows_last_120_days": count(
                "SELECT count(*) FROM silver_transactions "
                "WHERE transaction_date >= TIMESTAMPTZ '2026-02-18 06:00:00+00' "
                "AND transaction_date < TIMESTAMPTZ '2026-06-18 06:00:00+00'"
            ),
            "rows_last_365_days": count(
                "SELECT count(*) FROM silver_transactions "
                "WHERE transaction_date >= TIMESTAMPTZ '2025-06-18 06:00:00+00' "
                "AND transaction_date < TIMESTAMPTZ '2026-06-18 06:00:00+00'"
            ),
            "atm_purchases_rows": count(
                "SELECT count(*) FROM silver_transactions WHERE channel = 'ATM' AND transaction_type = 'Purchase'"
            ),
            "pos_deposits_rows": count(
                "SELECT count(*) FROM silver_transactions WHERE channel = 'POS' AND transaction_type = 'Deposit'"
            ),
            "process_date_minus_6h_match_share": _ratio(
                connection,
                "SELECT count(*) FILTER (WHERE process_date = CAST(transaction_date - INTERVAL 6 HOUR AS DATE))::DOUBLE / NULLIF(count(*), 0) FROM silver_transactions",
            ),
            "process_date_minus_6h_match_share_by_customer_country": _group_customer_country_ratio(
                connection
            ),
            "latest_transaction_utc": _scalar(
                connection, "SELECT CAST(max(transaction_date) AS VARCHAR) FROM silver_transactions"
            ),
            "business_date_range": _fetchone(
                connection,
                "SELECT CAST(min(process_date) AS VARCHAR), CAST(max(process_date) AS VARCHAR) FROM silver_transactions",
            ),
            "candidate_counts_last_120_days": _candidate_counts(connection),
            "candidate_counts_all": _candidate_distribution(connection, ""),
            "pending_rows_last_120_days": count(
                "SELECT count(*) FROM silver_transactions "
                "WHERE transaction_status = 'Pending' "
                "AND transaction_date >= TIMESTAMPTZ '2026-02-18 06:00:00+00' "
                "AND transaction_date < TIMESTAMPTZ '2026-06-18 06:00:00+00'"
            ),
            "pending_rows_over_14_days_last_120_days": count(
                "SELECT count(*) FROM silver_transactions "
                "WHERE transaction_status = 'Pending' "
                "AND transaction_date >= TIMESTAMPTZ '2026-02-18 06:00:00+00' "
                "AND transaction_date < TIMESTAMPTZ '2026-06-18 06:00:00+00' "
                "AND transaction_date < TIMESTAMPTZ '2026-06-18 06:00:00+00' - INTERVAL 14 DAY"
            ),
            "has_settlement_expiry_reversal_timestamps": any(
                any(
                    term in column.lower()
                    for term in ("settlement", "expiry", "expiration", "reversal")
                )
                and any(term in column.lower() for term in ("date", "time", "timestamp"))
                for column in schema_metadata["transactions"]["source_columns"]
            ),
            "source_columns": schema_metadata["transactions"]["source_columns"],
        }
    )
    tx["business_date_range"] = list(tx["business_date_range"])
    profile["scoped_file_count"] = sum(len(paths) for paths in files_by_table.values())
    profile["scope"] = list(TABLES)
    return profile


def _ratio(connection: duckdb.DuckDBPyConnection, query: str) -> float | None:
    value = _scalar(connection, query)
    return float(value) if value is not None else None


def _null_share(connection: duckdb.DuckDBPyConnection, table: str, column: str) -> float | None:
    return _ratio(
        connection,
        f"SELECT count(*) FILTER (WHERE {column} IS NULL)::DOUBLE / NULLIF(count(*), 0) FROM {table}",
    )


def _required_null_counts(
    connection: duckdb.DuckDBPyConnection, table: str, contract: dict[str, Any]
) -> dict[str, int]:
    required = [
        column
        for column, rules in contract["columns"].items()
        if not bool(rules.get("nullable", True))
    ]
    if not required:
        return {}
    checks = ", ".join(
        f"count(*) FILTER (WHERE {_sql_identifier(column)} IS NULL)" for column in required
    )
    result = _fetchone(connection, f"SELECT {checks} FROM silver_{table}")
    return {column: int(value) for column, value in zip(required, result, strict=True)}


def _group_share(
    connection: duckdb.DuckDBPyConnection, table: str, column: str
) -> dict[str, float]:
    rows = connection.execute(
        f"SELECT CAST({column} AS VARCHAR), count(*)::DOUBLE / (SELECT count(*) FROM {table}) "
        f"FROM {table} GROUP BY {column} ORDER BY {column}",
    ).fetchall()
    return {str(value): float(share) for value, share in rows}


def _candidate_counts(connection: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    return _candidate_distribution(
        connection,
        "WHERE transaction_date >= TIMESTAMPTZ '2026-02-18 06:00:00+00' "
        "AND transaction_date < TIMESTAMPTZ '2026-06-18 06:00:00+00'",
    )


def _candidate_distribution(
    connection: duckdb.DuckDBPyConnection, where_sql: str
) -> dict[str, Any]:
    rows = _fetchone(
        connection,
        "WITH counts AS (SELECT customer_id, count(*) AS n FROM silver_transactions "
        f"{where_sql} GROUP BY customer_id), "
        "all_counts AS (SELECT c.customer_id, coalesce(n, 0) AS n FROM dim_customers c LEFT JOIN counts USING (customer_id)) "
        "SELECT quantile_cont(n, 0.5), quantile_cont(n, 0.9), max(n), count(*) FILTER (WHERE n = 0) FROM all_counts",
    )
    return {
        "median": float(rows[0]),
        "p90": float(rows[1]),
        "max": int(rows[2]),
        "customers_with_none": int(rows[3]),
    }


def _group_count(connection: duckdb.DuckDBPyConnection, table: str, column: str) -> dict[str, int]:
    rows = connection.execute(
        f"SELECT CAST({column} AS VARCHAR), count(*) FROM {table} "
        f"GROUP BY {column} ORDER BY {column}"
    ).fetchall()
    return {str(value): int(count_value) for value, count_value in rows}


def _group_customer_country_ratio(connection: duckdb.DuckDBPyConnection) -> dict[str, float]:
    rows = connection.execute(
        "SELECT customer_country, "
        "count(*) FILTER (WHERE process_date = CAST(transaction_date - INTERVAL 6 HOUR AS DATE))::DOUBLE "
        "/ NULLIF(count(*), 0) FROM joined_transactions "
        "GROUP BY customer_country ORDER BY customer_country"
    ).fetchall()
    return {str(country): float(share) for country, share in rows}


def _amount_quantiles(connection: duckdb.DuckDBPyConnection) -> dict[str, float]:
    values = _fetchone(
        connection,
        "SELECT quantile_cont(amount_usd, 0.50), quantile_cont(amount_usd, 0.75), "
        "quantile_cont(amount_usd, 0.90), quantile_cont(amount_usd, 0.95), "
        "quantile_cont(amount_usd, 0.99) FROM silver_transactions "
        "WHERE transaction_type IN ('Purchase', 'Withdrawal', 'Payment') AND amount_usd IS NOT NULL",
    )
    return {
        key: float(value)
        for key, value in zip(("p50", "p75", "p90", "p95", "p99"), values, strict=True)
    }


def _flatten(profile: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}

    def visit(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                visit(f"{prefix}.{key}" if prefix else key, child)
        else:
            flat[prefix] = value

    for table in TABLES:
        for key, value in profile["tables"][table].items():
            visit(f"{table}.{key}", value)
    return flat


def _compare_expected(profile: dict[str, Any]) -> list[dict[str, Any]]:
    actual = _flatten(profile)
    comparisons: list[dict[str, Any]] = []
    for metric, (expected, mode) in EXPECTED.items():
        observed = actual.get(metric)
        if observed is None:
            outcome = "not_computed"
        elif mode == "exact":
            outcome = "match" if observed == expected else "DIFFERS"
        elif mode.startswith("approx_"):
            tolerance = float(mode.removeprefix("approx_"))
            outcome = (
                "match"
                if abs(float(observed) - float(expected)) <= abs(float(expected)) * tolerance
                else "DIFFERS"
            )
        else:
            tolerance = float(mode.removeprefix("ratio_"))
            outcome = "match" if abs(float(observed) - float(expected)) <= tolerance else "DIFFERS"
        comparisons.append(
            {"metric": metric, "observed": observed, "expected": expected, "result": outcome}
        )
    return comparisons


def _write_profile(profile: dict[str, Any], lake: Path) -> None:
    profile["comparisons"] = _compare_expected(profile)
    path = lake / "_meta" / "profile.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(profile, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    report_path = Path(__file__).resolve().parents[3] / "docs" / "data-quality-report.md"
    lines = [
        "# Data quality report",
        "",
        "Generated from local P1 pipeline aggregates. No source rows are included.",
        "",
        f"- Dataset version: `{profile['dataset_version']}`",
        f"- Source objects: {profile['scoped_file_count']} across customers, products, and transactions.",
        "- Processing: UTF-8 BOM-aware CSV → immutable local bronze → typed Parquet silver → DuckDB DQ aggregates.",
        "- Contracts: Pandera Polars schema validation on up to 2,000 rows per promoted table; full-table DQ counts use DuckDB SQL.",
        "",
        "## Comparison with §4 expectations",
        "",
        "| Metric | Pipeline output | Brief expectation | Result |",
        "|---|---:|---:|---|",
    ]
    for item in profile["comparisons"]:
        lines.append(
            f"| `{item['metric']}` | {item['observed'] if item['observed'] is not None else 'not computed'} | "
            f"{item['expected']} | {item['result']} |"
        )
    customers = profile["tables"]["customers"]
    products = profile["tables"]["products"]
    transactions = profile["tables"]["transactions"]
    lines.extend(
        [
            "",
            "## DQ highlights",
            "",
            f"- Source header variants: customers={customers['source_header_variant_count']}, products={products['source_header_variant_count']}, transactions={transactions['source_header_variant_count']}; unknown source columns: customers={customers['source_unknown_column_count']}, products={products['source_unknown_column_count']}, transactions={transactions['source_unknown_column_count']}.",
            f"- Customer country shares: `{json.dumps(customers['country_share'], sort_keys=True)}`.",
            f"- Customer segments/status: `{json.dumps(customers['segment_share'], sort_keys=True)}` / `{json.dumps(customers['status_share'], sort_keys=True)}`.",
            f"- Customer null shares: `detected_accent`={customers['detected_accent_null_share']:.6f}, `credit_score`={customers['credit_score_null_share']:.6f}; credit-score range={customers['credit_score_range']}; Mexican customers with document type DNI={customers['mexican_document_type_dni_share']:.6f}.",
            f"- Optional customer postal-code null share: {customers['postal_code_null_share']:.6f}.",
            f"- Product type shares after canonical normalization: `{json.dumps(products['product_type_share'], sort_keys=True)}`.",
            f"- Product status shares: `{json.dumps(products['status_share'], sort_keys=True)}`; duplicate product numbers: {products['duplicate_product_numbers']}.",
            f"- Transaction status shares: `{json.dumps(transactions['status_share'], sort_keys=True)}`.",
            f"- Transaction type shares: `{json.dumps(transactions['type_share'], sort_keys=True)}`.",
            f"- Transaction country shares after ISO normalization: `{json.dumps(transactions['country_share'], sort_keys=True)}`.",
            f"- Raw transaction-country label counts: `{json.dumps(transactions['source_country_counts'], sort_keys=True)}`; raw `Mexico` labels on normalized MX customers: {transactions['raw_mexico_label_rows_for_mx_customers']}.",
            f"- Transactions with a normalized transaction country different from the linked customer's normalized country: {transactions['foreign_country_rows']}.",
            f"- Null shares: `amount_usd`={transactions['amount_usd_null_share']:.6f}, `fraud_score`={transactions['fraud_score_null_share']:.6f}; fraud rows={transactions['fraud_rows']}.",
            f"- Fraud-score detail: null-score fraud rows={transactions['fraud_null_score_rows']}; score 27 < score ≤ 30 rows/fraud rows={transactions['fraud_score_27_to_30_rows']}/{transactions['fraud_score_27_to_30_fraud_rows']}; share of scored/all fraud above 30={transactions['fraud_score_gt_30_share_of_scored_fraud']:.6f}/{transactions['fraud_score_gt_30_share_of_all_fraud']:.6f}.",
            f"- Disputable transaction `amount_usd` quantiles (non-null Purchase/Withdrawal/Payment): `{json.dumps(transactions['amount_usd_quantiles_disputable'], sort_keys=True)}`; Purchase/Withdrawal maxima={transactions['purchase_amount_usd_max']}/{transactions['withdrawal_amount_usd_max']}; Payment median={transactions['payment_amount_usd_median']}.",
            f"- Product opening-date anomalies: {transactions['before_product_opening_rows']} transaction rows precede product opening.",
            f"- Latest transaction timestamp (UTC): `{transactions['latest_transaction_utc']}`; process-date range: `{transactions['business_date_range']}`.",
            f"- Transactions in the 120-day UTC window: {transactions['rows_last_120_days']}; in the 365-day UTC window: {transactions['rows_last_365_days']}.",
            f"- ATM purchases: {transactions['atm_purchases_rows']}; POS deposits: {transactions['pos_deposits_rows']}.",
            f"- Pending transactions older than 14 days in the 120-day window: {transactions['pending_rows_over_14_days_last_120_days']} of {transactions['pending_rows_last_120_days']}.",
            f"- Customers/products with `last_updated` after the final source business date ({SOURCE_END_DATE}): {customers['last_updated_after_source_end']} / {products['last_updated_after_source_end']}.",
            f"- Customer/product latest update dates: {customers['last_updated_max_date']} / {products['last_updated_max_date']}.",
            f"- Candidate counts across the full ledger: `{json.dumps(transactions['candidate_counts_all'], sort_keys=True)}`.",
            f"- Candidate count over the half-open 120-day UTC window for all customers: `{json.dumps(transactions['candidate_counts_last_120_days'], sort_keys=True)}`.",
            f"- Settlement/expiry/reversal timestamp fields present in the transaction source: {transactions['has_settlement_expiry_reversal_timestamps']}.",
            "- The 120-day window is `[2026-02-18 06:00:00 UTC, 2026-06-18 06:00:00 UTC)`; the 365-day window is `[2025-06-18 06:00:00 UTC, 2026-06-18 06:00:00 UTC)`. The DuckDB session timezone is pinned to UTC before parsing source timestamps.",
            "- `complaints.affected_product_id` is outside the serving scope; any joins from that field remain prohibited.",
            "- The currency gap against daily FX, contact-center findings, complaints, agents, survey/text findings, and source-regeneration comparison are outside this P1 table scope and remain unverified.",
        ]
    )
    lines.extend(
        [
            "",
            "## Contract checks",
            "",
            "| Table | Null count in required fields | Result |",
            "|---|---:|---|",
        ]
    )
    for table, checks in profile["contract_dq"].items():
        violations = sum(checks.values())
        result = "PASS" if violations == 0 else "FAIL"
        lines.append(f"| `{table}` | {violations} | {result} |")
        for column, count in checks.items():
            if count:
                lines.append(f"| └ `{column}` | {count} | FAIL |")
    lines.extend(["", "## Deviations", ""])
    differences = [item for item in profile["comparisons"] if item["result"] == "DIFFERS"]
    if differences:
        for item in differences:
            lines.append(
                f"- `{item['metric']}` differs: pipeline={item['observed']}, expectation={item['expected']}."
            )
    else:
        lines.append("- No computed expectation differs within the comparison tolerance.")
    lines.extend(
        [
            "- Facts outside the three-table P1 input set are not inferred from this pipeline run.",
            "",
            "## Reproduction",
            "",
            "Run `LOCAL_RAW_DIR=<local-source> python -m aclara.data.cli build`. The version manifest and profile are written under ignored `lake/`; this report is generated from that profile.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


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
    source_root = source.expanduser().resolve()
    lake_root = lake.expanduser().resolve()
    if not source_root.is_dir():
        raise FileNotFoundError("LOCAL_RAW_DIR must point to an existing directory")
    repository_root = Path(__file__).resolve().parents[3]
    if lake_root == source_root or source_root in lake_root.parents:
        raise ValueError("LAKE_DIR cannot be inside the organizer source directory")
    if repository_root not in lake_root.parents and lake_root != repository_root:
        raise ValueError("LAKE_DIR must remain inside this repository")

    files_by_table = {table: _source_files(source_root, table) for table in TABLES}
    contracts = {table: _read_contract(table) for table in TABLES}
    schema_metadata = {
        table: _schema_check(table, contracts[table], files, source_root)
        for table, files in files_by_table.items()
    }
    previous_manifest = _read_previous_manifest(lake_root / "_meta" / "manifest.parquet")
    version, manifest = _make_manifest(
        files_by_table,
        schema_metadata,
        source_root,
        previous_manifest,
        lake_root,
    )
    for table, result in schema_metadata.items():
        if result["unknown_columns"]:
            LOGGER.warning(
                "%s contains %d unknown columns; kept in bronze and excluded from silver",
                table,
                len(result["unknown_columns"]),
            )

    connection = duckdb.connect(":memory:")
    try:
        connection.execute("SET TimeZone='UTC'")
        silver_dirs: dict[str, Path] = {}
        counts: dict[str, int] = {}
        for table in TABLES:
            directory, row_count = _promote_silver(
                connection,
                table,
                files_by_table[table],
                contracts[table],
                source_root,
                manifest,
                version,
                lake_root,
                _pipeline_version(),
            )
            silver_dirs[table] = directory
            counts[table] = row_count
        profile = _query_metrics(
            connection,
            version,
            silver_dirs,
            files_by_table,
            source_root,
            contracts,
            schema_metadata,
        )
    finally:
        connection.close()
    profile["manifest_status_counts"] = {
        status: sum(1 for item in manifest if item["status"] == status)
        for status in ("new", "unchanged", "changed", "removed")
    }
    profile["silver_row_counts"] = counts
    _write_profile(profile, lake_root)
    summary = {table: count for table, count in counts.items()}
    LOGGER.info(
        "P1 pipeline complete · dataset_version=%s · rows=%s",
        version,
        json.dumps(summary, sort_keys=True),
    )
    diff_count = sum(item["result"] == "DIFFERS" for item in profile["comparisons"])
    if diff_count:
        LOGGER.warning(
            "%d computed aggregate(s) differ from brief expectations; see docs/data-quality-report.md",
            diff_count,
        )
    return profile
