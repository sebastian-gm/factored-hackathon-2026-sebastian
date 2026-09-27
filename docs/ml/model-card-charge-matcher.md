# Charge matcher model card

This card preserves v1. The [v2 model card](model-card-charge-matcher-v2.md) records
the retrained choice-first policy, comparable diagnostics and human before/after check.

Version: `v1`. Dataset: `b86f445cb468332bde984a788ef24f72f7070952b2d9292e0259e7b8f36397c9`. Seed: 20260926.

Validation-selected model: **lightgbm**. Deployment recommendation after the one-time comparison: **lightgbm**.

## Intended use

Rank a verified customer’s already-authorized transaction candidates from normalized recollection slots. A proposal always requires customer confirmation. The matcher has no identity, policy or write authority. Currency conversion uses the candidate transaction’s business date. Missing FX is neutral evidence, never an invented conversion.

## Data and leakage controls

Organizer synthetic ledger; team-generated normalized recollections, with 15% no-match queries. No raw source rows are committed. This original benchmark measures neither real customer language nor NLU quality; the separate human spot-check below adds a small NLU diagnostic. Customer groups use SHA-256 buckets and are disjoint. Train targets are before 2026-01-01, validation targets in January–February 2026, and test targets from 2026-03-01. Each query has its own as-of clock and a half-open 120-day retrieval window. Overlay fixtures, fraud fields, generator parameters, target identity and complaint/transcript text are excluded from features.

Query counts: `{"test": 3000, "train": 6000, "validation": 3000}`. Unique customer counts: `{"test": 2723, "train": 5754, "validation": 2730}`.

Validation customers are split again into tuning, calibration and policy groups. Hyperparameters and the two query-level logistic heads use tuning only; isotonic calibrators use calibration only; decision thresholds use policy only. Test-only stress noise families are frozen in the dataset metadata. Test touches are append-only local records by version.

## Models and operating point

Fixed rules scorer, scaled pointwise logistic regression, and pointwise LightGBM use the same features and queries. Each has query-level match-exists and top-correct heads followed by isotonic calibration. Thresholds minimize validation cost: wrong proposal 10, extra turn 1, false no-match 3, choice missing the target 4. The simplest model within 0.02 expected cost of the best validation cost is selected before opening test.

| Model | Top-1 | MRR | Recall@3 | NONE precision | NONE recall | ECE | Cost/query | Wrong proposals / proposals |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| rules | 0.8659 | 0.9162 | 0.9624 | 0.6906 | 0.6844 | 0.0485 | 0.6197 | 29 / 1684 |
| logistic | 0.9678 | 0.9834 | 0.9996 | 0.8695 | 0.8289 | 0.0260 | 0.3980 | 41 / 1958 |
| lightgbm | 0.9522 | 0.9750 | 0.9988 | 0.5833 | 0.9489 | 0.0864 | 0.4717 | 10 / 1871 |

Top-1, MRR and Recall@3 use queries with a true match; NONE metrics use all queries. ECE uses ten equal-width bins for P(top-1 correct), including no-match negatives. Risk–coverage curves and customer-clustered 95% bootstrap intervals (300 resamples) are in `metrics.json`. No observed low error rate establishes production safety.

## Candidate-set sizes

| Model | Candidates | n | Top-1 | NONE recall | Cost/query |
|---|---|---:|---:|---:|---:|
| rules | 0 | 0 | undefined | undefined | undefined |
| rules | 1 | 131 | 1.0000 | 0.8571 | 0.3817 |
| rules | 2-3 | 635 | 0.9026 | 0.7582 | 0.5354 |
| rules | 4-8 | 1677 | 0.8685 | 0.6842 | 0.6064 |
| rules | 9+ | 557 | 0.7865 | 0.5476 | 0.8115 |
| logistic | 0 | 0 | undefined | undefined | undefined |
| logistic | 1 | 131 | 1.0000 | 0.8929 | 0.2977 |
| logistic | 2-3 | 635 | 0.9835 | 0.8352 | 0.3937 |
| logistic | 4-8 | 1677 | 0.9699 | 0.8583 | 0.3441 |
| logistic | 9+ | 557 | 0.9366 | 0.7143 | 0.5889 |
| lightgbm | 0 | 0 | undefined | undefined | undefined |
| lightgbm | 1 | 131 | 1.0000 | 0.9643 | 0.3282 |
| lightgbm | 2-3 | 635 | 0.9743 | 0.9451 | 0.4724 |
| lightgbm | 4-8 | 1677 | 0.9538 | 0.9636 | 0.4699 |
| lightgbm | 9+ | 557 | 0.9112 | 0.9048 | 0.5099 |

## Human spot-check (n=9, es-CL)

Nine unchanged, intentionally typo-bearing recollections from one human author
were checked on 2026-09-27 UTC using Gemini 3 Flash Preview NLU → frozen v1 MATCH.
Chilean Spanish is out of distribution relative to MX/CO/AR; all nine customers
are outside the original benchmark. Intent accuracy was **5/9**, corrected
core-slot exact accuracy **7/9**, top-1 **6/9**, and recall@3 **8/9**. MATCH returned
**9/9 no-match**, with **0 proposals and 0 choices**; wrong-proposal rate is undefined.
All nine model calls succeeded, costing **US$0.009933** in total.

Gold preceded inference; one post-run thousands-separator annotation erratum
changed core-slot scoring from 6/9 to 7/9, with original gold and predictions
preserved. The [result review](result-review.md#human-spot-check-n9-es-cl) records
methods, failure patterns and private evidence paths. One author, synthetic cards,
single-annotator labels and no absent-target cases do not establish language
fairness, production performance or complete agent safety. No tuning followed
this spot-check; independent human label review and 31 Spanish recollections remain
pending. No card values or per-case records are committed.

## Limits and review

- This is an offline synthetic comparison, not measured production improvement. Donor and fabricated no-match generation may introduce artifacts; deployment requires naturally written recollections.
- Broader human validation remains pending beyond the nine-recollection spot-check above; independent NLU double-labeling and agreement statistics are not yet available. Portuguese recollections will be labeled model-generated and cross-checked by a second model vendor after model access/cost approval. Normalized slots cannot establish language fairness. Country and segment results are in metrics; cells below 30 are marked insufficient.
- Category and channel features are defined but unexercised in this generated slot workload (no category/channel mentions); their value is not measured. Complete feature definitions include status and weak channel match. Demographics, protected attributes, fraud labels and fraud scores are excluded. Country/segment are used for evaluation only; an explicitly mentioned transaction country is a matching feature.
- There are no empty candidate sets in target-sampled benchmark queries; empty-set behavior is separately unit tested. Sparse large-candidate slices limit conclusions.
- Twenty failures per model are categorized by a deterministic audit. Private per-query records permit later human review; no human failure review is claimed.
- Synthetic FX and source records have documented anomalies. Policy and authorization must recheck the transaction before any action.

## Reproduction and tracking

`uv run --extra data-ml python -m aclara.ml.charge_matcher.train --version v1 --trials 30` (use a new version for a new test touch). MLflow uses the local ignored file store in `lake/mlruns`; Optuna uses a seeded TPE sampler. Export contains numeric model parameters, calibrators, thresholds, feature order, metadata, metrics and checksums only. No pickled code or row records.

Sources consulted: [dbt contracts](https://docs.getdbt.com/docs/mesh/govern/model-contracts), [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html), [LightGBM classifier](https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.LGBMClassifier.html), [Optuna study API](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.create_study.html).

The frozen [result review](result-review.md) gives paired cost intervals, country/segment slices, and the recency-prior limitation. Training ran from an uncommitted feature tree based on the recorded Git SHA; the exact training-source SHA-256 is stored in metadata and was verified after export.
