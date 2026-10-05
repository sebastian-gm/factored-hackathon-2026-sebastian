# Post-v4 final-build regression

**Regression replay on the final build, NOT a new held-out evaluation.**
Sebastian authorized this replay in handoff 20 on October 5. Official v4 scores,
artifacts, suite bytes and bindings remain unchanged. No tuning on replay
outcomes is authorized. P runs once on all 100 previously evaluated cases. The
previously flagged eight run first and are reported as a subset, without a
second paid pass. B1 runs once at zero model cost. There are no judges or repeats.

The lifetime Postgres purse is `regression/final-build/v4`, run `final-build`,
**$0.30**, with reserve-before-call semantics across retries, fallback and
resumes. Unknown costs remain reserved and stop the worker. Clean main, an exact
SHA, unchanged suite/binding hashes and a local non-owner serving endpoint are
pinned. The serving load must include `temporal_quality_reason`; source reads use
forced RLS. Operational mutations are isolated in memory per case. Local serving
avoids workstation-to-Azure ledger hops; this is not deployed latency evidence.

After final-candidate merges, use an ignored launcher that sets a local
`EVAL_SERVING_DSN` without printing it. It obtains model and budget credentials
from Key Vault in memory, never from command arguments. Exact entry points:

```sh
LLM_REGRESSION_APPROVED=1 LLM_REAL_CALLS_APPROVED=1 \
  nohup .venv/bin/python -m scripts.final_build_regression start --real \
  > artifacts/final-build-regression/worker.log 2>&1 < /dev/null &
.venv/bin/python -m scripts.final_build_regression status --real
# Only after a stop, with the same SHA and pins; never start again:
LLM_REGRESSION_APPROVED=1 LLM_REAL_CALLS_APPROVED=1 \
  nohup .venv/bin/python -m scripts.final_build_regression resume --real \
  > artifacts/final-build-regression/resume.log 2>&1 < /dev/null &
```

Create the ignored output directory with mode 0700 first and use `umask 077`.
Watchdog: 15-minute stall, three-hour worker wall time, or budget/error. Results
and progress contain only aggregate counts and case IDs. Checkpoints and validated
provider journals remain ignored, mode 0600. No official final-program directory
is read or overwritten. This page will record the resulting counts and cost,
whatever they are, after the one approved final-candidate run.
