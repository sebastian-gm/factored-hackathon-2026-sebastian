# 2026-10-03 — Latest case status correction

## Completed (verified)

- The synthetic judge exploration reproduced a status lookup returning the older of two verified cases. Customer-scoped storage orders random IDs lexically; lookup previously took the last ID instead of the latest creation time.
- Prepared and verified the minimal patch in memory first. Sebastian then explicitly approved the cross-lane API edit in a separate held feature PR, with lead review.
- Status now selects the newest scoped creation timestamp. Explicit case references still select the requested case. Authorization, confirmation, write actions, receipt reads and frozen interfaces are unchanged.
- Added deterministic ES/PT regressions for B1/P, forcing IDs into reverse chronological order while filing through actual confirmed API actions and reading each receipt back. Targeted mock checks: 27 passed, 3 database-dependent skips. No model calls or spend; measured after the final evaluation, with official v4 numbers unchanged.

## Done but not verified

- Remote CI and lead security review pending. No live/deployed verification.

## Next / blocked

- Keep the feature PR unmerged during the lead's v0.9.0 / Gate A–B release hold. Merge only after the hold is explicitly lifted, lead review and green remote CI.
- Continue the separate authored exploration evidence PR; live exploration waits for the judge-access signal and its approved durable $0.30 scope.
