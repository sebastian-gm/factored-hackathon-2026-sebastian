"""Authored records exercise duplicates that PK checks alone miss."""

from __future__ import annotations

import duckdb

from aclara.data.pipeline import SQL_TYPES, _read_contract, _sql_identifier
from aclara.data.profiling import column_null_profile, duplicate_profile


def test_column_missingness_includes_zero_all_null_and_empty_populations() -> None:
    with duckdb.connect() as db:
        db.execute("CREATE SCHEMA silver")
        fields = ",".join(
            f"{_sql_identifier(name)} {SQL_TYPES[rules['type']]}"
            for name, rules in _read_contract("customers")["columns"].items()
        )
        db.execute(f"CREATE TABLE silver.customers ({fields})")
        assert all(row["null_rate"] is None for row in column_null_profile(db, "customers"))
        db.execute(
            "INSERT INTO silver.customers (customer_id,email,mobile_phone) VALUES ('authored-a',NULL,''),('authored-b','authored@example.invalid','  ')"
        )
        profile = {row["column"]: row for row in column_null_profile(db, "customers")}
        assert profile["customer_id"]["null_rate"] == 0
        assert profile["email"]["nulls"] == 1
        assert profile["email"]["null_rate"] == 0.5
        assert profile["address"]["null_rate"] == 1
        assert profile["address"]["nullable"] is True
        assert profile["mobile_phone"]["nulls"] == 0
        assert profile["mobile_phone"]["blank_nonnull"] == 2
        assert profile["email"]["rows"] == 2
        assert not any("authored@example.invalid" in str(row) for row in profile.values())


def test_exact_replay_conflicting_pk_and_regenerated_id_are_separate() -> None:
    with duckdb.connect() as db:
        db.execute("CREATE SCHEMA raw")
        db.execute(
            "CREATE TABLE raw.products (product_id VARCHAR,product_number VARCHAR,product_status VARCHAR,process_date DATE)"
        )
        db.execute(
            "INSERT INTO raw.products VALUES ('a','authored-number','Active','2026-06-10'),('a','authored-number','Active','2026-06-10'),('a','authored-number','Blocked','2026-06-10'),('b','authored-number','Active','2026-06-11')"
        )
        profile = duplicate_profile(
            db,
            "products",
            ("product_id", "product_number", "product_status", "process_date"),
            ("product_id",),
            schema="raw",
        )
        assert profile["primary_key"] == {"groups": 1, "excess_rows": 2, "member_rows": 3}
        assert profile["exact_record"] == {"groups": 1, "excess_rows": 1, "member_rows": 2}
        assert profile["payload_without_id_or_partition_date"]["excess_rows"] == 2
        assert profile["business_key"]["excess_rows"] == 3
        assert "authored-number" not in str(profile)
        assert db.execute("SELECT count(*) FROM raw.products").fetchone() == (4,)


def test_event_fingerprint_detects_replay_even_with_new_sessions_and_nullable_keys() -> None:
    with duckdb.connect() as db:
        db.execute("CREATE SCHEMA raw")
        db.execute(
            "CREATE TABLE raw.digital_events (event_id VARCHAR,session_id VARCHAR,customer_id VARCHAR,event_date TIMESTAMP,event_type VARCHAR,event_category VARCHAR,channel VARCHAR,action VARCHAR,element_id VARCHAR,product_id VARCHAR,process_date DATE)"
        )
        db.execute(
            "INSERT INTO raw.digital_events VALUES ('a','one','authored-c','2026-06-10 10:00:00','Click','Banking','Web','view',NULL,NULL,'2026-06-10'),('b','one','authored-c','2026-06-10 10:00:00','Click','Banking','Web','view',NULL,NULL,'2026-06-10'),('c','two','authored-c','2026-06-10 10:00:00','Click','Banking','Web','view',NULL,NULL,'2026-06-10'),('d','two','authored-c','2026-06-10 10:00:01','Click','Banking','Web','view',NULL,NULL,'2026-06-10')"
        )
        columns = [row[0] for row in db.execute("DESCRIBE raw.digital_events").fetchall()]
        profile = duplicate_profile(db, "digital_events", columns, ("event_id",), schema="raw")
        assert profile["primary_key"]["excess_rows"] == 0
        assert profile["exact_record"]["excess_rows"] == 0
        assert profile["payload_without_id_or_partition_date"]["excess_rows"] == 1
        assert profile["business_key"]["excess_rows"] == 1
        assert profile["cross_session_event"]["excess_rows"] == 2


def test_same_exchange_rate_on_different_days_is_not_duplicate_activity() -> None:
    with duckdb.connect() as db:
        db.execute("CREATE SCHEMA raw")
        db.execute(
            "CREATE TABLE raw.daily_exchange_rates (date DATE,source_currency VARCHAR,target_currency VARCHAR,exchange_rate DOUBLE)"
        )
        db.execute(
            "INSERT INTO raw.daily_exchange_rates VALUES ('2026-06-10','USD','USD',1),('2026-06-11','USD','USD',1)"
        )
        profile = duplicate_profile(
            db,
            "daily_exchange_rates",
            ("date", "source_currency", "target_currency", "exchange_rate"),
            ("date", "source_currency", "target_currency"),
            schema="raw",
        )
        assert profile["payload_without_id_or_partition_date"]["excess_rows"] == 0
