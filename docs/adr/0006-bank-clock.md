# ADR-0006: UTC event time and a simulated bank clock

Status: accepted for the local prototype (2026-09-26).

Interpret transaction timestamps as UTC, and `process_date` as the bank business date
(timestamp minus six hours). Normalize customer and transaction countries before comparing
them. Do not infer local time from the inconsistent country spelling.

Serving and complaint-history windows are half-open timestamp intervals ending at BANK_CLOCK;
rows at or after that clock are excluded. Candidate counts include every customer, including
zeros, with continuous quantiles. Matcher retrieval instead uses each query's own as-of
clock. FX uses the transaction's business date and the nearest prior rate, with a fallback flag.

This differs from inclusive calendar-date counts in some reference profiles. Recompute and
publish the pipeline definition rather than alter predicates to match the brief. Dimensions
are current snapshots, not valid historical SCD2 records: historical customer attributes
are unsuitable for causal analyses or historical eligibility claims.
