# Threat model

Scope: the synthetic development service, local data pipeline, evaluation tooling,
model adapters and [proposed frontend](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/17).
This is a control/evidence map, not a security certification. See
[architecture](../architecture.md) for flows and [readiness](../production-readiness.md)
for deployment gates. Tests below are named repository tests; final CI/run status is
in the [progress log](../history/status/progress-log.md).

Assets are authenticated scope, private rows, credentials, exact action proposals,
case/card state, handoff evidence, model budget and audit integrity. Untrusted inputs
include customer text, merchant strings, model output, browser fields and imported
files. Boundaries separate browser/BFF/API, runtime/migration database roles,
local organizer storage/model providers, and private traces/submission aggregates.
The LLM receives no bank credential or write tool. A stolen real browser session,
privileged host or database owner remains a significant attacker capability.

## Test IDs used below

| ID | Repository test / check |
| --- | --- |
| AUTH | [test_api_security.py](../../tests/test_api_security.py): `test_protected_routes_require_a_live_bearer_session`, `test_otp_is_bound_to_preauth_and_limited_to_five_attempts` |
| SCOPE | Same file: `test_transactions_are_customer_scoped_and_mask_internal_identifiers`, `test_action_proposal_is_session_bound_and_single_use` |
| CONFIRM | Same file: `test_tampered_or_expired_proposals_fail_closed`, `test_confirmation_requires_recent_step_up_authentication` |
| LIMIT | Same file: `test_request_models_reject_extra_fields_bad_otp_and_oversized_messages` |
| RLS | [test_operational_store.py](../../tests/test_operational_store.py): `test_forced_rls_tables_views_functions_autocommit_and_reuse` |
| AUDIT | Same file: `test_transaction_rollback_concurrent_chain_and_append_only` |
| RESTART | Same file: `test_api_session_proposal_case_handoff_and_execution_survive_restart`, `test_freeze_api_and_step_up_survive_app_restart` |
| FREEZE | [test_workflow_api.py](../../tests/test_workflow_api.py): `test_freeze_requires_step_up_hash_scope_recheck_and_readback`, `test_freeze_cancel_noncard_expiry_and_policy_recheck` |
| GUARD | Same file: `test_security_two_strikes_injection_legal_distress_and_language` |
| DLP | [test_ai_lane.py](../../tests/test_ai_lane.py): `test_grounding_and_dlp_force_template_fallback` |
| PAYLOAD | Same file: `test_openrouter_request_uses_strict_schema_and_privacy_flags`, `test_structured_retry_records_invalid_output_without_content` |
| BUDGET | Same file: `test_real_call_requires_approval_before_adapter_invocation`, `test_budget_reserve_blocks_a_real_call_before_network` |
| AUTHORITY | [test_agent_integration.py](../../tests/test_agent_integration.py): `test_p_api_extraction_grounding_and_no_model_confirmation_authority`, `test_p_outage_degrades_through_api` |
| DATA | [test_data_pipeline.py](../../tests/test_data_pipeline.py): `test_incremental_atomic_gate_and_idempotence`, `test_missing_required_schema_is_quarantined` |
| MODEL | [test_charge_matcher.py](../../tests/test_charge_matcher.py): `test_artifact_roundtrip_and_empty_set`, `test_generated_dataset_leakage_and_noise_holdout` |
| STAFF | [test_staff_api.py](../../tests/test_staff_api.py): `test_customer_cannot_infer_roles_or_read_staff_data_and_logout_revokes`, `test_staff_claim_resolve_trace_and_current_workspace_isolation`, `test_ops_reset_requires_fresh_bound_confirmation_and_preserves_auth`; PR #17 live staff browser workflow |
| WEB | [PR #17 browser tests](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/tree/feat/frontend/apps/web/tests): `server blocks cross-origin writes, forged confirmation, and customer staff access`; `proposal replay is idempotent and another authenticated browser cannot confirm it`; live freeze confirmation/cancellation |
| REPO | [CI safety checks](../../.github/workflows/safety.yml), [tracked-file scanner](../../scripts/check_staged_files.py), frozen lockfiles and interface checks |

## STRIDE

| Threat | Control implemented | Test ID | Residual risk / missing control |
| --- | --- | --- | --- |
| Spoofing: use an ID, guessed handle or staff alias as identity | Password and simulated OTP establish a short-lived random capability; server-derived scope; HTTP-only cookies in the proposed BFF; role cannot come from username prose. | AUTH, SCOPE, STAFF, WEB | Simulated SMS is not an independent factor. Trusted demo roles and upstream logout are implemented; no real IdP or independent staff identity federation. Browser/session theft remains possible. |
| Tampering: change amount, target, confirmation or ledger input | Strict request schemas; bound server proposal, expiry, policy recheck and idempotency; source hashes/contracts and atomic promotion. | CONFIRM, FREEZE, DATA | A privileged importer or host can alter source/config. Independent signed release/artifact attestations remain pending. |
| Repudiation: deny or rewrite an action | Committed execution records and separate read-back; append-only API audit privileges and hash-chain verification. | AUDIT, RESTART | A database owner can rewrite an unanchored chain. Independent signed export and retention are pending. |
| Information disclosure: another customer's data, secrets or thinking | Scoped tools/handles, forced RLS, non-owner role, restricted input projections, redaction and DLP; generic browser errors and no thinking storage. | SCOPE, RLS, DLP, PAYLOAD, REPO | Pattern redaction misses novel PII; model/provider behavior is not fully tested. Current-workspace staff packets are typed/redacted; broader task-scoped access needs independent review. |
| Denial of service: large requests, loops, database or provider failure | Input caps, bounded turns, provider timeout/retry/budget checks, deterministic fallback and readiness failure. | LIMIT, BUDGET, AUTHORITY; [degraded-mode tests](../../tests/test_degraded_mode.py) | Durable Postgres reservations retain spend exposure across restarts and parallel callers; see [budget tests](../../tests/test_llm_budget.py). Sustained load and provider-invoice reconciliation remain unverified. |
| Elevation of privilege: model/browser grants itself write or ops authority | Policy/actions are code; separate migration credentials; non-owner runtime rejects bypass roles; trusted staff roles and current-workspace scope are server-enforced; logout revokes capabilities. | AUTHORITY, RLS, FREEZE, STAFF, WEB | Production staff federation and cross-customer task grants are unimplemented. Development PostgreSQL's Azure-services network exception is broader than app-only access. |

## OWASP Top 10 for LLM Applications (2025)

Risk names follow the [official OWASP list](https://genai.owasp.org/llm-top-10/),
reviewed for this draft. The controls and gaps below are specific to this repository.

| Threat | Control implemented | Test ID | Residual risk / missing control |
| --- | --- | --- | --- |
| LLM01 Prompt injection: direct or merchant-carried instructions | Escaped data blocks, deterministic security guards, no model tool loop, schema validation and scoped action authority. | GUARD, AUTHORITY, DLP | Regex guards are incomplete; unseen multilingual/indirect attacks need held-out and adversarial review. |
| LLM02 Sensitive information disclosure | Contract projections, redacted customer input, DLP, opaque handles and RLS; no credential in the model payload. | SCOPE, RLS, PAYLOAD, DLP | Free text can contain identifiers outside patterns; provider retention/account settings remain a separate boundary. |
| LLM03 Supply chain: compromised package, model route or artifact | Dependency locks, SHA-pinned CI actions, numeric matcher export with checksums and interface snapshots. | MODEL, REPO | Comprehensive dependency/image audit, signed build provenance and endpoint/model change monitoring are not established. |
| LLM04 Data/model poisoning | Immutable-source hashes, schema/DQ gates, private local training, customer/time splits and frozen benchmark provenance. | DATA, MODEL | Hashes detect changes, not malicious but valid data. Organizer generator artifacts and pretrained-provider supply chains remain outside our control. |
| LLM05 Improper output handling | Pydantic/Zod validation, fact/citation checks, DLP, template fallback and React text rendering; no model-produced SQL or executable HTML. | DLP, PAYLOAD, AUTHORITY, WEB | Semantic errors can pass lexical checks; future rich rendering requires renewed review. |
| LLM06 Excessive agency | No autonomous model tools; eligibility in code; exact action hash, fresh OTP, explicit confirmation, idempotency and independent read-back. | CONFIRM, FREEZE, AUTHORITY, WEB | Incorrect policy/data can still produce a wrong permitted proposal. Human confirmation is not a substitute for correct matching. |
| LLM07 System prompt leakage | No secrets or authority in prompts; extraction guards and bounded response plans. | GUARD, DLP | Prompts are not confidential access controls. Semantic prompt extraction has not been comprehensively tested against real providers. |
| LLM08 Vector/embedding weaknesses | Not applicable to the current design: no vector store, embedding retrieval or RAG index. Retrieval is scoped structured ledger access. | MODEL, SCOPE; [matcher features](../../src/aclara/ml/charge_matcher/features.py) | This is an architecture inspection, not an embedding-security test. Adding vector search reopens this threat. |
| LLM09 Misinformation | Critical templates; grounded optional phrasing; calibrated matching and clarification; policy/rules shown with evidence. | DLP, AUTHORITY, MODEL | Synthetic normalized-slot quality does not establish natural-language accuracy. No guarantee against every wrong interpretation or promise. |
| LLM10 Unbounded consumption | Approval gate, estimated-cost reservation, output/request caps, bounded retries/turns and deterministic fallback. | BUDGET, LIMIT, AUTHORITY | Spend is durable Postgres; shared durable accounting and sustained-load tests are required before real-model release. |

## Release implications

Keep real customer data and real banking actions out of this service. The approved
development ingress restriction and database TLS are recorded by the lead, not
re-tested by this docs lane. CSP/HSTS, complete rate limiting, image/dependency
scanning, purge verification, independent audit anchoring and judge access still
require concrete implementation/verification; a checkbox here does not supply it.

The [frozen mock diagnostic](../history/evaluation/heldout-run01.md) observed forbidden
policy actions and incomplete handoffs despite passing individual security tests.
Engineering control tests do not supersede failed outcome acceptance gates. Later
staff API changes have no frozen-workload outcome claim.
