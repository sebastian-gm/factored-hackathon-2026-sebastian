# 2026-10-03 — Judge conversation exploration

## Completed (verified)

- Authored 30 synthetic ES/PT conversations, 109 turns and all handoff 19 topics. Actual mock API ran with scoped in-memory stores, code-owned matching/confirmation and independent receipt reads; all 93 supplied NLU observations validate.
- Final unchanged-base run met all goals in 15/30 conversations (ES 9/15, PT 6/15), 75/109 turns and 727/798 assertions. All 100 no-write, 109 zero-spend, 12 case-readback and 21 handoff-readback checks passed. Reviewed every conversation and reported five UX weaknesses with authoring/scope-policy limits.
- Preserved original six-row setup and corrected runs. Earlier 14/30 versus later 15/30 was caused only by the random latest-case bug, not an improvement. Authorized minimal API fix and deterministic mock regressions are separately held in PR #161 for lead review; full fixed run 15/30. Official v4 unchanged; no paid calls or cloud writes.
- Private final artifacts have source hashes, mode 0600 and read-back verification. Live, overwrite and outside-artifact guards verified. The standalone sandbox thread issue was isolated without app code; mock execution outside it completed normally.

## Done but not verified

- Remote CI pending. Live model/judge-browser coherence untested; remaining UX findings are open.
- Item 6 is complete in held PR #159. Its first web gate failed the existing phone-choice viewport check (170/171 passed); unchanged-head rerun is pending. Original failure retained.

## Next / blocked

- Hold all PRs unmerged until Sebastian lifts the v0.9.0 / Gate A–B release hold; lead reviews the cross-lane API fix. Keep remote gates green.
- Live suite and adapter await the explicit judge-access signal, scoped masked bindings, a separate durable $0.30 cap and private before/after balances.
