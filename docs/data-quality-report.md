# Data quality report

Generated from local P1 pipeline aggregates. No source rows are included.

- Dataset version: `849b8a1ff207346a7dbf078b3a44dec9cd65b11fcfb3eb1f7d28fc3884c26ed4`
- Source objects: 1099 across customers, products, and transactions.
- Processing: UTF-8 BOM-aware CSV → immutable local bronze → typed Parquet silver → DuckDB DQ aggregates.
- Contracts: Pandera Polars schema validation on up to 2,000 rows per promoted table; full-table DQ counts use DuckDB SQL.

## Comparison with §4 expectations

| Metric | Pipeline output | Brief expectation | Result |
|---|---:|---:|---|
| `customers.rows` | 150000 | 150000 | match |
| `customers.files` | 1 | 1 | match |
| `customers.source_header_variant_count` | 1 | 1 | match |
| `customers.source_unknown_column_count` | 0 | 0 | match |
| `products.rows` | 400000 | 400000 | match |
| `products.files` | 1 | 1 | match |
| `products.source_header_variant_count` | 1 | 1 | match |
| `products.source_unknown_column_count` | 0 | 0 | match |
| `products.duplicate_product_numbers` | 6 | 6 | match |
| `transactions.rows` | 4425008 | 4425008 | match |
| `transactions.files` | 1097 | 1097 | match |
| `transactions.source_header_variant_count` | 1 | 1 | match |
| `transactions.source_unknown_column_count` | 0 | 0 | match |
| `customers.duplicate_primary_keys` | 0 | 0 | match |
| `products.duplicate_primary_keys` | 0 | 0 | match |
| `transactions.duplicate_primary_keys` | 0 | 0 | match |
| `transactions.orphan_customer_rows` | 0 | 0 | match |
| `transactions.orphan_product_rows` | 0 | 0 | match |
| `transactions.product_owner_mismatch_rows` | 0 | 0 | match |
| `transactions.fraud_score_gt_30_rows` | 2373 | 2373 | match |
| `transactions.fraud_score_gt_30_not_labeled_fraud` | 0 | 0 | match |
| `transactions.mxn_rows` | 0 | 0 | match |
| `transactions.active_product_share` | 1.0 | 1.0 | match |
| `transactions.process_date_minus_6h_match_share` | 0.999988474597108 | 0.999988 | match |
| `transactions.process_date_minus_6h_match_share_by_customer_country.AR` | 0.9999886364282021 | 0.999988 | match |
| `transactions.process_date_minus_6h_match_share_by_customer_country.CO` | 0.9999879569944271 | 0.999988 | match |
| `transactions.process_date_minus_6h_match_share_by_customer_country.MX` | 0.9999887206053335 | 0.999988 | match |
| `transactions.before_product_opening_rows` | 827610 | 827610 | match |
| `customers.last_updated_after_source_end` | 9316 | 9316 | match |
| `customers.last_updated_max_date` | 2027-06-15 | 2027-06-15 | match |
| `products.last_updated_after_source_end` | 25113 | 25113 | match |
| `products.last_updated_max_date` | 2027-06-15 | 2027-06-15 | match |
| `transactions.rows_last_120_days` | 492414 | 494755 | DIFFERS |
| `transactions.rows_last_365_days` | 1481222 | 1483415 | DIFFERS |
| `transactions.atm_purchases_rows` | 325993 | 325993 | match |
| `transactions.pos_deposits_rows` | 213678 | 213678 | match |
| `transactions.fraud_rows` | 4316 | 4316 | match |
| `transactions.latest_transaction_utc` | 2026-06-18 05:59:41+00 | 2026-06-18 05:59:41+00 | match |
| `transactions.business_date_range` | ['2023-06-17', '2026-06-17'] | ['2023-06-17', '2026-06-17'] | match |
| `transactions.candidate_counts_last_120_days.median` | 3.0 | 3.0 | match |
| `transactions.candidate_counts_last_120_days.p90` | 7.0 | 8.0 | DIFFERS |
| `transactions.candidate_counts_last_120_days.max` | 28 | 28 | match |
| `transactions.candidate_counts_last_120_days.customers_with_none` | 26561 | 26475 | DIFFERS |
| `transactions.candidate_counts_all.median` | 27.0 | 29.0 | DIFFERS |
| `transactions.candidate_counts_all.p90` | 57.0 | 59.0 | DIFFERS |
| `transactions.candidate_counts_all.max` | 150 | 150 | match |
| `transactions.candidate_counts_all.customers_with_none` | 15485 | 15485 | match |
| `transactions.pending_rows_over_14_days_last_120_days` | 8744 | 8741 | DIFFERS |
| `transactions.pending_rows_last_120_days` | 9923 | 9963 | DIFFERS |
| `transactions.merchant_name_distinct_purchases` | 24 | 24 | match |
| `transactions.source_country_counts.Mexico` | 40515 | 40515 | match |
| `transactions.raw_mexico_label_rows_for_mx_customers` | 18412 | 18412 | match |
| `transactions.fraud_null_score_rows` | 891 | 891 | match |
| `transactions.fraud_score_27_to_30_rows` | 353682 | 353682 | match |
| `transactions.fraud_score_27_to_30_fraud_rows` | 111 | 111 | match |
| `transactions.fraud_score_gt_30_share_of_scored_fraud` | 0.6928467153284672 | 0.69 | match |
| `transactions.fraud_score_gt_30_share_of_all_fraud` | 0.5498146431881371 | 0.55 | match |
| `transactions.has_settlement_expiry_reversal_timestamps` | False | False | match |
| `customers.country_share.MX` | 0.49938 | 0.499 | match |
| `customers.country_share.CO` | 0.30167333333333335 | 0.302 | match |
| `customers.country_share.AR` | 0.19894666666666666 | 0.199 | match |
| `customers.segment_share.Basic` | 0.5983733333333333 | 0.6 | match |
| `customers.segment_share.Plus` | 0.25031333333333333 | 0.25 | match |
| `customers.segment_share.Premium` | 0.10138 | 0.1 | match |
| `customers.segment_share.Student` | 0.049933333333333337 | 0.05 | match |
| `customers.status_share.Active` | 0.8513333333333334 | 0.85 | match |
| `customers.status_share.Inactive` | 0.09942666666666666 | 0.1 | match |
| `customers.status_share.Suspended` | 0.02938 | 0.03 | match |
| `customers.status_share.Closed` | 0.01986 | 0.02 | match |
| `customers.detected_accent_null_share` | 0.29878 | 0.3 | match |
| `customers.credit_score_null_share` | 0.14994666666666667 | 0.15 | match |
| `customers.credit_score_range` | [422, 850] | [422, 850] | match |
| `customers.mexican_document_type_dni_share` | 1.0 | 1.0 | match |
| `products.status_share.Active` | 0.8499125 | 0.85 | match |
| `products.status_share.Blocked` | 0.0498375 | 0.05 | match |
| `products.status_share.Closed` | 0.0800975 | 0.08 | match |
| `products.status_share.Suspended` | 0.0201525 | 0.02 | match |
| `transactions.status_share.Approved` | 0.9199262464610234 | 0.92 | match |
| `transactions.status_share.Declined` | 0.049996293792011225 | 0.05 | match |
| `transactions.status_share.Pending` | 0.019964483680029507 | 0.02 | match |
| `transactions.status_share.Reversed` | 0.010112976066935925 | 0.01 | match |
| `transactions.type_share.Purchase` | 0.2448370714810007 | 0.24 | match |
| `transactions.type_share.Withdrawal` | 0.21800480360713473 | 0.22 | match |
| `transactions.type_share.Transfer` | 0.20258449250261243 | 0.2 | match |
| `transactions.type_share.Payment` | 0.16699721220842992 | 0.17 | match |
| `transactions.type_share.Deposit` | 0.1377192990385554 | 0.14 | match |
| `transactions.type_share.Adjustment` | 0.029857121162266825 | 0.03 | match |
| `transactions.merchant_name_null_share` | 0.7674051662731457 | 0.77 | match |
| `transactions.transaction_category_null_share` | 0.6087039842639832 | 0.61 | match |
| `transactions.amount_usd_quantiles_disputable.p50` | 319.47 | 320.0 | match |
| `transactions.amount_usd_quantiles_disputable.p75` | 471.72 | 472.0 | match |
| `transactions.amount_usd_quantiles_disputable.p90` | 1263.8030000000003 | 1265.0 | match |
| `transactions.amount_usd_quantiles_disputable.p95` | 1633.44 | 1633.0 | match |
| `transactions.amount_usd_quantiles_disputable.p99` | 1927.7633000000008 | 1927.0 | match |
| `transactions.purchase_amount_usd_max` | 500.0 | 500.0 | match |
| `transactions.withdrawal_amount_usd_max` | 500.0 | 500.0 | match |
| `transactions.payment_amount_usd_median` | 1025.95 | 1026.0 | match |

## DQ highlights

- Source header variants: customers=1, products=1, transactions=1; unknown source columns: customers=0, products=0, transactions=0.
- Customer country shares: `{"AR": 0.19894666666666666, "CO": 0.30167333333333335, "MX": 0.49938}`.
- Customer segments/status: `{"Basic": 0.5983733333333333, "Plus": 0.25031333333333333, "Premium": 0.10138, "Student": 0.049933333333333337}` / `{"Active": 0.8513333333333334, "Closed": 0.01986, "Inactive": 0.09942666666666666, "Suspended": 0.02938}`.
- Customer null shares: `detected_accent`=0.298780, `credit_score`=0.149947; credit-score range=[422, 850]; Mexican customers with document type DNI=1.000000.
- Optional customer postal-code null share: 0.100293.
- Product type shares after canonical normalization: `{"checking_account": 0.2499475, "credit_card": 0.250255, "debit_card": 0.099845, "insurance": 0.0051225, "investment": 0.0146475, "mortgage": 0.029775, "personal_loan": 0.0499, "savings_account": 0.3005075}`.
- Product status shares: `{"Active": 0.8499125, "Blocked": 0.0498375, "Closed": 0.0800975, "Suspended": 0.0201525}`; duplicate product numbers: 6.
- Transaction status shares: `{"Approved": 0.9199262464610234, "Declined": 0.049996293792011225, "Pending": 0.019964483680029507, "Reversed": 0.010112976066935925}`.
- Transaction type shares: `{"Adjustment": 0.029857121162266825, "Deposit": 0.1377192990385554, "Payment": 0.16699721220842992, "Purchase": 0.2448370714810007, "Transfer": 0.20258449250261243, "Withdrawal": 0.21800480360713473}`.
- Transaction country shares after ISO normalization: `{"AR": 0.19605862859456977, "BR": 0.00914619815376605, "CO": 0.2914125804970296, "ES": 0.009162017334205949, "MX": 0.48504070501115476, "US": 0.009179870409273837}`.
- Raw transaction-country label counts: `{"Argentina": 867561, "Brazil": 40472, "Colombia": 1289503, "Mexico": 40515, "M\u00e9xico": 2105794, "Spain": 40542, "USA": 40621}`; raw `Mexico` labels on normalized MX customers: 18412.
- Transactions with a normalized transaction country different from the linked customer's normalized country: 202800.
- Null shares: `amount_usd`=0.573435, `fraud_score`=0.200035; fraud rows=4316.
- Fraud-score detail: null-score fraud rows=891; score 27 < score ≤ 30 rows/fraud rows=353682/111; share of scored/all fraud above 30=0.692847/0.549815.
- Disputable transaction `amount_usd` quantiles (non-null Purchase/Withdrawal/Payment): `{"p50": 319.47, "p75": 471.72, "p90": 1263.8030000000003, "p95": 1633.44, "p99": 1927.7633000000008}`; Purchase/Withdrawal maxima=500.0/500.0; Payment median=1025.95.
- Product opening-date anomalies: 827610 transaction rows precede product opening.
- Latest transaction timestamp (UTC): `2026-06-18 05:59:41+00`; process-date range: `['2023-06-17', '2026-06-17']`.
- Transactions in the 120-day UTC window: 492414; in the 365-day UTC window: 1481222.
- ATM purchases: 325993; POS deposits: 213678.
- Pending transactions older than 14 days in the 120-day window: 8744 of 9923.
- Customers/products with `last_updated` after the final source business date (2026-06-17): 9316 / 25113.
- Customer/product latest update dates: 2027-06-15 / 2027-06-15.
- Candidate counts across the full ledger: `{"customers_with_none": 15485, "max": 150, "median": 27.0, "p90": 57.0}`.
- Candidate count over the half-open 120-day UTC window for all customers: `{"customers_with_none": 26561, "max": 28, "median": 3.0, "p90": 7.0}`.
- Settlement/expiry/reversal timestamp fields present in the transaction source: False.
- The 120-day window is `[2026-02-18 06:00:00 UTC, 2026-06-18 06:00:00 UTC)`; the 365-day window is `[2025-06-18 06:00:00 UTC, 2026-06-18 06:00:00 UTC)`. The DuckDB session timezone is pinned to UTC before parsing source timestamps.
- `complaints.affected_product_id` is outside the serving scope; any joins from that field remain prohibited.
- The currency gap against daily FX, contact-center findings, complaints, agents, survey/text findings, and source-regeneration comparison are outside this P1 table scope and remain unverified.

## Contract checks

| Table | Null count in required fields | Result |
|---|---:|---|
| `customers` | 0 | PASS |
| `products` | 0 | PASS |
| `transactions` | 0 | PASS |

## Deviations

- `transactions.rows_last_120_days` differs: pipeline=492414, expectation=494755.
- `transactions.rows_last_365_days` differs: pipeline=1481222, expectation=1483415.
- `transactions.candidate_counts_last_120_days.p90` differs: pipeline=7.0, expectation=8.0.
- `transactions.candidate_counts_last_120_days.customers_with_none` differs: pipeline=26561, expectation=26475.
- `transactions.candidate_counts_all.median` differs: pipeline=27.0, expectation=29.0.
- `transactions.candidate_counts_all.p90` differs: pipeline=57.0, expectation=59.0.
- `transactions.pending_rows_over_14_days_last_120_days` differs: pipeline=8744, expectation=8741.
- `transactions.pending_rows_last_120_days` differs: pipeline=9923, expectation=9963.
- Facts outside the three-table P1 input set are not inferred from this pipeline run.

## Reproduction

Run `LOCAL_RAW_DIR=<local-source> python -m aclara.data.cli build`. The version manifest and profile are written under ignored `lake/`; this report is generated from that profile.
