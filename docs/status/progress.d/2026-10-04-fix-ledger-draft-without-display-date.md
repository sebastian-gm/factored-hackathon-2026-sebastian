# Date-free charge explanation drafts

## Completed (verified)

- Reviewed and applied the AI lane's five-line frontend proposal
  `ledger-draft-no-display-date-frontend-proposed.patch`, SHA-256
  `54e81d09a7c3f763f7ee9351b1a84d897b7fbdedb2b439a1bf8aa7802cb82bb4`.
  The AI lane reported that the displayed transaction date differs from the
  process date used in matching. ES/PT explanation drafts now use the scoped
  merchant, exact amount and currency without adding a displayed-date filter.
- Preserved complete-charge/pending preference, missing/redacted merchant
  rejection, editable drafts, stale-profile protection and generic fallbacks.
  Updated the README judge guide and relevant browser expectations.
- Added ES/PT date-variance regressions: changing only the displayed date leaves
  the drafted explanation question unchanged.
- `FRONTEND_E2E_WEB_PORT=3217 FRONTEND_E2E_API_PORT=8217 pnpm test:e2e
  current-profile-stories.spec.ts judge-ux.spec.ts video-readiness.spec.ts
  judge-guide.spec.ts`: 69 passed, including MX/CO/AR/PT desktop/phone drafts,
  merchant placeholders, no auto-send and stale-profile responses.
- `FRONTEND_E2E_WEB_PORT=3217 FRONTEND_E2E_API_PORT=8217 pnpm test:e2e --live
  --grep 'recording helper'`: 2 passed against the local real BFF and authored
  fixture API with the mock provider. ESLint and TypeScript checks passed.

## Done but not verified

- Remote CI and deployed healthy-model behavior are pending at author time.
- This post-v4 frontend change does not alter the official v4 evaluation numbers.

## Next / blocked

- Open a small PR against main; lead owns review, merge and release. The release
  hold remains in force. No push to the v0.9.3 integration branch.
- No live Azure app/model calls or additional spending in this change.
