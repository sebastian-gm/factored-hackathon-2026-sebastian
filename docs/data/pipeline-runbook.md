# Data/ML lane reproduction and integration

Install with `uv sync --extra dev --extra data-ml`. The only shared-file changes in this lane
are the optional dependencies, NumPy in the dev extra for typing, lockfile, and mypy
handling of absent optional ML packages.
The dependency group pins dbt-duckdb 1.11.0 and constrains dbt-core to 1.x.

Set LOCAL_RAW_DIR, the shared external LAKE_DIR, and BANK_CLOCK in the ignored `.env`.
Each worktree needs its own COMPOSE_PROJECT_NAME and `POSTGRES_HOST_PORT`, `API_HOST_PORT`,
and `WEB_HOST_PORT`. Keep LLM_PROVIDER=mock. No command below calls an LLM.
Set LAKE_DIR explicitly for every entry point. This run retained the existing shared
`/tmp/aclara-shared-lake`; the lead's newer persistent default does not move existing data.

```bash
uv run --extra data-ml python -m aclara.data.cli build
uv run --extra data-ml python analysis/problem_analysis.py
uv run --extra data-ml python -m aclara.data.cli serve-load
uv run --extra data-ml python -m aclara.ml.charge_matcher.train --version v1 --trials 30
uv run --extra data-ml pytest tests/test_data_pipeline.py tests/test_charge_matcher.py
```

Serving requires an owner DSN supplied as DATA_LOAD_DSN; never echo it or put it on the
command line. The integration test uses TEST_DATA_LOAD_DSN and a separate fixture database.
`tests/test_serving_load.py` verifies an idempotent load, full row read-back, RLS on tables
and a security-invoker view, no context, autocommit, reused connection, and transaction rollback.
Base CI skips optional dbt/ML tests when their extras are absent; they must also be run locally
with the data-ml extra before merge. No organizer data is required by tests.

The lake `_meta/current.json` is the atomic consumer interface: dataset version, bank clock,
build fingerprint, DuckDB database, gold directory, aggregate report and manifest. Gold and
serving contract YAML files describe each projection. `contracts/interfaces/` is unchanged.
Gold transaction facts preserve the frozen fields and add the required lineage columns.
`gold.transactions` is the 120-day serving projection, with separate recomputed USD, FX date,
fallback and foreign-country flags, plus an internal fraud score. `is_fraud` never enters gold.

The backend still uses its existing fixture repository until the lead lane wires these serving
tables and pins the exported matcher in config/models.yaml. This lane does not change identity,
policy, APIs, orchestration or frozen interface definitions. The loader bootstraps local tables;
production migration ownership stays with the lead.

Gold snapshots remain in private run directories; rollback selects an older verified snapshot
and reloads it transactionally. No source or quarantine rows, dbt debug logs, MLflow row inputs,
query datasets, or per-query predictions should enter Git or CI artifacts. dbt telemetry is off;
MLflow points explicitly to a local file store. Source contracts, generated fixtures, aggregate
reports and row-free model parameters are the reviewable outputs.

## Spanish recollection sheet

The private review packet is `artifacts/human-validation/spanish-40/cards.md`, with a
blank UTF-8 CSV at `artifacts/human-validation/spanish-40/recollections.csv`. It contains
exactly 40 unique customers excluded from all synthetic benchmark splits (14 MX, 13 CO,
13 AR). The separate private references file preserves the transaction mapping. Write
the recollection and optional notes in the blank CSV columns; do not commit the packet.
`analysis/prepare_spanish_cards.py` creates this packet and refuses to overwrite it.

The first 40 Spanish recollections are pending Sebastian's writing. Portuguese generation
and a second-vendor cross-check remain a later, explicitly labeled model-generated set;
no language validation is inferred from the normalized-slot synthetic benchmark.
