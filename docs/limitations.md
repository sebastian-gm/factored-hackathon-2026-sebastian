# Limitations

- Layer 1 is a local prototype. Identity, OTP delivery, operational storage, and the ledger are simulated.
- The current chat logic is rules-based; it is not evidence of a learned matcher or production multilingual quality.
- The project owner will review Spanish. Portuguese and MX/AR dialect phrases for future model evaluation will be labeled model-generated and cross-checked by a second vendor; there is no fluent Portuguese reviewer.
- No paid LLM is called. `LLM_PROVIDER=mock` is the default pending access and budget approval.
- Organizer data is used only by the local data pipeline and is excluded from Git and CI.
- Dispute eligibility is a synthetic policy for this demo, not legal or bank policy.

## Data/ML lane (2026-09-26)

- The synthetic matcher benchmark operates on normalized slots, not human language. Human validation is pending. Sebastian will write recollections from 40 private Spanish cards; this initial set is smaller than the brief's 60–100 target.
- Portuguese recollections will be labeled model-generated and cross-checked by a second model vendor. That work is pending approved model access/cost; no fluent-human PT validation or paid model run is claimed here.
- Silver transformations are incremental by source object; downstream dbt gold tables rebuild as a complete tested snapshot. This intentionally trades work for simple atomic promotion.
- Gold and local Postgres loading are separate explicit steps. Freshness to gold and verified serving load time are recorded separately. Backend use of these tables and the matcher needs lead-lane integration.
- Bootstrap SQL for the local loader is not an Alembic production migration. The integration tests prove local table/view RLS and rollback, not a deployed service's complete authorization chain.
- Transcript duration contradicts the dictionary: 24,029 null values are preserved and warned on. Complaint product ownership is a field-level FAIL; unsafe links and complaint text are excluded from gold/serving.
- The app-error/contact comparison is event-level and descriptive, with activity confounding and repeated customers. No causal or independent-observation significance claim is made.
- The pipeline scopes ten relevant source tables. Marketing and branch-table ingestion, comparison with the older organizer regeneration, cloud scheduling, and live source freshness are not verified by this lane.
- The AI-lane provider, NLU, and NLG modules are built against the frozen `NluFrame` and `ResponsePlan` interfaces but are not yet wired into the lead lane's orchestrator. Rich slots remain internal to the AI lane until an additive interface proposal is reviewed.
- No round-1 or final-test model metrics exist yet. The model-comparison table is intentionally pending; no default model has been selected.
- Regex redaction, DLP, and grounding checks are conservative guards, not complete PII recognition or semantic factual verification. Unsafe or uncertain drafts fall back to an approved template.
- The LLM budget counter is process-local. A shared durable counter is needed before a multi-replica public deployment.
