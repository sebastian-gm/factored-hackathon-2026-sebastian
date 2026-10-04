# 2026-10-03 — Scoped conversation follow-ups

## Completed (verified)

- Sebastian authorized cross-lane API conversation edits, separate small PRs and lead review, with the release hold continuing. Main-targeted held PR #166 includes the already-audited latest-case fix #161 so the existing required CI runs.
- P answers short ES/PT why/next-step/timing questions from a freshly read selected charge, pending proposal or saved case. Informational turns retain the exact proposal hash/expiry and cannot confirm it. Everyday case questions use the shared status detector and independently verified receipt path; simulated response timing comes from COM-01, with no refund/date promise.
- Unchanged exploration inputs rose from 15/30 to 20/30 (86/109 turns). All 100 no-write and 109 mock/zero-spend checks passed; 13 case and 19 handoff reads passed. Matching thresholds and authored expectations unchanged. New ES/PT regressions and existing affected safety suites: 225 passed. B1 v2 remains 32/32. Ruff and strict mypy passed; $0 spend.
- Earlier held evidence PRs #159/#162 and latest-case PR #161 have all four remote gates green. All remain unmerged; no deployment, publication or live calls.

## Done but not verified

- New fix PR remote CI and lead review pending. Live behavior remains untested; mock target >=26/30 is not yet met.

## Next / blocked

- Finish P courtesy/nonterminal scope and candidate date/amount corrections in separate held PRs, each with ES/PT regressions. Report the unchanged suite score and remaining failures.
- Wait for explicit release-hold lift before merging, and judge-access signal before live runs.
