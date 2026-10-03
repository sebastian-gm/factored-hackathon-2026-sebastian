# 2026-10-03 — Privacy-first money recovery (AI lane, #149)

## Completed (verified)

- Authored mock controls reproduced the lead's latest payload leaks and ambiguity behavior before the redesign. Expanded controls cover descriptive ES/PT phone/account/document cues, cues following the amount, cards, all five smoke currencies, dollar-prefixed grouped amounts and shared-unit lists.
- Removed all money exemptions from `redact_for_model`: original phone/document/card patterns always mask their matches. Punctuated national documents after descriptive text/currency markers receive additional masking. Outbound grounding/DLP stays unchanged.
- Moved raw-money inspection into NLU code. After the provider call, merge only one qualified money expression with no identifier cue anywhere in its clause. Competing amounts and identifier-bearing monetary clauses clear even a model-selected amount and request amount clarification. Separately delimited safe money clauses may recover locally. The original raw message is never substituted into a provider payload.
- All 213 money/privacy controls passed, including model-payload assertions for the lead's four new and two earlier leak cases, exact `1000000.00 COP` (plus CLP/ARS/MXN/BRL), `$1.250.000,00`, and unresolved `125 y 234 pesos`. Strict mypy and Ruff passed. Zero model spend; no held-out rows accessed or official numbers changed.

- Full local mock checks passed: 1,591 tests / 40 database-dependent skips; B1 passed 32/32. Interface snapshots and policy checks passed.

## Done but not verified

- Corrected-head remote CI and lead security replay remain pending; final verification will be recorded in #149.

## Next / blocked

- Push the privacy-first correction to #149 for the lead's security replay and v0.8.1 inclusion. Keep the PR unmerged under the active release hold.
