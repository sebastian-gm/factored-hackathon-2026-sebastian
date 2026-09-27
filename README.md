# Aclara

Aclara is a synthetic-data demo for Spanish and Brazilian Portuguese charge questions and dispute intake. It is not a real banking service.

## Current layer

Layer 1 and the integration layer have login and simulated OTP, scoped transactions, deterministic policy, confirmed dispute intake with readback, human handoff, and a minimal chat page. B1 uses rules; P integrates structured NLU, guarded response phrasing and a calibrated charge matcher. Postgres stores operational state with customer/run/session isolation and an append-only hash-chained audit log. Verification is recorded in the [progress log](docs/status/progress-log.md).

## Local quickstart

1. Copy `.env.example` to `.env` and set local Postgres and demo login passwords. The demo username and password are `DEMO_USERNAME` and `DEMO_PASSWORD`; the UI shows the local simulated OTP after login.
2. Run `uv sync --extra dev`, then `make up`. This migrates Postgres, creates the non-owner app login and waits for healthy services.
3. Open <http://localhost:3000>. The page calls the API health endpoint through the compose network.
4. Run `make checks` and `uv run --no-sync python -m scripts.local_smoke`.

Run `uv run --no-sync python -m scripts.test_postgres` for isolated database integration tests. For reactive evaluation, use `uv run --no-sync python -m evals.runner --system P --scenarios evals/dev_scenarios_v2.yaml`. See the [harness guide](docs/evaluation/harness.md) for repeats, faults and aggregate outputs.

Each worktree needs a unique `COMPOSE_PROJECT_NAME` and host ports in its ignored `.env`; Compose scopes container names and the Postgres volume by project name. For example, a second worktree can use `COMPOSE_PROJECT_NAME=aclara-ai`, `POSTGRES_HOST_PORT=15433`, `API_HOST_PORT=18001`, and `WEB_HOST_PORT=13001`. The web origin and browser API URL follow the configured ports automatically. All worktrees should share the same persistent `LAKE_DIR` outside this repository (default `~/aclara-lake`; the pipeline expands `~` to the current user's home directory).

The dataset pipeline reads `LOCAL_RAW_DIR` and writes bronze, manifest, and silver outputs to `LAKE_DIR` (outside the checkout; do not run it in CI). Set `LOCAL_RAW_DIR` in `.env`, then run `make pipeline` or `uv run python -m aclara.data.cli build` from the repository root.

## Architecture in 60 seconds

The request follows **Understand → Decide → Act → Verify → Escalate**. Session identity scopes every transaction query. P passes structured slots to the matcher; deterministic code controls policy and writes. A failed or unavailable model falls back to B1. An action is reported only after commit and independent readback. `LLM_PROVIDER=mock` is the default; an unconfigured mock deliberately exercises B1 fallback. The dev suite is not a real-model quality comparison.

Operational writes use a non-owner Postgres role, forced RLS, explicit transactions and scoped connection context. The [persistence ADR](docs/adr/0013-durable-operations.md) describes restart behavior and audit verification. The generated [policy catalog](docs/policy-catalog.md) distinguishes implemented rules from partial or planned coverage.

The lane contracts and ownership rules are in [the interface map](docs/interfaces.md) and [AGENTS.md](AGENTS.md).

## Scope and limits

The local and Azure demos use a project-generated fixture ledger and durable Postgres operational storage. Organizer gold/serving data remains local and is not yet bound to the chat API. Identity and OTP are simulated; card freeze, some policy rules and held-out model evaluation remain unfinished. Azure access requires the owner's allowed IP and app login. See [limitations](docs/limitations.md) and [production readiness](docs/production-readiness.md).
