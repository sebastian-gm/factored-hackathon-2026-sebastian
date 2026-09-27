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

## Handoff 11: recording glass box (additive proposal, merge freeze)

The existing staff trace drops fields already saved in `llm_call` execution records.
This frontend PR changes only `apps/web/` and the required progress log. Lead review
and backend implementation are required after Sebastian lifts the merge freeze.

Extend `TraceEvent.llm` in the existing scoped `GET /chat/sessions/{id}/trace`:

| Optional field | Source / handling |
| --- | --- |
| `route` | `CallRecord.route`; `fallback_grok_4_20` identifies the Grok fallback. Model name alone only proves a Grok call. |
| `status`, `attempt` | Existing call record; include failed/retried calls so cost sums retain them. |
| `judgments` | Whitelist the Jev risk-call metadata below. Never expose arbitrary judgment, prompt, completion or thinking fields. |

`judgments` uses the names already in the saved record: `gemini_raw_flags`,
`gemini_raw_probabilities`, `jev_raw_probabilities`, `jev_threshold_flags`,
`union_flags`, `threshold`, `degradation`, `primary_failed`. Flags/probabilities are
keyed by `lost_stolen`, `regulator`, `legal`, `distress`, `injection_suspected`,
`human_requested`. Preserve null/partial raw Jev values and degradation (incomplete answers must not break the trace); Gemini per-cue
probabilities are null, and intent confidence is not a substitute. The browser
renders the recorded union; it does not recompute policy or risk authority.
The allowlisted Zod projection is `src/lib/trace.ts`. Existing trace responses remain
valid. Missing fields display unavailable. Conversation cost sums unique event IDs,
including failures; null-cost calls produce a known subtotal and an unknown count.
No-call traces do not claim a measured zero; costs show at least six decimal places.

The recording helper uses the current fixture/judge mode, authentication and reset.
Authored fixture mode can reset all demo stories in its existing browser workspace,
verify the receipt plus overview, then open the ES persona with a prepared message.
Story buttons switch ES/PT/fraud personas through regular password+OTP; the fraud
story opens the existing Agent Desk login. It never auto-sends or auto-confirms.

For live recording, propose optional `demo_stories: ["explain" | "ambiguous" | "fraud"]`
on each trusted `/personas` entry. This is a routing hint, not a role grant. The
frontend already accepts it; omitted mappings leave story buttons disabled. Bind
only owner-reviewed personas with suitable scoped transactions. Messages are generic
and contain no copied organizer values. The owner supplies any needed live details.
Existing Ops reset still requires enabled server flags, fresh OTP, explicit proposal
confirmation and receipt read-back, then opens ES if bound. Current cloud reset
remains disabled. Live reset clears only the current workspace; no cross-persona
bulk reset exists. If the recording needs that operation, the lead must define a
separately authorized reset orchestration; this UI does not widen RLS or bypass OTP.

Validation uses authored fixtures and local B1/mock API only. Risk/Grok display
fixtures are illustrative injected test responses, not paid-model measurements.
