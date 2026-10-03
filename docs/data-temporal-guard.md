# Temporal quality flags and the dispute gate

This is a **post-v4 data change, not reflected in official v4 numbers**. Transactions remain visible and explainable. A temporal flag requires the lead-owned policy to hand off an attempted dispute instead of automating it. This data PR alone does not activate the policy or change the live database. The earlier exclusion proposal was never merged or deployed and is superseded by this contract.

## Exact serving contract

[gold_transactions.yaml](../contracts/gold_transactions.yaml) adds one field, `temporal_quality_reason`, exported as nullable VARCHAR and loaded as **Postgres `TEXT NULL`**. No other serving column changes. `NULL` means the transaction passed these four temporal checks; it does not establish dispute eligibility or resolve other DQ warnings.

| Enum reason | Predicate | Meaning |
|---|---|---|
| `before_product_open` | Transaction UTC calendar date **or supplied bank business date** is before the product opening date | The charge cannot be given automated authority from the delivered product timeline. |
| `after_bank_clock` | Transaction timestamp is at or after `BANK_CLOCK` | The charge is outside the completed clock interval. |
| `product_updated_after_clock` | Linked product `last_updated` is at or after `BANK_CLOCK` | The delivered product status may contain post-clock information. |
| `customer_updated_after_clock` | Linked customer `last_updated` is at or after `BANK_CLOCK` | The delivered customer status may contain post-clock information. |

For overlapping findings, store the first applicable reason in the table's order. Each non-null value has the same automation restriction, so choosing a primary reason does not remove that restriction. Aggregate diagnostics retain all overlapping findings; the single serving field is not a complete list of anomalies. Timestamps are interpreted in UTC, including in a reader session whose local timezone differs.

**Preserve the existing half-open serving window** `[BANK_CLOCK − 120 days, BANK_CLOCK)`, as directed by the owner. No new temporal filter removes a transaction inside that window. Full customer/product projections also remain unchanged. The `after_bank_clock` predicate is defined and tested, but cannot occur inside this window; the fixed delivered source also contains zero such transactions over full history. It is not a request to expand the serving window.

The supplied business date is compared with `(transaction_timestamp − 6 hours).date` for DQ warnings. A mismatch alone has no reason in the approved four-value enum and remains a warning; it is flagged only if one of the four predicates also applies. No date is silently repaired. ADR-0015's last completed business-date anchor is `(BANK_CLOCK − 6 hours − 1 microsecond).date`; the lead's dispute window remains a separate policy check.

## Aggregate exposure and retained coverage

The [direct-source reconciliation](data-quality-reconciliation.md) reads only local `LOCAL_RAW_DIR`, dataset `b86f445cb468332bde984a788ef24f72f7070952b2d9292e0259e7b8f36397c9`, at `BANK_CLOCK=2026-06-18T06:00:00Z`. [Aggregate evidence](data/temporal-guard-aggregates.json) comes from the private source-derived warehouse and the [temporal profiler](../src/aclara/data/temporal.py), without model calls or system evaluation runs.

| Finding | Full history | In the 492,414-row serving window | Primary reason rows |
|---|---:|---:|---:|
| UTC transaction date before product opening | 827,610 | 10,193 | — |
| UTC or supplied bank business date before opening (union) | — | 10,241 | 10,241 |
| Transaction at/after bank clock | 0 | 0 | 0 |
| Transaction linked to post-clock product snapshot | 277,363 | 30,983 | 21,852 |
| Transaction linked to post-clock customer snapshot | 276,618 | 30,800 | 28,827 |
| Any of the four reasons (union) | — | **60,920** | **60,920** |
| Business-date/timestamp mismatch (warning only) | 51 | 4 | — |

**All 492,414 transactions remain visible**: 60,920 flagged and 431,494 unflagged. The union counts each transaction once; overlapping findings must not be summed. All 150,000 customers and 400,000 products retain their existing projections. The source has 9,301 post-clock customer snapshots and 25,079 post-clock product snapshots. The stricter supplied business-date check finds 827,989 pre-opening transactions over full history. These are data-quality measurements, not runtime handoff counts or evidence of improved evaluation accuracy.

## Operational treatment

| Finding | Data treatment | Runtime dependency |
|---|---|---|
| Required missing/invalid facts, PK duplication, required FK/ownership break | Quarantine / block snapshot promotion | No new snapshot or serving load |
| Any of the four temporal reasons | Preserve original facts; add the nullable reason | Explain allowed; automated dispute blocked; handoff with a data-quality reason and an `open_question` naming the anomaly |
| Business-date mismatch without a listed reason | Preserve original date; report warning | No additional automation block is claimed by this four-reason contract |
| Broken branch references, unsafe complaint/digital product links | Report aggregates; exclude unsafe fields from serving projections | Never follow an excluded link |
| Optional nulls, volume mismatch, nonidentical natural-key collision | Warn with denominators; no guessed repair or deduplication | Missing facts or collisions grant no authority |

Read-only dispute-path inspection found that eligibility uses customer status, product status and transaction business date. Although it does not directly use `last_updated` or `opening_date`, its facts can derive from anomalous snapshots. Preserving those rows requires the explicit policy gate; the data export alone cannot prove that disputes avoid anomalous authority. Earlier trusted dimension versions are unavailable, so a historical status cannot be reconstructed safely.

## Export proof and loader checks

[dbt](../dbt/models/transactions.sql) appends the reason without changing existing transaction fields. [dbt invariants](../dbt/tests/temporal_serving.sql) verify complete source-equivalent customer/product/window transaction row sets and correct nullable flags. Historical silver, `transaction_facts` and `matcher_ledger` remain unchanged. The gold contract enforces the four-value enum.

The [serving loader](../src/aclara/data/serving_load.py) rejects stale build fingerprints and checks actual exported customer/product/transaction Parquets against the private silver snapshot **before connecting to Postgres**. Missing or incorrect flags, removed/duplicated rows and changes to any non-lineage field in these three projections fail preflight. This includes transaction status/type/amount/currency, supplied USD amount, fraud score, product type, copied dimension facts and display fields. Recomputed USD amount, FX date, nearest-prior indicator and foreign-transaction flag are derived again from silver facts and rates using the same USD shortcut and ASOF rule as dbt; cached gold FX/ledger values do not grant equivalence. Correctly flagged rows pass. Existing atomic COPY, checksums, forced RLS and durable-commit readback remain. A fresh serving table uses nullable TEXT. The lead's #131 migration adds only the exact missing column inside the locked COPY/readback transaction, with DDL/data rollback together. Unexpected column names/types or NOT NULL still fail.

This preflight does not compare the five underscore-prefixed lineage columns (`_dataset_version`, `_source_file`, `_source_sha256`, `_ingested_at`, `_pipeline_version`) or the other serving tables (FX reference rates, agent directory, complaint aggregate). None of the serving authority fields identified in the lead review is excluded. The raw `is_fraud` label remains absent from serving projections; the checked serving field is `fraud_score`. Existing loader metadata and full Postgres checksum/readback checks remain separate; they do not prove source equivalence for those excluded fields/tables.

[Authored regressions](../tests/test_data_temporal.py) independently specify retained row counts, exact reasons and precedence, both sides of the six-hour business-date boundary, update-at-clock/just-before-clock, warning-only mismatches, timezone-independent reads, the unchanged serving window and original transaction fields, and tampered/old exports rejected before any bank connection. [Serving mutation regressions](../tests/test_serving_load.py) alter each reviewed authority field separately and assert rejection before any bank connection, including NULL-to-value changes. Their shared authored snapshot checks exact-rate, prior-rate and USD FX; missing source rates still block upstream promotion. These tests are included in the existing Postgres/data CI gate. The fast Python gate skips snapshot tests when optional dbt is absent. Database readback/type tests require disposable local Postgres; no organizer rows enter fixtures or CI.

## Coordinated release

The lead's DQ-01/migration companion #131 merged on green CI. This data PR still
requires green CI after its history-preserving refresh onto that migration.
The [release plan](history/evaluation/temporal-quality-release-plan.md) pairs the image
and serving reload. Required behavior:

1. An older serving load without this column fails closed **for automation only**. Explanations remain available, and readiness reports a warning; absence must never be treated as `NULL`/passed.
2. A non-null reason permits explanation but blocks automatic dispute creation. Create a data-quality handoff with an `open_question` naming the anomaly; read back the handoff before success.
3. The final release ships the policy-capable image and the flagged serving reload together. Its release gate asserts `bank.transactions.temporal_quality_reason` exists as nullable TEXT, verifies enum/flag coverage and serving readback, and exercises flagged and missing-column paths using authored cases.
4. Rebuild from local `LOCAL_RAW_DIR` using the final merged data head. Migration and serving COPY/readback commit atomically; do not commit a new NULL column on old unchecked rows. Check scoped demo/profile availability before releasing; all original window transactions should remain available.

The data lane did not perform an organizer rebuild or Azure load. After the
paired integration, the lead rebuilt local organizer gold and verified zero
source-equivalence mismatches; counts match this report. See the
[local evidence and release plan](history/evaluation/temporal-quality-release-plan.md).
Azure serving reload/deployment remains unexecuted. This data PR adds no NLU,
frozen-suite or official-result change. New model spend: USD 0.
