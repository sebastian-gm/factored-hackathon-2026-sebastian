# Local Postgres recovery rehearsal

Verified with `.venv/bin/python -m scripts.backup_restore` against the existing
local Postgres 16 container. The workstation's host tools are version 14, so the
script uses the matching container's pg_dump/pg_restore.

The rehearsal creates two uniquely named disposable databases and one temporary
non-owner login, migrates the source, and seeds authored API flows. It dumps a
custom-format archive, restores to the empty second database, and compares every
operational table's complete-row SHA-256 before using the restored API.

Observed results:

- All 11 operational tables and their row hashes matched, including 1 case,
  1 card state, 1 handoff, 1 conversation, 4 execution records, 3 turns,
  1 session and 16 audit entries.
- The original bearer session read its case, handoff and execution trace in the
  restored app. Card state also survived.
- All 16 audit entries verified. No-context reads returned zero cases and every
  ops table retained enabled, forced RLS.
- Dump + restore + recovery checks took 1.017 seconds for a 45,882-byte authored
  archive. This tiny-fixture duration is not an RTO claim for real workload size.
- Both disposable databases, temporary login and archive were removed. The
  existing application database was not modified. Aggregate evidence remains in
  ignored `artifacts/recovery/report.json`.

This is a local logical-recovery test. Azure PITR, regional DR, full organizer
volume, restore to a new server/identity environment, retention and scheduled
backup monitoring are not verified. VNet/private access remains production work;
the approved dev PostgreSQL Azure-services firewall exception remains a limitation.
