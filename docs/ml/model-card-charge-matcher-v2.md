# Charge matcher v2: offer choices when uncertain

> **superseded by v4 (2026-10-01)** — Historical evaluation/release status below; use the [current summary](../../README.md) and [official v4 results](../evaluation/final-v4-results.md). [Post-v4 fixes](../history/evaluation/post-v4-release-notes.md) are **not reflected in v4 numbers**.

**Integration status:** matcher v2 was active in the [official v4 run](../evaluation/final-v4-results.md).
The earlier v1-default/integration instruction is superseded. V2 is a retrained
LightGBM artifact with a versioned decision policy; it does not grant identity,
policy or write authority. The matcher diagnostics below remain historical
component evidence, separate from v4 conversation results.
Customers must confirm a transaction before any action, and must be able to
reject all offered choices. Keep the v1 artifact for comparison and rollback.

## Training and freeze

The [pre-training protocol](matcher-v2-protocol.md) fixed the noise families,
costs and selection grids before fitting. V2 uses 18,000 train queries and 9,000
validation queries from the original customer/time splits: each original query
plus two seeded variants. Validation remains customer-disjoint across tune
(3,078), calibration (2,985) and policy (2,937). Twenty Optuna trials select ranking
parameters on tune; query heads use tune, isotonic calibration uses calibration,
and thresholds use policy only. The model family remains LightGBM.

Variants combine missing dates with approximate amounts (`cerca de`, `casi`,
`como`), thousands separators, `k` suffixes, typos, merchant-type hints and urgency.
They are template-generated extraction surrogates passed through the unchanged
NLU postprocessor, **not measurements of real-model NLU**. The existing abbreviated
amount parsing defect is represented rather than silently repaired. Urgency
adds no matching or action authority. Training mirrors `MatchState`: candidate
category/channel/country are absent, raw type phrases remain raw, and FX defaults
to an empty book. Feature order and interfaces stay unchanged.

The artifact and thresholds were frozen at **2026-09-27 05:03:59 UTC**, before
opening the reused synthetic test or the human after-check. Training source commit:
`cffbe068bf6521598fea6215f707310fe428ea87`; exact code, NLU postprocessor, protocol,
source split and model hashes are in [metadata](../../models/charge_matcher/v2/metadata.json).
All nine human customers were verified absent from v2 train/validation. Human
utterances, predictions and labels were never fitting inputs. No post-check tuning
or frozen held-out scenario-suite access occurred.

## Decisions and cost preferences

V2 returns no-match for an empty set or when **every pointwise score is below
0.02**. Otherwise it proposes only when calibrated top-correct and match-exists
probabilities are both at least **0.90**; all remaining cases get up to three
ranked choices. Low calibrated match-exists probability alone cannot cause a
dead end. The 0.02 floor and 0.90 proposal threshold were selected on validation.
V1 artifacts retain their original policy through explicit version dispatch.

| Outcome | V1 cost | V2 cost |
|---|---:|---:|
| Wrong proposal | 10 | 10 |
| Choice containing the target, or choice on a true no-match | 1 | 1 |
| Choice missing a known target | 4 | 4 |
| False no-match | 3 | **6** |
| Correct proposal or true no-match | 0 | 0 |

These are product preferences in relative interaction units, not measured money.
A selectable list costs one interaction; a false no-match blocks progress and
costs more than an unhelpful list. A wrong proposal remains the largest cost.
Both models below are scored using the **v2 cost table** for comparability.

## Reused synthetic test diagnostics

These are previously used matcher-test customers, not a new blind acceptance
test and not `evals/suites/test/`. Both models receive identical serving-compatible
features. The original 3,000 queries contain 2,550 targets and 450 no-matches;
the 6,000 new variants contain 5,100 targets and 900 no-matches.

| Workload | Model | Top-1 | Recall@3 | Cost/query | Wrong / all proposals | Propose / choose / no-match |
|---|---|---:|---:|---:|---:|---|
| Original 3,000 | v1 | 94.75% | 99.84% | 1.2950 | 30 / 1,863 | 1,863 / 189 / 948 |
| Original 3,000 | v2 | 96.43% | 99.96% | 0.8133 | 13 / 1,819 | 1,819 / 531 / 650 |
| Sparse-language 6,000 | v1 | 60.29% | 76.00% | 4.9242 | 0 / 0 (undefined rate) | 0 / 211 / 5,789 |
| Sparse-language 6,000 | v2 | 97.67% | 99.98% | 0.2942 | 81 / 4,385 | 4,385 / 946 / 669 |

False no-matches fell from **566 to 296** on original queries and **4,889 to 1**
on new variants. Sparse-language gains come with **81 wrong proposals**, versus
v1's zero proposals: increased coverage introduces proposal risk. Top-1/recall
denominators include only known targets. [Metrics](../../models/charge_matcher/v2/metrics.json)
include calibration, slices and 300 customer-clustered bootstrap resamples.
V2 mean-cost 95% intervals are [0.7531, 0.8823] and [0.2610, 0.3295], respectively.
V1's historical card used a different feature projection and cost table; its
published numbers remain preserved and should not be substituted into this comparison.

## Human spot-check (n=9, es-CL): one after-check

Original human wording and intentional typos were unchanged. Gold was the
pre-existing annotation plus its documented separator erratum from the first
spot-check; no new labels were written after seeing v2. One fresh Gemini 3 Flash
Preview NLU run fed **both models the same slots** to control NLU variation.

| Measure | Recorded v1 before | V1 on fresh slots | V2 on fresh slots |
|---|---:|---:|---:|
| Target ranked first | 6/9 | 6/9 | **9/9** |
| Target in top three | 8/9 | 8/9 | **9/9** |
| Propose / choose / no-match | 0 / 0 / 9 | 0 / 0 / 9 | **6 / 2 / 1** |
| Wrong / all proposals | 0/0 (undefined) | 0/0 (undefined) | **0/6** |

Both choices contained the target (**2/2**). The remaining no-match had all
ranking scores below the preselected floor despite ranking the target first;
it remains a failure to surface an available transaction. We did not tune it away.
All nine model calls succeeded, with no retry/fallback, for **US$0.009762** against
the approved US$0.50. NLU intent accuracy remained 5/9; core-slot exact accuracy
changed from 7/9 to 6/9 with fresh model output. Matching improvement does not
establish an NLU fix. Pricing was verified using the
[OpenRouter catalog](https://openrouter.ai/api/v1/models) before this run.

## Limits and reproduction

- One author and nine synthetic-card recollections in an out-of-distribution
  dialect cannot establish language fairness, production accuracy or safety.
  There are no absent-target human cases. Zero wrong proposals out of six is
  insufficient evidence of a low population error rate. This tests NLU → MATCH,
  not full conversations, authentication, policy, writes or Postgres RLS.
- Synthetic targets are close to the as-of clock, making recency predictive.
  Positive variants start from target fields while negatives reuse the original
  donor/fabricated slots; missingness can therefore correlate with labels.
  Template extraction, this asymmetry and sparse candidate sets can inflate
  synthetic gains. Further independent language and no-match coverage is needed.
- Run `uv run --extra data-ml python -m aclara.ml.charge_matcher.train_v2 --trials 20`
  with the original private v1 dataset present under `artifacts/charge_matcher/v1/dataset/`.
  Its hashes must match v1 metadata. Reproduction requires those pinned local
  splits; regenerate them with the original seeded `build_dataset` from local
  gold if missing. The entry point refuses to overwrite an existing v2 run.
- Local-only evidence: `artifacts/charge_matcher/v2/` contains expressions,
  queries, trial records, model freeze and paired synthetic predictions;
  `artifacts/human-validation/spanish-40/spotcheck-es-cl-v2/` contains the detailed
  before/after report, billing and input/output manifests. No card values,
  utterances, credentials or row-level predictions are committed.

V4 integrated the v2 artifact **and** its version-dispatch code.
`MatchState(artifact=Path("models/charge_matcher/v2"))` loads it through the
existing checksum boundary; v1 remains available for explicit comparison/rollback.
The lead owns serving configuration and verification of scoped choices and
confirmation in each later release. Component diagnostics are not rescored v4 outcomes.
