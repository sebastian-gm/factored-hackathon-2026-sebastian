# Frozen matcher result review

For the authorized v2 development iteration and human before/after results, see
the [v2 model card](../../ml/model-card-charge-matcher-v2.md). The v1 results below remain preserved.

The synthetic comparison reuses the one-time v1 predictions, without refitting or additional test inference. The separately reported human spot-check uses new, excluded customers and leaves the frozen benchmark unchanged.

## Selection and uncertainty

LightGBM was selected on validation before opening test. Test logistic regression has lower mean cost and better calibration, while LightGBM makes fewer wrong proposals. The held-out result does not change thresholds or the selected artifact. A future independent workload should revisit this trade-off.

Specifically, test expected cost per query was 0.3980 for logistic regression versus
0.4717 for LightGBM, while LightGBM made 10 wrong proposals versus logistic regression's
41 (4.1 times fewer, approximately 4×). These are counts at their separately calibrated
operating points, not a claim that their proposal rates are equal. The pre-registered rule
selects the simplest model within 0.02 of the best validation cost: LightGBM scored
0.1828 and logistic regression 0.2584, a 0.0756 gap. Logistic regression was therefore
outside the simplicity tolerance. Selecting it after seeing the test would use held-out
results for model selection; the frozen v1 selection remains LightGBM.

| Model | Cost difference vs rules | Customer-clustered 95% interval |
|---|---:|---|
| logistic | -0.2217 | [-0.27330867489318195, -0.16777418521920653] |
| lightgbm | -0.1480 | [-0.19208010109397175, -0.10385692018958553] |

The lower-is-better cost combines explicitly chosen synthetic error costs; this interval is not a guarantee of production safety.

## Slice review

| Model | Slice | Group | n | Top-1 | Cost |
|---|---|---|---:|---:|---:|
| lightgbm | by_country | AR | 612 | 0.9578 | 0.4379 |
| lightgbm | by_country | CO | 909 | 0.9513 | 0.4939 |
| lightgbm | by_country | MX | 1479 | 0.9503 | 0.4719 |
| lightgbm | by_segment | Basic | 1797 | 0.9540 | 0.4686 |
| lightgbm | by_segment | Plus | 729 | 0.9468 | 0.4540 |
| lightgbm | by_segment | Premium | 306 | 0.9621 | 0.5163 |
| lightgbm | by_segment | Student | 168 | 0.9371 | 0.5000 |
| logistic | by_country | AR | 612 | 0.9693 | 0.3284 |
| logistic | by_country | CO | 909 | 0.9718 | 0.4037 |
| logistic | by_country | MX | 1479 | 0.9647 | 0.4233 |
| logistic | by_segment | Basic | 1797 | 0.9691 | 0.4124 |
| logistic | by_segment | Plus | 729 | 0.9645 | 0.3731 |
| logistic | by_segment | Premium | 306 | 0.9697 | 0.3922 |
| logistic | by_segment | Student | 168 | 0.9650 | 0.3631 |
| rules | by_country | AR | 612 | 0.8541 | 0.6062 |
| rules | by_country | CO | 909 | 0.8656 | 0.6744 |
| rules | by_country | MX | 1479 | 0.8710 | 0.5916 |
| rules | by_segment | Basic | 1797 | 0.8641 | 0.5982 |
| rules | by_segment | Plus | 729 | 0.8694 | 0.5981 |
| rules | by_segment | Premium | 306 | 0.8788 | 0.6993 |
| rules | by_segment | Student | 168 | 0.8462 | 0.7976 |

These groups describe source customer attributes, not language performance. Candidate-set size, query family and source composition can differ by group; gaps are observational. Protected attributes never enter the feature vector.

## Known synthetic artifacts

As-of clocks are zero to ten days after the target business date. This makes recency predictive by construction and can overstate improvement on a real workload. Customers without a target transaction are not sampled, so the target-sampled candidate distribution is larger than the all-customer serving distribution. No-match donor/fabrication and held-out stress profiles can shift confidence; LightGBM’s NONE precision and ECE warrant particular caution.

## Human validation plan

Sebastian has 40 private Spanish cards from customers excluded from every synthetic benchmark split. Nine recollections have now been checked below; 31 remain blank. Independent human annotation review is pending. Portuguese recollections will be labeled model-generated and cross-checked by a second model vendor, after the relevant model access/cost approval. No Portuguese performance or human labeling agreement is claimed here.

## Human spot-check (n=9, es-CL)

On 2026-09-27 UTC, Sebastian's nine card-elicited recollections ran through
`google/gemini-3-flash-preview` NLU and the unchanged v1 LightGBM `MatchState`
at source commit `c8588f4fc39593ab60ab0bfe9eeaab6bb6309a84`. Original wording
and intentional typos were preserved. Author-declared Chilean Spanish is an
out-of-distribution dialect relative to MX/CO/AR; ledger country is not dialect.

| Measure | Observed result |
|---|---:|
| Valid structured NLU / calls; degraded fallbacks | 9/9; 0/9 |
| Granular intent correct | 5/9 |
| All core slots correct, after annotation erratum | 7/9 (frozen labels: 6/9) |
| Amount; currency; date interval; merchant hint correct | 8/9; 9/9; 8/9; 9/9 |
| Target ranked first; target in top three | 6/9; 8/9 |
| Propose; choose; no-match | 0/9; 0/9; 9/9 |
| Wrong proposals / proposals | 0/0 — undefined rate |
| OpenRouter-reported total cost | US$0.009933 / US$0.50 approved cap |

Four explicit disputes became charge inquiries. One abbreviated amount lost its
magnitude; one date described a separate legitimate purchase. Every match-exists
probability fell below the frozen 0.15 threshold: useful ranking did not become a
proposal or choice. This is a failure to surface the known targets, not evidence
of safe resolution. No thresholds, models or prompts were retuned.

Gold intent/slots were authored from the [brief's §5.2/§9](../../00-build-brief.md)
before inference, without `aclara.policy`. A post-run audit corrected one gold
serialization error (thousands comma read as decimal); immutable original labels,
predictions and a timestamped erratum preserve both scores. Core slots are amount,
currency, date bounds and merchant hint; other extracted slots appear in the
private report. No precise date was supplied, so null-date correctness does not
measure date interpretation.

The local pinned ledger supplied nine distinct customers, zero overlaps with any
v1 benchmark split, and owned-product candidates in each card's half-open 120-day
window. MATCH used its serving projection and default empty FX book. This checks
NLU → MATCH, including an offline retrieval diagnostic for the card-block request;
it does not test session authentication, Postgres RLS, policy, writes or full chat.
One author, nine synthetic-card prompts, single-annotator gold and no absent-target
cases cannot establish dialect fairness or production accuracy. Independent human
review remains pending.

Evidence is local-only under `artifacts/human-validation/spanish-40/spotcheck-es-cl-v1/`:
`per-case-report.md` contains every intent, slot, selected transaction and target;
`GOLD.sha256.json` and `MANIFEST.sha256.json` pin inputs, annotations, code and results.
All row-level evidence remains ignored. The [model card](../../ml/model-card-charge-matcher.md)
keeps this diagnostic separate from held-out metrics. Pricing was checked against
the [OpenRouter model catalog](https://openrouter.ai/api/v1/models) before the run;
the two-attempt-per-case estimate was US$0.084901, with only nine attempts needed.
