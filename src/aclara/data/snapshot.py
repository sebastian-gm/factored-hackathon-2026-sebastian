"""Immutable objects, typed silver snapshots, and atomic promotion.

All SQL identifiers come from repository contracts; source values are bound or quoted.
Only aggregate diagnostics leave the private lake.
"""
# ruff: noqa: S608 -- identifiers are from checked-in contracts; values are quoted or bound.

from __future__ import annotations

import csv
import fcntl
import hashlib
import inspect
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandera.polars as pa
import polars as pl

from aclara.data.pipeline import (
    POLARS_TYPES,
    SQL_TYPES,
    _cast_expression,
    _fetchone,
    _hash_version,
    _normalize_bank_clock,
    _pipeline_version,
    _read_contract,
    _sha256,
    _source_files,
    _sql_identifier,
    _sql_string,
)

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[3]
TABLES = (
    "customers",
    "products",
    "transactions",
    "daily_exchange_rates",
    "service_agents",
    "complaints",
    "call_center_interactions",
    "satisfaction_surveys",
    "call_transcripts",
    "digital_events",
)


class PromotionBlocked(RuntimeError):
    """An aggregate DQ report exists; the last good snapshot remains active."""


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")
    temporary.replace(path)
    if json.loads(path.read_text()) != json.loads(json.dumps(value, default=str)):
        raise OSError("JSON read-back failed")


def fingerprint() -> str:
    digest = hashlib.sha256()
    paths = sorted((ROOT / "contracts").glob("*.yaml"))
    paths += sorted((ROOT / "dbt").rglob("*.sql")) + sorted((ROOT / "dbt").rglob("*.yml"))
    paths += sorted((ROOT / "src/aclara/data").glob("*.py"))
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _manifest(source: Path, lake: Path) -> tuple[str, list[dict[str, Any]]]:
    previous_path = lake / "_meta/manifest.parquet"
    previous = (
        {row["relative_path"]: row for row in pl.read_parquet(previous_path).to_dicts()}
        if previous_path.exists()
        else {}
    )
    now = datetime.now(UTC).isoformat()
    rows: list[dict[str, Any]] = []
    for table in TABLES:
        for path in _source_files(source, table):
            relative = path.relative_to(source).as_posix()
            old = previous.get(relative)
            digest = _sha256(path)  # Includes old partitions: catches restatements, not only mtime.
            unchanged = old is not None and old["sha256"] == digest
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                header = next(reader, [])
                count = (
                    int(old["row_count"])
                    if unchanged and old is not None
                    else sum(1 for _ in reader)
                )
            rows.append(
                {
                    "relative_path": relative,
                    "table_name": table,
                    "sha256": digest,
                    "size_bytes": path.stat().st_size,
                    "mtime_ns": path.stat().st_mtime_ns,
                    "header_sha256": hashlib.sha256(json.dumps(header).encode()).hexdigest(),
                    "row_count": count,
                    "first_seen": old["first_seen"] if old else now,
                    "last_seen": now,
                    "status": "unchanged" if unchanged else "changed" if old else "new",
                }
            )
    version = _hash_version(rows)
    names = {row["relative_path"] for row in rows}
    for name, old in previous.items():
        if name not in names and old["status"] != "removed":
            rows.append(
                {**{key: old[key] for key in rows[0]}, "status": "removed", "last_seen": now}
            )
    for row in rows:
        row["dataset_version"] = version
    return version, rows


def _bronze(source: Path, lake: Path, version: str, entries: list[dict[str, Any]]) -> int:
    copied = 0
    # Previous immutable versions can supply unchanged objects by hard link.
    old_manifest = lake / "_meta/manifest.parquet"
    old_versions = (
        pl.read_parquet(old_manifest)["dataset_version"].unique().to_list()
        if old_manifest.exists()
        else []
    )
    for row in entries:
        if row["status"] == "removed":
            continue
        target = lake / "bronze" / f"dataset_version={version}" / row["relative_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if _sha256(target) != row["sha256"]:
                raise OSError("immutable bronze object checksum mismatch")
            continue
        reused = False
        if row["status"] == "unchanged":
            for old in old_versions:
                candidate = lake / "bronze" / f"dataset_version={old}" / row["relative_path"]
                if candidate.is_file() and _sha256(candidate) == row["sha256"]:
                    os.link(candidate, target)
                    reused = True
                    break
        if not reused:
            shutil.copy2(source / row["relative_path"], target)
            copied += 1
        if _sha256(target) != row["sha256"]:
            raise OSError("bronze read-back failed")
    return copied


def _invalid_predicates(contract: dict[str, Any]) -> list[str]:
    checks = []
    for name, rules in contract["columns"].items():
        col = _sql_identifier(name)
        if not rules.get("nullable", True):
            checks.append(f"{col} IS NULL")
        for key, operator in (("min", "<"), ("max", ">"), ("exclusive_min", "<=")):
            if key in rules:
                checks.append(f"{col} {operator} {float(rules[key])}")
        if "enum" in rules:
            domain = ",".join(_sql_string(str(value)) for value in rules["enum"])
            checks.append(f"{col} NOT IN ({domain})")
    return checks


def _pandera_contract(contract: dict[str, Any]) -> pa.DataFrameSchema:
    columns = {}
    for name, rules in contract["columns"].items():
        checks = []
        if "min" in rules:
            checks.append(pa.Check.ge(rules["min"]))
        if "max" in rules:
            checks.append(pa.Check.le(rules["max"]))
        if "exclusive_min" in rules:
            checks.append(pa.Check.gt(rules["exclusive_min"]))
        if "enum" in rules:
            checks.append(pa.Check.isin(rules["enum"]))
        columns[name] = pa.Column(
            POLARS_TYPES[rules["type"]], checks=checks, nullable=rules.get("nullable", True)
        )
    return pa.DataFrameSchema(columns, strict=False)


def _conversion_hash(contract: dict[str, Any]) -> str:
    return hashlib.sha256(
        Path(__file__).read_bytes()
        + inspect.getsource(_cast_expression).encode()
        + json.dumps(SQL_TYPES, sort_keys=True).encode()
        + json.dumps(contract, sort_keys=True).encode()
    ).hexdigest()


def _silver_table(
    db: duckdb.DuckDBPyConnection,
    table: str,
    lake: Path,
    version: str,
    entries: list[dict[str, Any]],
    pipeline: str,
) -> dict[str, Any]:
    contract = _read_contract(table)
    # Cache identity includes all conversion code, not just the source checksum.
    conversion = _conversion_hash(contract)
    snapshot_dir = lake / "silver" / version / conversion / table
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    metrics = {
        "files": len(entries),
        "rebuilt_objects": 0,
        "invalid_rows": 0,
        "missing_required_files": 0,
        "unknown_column_files": 0,
    }
    schema = _pandera_contract(contract)
    for index, entry in enumerate(entries):
        source = lake / "bronze" / f"dataset_version={version}" / entry["relative_path"]
        with source.open(encoding="utf-8-sig", newline="") as stream:
            header = set(next(csv.reader(stream), []))
        required = {
            key for key, rules in contract["columns"].items() if not rules.get("nullable", True)
        }
        if required - header:
            metrics["missing_required_files"] += 1
            # Original rows remain in immutable bronze; quarantine references contain no copied text.
            write_json(
                lake / "quarantine" / version / table / f"{index}.json",
                {
                    "reason": "missing_required_columns",
                    "source_sha256": entry["sha256"],
                    "row_count": entry["row_count"],
                },
            )
            continue
        metrics["unknown_column_files"] += bool(header - set(contract["columns"]))
        key = hashlib.sha256(
            (entry["relative_path"] + entry["sha256"] + conversion).encode()
        ).hexdigest()
        cache = lake / "silver/_objects" / table / key
        stats_path = cache / "stats.json"
        if not stats_path.exists():
            cache.mkdir(parents=True, exist_ok=True)
            db.read_csv(
                str(source), header=True, all_varchar=True, hive_partitioning=False
            ).create_view("raw_object", replace=True)
            projections = [
                (
                    f"{_cast_expression(name, rules, contract.get('normalization', {}))}"
                    if name in header
                    else f"NULL::{SQL_TYPES[rules['type']]}"
                )
                + f" AS {_sql_identifier(name)}"
                for name, rules in contract["columns"].items()
            ]
            # Cast failures in nullable fields are invalid too, rather than silently converted to null.
            cast_failures = [
                f"(t.{_sql_identifier(name)} IS NOT NULL AND TRY_CAST(t.{_sql_identifier(name)} AS {SQL_TYPES[rules['type']]}) IS NULL)"
                for name, rules in contract["columns"].items()
                if name in header and rules["type"] != "string"
            ]
            casts = " OR ".join(cast_failures) or "FALSE"
            projections += [
                f"{_sql_string(entry['relative_path'])} AS _source_file",
                f"{_sql_string(entry['sha256'])} AS _source_sha256",
                "CURRENT_TIMESTAMP AS _ingested_at",
                f"{_sql_string(pipeline)} AS _pipeline_version",
                f"({casts}) AS _cast_failed",
            ]
            db.execute(
                "CREATE OR REPLACE TEMP TABLE typed_object AS SELECT "
                + ",".join(projections)
                + " FROM raw_object t"
            )
            invalid = (
                "coalesce(("
                + " OR ".join(["_cast_failed", *_invalid_predicates(contract)])
                + "), FALSE)"
            )
            rejected = int(_fetchone(db, f"SELECT count(*) FROM typed_object WHERE {invalid}")[0])
            db.execute(
                f"COPY (SELECT * EXCLUDE (_cast_failed) FROM typed_object WHERE NOT {invalid}) TO {_sql_string(str(cache / 'data.parquet'))} (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
            if rejected:
                quarantine = lake / "quarantine" / version / table
                quarantine.mkdir(parents=True, exist_ok=True)
                db.execute(
                    f"COPY (SELECT *, 'contract_violation' AS _reason FROM typed_object WHERE {invalid}) TO {_sql_string(str(quarantine / (key + '.parquet')))} (FORMAT PARQUET)"
                )
            # Every admitted row is schema-checked; diagnostics never include Pandera failure rows.
            try:
                schema.validate(pl.read_parquet(cache / "data.parquet"))
            except pa.errors.SchemaError:
                raise PromotionBlocked(f"{table}: Pandera validation failed") from None
            write_json(
                stats_path, {"invalid_rows": rejected, "sha256": _sha256(cache / "data.parquet")}
            )
            metrics["rebuilt_objects"] += 1
        stats = json.loads(stats_path.read_text())
        metrics["invalid_rows"] += stats["invalid_rows"]
        target = snapshot_dir / f"{index:06}.parquet"
        if not target.exists():
            os.link(cache / "data.parquet", target)
    return metrics


def attach_silver(db: duckdb.DuckDBPyConnection, lake: Path, version: str) -> None:
    db.execute("CREATE SCHEMA IF NOT EXISTS silver")
    for table in TABLES:
        directory = lake / "silver" / version / _conversion_hash(_read_contract(table)) / table
        files = sorted(directory.glob("*.parquet"))
        if not files:
            raise PromotionBlocked(f"{table}: no valid source partitions")
        db.read_parquet([str(path) for path in files], hive_partitioning=False).create_view(
            "snapshot_objects", replace=True
        )
        # The source-object cache is version-independent; the logical silver relation is versioned.
        db.execute(
            f"CREATE OR REPLACE VIEW silver.{_sql_identifier(table)} AS SELECT *, {_sql_string(version)}::VARCHAR AS _dataset_version FROM read_parquet({_sql_string(str(directory / '*.parquet'))}, hive_partitioning=false)"
        )


def run_dbt(database: Path, lake: Path, clock: str, run: Path) -> None:
    env = {
        **os.environ,
        "DBT_DATABASE": str(database),
        "BANK_CLOCK": clock,
        "LAKE_DIR": str(lake),
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
        "DO_NOT_TRACK": "1",
    }
    for command in (("build",), ("docs", "generate")):
        args = [
            str(Path(sys.executable).with_name("dbt")),
            *command,
            "--project-dir",
            str(ROOT / "dbt"),
            "--profiles-dir",
            str(ROOT / "dbt"),
            "--target-path",
            str(run / "dbt"),
            "--log-path",
            str(run / "logs"),
            "--no-use-colors",
        ]
        result = subprocess.run(args, env=env, capture_output=True, text=True, check=False)  # noqa: S603
        # Detailed SQL errors can contain source values: private logs only.
        (run / f"dbt-{command[0]}.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise PromotionBlocked(
                "dbt contract/test failure; details are in the private run directory"
            )


def build_snapshot(
    source: Path, lake: Path, *, bank_clock: str | None = None, reports: bool = True
) -> dict[str, Any]:
    source, lake = source.expanduser().resolve(), lake.expanduser().resolve()
    if not source.is_dir():
        raise ValueError("LOCAL_RAW_DIR must be an existing directory")
    if source == lake or source in lake.parents or lake in source.parents:
        raise ValueError("source and lake must not overlap")
    if ROOT in lake.parents and not any(
        root == lake or root in lake.parents for root in (ROOT / "lake", ROOT / "artifacts")
    ):
        raise ValueError(
            "generated data in the repository must be under ignored lake/ or artifacts/"
        )
    lake.mkdir(parents=True, exist_ok=True)
    clock = _normalize_bank_clock(
        bank_clock or os.environ.get("BANK_CLOCK") or "2026-06-18T06:00:00Z"
    )
    with (lake / ".pipeline.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _build_locked(source, lake, clock, reports)


def _build_locked(source: Path, lake: Path, clock: str, reports: bool) -> dict[str, Any]:
    from aclara.data.quality import quality_report
    from aclara.data.reporting import generate_reports

    started = datetime.now(UTC)
    version, manifest = _manifest(source, lake)
    signature = fingerprint()
    current_path = lake / "_meta/current.json"
    current = json.loads(current_path.read_text()) if current_path.exists() else {}
    if (
        current.get("dataset_version") == version
        and current.get("build_fingerprint") == signature
        and current.get("bank_clock") == clock
    ):
        profile: dict[str, Any] = json.loads(Path(current["profile_path"]).read_text())
        profile["no_op"] = True
        if reports:
            generate_reports(profile, ROOT / "docs")
        LOGGER.info("Pipeline no-op; immutable bronze, silver and gold reused (%s)", version)
        return profile
    run = lake / "_runs" / started.strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(parents=True)
    copied = _bronze(source, lake, version, manifest)
    (lake / "_meta").mkdir(exist_ok=True)
    manifest_path = lake / "_meta/manifest.parquet"
    pl.DataFrame(manifest).write_parquet(run / "manifest.parquet")
    shutil.copy2(run / "manifest.parquet", manifest_path)
    database = run / "warehouse.duckdb"
    db = duckdb.connect(str(database))
    db.execute("SET TimeZone='UTC'")
    db.execute("SET threads=4")
    metrics: dict[str, Any] = {}
    try:
        for table in TABLES:
            selected = [
                row for row in manifest if row["table_name"] == table and row["status"] != "removed"
            ]
            metrics[table] = _silver_table(db, table, lake, version, selected, _pipeline_version())
            LOGGER.info(
                "Silver %s: %d objects rebuilt; %d invalid rows",
                table,
                metrics[table]["rebuilt_objects"],
                metrics[table]["invalid_rows"],
            )
        if any(item["missing_required_files"] for item in metrics.values()):
            write_json(
                run / "dq.json",
                {"dataset_version": version, "tables": metrics, "status": "FAIL_SCHEMA"},
            )
            raise PromotionBlocked("required columns missing; partition references quarantined")
        attach_silver(db, lake, version)
        profile = quality_report(db, version, clock, metrics)
        profile.update(
            bronze_objects_copied=copied,
            manifest_status_counts={
                status: sum(row["status"] == status for row in manifest)
                for status in ("new", "changed", "unchanged", "removed")
            },
            build_fingerprint=signature,
            pipeline_version=_pipeline_version(),
        )
        write_json(run / "profile.json", profile)
        if any(check["blocks_promotion"] for check in profile["checks"]):
            raise PromotionBlocked("DQ gate blocked promotion; previous snapshot remains active")
        db.execute(
            "CREATE TABLE silver.analysis_aggregates (metric VARCHAR, value VARCHAR, _dataset_version VARCHAR, _source_file VARCHAR, _source_sha256 VARCHAR, _ingested_at TIMESTAMPTZ, _pipeline_version VARCHAR)"
        )
        db.executemany(
            "INSERT INTO silver.analysis_aggregates VALUES (?,?,?,?,?,?,?)",
            [
                (
                    key,
                    json.dumps(value, default=str),
                    version,
                    "aggregate:silver-snapshot",
                    version,
                    started,
                    _pipeline_version(),
                )
                for key, value in profile.items()
            ],
        )
    finally:
        db.close()
    run_dbt(database, lake, clock, run)
    db = duckdb.connect(str(database), read_only=True)
    try:
        # Export only after all contracts/tests have succeeded. Keep old snapshots for rollback.
        gold = run / "gold"
        gold.mkdir()
        gold_counts = {}
        for (table,) in db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='gold' ORDER BY table_name"
        ).fetchall():
            path = gold / f"{table}.parquet"
            db.execute(
                f"COPY gold.{_sql_identifier(table)} TO {_sql_string(str(path))} (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
            expected = db.execute(f"SELECT count(*) FROM gold.{_sql_identifier(table)}").fetchone()
            actual = db.execute("SELECT count(*) FROM read_parquet(?)", [str(path)]).fetchone()
            if actual != expected:
                raise OSError("gold export read-back failed")
            gold_counts[table] = int(actual[0]) if actual else 0
    finally:
        db.close()
    profile.update(
        gold_row_counts=gold_counts,
        no_op=False,
        promoted_at=datetime.now(UTC).isoformat(),
        change_to_gold_seconds=(datetime.now(UTC) - started).total_seconds(),
    )
    write_json(run / "profile.json", profile)
    marker = {
        "dataset_version": version,
        "bank_clock": clock,
        "build_fingerprint": signature,
        "database": str(database),
        "gold_dir": str(gold),
        "manifest_path": str(run / "manifest.parquet"),
        "profile_path": str(run / "profile.json"),
        "previous": current.get("database"),
    }
    write_json(current_path, marker)
    if reports:
        generate_reports(profile, ROOT / "docs")
    LOGGER.info(
        "Promoted dataset %s; gold counts=%s", version, json.dumps(gold_counts, sort_keys=True)
    )
    return profile
