# Frozen evaluation access ledger

Frozen suite inputs, labels and original observations remain unchanged. No row-level
records belong in this log. Local detailed access records stay under ignored
`artifacts/heldout/access-ledger.jsonl`, with purpose, timestamps and input hashes.

| Session | Access | Purpose and scope | System executions |
|---|---|---|---:|
| Handoff 06 | Release validation / binding preflight | Frozen hashes, ownership, partition and overlap checks; private artifact copy authorized by Sebastian. | 0 |
| Handoff 06 | First diagnostic at `564f008` | B1 200, P/mock 200 and two repeats of frozen 100 subset. Prior CLI parse failure occurred before test execution. | 600 |
| Handoff 06 | Measurement correction at `25c1c4f` | Saved observations only; generic created-state and explanation target measurements. Original report retained. | 0 |
| Handoff 08 | Committed aggregate reports | Read headline/slice schema and counts to scope independent dev regressions. | 0 |
| Handoff 08 | Saved scored observations, aggregate reducer | Counts by category, rule, outcome and language; missing action/packet fields and structural label contradictions. No utterance, ID, record or row emitted or inspected. A second reduction corrects the taxonomy to count packet completeness only when fields are required. | 0 |

Handoff 08 permits **at most one additional full diagnostic before final evaluation**,
only after unsafe-write and SAR/handoff fixes pass on independent dev cases. That
additional run has not been used. Reserve it until integration is ready. Real-model
held-out runs require a priced approval after the AI lane's round-two comparison.

Every deliberate future suite/observation access must be logged, including failed
attempts and offline remeasurement. Tests for development iterate exclusively on
authored dev fixtures. Never copy, paraphrase or tune against frozen utterances;
never edit frozen gold. Suspected label issues go to Sebastian for review.
