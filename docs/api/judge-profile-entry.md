# Judge account and profile API — prepared, Azure OFF

This post-v4 feature is not reflected in official v4 results. Backend behavior
and the threat check are defined in [ADR-0016](../adr/0016-judge-profile-sessions.md).
No Azure switch, password, Key Vault secret, ingress or replica setting is changed
by this API implementation. The frontend picker is separate work.

## Login and routes

The existing password plus simulated SMS OTP flow returns a picker-only bearer.
`GET /me` then has `judge_profiles_enabled=true`,
`profile_selection_required=true`, `judge_profile_id=null` (omitted when null),
and role `customer`. This bearer can read identity/profile metadata or sign out;
banking, chat, action OTP, Desk, Ops and reset return 403 until selection.

| Route | Input | Verified response / authority |
| --- | --- | --- |
| `GET /auth/judge/profiles` | Current judge bearer | `profiles`, `active_profile_id` (nullable), original `expires_at` |
| `POST /auth/judge/profile` | Current judge bearer; JSON with **only** `profile_id` | New `access_token`, `token_type=bearer`, `verified=true`, `identity`, original `expires_at` |
| `GET /me` | Current bearer | Ordinary identity fields plus judge flags/profile and gated `demo_stories` |
| `POST /auth/logout` | Current picker or profile bearer | `signed_out=true`, `verified=true`; entire controller revoked |

Profile objects have `profile_id`, `label`, `locale`, `language`, `demo_stories`.
Allowed IDs are `mx-es`, `co-es`, `ar-es`, `pt`; corresponding locales are
`es-MX`, `es-CO`, `es-AR`, `pt-BR`. `pt` describes the speaker, not the bank's
country. Story hints are inherited only when the reviewed source's serving data
already supports them; an empty hint list is valid. No source username, customer
ID or role supplied by the caller can select or widen the scope.

Invalid/extra selection fields return 422. Disabled/unconfigured picker routes
return 404; enabled routes without authentication return 401, owner bearers
return 403. Superseded, expired or configuration-invalid judge bearers return
401. A switch returns success only after independent child/controller readback;
failure can require signing in again. No plaintext bearer is persisted for retry.
The legacy Key Vault single-alias format remains supported without picker routes.
Changing that account to the profile format requires a new password/OTP login;
old single-alias capabilities cannot bypass the picker.
Ordinary owner `/me` responses retain their existing field shape.

## Frontend integration contract

1. Keep the API internal. BFF routes must enforce same-origin writes and retain
   the existing Secure/HttpOnly/SameSite cookie protections. Never expose bearer
   tokens to JavaScript, localStorage, logs or analytics.
2. After login OTP, inspect `/me`; show the picker when required. Fetch profile
   metadata without loading the anchored customer's transactions or Desk.
3. A selection POST runs once. The BFF consumes the returned capability, replaces
   the HttpOnly session cookie, and returns only identity/expiry/verified metadata
   to the browser. **Do not retry the POST**, including on timeout or cold start.
   A lost response can leave the old cookie revoked; request a new login.
4. Before selection, stop new customer requests, abort/discard in-flight reads and
   clear all customer lists, selected handles, conversation IDs, proposals,
   confirmations, OTP dialogs, receipts, Desk/Ops caches and route state. Tie all
   response application to the current frontend profile generation. A request
   authorized before switching may finish in its original customer scope; its
   response must never render in the new profile.
5. Coordinate tabs with a nonsecret generation notification (for example,
   BroadcastChannel). Other tabs clear state and re-fetch `/me`. Never broadcast
   the capability. The server rejects old tokens independently of this UX guard.
6. Switching even to the same profile creates a new operational workspace. Do not
   reuse an old conversation, transaction list, proposal or action OTP.
   Post-v4 audit fix: bank cases/card states persist within the same trusted
   customer + judge-profile realm across logins and visits. Returning to that
   profile can read its existing case; another profile or the owner realm cannot.
   Judge reset routes remain forbidden; selection restarts only the workspace.
7. Use `identity.locale` and `identity.demo_stories` for the active UI. Normal
   policy, proposal confirmation and action OTP freshness remain enforced;
   switching does not grant fresh write authority or extend the login deadline.
8. Sign-out clears browser state/cookie only after calling logout; expiry/revoked
   responses must also clear stale profile state. Never retry a write under a
   different profile after an authentication failure.

## Scope, persistence and budget

The original controller lives in an explicit auth scope, while each selected
capability has a new customer-specific run/session. Customer business tables
add a stable server-trusted realm and a unique open-case constraint; conversations,
handoffs, pending actions and receipts retain run/session isolation. Every access
uses the selected trusted customer and forced RLS. Cross-profile object IDs,
proposals and OTP challenges return not-found. A locked controller digest/revision
has exactly one winner across replicas; unpublished children have no authority.
Restart checks the persisted controller and credential/binding/dataset fingerprint.
Turning access OFF or changing those bindings invalidates existing sessions.

All calls still use the existing global durable `production` **$3 per UTC day**
breaker. Selection creates no model call, budget scope or run allowance. The
prepared Azure mode rejects any `LLM_BUDGET_RUN_ID` smoke override. Replenishment
is controlled by the UTC-day budget policy, never by login/profile/reset.

## Submission-day prerequisites

Owner approval still precedes activation; see
[infrastructure switches](../submission/infrastructure-switches.md). Supply four
reviewed, distinct customer bindings with the expected locales through the
existing `judge-persona` Key Vault secret. Generate a separate random
`judge-password`; never commit either value. The controller needs no new Azure
resource; the post-v4 bank-state fix needs migration 0004 before its image release.
Frontend cookie/tab handling and a live enabled
judge rehearsal must be verified before enabling public web ingress.
