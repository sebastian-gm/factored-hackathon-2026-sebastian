# Architecture as built

Scope: main at `dd957c7` plus the customer UI integration proposed in
[PR #17](https://github.com/sebastian-gm/bank-agent-lab/pull/17). Deployment verification
is separate. Solid paths below exist in code; dashed paths are pending integrations.

```mermaid
flowchart LR
  U[Customer: ES or PT] --> W[Next.js customer UI and same-origin BFF]
  W --> A[FastAPI: authenticated session and scoped routes]
  D[Agent Desk and Ops: flagged UI fixtures] -. Staff APIs pending .-> A
  A --> O[Orchestration: conversation state and guards]
  O --> N[Structured NLU: validated slots or B1 fallback]
  N -. Approved real provider only .-> L[Provider adapter: budget and timeout]
  N --> M[Authorized retrieval and matcher]
  M --> P[Deterministic policy with rule IDs]
  P --> C[Exact proposal and confirmation; fresh OTP]
  C --> T[Scoped bank writes; idempotency]
  T --> V[Commit then independent read-back]
  V --> R[Templates; guarded optional phrasing]
  P --> H[Handoff facts and deterministic routing]
  H --> DB[(Postgres operational state and forced RLS)]
  T --> DB
  V --> DB
  O --> E[Execution metadata and redacted turns]
  E --> DB
  DB --> AU[Append-only hash-chained audit]
  S[Local organizer files] --> B[Bronze hashes and manifest]
  B --> SI[Incremental silver: contracts and DQ]
  SI --> G[Complete tested gold snapshot: dbt and DuckDB]
  G --> ML[Local training and calibrated matcher artifact]
  ML --> M
  G --> SL[Explicit local serving load and checksum read-back]
  SL -. Organizer ledger binding pending .-> M
  F[Project-generated ledger] --> M
```

The deployed fixture ledger is held by the bank repository; operational writes use
Postgres. Local organizer serving tables are a separate data product and are not
silently treated as the deployed ledger. Routing may use an approved minimal service
agent projection; no organizer row values are embedded in this diagram or UI bundle.
The [data lineage image](data/dbt-lineage.svg) comes from the aggregate dbt manifest.

## Conversation and action state

The chart describes branches implemented in API/orchestration code, not a separate
workflow service. A message cannot supply an identity or authorize its own write.

```mermaid
stateDiagram-v2
  [*] --> Authenticate
  Authenticate --> Understand: password and simulated OTP
  Understand --> Refuse: security guard
  Refuse --> Understand: session remains valid
  Refuse --> End: repeated cross-customer request
  Understand --> Clarify: missing or ambiguous slots
  Clarify --> Understand: customer reply
  Clarify --> Escalate: clarification or turn guard
  Understand --> Match: scoped transaction request
  Match --> Choose: plausible candidates
  Choose --> Match: customer selects or rejects
  Match --> Decide: selected transaction
  Decide --> Explain: permitted status explanation
  Decide --> Status: existing case
  Decide --> Propose: eligible dispute
  Decide --> Escalate: human required
  Understand --> Escalate: explicit human or risk cue
  Escalate --> FreezeOffer: applicable card and fraud
  FreezeOffer --> StepUp: customer chooses a card
  StepUp --> ProposeFreeze: fresh OTP verified
  ProposeFreeze --> Confirm: server proposal
  Propose --> Confirm: server proposal
  Confirm --> Cancel: explicit cancellation
  Confirm --> Act: valid hash, scope, expiry and OTP
  Act --> Verify: committed write
  Verify --> Report: independent read-back succeeds
  Verify --> SafeFailure: failed or uncertain result
  SafeFailure --> Escalate
  Cancel --> Escalate: fraud review continues
  Cancel --> End: dispute cancelled
  Report --> Escalate: verified freeze
  Report --> End: dispute received
  Explain --> End
  Status --> End
  Escalate --> End: verified handoff
  End --> [*]
```

Session expiry invalidates authority; the UI requires authentication and a new
proposal. Backend guards recheck policy and ownership at confirmation. Reads have
bounded failure handling; writes are not blindly retried. A model outage degrades
to B1/templates. The frontend additionally reads case, handoff and frozen-card
records before showing receipts. A revoked session can show the refusal but cannot
claim a new handoff read-back using its invalid token.

## AI and deterministic responsibilities

| Concern | Implemented mechanism | Reason and boundary |
| --- | --- | --- |
| Intent, language, recollection slots | P uses schema-validated structured NLU; B1 uses rules. Default mock can fall back. | Language is uncertain; extracted text never grants authority. Real-model quality is pending. |
| Amount, relative date and currency interpretation | Deterministic normalization after extraction, using the bank clock; ambiguous currency asks a question. | Arithmetic and date semantics need repeatable tests. |
| Candidate retrieval | Authenticated customer scope, business-time window and serving contracts. | A model cannot widen access. |
| Transaction ranking | Validation-selected calibrated LightGBM; rules baseline. | Learned ranking addresses noisy slots; confidence controls proposal/choice/no-match, not eligibility. |
| Fraud cues | Provided score and deterministic lost/stolen/case-burst guards. | No fraud model is trained from the generator's label leakage. Language cues have documented gaps. |
| Eligibility, escalation and routing | Versioned policy engine; active skill/language/load routing and recorded fallbacks. | Auditable rules, independent of model prose and protected characteristics. |
| Dispute and freeze | Server-issued action hash, scoped authorization, fresh OTP, explicit confirmation, idempotency and read-back. | Code owns side effects. |
| Critical action/status wording | Deterministic ES/PT templates. | Action claims require evidence; no promise of refund or credit. |
| Clarification and explanation phrasing | Optional model draft, fact/citation/DLP checks and template fallback. | Narrow language flexibility; checks are not complete semantic verification. |
| Handoff | Deterministic facts/actions/questions and routing. | The brief's optional model-written summary is not established as a live feature. |
| Audit and UI explanation | Execution events, rule IDs, sources and verification. | Model thinking is neither an audit artifact nor a UI feature. |

[API contract](../contracts/interfaces/openapi.json), [policy catalog](policy-catalog.md),
[durable-state ADR](adr/0013-durable-operations.md), [routing](handoff-routing.md),
[matcher card](ml/model-card-charge-matcher.md), and [AI interface proposal](ai-interface-proposal.md)
provide the detailed boundaries. OpenTelemetry export, live Ops metrics, comprehensive
retention and operational SLOs remain production work; their boxes are not presented
as deployed infrastructure here.
