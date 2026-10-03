# 2026-10-02 — Explicit staff realm queue (AI lane, handoff 17 item 6)

## Completed (verified)

- Added masked realm publication, customer-issued short-lived invitations, separately authenticated staff membership, audited idempotent claims and read-back. Customer/root logout revokes delegation; separate judge visits stay isolated.
- Cross-lane staff.py/handoff backend/contracts/OpenAPI/migration/test-runner changes are called out in PR #138 for lead security review. No edits to agent/ai.py or llm/client.py.
- Authored tests cover packet refresh preserving claim state, digit-only masked IDs, roles, realm isolation, replay, logout and PostgreSQL FORCE-RLS/claim races.
- Prior head d3ec093 passed all four remote gates, including 80 Postgres tests. Full local checks: 1,348 passed / 38 DB skips, B1 32/32; targeted routing/freeze/evaluation/queue regressions pass. Local PG14 cannot apply the pre-existing PG15+ security_invoker baseline; disposable server was stopped, and actual migration verification came from remote PG16.
- Item 7 completed and merged in #142: real dev 34/36 versus 32/36, $0.0538905 from its own durable scope. PT guard fix #143 and separately preregistered stress study #144 are merged; official v4 is unchanged.
- Lead security review reproduced ten delegated-access failures before the correction. Source validation now reuses current JudgeSessions.validate on the trusted stored controller/current child digest; OFF/password/config/dataset changes fail closed, including cached claim replay and stale invitations. Same-visit profile switching stays valid.
- All 13 new replay/positive controls pass locally, alongside queue/judge-profile tests (42 total). Final full mock checks: 1,395 passed / 40 DB skips, strict typing and policy checks passed, B1 32/32. No paid model calls for the correction.

## Done but not verified

- Refreshed branch through merged #137/#140 and #142/#143/#144; shared progress-log diff removed. Frontend #145, merged into the queue branch, is preserved.
- The final-head remote gates, including replay of the 13 new controls against disposable Postgres, remain pending.
- Lead security approval, live migration, staff UI integration and deployment remain pending.

## Next / blocked

- New v0.8.0 release-window merge hold is active (main pinned a8d9993). Queue requires the lead to re-review the corrected source validity and all final-head gates.
- Human agreement awaits Sebastian's exported v4 CSV.
