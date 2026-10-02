# Gate A concurrency plan — OFF

2026-10-02, post-v4 preparation. **No apply, no Azure settings changed.**
Sebastian must approve the exact fresh plan, availability window and cost before
activation. This is independent of Gate B judge/public access.

## Proposed settings

- API min **1**, max **3**, HTTP rule threshold **5**; web min **1**, max **1**.
- Both remain **0.25 vCPU / 0.5 GiB**, one Uvicorn worker per replica. Internal
  API, owner-IP web, login, Key Vault and model budget controls are unchanged.
- `enable_submission_scale=false` by default. It requires the separate
  `enable_submission_warm=true,min_replicas=1` approval switches. Default release
  plans remain min 0/max 1, without a custom rule.
- HTTP autoscaling is asynchronous; threshold 5 is the platform HTTP metric,
  not the app's five-slot inference semaphore or a guarantee of immediate scale.
  [Microsoft scaling semantics](https://learn.microsoft.com/azure/container-apps/scale-app).

Two workers fit the measured local fixture/mock memory envelope: warmed worker
RSS **118.55 / 117.77 MiB**, cgroup peak **234.23 MiB** of 512, zero OOM events.
This used the actual API image, matcher, .25 CPU and two Uvicorn workers; six
local authored turns, no serving DB or provider network. It is not a production
RSS bound. The separate source/ASGI process peak was 177.36 MiB.

**Keep one worker:** live sandbox Postgres `max_connections=50`. Each worker can
use four pooled connections plus five dedicated session-lock connections.
Three replicas × one worker × nine = **27**; two workers would reach **54**,
before reserved/admin connections. Concurrent inference now works within one
worker. Two workers require a separately verified connection/memory plan.

## Verified plan and cost

Mocked Terraform plans: **13 passed / 0 failed**. The deferred Gate B check is
also strengthened: two visits actually file the same authored story with distinct
verified receipts and cross-visit denial (four memory cases; disposable Postgres
suite **86/86**, covering all four profiles). Judge access stays OFF in Azure.
Real state-based preview,
`-refresh=false -lock=false`: **0 create / 2 update / 0 delete**. Only API min/max/
HTTP rule and web min change; inputs unchanged. Private plan SHA-256:
`78a3e7a518fe8293c8032e1a4cf5c937e56fe3bf39c01eff0f7af2815b7b577c`.

Live East US 2 USD retail meters checked 2026-10-02 22:34 UTC:
[Azure retail-price API](https://prices.azure.com/api/retail/prices).
No free grants assumed; before tax, allowance estimates are not a quote.

| Compute | USD/hour | Oct 4–16, 312 hours |
|---|---:|---:|
| One warm replica of each app, idle | 0.0162 | 5.05 |
| One active replica of each | 0.0540 | 16.85 |
| API at three plus one web, all active | 0.1080 | 33.70 |

Warm delta versus 100 active hours: **$3.43**; two extra active API replicas add
**$0.054/hour** (e.g. $0.54 for ten hours). Monthly total with the same fixed DB,
registry and $8.14 ancillary allowance: **$34.28–$62.93** for this sharing window.
The upper estimate exceeds the original $40 gate: explicit cost approval is
required. No warmer/burst configuration is authorized by the image release.

## Commands and rollback

```bash
terraform -chdir=infra test -filter=tests/submission.tftest.hcl
# Save these three values in a private override file, not terraform.tfvars:
# enable_submission_warm=true; min_replicas=1; enable_submission_scale=true
terraform -chdir=infra plan -refresh=false -lock=false -input=false \
  -var-file=/absolute/repo/artifacts/gate-a.override.tfvars \
  -out=/absolute/repo/artifacts/gate-a.tfplan
# Inspect privately with terraform show -json; DO NOT APPLY this preview.
```

At approval time regenerate a refreshed, locked plan using the runbook; require
only two app updates and unchanged CPU/memory/access/secrets. Read back API scale
1..3/HTTP threshold 5, web 1..1, ready revisions, internal API and owner-IP web.
Watch connection usage and capacity denials. Rollback via a fresh reviewed plan:
`enable_submission_scale=false,enable_submission_warm=false,min_replicas=0`;
read back both 0..1. Never reuse this stale preview as an apply artifact.
