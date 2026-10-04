# English reviewer interface activation

## Completed (verified)

- English is the default reviewer interface; ES/PT remain selectable.
- Interface choice is separate from the authenticated bank conversation locale.
  Request headers, card actions and prepared customer messages remain ES/PT.
- Activated complete English chrome and Insights catalogs. Added the exact bank
  language explanation in the chat header and corrected English page metadata.
- English Why shows rule IDs and English rule/reason labels, not repeated reply
  prose. Agent Desk derives English summary/questions/next steps from reason IDs.
- Approved disclosure: existing packet text is a generated API summary, not
  original customer words. Label it “API summary (original, ES/PT)”; preserve API
  free text and do not invent or translate customer statements.
- Ten English desktop/phone browser checks passed with axe, zero overflow and
  original ES/PT replies/drafts; 24 existing profile-story checks passed.
- Broader browser validation: 127 checks passed, then the two remaining PT
  test setup errors were corrected and all 26 admission/resilience checks passed.
- Six authored staff/Ops desktop/phone audits passed with axe and no overflow;
  deduplicating shared English guidance passed the seventh console regression.
- Legacy tests select the PT customer explicitly, preserve the language preference
  across reloads, and allow only that preference in browser storage. The app still
  works if preference storage is blocked. Phone profile controls wrap within a
  growing toolbar; staff sessions without a locale retain the chosen UI language.
- English tests cover 429, session expiry, basic mode only for degraded replies,
  and no action/message replay. TypeScript and ESLint passed.

## Done but not verified

- Remote activation CI and deployed v0.9.5 behavior pending at author time.
- Official v4 evaluation figures are unchanged.

## Next / blocked

- Catalog #194 merged; lead owns activation #195 merge and v0.9.5 release.
- Requested clean English video assets follow both merges, using authored local
  mock fixtures at 2x scale; capture remains pending, with no paid model calls.
- No API changes, cloud changes or paid model calls by this lane.
