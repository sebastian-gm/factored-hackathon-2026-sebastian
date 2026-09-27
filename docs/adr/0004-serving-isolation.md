# ADR-0004: Organizer serving with customer RLS

- Status: Accepted
- Date: 2026-09-27

## Context

Sebastian requires the final demo, personas and held-out evaluation to run on organizer gold/serving outputs in the 120-day window, with authored ledgers retained only for tests and fixtures. The previous cloud API used authored transactions.

## Options

1. Load whole organizer tables into API memory: unnecessary data exposure and no database RLS boundary.
2. Query promoted Postgres projections under a non-owner customer context using the existing bounded pool: no new infrastructure cost.

## Decision

Choose option 2. Force customer RLS on all customer-scoped source tables; constrain queries by ownership and the promoted bank clock. Bind demo aliases privately in Postgres, with trusted roles and stable opaque authentication realms. Reject missing/version-mismatched serving state. Keep source projections read-only to the runtime and all operational writes under customer/run/session RLS.

The held-out adapter reads the same RLS source and applies declared counterfactual overlays only in isolated evaluation state; it does not mutate organizer tables or frozen labels. Independent dev tests verify the adapter boundary.

## Consequences

Serving load requires a separate owner connection and atomic checksum readback. Runtime startup requires loaded gold and private persona bindings. Shared demo credentials, simulated OTP and current-workspace staff access remain development limitations. UI and smoke tests must use actual source handles rather than hard-coded authored merchants.

## Revisit when

Production staff identity, cross-session queue grants, scheduled refresh/version pinning, realistic load or a production core-banking integration is approved.
