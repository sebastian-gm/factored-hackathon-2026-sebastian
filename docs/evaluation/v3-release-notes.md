# After-v2 release / v3 preparation notes

V2 remains the official result. Any later v3 report must say **after fixes, fresh
suite** and disclose that the earlier implementation fixes used v2 post-hoc
analysis. This release preparation does not start v3.

## V3 startup and blind-access disclosure

The first v3 launch at frozen, deployed product SHA
`9f0bff04f28aae4fef6e646575d825fc175b369e` began at
2026-09-28 02:51:36 UTC. It stopped during suite schema validation before its
first case checkpoint or provider reservation: **`ValidationError`**, zero calls,
**$0.00** v3 spend. The v2 schema branch rejected `ScenarioV2.expected` on two
entries of the first suite part. Only the error class, schema model, field path,
validator and aggregate count were inspected; no input value or scenario text was
printed. V1-branch errors were irrelevant to this v2 suite.

During that diagnosis, after the product SHA had already been frozen and deployed,
a broad repository search accidentally matched **two case-template snippets** in
the v3 **authoring tool** and several nearby code references. The search did not
open frozen scenario rows, selection contents, private binding values or results.
The snippets were not used to tune product behavior. This was a breach of the
lead's no-authoring-tool-access rule and is disclosed here. Sebastian explicitly
approved continuing v3 with this disclosure and with no changes under `src/aclara/`,
`prompts/` or `config/`. Subsequent searches exclude the v3 authoring tool and
suite directories.

The contract repair adds the already specified `cancelled` terminal value to the
v2 scenario-level `expected` enum, whose gold outcome enum already allowed it.
The canonical definitions and generated interface snapshot change together, with
an authored contract regression. No v3 suite, selection, binding or product bytes
change. The stopped attempt is preserved separately; the new SHA requires green
CI and fresh release verification before a fresh v3 start. This is a startup
contract repair, not a measured held-out improvement.

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
