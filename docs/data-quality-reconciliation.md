# Delivered-data quality reconciliation

Measured directly from `LOCAL_RAW_DIR` on 2026-10-02, with zero model calls. The ten contracted tables reproduce dataset `b86f445cb468332bde984a788ef24f72f7070952b2d9292e0259e7b8f36397c9`, the version in the [DQ report](data-quality-report.md). Three additional tables extend the duplicate and relationship audit; together the thirteen tables contain **23,495,188 records**. Source records, keys and private diagnostics remain ignored.

The organizer's *LATAM_Bank_Dataset_Summary (1).pdf*, version 1.0.0, generated July 2026, documents approximate volumes and “~2%” duplicates / “~5%” nonmandatory nulls, plus possible orphans (quality table, page 2). It does not specify a duplicate fingerprint or missingness denominator. These targets are not measured properties of this delivery.

## Duplicates: broadened definitions

The [scanner](../analysis/reconcile_data_quality.py) tests all thirteen tables. [Fingerprint definitions](../src/aclara/data/profiling.py) and [authored regression tests](../tests/test_data_quality_profile.py) distinguish exact records, repeated PKs, payload replay after removing surrogate IDs/partition dates, and business/event-key collisions. Natural date/currency FX keys remain in payloads: equal rates on different days are not replay. Excess rows count members beyond the first; member rows count everyone in a collision group. No source records are collapsed.

| Definition | Groups | Excess rows | Member rows |
|---|---:|---:|---:|
| Repeated primary keys, all tables | 0 | 0 | 0 |
| Exact full records, all tables | 0 | 0 | 0 |
| Payload replay, all tables | 0 | 0 | 0 |
| Product-number collisions / 400,000 products | 6 | 6 | 12 |
| Employee-code collisions / 1,200 agents | 13 | 13 | 26 |
| Transaction business/event fingerprint | 0 | 0 | 0 |
| Digital session-event fingerprint | 0 | 0 | 0 |
| Digital cross-session event fingerprint | 0 | 0 | 0 |

Cross-session events use customer, exact timestamp, type, channel, action and product; the **11,875,548 identified-customer events** are eligible, while anonymous events are excluded from that particular fingerprint. Other business fingerprints also have zero collisions. This is not a fuzzy-time/content duplicate detector. The earlier “zero duplicates” statement was valid for PKs and the transaction near-key only, not every identifier. Employee collision members are 26/1,200 = 2.17%, compatible with some injected imperfections but not evidence of 2% duplicates across the delivery. Surrogate IDs remain unique, and differing payloads are preserved.

## Nulls: explicit denominator and conditional fields

The [per-column report](data-quality-report.md#per-column-null-rates) covers **203 columns in ten contracted tables**, excluding lineage metadata. SQL NULLs total **157,483,584 / 538,022,507 cells = 29.27%**, or **157,483,584 / 340,935,630 nullable cells = 46.19%**. Required-column NULLs, non-null blank strings and contract-invalid rows are all zero. Cast failures are invalid inputs, not imputations. The three additional tables are outside this contracted null denominator.

Optional fields often encode applicability, not damage: complaint origin links are null in **67,095/67,095** rows; event value in **14,826,484/15,620,994** events and event product in **14,180,656/15,620,994** events. Unknown optional facts remain unknown. Required missing/type-invalid facts block promotion; unavailable facts needed for authority are subject to the written policy's missing-field checks. We neither reproduce nor force the organizer's unspecified 5% target by imputation.

## Relationships: existence is different from ownership

The extended scanner checks **24 relationships**. Operational customer/product/agent/interaction existence checks still have zero orphans. Two previously untested branch references do not:

| Relationship | Non-null links | Orphans | Owner mismatches |
|---|---:|---:|---:|
| Customer registration branch → branches | 150,000 | 149,995 | — |
| Agent assigned branch → branches | 833 | 831 | — |
| Digital event product → products | 1,440,338 | 0 | 1,094,226 |
| Complaint affected product → products | 44,570 | 0 | 44,570 |
| Complaint origin interaction → interactions | 0 | 0 | — |

Trimming/lowercasing does not repair the branch gaps. Digital ownership mismatches count non-null customers only. An all-null origin link makes its zero-orphan result vacuous. Registration/assigned branch fields, digital product links, and complaint product links/text are excluded from serving projections; they must not authorize lookup, routing or disputes. Analytical app-error association uses only the customer link. No broken ID is guessed or repaired.

## Volumes: delivery differences, not pipeline loss

| Source | Documented approximation | Delivered / silver | Difference |
|---|---:|---:|---:|
| Transactions | 5,000,000 | 4,425,008 | −574,992 (−11.50%) |
| Digital events | 10,000,000 | 15,620,994 | +5,620,994 (+56.21%) |
| Campaign sends (audit-only) | 2,000,000 | 1,746,801 | −253,199 (−12.66%) |

Transactions and digital events each have **1,097 daily files and all 1,097 business dates**, 2023-06-17 through 2026-06-17. Direct raw counts equal the contracted silver counts; there are zero invalid rows and zero exact/payload/event replay fingerprints. Therefore our quarantine, deduplication or missing daily partitions do not explain these two deltas. Approximate generator targets, a changed export/generator revision, or upstream cleanup are plausible explanations; no upstream generator/history is available to establish which occurred. A claimed 2% duplicate fraction cannot explain either measured delta. Marketing sends have 1,083 files and are not used by the application.

## Reproduce without disclosure

With local `LOCAL_RAW_DIR` and timezone-aware `BANK_CLOCK` configured, run `LLM_PROVIDER=mock uv run --extra data-ml python analysis/reconcile_data_quality.py`. It hashes every input, verifies unchanged source stats, scans aggregates with bounded DuckDB memory, and writes only to ignored `artifacts/dq-reconciliation/` with private permissions. The normal quality code also emits every column's null numerator/row denominator. Tests use authored fixtures only. All temporal comparisons use UTC and the fixed clock `2026-06-18T06:00:00Z`; see the follow-up operational temporal guard for automation treatment.
