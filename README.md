# Aclara

Aclara is a synthetic-data demo for Spanish and Brazilian Portuguese charge questions and dispute intake. It is not a real banking service.

## Current layer

Layer 1 is being built as a thin vertical slice: login and OTP, one customer's transaction scope, rules-based understanding, deterministic policy, verified dispute intake, a structured human handoff, a minimal chat page, and a mock-only development harness.

## Local quickstart

1. Copy `.env.example` to `.env` and set local Postgres and demo login passwords. The demo username and password are `DEMO_USERNAME` and `DEMO_PASSWORD`; the UI shows the local simulated OTP after login.
2. Run `make up`.
3. Open <http://localhost:3000>. The page calls the API health endpoint through the compose network.
4. Run `uv sync --extra dev`, then `make checks`.

The dataset pipeline reads `LOCAL_RAW_DIR` and writes organizer-derived files only under the ignored `lake/` directory. Run it locally with `uv run python -m aclara.data.cli build`; do not run it in CI.

## Architecture in 60 seconds

The request follows **Understand → Decide → Act → Verify → Escalate**. Rule-based NLU recognizes ES/PT requests. Session identity scopes every transaction query in the service. A deterministic policy engine decides whether to explain, ask a clarifying question, file an explicitly confirmed dispute, or create a human handoff. A dispute is reported only after a read-back confirms the case exists. `LLM_PROVIDER=mock` is the default; this layer does not make paid model calls.

## Scope and limits

The current local demo uses a project-generated fixture ledger and an in-memory operational store. It is not production identity, core banking, durable case storage, or regulatory policy. See [limitations](docs/limitations.md) and [production readiness](docs/production-readiness.md).
