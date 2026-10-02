# Item 7 hygiene verification

2026-10-02. **Local/mock verification. Post-v4 fixes, not reflected in v4
numbers.** No organizer inputs, model spend or Azure changes.

| Requirement | Control and verified evidence |
|---|---|
| Non-root API | `Dockerfile.api` uses `USER 10001:10001`. Executing `id -u` in the existing local v0.6.0 API image, with networking disabled, returned **10001**. The Dockerfile is unchanged from that release. |
| Explicit action failures | No assertions in API handlers/workflows, serving reads or durable spend guards. Missing judge controllers return 404; a lost recognition target returns 503 with no proposal/write. Missing serving connections raise `OperationalError`; unavailable accounting raises `BudgetFailure`, retaining reservations. Freeze verification already used an explicit 503 and rollback. |
| Private identity catalog | Authored `/personas` regressions omit staff and configured judge accounts; invalid judge aliases fail configuration. Actual local BFF `GET /api/bff/config`, with fixture judge access enabled, returned **5 customer entries and 0 staff/judge identities**. The live BFF filters the API catalog again. Manual staff login remains available. |
| Session expiry / re-login | `AUTH-01` grants **35 minutes**; the API returns the exact expiry. The live BFF uses that deadline, rejects a missing/expired deadline or one beyond 45 minutes, and clears cookies on logout. Existing ES/PT browser tests cover expiry, clearing both tabs and explicit re-login. Fixture mode can use a shorter deadline and retains the same re-login UI. |
| One structured turn log | Completed chat messages, dispute confirmation/retries, and card-freeze confirmation/retries emit exactly one `aclara.turn` JSON record after independent readback where needed. Keys: `conversation_id`, `outcome`, `rule_ids`, `llm_latency_ms`, `llm_cost_usd`, `degraded`. Unknown cost remains null. No text, credentials or organizer rows enter this log. Authentication/transport failures use HTTP error/access logging rather than a successful turn outcome. |

The follow-up closed nine remaining runtime assertions and the missing freeze
turn logs. Tests force the broken states and verify explicit failures, including
with Python optimization enabled. A short state table documents
`process_message`; its branches were not refactored.

## Commands and results

Refreshed on merged #124; its seven packaging regressions explain the increase
from the initially verified 1208 tests to 1215.

- `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 make checks`: **1215 passed /
  31 DB skips**, hooks, strict mypy, compilation, staged-file policy, B1
  **32/32**, interface and policy snapshots passed.
- `LLM_PROVIDER=mock .venv/bin/python -m pytest -q tests/test_audit_hygiene.py tests/test_nlu_transaction_boundary.py tests/test_judge_access.py tests/test_judge_profiles.py tests/test_workflow_api.py`:
  **67 passed / 1 local Postgres skip**.
- `LLM_PROVIDER=mock .venv/bin/python -O -m pytest -q tests/test_audit_hygiene.py`:
  **18 passed**. Pytest warns that non-test assertions are optimized away;
  the explicit runtime failures remain active.
- Local fixture BFF launched on an isolated localhost port with
  `FRONTEND_DEMO_MODE=fixtures FRONTEND_FIXTURE_JUDGE_ACCESS=true`; the config
  GET passed. It was stopped after the check. Private receipts/logs are in
  ignored `artifacts/azure/item7-*`; no server or container was left running.

The new code has not been deployed or checked against real models. Azure stays
on v0.6.0 until a subsequent release and its paid smoke are approved. This check
does not make a claim about concurrent production throughput; see the separate
local mock concurrency measurement.
