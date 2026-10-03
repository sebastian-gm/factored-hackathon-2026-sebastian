# Local mock concurrency after #116

2026-10-02. **Local/mock, zero model spend. Not an Azure or production SLO
measurement.** No organizer inputs, frozen-suite runs or infrastructure changes.

This is historical evidence before request isolation. See the
[post-v4 concurrency check](request-scoped-concurrency.md) for the later fix.

## Result

| Measurement | Concurrent sessions | Wall time | Turn p50 | Turn p95 |
|---|---:|---:|---:|---:|
| External audit at `360d4c1` | 3 | 3.780 s | Not reported | Not reported |
| Current local/mock check | 3 | **3.836 s** | **2.830 s** | **3.732 s** |
| Current local/mock check | 5 | **5.026 s** | **3.017 s** | **4.823 s** |

The service still **serializes chat turns** through `ai_turn_lock` and its
shared adapter. The three-session wall time is close to the audit's 3.78 s;
this is not evidence of higher chat throughput. The five-session turn times
include time waiting for that lock.

All **5/5 NLU calls** ran outside an operational transaction. During the first
one-second mock wait, **15/15** concurrent health/identity/transaction reads
returned 200; the slowest took **0.910 ms**. Each session retained exactly one
execution record and one NLU event. There were **0 case writes / $0 model cost**.
#116 makes blocking inference explicit and releases storage while it waits;
it retains serialization to protect shared adapter bookkeeping. Separate
regressions cover revalidation, cancellation and durable storage.

## Reproduce

From the repository root:

```bash
OPS_BACKEND=memory LEDGER_BACKEND=fixture AGENT_SYSTEM=P \
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 POLARS_MAX_THREADS=2 \
.venv/bin/python -m scripts.local_mock_concurrency
```

Defaults are batches of 3 and 5 sessions, with a **1.000 s mock delay per NLU
call**. The helper hardcodes mock routes, a zero-dollar client budget and
in-memory authored fixtures. An authored regression also forbids the provider
HTTP function under contrary ambient real-provider settings.

`LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 make checks` passed **1216 tests /
31 DB skips**, B1 **32/32**, hooks, strict mypy and interface/policy snapshots.

Setup/login/OTP is outside the measured interval. Each batch uses one API app,
five or three distinct authenticated sessions/conversations for **one authored
customer**, and a single shared adapter. Requests use HTTPX ASGI transport;
there is no socket, BFF, TLS, cloud hop or real provider. Normal explanations
use the deterministic template, so there is one NLU call and no phrase call
per turn. Queued request time and concurrent diagnostic reads are included.

Aggregate receipt and timing samples: ignored
`artifacts/local-mock-concurrency/results.json` (0600). Measured source:
`4538179edc179fd5b5f43c5b53f981aec618e355`, the hygiene candidate after #116;
the later #124 refresh moves offline studies without changing these runtime
paths. The three-session batch ran first; the five-session batch followed in
the same process and could reuse loaded libraries/model caches. Its timing
should not be treated as a comparison of equal cold states. This is one batch
per size; p95 uses inclusive interpolation on 3/5 observations, without an
interval or a production percentile claim.

The external audit reported only wall time, so its p50/p95 cannot be
reconstructed. Removing the shared turn lock requires request-local adapter
records, bounded admission and preserved session/customer locking; that work
was not implemented here. CPU, replicas and worker count are unchanged.
