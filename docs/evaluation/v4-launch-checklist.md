# V4 launch checklist — not started

Feature freeze: **2026-10-02 12:00 COT / 17:00 UTC**. Freeze plus an explicit
orchestrator run GO is required. No v4 rows, selections, authoring tool or binding
contents have been opened by the lead during this preparation.
An earlier **Oct 1 evening COT** freeze is tentative, pending the round-two work
and live rehearsal blockers; it is not a start authorization.

- [ ] Freeze the product; record clean main equal to origin/main and green remote
  CI/safety at that SHA. Keep official v2/v3 results unchanged.
- [ ] Under release approval, merge the suite release PR from its description and
  structural/hash checks only. Verify manifest pin
  `309c3aa22c2eab51b3289075b733c52bb7934a879299762c3fb9ba16a3d9bec8`.
- [ ] Copy only the approved private binding artifact to ignored
  `artifacts/evaluation-v4/customer-bindings.json`, mode 0600; compare opaque
  checksums to provenance without printing its contents.
- [ ] Verify the local serving DB is promoted and reachable as `aclara_app`;
  pass `EVAL_SERVING_DSN` privately. Loopback, customer RLS, dataset pin and
  120-day window are mandatory. Azure durable budget accounting remains separate.
- [ ] Close and count both dev scopes (`dev-gate/pre-v4` and
  `dev-gate/model-compare`), retaining unknown reserves. Prepare exactly one
  `final-evaluation-v4` / `final-program-v4` run, $3 lifetime. Recheck cumulative
  exposure plus both remaining $0.10 smoke allowances is ≤ $12.
- [ ] Release the frozen main SHA with the full acceptance gate and fresh
  `jev-release.json`. Existing resources/access/min replicas remain unchanged.
- [ ] Run zero-cost structural preflight through the documented final-program
  prepare gate; inspect only sanitized error class/field paths on failure.
- [ ] Immediately before the first launch, run the free OpenRouter credit gate.
  Account balance and the inference key's `limit_remaining` must each be **≥ $4**.
  Use fresh GET responses, not a cached receipt; no management key or inference
  probe is needed. Preserve only the sanitized numeric receipt.
- [ ] Obtain the final run GO. Execute the detached documented `start` once;
  use `resume` only after an authorized stop diagnosis. Never restart/reset spend.
- [ ] Watch progress: stop on 15-minute stall, three-hour wall clock, error or
  budget denial. Never print Pydantic input values or row-level journal content.
- [ ] Confirm B1 100 + P-Gemini 160 system runs; frontier OFF; frozen 30 repeat
  and 30 dual-judge selections, 1024-token Sonnet cap. Do not resample.
- [ ] Report aggregate primary metrics, safety counts, ES/PT slices, paired
  interval, flips, judge coverage/agreement, latency, costs and private human
  sheet path. Disclose partial phases. No result-informed product change/rerun.

Exact commands and immutable resume rules:
[final-run-plan.md](final-run-plan.md),
[v4-program-readiness.md](v4-program-readiness.md).
Submission warm replicas, judge ingress/publication and resource changes need
Sebastian's separate submission-day approval; they are not enabled by this list.

## Exact local-serving launch commands

Run from the repository root. This helper constructs the non-owner local serving
DSN in memory from the ignored `.env`; it does not print credentials, pass them
in argv, or substitute the Azure serving endpoint. The final program itself
validates loopback, role, dataset and immutable release pins. Existing local
configuration is required; no data load or resource change is performed here.

```bash
v4() {
  .venv/bin/python - "$@" <<'PY'
import os
import subprocess
import sys
from dotenv import dotenv_values
from psycopg.conninfo import make_conninfo

values = dotenv_values(".env")
environment = dict(os.environ)
environment["EVAL_SERVING_DSN"] = environment.get("EVAL_SERVING_DSN") or make_conninfo(
    host="127.0.0.1",
    port=values.get("POSTGRES_HOST_PORT") or "15432",
    dbname=values.get("POSTGRES_DB") or "aclara",
    user="aclara_app",
    password=values.get("OPS_APP_PASSWORD") or "",
)
raise SystemExit(subprocess.call([
    sys.executable, "-m", "scripts.final_program", *sys.argv[1:],
    "--suite", "test-v4",
    "--bindings", "artifacts/evaluation-v4/customer-bindings.json",
    "--manifest-pin", "309c3aa22c2eab51b3289075b733c52bb7934a879299762c3fb9ba16a3d9bec8",
], env=environment))
PY
}
```

**After confirmed freeze/release approval**, integrate the pinned suite/bindings
and verify the accepted main SHA and deployment gates first. The next command
closes both dev scopes and creates the single $3 v4 purse, preserving all charges
and unknown reservations. Its live cumulative check includes the two remaining
$0.10 smoke allowances and must stay ≤ $12:

```bash
FINAL_BUDGET_PREPARATION_APPROVED=1 \
  .venv/bin/python -m scripts.final_budget --prepare --suite test-v4 \
  --bindings artifacts/evaluation-v4/customer-bindings.json \
  --manifest-pin 309c3aa22c2eab51b3289075b733c52bb7934a879299762c3fb9ba16a3d9bec8
v4 prepare
.venv/bin/python -m scripts.openrouter_preflight
v4 status
```

**After the explicit final-run GO only**, recheck credits and launch once:

```bash
.venv/bin/python -m scripts.openrouter_preflight && \
  LLM_FINAL_RUN_STARTED=1 LLM_REAL_CALLS_APPROVED=1 v4 start
v4 status
```

The launcher detaches its worker with `start_new_session=True`, disconnected
stdin and ignored, mode-0600 `artifacts/final-program-v4/worker.log`; it survives
the shell/session ending. No second `start` is permitted. Check status periodically;
the watchdog stops on 15 minutes without progress, three hours total wall time,
budget denial or error. Under an authorized recovery on the **same pinned SHA**:

```bash
LLM_FINAL_RUN_STARTED=1 LLM_REAL_CALLS_APPROVED=1 v4 resume
v4 status
```

Neither budget preparation, suite preparation, start nor resume was executed
while writing this checklist. The runner's detached/resume behavior was exercised
only in the zero-spend retired-v3 rehearsal. The free credit helper was checked
with authored HTTP mocks and the inference key's two metadata GETs; it never
calls a completion endpoint or prints the key, account label or raw response.
