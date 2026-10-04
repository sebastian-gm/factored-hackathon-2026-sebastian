# AI lane: reply language and safe selection audit

## Completed (verified)

- P reply language follows reliable ES/PT customer evidence, ignoring scoped merchant names; uncertain turns retain the conversation language. Candidate selection cannot lock case questions into the previous language. Trusted locale initializes new P chats; B1 behavior remains frozen.
- Confirmation/cancellation/failure use current conversation language while the proposal hash, expiry and source language remain immutable. Replay verifies the same scoped case, changes only reply text, scans the code template and makes no new model call or financial write. Existing machine-readable error details remain intact for the BFF.
- Explicit different-merchant retargets clear prior amount/date slots, including an amount-only identified prior charge. MATCH and confirmation gates remain unchanged.
- New ES/PT/B1 language, replay, restart, retarget and guard regressions: 30 passed. Existing conversation/safety suites: 231 passed. Ruff and strict mypy passed on 79 source files. Mock/fixture/memory only; $0 spent.
- Read-only JE-08/16 audit found no lost positively identified requested charge. Merchant-only requests return two choices below the unchanged 0.9 confidence gate; fresh merchant-only matching still chooses safely. Keep those selections and frozen expectations.
- Sebastian explicitly authorized cross-lane API edits. Lead review required; official v4 results unchanged.

## Done but not verified

- New combined frozen exploration/B1 score, full local suite, remote CI and lead review pending.
- Live-model/browser behavior remains unverified; no live calls.

## Next / blocked

- Measure the full held stack, commit aggregate evidence and batch one substantive feature PR update. No threshold or expectation weakening.
- Keep release hold; wait for the lead's CI-restored and judge-access signals. No budget or repository-visibility changes.
