"""Only project-generated inputs; no organizer records in tests or CI."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import duckdb
import pytest

from aclara.data.snapshot import PromotionBlocked, build_snapshot

FIXTURE = Path(__file__).parent / "fixtures/incremental"


def test_incremental_atomic_gate_and_idempotence(tmp_path: Path) -> None:
    pytest.importorskip("dbt.cli.main")
    source, lake = tmp_path / "source", tmp_path / "lake"
    shutil.copytree(FIXTURE / "day1", source)
    day1 = build_snapshot(source, lake, reports=False)
    assert day1["gold_row_counts"]["transactions"] == 3
    assert day1["complaint_ownership"] == {"joinable": 1, "owned": 0, "mismatched": 1}
    marker1 = json.loads((lake / "_meta/current.json").read_text())
    no_op = build_snapshot(source, lake, reports=False)
    assert no_op["no_op"]
    assert json.loads((lake / "_meta/current.json").read_text()) == marker1
    shutil.copytree(FIXTURE / "day2", source, dirs_exist_ok=True)
    shutil.copytree(FIXTURE / "bad", source, dirs_exist_ok=True)
    with pytest.raises(PromotionBlocked):
        build_snapshot(source, lake, reports=False)
    assert json.loads((lake / "_meta/current.json").read_text()) == marker1
    assert list((lake / "quarantine").rglob("*.parquet"))
    (source / "transactions/invalid.csv").unlink()
    day2 = build_snapshot(source, lake, reports=False)
    assert day2["dataset_version"] != day1["dataset_version"]
    assert day2["gold_row_counts"]["transactions"] == 5
    assert day2["tables"]["transactions"]["unknown_column_files"] == 1
    assert all(day2["tables"][table]["rebuilt_objects"] == 0 for table in day2["tables"])
    marker2 = json.loads((lake / "_meta/current.json").read_text())
    with duckdb.connect(marker2["database"], read_only=True) as db:
        assert db.execute(
            "SELECT amount FROM gold.transactions WHERE transaction_id='fixture-txn-15'"
        ).fetchone() == (75.0,)
        assert db.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema='gold' AND column_name='affected_product_id'"
        ).fetchone() == (0,)
        assert db.execute(
            "SELECT count(DISTINCT _dataset_version) FROM gold.transactions"
        ).fetchone() == (1,)
    assert build_snapshot(source, lake, reports=False)["no_op"]
    # Removing an object removes its rows, even though immutable objects remain cached.
    (source / "transactions/day-10.csv").unlink()
    removed = build_snapshot(source, lake, reports=False)
    assert removed["manifest_status_counts"]["removed"] == 1
    assert removed["gold_row_counts"]["transactions"] == 4
    # Clock changes rebuild the serving window without rebuilding source transformations.
    earlier = build_snapshot(source, lake, bank_clock="2026-06-16T00:00:00Z", reports=False)
    assert earlier["gold_row_counts"]["transactions"] == 2
    assert earlier["bronze_objects_copied"] == 0


def test_missing_required_schema_is_quarantined(tmp_path: Path) -> None:
    source, lake = tmp_path / "source", tmp_path / "lake"
    shutil.copytree(FIXTURE / "day1", source)
    path = source / "transactions/day-14.csv"
    text = path.read_text().replace("transaction_status", "missing_status")
    path.write_text(text)
    with pytest.raises(PromotionBlocked, match="required columns"):
        build_snapshot(source, lake, reports=False)
    assert not (lake / "_meta/current.json").exists()
    assert list((lake / "quarantine").rglob("*.json"))


def test_naive_clock_and_overlapping_directories_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timezone"):
        build_snapshot(FIXTURE / "day1", tmp_path / "lake", bank_clock="2026-06-18", reports=False)
    with pytest.raises(ValueError, match="overlap"):
        build_snapshot(tmp_path, tmp_path / "lake", reports=False)
