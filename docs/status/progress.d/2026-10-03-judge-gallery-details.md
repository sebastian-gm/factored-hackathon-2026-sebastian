# Judge gallery detail corrections — 2026-10-03

## Completed (verified)

- Quick-start shows only available stories for the active trusted judge profile
  or live persona. Language suffixes and the vague unavailable caption are gone.
- Case receipt verification groups its icon and label inline. Transaction cards
  omit the empty product row; messages omit the duplicate step label.
- Eleven quick-start/phone/guide browser checks and four ES/PT desktop/phone
  healthy → degraded → healthy checks passed. The latter use nonfixture config,
  explicit false/true/absent flags, receipt geometry, axe and overflow assertions.
- Broader local browser suite: 172 checks passed; seven outdated shortcut
  expectations were corrected and their focused rerun passed 7/7. Runnable
  shortcuts still lock during pending actions; unsupported stories stay hidden.
- Real mock-stack gallery refresh: 24 checks passed in the full sweep; four
  corrected retry assertions then passed. HTTP errors retain the previous reply,
  so its degraded notice stays until a healthy reply replaces it.
- Four first-time receipts followed independently verified scoped local reset,
  explicit recognition/denial/confirmation and matching case/transaction read-back.
  Rebuilt the private gallery: 219 PNGs; 104 screen audits, zero axe violations,
  overflow, application console errors or page errors. Desktop/phone receipt and
  PT phone transaction captures were visually inspected.
- Local integration production build, typecheck and lint passed. BFF profile
  selection validation is untouched. Measured after final evaluation; v4 unchanged.

## Done but not verified

- Remote CI unavailable: owner reported exhausted GitHub Actions budget. No
  repeated push, budget increase or repository visibility change is authorized.
- Healthy real-model replies on the deployed app remain to verify after judge
  access opens. The browser regression uses explicit healthy/degraded projections;
  no real model or live customer calls were made.

## Next / blocked

- Keep one small stacked PR open under the merge hold. Batch final changes in one
  push, then wait for restored CI and an explicit lift of the hold before merging.
- Live owner/GitHub tours remain pending the user's access-open message and the
  lead's durable private budget adapter. No paid calls or cloud changes made.
