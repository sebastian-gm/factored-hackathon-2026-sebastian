# ADR-0001: Layer 1 vertical slice and mock-only provider

- Status: Accepted
- Date: 2026-09-26

## Context

The demo must be usable end to end at the end of every work session. Layer 1 needs to establish authentication, customer scope, policy-controlled actions, verification, human handoff, Spanish and Portuguese paths, and a small baseline harness.

## Options

1. Build the broader infrastructure and operations surfaces first; higher setup cost and no end-to-end customer path.
2. Build a thin local vertical slice using deterministic rules and a mock-only provider; focused evidence with an explicit prototype limitation.

## Decision

Build the thin local slice. `LLM_PROVIDER=mock` is the default. Terraform, cloud resources, JWKS/ES256, hash-chained audit, Ops UI, learned matcher, and paid-model runs are deferred.

## Consequences

The first slice has an in-memory operational store and a project-generated ledger fixture. It demonstrates flow and policy, not production persistence or a real identity provider. The first deploy requires owner approval.

## Revisit when

Layer 1 checks pass, the owner provides LLM access and a budget, and deployment costs are estimated and approved.
