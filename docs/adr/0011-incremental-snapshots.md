# ADR-0011: Incremental objects and atomic snapshots

Status: accepted for the local prototype (2026-09-26).

Streaming is unnecessary for a static source and a business-day freshness target. Diff every
source checksum, including the last seven days and older objects, to detect late arrivals,
restatements and removals. A dataset version hashes the scoped source inventory. Contract,
transformation and clock changes have a separate build identity.

Bronze reuse is byte-identical and immutable. Silver transformations are cached per source
object, contract and conversion code; snapshot views supply the current dataset version.
Their five lineage columns are persisted in gold. Unchanged transformations are reused,
while gold tables rebuild as one tested snapshot. This accepts extra gold work for a simpler
atomic publication mechanism; there is no claim of partition-incremental dbt execution.

A lake file lock serializes builds. Only after DQ, dbt contracts, tests and export read-back
succeed does an atomic JSON pointer switch consumers to the new snapshot. Old runs remain
available for rollback. Postgres reloads in one transaction and records the same identity;
its read-back verifies every projected row. Freshness is change detection to gold promotion;
serving completion is recorded separately, not confused with source wall-clock freshness.

The labeled fixture proves additions, late data, restatement, new columns, invalid rows,
duplicates, removal, failed promotion, clock-only changes and idempotence. No comparison
against an older organizer copy is claimed. Revisit with a partitioned warehouse when measured
load time makes full downstream builds too costly.
