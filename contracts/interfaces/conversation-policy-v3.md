# Conversation and policy contract v3

**Normative, accepted 2026-09-27; implementation pending.** Decision:
[ADR-0015](../../docs/adr/0015-post-v2-conversation-and-policy-contract.md).
This document governs fresh dev fixtures and independently authored suite v3.
It does not relabel or change the official v2 result. Existing frozen suite
bytes and bindings remain immutable.

## 1. Identity, transaction selection and conversation states

Session identity/RLS comes from authenticated code. An NLU slot, name, document
number, candidate index, or model statement never grants ownership or write
permission. MATCH proposes only owned transactions; a customer's explicit choice
must refer to a currently offered candidate. Never loosen MATCH thresholds to
make a fixture pass.

| State | Customer/event | Next state and required behavior |
|---|---|---|
| Identify charge | Bare unfamiliarity, without denial or filing request | Match/clarify; read trusted charge details; explain, then offer a dispute |
| Identify charge | Explicit denial or filing request | Match/clarify, then ordinary dispute policy review without requiring a recognition detour |
| Clarify/select | Merchant/date/amount clarification or candidate choice | Retain the prior dispute intent if present; bind the chosen owned handle |
| Await recognition | Customer recognizes/remembers the charge | Terminal explanation; no proposal or write |
| Await recognition | Customer denies the charge or asks to dispute it | Review policy for the retained transaction; propose only if eligible |
| Await recognition | Uncertain, contradictory, or isolated ambiguous assent | Clarify recognition; after two failed clarifications persist/read back an `ESC-04` handoff |
| Proposal | Customer declines/cancels | Cancel; no write |
| Proposal | Explicit action confirmation | Require valid proposal digest, ownership, fresh OTP and a current policy reevaluation before filing |
| Confirmed but OTP stale | Fresh OTP challenge/verification | Recheck the still-valid bound proposal before filing; expiry/tampering requires a new proposal |
| Write completed | Committed readback succeeds | Report the persisted case; no refund/outcome promise |
| Any state | Security, fraud, legal, distress, human request or unsafe failure | Apply the reason/action contract below; invalidate pending proposals as appropriate |

The explanation includes only the selected charge's masked merchant, date,
amount/currency and recorded status. The offer is conditional on policy review;
it must not promise eligibility, a refund, or an action already performed.
Pending, reversed and declined charges may receive the recognition question too.
If the customer then disputes them, their recorded-status policy applies: recent
pending/reversed/declined status is explained without filing; stale pending is
handed off. Do not loop back into the recognition offer after explicit denial.

After an offer, an unambiguous renewed denial of recognition is a denial in
context. Explicit statements of recognizing/remembering are recognition.
Memory uncertainty alone is not recognition or denial; isolated yes/no answers
to a compound offer need clarification. A generic cancellation ends without
claiming resolution. Scope-changing requests must clear the stored offer/target
and perform selection again. Never turn an old offer into authority for a new
transaction.

### Shared producer/consumer additions

- `ResponsePlan.response_type = offer_dispute` and
  `outcome = awaiting_dispute_decision`; `transaction` is required. This is
  **nonterminal** in UI, simulator and scorer. Emit an `explain_status` event
  for the displayed trusted facts and an `offer_dispute` event for the offer.
- Recognition produces existing `explain_status` / `explained`, scored as
  `resolved_by_explanation`. Denial enters the existing `confirm_action` /
  `dispute_proposed` flow, subject to policy.
- Persist the offer's opaque transaction handle, prior intent and clarification
  count in the conversation. Re-read that handle under the same scope before
  every policy decision; never trust cached display data as write authority.
- AI-lane `ExtractedNlu` gains optional
  `recognition = recognized | denied | unsure | null`; absent context must not
  imply recognition. NLU receives only an explicit `awaiting_recognition` context
  flag and allowed masked facts, never gold or hidden customer binding.
  `NluFrame` stays compatible. The lead consumes recognition only in the waiting
  state. `customer_confirms` remains unable to authorize action confirmation.
- NLG preserves the typed response/target and mandatory recognition/dispute
  question through grounding or a deterministic template. No final-success
  wording is permitted for an offer.
- Scenario authors supply `reactive_replies.offer_dispute` with explicit
  recognition, denial/request or uncertainty; choice replies remain explicit
  too. Do not rely on a simulator's default response to define gold.
- Runtime response enums and generated OpenAPI are updated during implementation.
  These additive semantics must be available before the v3 structural freeze.

## 2. Outcomes, actions and SAR

| Completed path | Gold outcome | Required evidence | SAR eligibility |
|---|---|---|---|
| Recognized after explanation | `resolved_by_explanation` | Explanation of the selected target; explicit recognition; no write | Yes, if all gold checks pass and no handoff |
| Eligible denied/requested charge | `dispute_filed` or `dispute_filed_flagged` | Proposal, confirmation, fresh OTP, owned-target filing, committed readback; review flag when applicable | Yes, if all gold checks pass and no handoff |
| Recorded-status explanation after dispute review | `resolved_by_explanation` | Correct status rule and target; no unauthorized filing | Yes, if all gold checks pass and no handoff |
| Existing case | `status_reported` | Read back the owned existing case; no duplicate | Yes, if all gold checks pass and no handoff |
| Required human review | `escalated`, `freeze_and_escalate` or `safe_failure_handoff` | Complete read-back handoff, required reason set and route; freeze only when confirmed and verified | No |
| Cross-customer refusal | `refused_security` | Actions in section 4; no disclosure/write | No when gold requires a handoff; otherwise existing in-scope/pass convention |
| Offer/clarification without completed resolution | Nonterminal; not a successful gold resolution | No invented success from turn-limit exhaustion | No |
| Cancellation | `cancelled` | No write | No |

SAR means in-scope, correct terminal automation without handoff; all required
actual actions/targets, readbacks, safety and outcome checks must pass. Preserve
the separately reported workload, in-scope and automation-eligible denominators.
Containment alone is not success. A freeze plus transfer remains escalation.

Readback requirements distinguish `created-case`, `existing-case`, `product`
and `handoff`. `created-state` is the legacy generic verified-state alias and
accepts any of those independently verified persisted states. An alias never
creates a readback without observed evidence. Gold authors should use precise
references for new fixtures. A failed write/readback may lead to safe handoff;
never count a handoff readback as proof of that write's success.

## 3. Handoff reasons, precedence and required sets

`reason_codes` is a deduplicated set encoded as a list. Carry **all applicable,
evidenced reasons**, including supplemental controls/causes, through persistence
and readback. Add optional `primary_reason` to the packet for deterministic
routing. It must occur in `reason_codes`; it does not replace that set. Consumers
may accept additional truthful reasons; gold requires its documented set as a
subset and separately checks actions and routing.

Routing precedence when several reasons apply:
`SEC-01` → `FRD-01` → `ESC-02` → `ESC-03` → `DSP-05` → `DSP-03` →
`DSP-04` → `DATA-01` → `BRD-01` → `DSP-01` → `DSP-07` → `DSP-02` →
`TXN-02` → `ESC-04` → `ESC-01` → `SCOPE-01`.
Control-only `AUTH-02`, `AUTH-03`, and `COM-01` never select a queue.
`SEC-01` requests Seguridad; `FRD-01` requests Fraudes; others request
Quejas y Reclamos. Existing documented language/specialty fallback rules apply.
Any `FRD-01` or `ESC-02` makes priority high even when another reason wins routing.

| Trigger | Minimum required set | Meaning / additional required action |
|---|---|---|
| Fraud/lost-card review | `FRD-01`, `AUTH-02` | OTP is a required control for any freeze; offer freeze only for an eligible owned card; record actual acceptance/decline/result separately |
| Legal/regulatory cue | `ESC-02` | High priority; retain concurrent fraud/distress/human-request reasons |
| Expressed distress | `ESC-03` | Retain `ESC-01` too if a human was explicitly requested; do not infer protected attributes |
| Explicit human request | `ESC-01` | Immediate handoff; no compulsory self-service continuation |
| Amount within inclusive ±5% of USD 1000 | `BRD-01`, `DSP-07` | Use trusted transaction-date FX; no automatic filing |
| Age 85–90 business days inclusive | `BRD-01`, `DSP-01` | No automatic filing |
| Age 91–120 | `DSP-01` | Outside intake; age alone does not add `BRD-01` here |
| Amount above the boundary band | `DSP-07` | No automatic filing |
| Missing/inconsistent intake fields or missing/prior-date FX | `BRD-01` | Name the safe missing/uncertain field; retain a known unsupported-type reason too |
| Database/read dependency failure | `DATA-01`, `COM-01`, `ESC-04` | Safe failure; do not claim an unverified action |
| Tool/action/readback failure | `COM-01`, `ESC-04` | Safe failure with actual attempted/verified action evidence |
| Model outage with unsuccessful deterministic fallback | `COM-01`, `ESC-04` | Safe handoff; successful safe fallback need not transfer solely because a model failed |
| Two unsuccessful clarifications / low confidence | `ESC-04` | No arbitrary selection or fabricated facts |
| Known unsupported adjustment/fee or transfer/deposit | `DSP-03` or `DSP-04` respectively | Preserve applicable `BRD-01`; type determines routing precedence |
| Second cross-customer attempt | `SEC-01`, `AUTH-03` | Section 4 actions; security routing |

A control code is an **obligation**, not evidence it was satisfied. In particular,
`AUTH-02` in a fraud packet does not claim OTP occurred. `actions_taken`, policy
evaluations, verification events and freeze outcome record what actually happened.
Do not pad packets with reasons whose predicates were never established.

## 4. Cross-customer attempts

Attempts to query, disclose or change another person's account/transaction, or
to replace session identity with a chat claim, never reach another customer's
repository scope. Apply this guard before treating a human request as an ordinary
handoff; preserve a structured NLU cross-customer cue as a refusal signal too.

- Every attempt: emit `refuse_request`, persist `log_security_event` with a safe
  category, clear pending proposals/offers, and return `refused_security`.
  No customer rows, document values or model reasoning enter the security log.
- First attempt: session may continue; response policy reasons are `AUTH-03`
  and `SEC-01`. No security handoff or session termination is required yet.
- Second attempt in the **same authenticated session**, including after a worker
  restart: also persist and independently read back a security handoff, emit
  `end_session`, revoke the session, and return `session_ended=true`. Packet
  reasons contain both `SEC-01` and `AUTH-03`; outcome remains `refused_security`.
- Subsequent protected requests fail authentication. Already committed handoff
  verification uses the server's original trusted scope, never a new token or
  authority derived from the attempted identity. Both systems use this contract.

## 5. Age convention and worked boundary

As in [ADR-0006](../../docs/adr/0006-bank-clock.md), `process_date` is the bank
business date. The simulated clock denotes the end of a completed business day:

```text
business_date = (BANK_CLOCK - 6 hours - 1 microsecond).date()
age_days = (business_date - process_date).days
```

For `BANK_CLOCK = 2026-06-18T06:00:00Z`, the anchor is **2026-06-17**.
The following are fresh arithmetic examples, not suite rows:

| process_date | Age | Dispute decision with otherwise eligible facts |
|---|---:|---|
| 2026-03-25 | 84 | May propose; confirmation/OTP/readback still required |
| 2026-03-24 | 85 | Handoff with `BRD-01` + `DSP-01` |
| 2026-03-19 | 90 | Handoff with `BRD-01` + `DSP-01` |
| 2026-03-18 | 91 | Handoff with `DSP-01` |

Authors calculate `process_date = business_date - intended_age`, never subtract
from `BANK_CLOCK.date()`. Pending age 14 is recent; age 15 is stale (`TXN-02`).
The serving timestamp interval remains half-open and customer date matching may
tolerate ±1 day; neither changes policy age. Calendar/segment attributes must
not alter thresholds.

## 6. Policy rule order

Authorization and ownership are mandatory prerequisites. The engine records all
applicable handoff reasons from facts it can establish, then selects the primary
reason above; it must not lose a cause because an earlier rule returned first.
The following order determines the action; the reason precedence determines
routing if several review causes coexist.

1. Enforce session, ownership and search window. Do not expose out-of-scope facts.
2. Apply security and explicit fraud/legal/distress/human guards. These may
   terminate self-service before transaction selection; only evidenced reasons
   apply. Customer/product restrictions also prevent automatic writes.
3. For an owned existing dispute, return verified status and avoid duplicate
   intake. Unconditional safety restrictions still take precedence.
4. Apply recorded transaction-status rules: recent Pending, Reversed and Declined
   are explanations; stale Pending is `TXN-02`. Unknown/missing status requires
   review, never assumed approval.
5. For an inquiry with sufficient trusted display facts, explain and offer the
   recognition/dispute decision. Missing essential display facts requires review.
6. On dispute review of a known type: Adjustment/fee uses `DSP-03`, Transfer or
   Deposit uses `DSP-04`, other unsupported types use `DSP-02`. **A known
   unsupported type takes precedence over missing/inconsistent intake data for
   routing**, while `BRD-01` is retained whenever that data defect also applies.
   With no trustworthy type, use missing-data review; never guess the type.
7. Check required intake data and FX, then intake age, boundary band and amount
   limit. Collect all applicable reasons; no write when any requires review.
8. Only approved Purchase/Withdrawal/Payment satisfying those checks can reach
   a proposal. Apply `ESC-05` review flag on intake when its complaint threshold
   is met; that flag alone does not require handoff. Confirmation/OTP/ownership
   and policy are rechecked at commit; read back before reporting success.

## 7. Evaluation and access boundary

Dev fixtures and a new pre-fix-frozen confirmation set exercise the contract.
Implementers do not open fresh suite-v3 rows. Independent authors freeze 100
cases (35/20/20/25 category mix), private bindings and manifest before any B1/P
execution; structural checks do not run a system or obtain outputs for gold.
Any claim is labeled **after fixes, fresh suite**, disclosing v2-informed fixes.

Global and slice escalation recall use the same strict correct-handoff predicate
and denominator; missed transfers are its complement. Readback scoring follows
section 2. Preserve official v2 outputs; any corrected saved-v2 slice table is
separately labeled a reporting correction, with no system rerun or new success
claim. Step 3 authorization ends at the dev-gate report. Release and v3 execution
require Sebastian's later go.
