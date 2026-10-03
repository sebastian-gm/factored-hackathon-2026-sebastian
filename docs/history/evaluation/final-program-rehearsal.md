# Final-program rehearsal — 2026-09-30

This is an operational development rehearsal on **retired test-v3**. It is not a
new official evaluation, a model comparison, or a change to the v3 results. V4
rows, selections and bindings were not opened. No product, prompt, policy,
configuration or Azure changes were made. No real models were called.

## Verified execution

Command, run from a clean checkout:

```bash
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 LLM_REHEARSAL_APPROVED=1 \
  .venv/bin/python -m scripts.rehearse_final_program --name sept30-b
```

The three programs completed in **178.97 seconds total**, pinned to runner SHA
`af769b7c776f160c23cbd1b2df6cc5ab834be41c`. The subsequent CLI-only guard moves
`--rehearsal` onto the final-program parser so the paid budget command cannot
silently accept and ignore it; the launcher and parser regressions pass.

Each program reads the existing **local** organizer serving projection through
`aclara_app` and forced customer RLS. All 260 system runs use B1, including the
logical P and repeat positions; reports label these `B1-repeated`. The judge phase
uses `StructuredClient` with a mock adapter, the real judge schema/prompt and
1024-token limit. Its second rubric is an identical synthetic copy, not a TypeSafe
SDK call. Mock agreement is not evidence of vendor or human agreement.

| Program | System runs | Judge items | Completed units | Unit attempts | Mock calls | Unscored failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `sept30-b-baseline` | 260 | 60 | 320 | 320 | 60 | 0 |
| `sept30-b-resumed` | 260 | 60 | 320 | 320 | 60 | 0 |
| `sept30-b-faults` | 260 | 60 | 320 | 321 | 61 | 1 |

Every program produced `results.json`, `results.md` and a 20-item human sheet
under its own ignored `artifacts/final-program-rehearsal/<name>/`. Connection files
are mode 0600. The aggregate evidence is
`artifacts/final-program-rehearsal/sept30-b-summary.json`. All worker PID files are
absent and their exclusive locks are free. Resuming the completed resumed program
returned “Program already complete; no requests sent”; its 60 journaled mock calls
were unchanged.

### Interruptions and equality

- Sent actual SIGTERM after the 12th committed system result, then used `resume`.
- Sent actual SIGTERM after the 12th committed judge result, then used `resume`.
- Both stops recorded `InterruptedError`. No completed unit was replayed: 320
  attempts for 320 units, and exactly the baseline's 60 mock calls.
- All objective aggregates and their intervals, including slices, safety, costs,
  readbacks and paired/repeat measures, matched the uninterrupted program exactly.
  Judge aggregates also matched after both resumes.
- Actual latency, component times and recovery counters are explicitly excluded
  from the equality projection. They measure separate executions and must not be
  fabricated into byte-identical results. The fault run has one genuine recovered
  case attempt and one deliberately unpaired judge item.

### Injected failures

1. **Database blip:** after 22 committed system runs, the next unit attempted a
   local serving connection on an exclusively reserved, non-listening port. This
   produced a real `psycopg.OperationalError` without stopping shared Postgres or
   changing its firewall. The worker stopped with sanitized exception metadata,
   retaining checkpoints. A non-owner `SELECT 1` on the original local serving DSN
   succeeded; one `resume` completed the remaining workload. Only the unfinished
   unit acquired a second attempt. The injection marker, metadata event and summary
   preserve evidence of the stop.
2. **Judge length failure:** one mock response at judge position 11 returned
   `stop_reason=length`. The real structured client exhausted its two bounded
   attempts, journaled two refusals and raised `ModelFailure`. The runner saved
   `judge_failed` with null scores, then continued: 59 paired items, one failed
   item, complete primary/report output. This is disclosed partial judging, never
   an invented score. Authored tests verify that resume does not replay this failed
   item and that budget refusal/connectivity errors still stop.

## Durable zero-spend gate

Exact scope/run identities:

| Scope | Run ID | Lifetime cap |
| --- | --- | ---: |
| `rehearsal/final-program/sept30-b-baseline` | `rehearsal-sept30-b-baseline` | $0 |
| `rehearsal/final-program/sept30-b-resumed` | `rehearsal-sept30-b-resumed` | $0 |
| `rehearsal/final-program/sept30-b-faults` | `rehearsal-sept30-b-faults` | $0 |

Each has its own disposable **local** Postgres database. Production migrations
require positive caps, so the rehearsal adapts only the check constraints in that
new database to allow zero for `rehearsal/%`. Production schema/migrations and the
actual `llm.reserve` function are unchanged. The non-owner `PostgresSpendGate`
attempted a positive $0.00000001 reservation before execution; the actual function
denied it. Connectivity failures are not accepted as proof of budget denial.

Owner readback after all phases/resumes confirmed enabled $0 limits, one lifetime
run, **zero paid reservations, $0 charged and zero unknown costs** in all three
databases. Existing cloud/dev/final scopes were not changed. Mock calls naturally
have no paid reservation; this does not claim to test live provider cancellation
or billing. Durable reservation/restart tests are also covered by the separate
local Postgres gate.

## Runner changes

- An explicit rehearsal mode requires retired v3, local non-owner serving, a
  separate artifact/database identity, mock mode and real-call approval **off**.
  It refuses v4 and never fetches Key Vault secrets. Names, binding/manifest,
  implementation, serving identity and injection controls are pinned on resume.
  Existing paid-start/deployed-release guards remain required for real programs.
- Exhausted judge `ModelFailure` becomes a checkpointed failed/unpaired item.
  Other judge items and primary reports continue. `FinalBudgetStop`,
  `BudgetFailure` and unexpected infrastructure errors still fail closed.
- STOPPED metadata includes exception **class chains only**, helping distinguish
  database failures from wrapper errors without echoing row text or credentials.
  Resume clears the previous stop marker when the new worker owns its lock.
- Serving is closed if initialization of the budget store fails.
- The reproduction controller sends real signals, verifies checkpoint/journal
  counts and compares objective aggregates. Its first development run completed
  all programs but incorrectly included six repeated-latency fields in equality;
  the projection and authored regression were corrected. Those earlier `sept30-a`
  artifacts are retained unchanged.

## Verification commands

| Command | Verified outcome |
| --- | --- |
| `python -m scripts.rehearse_final_program --name sept30-b` with the mock environment above | All three complete; two SIGTERMs; connectivity stop/resume; one bounded judge failure; identical objective aggregates |
| `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/pytest` with mock mode | 497 passed, 21 skipped before the final CLI-only guard |
| `.venv/bin/pytest tests/test_program_rehearsal.py tests/test_final_program.py tests/test_program_v3.py tests/test_program_v4.py` | 33 passed on the final candidate; authored fixtures only |
| `.venv/bin/python -m scripts.test_postgres` | 24 passed in a separate disposable local database |
| `.venv/bin/pre-commit run --all-files` | Passed using repository-local caches |
| `.venv/bin/ruff check .`; `.venv/bin/mypy --strict src/aclara` | Passed |
| `.venv/bin/python -m compileall -q src evals scripts` | Passed |
| `.venv/bin/python -m scripts.export_interfaces --check`; `.venv/bin/python -m scripts.generate_policy_catalog --check` | Passed |
| `.venv/bin/python -m evals.runner --system B1`; same with `--scenarios evals/dev_scenarios_v2.yaml` | Both exited 0; reactive suite 32/32 |
| `.venv/bin/python scripts/check_staged_files.py --working-tree` | Passed |

The first full pytest invocation in the restricted sandbox stalled and was
terminated; it is not counted as passing. The completed invocation used authorized
local connectivity and numerical-library thread limits. Private logs remain under
`artifacts/integration/checks/`. No product repair was made for that test-process
stall.

## Reproduce or recover

Without organizer data, run the authored runner tests and the disposable Postgres
gate above. The complete rehearsal additionally requires the ignored v3 bindings,
matcher split artifacts and the local serving load from the documented pipeline.
It derives DSNs only from local `.env`; provider keys are unnecessary and inherited
`*_API_KEY` values are removed in the worker.

Use a **new** short name for a new rehearsal; existing directories/databases are
never reset. If interrupted, restore the recorded implementation SHA and controls,
then resume the affected leaf program:

```bash
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 LLM_REHEARSAL_APPROVED=1 \
  .venv/bin/python -m scripts.final_program resume \
  --suite test-v3 --rehearsal <existing-program-name>

.venv/bin/python -m scripts.final_program status \
  --suite test-v3 --rehearsal <existing-program-name>
```

Do not use `start` twice. The controller refuses existing programs; its commands
and checkpoint evidence remain available for manual recovery. A fresh final-v4
program still requires the feature freeze, pinned release acceptance gates and
the owner's go. This rehearsal makes no claim about live-provider availability,
actual LLM latency, Azure connectivity or model quality.
