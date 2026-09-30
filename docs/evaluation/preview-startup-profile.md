# Preview startup profile — 2026-09-29 PDT

Read-only investigation of deployed preview
`dac38017d4ea9910afc3aa4851f661dd6608b7ce`, explicitly in `Seb Azure Sandbox` /
`rg-aclara-dev-eastus2`. No Azure setting, replica limit or image was changed.
No paid model call or banking write was made. Credentials stayed in memory;
only timings, sizes, event types and verification booleans were displayed.

## What the 86 seconds measures

The earlier authenticated cold BFF `me` request took **86.059 s**, with both web
and API at zero before the read. This is **web → internal API end-to-end wall
time**, not an 86-second Python initialization measurement.

For that read, web readiness was logged at **02:23:30.7019168 UTC** and Uvicorn
startup completed at **02:24:14.2825084 UTC**, a **43.581 s gap**. API server-start,
ASGI-startup and ready markers then occurred within approximately 1 ms. The
application's synchronous imports and `create_app()` run *before* those markers,
so fast ASGI startup alone does not establish fast total initialization.

The remaining approximately 42.5 s includes the preceding web activation and
request/network overhead; it cannot all be assigned to a specific platform
stage from the retained logs. Warm authenticated me/transactions reads took
approximately 0.1–0.2 s in the original smoke and passed, including the clock.

## Measurements and code paths

| Component | Evidence | Interpretation / limit |
| --- | --- | --- |
| API image | `docker image inspect`: **237,903,813 bytes (226.88 MiB)**. Web: **75,771,752 bytes (72.26 MiB)**. | Cached Docker image sizes, not compressed network transfer sizes. |
| Image activation | Private Azure system event on a later API activation: image pull **7.54 s**, completed 02:34:30.9306634; container started 02:34:36.7850873 (**5.854 s later**). | Platform activation adds real delay. This is a different activation from the 86 s smoke, so the durations cannot be added to its timeline. |
| Imports / fixture app readiness | Cached production API image, `--network none --cpus 0.25 --memory 512m`, mock/memory/fixture settings: **6.399 s total**. FastAPI 2.805; psycopg pool 0.879; TypeSafe SDK 0.516; NumPy 0.903; remaining matching imports 0.581; remaining API/app construction 0.715 s. | Sequential, one-run local measurement at the deployed resource limits. Excludes Azure scheduling, network/DB and serving startup. Shared imports are already cached between stages. |
| Matcher | No `lightgbm` module loaded at fixture readiness; constructing `MatchState` afterward took **2.479 s**. | `app.py` creates the matcher only on the first P MATCH. It does not explain cold `me`/clock/transactions readiness. |
| TypeSafe / provider initialization | SDK import 0.516 s locally; `AgentAI` constructor with the selected real-provider configuration and durable gate **0.015 s**. | No provider request or Jev client call occurred. `TypeSafeClient` is constructed inside risk evaluation, not at API startup. |
| First pooled TLS connection and scoped checks | Non-owner Azure DB read from workstation: **2.300 s**. | Includes role/config/session scope statements. Not an in-region Azure measurement. |
| Serving identity / personas / hints / directory | **0.882 / 0.702 / 3.302 / 0.893 s**, respectively, from workstation. | No rows printed. Identity and RLS checks retained. Constructor eagerly computes demo hints; MX hint calculation reads a snapshot twice outside the HTTP request cache. Network round trips inflate these workstation timings. |
| Readiness | Both deployed probes have a **10 s interval**. API `/readyz` creates a fresh DB connection, checks operational scope, and checks serving identity through the pool. | Probe scheduling can add waiting and DB work. Exact contribution was not measured. Do not weaken identity/RLS readiness checks. |

The first pooled workstation profiling attempt timed out before completing.
A subsequent direct TLS check succeeded, the workstation IPv4 still matched the
existing firewall rule, and the repeated serving profile completed. No firewall
or connection setting was changed. This transient workstation timeout is not
evidence of an 86-second deployed DB startup.

ARM also reports polling interval 30 s and cooldown 300 s. Do **not** conclude
that HTTP cold starts incur a fixed 30 s polling wait: Microsoft's
[scaling documentation](https://learn.microsoft.com/en-us/azure/container-apps/scale-app)
distinguishes HTTP scaling from custom event-source polling. Its
[probe documentation](https://learn.microsoft.com/en-us/azure/container-apps/health-probes)
describes readiness separately. Our sampled events do not provide a complete
request-to-activation trace.

These observations support sequential scale-from-zero, image/container
activation, imports and readiness work as contributors. They do not support
attributing the delay to a model request, matcher loading at readiness, or a
demonstrated new serving bug. The complete platform/application decomposition
remains unmeasured.

## Proposed code improvements, not implemented

Keep min replicas zero, the longer GET timeout, GET-only retry and ES/PT startup
state. No new resource or always-on service is proposed.

1. **Add aggregate startup timings** around imports, first connection, identity,
   personas, demo hints and directory construction. Log stage names and elapsed
   time only. Correlate these with replica events during the next approved
   preview/release; this would resolve the current timing gap without model calls.
2. **Reuse scoped snapshots while computing startup hints**, then immediately
   discard that cache. MX currently reads the same owned projection twice.
   Retain the serving-version and RLS checks and add a startup isolation test.
   This may save round trips; the current evidence does not establish the size
   of an in-region improvement.
3. **Defer matcher-only imports until MATCH**, preserving artifact checksum and
   authorization checks. NumPy alone cost 0.903 s here. This moves work to first
   chat; it will not remove the platform activation delay.
4. **Separate pipeline-only dependencies from API installation.** `_duckdb`
   occupies **57.66 MiB** in the cached image and is not needed by the API
   startup path. Move ETL dependencies to an explicit pipeline extra only after
   checking pipeline, matcher and Docker dependency closure. Image reduction
   does not imply a proportional cold-start reduction.
5. **Consolidate readiness DB work in the existing non-owner pool**, preserving
   the same DB availability, role, operational and serving-identity failures.
   Removing the redundant fresh TLS connection may reduce probe latency. Test
   DB outage, unauthorized role and serving-version changes before release.

All five remain proposals. No lazy-import, dependency, cache, probe, readiness
or infrastructure optimization was applied in this session. Releasing code
changes still needs the established gates; replica/probe Azure changes remain
outside this work.

## Reproduction / receipts

Executed `docker image inspect`, a network-disabled CPU-limited `docker run`
import/constructor profile, `az containerapp show` and private system-log reads.
Azure CLI calls specified the approved subscription and resource group.
Non-owner `psycopg` TLS reads measured serving stages and verified the existing
firewall allowlist without displaying its IP or customer projections.

Ignored evidence: `artifacts/startup-profile/readonly.json`, the read-only helper
and private system-event captures, plus the earlier
`artifacts/preview-release/read-only.json` and private console logs. The latter
retain only the prior authenticated smoke; no new cold HTTP or paid chat test is
claimed here. Product integration gates are in the
[review record](../reviews/pr-65-66-integration-review.md).
