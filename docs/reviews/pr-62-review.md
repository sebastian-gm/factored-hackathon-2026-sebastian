# PR #62 review — original head 32587c9

Lead review of the orchestrator's commits, 2026-09-29 PDT. This review does not
merge the PR, run paid models or open v4 inputs. The Azure startup defect is
separately reproduced and addressed in [the diagnosis](../evaluation/preview-startup-diagnosis.md).
Existing local tests passed, but the authored checks below expose missing cases.

## Findings requiring follow-up before release

### 1. P1: phrase v2 does not receive the actual recognition question

`d935c8a`, `src/aclara/agent/nlg/builder.py` (`fallback` and `approved_text`).
The new approved text is `render_template(plan)`, whose clarification is the
generic amount/currency/date question. For the orchestrator's awaiting-recognition
clarification, it is **not** the approved `plan.reply` asking whether the customer
recognizes the already identified charge or wants to dispute it. `AgentAI.reply`
then accepts a safe generic draft and replaces that question.

**Executed zero-cost reproduction:** an authored recognition plan plus a mock
Spanish amount/date draft produced a prompt and returned reply with no recognition
question. The state is still awaiting recognition, but the customer is asked for
irrelevant charge identifiers. The prompt's “keep its question” instruction cannot
preserve a question it never receives.

**Owner: AI lane, with lead context tests.** Pass the approved state-specific text
and preserve required recognition semantics, or keep this clarification entirely
deterministic. Validate both ES/PT recognition retries, including a generic safe
draft that must not replace the required question.

### 2. P1: session-wide security strikes lose cues across conversation tabs

`d935c8a`, `src/aclara/api/app.py`, `refuse_cross_customer`.
Strike counts are scoped to the authenticated session in `security_state`, while
new legal/distress cues are accumulated only in one `Conversation.security_cues`.
The second strike in another conversation terminates the same session but builds
its packet from that second conversation only.

**Executed zero-cost reproduction:** an authored first cross-customer attempt with
a regulator cue, then a second attempt in a new conversation, ended the session
with `SEC-01`/`AUTH-03` and **lost `ESC-02`**. No cross-customer data was disclosed;
the defect is incomplete required handoff reasons. The new regression test covers
two attempts in the same conversation, so it misses this case.

**Owner: lead.** Keep strike-associated cues in the same session-scoped durable
record as the attempts, union them before the terminal handoff, and test separate
tabs plus restart. Retain the existing two-strike rule and authorization boundary.

### 3. P2: a domain or SIM card incorrectly switches Spanish to Portuguese

`d935c8a`, `src/aclara/agent/nlu/rules.py`, `detect_language`.
Any one token from the added set forces Portuguese; `com` matches a `.com` merchant
and `sim` matches a Spanish SIM-card reference. The same heuristic is now used as
a hard acceptance check on NLG drafts. Conversely, a valid short PT draft with no
listed marker defaults to Spanish and can consume an unnecessary correction call.

**Executed authored checks:** “¿Qué es el cargo de Booking.com?” and a Spanish
human request about a SIM card both return `pt`; “Informe valor e moeda.” returns
`es`. These are project-authored examples, not suite text.

**Owner: AI lane.** Exclude domain/name tokens from language evidence and use
stronger contextual evidence or an explicit uncertain result. Keep the required
wrong-language fallback, but do not use this single-token test to reject every
short valid PT draft. Add mock regressions before any paid measurement.

### 4. P2: generic stale-OTP renewal cannot reuse a freeze hash

`d935c8a`, `evals/bound_execution.py`, the new 401 renewal branch.
It renews step-up then reposts the **same** confirmation for both dispute and
freeze endpoints. A freeze proposal intentionally binds `step_up_at`; after
renewal its old hash still fails the API's binding check. Dispute renewal and
freeze renewal require different generic state transitions.

**Executed zero-cost reproduction:** the authored freeze fixture with a stale-OTP
fault and `provides_new_step_up=true` still ended `refused_security`, missing
`freeze_card`. No policy threshold or OTP check should be weakened to fix this.

**Owner: lead/evaluation harness.** Require the exact step-up-required error before
renewal; for freeze, obtain a new proposal and return it to the simulated customer
for confirmation. Preserve rejection of expired sessions, wrong/tampered hashes
and customers who decline the fresh OTP.

### 5. P2: latest fraud packet can belong to another pending conversation

`d935c8a`, `src/aclara/api/workflows.py`, `fraud_reasons`.
The helper chooses the newest fraud packet in the whole session. A later fraud
conversation can replace the reasons belonging to an earlier pending freeze.
The freeze proposal has no link to its originating fraud packet, so the intended
reason provenance cannot be reconstructed reliably.

**Executed zero-cost reproduction:** two authored fraud conversations under one
login, first with `ESC-02`, second without it, followed by freeze cancellation,
returned only the second packet's `FRD-01`/`AUTH-02`. The first conversation's
legal reason was absent. A single-conversation test cannot detect this.

**Owner: lead, shared API/frontend contract.** Bind the freeze proposal to the
originating owned handoff/conversation and preserve that packet's reasons through
the final response. Do not infer that the most recently created packet is the one
the customer is confirming.

Aggregate authored reproduction receipt: ignored, mode-0600
`artifacts/preview-diagnosis/review-reproductions.json`. Checks used
`PYTHONPATH=src:tests .venv/bin/python` with the existing authored API and bound
evaluation fixtures, in-memory ASGI clients, `StructuredClient` mock responses and
no provider keys. No frozen input or paid call was used. Product/evaluation fixes
for these findings are not included in the separate startup patch.

## Commit-by-commit disposition

| Commit | Review |
|---|---|
| `80434ab` | Historical operational stop entry; preserves checkpoints, spend and release pin. No runtime change. |
| `cf03a59` | Historical single-resume stop entry; scopes connectivity cause and judging interruption accurately. No runtime change. |
| `018c8d5` | Partial v3 result entry agrees with saved aggregates; explicitly does not claim whole-program completion. |
| `d935c8a` | Multi-area fixes; findings 1–5 above. Lost-card/distress/outage branches and judge-cap update have no additional confirmed defect from this review. Generic repairs need independent authored coverage beyond seen-v3 reruns. |
| `095085e` | Snapshot cache resets per HTTP request; customer/clock authorization checks precede cache hits. Warm authenticated serving reads and disposable-Postgres tests passed. Budget script closes prior scopes and enforces the dev lifetime cap plus future allowance; no paid preparation was rerun. No confirmed cache defect. |
| `63545c9` | Post-v3 gate profile selects the existing dev/fault/confirmation sets and new shared budget scope. No v4 access or confirmed routing defect. Confirmation data is now seen; another pass is not blind validation. |
| `d44a480` | First-attempt timeout remains inside the existing retry/reserve accounting; its authored budget test passes. Timeout can leave unknown billed usage, which keeps the conservative reservation. The 6-second performance benefit has not been independently measured here; no paid latency claim. |
| `817a07b` | Stale dispute OTP keeps the access cookie and rechecks the proposal after renewal. Local browser flows pass. No automatic transport-level POST replay is introduced. New renewal UI lacks dedicated original-PR browser coverage; wrong-code handling drops the proposal and asks for a new login despite a potentially valid session (code-review observation, not separately exercised). |
| `14745df` | Historical `docs/v3-operational-stop` entries are already merged into this feature branch; no second merge required. |
| `37627d4` | Development analysis explicitly labels the seen-v3 100/100 as a regression check. Do not use it as a new official result or evidence for a fresh v4. The claim “all fixed” is limited by the authored findings above. |
| `32587c9` | Preview-deploy record distinguishes branch preview from main release and states the remote billing block and unrun paid smokes. Azure image metadata confirms `37627d4`; its cold-start limitation is now reproduced. |

## Merge gate

PR #62 is **OPEN**. Its remote checks report failure because GitHub did not start
the jobs: an Actions budget prevents further use. Local CI execution is recorded
separately in the progress log. Resolve the findings, restore CI or obtain the
owner's explicit merge exception, and reverify the actual release before v4.
No merge, Azure configuration change or v4 start was performed by this review.
