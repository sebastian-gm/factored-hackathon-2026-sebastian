# Frontend integration and remaining API requests

PR #17 consumes the additive contracts merged in backend PR #21. No backend,
policy, frozen interface or shared CI file is changed by the frontend lane.
See [the lead's contract notes](../../docs/api/frontend-additions.md) and
[OpenAPI](../../contracts/interfaces/openapi.json).

| Capability | Implemented frontend behavior |
| --- | --- |
| Identity | Discover safe personas; use trusted `/me.role`, locale and bank clock. The backend remains the authorization authority. |
| Session | HTTP-only cookies; upstream logout followed by `/me` rejection; fresh OTP for freeze/reset. |
| Plans | Accept typed refusal/status/review flags/freeze offers. A revoked session shows refusal without an unverifiable receipt. |
| Freeze | Exact proposal hash and confirmation/cancellation; independent card and handoff GETs plus backend verified flags. |
| Agent Desk | Scoped queue/detail, priority/SLA, evidence, actions, risk flags and next steps. Claim/resolve use version and idempotency fields, then GET readback. Resolution does not promise a refund. |
| Trace | Scoped execution stages, fired rules, tool/readback and provider/model/prompt/token/cost/latency metadata. No thinking or prompt/completion payloads. |
| Ops | Real current-workspace counts, observed model cost, DQ/source metadata and traces. SAR/unsafe remain null; freshness is unknown without a supplied threshold. |
| Reset | Disabled by default; requires trusted web/API flags, ops role, fresh OTP, exact confirmation and receipt GET. Clears only current workspace operations; retains auth/audit. |

Opt-in fixtures remain for isolated UI tests. Live failures never fall back to
fixtures, and live Ops never displays the illustrative fixture result table.
The current API exposes one configured identity and its own workspace. Production
staff federation, a multi-customer queue, masked product display labels and
transaction-to-product mappings remain backend requests. Daily cost history and
an explicit freshness SLA are also absent; the UI does not invent them.

Before deployment, run `node scripts/check-api-hop.mjs` inside the web runtime.
It requires the configured `API_BASE_URL` (or `BROWSER_API_BASE_URL`) and exposes
only status metadata. Local reachability is tested; Azure reachability from the
web container under the owner-IP ingress restriction is **not verified**. Keep
that restriction in place. The lead owns deployment/private connectivity.

Lead-owned CI follow-up: install Playwright Chromium, then run `pnpm test:e2e`.
`--live` and `--staff` additionally need the repository Python dev environment.
All browser tests use authored fixtures, ephemeral credentials and mock/B1 models;
they do not read the worktree `.env` or spend money.
