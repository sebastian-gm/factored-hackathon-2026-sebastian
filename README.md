# Aclara

Aclara is a synthetic-data demo for Spanish and Brazilian Portuguese charge questions and dispute intake. It is not a real banking service.

## Current layer

Customer Chat, Agent Desk and Ops run against promoted organizer serving data and durable Postgres activity. B1 uses rules; P adds structured NLU, guarded phrasing and the calibrated matcher, with mock fallback by default. See the [progress log](docs/status/progress-log.md) for the checks actually run and [serving runbook](docs/serving-demo.md) for identity/data boundaries.

## Local quickstart

1. Copy `.env.example` to ignored `.env`; set local Postgres/demo passwords and `LOCAL_RAW_DIR`. Use persistent ignored `LAKE_DIR=./lake` in this checkout.
2. Run `uv sync --extra dev --extra data-ml`, `python -m scripts.local_ops`, then `docker compose up -d --wait postgres` and `docker compose run --rm migrate`.
3. Run `python -m aclara.data.cli build --lake lake --no-reports`, then `python -m scripts.load_demo_serving --target local`.
4. Run `make up`, open <http://localhost:3000>, then run `make checks` and `python -m scripts.local_smoke`. Four server-bound personas share the configured demo password; the UI displays simulated OTP.

Organizer inputs are never required for CI. Isolated browser and database tests use authored fixtures. Runtime serving mode fails closed if its promoted dataset, clock or persona bindings are missing; it never falls back to the authored ledger.

Run `uv run --no-sync python -m scripts.test_postgres` for isolated database integration tests. For reactive evaluation, use `uv run --no-sync python -m evals.runner --system P --scenarios evals/dev_scenarios_v2.yaml`. See the [harness guide](docs/evaluation/harness.md) for repeats, faults and aggregate outputs.

Compose project names and host ports are set in ignored `.env`. The default pipeline lake is persistent `~/aclara-lake`; this session uses ignored `./lake` to honor repository-only writes. Source records are read only through `LOCAL_RAW_DIR`. Generated bronze/silver/gold/manifest files and serving reports remain ignored; no organizer rows are CI inputs or artifacts.

## Architecture in 60 seconds

The request follows **Understand → Decide → Act → Verify → Escalate**. Session identity scopes every transaction query. P passes structured slots to the matcher; deterministic code controls policy and writes. A failed or unavailable model falls back to B1. An action is reported only after commit and independent readback. `LLM_PROVIDER=mock` is the default; an unconfigured mock deliberately exercises B1 fallback. The dev suite is not a real-model quality comparison.

Operational writes use a non-owner Postgres role, forced RLS, explicit transactions and scoped connection context. The [persistence ADR](docs/adr/0013-durable-operations.md) describes restart behavior and audit verification. The generated [policy catalog](docs/policy-catalog.md) distinguishes implemented rules from partial or planned coverage.

The lane contracts and ownership rules are in [the interface map](docs/interfaces.md) and [AGENTS.md](AGENTS.md).

## Scope and limits

The organizer dataset is synthetic. Identity/password sharing and OTP are development simulations. Demo Ops identities can use all three surfaces within their own customer/run/session scope; customer identities cannot access staff routes. Real-model comparison, fluent Portuguese review and frozen-suite acceptance remain pending. Azure's web endpoint requires the owner's IP and app login; its API is internal to the Container Apps environment. See [limitations](docs/limitations.md) and [production readiness](docs/production-readiness.md).
