# Lead follow-up to the accepted PR #62 review

2026-09-29 PDT. Based on feature preview `dac3801`, with session-security PR
[#67](https://github.com/sebastian-gm/bank-agent-lab/pull/67) included in the
combined candidate. Both follow-up PRs target `fix/post-v3-analysis`.
Main remains `e12efc73be64f8355aa9f177f08a04337593616c`; these fixes are not deployed.
Findings #1 and #3 remain with the AI lane. No paid calls or v4 access occurred.

## Finding #2: security cues have the same scope as strikes

The durable `execution_records/security_state` stores attempts and the union of
legal/distress cues under the authenticated customer/run/session scope. A strike
in another tab retains earlier cues. Older conversation-only cues are unioned on
the next strike for upgrade compatibility. The two-strike rule, session revocation
and invalidation of all pending session decisions are unchanged.

Authored checks cover another conversation tab, another login remaining isolated,
actual browser tabs sharing the access cookie, and app/store restart on Postgres.
The BFF deliberately withholds the terminal receipt after revocation because the
revoked token cannot independently read it. API/Postgres tests verify its persisted
reasons; browser tests verify revocation of both views without claiming a receipt.

## Finding #5: freeze provenance is explicit and durable

Shared request/response contract changes:

- `POST /cards/{handle}/freeze/proposal` **requires `handoff_id`**, in addition to
  the existing language. Missing origin returns 422; unknown/unowned/non-fraud
  origins and cards not actually offered by that packet return 404.
- `FreezeProposalView` adds `handoff_id` and `conversation_id`. The BFF, UI and
  evaluation adapter consume the same contract; OpenAPI was regenerated.
- The server stores the offered card handles in scoped idempotency state. It
  checks the originating owned packet and conversation, then hashes the origin,
  conversation and complete reasons into the proposal with the existing scope,
  card, nonce, expiry and OTP timestamp.
- Confirmation rechecks ownership and origin. Final freeze/decline packets use
  that conversation and those reasons, regardless of later fraud conversations.
  The original packet remains unchanged. The session's newest packet is never
  inferred as the origin.

This intentionally tightens a write-related request: callers must pass the handoff
that offered the card. Old unbound proposals are rejected and require a fresh
review; offers from older deployments without the stored provenance need a new
conversation. No migration loosens authorization. The checked-in authored callers
have been updated; frozen suite bytes and private bindings are untouched.

Authored checks cover freeze and cancellation after a later plain fraud packet,
wrong-session/non-fraud/unoffered-card origins, tampered binding, renewal with a
new hash, and the originating legal packet surviving app/store restart.

## Finding #4: renewal is an explicit harness transition

The evaluation adapter renews only for **HTTP 401 with the exact API detail
`Step-up verification required`**, and only when the simulated customer explicitly
provides a fresh step-up. Other 401s, expired sessions and malformed error bodies
never trigger renewal. A successful renewal is recorded only after verification.

A still-valid dispute proposal can be confirmed again after renewal. A freeze
proposal binds the OTP timestamp and cannot be reused: the adapter obtains a new
proposal for the same origin, records it as the next observed response, then asks
`Customer.reply` for a new decision. It does not automatically confirm the card.
An authored customer changing its mind declines the new proposal, with no freeze.
This is generic runtime behavior, not a case-specific adjustment or threshold change.

## Commit 817a07b: incorrect renewal codes remain retryable

The BFF maps **only `auth/step-up/verify`, HTTP 401, `Invalid code`** to
`invalid_otp_code`. The UI keeps the exact pending dispute and challenge, clears
the incorrect entry and shows an ES/PT retry message. The customer can try again;
no confirmation is resent until code verification succeeds. Other session errors
retain their existing handling. The server still enforces five attempts.

Authored browser checks exercise real local OTP verification through the BFF in
both UI languages. The initial stale-step-up response is mocked to enter the
dialog; subsequent wrong/correct OTP calls and confirmed intake use the real mock
bank API. A disposable-Postgres check verifies wrong-code attempt state and the
pending dispute survive restart and can complete with the correct code.

## Verification and limitations

- `make checks`: 324 passed, 16 database-dependent skips; B1 32/32;
  pre-commit/staged-file policy, compile and interface/catalog checks passed.
- `python -m scripts.test_postgres`: 19 passed, including real restart/RLS checks.
- `python -m evals.runner --system B1 --scenarios evals/dev_scenarios_v2.yaml`: 32/32.
- Ruff and strict mypy passed; web typecheck, lint and production build passed.
- `pnpm test:e2e`: 46 passed; `--live`: 12 passed; `--staff`: one passed.
  The live two-conversation check verifies the BFF/UI forwarded the first handoff
  and retained its legal reasons after another tab opened a fraud packet.

Tests use authored fixtures and mock NLU only. No fresh paid dev measurement,
v4 preflight or held-out evaluation is claimed. GitHub Actions still cannot start
due account billing. The candidate needs review and the existing main merge gate.
