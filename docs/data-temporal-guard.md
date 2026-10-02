# Temporal facts: analysis versus automation

This is a **post-v4 data fix, not reflected in official v4 numbers**. The committed implementation protects newly built operational exports. It does not modify an existing Azure database: the lead must rebuild, review availability and reload before claiming live protection.

## Measured exposure

The [direct-source reconciliation](data-quality-reconciliation.md) uses only local `LOCAL_RAW_DIR` inputs, dataset `b86f445cb468332bde984a788ef24f72f7070952b2d9292e0259e7b8f36397c9`, and `BANK_CLOCK=2026-06-18T06:00:00Z`. [Aggregate evidence](data/temporal-guard-aggregates.json) was computed with the new [eligibility profiler](../src/aclara/data/temporal.py), with private readback and no model/system evaluation runs.

| Anomaly | Full history | In the 492,414-row 120-day window |
|---|---:|---:|
| UTC transaction date before product opening | 827,610 | 10,193 |
| UTC or bank business date before opening (union) | — | 10,241 |
| Supplied business date differs from timestamp − 6 hours | 51 | 4 |
| Transaction linked to post-clock customer snapshot | 276,618 | 30,800 |
| Transaction linked to post-clock product snapshot | 277,363 | 30,983 |
| Any temporal blocker (union, not summed reasons) | — | **60,924** |

There are **9,301/150,000 customer snapshots** and **25,079/400,000 product snapshots** updated at or after the clock. These are dimension counts, distinct from linked transaction counts. The stricter business-date definition finds **827,989** pre-opening transactions over full history. Reader sessions explicitly set UTC, so local workstation timezones cannot reinterpret naive source timestamps.

The prospective eligible window is **431,490 / 492,414 (87.63%)**, excluding **60,924 (12.37%)** once each. This is a coverage cost, not an accuracy improvement or a rerun of any held-out suite.

## Operational treatment

| Finding | Historical analysis | Automation |
|---|---|---|
| Required missing/invalid facts, PK duplication, required FK/ownership break | Quarantine / block snapshot promotion | No new snapshot or load |
| Pre-opening transaction or inconsistent business date | Warn; preserve in silver and historical matcher ledger | Exclude transaction from operational gold |
| Customer or product snapshot updated at/after clock | Warn; preserve delivered snapshot | Exclude untrusted customer/product and their operational transactions |
| Product opening after last completed bank business date | Preserve source | Exclude product and its operational transactions |
| Broken branch references, unsafe complaint/digital product links | Report aggregates without following unsafe links | Fields excluded from serving projections |
| Optional nulls, volume mismatch, nonidentical natural-key collision | Warn with explicit denominator; no guessed repair | No authority inferred from missing facts or a collision |

The bank business anchor follows ADR-0015: `(BANK_CLOCK − 6 hours − 1 microsecond).date`. Updates must be strictly earlier than the clock; operational transaction timestamps use `[BANK_CLOCK − 120 days, BANK_CLOCK)`. Both UTC and business transaction dates must be on/after product opening. An earlier trusted dimension version is unavailable, so we cannot reconstruct a historical status or assume a post-clock edit left it unchanged. Excluding the entity is conservative and may reduce service availability; it does not delete organizer history.

## Dispute-path review and proof

Read-only inspection of the serving adapter found that dispute eligibility reads **customer status, product status and transaction business date**. It does not directly read `last_updated` or `opening_date`, but those statuses/dates can derive from anomalous snapshots. Therefore the previous blanket claim that temporal anomalies could not affect disputes was unjustified.

[dbt macros](../dbt/macros/temporal_guard.sql) now filter operational customers, products and transactions, without changing bank/interface columns. Full-history `transaction_facts` and `matcher_ledger` stay analytical, with their source ownership test preserved. The [dbt temporal invariant](../dbt/tests/temporal_serving.sql) tests the resulting operational tables. No source date is silently repaired.

The [serving loader](../src/aclara/data/serving_load.py) rejects stale build fingerprints, reads the actual exported Parquets against the private silver snapshot, and rejects unsafe or changed statuses/dates **before connecting to Postgres**. Existing atomic load/readback/RLS and durable-commit checks remain. A same-version reload also executes the preflight. Authored [regressions](../tests/test_data_temporal.py) cover pre-opening/business-date boundaries, update-at-clock and just-before-clock, future product opening, timezone-independent reads, retained analytical history, altered exports and no-bank-connection rejection.

After the lead rebuilds and loads with this code, the checked temporal fields cannot enter the dispute path through these operational exports. This guarantee depends on loading through this preflight; it does not cover unrelated external writers. Absence from the operational candidate set means insufficient trusted evidence, not proof that no charge exists. Offer a human review rather than inventing eligibility or repairing a date; the lead owns any additional runtime/UX handling.

## Activation and verification

1. Lead builds a new local snapshot from `LOCAL_RAW_DIR` with the same explicit clock; source transformations are reusable, gold rebuilds because its fingerprint changed.
2. Review excluded customer/product coverage and scoped demo/judge bindings before release. Analytical datasets and frozen evaluation suites are not rewritten.
3. Use the existing explicit serving-load command. Require zero temporal preflight failures plus full Postgres readback/RLS verification, and retain the old snapshot for rollback.
4. Recheck a scoped dispute with authored safe facts. Do not publish a changed accuracy/safety figure without a separately authorized evaluation.

Local guard/tests and source aggregates are verified; **a full organizer gold rebuild, Postgres load and Azure activation are pending lead review**. No cloud or paid model work was performed.
