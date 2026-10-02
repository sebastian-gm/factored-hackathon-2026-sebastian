# Judge profile entry

One existing password/SMS-OTP login opens a metadata-only picker with MX · ES,
CO · ES, AR · ES and a Portuguese speaker. The header switches profiles later;
each selection, including the same profile, opens a fresh workspace. Story
shortcuts select the appropriate profile only when the server supplies a scoped
hint and prepare a generic draft without sending it. The Portuguese profile is
a conversation language, not a Brazilian bank or currency.

The server's `judge_profiles_enabled` identity flag gates this UI. Owner and
legacy single-alias sessions retain the existing interface. This PR does not
enable judge access, change infrastructure or secrets, or add another activation
flag. Submission-day activation and enabled Azure rehearsal remain lead-owned.
The contract is [judge-profile-entry.md](../../docs/api/judge-profile-entry.md)
and [ADR-0016](../../docs/adr/0016-judge-profile-sessions.md).

## Cookie and state boundary

- The BFF accepts only `profile_id`, enforces same-origin JSON writes, calls the
  selection POST once, and independently reads `/me` with the returned capability.
  It validates that identity before replacing the HttpOnly/Secure/SameSite=Strict
  access cookie. Its expiry remains the original login deadline. JavaScript gets
  only verified identity/expiry metadata; no token is logged, stored or broadcast.
- Before opening the picker or selecting, the client aborts pending requests,
  retires their generation and unmounts chat, lists, conversations, proposals,
  action OTP, receipts, Desk/Ops state, recording state and route preferences.
  Every response checks its generation, including reads already authorized by
  the server. No write is retried in another profile.
- BroadcastChannel carries random nonsecret transition notices. A storage-event
  fallback carries the same notice, never a profile or customer object. Other
  tabs stop and clear during a transition, then re-fetch identity and profile
  metadata after it completes. Browser restoration/back and visibility changes
  also clear/revalidate judge state. History contains paths, not profile data.
- A delayed old-token 401 does not clear the shared cookie: it could otherwise
  delete a newly rotated cookie. The client clears stale state, and the server
  rejects the old token. Explicit login/logout and failed activation change the
  cookie. A failed/lost/unverified switch requires login, without replaying the
  selection. Logout must finish its server revocation/readback before claiming
  success; failure does not leave the view indefinitely loading.
- Judge reset controls are absent and reset requests remain denied. Selecting
  again is a workspace restart, not renewed OTP freshness, an extended session
  or additional model budget. Authority remains in the existing API.

## Verification and screenshots

Authored fixtures implement the UI contract only, behind the test-only
`FRONTEND_FIXTURE_JUDGE_ACCESS=true` flag. They contain no organizer records,
held-out suite content or real credentials. Live-mode browser tests still use
the local authored mock bank; neither test path calls a model.

The ignored local gallery is `artifacts/ux-audit/judge-profile-picker/index.html`.
It includes ES/PT picker and active-chat views at 1440px and 390px. Images and
gallery are mode 0600 in a mode-0700 directory; credential/OTP fields are masked.
`FRONTEND_PROFILE_CAPTURE=1 pnpm test:e2e judge-profiles.spec.ts` reproduces them.
No images or browser traces are committed or uploaded by CI.

- Completed (verified): source-contract review, production build, typecheck,
  lint, aggregate-source check; 137 fixture browser tests (19 picker cases),
  12 local mock-API customer tests and one staff test. ES/PT desktop and phone
  screenshots passed all-rule axe with zero violations. Model spend was $0.
- Done but not verified: Azure activation/rehearsal. Remote CI is required on
  the PR before merge; the PR check status is the remote verification receipt.
- Next / blocked: lead review/release and enabled judge rehearsal before
  submission-day activation. Changes are confined to apps/web and follow the
  minimalist design PR #104; official frozen v4 results remain unchanged.
