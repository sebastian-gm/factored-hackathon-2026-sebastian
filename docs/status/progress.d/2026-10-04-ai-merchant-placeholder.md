# AI missing-merchant normalization and starter replays

## Completed (verified)

- Read-only owner-tour execution audits found ES normalizing the missing display
  placeholder as merchant evidence; PT omitted it and reached a required
  BRD-01 handoff for `missing:merchant_name`. Approved ES aggregate reconstruction
  additionally found display/process-date mismatch. No app/model calls or row,
  value, transcript, credential or identifier exports; historical dataset equality
  is unavailable and current-snapshot findings are labeled accordingly.
- Normalize only blank/em-dash merchant displays as absent in NormalizedSlots.
  Preserve the complete ExtractedNlu, genuine merchant strings, date slots,
  confidence, thresholds, risk signals, policy and existing API guards.
- **32 new ES/PT regressions and 310 existing controls passed**, one explicit
  disposable-Postgres skip. Ruff and strict mypy on all 80 source files pass.
  Replays use recorded normalized enums/flags and authored reconstructed values;
  raw model JSON and confidence were not retained.
- Fresh-conversation complete-purchase starters reach an explanation/dispute
  offer in mocks; textual assent/stale hashes cannot file. Missing bank merchant
  data still hand off with verified BRD-01 receipt; conflicting process date
  still clarifies. Independent safety and low-confidence controls pass.
- A concrete owned-charge frontend proposal remains ignored for w8 to apply:
  TypeScript, ESLint and 46 offline checks pass; six browser regressions unrun.
  No tracked frontend files or profile bindings changed. Zero model spend.
- Remote CI reproduced a language bug independent of merchant normalization:
  random case ID `DSP-E9B0CA7A` supplied Portuguese `e`/`a` fragments and blocked
  an explicit ES status switch. Whole-word tokenization excludes alphanumeric
  references without changing language confidence or routing thresholds.
  Nine new evidence cases and four additional deterministic ES/PT B1/P receipt
  cases cover it. All 96 targeted language/starter regressions pass; the existing
  conflict/uncertainty, verified case, no-extra-write and no-model-call checks remain.

## Done but not verified

- Updated remote CI is pending. No live rerun or deployed verification of this fix.
- Placeholder normalization alone does not fix the opener's incomplete target;
  the frontend must draft from a complete owned purchase without an added date.

## Next / blocked

- Keep this feature held for lead review and release merge order. No main or
  integration/v0.9.3-judge-stories push; the lead owns the active release.
- Preserve the partial 5/9 live score and retained unknown reservation. No paid retry.
