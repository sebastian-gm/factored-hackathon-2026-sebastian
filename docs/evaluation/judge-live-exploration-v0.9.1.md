# Judge exploration on live v0.9.1

What this shows: the frozen 30-story exploration against fresh live judge visits.
Result: **partial; 5/9 completed stories coherent**, with 11 fixture gaps.
Limits: this is not a 30-story live score or a repeat of the final evaluation.

The deployed API and web images were verified at
`0f0e12df13e281538d7b25800f56c55da0b8dc0b` (`v0.9.1`). The private operator used
the real model through the web BFF. Profile bindings, matcher thresholds,
expectations, turn order and separate confirmation controls were preserved.
Organizer values and transcripts were kept out of committed evidence.

## Coherence and controls

| Measure | Mock | Live |
| --- | --- | --- |
| Full frozen study | 27/30 | Incomplete |
| Same nine completed stories | 9/9 | 5/9 |
| Completed / partially attempted / unrun bound stories | 30 / 0 / 0 | 9 / 1 / 9 |
| Stories unavailable on the configured live profiles | 0 | 11 |
| Verified turns / passing turns | 109 / 103 | 33 / 22 |
| Assertions / passing assertions | 789 / 773 | 202 / 177 |
| Observed financial-write prevention | 100/100 | 30/30 |
| Independent case readbacks | 14/14 | 3/3 |

The live assertions include one verified turn of unfinished JE-18. Its next
turn was dispatched but did not pass the operator's receipt check; it is excluded
from verified-turn and coherence counts. Two cases were filed through separate
confirmation controls. No observed message or cancellation made a financial write.

The mock comparison uses the published [27/30 receipt](judge-language-and-choice-audit.md).
It supplies authored NLU and a small synthetic ledger. Live requests use real
extraction and each profile's full owned ledger. PT retains its configured MX
bank identity, whereas the synthetic PT fixture uses BR. Authored currency
literals were rebound to the referenced live charge before placeholder expansion;
invalid amount/date literals and all behavioral expectations were preserved.
Date corrections used the verified process date. These differences limit direct
comparison; the full mock percentage must not be compared with a fabricated live
30-story percentage.

## Which stories a judge can reproduce

“Unbound” means **unbound on live (fixture prerequisite absent)**.
“Unrun” means its fixture bound in the zero-model audit, but the paid run stopped
before that story. “Partial” means JE-18's first turn was verified.

| Story | Profile | Mock | Live |
| --- | --- | --- | --- |
| JE-01 | mx-es | Pass | Unbound: Pending absent |
| JE-02 | pt | Pass | Unbound: Pending absent |
| JE-03 | ar-es | Pass | Fail |
| JE-04 | pt | Pass | Unbound: Reversed absent |
| JE-05 | co-es | Pass | Fail |
| JE-06 | pt | Pass | Pass |
| JE-07 | mx-es | Pass | Pass |
| JE-08 | pt | Fail | Unbound: suitable second Approved explanation absent |
| JE-09 | ar-es | Pass | Unbound: same-merchant pair absent |
| JE-10 | pt | Pass | Unbound: same-merchant pair absent |
| JE-11 | co-es | Pass | Pass |
| JE-12 | pt | Pass | Pass |
| JE-13 | mx-es | Pass | Fail |
| JE-14 | pt | Pass | Unbound: same-merchant pair absent |
| JE-15 | ar-es | Pass | Pass |
| JE-16 | pt | Fail | Unbound: Pending absent |
| JE-17 | co-es | Pass | Fail |
| JE-18 | pt | Pass | Partial |
| JE-19 | mx-es | Pass | Unrun |
| JE-20 | pt | Pass | Unrun |
| JE-21 | ar-es | Pass | Unrun |
| JE-22 | pt | Pass | Unrun |
| JE-23 | co-es | Pass | Unrun |
| JE-24 | pt | Pass | Unbound: same-merchant pair absent |
| JE-25 | mx-es | Pass | Unrun |
| JE-26 | pt | Pass | Unrun |
| JE-27 | ar-es | Pass | Unrun |
| JE-28 | pt | Fail | Unbound: Pending absent |
| JE-29 | co-es | Pass | Unrun |
| JE-30 | pt | Pass | Unbound: two distinct eligible targets absent |

JE-08's second inquiry permits an ordinary non-Purchase Approved charge; it still
lacked a distinct safe merchant and ordinary explanation on the PT profile.
No profile binding was changed and no substitute transaction was invented.

## Findings a judge would notice

- **Fixture coverage:** the PT profile cannot reproduce pending/reversed stories,
  the two-candidate stories or the two-target recovery story. These are visible
  coverage gaps, including mock failures JE-08, JE-16 and JE-28.
- **Selection interrupts merchant-only stories:** JE-03, JE-05 and JE-17 requested
  a choice instead of identifying the named charge immediately. Later authored
  follow-ups did not complete their intended flow. No prior positive selection
  had been established; preserving a choice is safe. Thresholds were not lowered.
- **A proposal loses its dispute intent on target correction:** JE-13 identified
  the corrected charge but answered with an explanation. Confirmation then
  returned 409 and status correctly found no case. ES/PT zero-model regressions
  reproduce this when the correction is extracted as an inquiry. This warrants
  a context fix while retaining a new proposal and separate confirmation.
- **Overlong-message errors:** offline source review found the BFF reports its
  own message-validation failure as 502 rather than 422. JE-29 was not reached;
  this is an offline finding, not a live observation. The frontend lane owns
  the proposed correction.

## Model extraction versus product context

Only normalized NLU intent, recognition, unfamiliarity, language, trusted country,
clarification and degraded flags are retained. Raw parsed model JSON, per-turn
slots and confidence were not persisted. Latest cumulative conversation slots
cannot establish each historical extraction. New tests replay the observed enums
and flags; reconstructed confidence and synthetic slots are labeled as such.

| Failure | Observed extraction and matching | Classification and response |
| --- | --- | --- |
| JE-03 | Inquiry, unfamiliar false; MATCH chooses, top 0.704 / exists 0.847. The later status question invokes no NLU. | Opening needs a safe explicit choice. Later question loses pending-choice context: product fix #185. |
| JE-05 | Inquiry, unfamiliar true; MATCH chooses at the same probabilities. Recognition invokes no NLU. | Same normalized opening as mock; later recognition is wrongly treated as out of scope: product fix #185. |
| JE-13 | Correction normalizes to inquiry, whereas mock supplied dispute. MATCH identifies the replacement, top 0.909 / exists 1.000. | Real extraction difference exposes lost pending intent: product fix #180. |
| JE-17 | Inquiry, unfamiliar true; MATCH chooses. Weather and the later return invoke no NLU; choices remain available. | No positive charge selection was made. Requiring a choice is safe; keep thresholds and confirmation guards. Raw slot differences cannot be established. |

[Candidate-context PR #185](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/185)
keeps owned choices visible on short questions and recognition, without selecting,
consuming another clarification round or invoking NLU. Explicit recognition
clears unfamiliarity. Twenty-four ES/PT regressions cover later selection and
safety precedence; the corrected combined tree passed 183 targeted regressions.
It depends on #180 and requires the same authorized cross-lane API lead review.

## Frontend owner-tour evidence: separate from judge visits

The owner supplied 12 charge-story references (14 execution records). These are
owner-network personas, not fresh judge visits, and are excluded from the 5/9
judge score and AI-lane cost. The tour replaces the quickstarter draft with a
scoped charge draft before sending; it does not test the exact generic starter.

Both ES explanation stories normalize to Spanish inquiry, no unfamiliarity,
no clarification and no degradation, then clarify before MATCH. Non-owner scoped
aggregate checks confirm one NLU event per conversation and no unknown execution
history. Normalized amount, currency and date match the retained input; the
merchant is the missing-display placeholder, not an authored fixture name.

The owner explicitly approved aggregate ledger consistency checks. In the stable
current promoted snapshot, each ES scope has four owned rows. Amount matches one,
currency four, raw merchant zero, process date zero and displayed transaction
date one. Amount + currency + displayed date identify one row whose bank merchant
is absent; its safe display label equals the supplied placeholder. The pre-MATCH
consistency guard instead compares raw merchant wording and process date, so
both contradict this input. A date-only change would leave the merchant failure.
Historical snapshot equality was not retained and is not claimed. Raw parsed
model JSON and confidence remain unavailable.

The inputs were not the generic starter templates. The preserved tour helper's
date-free draft does not establish complete runtime input: the retained input
contains an ISO date, and its normalized one-day window matches that date. An
invented-date or date-parse-error diagnosis is unsupported.

Both PT explanation stories normalize to Portuguese inquiry with trusted MX
country, no unfamiliarity, no clarification and no degradation. MATCH identifies
one charge (top 0.9855 / exists 0.9888), then policy requires a human because
`missing:merchant_name` triggers `BRD-01`. Ownership, customer/product status,
fraud, FX and temporal metadata pass. This is a correct missing-data policy guard,
not a language, low-confidence or model-requested handoff. The tour's truthy
merchant test admits the display placeholder `—`; use a real merchant for its
explanation story. Do not invent a merchant or relax policy.

Source review separately confirms the shipped generic quickstarters provide no
merchant, amount, currency or date. A localized draft bound at runtime to an owned
Approved Purchase with a real merchant gives the opening story useful evidence;
keep explicit Send and let normal matching/policy decide its response. The
frontend lane owns that patch; no judge-profile binding is changed. The ignored
`artifacts/judge-exploration/owned-charge-starter-frontend-proposed.patch`
contains the concrete implementation and ES/PT regressions. TypeScript, ESLint
and 46 actual-source hook/API mock checks pass; six browser regressions remain
for w8 to run. The existing paid tour still overrides the starter, so it must not
be cited as a measurement of the new first click. No live rerun is authorized.

## Three fixes to prioritize before the video

1. **Make the first charge story use complete owned facts.** Apply the frontend
   starter proposal in w8's lane; exclude missing merchant displays and avoid
   adding a date that the UI cannot bind to the matcher's process-date contract.
   Normalize the em-dash placeholder as absent in the AI lane. Missing trusted
   data must still produce a policy handoff, never an invented explanation.
2. **Keep a dispute when its target is corrected.** Ship #180 with the lead's
   punctuation-free ES/PT read-question correction. A real inquiry still explains;
   a valid correction needs a fresh proposal and separate confirmation.
3. **Keep pending choices visible on follow-ups.** Ship #185 after #180 so short
   questions and recognition stay in the banking conversation. Explicit choice
   and all security/human-handoff controls remain required.

These are offline verified changes/proposals, not evidence of a repaired live
video opener. The frontend browser checks and lead release remain outstanding.

## Stops and cost

The first attempt stopped after two completed stories because the operator
incorrectly required the customer role. Configured MX/PT judge personas retain
trusted ops roles. Four fresh zero-model visits verified the corrected guard.
The owner then explicitly approved untouched stories only; neither completed
story was replayed, and no reservation or budget was reset.

The continuation stopped at JE-18's second turn. The operator compared an API
handoff with the BFF's smaller public handoff schema. A synthetic mock API plus
the actual local Zod parser reproduced that operator defect without paid calls.
It is not evidence of a broken product handoff.

The owner approved one final attempt for only JE-19/20/21/22/23/25/26/27/29.
Its deployment preflight found both images at `f9d1796`, rather than the approved
`0f0e12d`. It stopped before any application HTTP call, model call or reservation.
The final-stop instruction applies: no retry and all nine remain unrun. Historical
journals are byte-identical and the cost totals below were independently read
back after the stop. This is an operator/source-binding stop, not a product score.

| AI scope `go-live/2026-10-03/ai` | USD |
| --- | ---: |
| Approved lifetime cap | 0.30000000 |
| Verified own-call cost, 16 model calls | 0.03126800 |
| Retained maximum for one unverifiable turn | 0.06303700 |
| Durable charged exposure | **0.09430500** |

All application HTTP calls were reserved before dispatch. Known costs were
settled from independently read records in the authenticated judge scope;
one unknown reservation remains held. Production key and account balances were
checked privately before and after each paid segment. Their shared deltas were
not used to attribute lane cost. Private receipts remain under ignored artifacts;
only aggregates and project-generated test fixtures belong in Git.

## Offline fixes and review

[Operator controls PR #179](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/179)
checks trusted judge identity and permits only the source-proven BFF handoff
projection. All 61 pure regressions pass; full API comparison remains exact.
This correction neither settles the unknown reservation nor authorizes a paid retry.

[Product fix PR #180](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/180)
retains pending dispute intent for an explicit, grounded ES/PT target correction.
Thirty-two new regressions and 329 existing regressions pass, including the
lead-reported punctuation-free ES/PT read questions. A fresh proposal and
separate confirmation are required; stale hashes, textual assent, ordinary
questions, cancellation and safety routes remain protected. The API cross-lane
edit is explicitly authorized and requires lead review.

The unchanged frozen mock suite remains **27/30**, with the same JE-08/16/28
failures. All 100 no-write, 109 zero-spend, 14 case-readback and 7 handoff-readback
checks pass. Final B1 v2 remains **32/32**. No threshold or expectation changed.
The original mock extraction already labeled JE-13's correction as a dispute;
the new regressions exercise the live inquiry extraction that exposed the bug.

The proposed frontend patch is retained under ignored local artifacts for its
owning lane. Twenty mocked route checks and TypeScript checks pass; four ES/PT
browser regressions are proposed but unrun. It changes invalid message errors
to 422 while preserving upstream 502 errors and the API's Unicode character limit.

These results were measured after the final evaluation. Official v4 numbers are
unchanged. Product fixes require lead review, green CI and the lead's merge order;
this report does not claim a live rerun of any fix.
