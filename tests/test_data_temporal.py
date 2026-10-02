"""Authored temporal cases preserve visibility and independently check each reason."""

# ruff: noqa: S608 -- SQL fragments come only from the fixed repository predicate.

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest
import yaml

from aclara.data.serving_load import PG_TYPES, load_serving
from aclara.data.snapshot import build_snapshot
from aclara.data.temporal import (
    register_temporal_exports,
    temporal_profile,
    temporal_reason_sql,
    validate_temporal_exports,
)

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


@pytest.mark.parametrize(
    ("file", "fields", "reason", "flagged", "warnings"),
    [
        ("products.csv", {"opening_date": "2026-06-15"}, "before_product_open", 1, 0),
        ("transactions/day-14.csv", {"process_date": "2026-06-13"}, None, 0, 1),
        ("customers.csv", {"last_updated": CLOCK}, "customer_updated_after_clock", 3, 0),
        (
            "products.csv",
            {"last_updated": "2026-06-18T06:00:01Z"},
            "product_updated_after_clock",
            3,
            0,
        ),
        ("products.csv", {"last_updated": CLOCK}, "product_updated_after_clock", 3, 0),
        ("products.csv", {"opening_date": "2026-06-18"}, "before_product_open", 3, 0),
        ("customers.csv", {"last_updated": "2026-06-18T05:59:59.999999Z"}, None, 0, 0),
    ],
)
def test_temporal_flags_preserve_original_projections(
    tmp_path: Path,
    file: str,
    fields: dict[str, str],
    reason: str | None,
    flagged: int,
    warnings: int,
) -> None:
    source, lake = tmp_path / "source", tmp_path / "lake"
    shutil.copytree(FIXTURE, source)
    edit_fixture(source / file, fields)
    profile = build_snapshot(source, lake, reports=False)
    assert tuple(
        profile["gold_row_counts"][t] for t in ("customers", "products", "transactions")
    ) == (2, 2, 3)
    assert profile["gold_row_counts"]["matcher_ledger"] == 3
    marker = json.loads((lake / "_meta/current.json").read_text())
    with duckdb.connect(marker["database"], read_only=True) as db:
        db.execute("SET TimeZone='Asia/Tokyo'")
        flags = temporal_profile(db, CLOCK)
        assert flags["flagged_transaction_rows"] == flagged
        assert flags["unflagged_transaction_rows"] == 3 - flagged
        assert flags["window_business_date_mismatch_warning"] == warnings
        expected_counts = []
        if flagged:
            expected_counts.append((reason, flagged))
        if flagged < 3:
            expected_counts.append((None, 3 - flagged))
        assert (
            db.execute(
                "SELECT temporal_quality_reason,count(*) FROM gold.transactions GROUP BY 1 ORDER BY 1"
            ).fetchall()
            == expected_counts
        )
        # All pre-existing transaction fields equal the original serving projection.
        db.execute(
            """CREATE TEMP VIEW original_projection AS SELECT t.*,r.fraud_score
            FROM gold.matcher_ledger t JOIN silver.transactions r USING(transaction_id)
            CROSS JOIN temporal_clock
            WHERE t.transaction_date>=as_of-INTERVAL 120 DAY AND t.transaction_date<as_of"""
        )
        assert db.execute(
            """SELECT count(*) FROM (
            (SELECT * EXCLUDE(temporal_quality_reason) FROM gold.transactions EXCEPT ALL SELECT * FROM original_projection)
            UNION ALL
            (SELECT * FROM original_projection EXCEPT ALL SELECT * EXCLUDE(temporal_quality_reason) FROM gold.transactions))"""
        ).fetchone() == (0,)
        register_temporal_exports(db, Path(marker["gold_dir"]))
        assert validate_temporal_exports(db, CLOCK) == dict.fromkeys(
            ("customers", "products", "transactions"), 0
        )
        assert db.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema='gold' AND column_name IN ('registration_branch_id','assigned_branch_id','affected_product_id')"
        ).fetchone() == (0,)


def test_business_boundary_flags_without_removing_charge(tmp_path: Path) -> None:
    source, lake = tmp_path / "source", tmp_path / "lake"
    shutil.copytree(FIXTURE, source)
    edit_fixture(source / "products.csv", {"opening_date": "2026-06-15"})
    file = source / "transactions/day-14.csv"
    edit_fixture(file, {"transaction_date": "2026-06-15T05:59:59.999999Z"})
    for fields, expected in (
        ({}, "before_product_open"),
        ({"transaction_date": "2026-06-15T06:00:00Z", "process_date": "2026-06-15"}, None),
    ):
        edit_fixture(file, fields)
        profile = build_snapshot(source, lake, reports=False)
        assert profile["gold_row_counts"]["transactions"] == 3
        marker = json.loads((lake / "_meta/current.json").read_text())
        with duckdb.connect(marker["database"], read_only=True) as db:
            assert db.execute(
                "SELECT temporal_quality_reason FROM gold.transactions WHERE transaction_id='fixture-txn-14'"
            ).fetchone() == (expected,)


def test_multiple_findings_use_contract_precedence(tmp_path: Path) -> None:
    source, lake = tmp_path / "source", tmp_path / "lake"
    shutil.copytree(FIXTURE, source)
    edit_fixture(source / "customers.csv", {"last_updated": CLOCK})
    edit_fixture(source / "products.csv", {"last_updated": CLOCK, "opening_date": "2026-06-15"})
    build_snapshot(source, lake, reports=False)
    marker = json.loads((lake / "_meta/current.json").read_text())
    with duckdb.connect(marker["database"], read_only=True) as db:
        assert db.execute(
            "SELECT temporal_quality_reason,count(*) FROM gold.transactions GROUP BY 1 ORDER BY 1"
        ).fetchall() == [("before_product_open", 1), ("product_updated_after_clock", 2)]
        flags = temporal_profile(db, CLOCK)
        assert flags["flagged_transaction_rows"] == 3
        assert flags["findings"]["customer_updated_after_clock"] == 3
        assert sum(flags["primary_reason_counts"].values()) == 3


def test_after_clock_reason_does_not_expand_serving_window(tmp_path: Path) -> None:
    source, lake = tmp_path / "source", tmp_path / "lake"
    shutil.copytree(FIXTURE, source)
    edit_fixture(
        source / "transactions/day-14.csv",
        {"transaction_date": CLOCK, "process_date": "2026-06-18"},
    )
    profile = build_snapshot(source, lake, reports=False)
    assert profile["gold_row_counts"]["transactions"] == 2
    assert profile["gold_row_counts"]["matcher_ledger"] == 3
    marker = json.loads((lake / "_meta/current.json").read_text())
    with duckdb.connect(marker["database"], read_only=True) as db:
        db.execute("SET TimeZone='UTC'")
        db.execute("CREATE TEMP TABLE temporal_clock AS SELECT ?::TIMESTAMPTZ as_of", [CLOCK])
        assert db.execute(
            f"""SELECT {temporal_reason_sql()} FROM silver.transactions t
            JOIN silver.products p USING(product_id) JOIN silver.customers c ON t.customer_id=c.customer_id
            CROSS JOIN temporal_clock WHERE t.transaction_id='fixture-txn-14'"""
        ).fetchone() == ("after_bank_clock",)
        register_temporal_exports(db, Path(marker["gold_dir"]))
        assert validate_temporal_exports(db, CLOCK)["transactions"] == 0


def test_nullable_text_contract_matches_exact_enum() -> None:
    contract = yaml.safe_load(Path("contracts/gold_transactions.yaml").read_text())
    field = contract["columns"]["temporal_quality_reason"]
    assert field["nullable"] is True
    assert PG_TYPES[field["type"]] == "text"
    assert field["enum"] == [
        "before_product_open",
        "after_bank_clock",
        "product_updated_after_clock",
        "customer_updated_after_clock",
    ]


@pytest.mark.parametrize(
    "altered_field",
    [
        "business_date",
        "customer_status",
        "product_status",
        "old_build",
        "missing_flag",
        "cleared_flag",
        "unknown_flag",
        "dropped_transaction",
        "duplicate_transaction",
        "dropped_customer",
        "dropped_product",
    ],
)
def test_load_preflight_rejects_bad_artifacts_before_bank_connection(
    tmp_path: Path, altered_field: str
) -> None:
    lake, source = tmp_path / "lake", tmp_path / "source"
    shutil.copytree(FIXTURE, source)
    edit_fixture(source / "products.csv", {"opening_date": "2026-06-15"})
    build_snapshot(source, lake, reports=False)
    marker_file = lake / "_meta/current.json"
    marker = json.loads(marker_file.read_text())
    if altered_field == "old_build":
        marker["build_fingerprint"] = "obsolete-authored-build"
        marker_file.write_text(json.dumps(marker))
    else:
        table = (
            "customers"
            if altered_field in ("customer_status", "dropped_customer")
            else "products"
            if altered_field in ("product_status", "dropped_product")
            else "transactions"
        )
        file = Path(marker["gold_dir"]) / f"{table}.parquet"
        with duckdb.connect() as db:
            db.execute("CREATE TABLE altered AS SELECT * FROM read_parquet(?)", [str(file)])
            query = {
                "business_date": "UPDATE altered SET process_date=process_date-1",
                "customer_status": "UPDATE altered SET customer_status='Closed'",
                "product_status": "UPDATE altered SET product_status='Closed'",
                "missing_flag": "ALTER TABLE altered DROP temporal_quality_reason",
                "cleared_flag": "UPDATE altered SET temporal_quality_reason=NULL",
                "unknown_flag": "UPDATE altered SET temporal_quality_reason='not_in_contract'",
                "dropped_transaction": "DELETE FROM altered WHERE transaction_id='fixture-txn-14'",
                "duplicate_transaction": "INSERT INTO altered SELECT * FROM altered",
                "dropped_customer": "DELETE FROM altered WHERE customer_id='fixture-customer-a'",
                "dropped_product": "DELETE FROM altered WHERE product_id='fixture-product-a'",
            }[altered_field]
            db.execute(query)
            db.execute("COPY altered TO ? (FORMAT PARQUET)", [str(file)])
    with (
        patch("aclara.data.serving_load.psycopg.connect") as connect,
        pytest.raises(ValueError, match="preflight|outdated"),
    ):
        load_serving(lake, "authored-never-used-connection")
    connect.assert_not_called()
