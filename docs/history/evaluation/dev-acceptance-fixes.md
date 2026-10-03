# Handoff 08: independent development fixes

The only diagnostic input used for these changes is the [aggregate taxonomy](../../evaluation/run01-failure-taxonomy.json).
The reducer reads saved scored observations and emits counts; no frozen utterance,
transaction, scenario ID or per-case trace was opened for diagnosis. Every access is
recorded in the [access ledger](test-access-log.md). Frozen labels and run-01 results
remain unchanged. No additional full held-out run has been used.

## Failure taxonomy

B1 and P/mock have identical counts (do not pool them as independent samples):

| Pattern | Count per system | Rules / category / language |
|---|---:|---|
| Forbidden dispute write | 6 | ESC-04; ambiguous/unsupported 4, human-required 2; ES 2, PT 4; observed outcome dispute_filed |
| Missing required handoff | 12 | ESC-04 6, BRD-01 4, DSP-01 5, SCOPE-01 1 (rules overlap); ES 4, PT 7, mixed 1 |
| Required packet incomplete | 54 | All 54 lack 11 fields listed in the JSON; field coverage is distinct from useful content |
| Outcome mismatch | 93 | Includes 49 out-of-scope abstentions, 8 filed disputes, 25 transfers, 2 refusals and 9 explanations |
| Missing required action | 82 | Includes 31 explanations, 19 security events, 17 readbacks, 15 filings and 14 refusals; action counts overlap |
| Explicit route mismatch | 4 | Two fee and two fraud paths; ES 2 / PT 2; each abstained out of scope |

These counts locate failure families, not the exact causes of individual frozen
cases. The association between a code defect and any particular held-out failure
is unproven until an authorized future run.

## System bugs reproduced on new dev cases

The fixtures use newly authored Taller Prisma / Estudio Nube records and queries.
They derive from the written policy and code paths, not frozen item paraphrases.

1. A singleton scoped ledger was treated as positive identification even with no
   matching facts or a contradictory amount. Matching now intersects supplied
   merchant/amount/currency evidence; absent evidence requires an explicit choice.
2. Ordinals inside a negation or multiple alternatives selected a transaction.
   Selection now requires a complete positive choice. Uncertainty cannot produce
   an action proposal, including through learned matching.
3. Clarification failure could be followed by a new automatic proposal in the same
   conversation. Handoffs now terminate that conversation; two failed clarification
   rounds retain ESC-04. This boundary survives a Postgres-backed process restart.
4. A prior action hash remained valid after another message changed the context,
   and after transaction facts changed under the same record ID. Any new message
   invalidates the prior proposal; confirmation compares the current scoped record
   against the proposed facts before writing.
5. Status questions about an owned, named merchant were rejected as out of scope
   when the short baseline lexicon missed the wording. The orchestrator recognizes
   narrow ES/PT status context as an inquiry, preserving all authorization/matching
   gates. It grants no dispute intent from that inference.
6. Case references were missed outside the original status phrase, and the readback
   guard assumed every existing case still had status `received`. Scoped lookup now
   handles an explicit case reference and verifies the returned persisted status.
7. Packet metadata added after run-01 already covers the missing structural fields.
   Further dev tests found missing useful customer statements and PT preference
   overwritten by a Spanish fallback route. Packets now keep a bounded, masked,
   explicitly unverified statement and the conversation's preferred language.
   Injection/security text and DLP failures are excluded from quoted statements.

`tests/test_dev_acceptance.py`: **32 passed**, including 30 negative/clarification
checks and two positive filing/readback controls. No forbidden writes occurred on
these dev paths. `scripts.test_postgres`: **8 passed**, including terminal-handoff
persistence. `tests/test_dev_resolution.py` covers scoped status questions, packet
readback/redaction, fallback language, currency conflict and existing-case status.
These checks do not establish full language coverage or held-out improvement.

## Harness / adapter bugs

- The initial taxonomy draft counted all 114 observed handoffs as incomplete when
  60 had no required packet fields (`completeness = null`). The reducer now counts
  only the 54 with required fields, with an independent regression test. This does
  not change run-01's SAR, safety counts or original completeness gate.
- The two prior measurement bugs remain documented in run-01: generic created-state
  mapping and explanation target observation. Their correction used saved outputs;
  no new scorer correction or system rerun has been applied in this layer.
- B1 still has two structurally unreachable model-outage boundaries. This is a
  baseline/adapter reachability limitation, not a successful outage exercise.

## Suspected gold-label errors for Sebastian

**None identified from the permitted aggregate evidence.** Structural required-action
versus forbidden-action intersection counts are zero. BRD-01/DSP-01 and outcome
mismatches alone cannot establish a label error: they may reflect wrong intent or
wrong transaction matching. No frozen gold was inspected item by item or edited.
A later authorized label review should check these rule interpretations against
the written policy; any suspicion must retain rule/reasoning and original labels.

## Next diagnostic

Keep the one remaining pre-final diagnostic unused until development fixes and
frontend integration are ready. Real-model evaluation needs priced approval after
the AI lane's round-two dev comparison. Do not claim run-01 numbers improved from
passing these independent dev tests.
