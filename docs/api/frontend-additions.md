# Frontend API review and additive integration

Review of frontend PR #17 against the policy/workflow API. The lead ships backend
contracts; `apps/web/` remains owned by the frontend lane. Read the current
`contracts/interfaces/openapi.json`; v1 chat, dispute and handoff routes remain.

| Requested capability | Additive interface |
| --- | --- |
| Trusted identity | `GET /personas`, typed `GET /me`: username, role, language, locale, bank clock. Role comes from trusted server configuration at password+OTP issuance, never username parsing or request fields. |
| Products | Scoped `GET /accounts` and `GET /cards/{handle}` expose handles/type/status; no full product identifiers or numbers. |
| Fresh OTP and freeze | `POST /auth/step-up`, `/auth/step-up/verify`, `/cards/{handle}/freeze/proposal`, `/cards/{handle}/freeze`; exact stored action hash, current scope/product recheck and committed readback. |
| Logout | `POST /auth/logout` revokes the capability and verifies deletion. Clearing a BFF cookie alone is insufficient. |
| Agent Desk | `GET /agent/handoffs`, `GET /agent/handoffs/{id}` return typed packet, workspace status/version, evidence, actions and SLA. |
| Claim / resolve | POST `/agent/handoffs/{id}/claim` or `/resolve`, body `{expected_version, idempotency_key, resolution?}`. Resolution is `review_completed` or `transferred`; no refund promise. Conflicts return 409. Verify using GET. |
| Trace | `GET /chat/sessions/{id}/trace`, also referenced by `/agent/conversations/{id}`. Only stage/state, rules, tool/readback and provider/model/prompt/token/cost/latency metadata. No input snapshots, messages, hidden scores or thinking. |
| Ops | `GET /ops/snapshot` and `/ops/metrics`: actual scoped operational counts and fixture-source metadata. SAR/unsafe evaluation rates are null because operations lack gold labels. No illustrative metric is represented as measured evaluation. |
| Reset | `POST /ops/reset/proposal`, then `/ops/reset` with hash + confirmation; `GET /ops/reset/{receipt_id}`. Requires ops role, fresh step-up, enabled demo-reset flag and current workspace. Auth/audit are retained; operational state is cleared and read back. |

## Authorization and deployment boundary

This dev layer uses one configured demo identity, with `DEMO_ROLE=customer` by
default. A trusted local process can configure `agent` or `ops`; every read and
write is still limited to that identity's current run/session workspace. There is
no organization-wide staff queue or cross-workspace impersonation.
`ALLOW_DEMO_RESET=false` by default. Azure keeps both defaults. Production staff
identity federation and task-scoped access grants are future work; RLS is unchanged.

The packet records masked customer/auth metadata, conversation/trace links, policy
reasons, risk categories, synthetic 15-day SLA, open questions and next steps.
Statements are empty when no separately recorded statement is available; no
statement is invented. Existing packets may lack newer optional metadata.

## Required changes in frontend PR #17 before merge

- Update runtime plan schemas for additive `refuse`/`refused_security`,
  `report_status`/`status_reported`, `review_flag`, and freeze offers.
- Consume trusted `/me.role`; keep backend role checks authoritative. The current
  BFF forces live sessions to customer and returns 501 for live staff APIs. Enable
  routes only after integrating these contracts.
- Wire upstream logout and step-up/freeze. Dispute confirmation remains hash plus
  boolean; freeze uses its explicit card endpoint.
- The API marks a handoff `verified=true` only after committed readback, matching
  the BFF's receipt check. Preserve both checks.
- Update Ops to the measured workspace schema. Keep reset disabled unless enabled
  in trusted configuration. Never relabel fixture results as held-out evaluation.
- Add a live handoff browser test and refusal/status tests. Then the lead can merge
  the UI and add its authored Playwright suite to shared CI.

These additions followed the frozen diagnostic; its results describe the recorded
implementation SHA, not the later packet/trace additions. The frozen suite was not
rerun or used to tune policy or NLU.
