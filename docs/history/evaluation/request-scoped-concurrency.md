# Request-scoped concurrency (post-v4)

2026-10-02. Local/mock evidence; zero model spend. Not reflected in official v4
results and not an Azure latency measurement. Source: `ad54866c7c421274041605edaadac50cd54b3b6a`.

## Measured result

| Authored sessions | Wall | Turn p50 | Turn p95 |
|---|---:|---:|---:|
| 3, first batch with cold libraries | 1.832 s | 1.828 s | 1.828 s |
| 5, following warm batch | **1.026 s** | **1.020 s** | **1.022 s** |

Each mock NLU sleeps one second. Five warm sessions previously took 5.026 s
([historical check](local-mock-concurrency.md)). Setup/login is outside timing;
ASGI, memory storage, one authored customer, distinct sessions, no BFF/TLS/cloud.
This is one batch per size, inclusive percentiles on 3/5 observations, no SLO
or equal-cold-state comparison. All five NLU calls ran outside storage; 15/15
concurrent diagnostic reads succeeded (maximum 1.499 ms), five independently
scoped execution records, zero cases and $0. Normal NLG uses templates.

## Safety and boundedness

- Runtime events, model records/deadlines and the mutable AgentAI cursor use
  request contexts inherited by `asyncio.to_thread`. Serving HTTP requests do
  not accumulate a shared history; explicitly supplied offline runtimes retain
  an archive for evaluation compatibility. HTTP traces still use their own buffer.
- Model budget checks/reservations and settlements have short atomic sections;
  provider I/O holds no shared client lock. Unknown cost retains its reservation.
  A prior-day settlement cannot refund the current UTC day's allowance.
- Five admitted turns and 64 pending requests per worker. A local session queue
  and dedicated Postgres session advisory lock cover inference through readback;
  messages and confirmations share this guard. Existing transaction/customer
  locks, RLS, identity revalidation and proposal checks remain in force.
- The dedicated autocommit connection is closed on cancellation/process exit;
  it holds no customer transaction or pooled slot. This adds at most five
  connections per worker (up to nine including the existing four-slot pool).
  Scaling must account for the database connection limit.
- Authored tests force five provider calls to overlap, verify exact event/call
  attribution, order same-session turns across separate API/store instances,
  cancel waiting/held advisory locks and check cleanup, race local budgets and
  cross UTC midnight. No organizer rows or frozen suite are used.

## Verification

```bash
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 make checks
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 .venv/bin/python -m scripts.test_postgres
OPS_BACKEND=memory LEDGER_BACKEND=fixture AGENT_SYSTEM=P \
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 POLARS_MAX_THREADS=2 \
.venv/bin/python -m scripts.local_mock_concurrency \
  --output artifacts/request-scoped-concurrency/results.json
```

Full local checks: **1340 passed / 38 DB skips**, B1 **32/32**, hooks, strict
mypy and interface/policy snapshots. Subsequently added cancellation coverage
also passed the disposable Postgres gate: **86/86**, including cross-instance
serialization. The extra cancellation test requires Postgres. Receipts/logs
are ignored private artifacts; remote PR gates are required before merge.
