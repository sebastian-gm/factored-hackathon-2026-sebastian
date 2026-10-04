# AI lane: corrected candidate details

## Completed (verified)

- P candidate replies with corrected dates/amounts use structured NLU, retain dispute intent and re-filter freshly read customer-scoped charges. A uniquely consistent correction uses the existing policy, separate confirmation and receipt readback; contradictory or uncertain details cannot select a charge. No matcher thresholds changed.
- Validate new selection facts against customer text before merging conversation slots. Rejected model-invented details cannot influence a later turn. Currency alone cannot identify a charge after clarification. A missing date alone still allows safe owned choices.
- `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 OPS_BACKEND=memory LEDGER_BACKEND=fixture .venv/bin/pytest tests/test_candidate_corrections.py -q`: 32 ES/PT regressions passed, including ghost-date persistence, competing dates, stale bank facts, confirmation denial and verified receipt identity. Ruff passed; strict mypy passed on 79 source files. Zero model spend.
- Sebastian authorized cross-lane `src/aclara/api/` changes for this task. Lead review required. Post-v4 changes do not revise official v4 results.

## Done but not verified

- Full local suite, remote CI and combined frozen exploration/B1 scores pending. Prior combined context/courtesy score is 25/30; candidate changes have not yet been included in that measurement.
- Real-model understanding, browser behavior and live judge exploration unverified.

## Next / blocked

- Combine the three held fixes locally; measure the unchanged exploration suite against >=26/30 and B1 v2 against 32/32. Preserve every safety/no-write expectation.
- Keep PR unmerged under the v0.9.0 / Gate A–B release hold; live calls await the lead's explicit judge-access signal and approved spend scope.
