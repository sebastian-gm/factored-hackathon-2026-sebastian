"""Authored serving/source regressions; DB readback needs local TEST_DATA_LOAD_DSN."""

# ruff: noqa: S608 -- mutation identifiers/expressions are fixed authored test parameters.

from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import date
from pathlib import Path
from unittest.mock import patch

import duckdb
import psycopg
import pytest

from aclara.data.serving_load import CUSTOMER_SCOPED, _migrate_temporal_column, load_serving
from aclara.data.snapshot import PromotionBlocked, build_snapshot
from aclara.data.temporal import register_temporal_exports, validate_temporal_exports


def test_serving_readback_and_rls(tmp_path: Path) -> None:
    dsn = os.environ.get("TEST_DATA_LOAD_DSN")
    if not dsn:
        pytest.skip("local Postgres owner DSN required")
    pytest.importorskip("dbt.cli.main")
    lake = tmp_path / "lake"
    build_snapshot(Path("tests/fixtures/incremental/day1"), lake, reports=False)
    result = load_serving(lake, dsn)
    assert result["tables"]["transactions"]["rows"] == 3
    assert load_serving(lake, dsn)["same_version_reload"]
    with psycopg.connect(dsn, autocommit=True) as db:
        assert db.execute(
            "SELECT data_type,is_nullable FROM information_schema.columns WHERE table_schema='bank' AND table_name='transactions' AND column_name='temporal_quality_reason'"
        ).fetchone() == ("text", "YES")
        assert db.execute(
            "SELECT count(*) FROM bank.transactions WHERE temporal_quality_reason IS NOT NULL"
        ).fetchone() == (0,)
        db.execute(
            "CREATE OR REPLACE VIEW bank.fixture_transaction_view WITH (security_invoker=true) AS SELECT * FROM bank.transactions"
        )
        db.execute("GRANT SELECT ON bank.fixture_transaction_view TO aclara_api")
        db.execute("SET ROLE aclara_api")
        assert db.execute("SELECT count(*) FROM bank.transactions").fetchone() == (0,)
        assert db.execute("SELECT count(*) FROM bank.fixture_transaction_view").fetchone() == (0,)
        with db.transaction():
            db.execute("SELECT set_config('app.customer_id',%s,true)", ["fixture-customer-a"])
            assert db.execute("SELECT count(*) FROM bank.transactions").fetchone() == (3,)
            assert db.execute("SELECT count(*) FROM bank.fixture_transaction_view").fetchone() == (
                3,
            )
            assert db.execute(
                "SELECT count(*) FROM bank.transactions WHERE customer_id=%s",
                ["fixture-customer-b"],
            ).fetchone() == (0,)
            assert db.execute(
                "SELECT count(*) FROM bank.complaint_history_agg WHERE customer_id=%s",
                ["fixture-customer-b"],
            ).fetchone() == (0,)
        # Same physical connection after transaction reset and in autocommit mode.
        assert db.execute("SELECT count(*) FROM bank.transactions").fetchone() == (0,)
        with db.transaction():
            db.execute("SELECT set_config('app.customer_id',%s,true)", ["fixture-customer-b"])
            assert db.execute("SELECT count(*) FROM bank.transactions").fetchone() == (0,)
        flags = db.execute(
            "SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class JOIN pg_namespace n ON relnamespace=n.oid WHERE n.nspname='bank' AND relname=ANY(%s)",
            [list(CUSTOMER_SCOPED)],
        ).fetchall()
        assert all(enabled and forced for _, enabled, forced in flags)
        db.execute("RESET ROLE")
        db.execute("DROP VIEW bank.fixture_transaction_view")
    # A changed artifact must be rejected before any bank write.
    marker = json.loads((lake / "_meta/current.json").read_text())
    file = Path(marker["gold_dir"]) / "transactions.parquet"
    with duckdb.connect() as db:
        db.execute("CREATE TABLE bad AS SELECT * FROM read_parquet(?)", [str(file)])
        db.execute("UPDATE bad SET transaction_id=NULL")
        db.execute("COPY bad TO ? (FORMAT PARQUET)", [str(file)])
    with pytest.raises(ValueError, match="temporal serving preflight"):
        load_serving(lake, dsn)
    with psycopg.connect(dsn) as db:
        assert db.execute("SELECT count(*) FROM bank.transactions").fetchone() == (3,)


def test_temporal_migration_rolls_back_with_the_locked_loader_transaction() -> None:
    dsn = os.environ.get("TEST_DATA_LOAD_DSN")
    if not dsn:
        pytest.skip("local Postgres owner DSN required")

    class InjectedLoadFailure(RuntimeError):
        pass

    class RestoreAuthoredSchema(RuntimeError):
        pass

    # Outer rollback restores the exact prior test schema and flags.
    with psycopg.connect(dsn) as db, pytest.raises(RestoreAuthoredSchema), db.transaction():
        db.execute("SELECT pg_advisory_xact_lock(61928471)")
        db.execute("ALTER TABLE bank.transactions DROP COLUMN IF EXISTS temporal_quality_reason")
        existing = db.execute(
            "SELECT column_name,data_type,is_nullable FROM information_schema.columns "
            "WHERE table_schema='bank' AND table_name='transactions' ORDER BY ordinal_position"
        ).fetchall()
        names = [r[0] for r in existing] + ["temporal_quality_reason"]
        with pytest.raises(InjectedLoadFailure), db.transaction():
            _migrate_temporal_column(db, "transactions", names, existing)
            assert db.execute(
                "SELECT data_type,is_nullable FROM information_schema.columns "
                "WHERE table_schema='bank' AND table_name='transactions' "
                "AND column_name='temporal_quality_reason'"
            ).fetchone() == ("text", "YES")
            raise InjectedLoadFailure("authored post-migration load failure")
        assert db.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema='bank' "
            "AND table_name='transactions' AND column_name='temporal_quality_reason'"
        ).fetchone() == (0,)
        assert db.execute("SELECT count(*) FROM bank.transactions").fetchone() == (3,)
        raise RestoreAuthoredSchema


FIXTURE = Path(__file__).parent / "fixtures/incremental/day1"
CLOCK = "2026-06-18T06:00:00Z"


def edit_fixture(path: Path, fields: dict[str, str]) -> None:
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        names, rows = reader.fieldnames, list(reader)
    rows[0].update(fields)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=names or [])
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture(scope="module")
def authority_snapshot(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    """One immutable authored snapshot covers exact, prior and USD FX."""
    pytest.importorskip("dbt.cli.main")
    root = tmp_path_factory.mktemp("authority-projection")
    source, lake = root / "source", root / "lake"
    shutil.copytree(FIXTURE, source)
    edit_fixture(
        source / "transactions/day-14.csv",
        {
            "currency": "COP",
            "amount": "8000",
            "transaction_country": "CO",
        },
    )
    edit_fixture(source / "transactions/day-16.csv", {"currency": "COP", "amount": "8000"})
    build_snapshot(source, lake, reports=False)
    return json.loads((lake / "_meta/current.json").read_text())


def test_source_equivalence_accepts_authored_fx_projection(
    authority_snapshot: dict[str, object],
) -> None:
    with duckdb.connect(str(authority_snapshot["database"]), read_only=True) as db:
        register_temporal_exports(db, Path(str(authority_snapshot["gold_dir"])))
        assert validate_temporal_exports(db, CLOCK) == dict.fromkeys(
            ("customers", "products", "transactions"), 0
        )
        assert db.execute(
            """SELECT amount_usd_recomputed,fx_date,fx_nearest_prior,foreign_transaction
            FROM served_transactions ORDER BY transaction_id"""
        ).fetchall() == [
            (2.0, date(2026, 6, 14), False, True),
            (50.0, date(2026, 6, 15), False, False),
            (2.0, date(2026, 6, 14), True, False),
        ]


@pytest.mark.parametrize(
    ("table", "field", "value"),
    [
        ("transactions", "transaction_status", "'Pending'"),
        ("transactions", "transaction_type", "'Adjustment'"),
        ("transactions", "amount", "amount+1"),
        ("transactions", "currency", "'USD'"),
        ("transactions", "amount_usd", "999"),
        ("transactions", "fraud_score", "90"),
        ("transactions", "amount_usd_recomputed", "amount_usd_recomputed+1"),
        ("transactions", "fx_date", "fx_date+1"),
        ("transactions", "fx_nearest_prior", "NOT fx_nearest_prior"),
        ("transactions", "foreign_transaction", "NOT foreign_transaction"),
        ("transactions", "customer_country", "'CO'"),
        ("transactions", "product_status", "'Blocked'"),
        ("transactions", "merchant_name", "'Authored altered merchant'"),
        ("products", "product_type", "'credit_card'"),
        ("products", "currency", "'COP'"),
        ("customers", "country", "'CO'"),
        ("customers", "segment", "'Premium'"),
    ],
)
def test_each_authority_field_mutation_fails_before_bank_connection(
    tmp_path: Path, authority_snapshot: dict[str, object], table: str, field: str, value: str
) -> None:
    gold, lake = tmp_path / "gold", tmp_path / "lake"
    shutil.copytree(Path(str(authority_snapshot["gold_dir"])), gold)
    marker = {**authority_snapshot, "gold_dir": str(gold)}
    (lake / "_meta").mkdir(parents=True)
    (lake / "_meta/current.json").write_text(json.dumps(marker))
    file = gold / f"{table}.parquet"
    with duckdb.connect() as db:
        db.execute("CREATE TABLE altered AS SELECT * FROM read_parquet(?)", [str(file)])
        key, identity = {
            "transactions": ("transaction_id", "fixture-txn-14"),
            "products": ("product_id", "fixture-product-a"),
            "customers": ("customer_id", "fixture-customer-a"),
        }[table]
        db.execute(f"UPDATE altered SET {field}={value} WHERE {key}=?", [identity])
        db.execute("COPY altered TO ? (FORMAT PARQUET)", [str(file)])
    with (
        patch("aclara.data.serving_load.psycopg.connect") as connect,
        pytest.raises(ValueError, match="temporal serving preflight"),
    ):
        load_serving(lake, "authored-never-used-connection")
    connect.assert_not_called()


def test_missing_source_fx_rate_still_blocks_promotion(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(FIXTURE, source)
    edit_fixture(source / "transactions/day-14.csv", {"currency": "ARS"})
    with pytest.raises(PromotionBlocked, match="DQ gate blocked"):
        build_snapshot(source, tmp_path / "lake", reports=False)
