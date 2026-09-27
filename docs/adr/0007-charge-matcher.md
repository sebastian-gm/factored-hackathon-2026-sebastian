# ADR-0007: Compare simple rankers with calibrated query decisions

Status: experimental; selection follows the registered validation rule (2026-09-26).

Small authorized candidate sets make rules a strong baseline. Compare a fixed rules scorer,
scaled logistic regression and pointwise LightGBM on identical generated recollections.
Use two query-level logistic heads (top correct and match exists), isotonic calibration and
three decisions: propose, choose up to three, or no match. Ranking confidence never authorizes
an action; confirmation and policy remain outside this package.

SHA-256 customer groups are disjoint. Train targets end before January 2026; validation is
January-February; test begins March 1. Validation customer groups separately support tuning,
calibration and policy thresholds. Test-only noise families stress generalization. All windows
are relative to the query as-of clock. Fraud fields and noise-generation metadata are not
features. Use 30 seeded Optuna trials and a local MLflow file store; no external model calls.

Pre-test selection chooses the simplest model within 0.02 expected validation cost of the best.
A wrong proposal costs 10, an extra turn 1, a false no-match 3, and a top-three choice omitting
the target 4. Test is touched once per artifact version, including failed attempts. Report
candidate-size slices, calibration, risk-coverage, customer-clustered bootstrap intervals,
country/segment slices and a 20-error deterministic audit. A weak LightGBM comparison is
reported honestly and favors a simpler deployment recommendation without retuning on test.

Synthetic normalized recollections are not human language evidence. The human gold set,
independent labeling and PT review remain required before any language-quality or production
claim. Revisit model selection on a new independently collected workload, with a new version.
