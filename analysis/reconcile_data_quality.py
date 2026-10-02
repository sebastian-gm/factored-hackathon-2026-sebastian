"""Direct LOCAL_RAW_DIR scan; output only aggregates to ignored artifacts."""

# ruff: noqa: S608 -- quoted metadata identifiers and repository-defined predicates only.
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from pathlib import Path
from typing import Any

import duckdb
from dotenv import dotenv_values

from aclara.data.pipeline import (
    _cast_expression,
    _fetchone,
    _hash_version,
    _normalize_bank_clock,
    _read_contract,
    _sha256,
    _source_files,
    _sql_identifier,
)
from aclara.data.profiling import column_null_profile, duplicate_profile
from aclara.data.quality import DOCUMENTED
from aclara.data.snapshot import ROOT, TABLES, _invalid_predicates

EXTRA = {"branches": 350, "marketing_campaigns": 200, "campaign_sends": 2_000_000}
LINKS = (
    (
        ("products", "customer_id", "customers", "customer_id"),
        ("transactions", "customer_id", "customers", "customer_id"),
        ("transactions", "product_id", "products", "product_id"),
        ("transactions", "branch_id", "branches", "branch_id"),
        ("customers", "registration_branch_id", "branches", "branch_id"),
        ("products", "opening_branch_id", "branches", "branch_id"),
        ("service_agents", "assigned_branch_id", "branches", "branch_id"),
        ("complaints", "affected_product_id", "products", "product_id"),
        ("complaints", "related_branch_id", "branches", "branch_id"),
        ("complaints", "origin_interaction_id", "call_center_interactions", "interaction_id"),
        ("digital_events", "product_id", "products", "product_id"),
        ("campaign_sends", "campaign_id", "marketing_campaigns", "campaign_id"),
    )
    + tuple(
        (t, "customer_id", "customers", "customer_id")
        for t in (
            "complaints",
            "call_center_interactions",
            "satisfaction_surveys",
            "call_transcripts",
            "digital_events",
            "campaign_sends",
        )
    )
    + tuple(
        (t, c, "service_agents", "agent_id")
        for t, c in (
            ("complaints", "assigned_agent_id"),
            ("call_center_interactions", "agent_id"),
            ("satisfaction_surveys", "agent_id"),
            ("call_transcripts", "agent_id"),
        )
    )
    + tuple(
        (t, "interaction_id", "call_center_interactions", "interaction_id")
        for t in ("satisfaction_surveys", "call_transcripts")
    )
)


def scan(source: Path, output: Path, clock: str) -> dict[str, Any]:
    os.umask(0o077)
    output = output.resolve()
    if not any(
        root == output.parent or root in output.parents
        for root in (ROOT / "artifacts", ROOT / "lake")
    ):
        raise ValueError("output must remain in ignored artifacts/ or lake/")
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    manifest: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "bank_clock": clock,
        "tables": {},
        "column_null_rates": [],
        "relationships": [],
    }
    with duckdb.connect(str(output.parent / "source-scan.duckdb")) as db:
        db.execute("SET TimeZone='UTC'; SET threads=4; SET memory_limit='3GB'")
        db.execute("SET temp_directory=?", [str(output.parent / "spill")])
        db.execute("CREATE SCHEMA IF NOT EXISTS raw; CREATE SCHEMA IF NOT EXISTS silver")
        for table in (*TABLES, *EXTRA):
            paths = _source_files(source, table)
            for path in paths:
                manifest.append(
                    {
                        "table": table,
                        "relative_path": path.relative_to(source).as_posix(),
                        "sha256": _sha256(path),
                        "stat": (path.stat().st_size, path.stat().st_mtime_ns),
                    }
                )
            with paths[0].open(encoding="utf-8-sig", newline="") as file:
                columns = next(csv.reader(file))
            db.read_csv(
                [str(p) for p in paths],
                header=True,
                all_varchar=True,
                hive_partitioning=False,
                union_by_name=True,
            ).create_view("source_csv", replace=True)
            db.execute(
                f"CREATE OR REPLACE TABLE raw.{_sql_identifier(table)} AS SELECT * FROM source_csv"
            )
            rows = int(_fetchone(db, f"SELECT count(*) FROM raw.{_sql_identifier(table)}")[0])
            if table in TABLES:
                contract = _read_contract(table)
                projections = [
                    f"{_cast_expression(n, r, contract.get('normalization', {}))} AS {_sql_identifier(n)}"
                    for n, r in contract["columns"].items()
                ]
                cast_failures = [
                    f"(t.{_sql_identifier(n)} IS NOT NULL AND {_cast_expression(n, r, contract.get('normalization', {}))} IS NULL)"
                    for n, r in contract["columns"].items()
                    if r["type"] != "string"
                ]
                projections.append(f"({' OR '.join(cast_failures)}) AS _cast_failed")
                db.execute(
                    f"CREATE OR REPLACE VIEW silver.{_sql_identifier(table)} AS SELECT {','.join(projections)} FROM raw.{_sql_identifier(table)} t"
                )
                result["column_null_rates"].extend(column_null_profile(db, table))
                key = contract["primary_key"]
                bad = " OR ".join(["_cast_failed", *_invalid_predicates(contract)])
                invalid = int(
                    _fetchone(
                        db,
                        f"SELECT count(*) FROM silver.{_sql_identifier(table)} WHERE coalesce(({bad}),FALSE)",
                    )[0]
                )
            else:
                key, invalid = [columns[0]], None
            fingerprints = duplicate_profile(db, table, columns, key, schema="raw")
            expected = {**DOCUMENTED, **EXTRA}[table]
            metrics = {
                "rows": rows,
                "documented_rows": expected,
                "delta_rows": rows - expected,
                "files": len(paths),
                "contract_invalid_rows": invalid,
                "duplicates": fingerprints,
            }
            if "process_date" in columns:
                start, end, days = _fetchone(
                    db,
                    f"SELECT min(process_date),max(process_date),count(DISTINCT process_date) FROM raw.{_sql_identifier(table)}",
                )
                metrics["business_date_coverage"] = {"start": start, "end": end, "days": days}
            result["tables"][table] = metrics
            output.write_text(json.dumps(result, indent=2, default=str) + "\n")
            logging.info("Profiled %s: %d rows (aggregates only)", table, rows)
        for table, column, parent, parent_key in LINKS:
            qtable, qcolumn, qparent, qkey = map(
                _sql_identifier, (table, column, parent, parent_key)
            )
            present, missing, mismatched = _fetchone(
                db,
                f"SELECT count(*) FILTER (WHERE c.{qcolumn} IS NOT NULL),count(*) FILTER (WHERE c.{qcolumn} IS NOT NULL AND p.{qkey} IS NULL),0 FROM raw.{qtable} c LEFT JOIN raw.{qparent} p ON c.{qcolumn}=p.{qkey}",
            )
            if parent in ("products", "call_center_interactions"):
                mismatched = _fetchone(
                    db,
                    f"SELECT count(*) FROM raw.{qtable} c JOIN raw.{qparent} p ON c.{qcolumn}=p.{qkey} WHERE c.customer_id IS NOT NULL AND c.customer_id IS DISTINCT FROM p.customer_id",
                )[0]
            result["relationships"].append(
                {
                    "table": table,
                    "column": column,
                    "parent": parent,
                    "nonnull_links": present,
                    "orphans": missing,
                    "owner_mismatches": mismatched,
                }
            )
        db.execute(
            "CREATE OR REPLACE TEMP TABLE dq_clock AS SELECT ?::TIMESTAMPTZ AS as_of", [clock]
        )
        fields = (
            "utc_before_open",
            "business_before_open",
            "business_date_mismatch",
            "transactions_with_future_customer_update",
            "transactions_with_future_product_update",
            "window_rows",
            "window_utc_before_open",
            "window_future_customer_update",
            "window_future_product_update",
            "window_any_temporal_issue",
        )
        tests = (
            "t.transaction_date::DATE<p.opening_date",
            "t.process_date<p.opening_date",
            "t.process_date<>(t.transaction_date-INTERVAL 6 HOUR)::DATE",
            "c.last_updated>=as_of",
            "p.last_updated>=as_of",
        )
        window = "t.transaction_date>=as_of-INTERVAL 120 DAY AND t.transaction_date<as_of"
        predicates = [
            *tests,
            window,
            *(f"({window}) AND ({tests[i]})" for i in (0, 3, 4)),
            f"({window}) AND ({' OR '.join(tests)})",
        ]
        values = _fetchone(
            db,
            f"SELECT {','.join(f'count(*) FILTER (WHERE {p})' for p in predicates)} FROM silver.transactions t JOIN silver.products p USING(product_id) JOIN silver.customers c ON t.customer_id=c.customer_id CROSS JOIN dq_clock",
        )
        result["temporal"] = dict(zip(fields, values, strict=True))
        for table in ("customers", "products"):
            result["temporal"][f"{table}_post_clock_rows"] = _fetchone(
                db, f"SELECT count(*) FROM silver.{table},dq_clock WHERE last_updated>=as_of"
            )[0]
        result["pipeline_dataset_version"] = _hash_version(
            [m for m in manifest if m["table"] in TABLES]
        )
        result["full_delivery_version"] = _hash_version(manifest)
        for entry in manifest:
            path = source / entry["relative_path"]
            if (path.stat().st_size, path.stat().st_mtime_ns) != entry["stat"]:
                raise ValueError("source changed during scan")
        output.write_text(json.dumps(result, indent=2, default=str) + "\n")
        if json.loads(output.read_text()) != json.loads(json.dumps(result, default=str)):
            raise OSError("aggregate readback failed")
    return result


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    values = dotenv_values(ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "artifacts/dq-reconciliation/source-profile.json"
    )
    args = parser.parse_args()
    source = os.getenv("LOCAL_RAW_DIR") or values.get("LOCAL_RAW_DIR")
    if not source:
        parser.error("configure LOCAL_RAW_DIR")
    clock = _normalize_bank_clock(
        os.getenv("BANK_CLOCK") or values.get("BANK_CLOCK") or "2026-06-18T06:00:00Z"
    )
    try:
        scan(Path(source).expanduser().resolve(), args.output, clock)
    except Exception as error:
        logging.error("DQ scan failed (%s); no success reported", type(error).__name__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
