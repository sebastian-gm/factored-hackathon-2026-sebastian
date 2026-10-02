"""Run with a local owner TEST_DATA_LOAD_DSN; no network or secrets in CI defaults."""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
import psycopg
import pytest

from aclara.data.serving_load import CUSTOMER_SCOPED, _migrate_temporal_column, load_serving
from aclara.data.snapshot import build_snapshot


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
    # A changed artifact that fails contract constraints must roll back the whole load.
    marker = json.loads((lake / "_meta/current.json").read_text())
    file = Path(marker["gold_dir"]) / "transactions.parquet"
    with duckdb.connect() as db:
        db.execute("CREATE TABLE bad AS SELECT * FROM read_parquet(?)", [str(file)])
        db.execute("UPDATE bad SET transaction_id=NULL")
        db.execute("COPY bad TO ? (FORMAT PARQUET)", [str(file)])
    with pytest.raises(psycopg.errors.NotNullViolation):
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
