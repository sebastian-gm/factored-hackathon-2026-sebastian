# Frozen lane interfaces

These are versioned contracts for parallel implementation. Producers keep payloads compatible with the checked-in version. Additive optional fields are allowed; incompatible changes require an explicit version bump and a PR that identifies affected consumers.

| Interface | Source of truth | Consumer |
|---|---|---|
| HTTP API | `contracts/interfaces/openapi.json`, exported from FastAPI route models | Web client, AI lane, integrations |
| NLU result | `NluFrame` in `src/aclara/agent/contracts.py` | Orchestrator, policy, evaluations, AI lane |
| Orchestrator response plan | `ResponsePlan` in `src/aclara/agent/contracts.py`; used as the FastAPI response model | Web client, human-handoff flow, AI lane |
| Scenario YAML | `contracts/interfaces/scenario-suite.schema.json`; enforced by `src/aclara/evals/schema.py` | B1 and future model comparisons |
| Gold transaction facts | `contracts/interfaces/gold_transaction_facts.yaml` | Data/ML lane and serving projection |
| Serving transaction view | `contracts/interfaces/serving_transaction.yaml`; its fields are mirrored by `TransactionView` in `agent/contracts.py` | API and web client |
| P1 silver inputs | `contracts/customers.yaml`, `products.yaml`, and `transactions.yaml` | P1 pipeline; these are source-to-silver contracts, not the gold output |

The gold transaction contract describes a planned normalized, ownership-checked projection; the current P1 pipeline materializes bronze and silver only. The serving view is live in the Layer 1 API. It contains an opaque transaction handle and masked display fields; customer scope comes from the authenticated session, and internal transaction/product/customer identifiers are excluded.

Regenerate the OpenAPI and scenario-schema snapshots with `make interfaces`. CI runs `python -m scripts.export_interfaces --check`; a stale snapshot fails the check.
