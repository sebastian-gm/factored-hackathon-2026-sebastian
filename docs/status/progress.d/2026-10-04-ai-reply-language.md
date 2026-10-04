# AI lane: reply language and safe selection audit

## Completed (verified)

- P reply language follows reliable ES/PT customer evidence, ignoring scoped merchant names; uncertain turns retain the conversation language. Candidate selection cannot lock case questions into the previous language. Trusted locale initializes new P chats; B1 behavior remains frozen.
- Confirmation/cancellation/failure use current conversation language while the proposal hash, expiry and source language remain immutable. Replay verifies the same scoped case, changes only reply text, scans the code template and makes no new model call or financial write. Existing machine-readable error details remain intact for the BFF.
- Explicit different-merchant retargets clear prior amount/date slots, including an amount-only identified prior charge. MATCH and confirmation gates remain unchanged.
- New ES/PT/B1 language, replay, restart, retarget and guard regressions: 30 passed. Existing conversation/safety suites: 231 passed. Ruff and strict mypy passed on 79 source files. Mock/fixture/memory only; $0 spent.
- Combined held stack: full local tests 1,740 passed, 43 skipped; B1 v2 32/32. Unchanged exploration 27/30, 103/109 turns, 773/789 checks. All 100 no-write, 109 zero-spend, 14 case and 7 handoff readbacks pass. JE-28's Portuguese status-language check now passes; its unselected new charge still prevents a case. Independent source/frozen-input/readback review passed. [Remaining-choice audit](../../evaluation/judge-language-and-choice-audit.md).
- Read-only JE-08/16 audit found no lost positively identified requested charge. Merchant-only requests return two choices below the unchanged 0.9 confidence gate; fresh merchant-only matching still chooses safely. Keep those selections and frozen expectations.
- Sebastian explicitly authorized cross-lane API edits. Lead review required; official v4 results unchanged.
- Held [PR #174](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/174) was opened before the publication audit hold. Readback verified its exact description, feature head, 719 changed lines, open state and unmerged state. The earlier checks and invariants did not execute because of the Actions budget, as verified in their annotations.
- Sebastian lifted the publication audit hold and authorized pushing local commits and refreshing held branches. GitHub readback confirms the repository is public. The lead retains review and merge order for v0.9.1; no merges or live calls are authorized by this signal.

## Done but not verified

- Refreshed remote CI, skipped infrastructure tests and lead review remain pending. Already-passing current branches need no rerun; budget-blocked current branches may rerun now that CI access is restored.
- Live-model/browser behavior remains unverified; no live calls.

## Next / blocked

- Preserve shared conversation seams when integrating #174 with #166/#169/#170. JE-08/16 choices remain deliberate policy-safe requests; JE-28 now has only the selection/missing-case workflow failures. No threshold or expectation weakening.
- Refresh published older branches with main merges to preserve history under the repository's no-force-push rule; the remaining branches already contain current main. Push the local documentation and verify remote heads and CI. Keep the separate merge hold and wait for judge access. No budget or repository-visibility changes performed by the AI lane.
