# Problem analysis

The selected workflow is unrecognized-charge questions and dispute intake in Spanish and Brazilian Portuguese. This is a local prototype scope statement, not a measured operational result.

## P1 data evidence

The local pipeline ingests customers, products, and transactions only. It reads source files from `LOCAL_RAW_DIR`, writes immutable bronze copies and typed Parquet silver under ignored `lake/`, validates up to 2,000 promoted rows per table with Pandera, and computes full-table aggregates with DuckDB. It pins the DuckDB session timezone to UTC before parsing timestamps. No source rows are included in generated reports.

The pipeline comparison currently includes source object counts and header variants, primary key duplicates, customer profile shares and nulls, Mexican document-type mismatch, orphan and ownership checks, active product share, fraud score bands, transaction status/type/country shares, merchant and amount summaries, product opening-date anomalies using the UTC transaction date, customer/product freshness after the final source business date, 120/365-day transaction windows anchored at `BANK_CLOCK`, pending age counts, latest timestamp, process-date range, and 3-year/120-day candidate distributions. Every difference from the §4 expectation is emitted as `DIFFERS` in `docs/data-quality-report.md`.

Observed aggregate issues include a 10.0293% optional customer postal-code null share and eight remaining differences in 120/365-day row counts, candidate distributions, and pending counts. The pipeline uses half-open UTC timestamp windows anchored at `BANK_CLOCK`; §4 does not state the exact date boundary or percentile method, so computed differences remain visibly flagged. The fraud 27–30 band excludes score 27 to match the brief's stated 353,682-row band. The transaction `process_date` versus timestamp-minus-six-hours share matches the brief within tolerance. Full results are in the generated report. The pipeline normalizes transaction country labels to ISO codes before calculating cross-country counts.

Contact-center findings, complaints, agents, daily FX, survey/text findings, source-regeneration comparison, and other tables outside the three-table P1 input set remain unverified. No claim about those tables is inferred from this run.
