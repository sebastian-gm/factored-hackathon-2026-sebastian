# ADR-0016: One judge login, separately scoped customer profiles

- Status: Accepted for implementation under the owner's 2026-10-01 GO; Azure OFF
- Date: 2026-10-01

## Context

Judges currently authenticate separately for four reviewed serving personas.
They need one password/OTP entry and a profile picker. Every bank read/write must
still have exactly one trusted customer under forced RLS. This is a post-v4 demo
change, not reflected in official v4 numbers. No held-out run or paid call is needed.

## Options

1. Change a live token's customer in place. Rejected: stale tabs, proposals and
   replay could share one credential across customer scopes.
2. Keep a durable judge controller and rotate a separately scoped capability on
   every selection. Chosen: reuse existing sessions, RLS and advisory transaction
   locks; no new table, resource or privilege.

## Decision

- Reuse `enable_judge_access=false`, `JUDGE_ACCESS_ENABLED=false` and the two
  prepared Key Vault secret references. Do not enable anything or create secrets.
- The new Key Vault definition has exactly `username` and `profiles`. The latter
  maps the fixed IDs `mx-es`, `co-es`, `ar-es`, `pt` to existing reviewed persona
  usernames. All four must exist, have their expected locale and distinct
  customer IDs. Customer IDs/roles cannot be supplied by the definition/request.
  The original `username`/`source_username` single-alias format remains compatible.
- Password plus existing OTP creates a **picker-only** controller in an auth
  scope anchored to the configured MX source. It grants no bank or staff access.
  The anchor is storage scope, not permission to read that customer's ledger.
- `GET /auth/judge/profiles` lists fixed IDs, labels/locales and scoped story hints;
  no customer IDs, credential material or source usernames. An owner token cannot
  use these endpoints. `POST /auth/judge/profile` accepts only `profile_id`.
- Each selection creates a fresh server-generated run, session and opaque token
  in the selected customer's realm. Roles/locales come from that trusted persona.
  The child contains a non-secret controller reference; only token hashes persist.
- Post-v0.7 correction: the business realm includes the profile and a 96-bit
  visit identifier derived from the authenticated controller digest. Separate
  password/OTP logins to the shared account get independent case/card state.
  Switching away and back within one visit retains that visitor's bank state;
  a later login starts fresh. Controller validation checks the visit identifier;
  a caller cannot choose another visitor's namespace. No client customer claim
  or RLS bypass is added, and restart preserves the controller-bound realm.
- Publish the child first, then atomically compare-and-swap the controller's active
  digest under its existing advisory lock. An unpublished/orphan child cannot
  authenticate. A losing concurrent switch never supersedes the winning token.
  Independently read back activation before returning `verified=true`.
- All judge authentication checks the live controller, binding fingerprint, expiry
  and active digest. Previous controller/child bearer tokens fail after rotation.
  Configuration/binding changes or turning mode OFF invalidate these grants.
  Pre-picker single-alias grants are rejected when transitioning to profiles;
  they have no controller and must not retain their previous bank authority.
  The checks survive API restarts and work across replicas through Postgres.
- Switching preserves the original login deadline and login OTP timestamp; it
  clears action step-up grants. Ordinary existing action freshness/OTP and separate
  confirmation remain required. No model call or per-profile budget is created.
- Logout revokes the controller, invalidating every child. Judge reset endpoints
  are forbidden even in an authored environment with reset enabled. Each visit
  starts a fresh operational workspace; old conversations/proposals cannot be
  recovered by selecting that profile again. Bank receipts remain available only
  to the same visit/profile, with fresh action OTP still required. Existing demo overlays are
  workspace-scoped, not a production banking ledger mutation.
- Audit records contain selection/revocation and fixed profile IDs/generation,
  not tokens, passwords or row facts. The global durable `production` budget stays
  **$3 per UTC day** for all profiles, retries and supporting model calls. Smoke
  overrides remain incompatible with judge mode. Switching/reset cannot replenish it.

## Threat check

| Threat | Control / remaining boundary |
|---|---|
| Session fixation | Server creates every run/session/capability; client cannot choose them. Login OTP consumes its challenge; selection rotates the capability. |
| Cross-profile reads/writes | Fixed server allowlist, immutable trusted child customer, customer-specific auth realm and forced RLS; new operational run/sid; other-profile object references return not-found. No mutable customer claim or RLS bypass. |
| Old-token/proposal/OTP replay | Controller digest makes prior tokens inactive. Proposals and action OTP are scoped to old run/sid; selected profile cannot consume them. Original login expiry is not extended. |
| Concurrent selection / logout | Locked controller compare-and-swap has one winner. Inactive children fail closed. Logout invalidates the controller even if a child row remains. |
| Crash / lost switch response | Orphan child stays inactive; activation without delivered response fails closed for the old cookie. Sign in again; never automatically retry the POST or recover stored plaintext tokens. |
| Stale tabs / in-flight responses | New requests with old tokens are denied. Already authorized requests may finish in their original scope; they never acquire the new customer's scope. Frontend must abort/discard old-generation requests, clear all customer state and pending dialogs, and coordinate tabs. It must never retry a write after switching. |
| CSRF / stolen bearer | API remains internal; BFF must enforce same-origin writes, retain HttpOnly/Secure/SameSite cookie handling and never expose bearer tokens to JS. A stolen current bearer still has ordinary bearer authority until revoked/expired; this does not add independent MFA. |
| Reset / spend bypass | Judge reset denied, controller outside operational reset, shared durable daily budget independent of customer/run/sid. |

## Consequences and acceptance gate

This adds an auth controller check for judge calls only; OFF/owner paths retain
their current behavior. Four missing/invalid bindings fail startup rather than
fall back to authored/customer data. Frontend picker and Azure enablement are
separate work; backend tests cannot establish browser stale-response handling.

Authored mock tests must cover password/OTP, picker-only denial, all four scopes,
invalid claims, rotation/replay, TTL/freshness, reset, logout, switch failures and
configuration changes. Disposable Postgres tests must cover forced RLS, restarted
stores, two competing controllers and persisted audit events. Existing local CI,
B1 and browser suites must stay green before main integration. No paid test needed.

## Revisit when

Replacing simulated SMS with real identity/MFA, enabling multiple reviewer roles,
preserving demo workspaces across visits, or integrating a production bank's
customer selection/consent system. None is implied by this restricted demo design.
