# Limitations

- Layer 1 is a local prototype. Identity, OTP delivery, operational storage, and the ledger are simulated.
- The current chat logic is rules-based; it is not evidence of a learned matcher or production multilingual quality.
- The project owner will review Spanish. Portuguese and MX/AR dialect phrases for future model evaluation will be labeled model-generated and cross-checked by a second vendor; there is no fluent Portuguese reviewer.
- No paid LLM is called. `LLM_PROVIDER=mock` is the default pending access and budget approval.
- Organizer data is used only by the local data pipeline and is excluded from Git and CI.
- Dispute eligibility is a synthetic policy for this demo, not legal or bank policy.
- The AI-lane provider, NLU, and NLG modules are built against the frozen `NluFrame` and `ResponsePlan` interfaces but are not yet wired into the lead lane's orchestrator. Rich slots remain internal to the AI lane until an additive interface proposal is reviewed.
- No round-1 or final-test model metrics exist yet. The model-comparison table is intentionally pending; no default model has been selected.
- Regex redaction, DLP, and grounding checks are conservative guards, not complete PII recognition or semantic factual verification. Unsafe or uncertain drafts fall back to an approved template.
- The LLM budget counter is process-local. A shared durable counter is needed before a multi-replica public deployment.
