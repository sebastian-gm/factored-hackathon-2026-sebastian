# Saved live failures: post-v4, final build

The v0.9.1 exploration completed nine stories, five coherent. This audit uses
only the saved execution metadata; it makes no new live or provider calls.
It does not change official v4 numbers or claim a new live score.

| Live failure | Evidence and classification | Code response |
| --- | --- | --- |
| JE-03 | Opening NLU is inquiry, unfamiliar false. MATCH chooses three candidates at top 0.704 / exists 0.847. The short status question and repeated merchant status request invoke no NLU. These later failures are product/context bugs. | #185 keeps choices on the short question. The final-day fix accepts a literal, positive status request naming exactly one current owned candidate as an explicit choice and explains it. |
| JE-05 | Opening NLU is inquiry, unfamiliar true. MATCH chooses at the same probabilities. Recognition invokes no NLU and becomes out of scope: a product/context bug. | #185 retains choices and clears unfamiliarity; later explicit selection explains the charge. |
| JE-13 | The real correction normalizes to inquiry; the mock supplied dispute. MATCH identifies the replacement at top 0.909 / exists 1.000. This extraction difference exposes a product bug in pending action context. The later 409/no-case replies follow from the absent proposal. | #180 preserves dispute intent for a positive target correction, creates a new proposal and requires separate confirmation. Explicit read questions, including questions without question marks, still explain. |
| JE-17 | Opening NLU is inquiry, unfamiliar true. MATCH chooses. The weather request and return-to-dispute request invoke no NLU. No charge was positively selected. | Continue to require an explicit choice; an unbound cancellation cannot invent a proposal. No matching threshold or confirmation control is weakened. |

The opening choices in JE-03/05/17 are policy-safe given the retained MATCH
result. Their normalized NLU flags agree with the authored mock observations.
Historical raw JSON, per-turn slots and confidence were not retained, so a
raw extraction difference or a unique historical merchant match cannot be
established. Later cumulative slots cannot fill that evidence gap.

## Literal merchant choice

The repeated JE-03 request names the merchant while choices are already shown.
The existing ordinal-only parser ignores it. The fix checks literal full-name
word boundaries against the entire current authorized ledger, requires exactly
one match also present in the retained list, and verifies unchanged record
identity before using the normal policy decision. Duplicate names outside the
displayed three also prevent selection. Read wording clears pending dispute
intent and unfamiliarity; standalone positive selection preserves the usual flow.

Negation, uncertainty, alternatives, unrelated clauses and new amount/date
details do not resolve a name. Existing security, human, fraud, cross-customer,
NLU confidence and degraded-mode guards run first. No extra model call or write
is required to resolve the choice. Financial actions still need a valid separate
confirmation.

The regression replays the retained inquiry/unfamiliar flags, absence of a later
NLU call, and exact MATCH action/probabilities. Confidence, slots, names, rows
and PT variants are explicitly authored reconstructions. Disabling the resolver
reproduces four failing repeated-name cases; enabling it passes all 40 new cases.
The combined candidate/context/security/starter/language group passes 215 tests.
Ruff and strict mypy pass. Frozen exploration remains 27/30 (JE-08/16/28 require
safe choices); all 100 no-write, 109 zero-spend, 14 case and 7 handoff readbacks
pass. B1 v2 remains 32/32. New model spend is $0.

The next measurement is the owner's newly approved single live rerun after the
lead deploys these fixes and supplies its exact SHA and new durable AI scope.
Its cap is $0.40 within the approved $18 cumulative ceiling. Preserve the old
partial run, fixture gaps and unknown reservation; use fresh judge visits.
