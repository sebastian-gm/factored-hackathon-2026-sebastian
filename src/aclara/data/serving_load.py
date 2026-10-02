"""Explicit atomic gold-to-Postgres load with RLS and full read-back checksums."""

# ruff: noqa: S608 -- DuckDB projection names come only from versioned gold contracts.
from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import psycopg
import yaml  # type: ignore[import-untyped]
from psycopg import sql

from aclara.data.pipeline import _sql_identifier, _sql_string
from aclara.data.snapshot import ROOT, fingerprint, write_json
from aclara.data.temporal import register_temporal_exports, validate_temporal_exports

LOGGER = logging.getLogger(__name__)
TABLES = (
    "customers",
    "products",
    "transactions",
    "fx_rates",
    "service_agents",
    "complaint_history_agg",
)
CUSTOMER_SCOPED = {"customers", "products", "transactions", "complaint_history_agg"}
PG_TYPES = {
    "string": "text",
    "number": "double precision",
    "integer": "bigint",
    "boolean": "boolean",
    "date": "date",
    "timestamp": "timestamp with time zone",
}


def _row_bytes(row: tuple[Any, ...]) -> bytes:
    return (
        json.dumps(row, default=str, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()


def _load_table(
    db: duckdb.DuckDBPyConnection, pg: psycopg.Connection[Any], table: str, gold: Path
) -> dict[str, Any]:
    contract = yaml.safe_load((ROOT / "contracts" / f"gold_{table}.yaml").read_text())
    names = list(contract["columns"])
    fields = [
        sql.SQL("{} {} {}").format(
            sql.Identifier(name),
            sql.SQL(PG_TYPES[rules["type"]]),
            sql.SQL("NOT NULL" if not rules.get("nullable", True) else ""),
        )
        for name, rules in contract["columns"].items()
    ]
    keys = sql.SQL(",").join(sql.Identifier(name) for name in contract["primary_key"])
    relation = sql.Identifier("bank", table)
    pg.execute(
        sql.SQL("CREATE TABLE IF NOT EXISTS {} ({}, PRIMARY KEY ({}))").format(
            relation, sql.SQL(",").join(fields), keys
        )
    )
    existing = pg.execute(
        "SELECT column_name,data_type,is_nullable FROM information_schema.columns WHERE table_schema='bank' AND table_name=%s ORDER BY ordinal_position",
        [table],
    ).fetchall()
    if [row[0] for row in existing] != names:
        raise ValueError("serving schema differs from gold contract; lead migration required")
    if table == "transactions" and existing[-1] != ("temporal_quality_reason", "text", "YES"):
        raise ValueError("temporal reason must be nullable TEXT; lead migration required")
    if table in CUSTOMER_SCOPED:
        pg.execute(sql.SQL("ALTER TABLE {} ENABLE ROW LEVEL SECURITY").format(relation))
        # Azure's database owner is not a superuser. Its COPY/readback must run
        # as owner inside this ACCESS EXCLUSIVE load transaction. Restore FORCE
        # before commit; concurrent runtime readers never see an unforced table.
        pg.execute(sql.SQL("ALTER TABLE {} NO FORCE ROW LEVEL SECURITY").format(relation))
        pg.execute(sql.SQL("DROP POLICY IF EXISTS customer_scope ON {}").format(relation))
        pg.execute(
            sql.SQL(
                "CREATE POLICY customer_scope ON {} FOR SELECT TO aclara_api USING (customer_id = NULLIF(current_setting('app.customer_id', true), ''))"
            ).format(relation)
        )
        pg.execute(
            sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} (customer_id)").format(
                sql.Identifier(table + "_customer_idx"), relation
            )
        )
    pg.execute(sql.SQL("GRANT SELECT ON {} TO aclara_api").format(relation))
    pg.execute(sql.SQL("TRUNCATE {}").format(relation))
    order = ",".join(_sql_identifier(name) for name in contract["primary_key"])
    query = (
        "SELECT "
        + ",".join(_sql_identifier(name) for name in names)
        + " FROM read_parquet("
        + _sql_string(str(gold / f"{table}.parquet"))
        + ") ORDER BY "
        + order
    )
    cursor = db.execute(query)
    source_hash = hashlib.sha256()
    expected = 0
    with (
        pg.cursor() as write_cursor,
        write_cursor.copy(
            sql.SQL("COPY {} ({}) FROM STDIN").format(
                relation, sql.SQL(",").join(map(sql.Identifier, names))
            )
        ) as copy,
    ):
        while rows := cursor.fetchmany(5_000):
            for row in rows:
                copy.write_row(row)
                source_hash.update(_row_bytes(row))
                expected += 1
    actual_hash = hashlib.sha256()
    actual = 0
    # C collation matches DuckDB bytewise identifier sorting.
    read_order = sql.SQL(",").join(
        sql.SQL('{} COLLATE "C"').format(sql.Identifier(name))
        if contract["columns"][name]["type"] == "string"
        else sql.Identifier(name)
        for name in contract["primary_key"]
    )
    with pg.cursor(name="readback_" + table) as read_cursor:
        read_cursor.itersize = 5_000
        read_cursor.execute(
            sql.SQL("SELECT {} FROM {} ORDER BY {}").format(
                sql.SQL(",").join(map(sql.Identifier, names)), relation, read_order
            )
        )
        for row in read_cursor:
            actual_hash.update(_row_bytes(row))
            actual += 1
    if actual != expected or actual_hash.digest() != source_hash.digest():
        raise RuntimeError("serving read-back mismatch; transaction rolled back")
    if table in CUSTOMER_SCOPED:
        pg.execute(sql.SQL("ALTER TABLE {} FORCE ROW LEVEL SECURITY").format(relation))
    return {"rows": actual, "sha256": actual_hash.hexdigest()}


def load_serving(lake: Path, dsn: str) -> dict[str, Any]:
    """Connect using a caller-provided owner DSN, which is never returned or logged."""
    marker = json.loads((lake / "_meta/current.json").read_text())
    profile = json.loads(Path(marker["profile_path"]).read_text())
    if any(check["blocks_promotion"] for check in profile["checks"]):
        raise ValueError("cannot load a failed snapshot")
    if marker["build_fingerprint"] != fingerprint():
        raise ValueError("outdated data build; rebuild before loading operational gold")
    # Validate the actual exported artifacts, not merely a profile/stamp. This
    # happens before connecting to Postgres, including for same-version reloads.
    with duckdb.connect(marker["database"], read_only=True) as db:
        register_temporal_exports(db, Path(marker["gold_dir"]))
        temporal_preflight = validate_temporal_exports(db, marker["bank_clock"])
    identity = {key: marker[key] for key in ("dataset_version", "bank_clock", "build_fingerprint")}
    with psycopg.connect(dsn) as pg:
        pg.execute("SELECT pg_advisory_xact_lock(61928471)")
        pg.execute("SET LOCAL TIME ZONE 'UTC'")
        pg.execute("CREATE SCHEMA IF NOT EXISTS meta")
        pg.execute("CREATE SCHEMA IF NOT EXISTS bank")
        pg.execute(
            "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='aclara_api') THEN CREATE ROLE aclara_api NOLOGIN NOSUPERUSER NOBYPASSRLS; END IF; END $$"
        )
        role = pg.execute(
            "SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname='aclara_api'"
        ).fetchone()
        if role != (False, False):
            raise ValueError("API role must not bypass row-level security")
        pg.execute("GRANT USAGE ON SCHEMA bank TO aclara_api")
        pg.execute(
            "CREATE TABLE IF NOT EXISTS meta.serving_state (singleton boolean PRIMARY KEY CHECK(singleton), identity jsonb NOT NULL, counts jsonb NOT NULL, loaded_at timestamptz NOT NULL)"
        )
        previous = pg.execute(
            "SELECT identity,counts FROM meta.serving_state WHERE singleton"
        ).fetchone()
        # Re-run still validates checksums by loading and reading within one transaction.
        results = {}
        with duckdb.connect(":memory:") as db:
            db.execute("SET TimeZone='UTC'")
            for table in TABLES:
                results[table] = _load_table(db, pg, table, Path(marker["gold_dir"]))
        pg.execute(
            "CREATE TABLE IF NOT EXISTS meta.manifest (dataset_version text NOT NULL, relative_path text NOT NULL, sha256 text NOT NULL, status text NOT NULL, row_count bigint NOT NULL, size_bytes bigint NOT NULL, header_sha256 text NOT NULL, first_seen timestamptz NOT NULL, last_seen timestamptz NOT NULL, PRIMARY KEY(dataset_version,relative_path))"
        )
        with duckdb.connect(":memory:") as db:
            entries = db.execute(
                "SELECT dataset_version,relative_path,sha256,status,row_count,size_bytes,header_sha256,first_seen,last_seen FROM read_parquet(?)",
                [marker["manifest_path"]],
            ).fetchall()
        with pg.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO meta.manifest VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (dataset_version,relative_path) DO UPDATE SET status=excluded.status,last_seen=excluded.last_seen",
                entries,
            )
        pg.execute(
            "INSERT INTO meta.serving_state VALUES (true,%s::jsonb,%s::jsonb,%s) ON CONFLICT(singleton) DO UPDATE SET identity=excluded.identity,counts=excluded.counts,loaded_at=excluded.loaded_at",
            [json.dumps(identity), json.dumps(results), datetime.now(UTC)],
        )
        readback = pg.execute(
            "SELECT identity,counts FROM meta.serving_state WHERE singleton"
        ).fetchone()
        if readback != (identity, results):
            raise RuntimeError("serving metadata read-back mismatch")
    # Verify durable commit using a fresh connection before reporting success.
    with psycopg.connect(dsn) as pg:
        if pg.execute(
            "SELECT identity,counts FROM meta.serving_state WHERE singleton"
        ).fetchone() != (identity, results):
            raise RuntimeError("serving commit verification failed")
    output = {
        **identity,
        "tables": results,
        "temporal_preflight": temporal_preflight,
        "same_version_reload": previous is not None and previous[0] == identity,
        "verified_at": datetime.now(UTC).isoformat(),
    }
    write_json(lake / "_meta/serving-load.json", output)
    LOGGER.info(
        "Serving load verified: %s",
        json.dumps({name: item["rows"] for name, item in results.items()}, sort_keys=True),
    )
    return output
