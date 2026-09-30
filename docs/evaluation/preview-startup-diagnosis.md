# Azure preview startup diagnosis — 2026-09-29 PDT

Preview source: `37627d4001bc02bd3ae0c25c618acd16f5b4a47e`, in the approved
`Seb Azure Sandbox` / `rg-aclara-dev-eastus2`. No Azure setting or image was
changed during this diagnosis. No model call or banking write was made.

## Observed cause

ARM metadata showed **zero API and web replicas** before the first request.
Both images matched the preview SHA. Authenticated checks used the existing
Key Vault demo password in memory, the BFF cookie jar and simulated OTP; no
credential, OTP, cookie or customer row was printed.

| Check | Status | Wall time |
|---|---:|---:|
| First BFF config GET (web then API cold start) | 503 `service_unavailable` | 50.560 s |
| First login POST | 503 `service_unavailable` | 10.114 s |
| Warm config GET | 200 | 0.485 s |
| Warm login POST | 200 | 0.108 s |
| OTP SMS GET / verification POST | 200 / 200 | 0.159 / 0.299 s |
| Authenticated me GET, including bank clock | 200 | 0.198 s |
| Authenticated transactions GET | 200 | 0.114 s |
| Second me / transactions GET | 200 / 200 | 0.104 / 0.109 s |
| Logout with revocation readback | 200 | 0.205 s |

The clock is a field of `/me`, not a separate API route. Four scoped transaction
projections passed the BFF schema; only their count was inspected.

API console logs show Uvicorn startup completed at **2026-09-30 01:29:21 UTC**,
after web readiness at **01:28:39 UTC**. The sampled logs contain no application
exception. They show successful personas, login, OTP, me and transaction reads,
plus the expected 401 after logout. The aborted first login eventually reached
the API too: retrying it automatically would have duplicated an auth operation.

This reproduces a **cold-start chain exceeding the BFF's 10-second deadline**.
Warm authenticated reads exercise the new snapshot middleware without a failure.
Phrasing is not invoked by these reads. This is evidence for the reported startup
failure; it does not verify paid chat execution or exclude unrelated PR defects.

Ignored, mode-0600 evidence: `artifacts/preview-diagnosis/read-only.json`,
`warm-read-only.json`, and private API/web console captures. Read-only metadata
commands used `az containerapp show`, `az containerapp replica list` and
`az containerapp logs show --type console --tail 300 --format json`, always with
`--subscription 'Seb Azure Sandbox' --resource-group rg-aclara-dev-eastus2`.
HTTP checks ran with `.venv/bin/python` and `httpx` against the web BFF; no chat,
confirm, freeze or staff mutation endpoint was called.

## Smallest code fix

Sebastian approved a code-only startup correction, keeping **min replicas zero**
while testing:

- BFF startup GETs (`me`, clock, transactions and config's upstream personas read)
  receive **75 seconds per attempt**, covering the observed approximately
  60-second API startup. The clock continues to arrive through `me`.
- Idempotent GETs get **at most one retry** on timeout/network failure or HTTP
  502/503/504, with a fresh timeout signal. Authentication/authorization failures
  and other HTTP statuses are returned directly.
- **No POST is retried**, including login, messages, confirmation and freeze.
  Existing message deadlines remain unchanged.
- The UI shows **“Iniciando el servicio…” / “Iniciando o serviço…”** while
  bootstrap reads wait, followed by a friendly explicit retry if startup fails.
  A transient me failure is not silently converted into a logged-out session.

The patch is prepared on `fix/preview-startup-review`, based on PR #62's reviewed
head `32587c9`. It has not been deployed. This is not a claim that a new cold
Azure startup has passed with the patch. Local tests cover timeout/retry limits,
POST non-replay, ES/PT startup state and recovery; local CI evidence is in the
progress log. A preview image change still needs an approved deployment step.

## Billing and submission-day replicas

GitHub's `checks` annotation on PR #62 says the job **was not started because an
Actions budget is preventing further use**. Local checks supplement this gap;
they are not a green GitHub Actions run. PR #62 remains unmerged while the owner
decides billing or explicitly overrides the merge gate.

The [submission checklist](../submission/checklist.md) records min replicas one
only from share/submission day (about October 3–4), its live-price estimate and
the separate approval/verification step. No replica change was made here.
