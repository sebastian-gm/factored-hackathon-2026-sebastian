# Matcher v2 development protocol

Frozen before fitting or examining any new synthetic test/human predictions.
This is an authorized development iteration, not a new blind acceptance result.
Never read or execute `evals/suites/test/` for this work.

- Reuse the pinned v1 matcher train/validation customer groups and time windows.
  Retain each original query and add two seeded, template-authored variants.
  Variants omit dates and mix approximate amounts (`cerca de`, `casi`, `como`),
  comma thousands grouping, `k` suffixes, typos, merchant-type hints and urgency.
  No human recollection, human prediction or human gold is a training input.
- Literal expressions go through the existing deterministic NLU postprocessor.
  These are synthetic extraction surrogates, not real-model NLU measurements.
  They deliberately retain current normalization failures. Urgency is contextual
  text only; it never supplies matching, policy or authorization authority.
- Match serving inputs: remove candidate category/channel/country, retain raw
  type expressions, and use the default empty FX book. Source customer country
  only supplies the existing NLU normalization context. No feature contract change.
- Retrain LightGBM with 20 seeded Optuna trials using train and validation-tune
  only. Fit query-level heads on tune, isotonic calibration on calibration, and
  decision thresholds on policy, keeping all variants of a customer together.
  Keep the v1 model family fixed; no test-dependent deployment recommendation.
- V2 policy: empty candidates → no-match; all pointwise scores strictly below
  the selected very-low floor → no-match; confident top candidate → propose;
  otherwise → choose up to three authorized candidates. Low calibrated existence
  alone cannot discard a nonempty candidate set. Proposal thresholds search
  `{0.90, 0.95, 0.98, 1.01}` with existence ≥0.90; raw-score floors search
  `{0, 0.001, 0.005, 0.01, 0.02}`. A zero floor disables nonempty no-match.
- Minimize policy-validation expected cost, then wrong proposals, then false
  no-matches, then prefer the smaller no-match floor and higher proposal threshold.
  Costs: wrong proposal 10, extra choice 1, false no-match 6 (v1: 3), a choice
  missing the known target 4, correct proposal/true no-match 0. These are explicit
  product preferences: a selectable list is recoverable; a false dead end costs
  more. They are not financial losses or costs fitted to the nine human cases.
- Write the selected model, thresholds, source hashes and freeze manifest before
  opening the reused synthetic matcher test. Evaluate v1/v2 on the same serving
  projection of the original 3,000 cases and its 6,000 added variants, using the
  v2 cost table for both. Label these reused synthetic tests as development
  diagnostics. Preserve v1 bytes and its historic metrics.
- After the artifact freeze, run the nine human messages once through the approved
  default Gemini NLU, then score both frozen matchers on the same new slots. Also
  compare the recorded v1 baseline; fresh NLU variation is a confounder. Preserve
  pre-existing gold plus its documented separator erratum. Do not tune after this
  check. Keep every row-level artifact private and publish only aggregates.

The lead owns application integration: select `models/charge_matcher/v2`, keep
confirmation before any action, and retain a way to reject all displayed choices.
**Integrate v2 before the final evaluation run.**
