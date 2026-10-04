# Judge gallery detail corrections — 2026-10-03

## Completed (verified)

- Quick-start shows only available stories for the active trusted judge profile
  or live persona. Language suffixes and the vague unavailable caption are gone.
- Case receipt verification groups its icon and label inline. Transaction cards
  omit the empty product row; messages omit the duplicate step label.
- Eleven quick-start/phone/guide browser checks and four ES/PT desktop/phone
  healthy → degraded → healthy checks passed. The latter use nonfixture config,
  explicit false/true/absent flags, receipt geometry, axe and overflow assertions.
- Web typecheck and lint passed. BFF profile selection validation is untouched.

## Done but not verified

- Added local-only scoped reset and independent read-back before the first-time
  receipt journey; existing-case replies now fail rather than become captures.
  Real mock-stack reset, refreshed gallery and final build remain to verify.
- Remote CI unavailable: owner reported exhausted GitHub Actions budget. No
  repeated push, budget increase or repository visibility change is authorized.

## Next / blocked

- Regenerate affected ES/PT desktop/phone captures on the local mock stack.
- Keep one small stacked PR open under the merge hold. Batch final changes in one
  push, then wait for restored CI and an explicit lift of the hold before merging.
- Live owner/GitHub tours remain pending the user's access-open message and the
  lead's durable private budget adapter. No paid calls or cloud changes made.
