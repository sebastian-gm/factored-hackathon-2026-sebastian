# AI lane: corrected candidate details

## Completed (verified)

- P candidate replies with corrected dates/amounts use structured NLU, retain dispute intent and re-filter freshly read customer-scoped charges. A uniquely consistent correction uses the existing policy, separate confirmation and receipt readback; contradictory or uncertain details cannot select a charge. No matcher thresholds changed.
- Validate new selection facts against customer text before merging conversation slots. Rejected model-invented details cannot influence a later turn. Currency alone cannot identify a charge after clarification. A missing date alone still allows safe owned choices.
- Candidate regressions: 34 ES/PT cases pass, including ghost-date persistence, competing dates with/without uncertainty words, stale bank facts, confirmation denial and verified receipt identity. Reject competing dates before merging slots. Ruff passed; strict mypy passed on 79 source files. Zero model spend.
- Combined held fixes: `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 OPS_BACKEND=memory LEDGER_BACKEND=fixture .venv/bin/pytest -o addopts='' -q`: 1,710 passed, 43 skipped. All 75 new ES/PT context/courtesy/correction regressions pass.
- Hash-verified frozen exploration: 27/30 (103/109 turns, 772/789 checks), ES 15/15 and PT 12/15. All 100 no-write, 109 zero-spend, 14 case and 7 handoff readbacks pass. B1 v2 remains 32/32. Independent review confirmed hashes, unchanged expectations and matcher checksums. [Aggregate report and remaining JE-08/16/28 failures](../../evaluation/judge-conversation-improvements.md).
- Sebastian authorized cross-lane `src/aclara/api/` changes for this task. Lead review required. Post-v4 changes do not revise official v4 results.

## Done but not verified

- Latest remote CI is blocked before setup by the exhausted GitHub Actions budget; no retry pushes or budget/visibility changes. Courtesy #169's earlier four green gates remain verified. Skipped infrastructure tests and lead review remain unverified.
- Real-model understanding, browser behavior and live judge exploration unverified.

## Next / blocked

- Lead reviews cross-lane API edits and shared conversation seams in #166/#169/#170. Batch the final date guard, tests and aggregate report; rerun remote CI only after the lead says access is restored. Remaining workflow failures are conservative matching/selection and JE-28's missing-case/language cascade; no UX/control failures.
- Keep PR unmerged under the v0.9.0 / Gate A–B release hold; live calls await the lead's explicit judge-access signal and approved spend scope.
