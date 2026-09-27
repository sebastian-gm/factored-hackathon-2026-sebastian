# ADR-0005: Contracted local gold tables

Status: accepted for the local prototype (2026-09-26).

The source is static, synthetic CSV with delivery and schema claims that need verification.
Use immutable bronze objects, content-addressed typed Parquet objects, versioned logical
silver views and dbt DuckDB table materializations with enforced contracts. Export Parquet
after `dbt build` passes. dbt-core is constrained to 1.x and dbt-duckdb to 1.11.0; the lockfile
pins exact versions. External materialization was rejected because it does not inherently
enforce the complete table contract. See the [dbt contract documentation](https://docs.getdbt.com/docs/mesh/govern/model-contracts).

Every admitted source row receives Pandera validation. Full-snapshot keys, foreign keys,
ownership and FX availability are promotion gates. Bad rows remain in private quarantine.
Complaint product ownership fails its field-scoped check, so that link and all complaint
text are excluded from every gold table. This is a restrictive projection, not a waiver
for unsafe joins. Snapshot-scoped failures preserve the last successful gold pointer.

The dictionary's required transcript duration is nullable in observed data (24,029 nulls).
Contract 1.1.0 preserves nulls and emits a warning; duration is not needed for serving or
matcher training. Revisit with corrected source documentation or a consuming requirement.

Local Postgres loads use explicit owner credentials, contract-shaped tables, RLS for the
API role, a transaction, and source-versus-readback row checksums. Backend adapter wiring
and production migrations remain lead-lane work. Revisit the stack when measured freshness
or scale calls for scheduled jobs and a managed lake.
