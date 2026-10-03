# Architecture as built

**What this shows:** How Aclara understands charge questions and handles requests in Spanish and Portuguese.<br>
**Result:** Code controls access, confirmation, bank actions and verified receipts.<br>
**Limits:** This is a synthetic-bank demo with simulated identity, not a real banking service.

<details>
<summary>Technical details and evidence</summary>

> **superseded by v4 (2026-10-01)** — Historical evaluation/release status below; use the [current summary](../README.md) and [official v4 results](evaluation/final-v4-results.md). [Post-v4 fixes](evaluation/post-v4-release-notes.md) are **not reflected in v4 numbers**.

Scope: shipped backend contracts and the merged customer/staff UI in
[PR #17](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/17). Private real-model deployment is verified in the [progress log](status/progress-log.md). Solid paths below exist in code; dashed paths are pending integrations.

The current source configuration disables live Jev; the lead's next image release
is pending. Gemini/Grok calls go through OpenRouter; historical Sonnet/Jev
evaluation judges remain offline. **Post-v4 fixes, not reflected in v4 numbers.**
[ADR-0017 and saved-record evidence](adr/0017-drop-jev-from-live-path.md).

```mermaid
flowchart LR
  U[Customer: ES or PT] --> W[Next.js customer UI and same-origin BFF]
  W --> A[FastAPI: authenticated session and scoped routes]
  D[Agent Desk and Ops: trusted role and current workspace] --> W
  A --> O[Orchestration: conversation state and guards]
  O --> N[Structured NLU: validated slots or B1 fallback]
  N --> L[OpenRouter: Gemini default; Grok failure fallback]
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
  SL --> M
  F[Project-generated ledger] --> M
```

The runtime binds a checksummed organizer serving snapshot and trusted personas;
missing serving bindings fail closed. Project-generated fixtures remain the isolated
test path. Operational writes and model budget reservations use Postgres. No organizer
row values belong in diagrams or UI bundles. [Serving isolation](serving-demo.md).
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
  Refuse --> End: two non-degraded P-model-confirmed access strikes
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
| Intent, language, recollection slots | P uses schema-validated structured NLU; B1 uses rules. Default mock can fall back. | Language is uncertain; extracted text never grants authority. Development model comparisons exist; final acceptance is pending. |
| Amount, relative date and currency interpretation | Deterministic normalization after extraction, using the bank clock; ambiguous currency asks a question. | Arithmetic and date semantics need repeatable tests. |
| Candidate retrieval | Authenticated customer scope, business-time window and serving contracts. | A model cannot widen access. |
| Transaction ranking | Validation-selected LightGBM v2; v1 and rules retained for comparison. | Learned ranking addresses noisy slots; confidence controls proposal/choice/no-match, not eligibility. |
| Fraud cues | Gemini flags and deterministic score/case-burst guards; live Jev disabled behind its opt-in flag. | No fraud model is trained from the generator's label leakage. Historical v4 included Jev; marginal benefit was unproven. |
| Eligibility, escalation and routing | Versioned policy engine; active skill/language/load routing and recorded fallbacks. | Auditable rules, independent of model prose and protected characteristics. |
| Dispute and freeze | Server-issued action hash, scoped authorization, fresh OTP, explicit confirmation, idempotency and read-back. | Code owns side effects. |
| Critical action/status wording | Deterministic ES/PT templates. | Action claims require evidence; no promise of refund or credit. |
| Clarification phrasing | Blank-plan clarifications may use a model draft with fact/citation/DLP and unsupported-action/cause checks. Status explanations and approved state-specific replies are templates. | Narrow language flexibility; checks are not complete semantic verification. |
| Handoff | Deterministic facts/actions/questions and routing. | The brief's optional model-written summary is not established as a live feature. |
| Audit and UI explanation | Execution events, rule IDs, sources and verification. | Model thinking is neither an audit artifact nor a UI feature. |

[API contract](../contracts/interfaces/openapi.json), [policy catalog](policy-catalog.md),
[durable-state ADR](adr/0013-durable-operations.md), [routing](handoff-routing.md),
[matcher card](ml/model-card-charge-matcher.md), and [AI interface proposal](ai-interface-proposal.md)
provide the detailed boundaries. Staff claim/resolve uses version and idempotency
checks plus a GET read-back. Ops reports measured current-workspace counts; SAR and
unsafe rates remain null without gold labels. Reset is disabled by default and
requires trusted flags, ops role, fresh OTP, exact confirmation and a read-back;
authentication and audit are retained. This is not a multi-customer staff queue.

OpenTelemetry export, comprehensive retention and operational SLOs remain production
work. Private real-model deployment and browser flows are verified in the
[release progress log](status/progress-log.md). The final held-out evaluation remains
separate from smoke evidence. The earlier mock diagnostic failed acceptance gates.

</details>
