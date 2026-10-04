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
- English tests cover 429, session expiry, basic mode only for degraded replies,
  and no action/message replay. TypeScript and ESLint passed.

## Done but not verified

- Remote activation CI and deployed v0.9.5 behavior pending at author time.
- Official v4 evaluation figures are unchanged.

## Next / blocked

- Lead merges catalog #194 first, then this activation, and releases v0.9.5.
- No API changes, cloud changes or paid model calls by this lane.
