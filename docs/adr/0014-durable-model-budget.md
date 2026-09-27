# ADR 0014: Durable model spending limits

- Status: Accepted for the owner-approved restricted demo
- Date: 2026-09-27

## Context

Handoff 09 authorizes a production OpenRouter key, the selected Gemini route with failure-only Grok fallback, a US$3 daily breaker and at most five smoke conversations costing at most US$0.10. Process-local counters cannot enforce those limits across workers, restarts or request rollbacks.

## Decision

Before each paid attempt, commit a conservative reservation through a separate Postgres connection. A row lock serializes reservations and settlements across workers. The UTC day comes from the database clock. Outstanding and unknown-cost calls retain their full reservation; there is no automatic expiry or refund after a crash. Known charges settle once, idempotently. A charge above its reservation disables the scope for owner investigation.

Only the owner migration role can change the limits. The non-owner API role can execute the two narrow reserve/settle functions; it cannot read or mutate the underlying tables directly. Those tables contain cost metadata only and have forced RLS with an owner-only policy. Customer and banking tables retain their existing RLS.

The `production` scope has a US$3 daily limit. The optional `handoff09-smoke` run has an additional cumulative US$0.10 limit, which does not reset at midnight or restart. The smoke script also checkpoints its conversation count before creating a conversation. Budget denial or database failure stops model attempts and uses the deterministic application path. Budget failures never invoke another provider.

Model requests use the reviewed endpoint selection, output bounds and OpenRouter price ceilings. Unknown usage is never reported as a measured zero cost. A model-generation deadline bounds primary and fallback attempts together; the browser BFF allows time for NLU and the bounded grounded-phrasing attempts and does not retry writes.

The production key goes from the ignored local environment file into the existing Key Vault, with matching readback before local removal. Only the API managed identity gets secret-scoped access. Terraform stores a secret URI, never this key's value. Local/default configuration remains mock; enabling production is explicit deployment configuration.

## Consequences and limits

Reservations may stop calls early after an unobserved provider failure. The owner must reconcile unknown charges before releasing their reserve. UTC midnight starts a new daily allowance; it is not a rolling 24-hour cap. The US$3 breaker limits model calls, not Azure charges or a monthly bill. Provider invoices and key-level limits remain separate controls. No new public access, judge execution or frozen-suite run is authorized by this change.

## Verification

`python -m scripts.test_postgres` exercises parallel reservations, request rollback, a replacement connection pool, UTC rollover, the cumulative run cap, immutable runtime limits and over-reservation shutdown. Fixture adapters exercise reserve-before-call, unknown usage and deadline behavior without real model calls. Cloud verification and the priced smoke are recorded separately in the progress log and ignored release receipts.
