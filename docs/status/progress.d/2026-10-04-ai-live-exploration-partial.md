# AI live judge exploration: partial

## Completed (verified)

- Verified deployed API/web SHA `0f0e12d` and fresh judge identity. No profile
  binding changed. Every application request reserved before dispatch; only
  independently read own-scope records settled costs.
- All 30 frozen stories classified: 19 bound, 11 unbound for missing fixtures.
  Nine completed stories scored **5/9** (same cohort mock **9/9**); JE-18 is partial
  and nine bound stories remain unrun. The full mock comparator remains **27/30**.
- 33 verified turns, 22 passing; 202 assertions, 177 passing. All 30 observed
  no-write checks and three independent case readbacks passed. Two distinct cases
  used separate confirmation controls.
- Verified own-call cost **$0.03126800**; one unknown reservation retains
  **$0.06303700**. Charged exposure **$0.09430500**, cap unchanged at **$0.30**.
  Production key/account balances were checked privately before and after both
  paid segments; shared deltas were not used to attribute lane cost.
- Operator role and BFF-projection defects have zero-model regressions in #179.
  Live JE-13's actual product context bug has an authorized API fix in #180.
  Final frozen mock remains 27/30 with all controls passing; final B1 v2 32/32.
- Read back own execution metadata for all four live failures: JE-13 combines
  a normalized-intent difference with lost pending intent (#180); JE-03/05 lose
  choice context without NLU (#185); JE-17 safely still requires a choice.
  Raw model JSON, per-turn confidence and slots are unavailable.
- Audited all 12 supplied owner-tour charge stories (14 execution records),
  separately from judge scoring/cost. PT explanation reaches MATCH then required
  BRD-01 for missing merchant. Approved ES aggregate reconstruction finds a
  missing-merchant placeholder plus display/process-date mismatch before MATCH.
  Input date parsing passed; current snapshot stayed stable, historical equality
  is unavailable. Zero app/model calls, no rows/transcripts/values exported.
- Concrete owned-charge starter proposal retained for w8: TypeScript/ESLint and
  46 offline checks pass; six browser regressions remain unrun. No tracked frontend
  edits or judge-binding changes; no claim of repaired live first-click behavior.
- Frontend overlong-message proposal retained as an ignored local patch for w8:
  20 mocked route checks and TypeScript passed; browser checks remain unrun.
- Read back the lead's #187 batch: #180/#185 and w8's starter/error fixes were
  included; this lane made no release merge. Earlier frontend proposals remain
  pinned to their author-time source. The new minimal date-omission proposal
  targets `63e69b6`; 64 actual-helper checks, TypeScript/ESLint/formatting pass.
- #189 adds missing-display normalization and excludes opaque alphanumeric
  reference fragments from language evidence. The CI-observed `DSP-E9B0CA7A`
  language defect reproduces deterministically. Ninety-six targeted tests and
  the feature branch's full mock Python suite pass; Ruff and strict mypy pass.
- Rechecked `63e69b6` plus #189 locally: **316** relevant regressions pass;
  frozen exploration **27/30**, B1 **32/32**. All 100 no-write, 109 zero-spend,
  14 case-readback and 7 handoff-readback checks pass. Same JE-08/16/28 workflow
  failures; thresholds and expectations unchanged. No paid calls.

## Done but not verified

- JE-18's second dispatched turn lacks verified cost; its maximum remains held.
- No live rerun of any product fix. The final approved continuation stopped in
  deployment preflight before any application/model call or reservation.

## Next / blocked

- Final approval was attempted once; both images were `f9d1796` rather than the
  approved `0f0e12d`. No requests ran. Keep all nine untouched stories unrun and
  honor the final-stop instruction: no paid retry.
- Preserve the partial score, fixture gaps and unresolved reservation.
- The lead reviews and owns all merges. #189 and this follow-up report remain
  held; no main merge or integration/v0.9.3-judge-stories push by this lane.
