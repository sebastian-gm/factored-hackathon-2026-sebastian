"""Reproduce routing capacity and score-only fraud flags without exporting rows."""

from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path

import duckdb
from dotenv import dotenv_values

from aclara.handoff.routing import aggregates, read_source
from aclara.settings import Settings


def main() -> None:
    values = dotenv_values(".env")
    raw = os.getenv("LOCAL_RAW_DIR") or values.get("LOCAL_RAW_DIR")
    if not raw:
        raise ValueError("LOCAL_RAW_DIR is required")
    source = Path(raw)
    directory = Path("artifacts/routing")
    directory.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect(":memory:")
    db.execute("SET memory_limit='2GB'")
    db.execute("SET TimeZone='UTC'")
    db.execute("SET temp_directory=?", [str((directory / "duckdb-temp").resolve())])
    clock = Settings().bank_clock
    paths = sorted(str(p) for p in (source / "transactions").rglob("*.csv"))
    if not paths:
        raise ValueError("No transaction objects found in the allowlisted source directory")
    rows = db.execute(
        """SELECT count(*),count(*) FILTER(WHERE t.fraud_score::DOUBLE>30)
      FROM read_csv(?,union_by_name=true,all_varchar=true) t
      JOIN read_csv(?,all_varchar=true) p ON t.product_id=p.product_id AND t.customer_id=p.customer_id
      WHERE t.transaction_date::TIMESTAMPTZ>=? AND t.transaction_date::TIMESTAMPTZ<?""",
        [paths, str(source / "products.csv"), clock - timedelta(days=120), clock],
    ).fetchone()
    assert rows is not None
    report = {
        **aggregates(read_source(source / "service_agents.csv")),
        "bank_clock": clock.isoformat(),
        "ledger_120_days": rows[0],
        "fraud_score_gt_30": rows[1],
        "score_flag_rate": rows[1] / rows[0] if rows[0] else None,
        "scope": "Owned 120-day ledger; score trigger only. Lost/stolen and simulated operational case bursts are separate triggers.",
    }
    (directory / "source-aggregates.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# Handoff routing and fraud flags",
        "",
        "Generated from local source aggregates; no source rows are committed.",
        "",
        *[f"- **{key}**: {json.dumps(value, ensure_ascii=False)}" for key, value in report.items()],
        "",
        "Routing requires Active agents, prefers Digital/Hybrid, then selects the least monthly interactions with a stable opaque-reference tie-break. PT fraud uses PT/Fraudes, then PT/Quejas y Reclamos with specialty fallback, then ES/Fraudes with language fallback. No eligible agent leaves an explicit pending assignment; it never invents an agent.",
        "",
        "The database projection contains only the six routing attributes listed above. The API role can read it but cannot change it. Existing forced customer/run/session RLS continues to protect operational records. The Azure deployment uses the same projection loader; no raw organizer file is embedded in an image or committed.",
        "",
    ]
    Path("docs/handoff-routing.md").write_text("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except (duckdb.Error, ValueError):
        raise SystemExit("Aggregate routing report failed; source details redacted") from None
