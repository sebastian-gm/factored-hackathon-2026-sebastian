# After-v2 release / v3 preparation notes

V2 remains the official result. Any later v3 report must say **after fixes, fresh
suite** and disclose that the earlier implementation fixes used v2 post-hoc
analysis. This release preparation does not start v3.

## Post-gate baseline fix

After the accepted real dev gate (20/20, blind 18/20, 12/12, 0/52 unsafe), the mock
Azure smoke exposed a deterministic fallback defect before policy execution.
Blank merchant names matched every query and the new numeric-merchant cleanup
then corrupted the parsed amount. An authored fixture reproduced zero candidates
despite an exact named target; excluding blank merchant names restored that target.

The orchestrator explicitly approved this minimal guard, conditional on B1 32/32,
mock P 20/20 no-fault + 12/12 faults, disclosure and green CI. At code commit
`4fee1ee3db7428a5564ecbc634bb62e0ae7049d5`:

- Three independent authored regressions passed.
- B1 remained **32/32**, 12 readbacks, safety guards passed.
- Mock P passed **20/20 + 12/12**, all 12 faults triggered, **0/32 unsafe/forbidden**,
  zero execution errors and **$0** provider cost.
- No paid dev or confirmation repeat, v3 input inspection, frozen-file edit,
  learned MATCH threshold change, NLU/prompt change or policy change occurred.

This is a disclosed **post-gate baseline fix** affecting B1 and P's deterministic
fallback. The paid gate below its original SHA is preserved; no new paid acceptance
or held-out improvement is claimed. See [the dev report](after-v2-dev-gate.md) for
commands and ignored evidence paths, and [the final-run plan](final-run-plan.md)
for fixed workload, budget enforcement and start/resume commands.

## Release evidence

Runtime smoke SHA: **`81ce84ec6c6e1c93063bbaf84eb67dd3d98e604e`**. PR #58
and main passed all four checks. Main CI `36369151946`, safety `36369151820`,
and external-access workflow `36369616217` passed. API/web images were built,
pushed privately and applied in the approved subscription. Mock serving smoke
and replacement-replica recovery, Azure controls, real ES/PT/fraud checks and
the three-surface browser check passed.

The first real smoke stopped at a stale assertion requiring model execution for
explicit stolen-card language. ADR-0015's deterministic pre-NLU guard had already
created and read back the correct handoff. The verification script now requires
zero NLU/provider calls, `FRD-01` + `AUTH-02`, readback and logout for that path;
ES/PT still require valid Gemini/Jev calls and union checks. The corrected fraud
check passed without provider spend. No product behavior was changed for this
verification correction, and neither image contains the smoke script.

Combined API/browser smoke: **$0.00802475 / $0.10**, nine settled provider
attempts, no unknown costs or fallback calls. Five conversation allowances were
used, including the failed assertion and its zero-cost correction. Browser and
explicit-fraud handoffs used deterministic guards. V3 remains at **zero calls**.

The final release SHA, image-digest equivalence for the docs/verification-only retag,
CI/safety/access runs, smoke receipts and durable budget are recorded in ignored
`artifacts/azure/jev-release.json` and the current progress-log entry. Do not start
the prepared v3 program until those gates pass and the orchestrator supplies a go.
