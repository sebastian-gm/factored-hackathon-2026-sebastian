# Dev API first-request startup diagnosis

Read-only investigation with `.venv/bin/python -m scripts.azure_health_diagnostics`
in `Seb Azure Sandbox`, resource group `rg-aclara-dev-eastus2`.

At 2026-09-27 02:57–02:58 UTC, the current deployed API had **zero replicas** before
the request and one afterward. Two `/healthz` requests hit the 20-second client
timeout (20.267 and 20.240 seconds); the subsequent `/readyz` returned 200 in 8.641
seconds. This reproduces a first-request timeout during scale-from-zero startup.

System event reasons subsequently showed KEDA activation (02:57:38 UTC), replica
assignment, image pull (02:57:41–02:57:48), container creation/start (02:57:54), and
one `ProbeFailed` event. The repeated warm check at 03:00 UTC returned 200 for both
health probes in 0.323/0.287 seconds and readiness in 0.384 seconds. Only event
classes/timestamps were retained; no application console content was collected.

The evidence supports cold startup as the observed cause of these new first-request
timeouts. It does **not** establish the exact cause/duration of the older 120-second
timeout, nor isolate image pull, CPU scheduling, imports and probe startup costs.

The smoke now polls only idempotent health/readiness GETs within a four-minute
budget, with per-request timeouts and visible progress. It never retries a write.
`min_replicas=0` stays in place; no cost/access/resource change was made. Keeping a
warm replica or changing capacity requires a fresh cost estimate and owner approval
if it broadens the approved plan. The frontend should present a startup state and
retry health safely, without extending mutation retries or weakening ingress.

Private aggregate evidence: `artifacts/azure/health-diagnostics-cold.json` and
`artifacts/azure/health-diagnostics.json`.
