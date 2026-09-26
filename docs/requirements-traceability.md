# Requirements traceability

Layer 1 skeleton. Evidence links will be filled as the implementation and evaluation grow.

| ID | Requirement | Judging criteria | Implementation | Verification | Evidence |
|---|---|---|---|---|---|
| R1 | Use data evidence to prioritize the workflow and define outcomes. | Business Reasoning, Data Quality | P1 profiles and problem analysis. | Run the local data pipeline; compare aggregates with §4. | Verified: [P1 data-quality report](data-quality-report.md); four §4 values remain flagged. |
| R2 | Preserve context, clarify ambiguity, ground facts, use tools, and verify reported actions. | Architecture, Reliability, Privacy & Fairness | Chat state machine, scoped repository, response plans, action read-back. | B1 API scenario harness and Compose API round-trip. | Verified: B1 and Compose normal-dispute read-back. |
| R3 | Enforce policy, confirmation, abstention, and human handoff in code. | Architecture, Reliability, Privacy & Fairness | Policy engine and handoff packet. | Normal, ambiguous, and human scenarios. | Verified: B1 32/32 passed with safety guards. |
| R4 | Use repeatable data prep, contracts, DQ, lineage, freshness, and an evaluated learned component. | Reproducibility, Data Quality, Architecture | DuckDB/Pandera pipeline; later matcher evaluation. | Pipeline/DQ checks; matcher evaluation deferred. | Partial: three scoped tables build with contracts; matcher evaluation deferred. |
| R5 | Measure quality and failure behavior on held-out cases. | Reliability, Reproducibility | B1 dev harness now; full held-out suite later. | Dev harness in this layer. | Partial: 32 dev scenarios pass; held-out evaluation deferred. |
| R6 | Provide a reproducible operational path and explain decisions from evidence. | Architecture, Reproducibility, Production Thinking | Compose, health endpoints, deterministic policy and structured handoff. | Compose health checks and API/UI round-trip. | Verified: local Compose Postgres/API/web healthy; UI renders API health. |
| R7 | Support normal, ambiguous, and human paths in ES and PT. | Business Reasoning, Privacy & Fairness | Rule-based ES/PT NLU and localized response templates. | B1 scenarios across both languages. | Verified: B1 32/32 passed; PT/MX/AR phrase review limitation is documented. |
| R8 | Enforce approved data boundaries and per-customer access. | Privacy & Fairness, Reliability | Synthetic fixture ledger and session-derived customer scope. | B1 session-scoped transaction read and caller-supplied customer-id override attempt. | Verified: B1 scope guard passed; Compose returned six configured-customer transactions. |
| R9 | Compare baseline and proposed on a shared held-out workload with variability and judge validation. | Reproducibility, Reliability | B1 harness skeleton; proposed system and held-out suite deferred. | Later evaluation protocol. | Deferred beyond Layer 1. |
| R10 | Report safe resolution, containment, escalation quality, unsafe outcomes, and efficiency separately. | Business Reasoning, Reliability | Metrics schema deferred. | Later evaluation. | Deferred beyond Layer 1. |
| R11 | Report outcomes by language and authorized segments with sample caveats. | Privacy & Fairness, Data Quality | Scenario language metadata. | Later segmented evaluation. | Partial: scenarios carry language labels; segment report deferred. |
| R12 | Match processing mode to inputs and prove update handling with a fixture. | Reproducibility, Data Quality | Local batch pipeline; incremental fixture deferred. | Pipeline run now; fixture later. | Partial: local P1 batch verified; incremental/restatement fixtures deferred. |
| R13 | Report autonomy, accuracy, latency, cost, and oversight trade-offs. | Business Reasoning, Production Thinking | Deterministic policy and mock-only system now. | Later Pareto and risk/coverage evaluation. | Partial: mock-only deterministic baseline; model comparison deferred. |
| R14 | Separate conversation, risk estimate, and policy eligibility. | Architecture, Privacy & Fairness | Rules-based NLU separated from policy functions. | Unit/API harness scenarios. | Verified: B1 scenarios exercise separate NLU and policy paths. |

The mapped judging criteria are the seven published categories: Architecture, Reliability, Reproducibility, Data Quality, Business Reasoning, Privacy & Fairness, and Production Thinking.
