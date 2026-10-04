# 2026-10-03 — Courtesy and scope recovery

## Completed (verified)

- User-authorized P conversation/API changes keep whole-message ES/PT greetings, thanks and small talk friendly and open. These turns preserve decisions and never confirm an action. NLG retains code-approved courtesy text with unchanged privacy checks.
- Genuine out-of-scope requests offer a person without making the chat terminal. Active charge/offer/choice context is retained; unrelated requests invalidate pending proposals. Optional scoped packets are reused, including after restart; explicit human requests promote the same packet to a terminal handoff. Security, fraud, legal, bounded ambiguity and real handoff behavior remain protected.
- Combined with the context fix, unchanged exploration is 25/30 (98/109 turns): all 100 no-write and 109 mock/zero-spend checks pass, plus 14 case and 8 handoff reads. Matching thresholds and authored expectations unchanged. Twenty-nine ES/PT courtesy regressions pass; affected suites before the two restart additions passed 252 tests. Existing NLG tests: 93 passed. B1 v2: 32/32. Ruff/mypy passed; $0 spend.

## Done but not verified

- Remote CI and lead review pending. Live behavior untested; target >=26/30 awaits candidate correction.

## Next / blocked

- Keep this separate cross-lane PR held until Sebastian lifts the release hold. Lead reviews optional serialized conversation state and soft scope semantics.
- Finish candidate date/amount correction and report the final score and remaining failures; judge-access signal still required before live runs.
