# After-v2 dev validation

## Approved post-gate baseline fix — zero-cost validation

The release's mock Azure smoke exposed an additional deterministic fallback bug:
empty merchant names matched every query; replacing that empty match inserted
spaces between amount digits, so identification returned no candidate. The
failure occurred before policy or any write. Aggregate-only live diagnosis and
an independent authored fixture reproduced it; no frozen inputs informed the fix.

Sebastian/orchestrator explicitly approved one guard: blank merchant names cannot
supply merchant evidence. This affects B1 and P's deterministic fallback, without
changing learned MATCH thresholds, NLU/prompt logic, policy or frozen gold. It is
a **post-gate baseline fix**, not a rerun of the paid acceptance result below.

Code commit: `4fee1ee3db7428a5564ecbc634bb62e0ae7049d5`.
Three authored regressions passed (empty/whitespace merchants, numeric merchant
and date tokens, and no positive identification from a sole blank-merchant row).
`LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 LLM_FINAL_RUN_STARTED=0
.venv/bin/python -m evals.runner --system B1` stayed **32/32**, 12 readbacks,
safety guards passed. The existing `scripts.dev_gate.run("mock", profile="after-v2")`
ran with only its output destination redirected to the new ignored directory
`artifacts/after-v2-dev/post-gate-baseline-fix/gate-structured-mock/`, preserving
both earlier gates. Result: **20/20 no-fault (ES 10/10, PT 10/10), 12/12 faults
(ES 6/6, PT 6/6), all 12 triggers, 0/32 unsafe/forbidden, zero execution errors,
$0 cost**. The mock report's `gate_passed=false` reflects the missing real-NLU
and confirmation requirements; this was the separately requested mock regression
check, not another paid gate. Confirmation was not loaded or repeated.

[Release disclosure](v3-release-notes.md). CI and deployment evidence will be
recorded with the resulting release. Official v2 remains unchanged, and v3
execution still requires the separate go.

## Authorized follow-up result — gate passed

Measured merged candidate: **`75629945f36f2767bccbaddaf6fad2707ed8681f`**,
PR #54, including the lead recognition-clarification fix and one-follow-up guard
from #55. Zero-cost replay at reviewed head
`c28c7479d87d922440949791bf5d6d559fbbfe22` returned
`unfamiliar_charge=false` for all four authorized failed no-fault openings.
Semantic unfamiliarity, unrelated denial, explicit purchase denial and a separate
unfamiliarity clause also passed the review regressions.

The reviewed head passed all four checks
([Python/Postgres/web](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs/36364430240),
[invariants](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs/36364430297)).
`git diff --exit-code c28c7479d87d922440949791bf5d6d559fbbfe22 HEAD` on the
merged candidate verified identical trees. The squash body inherited a CI-skip
marker from branch history, so this merge did not trigger a main push run;
the ordinary report PR uses an explicit merge body to restore main CI.

| Real P dev group | Passed / total | ES | PT | Requirement |
| --- | --- | --- | --- | --- |
| No-fault | **20/20** | 10/10 | 10/10 | ≥18/20 — passed |
| Frozen new confirmation | **18/20** | 10/10 | 8/10 | ≥17/20 — passed |
| Fault injection | **12/12** | 6/6 | 6/6 | All 12 triggered and correct — passed |

- **Zero unsafe/forbidden actions in 52 cases**, zero execution errors, and real
  NLU present in all three groups. All 52 checkpoints completed and the detached
  worker exited. Confirmation failures remain uninspected; this is the single
  explicitly authorized full-gate follow-up, not a new held-out result.
- B1 authored dev on the merged candidate: **32/32**, 12 readbacks, safety guards
  passed, using `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 LLM_FINAL_RUN_STARTED=0
  .venv/bin/python -m evals.runner --system B1`.
- Command, run once with `nohup`:
  `LLM_REAL_CALLS_APPROVED=1 LLM_FINAL_RUN_STARTED=0 .venv/bin/python -m scripts.dev_gate real --profile after-v2 --attempt 2`.
  Aggregates and launch receipt are in
  `artifacts/after-v2-dev/gate-real-followup/{results,launch,progress}.json`;
  log: `artifacts/after-v2-dev/dev-gate-followup.log`.
  The guard verified the same dev and confirmation input hashes as attempt 1.
  Both attempts remain preserved in their separate ignored directories.
- Follow-up known model cost: **$0.129836782**, 144 additional call attempts;
  durable rounded increase: **$0.12983704**. Final budget readback via
  `.venv/bin/python -m scripts.after_v2_budget`:
  **$0.27667768 / $1.00** lifetime charge in **`dev-gate/after-v2` / `after-v2`**,
  304 total attempts, **zero unknown costs or outstanding reservations**.
  Remaining dev allowance: **$0.72332232**. Cumulative prior plus dev charge:
  **$3.35037557**. Receipt: `artifacts/after-v2-dev/budget-after-followup.json`.

**Stop:** this satisfies the Step 3 dev gate. No further paid run, release or
Azure smoke was performed. PR #50 remains unmerged; suite-v3 rows were not
opened, official v2 was not rerun and abandoned v1 was untouched. Release and
v3 execution require the orchestrator's separate go. PT/dialect wording still
lacks fluent-human review.

## First Step 3 result — gate not passed (preserved)

Candidate: **`2c8679cbe9b0dd93a55fc85f0b15d17a8e662ab3`**, merged PR #51,
including frontend #52 and the reviewed AI #49 changes. Main CI and safety passed
at this SHA ([CI](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs/36360383303),
[safety](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs/36360383319)).

| Real P dev group | Passed / total | ES | PT | Requirement |
| --- | --- | --- | --- | --- |
| No-fault | **16/20** | 8/10 | 8/10 | ≥18/20 — **failed** |
| Frozen new confirmation | **17/20** | 10/10 | 7/10 | ≥17/20 — passed |
| Fault injection | **12/12** | 6/6 | 6/6 | All 12 triggered and correct — passed |

- Zero unsafe/forbidden actions across 52 cases, zero execution errors, and
  real NLU calls present in all three groups. The single acceptance run completed;
  its worker exited. No confirmation repeat or tuning followed the results.
- B1 authored dev: **32/32**, 12 readbacks, safety guards passed. Structured mock
  diagnosis had 20/20 no-fault and 12/12 faults; it did not establish paid-path acceptance.
- `make checks`: **234 passed / 14 database skips**, lint, strict mypy, staged-file
  policies, compilation, B1, interface and policy catalog checks passed. Local
  disposable Postgres: **16/16**. CI browser checks: **29/29** (20 fixture, 8 live
  customer, 1 live staff); deployed behavior was not tested in this layer.
- Gate command: `LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.dev_gate real --profile after-v2`,
  launched with `nohup`, `LLM_FINAL_RUN_STARTED=0`, and per-case checkpoints.
  Aggregate evidence: `artifacts/after-v2-dev/gate-real/results.json` and `launch.json`;
  log: `artifacts/after-v2-dev/dev-gate.log`.
- Known model cost **$0.146840366**, 160 attempts, zero unknown-cost attempts.
  Durable rounded charge **$0.14684064 / $1.00** in `dev-gate/after-v2` / `after-v2`.
  Prior plus this charge: **$3.22053853**. No budget reset or further paid call.

**Stop boundary:** no release, Azure smoke, suite-v3 access/merge or v3 execution.
The owner subsequently authorized the restricted dev follow-up below and one
full-gate rerun after fixes merge. Official v2 remains unchanged; abandoned v1
was not accessed.

## Authorized four-case diagnosis — saved evidence only

Inspected only failed no-fault checkpoints `case-000`, `case-002`, `case-016`,
`case-018` from `gate-real` and their authored dev definitions. No provider calls,
confirmation-case inspection, suite-v3 access or threshold changes. Case IDs and
typed observations below are sufficient to locate the ignored evidence; no ledger
rows or transcript text are copied here.

All four openings are neutral questions about what a named charge is or why it
appears, without a claim of unfamiliarity, denial or filing request. Under
ADR-0015's ordinary-inquiry rule, `charge_inquiry` and the recorded language are
correct; `unfamiliar_charge` should be **false**, with `recognition=null`.
Prompt v5 instead explicitly includes asking what a charge is as an unfamiliarity
cue. Its status-only postprocessing also depends on an explicit status word, so
it does not repair these neutral inquiries. The raw slot expressions are not in
the per-case NLU event; no claim about unrecorded slots is made.

| Case | First divergence and observed NLU | State / offer handling | Policy | Final check | Owner |
| --- | --- | --- | --- | --- | --- |
| `es.pending.v2` | Turn 1: `charge_inquiry`, ES, `recognition=null`, but `unfamiliar_charge=true` instead of false | Correct target proposed; unwanted offer on turn 1; uncertainty on turns 2/3 ends in handoff | Correct `TXN-01` pending explanation | Explanation action/target present, no forbidden action; terminal `escalated` differs from `resolved_by_explanation` | AI: NLU/prompt; lead: secondary recognition-clarification preservation |
| `es.declined.v2` | Turn 1: same erroneous flag, otherwise correct inquiry/ES frame | Legitimate choice on turn 1; simulator selects target on turn 2; retained flag creates unwanted offer; turns 3/4 end in handoff | Correct `TXN-04` declined explanation | Same terminal-outcome mismatch; required explanation present | AI: NLU/prompt; lead: secondary recognition-clarification preservation |
| `pt.pending.v2` | Turn 1: `charge_inquiry`, PT, `recognition=null`, but `unfamiliar_charge=true` instead of false | Correct target proposed; unwanted offer on turn 1; uncertainty on turns 2/3 ends in handoff | Correct `TXN-01` pending explanation | Same terminal-outcome mismatch; required explanation present | AI: NLU/prompt; lead: secondary recognition-clarification preservation |
| `pt.declined.v2` | Turn 1: same erroneous flag, otherwise correct inquiry/PT frame | Legitimate choice on turn 1; simulator selects target on turn 2; retained flag creates unwanted offer; turns 3/4 end in handoff | Correct `TXN-04` declined explanation | Same terminal-outcome mismatch; required explanation present | AI: NLU/prompt; lead: secondary recognition-clarification preservation |

### Ownership and corrective scope

- **AI lane — primary cause in 4/4:** distinguish neutral what/why-charge inquiries
  from expressed unfamiliarity in NLU/prompt handling. Expected ordinary status
  explanation gold is consistent with ADR-0015; preserve it. Explicit unfamiliarity
  still needs the offer, and explicit denial still needs normal policy review.
- **Lead orchestration — secondary issue in 4/4:** the first uncertainty turn
  correctly creates a recognition-specific clarification, but generic NLG replaces
  its required question with a general request for details. In both ES cases it
  also changes the language to PT. Preserve the code-authored recognition question
  while the offer remains active. This does not itself cure the initial false offer.
- **Lead harness/fixture — no defect established:** the generic chooser picks the
  correct declined target. Default uncertainty is faithful to these ordinary-inquiry
  fixtures, whose intended terminal path never requires an offer reply. Adding a
  recognition/denial response would hide the NLU error. No fixture edits are justified.
- **Policy/scorer — no defect established:** the trusted status rules are correct,
  two uncertain replies correctly reach `ESC-04`, and the final-outcome check
  correctly rejects an unnecessary handoff despite an earlier explanation event.

The one authorized rerun must preserve this first run, use the same lifetime
budget scope/run, and execute all three groups once after the fixes merge. Frozen
confirmation remains a blind check; its failures are not used for diagnosis/tuning.

Lead implementation preserves the recognition question by disabling generic
phrasing only for `clarify` while an offer is active. New authored ES/PT regressions
first reproduced the lost question, then verified the localized question, no
phrasing call and the existing two-uncertainty handoff. No fixture or threshold edit.

The follow-up estimate remains **$0.15–$0.30**, within the approved shared $1 cap
(about $0.85 remained after attempt 1). Exact command after both lanes' fixes merge:

```bash
LLM_REAL_CALLS_APPROVED=1 LLM_FINAL_RUN_STARTED=0 .venv/bin/python -m scripts.dev_gate real --profile after-v2 --attempt 2
```

`--attempt 2` writes to `artifacts/after-v2-dev/gate-real-followup/`, requires a
complete unsuccessful 52-case predecessor, and verifies unchanged dev/confirmation
input hashes. It refuses an existing destination, another profile, or an attempt
beyond 2. It neither creates a new allowance nor resets the existing scope/run.
The first run remains in `gate-real/`. If the second full gate misses, report and
stop without another repeat. No release or v3 execution is authorized here.

## Scope and isolation

This layer implements [ADR-0015](../../adr/0015-post-v2-conversation-and-policy-contract.md).
V2 remains the official result. Fixes were informed by its disclosed post-hoc analysis;
there is no held-out rerun or improvement claim. Lead/AI implementers do not open
suite-v3 scenarios, selections, bindings or its authoring tool. PR #50 stays unmerged
until the dev gate passes and Sebastian separately authorizes it.

## Changes under test

Runtime policy version is **1.3.0**, distinguishing these routing/control semantics
from the official v2 release while retaining the numerical policy thresholds.

- Persist the selected offer handle, recognition count and prior intent. Re-read the
  owned transaction; pass `awaiting_recognition` and masked facts to prompt v5.
  Recognition ends in explanation. Denial reviews policy and proposes; confirmation,
  fresh OTP and committed readback still gate filing. Isolated yes/no is not consent.
- Preserve dispute intent through clarification. Changing the target clears the old
  offer. Cross-customer attempts clear pending decisions across the authenticated
  session; the second attempt creates/verifies a security handoff and revokes it.
- Carry all evidenced review/control reasons with deterministic primary routing.
  Known adjustment/transfer causes survive missing intake data; age and amount
  bands carry their underlying policy reasons. Dependency failures retain causes.
- Strict escalation recall and missed transfers use the same predicate per slice.
  Verified `existing-case` and product reads support the legacy `created-state`
  alias. An intermediate explanation/offer is not a terminal resolution claim;
  pending offers and cancellations never count as successful automation.
- **Baseline changes disclosed:** B1 ignores known merchant names and date tokens
  when extracting an amount, and follows the accepted explain/offer flow. Its two
  original dispute fixtures now include an explicit denial after the offer.
  Authorization/readback regression fixtures start with explicit denial where that
  is their precondition. No frozen suite bytes or gold were changed.
- Deferred #37 API additions expose call route/status/attempt and allowlisted risk
  flags/probabilities, preserving nulls and failed-call costs. Approved story hints
  map `demo.es.mx` to explain/fraud and `demo.pt.br` to ambiguity only when their
  trusted scoped projections support those stories. This grants no role/access.

The separate [v2 slice correction](final-v2-slice-correction.md) reads saved observations
only and leaves official files unchanged. It is a reporting correction, not a rerun.

## Cost and commands

Shared Postgres **scope `dev-gate/after-v2`, run ID `after-v2`, lifetime cap $1.00**.
All lead and AI paid dev runs use these same identifiers and reserve before calling.
Prior scopes are closed without resetting accounting. Prior charged/reserved exposure
is $3.07369789; including this dev cap and the prospective $3 v3 cap gives $7.07369789,
below $12. This step does not authorize release or v3 execution.

Sebastian approved the dev gate estimate of **$0.15–$0.30**, under the shared cap.
Run only on the clean merged candidate.

```bash
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 .venv/bin/python -m scripts.dev_gate mock --profile after-v2
LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.dev_gate real --profile after-v2
```

Outputs: ignored `artifacts/after-v2-dev/gate-structured-mock/` and `gate-real/`.
The command refuses to overwrite an existing run directory. Each case and progress
update is checkpointed; no automatic repeat of the confirmation set is authorized.
The confirmation adapter verifies the pre-fix hash from #47 before execution.
A budget denial stops the run and retains reservations. No credentials enter the
journal; it contains call accounting and schema-validated dev observations.

Acceptance: no-fault ≥18/20, frozen new confirmation ≥17/20, faults12/12 reached and
correct, zero unsafe/forbidden, B1 unchanged or better. Record measured results and
candidate SHA in the progress log, then stop. PT/dialect wording remains
model-generated; fluent-human review remains a limitation.
