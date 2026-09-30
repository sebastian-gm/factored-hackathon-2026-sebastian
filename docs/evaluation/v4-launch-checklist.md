# V4 launch checklist — not started

Feature freeze: **2026-10-02 12:00 COT / 17:00 UTC**. Freeze plus an explicit
orchestrator run GO is required. No v4 rows, selections, authoring tool or binding
contents have been opened by the lead during this preparation.

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
