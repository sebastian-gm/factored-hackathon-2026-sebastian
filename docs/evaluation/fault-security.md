# Fault and security harness coverage

Verified with `.venv/bin/pytest tests/test_bound_evaluation.py tests/test_evaluation.py -q`:
16 tests passed. Inputs are independent authored development fixtures; no network
request or paid model invocation occurs in the provider-failure tests.

| Category | Observable check |
| --- | --- |
| Model timeout / outage | Inject `TimeoutError` / `URLError` at the HTTP adapter, observe two bounded attempts and provider-error records, P fallback, explicit confirmation and verified receipt. |
| Persistent NLU outage | Every applicable call fires; B1's absent model boundary remains explicitly not executed. |
| Scoped database / tool / connection faults | Match/write/readback boundaries fail; available handoff persists and reads back. An authorized intake followed by readback failure is not scored as an unauthorized write. |
| Expired session / stale OTP | Confirmation returns denial and no intake; fresh step-up uses real API endpoints for freeze. |
| Confirmation tamper / replay | Altered live hash rejected; replay leaves exactly one case. |
| Cross-customer attempts | First refusal logged; second scheduled attack ends session and persists a security packet without restoring HTTP access. |
| Direct / indirect injection | Security event observed; no instruction/credential canary disclosed and hostile merchant instructions omitted from the reply. |
| Required handoff fields / unknown predicates | Every required field is enforced; unknown semantic predicates fail closed as adapter errors. |

These tests cover specific attacks and failures, not arbitrary-language security.
A process-wide database outage can prevent handoff persistence; the existing API
returns 503 without claiming success in that situation. Readiness/liveness checks
are covered separately in `tests/test_degraded_mode.py`. Real network timeout timing,
provider availability and deployed chaos tests have not been exercised.
