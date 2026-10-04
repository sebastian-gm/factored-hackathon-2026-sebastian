# Profile-bound judge quick-start drafts

## Completed (verified)

- Confirmed the live quick-start charge drafts were generic static text; they did
  not read the selected profile's ledger. Authored fixture story drafts remain
  available for the local demo.
- Live charge stories now fetch the active profile's scoped `/transactions`,
  skip purchases without a merchant, amount, currency or date, and prefer a
  complete pending purchase. The editable question includes the actual merchant,
  unrounded numeric amount, currency and ISO date. Preparing a story never sends
  a message or authorizes an action.
- Profile changes re-fetch the ledger. Aborted or retired workspace responses
  cannot replace the new profile's draft. Empty, unavailable or malformed ledgers
  show a localized notice and an editable generic question.
- PT judge quick-start is labeled “Entender cobrança”; desktop and phone browser
  regressions skip null/blank merchant names and prefer a complete pending charge
  over a newer approved charge. This change introduces no dispute story or
  frontend determination of dispute eligibility.
- `FRONTEND_E2E_WEB_PORT=3217 FRONTEND_E2E_API_PORT=8217 pnpm test:e2e
  current-profile-stories.spec.ts judge-ux.spec.ts video-readiness.spec.ts
  judge-guide.spec.ts`: 67 passed, including MX/CO/AR/PT desktop/phone coverage,
  fallback states, no auto-send, focus/viewport and late-profile-response checks.
- `FRONTEND_E2E_WEB_PORT=3217 FRONTEND_E2E_API_PORT=8217 pnpm test:e2e --live
  --grep 'recording helper'`: 2 passed against the local real BFF and authored
  fixture API with `llm_provider="mock"`. `pnpm lint` and `pnpm typecheck` passed.
- Recovered only execution/conversation metadata for this lane's own settled
  live calls. The AI-lane handoff has 12 charge-story ID sets, including four
  explanation attempts, in ignored
  `artifacts/ux-audit/go-live/operator/ai-lane-story-ids.private.json`; mode 0600
  and ignore status verified. No transcripts, credentials or row data in Git.

## Done but not verified

- Remote CI and this patch's deployed healthy-model behavior are pending at
  author time. The earlier ledger-specific tour failures still require AI-lane
  diagnosis; this frontend change alone does not establish their resolution.
- Post-v4 implementation change; official v4 evaluation numbers are unchanged.

## Next / blocked

- Open the small PR against main for existing CI; lead reviews it first and
  folds it into the v0.9.3 judge-stories integration. Merge remains held.
- No new Azure app/model calls or spending. Prior unknown-cost reservations and
  operator stops remain preserved; fresh live verification needs a released
  candidate and an authorized healthy budget scope.
