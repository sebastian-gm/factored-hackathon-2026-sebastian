# Post-v4 targeted conversation round

One normalized exact merchant name (or existing fixed MATCH alias) now identifies
one current owned transaction in the 120-day window. Two or more matches still
require a choice, counting the entire window before displaying three. Fuzzy
names, prefixes, competing or negated names, uncertain identity, conflicting
details, degraded NLU and unsafe merchant names cannot use this rule. The NLU
0.6 and MATCH 0.9 gates, policy, authorization and separate confirmation remain
unchanged. B1 keeps its existing route.

JE-11's saved normalized NLU changes from dispute to inquiry. A zero-cost
metadata readback shows its corrected amount replaced 999, the dispute intent
remained, no date was retained and the round count stayed at one. Source flow
therefore points to the intent-confidence gate, rather than a lost correction;
raw confidence was not retained, so no exact value is claimed. NLU previously
received no collection intent on that short correction. It now receives only a
validated pending inquiry/dispute enum, with no old merchant/amount/date or
selected charge. Whether this improves real-model confidence awaits live.

Production NLU is v5.3; the historical v5.1 prompt is archived byte-for-byte for
the existing dev study. The archived v5.2 experiment is unchanged and distinct.
New gate traces expose only low-confidence/clarification metadata, no raw slots.
The operator ceiling includes the new enum under all four possible attempts.

The frozen mock suite is **29/30**, **106/109 turns**, **779/789 checks**.
Remaining JE-28 is an amount-bearing PT-to-ES retarget still requiring MATCH;
it is outside the merchant-only rule and was unbound on live. All **100 no-write**,
**109 zero-spend**, **14 case** and **7 handoff** checks pass. Same live-bound mock
cohort remains **19/19**. B1 v2 stays **32/32**; new model spend is **$0**.

Replays use the saved inquiry/unfamiliar and dispute-to-inquiry flags, plus the
recorded merchant-only MATCH boundary. Raw slots/confidence and PT variants are
authored, because historical raw JSON was not retained. Tests cover ES/PT exact
identity, aliases, duplicates outside the first three, foreign/expired rows,
policy, refusals, separate confirmation/readback, correction context and the
unchanged 0.59/0.6 confidence boundary. Frozen suite assertions and official v4
files are untouched.

Full local mock suite: 2,073 passed, 44 infrastructure skips. Final parser,
reply-language and budget controls: 157 passed. Ruff and strict mypy pass.

The owner approved one further run of the same 19 bound stories, cap **$0.15**,
after the lead deploys this fix and supplies its exact SHA and a new durable
scope/run. Main merges stay held; lead owns review and release. No new paid
calls were made while preparing this change.
