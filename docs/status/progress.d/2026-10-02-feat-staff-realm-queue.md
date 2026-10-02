# 2026-10-02 — Explicit staff realm queue (AI lane, handoff 17 item 6)

## Completed (verified)

- Added masked realm publication, customer-issued short-lived invitations, separately authenticated staff membership, audited idempotent claims and read-back. Customer/root logout revokes delegation; separate judge visits stay isolated.
- Cross-lane staff.py/handoff backend/contracts/OpenAPI/migration/test-runner changes are called out in PR #138 for lead security review. No edits to agent/ai.py or llm/client.py.
- Authored tests cover packet refresh preserving claim state, digit-only masked IDs, roles, realm isolation, replay, logout and PostgreSQL FORCE-RLS/claim races.
- Prior head d3ec093 passed all four remote gates, including 80 Postgres tests. Full local checks: 1,348 passed / 38 DB skips, B1 32/32; targeted routing/freeze/evaluation/queue regressions pass. Local PG14 cannot apply the pre-existing PG15+ security_invoker baseline; disposable server was stopped, and actual migration verification came from remote PG16.
- Item 7 completed in #142: real dev 34/36 versus 32/36, $0.0538905 from its own durable scope. PT guard fix #143 and separately preregistered stress study #144 are open; official v4 is unchanged.

## Done but not verified

- Moving this legacy entry out of progress-log and refreshing the branch from main; final-head local/remote checks pending.
- Lead security approval, live migration, staff UI integration and deployment remain pending.

## Next / blocked

- Merge hold until the lead lands #137 then #140 and announces clearance. Queue requires lead security approval and all final-head gates.
- Human agreement awaits Sebastian's exported v4 CSV.
