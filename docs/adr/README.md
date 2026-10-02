# Architecture decision records

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-layer-1-scope.md) | Layer 1 vertical slice and mock-only provider | Accepted |
| 0002 | LLM provider and model | Deferred pending access and budget approval |
| 0003 | AI and deterministic split | Planned |
| [0004](0004-serving-isolation.md) | Organizer serving and persona isolation | Accepted |
| [0005](0005-data-platform.md) | Contracted local gold tables | Accepted |
| [0006](0006-bank-clock.md) | UTC timestamps and bank clock | Accepted |
| [0007](0007-charge-matcher.md) | Leakage-safe matcher comparison | Experimental |
| 0008 | Templates and phrasing | Planned |
| 0009 | Test identity service | Planned |
| 0010 | Hosting | Deferred pending explicit approval |
| [0011](0011-incremental-snapshots.md) | Incremental objects and atomic snapshots | Accepted |
| 0012 | Fraud score threshold | Deferred |
| [0013](0013-durable-operations.md) | Durable operations, RLS and audit chains | Accepted |
| [0014](0014-durable-model-budget.md) | Durable daily and smoke-run model budgets | Accepted for restricted demo |
| [0015](0015-post-v2-conversation-and-policy-contract.md) | Explain/offer/dispute, reason sets and independent gold contract | Accepted specification; implementation pending |
| [0016](0016-judge-profile-sessions.md) | One judge login, rotated customer-scoped sessions | Accepted for implementation; Azure OFF |
| [0017](0017-drop-jev-from-live-path.md) | Disable live Jev risk union; preserve historical judges/studies | Accepted; release pending |

Copy [the ADR template](template.md) for each new decision.
