# Limitations

## Application and evaluation

- The development service uses an authored fixture ledger, simulated identity and simulated OTP. It performs no real banking action. Organizer gold/serving tables are available locally but are not bound to the chat API.
- Cases, card states, handoffs, conversations, execution records, sessions and audit entries persist in Postgres. RLS isolates customer/run/session state. Local restart and isolation tests do not establish production recovery, retention or scale guarantees.
- Card-state repository persistence is tested; the customer-facing freeze/confirmation workflow is unfinished. Some brief policy rules remain partial or planned, explicitly marked in the generated [catalog](policy-catalog.md). Dispute eligibility is synthetic demo policy.
- P integrates structured NLU, guarded phrasing and the calibrated matcher. The default unconfigured mock degrades to B1 rules. Its passing dev suite is fallback evidence, not learned-language or real-model quality evidence. Configured mock tests separately exercise P and learned matching.
- No real-model run or model default selection has occurred. The [comparison table](ml/model-comparison.md) remains pending an estimated-cost approval. A later judge must use a different vendor from the system model.
- Reactive v2 evaluation supports authored fixture personas, clocks, transaction overlays, replies and injected faults. Organizer persona selectors and other overlay types are explicitly rejected until binding adapters exist. This is a dev suite, not a held-out evaluation.
- Unsafe-outcome detectors and the deterministic handoff rubric have bounded coverage. Zero observed errors in a small correlated dev sample does not establish zero risk. Regex redaction, DLP and grounding checks are not complete semantic verification.
- The model budget counter is process-local. A shared durable counter is needed before real-model public deployment; restarts must not reset the effective spend cap.
- The owner will review Spanish. Portuguese and MX/AR dialect material is model-authored and awaits the agreed second-vendor cross-check; no fluent Portuguese reviewer is available. Catalog translations also need review.

## Data and matcher

- Organizer data is excluded from Git, CI and the Azure demo. Only aggregates, contracts, code and project-authored fixtures are committed.
- The matcher benchmark evaluates normalized slots, not human language. Human validation is pending: 40 private Spanish recollection cards are prepared, fewer than the brief's 60–100 target. Portuguese recollections need approved generation and cross-vendor review.
- Silver transformations are incremental by source object; downstream dbt gold tables rebuild as a complete tested snapshot. Gold promotion and explicit Postgres serving load have separate freshness timestamps.
- Operational tables use Alembic migrations. The separate local serving loader uses bootstrap SQL; its integration tests prove fixture RLS and checksum/rollback behavior, not full production serving authorization.
- Transcript duration contradicts the dictionary: 24,029 nulls are preserved and warned on. Complaint product ownership is a field-level FAIL; unsafe links and complaint text are excluded from gold/serving.
- The app-error/contact comparison is event-level and descriptive, with activity confounding and repeated customers. It supports no causal or independent-observation significance claim.
- Ten source tables are scoped. Marketing and branch ingestion, comparison with the older organizer regeneration, cloud scheduling and live source freshness remain unfinished.

## Deployment

- Azure endpoints require the owner's IP and app login. PostgreSQL's approved Azure-services firewall exception admits network sources across Azure subscriptions; private access remains future work.
- Audit append privileges and hash links detect tested mutations. A privileged database owner can rewrite an entire unanchored chain; independent signed exports are future work.
- Budget alerts notify rather than stop spending. Monthly charges, alert delivery, fixed CAD conversion, restore/DR, sustained load and browser visual review remain unverified. See [production readiness](production-readiness.md).
