# Frontend integration and remaining API requests

## Basic-mode reply signal (2026-10-02 UTC)

The frontend accepts optional `degraded: boolean` on each chat message/confirmation
plan. `true` shows a neutral localized **Modo básico** status; `false` or omission
shows no notice. This display flag grants no authority and changes no action,
readback, confirmation or OTP check. ES/PT authored browser fixtures cover it.

**Lead-owned addition needed:** current main keeps `Conversation.degraded` in
`src/aclara/api/app.py` and NLU/phrasing failures in traces, but does not expose a
reply-level signal. Add `degraded` to the public plan response, true when this
turn uses deterministic fallback because budget/model availability failed. A
successful alternate model or a normal policy template should not imply basic
mode. Set it for messages and confirmations; preserve it on idempotent readback.
Only a boolean is needed—no budget balance, diagnostic text or provider failure
details. The BFF and chat allowlist already retain this optional field. The UI
does not infer degradation from customer-facing wording or extra trace calls.

## Live video readiness triage (2026-09-30 PDT)

GET-only Azure check at **2026-10-01 01:18:03 UTC**, web/API release
**c32fd6429281a764ee33dd96622f237c7c0289c3**. No authentication request, model
call, chat message, reset or cloud configuration change was made. The safe
project-persona projection is in [live-story-evidence.json](fixtures/live-story-evidence.json);
it contains no customer binding, organizer row or credential.

| Trusted live persona | API role | Supplied `demo_stories` | Diagnosis                                                                                                          |
| -------------------- | -------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `demo.es.mx`         | `ops`    | `explain`, `fraud`      | Frontend defect: `storyPersona` required `customer`, rejecting both supplied hints.                                |
| `demo.pt.br`         | `ops`    | empty array             | API availability gate: no PT shortcut was authorized by the hint. Removing the role filter alone cannot enable it. |

`GET /api/bff/config` returned **200**, `fixtures: false`. The BFF reads upstream
`GET /personas`, validates `personaSchema`, and preserves the optional hint array.
Direct unauthenticated `GET /api/bff/personas` returned **401**; it is not the public
persona-discovery passthrough. That status is not evidence about upstream hints.
See [the config handler](src/app/api/bff/[...path]/route.ts) and
[the upstream persona gate](../../src/aclara/bank/serving.py).

Frontend fix: accept a supplied live hint for any served persona role. Prefer the
current hinted identity, then a hinted customer if available, then another hinted
persona. A shortcut only selects an account and prepares a draft. Password/OTP,
`/me.role`, staff authorization, proposal confirmation, scoped serving data and
reset gates remain authoritative. Absent hints still disable the shortcut; no
username-based live fallback is introduced. Fixture eligibility remains unchanged.

**Lead request for PT:** `demo_story_mappings` currently requires at least two
`displayable` transactions, and that list requires a nonempty merchant name.
The observed role/locale satisfy the PT gate; no hint was returned. Review that
condition independently of model outputs. Either bind an owner-reviewed PT persona
with two suitable named transactions, or separate named explanation eligibility
from purchase-choice eligibility: allow `ambiguous` when at least two **owned,
scoped, reviewable** movements can supply a valid handle/date/amount/currency/status.
An absent merchant should retain its missing label, not be invented. The frontend
now renders named ordinal choices and explicit missing-merchant text. Existing
policy and authorization still decide what follows selection, including human
review. Keep the hint absent when the scoped candidate set is insufficient. No
backend gate was changed in this PR.

## Other rehearsal blockers: ownership and disposition

| Finding from rehearsal                                                                | Frontend handling / remaining owner work                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ES pending draft selected an Approved card; default PT unfamiliarity draft handed off | Live drafts use a neutral ES charge inquiry and the previously observed alternative PT inquiry. The MX persona label no longer asserts Pending. Drafts still require send; no live model replay verifies the new release. Original failed rehearsal remains disclosed in PR #88.                                                                                                                                                                |
| Blank/em-dash merchant names; missing card/product labels                             | Number the three choices and label absent merchant values explicitly; numeric merchant names remain unchanged. Keep product unavailable. A masked product display field/mapping, if wanted, remains an additive backend request; do not infer card type or copy a fixture product into live mode.                                                                                                                                               |
| Fresh SLA counter spans months                                                        | Backend supplies `created_at` in real UTC and `sla_due_at = created_at + 15 days`. Live Desk now compares against wall time; authored fixtures retain their simulated clock. Show days/hours/minutes and the supplied deadline as a tooltip. Backend owns the duration. Browser clock skew remains a presentation limitation; a server wall-clock anchor could address that later.                                                              |
| Raw `fraud_review`                                                                    | Localized review indicator; original flags in collapsed technical references. Unknown flags receive a generic label and stay available as secondary references; no routing/risk inference.                                                                                                                                                                                                                                                      |
| Empty verified facts, actions and questions                                           | Explain each absence explicitly. Do not fabricate facts or green action icons. The lost-card story need not identify a transaction. **Lead request:** Desk currently constructs `actions` only for freeze outcomes. Include the verified handoff creation/readback in that existing array only after durable verification, with its saved trace/evidence reference. The frontend already supports `create_handoff`; no schema change is needed. |
| Deterministic fraud Ops says only “No registrado”                                     | Show “no model calls recorded,” explicitly say there is no model-cost measurement, and scope absent risk judgments to this trace. Preserve a known subtotal/unknown count for actual calls; never label absent usage as measured zero.                                                                                                                                                                                                          |
| Recording controls below the fold                                                     | Recording opt-in adds a quickstart shortcut that opens, scrolls to and focuses the helper. It stays hidden by default and makes no API call.                                                                                                                                                                                                                                                                                                    |
| Generated ES `operaci3n` and ES/PT `approved` in prose                                | AI/lead-owned NLG defect. Status badges are already localized. Preserve received prose; do not silently rewrite model facts in the browser. Review grounding/localized status rendering and corruption guards before the polished recording.                                                                                                                                                                                                    |
| Initial startup latency                                                               | Infrastructure/runtime startup, not a story-button gate. Existing distinct starting/error states and bounded GET retry remain; no replica or access change. Browser checks retain startup/error coverage.                                                                                                                                                                                                                                       |

Verification uses authored UI responses and local B1/mock fixture APIs only. Local
browser ports can be isolated with `FRONTEND_E2E_WEB_PORT` and
`FRONTEND_E2E_API_PORT`; CI retains 3212/8212 by default. Live fixes require lead
merge/deployment and a new authorized rehearsal. No frozen suite or gold was used.

## ADR-0015 customer decision and reason sets (2026-09-27)

The frontend accepts the lead's regenerated additive contract from PR #51
(`5aa0f11`, `feat/lead-after-v2-fixes`). This frontend PR targets that branch for
integration into #51; main/deployment integration remains the lead's work.
No shared schema or backend file is changed here.

| Field                                                                                        | Frontend handling                                                                                                                                                                                                                                                                    |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `response_type: offer_dispute`, `outcome: awaiting_dispute_decision`, required `transaction` | Nonterminal explanation card, explicit recognition/denial buttons and free text. Buttons send only `{message}` through the existing messages endpoint. No confirmation hash or write is synthesized. Reject an offer combined with a proposal, case receipt, handoff or session end. |
| `cancelled` outcome                                                                          | A neutral cancellation notice; composer remains usable, without claiming successful dispute resolution.                                                                                                                                                                              |
| Optional `handoff.primary_reason: string \| null`                                            | Show it first, then every remaining reason. It must belong to `reason_codes`. An omitted value leaves the server's reason order intact and is labeled unavailable; the UI does not infer routing precedence or completed OTP from a reason code.                                     |

The #37 optional live projections below remain wired through the existing BFF
allowlist into Ops and the recording helper. No switch to illustrative fixtures
occurs on a live error or absent field. The lead's announced story mapping is
`demo.es.mx → explain, fraud` and `demo.pt.br → ambiguous`, gated on scoped serving
data. The frontend consumes those hints **only when supplied** on trusted personas;
it never hardcodes that mapping into live mode. An absent mapping disables only
the affected shortcut and leaves ordinary chat available. A shared persona may
serve two stories without an unnecessary logout. Each shortcut prepares a draft,
never sends it or confirms an action. Reset authorization remains unchanged.

PR #51 now publishes nullable `LlmMetadata.route/status/attempt`, risk `judgments`
and scoped `PersonaView.demo_stories`. The BFF and browser consume those live fields
without a fixture fallback; null or absent metadata remains unavailable. The risk
projection continues to allowlist known flags/probabilities rather than arbitrary
judgment text. No additional field is requested beyond the accepted proposal below.
Browser checks use new authored UI responses and the local #51 B1/mock fixture API,
including the real explain → offer → denial → proposal → confirmation path after
password/OTP. No held-out suite or gold is used.

The recognition buttons retain the requested short labels but send an explicit
sentence: “Sí, la reconozco. Ya me acordé de esta compra.” / “Sim, reconheço.
Agora lembrei dessa compra.” This remains ordinary user text, not a confirmation
or trusted intent. Lead integration reproduced and fixed the shorter ES/PT labels
being treated as out of scope by the deterministic fallback. Authored API tests
cover both short labels with B1/P mock, while isolated yes/no remains ambiguous.
Both fuller button messages are covered by authored browser checks; the Spanish
message also runs through the real local API.

## Existing integration

PR #17 consumes the additive contracts merged in backend PR #21. No backend,
policy, frozen interface or shared CI file is changed by the frontend lane.
See [the lead's contract notes](../../docs/api/frontend-additions.md) and
[OpenAPI](../../contracts/interfaces/openapi.json).

| Capability | Implemented frontend behavior                                                                                                                                                               |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity   | Discover safe personas; use trusted `/me.role`, locale and bank clock. The backend remains the authorization authority.                                                                     |
| Session    | HTTP-only cookies; upstream logout followed by `/me` rejection; fresh OTP for freeze/reset.                                                                                                 |
| Plans      | Accept typed refusal/status/review flags/freeze offers. A revoked session shows refusal without an unverifiable receipt.                                                                    |
| Freeze     | Exact proposal hash and confirmation/cancellation; independent card and handoff GETs plus backend verified flags.                                                                           |
| Agent Desk | Scoped queue/detail, priority/SLA, evidence, actions, risk flags and next steps. Claim/resolve use version and idempotency fields, then GET readback. Resolution does not promise a refund. |
| Trace      | Scoped execution stages, fired rules, tool/readback and provider/model/prompt/token/cost/latency metadata. No thinking or prompt/completion payloads.                                       |
| Ops        | Real current-workspace counts, observed model cost, DQ/source metadata and traces. SAR/unsafe remain null; freshness is unknown without a supplied threshold.                               |
| Reset      | Disabled by default; requires trusted web/API flags, ops role, fresh OTP, exact confirmation and receipt GET. Clears only current workspace operations; retains auth/audit.                 |

Opt-in fixtures remain for isolated UI tests. Live failures never fall back to
fixtures, and live Ops never displays the illustrative fixture result table.
Live identities have separate scoped workspaces. Production staff federation,
a multi-customer queue, masked product display labels and
transaction-to-product mappings remain backend requests. Daily cost history and
an explicit freshness SLA are also absent; the UI does not invent them.

Before deployment, run `node scripts/check-api-hop.mjs` inside the web runtime.
It requires the configured `API_BASE_URL` (or `BROWSER_API_BASE_URL`) and exposes
only status metadata. Local reachability is tested; the live Azure config-to-personas GET is verified
at the release above. This does not verify every API route or authorize changing
the owner-IP ingress restriction. The lead owns deployment/private connectivity.

The shared CI installs Playwright Chromium and runs all three browser modes.
`--live` and `--staff` additionally need the repository Python dev environment.
All browser tests use authored fixtures, ephemeral credentials and mock/B1 models;
they do not read the worktree `.env` or spend money.

## Handoff 11: recording glass box (accepted by PR #51)

PR #51 projects the fields saved in `llm_call` execution records as proposed below.
This frontend PR changes only `apps/web/`. The lead owns merging and deployment.

Extend `TraceEvent.llm` in the existing scoped `GET /chat/sessions/{id}/trace`:

| Optional field      | Source / handling                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `route`             | `CallRecord.route`; `fallback_grok_4_20` identifies the Grok fallback. Model name alone only proves a Grok call.    |
| `status`, `attempt` | Existing call record; include failed/retried calls so cost sums retain them.                                        |
| `judgments`         | Whitelist the Jev risk-call metadata below. Never expose arbitrary judgment, prompt, completion or thinking fields. |

`judgments` uses the names already in the saved record: `gemini_raw_flags`,
`gemini_raw_probabilities`, `jev_raw_probabilities`, `jev_threshold_flags`,
`union_flags`, `threshold`, `degradation`, `primary_failed`. Flags/probabilities are
keyed by `lost_stolen`, `regulator`, `legal`, `distress`, `injection_suspected`,
`human_requested`. Preserve missing/null/partial maps and individual null flags
across all risk sources, plus degradation (incomplete answers must not break the
trace). Unknown flags display “not recorded,” never false. Gemini per-cue
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

For live recording, PR #51 supplies optional `demo_stories: ["explain" | "ambiguous" | "fraud"]`
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
