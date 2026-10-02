"""Authored boundary cases prove unsafe facts never reach operational exports."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

from aclara.data.serving_load import load_serving
from aclara.data.snapshot import build_snapshot
from aclara.data.temporal import (
    register_temporal_exports,
    temporal_profile,
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
    ("file", "fields", "counts"),
    [
        ("products.csv", {"opening_date": "2026-06-15"}, (2, 2, 2)),
        ("transactions/day-14.csv", {"process_date": "2026-06-13"}, (2, 2, 2)),
        ("customers.csv", {"last_updated": CLOCK}, (1, 1, 0)),
        ("products.csv", {"last_updated": "2026-06-18T06:00:01Z"}, (2, 1, 0)),
        ("products.csv", {"opening_date": "2026-06-18"}, (2, 1, 0)),
        ("customers.csv", {"last_updated": "2026-06-18T05:59:59.999999Z"}, (2, 2, 3)),
    ],
)
def test_temporal_exclusions_preserve_history(
    tmp_path: Path, file: str, fields: dict[str, str], counts: tuple[int, int, int]
) -> None:
    source, lake = tmp_path / "source", tmp_path / "lake"
    shutil.copytree(FIXTURE, source)
    edit_fixture(source / file, fields)
    profile = build_snapshot(source, lake, reports=False)
    assert (
        tuple(profile["gold_row_counts"][t] for t in ("customers", "products", "transactions"))
        == counts
    )
    assert profile["gold_row_counts"]["matcher_ledger"] == 3
    marker = json.loads((lake / "_meta/current.json").read_text())
    with duckdb.connect(marker["database"], read_only=True) as db:
        # The reader's local timezone must not alter the business-date guard.
        db.execute("SET TimeZone='Asia/Tokyo'")
        flags = temporal_profile(db, CLOCK)
        assert flags["eligible_transaction_rows"] == counts[2]
        assert flags["blocked_transaction_rows"] == 3 - counts[2]
        register_temporal_exports(db, Path(marker["gold_dir"]))
        assert validate_temporal_exports(db, CLOCK) == dict.fromkeys(
            ("customers", "products", "transactions"), 0
        )
        assert db.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema='gold' AND column_name IN ('registration_branch_id','assigned_branch_id','affected_product_id')"
        ).fetchone() == (0,)


def test_business_boundary_uses_date_minus_six_hours(tmp_path: Path) -> None:
    source, lake = tmp_path / "source", tmp_path / "lake"
    shutil.copytree(FIXTURE, source)
    edit_fixture(source / "products.csv", {"opening_date": "2026-06-15"})
    file = source / "transactions/day-14.csv"
    edit_fixture(file, {"transaction_date": "2026-06-15T05:59:59.999999Z"})
    before = build_snapshot(source, lake, reports=False)
    assert before["gold_row_counts"]["transactions"] == 2
    edit_fixture(file, {"transaction_date": "2026-06-15T06:00:00Z", "process_date": "2026-06-15"})
    after = build_snapshot(source, lake, reports=False)
    assert after["gold_row_counts"]["transactions"] == 3


@pytest.mark.parametrize(
    "altered_field", ["business_date", "customer_status", "old_build", "historical_unsafe"]
)
def test_load_preflight_rejects_bad_artifacts_before_bank_connection(
    tmp_path: Path, altered_field: str
) -> None:
    lake = tmp_path / "lake"
    source = FIXTURE
    if altered_field == "historical_unsafe":
        source = tmp_path / "source"
        shutil.copytree(FIXTURE, source)
        edit_fixture(source / "products.csv", {"opening_date": "2026-06-15"})
    build_snapshot(source, lake, reports=False)
    marker_file = lake / "_meta/current.json"
    marker = json.loads(marker_file.read_text())
    if altered_field == "old_build":
        marker["build_fingerprint"] = "obsolete-authored-build"
        marker_file.write_text(json.dumps(marker))
    elif altered_field == "historical_unsafe":
        # Simulate accidentally exporting the retained analytical ledger under
        # a current fingerprint. Stamps alone must not approve the older row.
        file = Path(marker["gold_dir"]) / "transactions.parquet"
        with duckdb.connect(marker["database"], read_only=True) as db:
            db.execute("COPY gold.matcher_ledger TO ? (FORMAT PARQUET)", [str(file)])
    else:
        table = "transactions" if altered_field == "business_date" else "customers"
        file = Path(marker["gold_dir"]) / f"{table}.parquet"
        with duckdb.connect() as db:
            db.execute("CREATE TABLE altered AS SELECT * FROM read_parquet(?)", [str(file)])
            db.execute(
                "UPDATE altered SET process_date=process_date-1"
                if altered_field == "business_date"
                else "UPDATE altered SET customer_status='Closed'"
            )
            db.execute("COPY altered TO ? (FORMAT PARQUET)", [str(file)])
    with (
        patch("aclara.data.serving_load.psycopg.connect") as connect,
        pytest.raises(ValueError, match="preflight|outdated"),
    ):
        load_serving(lake, "authored-never-used-connection")
    connect.assert_not_called()
