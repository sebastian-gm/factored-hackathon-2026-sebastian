"""Full-table DQ gates and aggregate-only evidence; never return source rows."""

# ruff: noqa: S608 -- SQL fragments use fixed identifiers and internally defined predicates.
from __future__ import annotations

from typing import Any

import duckdb

from aclara.data.pipeline import _fetchone, _read_contract, _sql_identifier

DOCUMENTED = {
    "customers": 150_000,
    "products": 400_000,
    "transactions": 5_000_000,
    "daily_exchange_rates": 3_000,
    "service_agents": 1_200,
    "complaints": 80_000,
    "call_center_interactions": 800_000,
    "satisfaction_surveys": 250_000,
    "call_transcripts": 200_000,
    "digital_events": 10_000_000,
}


def records(db: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    cursor = db.execute(sql)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def quality_report(
    db: duckdb.DuckDBPyConnection, version: str, clock: str, ingest: dict[str, Any]
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def scalar(query: str) -> int:
        row = db.execute(query).fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def check(
        identifier: str,
        severity: str,
        observed: int | float,
        *,
        threshold: float = 0,
        scope: str = "snapshot",
    ) -> None:
        failed = observed > threshold
        checks.append(
            {
                "id": identifier,
                "severity": severity,
                "owner": "data-ml",
                "observed": observed,
                "threshold": threshold,
                "status": "FAIL" if failed and severity == "fail" else "WARN" if failed else "PASS",
                "scope": scope,
                "blocks_promotion": failed and severity == "fail" and scope == "snapshot",
            }
        )

    db.execute(
        "CREATE OR REPLACE TEMP TABLE analysis_clock AS SELECT ?::TIMESTAMPTZ AS as_of", [clock]
    )
    tables = {}
    for table, stats in ingest.items():
        relation = "silver." + _sql_identifier(table)
        keys = ",".join(_sql_identifier(key) for key in _read_contract(table)["primary_key"])
        rows = scalar(f"SELECT count(*) FROM {relation}")
        duplicates = scalar(
            f"SELECT coalesce(sum(n-1),0) FROM (SELECT count(*) AS n FROM {relation} GROUP BY {keys} HAVING count(*)>1)"
        )
        tables[table] = {
            **stats,
            "rows": rows,
            "documented_rows": DOCUMENTED[table],
            "duplicate_primary_keys": duplicates,
        }
        check(f"STRUCT-{table}-invalid", "fail", stats["invalid_rows"])
        check(f"STRUCT-{table}-pk", "fail", duplicates)
        check(f"SCHEMA-{table}-extra", "warn", stats["unknown_column_files"])
        check(f"VOLUME-{table}", "warn", abs(rows - DOCUMENTED[table]))
        if table not in {"customers", "daily_exchange_rates", "service_agents"}:
            orphan = scalar(
                f"SELECT count(*) FROM {relation} t LEFT JOIN silver.customers c USING(customer_id) WHERE t.customer_id IS NOT NULL AND c.customer_id IS NULL"
            )
            check(f"FK-{table}-customer", "fail", orphan)
    check(
        "FK-transactions-product",
        "fail",
        scalar(
            "SELECT count(*) FROM silver.transactions t LEFT JOIN silver.products p USING(product_id) WHERE p.product_id IS NULL"
        ),
    )
    check(
        "OWNER-transactions",
        "fail",
        scalar(
            "SELECT count(*) FROM silver.transactions t JOIN silver.products p USING(product_id) WHERE t.customer_id IS DISTINCT FROM p.customer_id"
        ),
    )
    for table, field in (
        ("call_center_interactions", "agent_id"),
        ("complaints", "assigned_agent_id"),
        ("call_transcripts", "agent_id"),
        ("satisfaction_surveys", "agent_id"),
    ):
        check(
            f"FK-{table}-agent",
            "fail",
            scalar(
                f"SELECT count(*) FROM silver.{table} t LEFT JOIN silver.service_agents a ON t.{field}=a.agent_id WHERE t.{field} IS NOT NULL AND a.agent_id IS NULL"
            ),
        )
    for table in ("call_transcripts", "satisfaction_surveys"):
        check(
            f"FK-{table}-interaction",
            "fail",
            scalar(
                f"SELECT count(*) FROM silver.{table} t LEFT JOIN silver.call_center_interactions i USING(interaction_id) WHERE t.interaction_id IS NOT NULL AND i.interaction_id IS NULL"
            ),
        )
    ownership = records(
        db,
        "SELECT count(*) AS joinable, count(*) FILTER (WHERE q.customer_id=p.customer_id) AS owned, count(*) FILTER (WHERE q.customer_id IS DISTINCT FROM p.customer_id) AS mismatched FROM silver.complaints q JOIN silver.products p ON q.affected_product_id=p.product_id",
    )[0]
    # This FAIL applies to the unsafe field; every gold model excludes the entire link.
    check(
        "OWNER-complaints-affected-product",
        "fail",
        ownership["mismatched"],
        scope="excluded_field:complaints.affected_product_id",
    )
    check(
        "DATE-business-offset",
        "warn",
        scalar(
            "SELECT count(*) FROM silver.transactions WHERE process_date <> (transaction_date-INTERVAL 6 HOUR)::DATE"
        ),
    )
    check(
        "DATE-before-product-open",
        "warn",
        scalar(
            "SELECT count(*) FROM silver.transactions t JOIN silver.products p USING(product_id) WHERE t.transaction_date::DATE<p.opening_date"
        ),
    )
    for table in ("customers", "products"):
        check(
            f"DATE-{table}-future-update",
            "warn",
            scalar(
                f"SELECT count(*) FROM silver.{table}, analysis_clock WHERE last_updated >= as_of"
            ),
        )
    check(
        "CURRENCY-mx-usd",
        "warn",
        scalar(
            "SELECT count(*) FROM silver.transactions t JOIN silver.customers c USING(customer_id) WHERE c.country='MX' AND t.currency='USD'"
        ),
    )
    check(
        "DUP-products-number",
        "warn",
        scalar("SELECT count(*)-count(DISTINCT product_number) FROM silver.products"),
    )
    check(
        "DUP-transactions-near",
        "warn",
        scalar(
            "SELECT coalesce(sum(n-1),0) FROM (SELECT count(*) AS n FROM silver.transactions GROUP BY customer_id,product_id,transaction_date,transaction_type,amount,currency,merchant_name HAVING count(*)>1)"
        ),
    )
    db.execute(
        "CREATE OR REPLACE TEMP VIEW fx_transactions AS SELECT t.*, CASE WHEN t.currency='USD' THEN t.amount ELSE t.amount*f.exchange_rate END AS recomputed_usd, f.date AS fx_date FROM silver.transactions t ASOF LEFT JOIN (SELECT * FROM silver.daily_exchange_rates WHERE target_currency='USD') f ON t.currency=f.source_currency AND t.process_date>=f.date"
    )
    check(
        "FX-missing-prior-rate",
        "fail",
        scalar("SELECT count(*) FROM fx_transactions WHERE recomputed_usd IS NULL"),
    )
    check(
        "FX-nearest-prior",
        "warn",
        scalar(
            "SELECT count(*) FROM fx_transactions WHERE currency<>'USD' AND fx_date<process_date"
        ),
    )
    fx = records(
        db,
        "SELECT count(*) FILTER (WHERE amount_usd IS NOT NULL) AS comparable, count(*) FILTER (WHERE amount_usd IS NOT NULL AND abs(amount_usd-recomputed_usd)>0.01) AS differs_over_one_cent, avg(abs(amount_usd-recomputed_usd)/nullif(recomputed_usd,0)) FILTER (WHERE amount_usd IS NOT NULL) AS mean_relative_gap, quantile_cont(recomputed_usd,[0.5,0.75,0.9,0.95,0.99]) FILTER (WHERE transaction_type IN ('Purchase','Withdrawal','Payment')) AS disputable_usd_quantiles FROM fx_transactions",
    )[0]
    check("FX-source-usd-gap", "warn", fx["differs_over_one_cent"])
    contacts = records(
        db,
        "SELECT contact_reason, count(*) AS n, count(*)::DOUBLE/sum(count(*)) OVER () AS volume_share, sum(duration_seconds)::DOUBLE/nullif(sum(sum(duration_seconds)) OVER (),0) AS handle_time_share, avg(was_resolved::INT) AS fcr, count(was_resolved) AS fcr_denominator, avg(duration_seconds) AS mean_duration_seconds, avg(was_escalated::INT) AS escalation_share, avg(wait_time_seconds) AS mean_wait_seconds FROM silver.call_center_interactions GROUP BY contact_reason ORDER BY n DESC",
    )
    complaints = records(
        db,
        "SELECT category, subcategory, count(*) AS n, avg(sla_breached::INT) AS sla_breach_share, avg(resolution_days) AS mean_resolution_calendar_days, count(resolution_days) AS resolution_days_n FROM silver.complaints GROUP BY category,subcategory ORDER BY n DESC",
    )
    csat = records(
        db,
        "SELECT i.was_resolved, count(*) AS n, min(s.main_score) AS min_score, max(s.main_score) AS max_score, avg(s.main_score) AS mean_score FROM silver.satisfaction_surveys s JOIN silver.call_center_interactions i ON s.interaction_id=i.interaction_id AND s.customer_id=i.customer_id WHERE s.survey_type='CSAT' AND i.was_resolved IS NOT NULL GROUP BY i.was_resolved ORDER BY i.was_resolved",
    )
    accents = {}
    for name, expression in (("used", "i.agent_used_accent"), ("native", "a.native_accent")):
        accents[name] = records(
            db,
            f"SELECT (i.customer_detected_accent={expression}) AS accent_match, count(DISTINCT i.interaction_id) AS contacts, avg(i.was_resolved::INT) AS fcr, count(s.survey_id) AS csat_n, avg(s.main_score) AS mean_csat FROM silver.call_center_interactions i LEFT JOIN silver.service_agents a USING(agent_id) LEFT JOIN (SELECT interaction_id, customer_id, avg(main_score) AS main_score, min(survey_id) AS survey_id FROM silver.satisfaction_surveys WHERE survey_type='CSAT' GROUP BY interaction_id,customer_id) s ON s.interaction_id=i.interaction_id AND s.customer_id=i.customer_id WHERE i.customer_detected_accent IS NOT NULL AND {expression} IS NOT NULL GROUP BY accent_match ORDER BY accent_match",
        )
    texts = {
        "complaints": records(
            db,
            "SELECT count(*) AS n, count(DISTINCT description) AS descriptions, count(DISTINCT resolution) AS resolutions, count(*) FILTER (WHERE resolution IS NULL) AS resolution_nulls, count(*) FILTER (WHERE origin_interaction_id IS NULL) AS origin_nulls FROM silver.complaints",
        )[0],
        "transcripts": records(
            db,
            "SELECT count(*) AS n, count(DISTINCT full_text) AS distinct_texts, count(*) FILTER (WHERE regexp_matches(full_text, '\\{[^}]+\\}')) AS with_placeholders, count(*) FILTER (WHERE detected_language='pt') AS portuguese_rows FROM silver.call_transcripts",
        )[0],
        "surveys": records(
            db,
            "SELECT count(*) AS n, count(DISTINCT open_comments) AS distinct_comments, count(*) FILTER (WHERE open_comments IS NULL) AS null_comments FROM silver.satisfaction_surveys",
        )[0],
    }
    check("TEXT-transcript-placeholders", "warn", texts["transcripts"]["with_placeholders"])
    check(
        "SCHEMA-transcript-duration-null",
        "warn",
        scalar("SELECT count(*) FROM silver.call_transcripts WHERE duration_seconds IS NULL"),
    )
    agents = records(
        db,
        "SELECT count(*) AS total, count(*) FILTER (WHERE contains(lower(languages),'portugu')) AS portuguese, count(*) FILTER (WHERE specialty='Fraudes') AS fraud, count(*) FILTER (WHERE specialty='Quejas y Reclamos') AS complaints, count(*) FILTER (WHERE specialty='Fraudes' AND contains(lower(languages),'portugu') AND agent_status='Active') AS active_pt_fraud, count(*) FILTER (WHERE specialty='Fraudes' AND contains(lower(languages),'portugu') AND agent_status='Active' AND agent_type IN ('Digital','Hybrid')) AS active_digital_pt_fraud FROM silver.service_agents",
    )[0]
    fraud = records(
        db,
        "SELECT threshold, count(*) AS total, count(*) FILTER (WHERE fraud_score>threshold) AS flagged, count(*) FILTER (WHERE fraud_score>threshold AND is_fraud) AS labeled_fraud, count(*) FILTER (WHERE transaction_date >= as_of-INTERVAL 120 DAY AND transaction_date<as_of) AS window_n, count(*) FILTER (WHERE transaction_date >= as_of-INTERVAL 120 DAY AND transaction_date<as_of AND fraud_score>threshold) AS window_flagged FROM silver.transactions, (VALUES (27),(30)) thresholds(threshold), analysis_clock GROUP BY threshold ORDER BY threshold",
    )
    candidate_counts = records(
        db,
        "WITH counts AS (SELECT c.customer_id, count(t.transaction_id) AS n FROM silver.customers c CROSS JOIN analysis_clock LEFT JOIN silver.transactions t ON c.customer_id=t.customer_id AND t.transaction_date>=as_of-INTERVAL 120 DAY AND t.transaction_date<as_of GROUP BY c.customer_id) SELECT count(*) AS customers, sum(n) AS transactions, count(*) FILTER (WHERE n=0) AS zero_customers, quantile_cont(n,0.5) AS p50, quantile_cont(n,0.9) AS p90, max(n) AS maximum FROM counts",
    )[0]
    pending = records(
        db,
        "SELECT count(*) AS n, count(*) FILTER (WHERE transaction_date<as_of-INTERVAL 14 DAY) AS over_14_days FROM silver.transactions,analysis_clock WHERE transaction_status='Pending' AND transaction_date>=as_of-INTERVAL 120 DAY AND transaction_date<as_of",
    )[0]
    channel_type = records(
        db,
        "SELECT channel,transaction_type,count(*) AS n FROM silver.transactions GROUP BY channel,transaction_type ORDER BY channel,transaction_type",
    )
    # A next-contact ASOF join avoids a many-to-many range join. Exclude right-censored events.
    app_contact = records(
        db,
        "WITH events AS (SELECT customer_id,event_date,event_type='Error' AS is_error FROM silver.digital_events,analysis_clock WHERE customer_id IS NOT NULL AND channel IN ('Android App','iOS App') AND action IN ('view_transactions','initiate_transfer','initiate_payment') AND event_date<=as_of-INTERVAL 48 HOUR), joined AS (SELECT e.*, i.interaction_date FROM events e ASOF LEFT JOIN silver.call_center_interactions i ON e.customer_id=i.customer_id AND e.event_date<=i.interaction_date) SELECT is_error,count(*) AS events,count(*) FILTER (WHERE interaction_date<event_date+INTERVAL 48 HOUR) AS followed_by_contact, avg(CASE WHEN interaction_date<event_date+INTERVAL 48 HOUR THEN 1.0 ELSE 0.0 END) AS contact_rate FROM joined GROUP BY is_error ORDER BY is_error",
    )
    return {
        "dataset_version": version,
        "bank_clock": clock,
        "tables": tables,
        "checks": checks,
        "contact_reasons": contacts,
        "complaint_mix": complaints,
        "complaint_ownership": ownership,
        "complaint_channels": records(
            db,
            "SELECT reception_channel,count(*) AS n FROM silver.complaints GROUP BY reception_channel ORDER BY n DESC",
        ),
        "contact_channels": records(
            db,
            "SELECT channel,count(*) AS n FROM silver.call_center_interactions GROUP BY channel ORDER BY n DESC",
        ),
        "day_of_week": records(
            db,
            "SELECT isodow(interaction_date)::INT AS weekday,count(*) AS n,count(DISTINCT interaction_date::DATE) AS observed_days,count(*)::DOUBLE/count(DISTINCT interaction_date::DATE) AS contacts_per_observed_day FROM silver.call_center_interactions GROUP BY weekday ORDER BY weekday",
        ),
        "hour_of_day": records(
            db,
            "SELECT hour(interaction_date)::INT AS utc_hour,count(*) AS n FROM silver.call_center_interactions GROUP BY utc_hour ORDER BY utc_hour",
        ),
        "csat_by_resolution": csat,
        "accent_test": accents,
        "text_degeneracy": texts,
        "agents": agents,
        "fx": fx,
        "fraud_thresholds": fraud,
        "candidate_counts": candidate_counts,
        "pending_window": pending,
        "channel_type_counts": channel_type,
        "app_error_contact": app_contact,
        "currency_counts": records(
            db,
            "SELECT currency,count(*) AS n FROM silver.transactions GROUP BY currency ORDER BY currency",
        ),
        "foreign_transactions": scalar(
            "SELECT count(*) FROM silver.transactions t JOIN silver.customers c USING(customer_id) WHERE t.transaction_country<>c.country"
        ),
        "max_business_date": str(
            _fetchone(db, "SELECT max(process_date) FROM silver.transactions")[0]
        ),
    }
