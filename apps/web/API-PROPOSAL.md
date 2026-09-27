# Additive API proposal for lead review

No backend or frozen interface is changed in this PR. Existing customer requests use
only the fields in `contracts/interfaces/openapi.json`; browser tokens move to the
Next.js server-side cookie proxy. These additions are needed for the full live UI.
Typed extension models are in `src/lib/contracts.ts`, and their only implementation
is behind server-only `FRONTEND_DEMO_MODE=fixtures`. Live mode returns an explicit
unavailable state for missing contracts, without issuing invented upstream requests.

| Contract gap | Proposed addition / behavior |
| --- | --- |
| Persona discovery and staff identity | Safe alias/label/locale persona list; typed `/me` with trusted server role, locale and bank clock. Agent/ops roles must come from verified authentication, never a username or client field. Password and OTP remain mandatory. |
| Products | Add masked product label/type/handle to transaction views, or publish owned `/accounts` views. Never expose full account/card numbers. Until then the live UI says product unavailable. |
| Proposal integrity and freeze | Extend the proposal with explicit typed handle parameters, server-signed nonce and card-freeze action; extend confirmation input accordingly while preserving v1. Current frozen input accepts only proposal hash plus boolean. The UI submits exactly those fields and implements dispute confirmation only. Fraud currently hands off without claiming a card freeze. |
| Session and step-up | Publish challenge refresh / fresh OTP and logout revocation endpoints. Until then expiry requires a new authenticated session and a new proposal; no client bypass. BFF logout clears cookies but cannot revoke an upstream token. |
| Agent queue | `GET /agent/handoffs`: priority, SLA due timestamp, language, reason codes, status, claimant and opaque handoff/conversation references, scoped to an authorized agent. |
| Handoff details | Agent-scoped `GET /agent/handoffs/{id}` with the §12.4 packet: masked customer, evidence-linked verified facts with tool/dataset/time, separately labeled unverified statements, verified action timeline, routing/fallback, open questions, transcript reference. No raw scores, thinking or raw transcript payload. |
| Claim / resolve | POST claim and resolve endpoints with authorization, version/conflict handling and idempotency. Return a result that the UI can verify using GET. Resolution must not imply a refund. |
| Execution trace | Role-scoped `GET /chat/sessions/{id}/trace`, with stage/state, fired rules, tool calls, verification and LLM provider/model/prompt/tokens/cost/latency only. Customers continue to see safe response-plan evidence, not staff trace details. |
| Ops | Typed DQ/freshness/metrics endpoints with dataset version, bank clock, timestamps, result denominators/system/version, daily costs and available conversations. Never conflate fixture examples, dev results and held-out results. |
| Reset | Ops-only POST reset with explicit confirmation, fresh step-up, well-defined demo isolation and verified read-back. The fixture action resets only the current browser workspace. |

The current `TransactionView`, `ProposalView`, `DisputeCaseView`, `HandoffView` and
`ResponsePlan` projections have runtime validation before reaching the UI. Optional
fields are not treated as evidence when absent. The current live `/me` has no role,
so the proxy grants customer UI access only; staff aliases do not escalate it.

No deployment or paid model run is part of this frontend PR. The local fixture
backend is not suitable for multi-instance deployments: it has in-memory sessions,
short-lived workspaces and no shared store or production rate limiting. Lead-owned
identity, persistence, role enforcement, signed confirmation and live Ops/Desk
integration remain required before claiming those surfaces are production-ready.

CI follow-up: add `pnpm exec playwright install --with-deps chromium` and
`pnpm test:e2e` to the web job. The fixture run has no Python or live-service
dependency. The separate `--live` integration run needs the repository dev Python
environment and still uses only generated fixtures / mock B1.
