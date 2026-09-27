# ADR-0013: Durable, isolated operational state

Status: accepted for the restricted dev environment. Date: 2026-09-27.

## Decision

Use Alembic to create `ops.cases`, `card_states`, `handoffs`, `conversations`, `turns`, `execution_records`, `idempotency_keys`, `otp_challenges`, `sessions`, `demo_identities` and `audit_log` in the existing PostgreSQL server. Payloads use typed application adapters and JSONB; every operational primary key includes customer, run and session. The migration owner is `aclara_owner`. The non-owner API login inherits only `aclara_api`; `aclara_ops` is a separate read-only role. Runtime refuses superuser, BYPASSRLS and owner-member logins.

Every table has ENABLE/FORCE RLS, the brief's exact customer predicate, a customer index and an additional restrictive run/session policy. The request opens an explicit transaction, sets all context with bound `set_config(..., true)` calls and takes a session advisory lock. The pool is limited to four connections. Invoker views/functions preserve RLS. Missing context reads zero rows. Tokens are random capabilities with opaque run/session routing prefixes; only their SHA-256 lookup keys are stored. Prefixes alone confer no access. Preauth capabilities are hashed too. OTP remains simulated and short-lived.

Mutable conversation state flushes with the case, idempotency record, redacted turn and execution metadata in one transaction. Commit precedes an independent case/handoff readback. An unavailable database returns an error, never an in-memory success. A fresh app can use a still-valid session to resume a proposal or read its records. New sessions/runs intentionally cannot see prior demo state. Card state storage is implemented and restart-tested; the customer card-freeze action is a separate workflow still to be completed.

Only the database function can append audit rows for the API role. A session lock serializes the chain. The digest is `sha256(previous_hex || canonical_row_utf8)`; canonical rows use PostgreSQL's deterministic JSONB text serialization and include scope, sequence, timestamp and event. Built-in [PostgreSQL 16 SHA-256](https://www.postgresql.org/docs/16/functions-binarystring.html) avoids enabling extensions. The verifier checks scope, contiguous sequence, linkage and digest. API UPDATE/DELETE permissions are absent. Audit events contain action metadata, not prompts, secrets or model thinking.

## Evidence and limits

`python -m scripts.test_postgres` creates and removes an isolated loopback test database. Tests cover tables/views/functions, no context, cross-customer/run/session access, autocommit, reused connections, rollback, concurrent append, forbidden audit edits, tamper detection, restart across OTP/proposal/confirmation/readback, and serving-loader RLS/checksum rollback. CI runs the same command with an ephemeral loopback-only Postgres service.

A privileged database owner could rewrite a whole chain; external signed anchors and independent audit export are future production work. Backups, restore drills, multi-replica load and automatic retention/reset schedules have not been verified. Redaction is pattern-based and not complete semantic PII detection. Organizer ledger serving remains a separate explicit load; the dev API still uses authored fixture ledger data. No cloud data upload or real-model call is introduced.
