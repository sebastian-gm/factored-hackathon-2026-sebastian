# Priced final evaluation plan — $12 approved, execution on hold

## V2 release preparation — do not start

Sebastian accepted Step 3 and authorized the Option A re-release. The #37 backend
glass-box additions are deferred until after v2, with a separate video redeploy.
PR #39's language model card is included in the release.

The runtime release at `a52a8f3389a72e321c3b587a8063215a38383564` passed
CI/safety, mock serving and replica recovery, real ES/PT/fraud smoke, browser
verification across three surfaces, Azure controls and external access denial.
API plus browser smoke charged **$0.00778471 / $0.10**, with zero unknown-cost
attempts. The final release identity, any documentation-only retag with identical
image digests, and its fresh gate evidence are recorded in
`artifacts/azure/jev-release.json`. This remains **preparation, not a v2 go**.

### Cumulative ceiling, including the stopped attempt

Postgres aggregate readback found **$0.02058083** charged exposure in the old
`final-evaluation` scope, including **one unsettled reservation**. The earlier
$0.0119 progress figure is not the full reserved exposure. No v1 file or result
was opened to obtain this number. The dev scope charged **$0.10791745**.

`python -m scripts.final_budget --prepare` locks and closes both prior scopes to
new calls, preserving every reservation. It prepares a new scope
**`final-evaluation-v2`**, run **`final-program-v2`**, with a **$11.87** daily and
cumulative run limit. It refuses preparation if prior exposure plus this limit
exceeds $12, and never raises a limit or re-enables a disabled v2 breaker.

**$0.02058083 + $0.10791745 + $11.87 = $11.99849828 ≤ $12.00.**
Unknown costs retain their reservations. Every v2 OpenRouter/TypeSafe attempt,
retry, fallback and judge call reserves before calling through this same durable
run gate. Start/resume verifies the prior scopes remain closed and records both
v2 and combined exposure. The reduced v2 ceiling applies across days, processes
and interruptions. Later dev calls must not reopen these closed scopes.

Preparation writes only `artifacts/final-program-v2/prepared-budget.json`;
it starts no worker, reads no frozen inputs, and makes no model calls. The
separately approved release smoke uses `production/option-a-release-smoke`,
at most five conversations across API/browser checks and **$0.10 total**.
Estimated smoke cost is $0.01–$0.03; production's $3 daily ceiling also applies.

### Exact v2 commands, only after a separate explicit start signal

The launcher now targets **only `artifacts/final-program-v2/`**. Never run or
inspect the abandoned v1 directory. On clean accepted main:

```bash
LLM_FINAL_RUN_STARTED=1 LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.final_program start
```

This launches one detached worker with logs, per-case/per-judge checkpoints,
validated call journals and final outputs in the v2 directory. After an
interruption, preserve all artifacts and use:

```bash
LLM_FINAL_RUN_STARTED=1 LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.final_program resume
```

Aggregate-only status (no model calls):

```bash
.venv/bin/python -m scripts.final_program status
```

The remaining workload, repeat IDs, judge protocol, output metrics and human
sheet described below are unchanged. The old v1 commands and budget identity
in the historical section are superseded. **Preparation is not a start signal.**

## Option A supersedes the v1 commands below

`final-program-v1` is abandoned. Never start, resume, inspect, or delete its
artifacts. Historical commands below are retained for provenance only and must
not be executed. Disclosure: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed.

Sebastian accepted Step 3 and approved the re-release; the completed runtime
gates are listed above. A separate explicit v2 start signal is still required.
No final execution is authorized by this document.

### Simulator change decided on dev evidence

The shared `evals.reactive.Customer` now chooses the scenario's known transaction
when that transaction is actually offered by MATCH. The knowledge comes from
`customer_knowledge.selection_ref` when declared, otherwise the existing
`gold.expected_transaction_ref`. Only that reference identity is used to model
customer recognition; no outcome/action gold reaches NLU, MATCH, or policy.
The same simulator serves B1 and P. It never chooses an absent target, invents a
target, or confirms an action implicitly. Explicit choice replies and refusals
take precedence. An authored no-choice fixture still verifies escalation without
a write. No MATCH thresholds, eligibility rules, frozen suite bytes, or bindings
changed. This repair follows the dev findings in
[dev-p-failure-analysis.md](../ml/dev-p-failure-analysis.md).

The authorized static audit conservatively includes all 200 frozen scenarios:
200 already have explicit choice behavior; 152 reference a transaction overlay
and match the declared expected target. Of the other 48 explicit behaviors,
45 have no expected target and 3 do. These 48 are not statically proven usable
choices; their explicit behavior remains authoritative. Zero frozen scenarios
use the new implicit fallback. No scenario text, outcomes, bindings, or saved
observations were inspected or reported. Static coverage cannot prove which
paths a live model will take. The count-only command is
`python -m scripts.audit_simulator_choices`; accesses are logged, and suite hashes
are asserted unchanged.

### Option A dev gate and budget

The exact shared Postgres identity is scope `dev-gate/option-a`, run `option-a`,
with a $1 cumulative cap. Both lanes reserve before every provider attempt,
including parallel Jev, retries and fallback; unknown usage retains its reserve.
The gate never resets spend or re-enables a breaker. AI diagnosis used
$0.02748308 before lead acceptance. Expected additional gate spend is $0.15–$0.25,
within the existing $1 approval. The real gate runs the corrected original 20
no-fault cases, 12 faults, and the pre-fix frozen 20-case dev confirmation set.
Only authored data is used; the confirmation set is neither edited nor used to
tune. Its SHA-256 is `5a828ca67ffa836b29fcb6799064738c3111f990526c12a497951ee0de223ffe`.

On a clean committed candidate, the authorized command is
`LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.dev_gate real`.
It checkpoints private dev evidence and call costs under
`artifacts/option-a-dev/gate-real/`, refuses an existing output directory, and
records the shared budget before and after. A partial/error result does not pass.
Do not rerun confirmation cases or delete checkpoints to obtain a better score.
`python -m scripts.dev_gate mock` is a separate message-derived structured-NLU
diagnostic and never opens the confirmation set.

**Step 3 completed:** candidate `f6813279620feb1869498fcbcc40cc8c59ad53ae`
passed 20/20 dev, 20/20 confirmation and 12/12 fault cases with all triggers and
zero observed unsafe/forbidden actions. Gate cost $0.08043419; shared dev charged
spend $0.10791745, including diagnosis and reserve rounding. See the
[acceptance report](../ml/dev-p-failure-analysis.md). Do not run the command again
to improve the result. Sebastian subsequently accepted these results and
authorized the re-release; **stop before final v2 and await its separate go**.

The cumulative ceiling is now prepared as described above: the v2 cap is $11.87,
both prior scopes are closed, and their preserved charged exposure includes
unknown-cost reservations. The v2 scope has zero attempts at preparation.

## Historical v1 plan (superseded operational instructions)

**Planning status, 2026-09-27 UTC:** Sebastian pre-approved this final program with a **$12 hard ceiling**, but explicitly said **do not start** until he gives the start signal after the lead's acceptance fixes, matcher v2, and NLU prompt v4 are merged with green gates. No real-model final test has been run. The integrated release adds the real routes, production secret references, resumable runner and shared Postgres gate. The exact accepted SHA is recorded in the private deployment receipt; execution still waits for Sebastian. The existing B1/P-mock diagnostic is prior test access, not a prediction of this final result. Its failed acceptance gates remain open. The frozen 200-case suite, labels, bindings, and preselected repeat IDs must not be changed in response to outcomes. Current readiness is tracked in [final-preflight.md](final-preflight.md).

## Fixed workload and model configuration

The [frozen protocol](eval-protocol.md) has **200 cases and 206 customer messages**. Its committed stratified repeat subset has **100 cases and 102 messages**, selected by `SHA-256("repeat-v1:" + scenario_id)` within category at 35 normal / 20 ambiguous / 20 human-required / 25 security cases. Sebastian confirmed **three total Gemini runs on the subset**: the full-suite pass supplies subset pass 1, followed by two extra 100-case passes. This is 200 B1 case-runs, **400 P/Gemini case-runs** (410 customer messages), and 100 P/Sonnet case-runs (102 messages). The frontier comparison uses exactly the same 100 IDs. No repeat is added to B1 or Sonnet.

| Component | Planned exact route and guard | Workload |
|---|---|---:|
| B1 baseline | `AGENT_SYSTEM=B1`, `LLM_PROVIDER=mock`; rules NLU/matcher and templates | 200 cases, 206 messages |
| P selected system | `AGENT_SYSTEM=P`, `LLM_PROVIDER=openai_compat`, `LLM_MODEL_ROUTE=default`; `google/gemini-3-flash-preview` for NLU and eligible phrasing, NLU prompt `prompts/nlu/v4.md`, phrase prompt `prompts/phrase/v1.md`, strict JSON schema, local Pydantic validation, one retry, ZDR, `data_collection=deny`, `require_parameters=true` | 200 full + 2 × 100 extra cases; 410 messages |
| P risk-cue second opinion | Direct TypeSafe `jev-1.13.0`, six `Noul` risk questions, one call with no retry in parallel with each Gemini NLU call. Boolean union at `>=0.5`; on Jev failure/timeout use Gemini flags and log degradation. No Jev intent, slots or phrasing. Include Jev costs and no-usage reserves in the same durable $12 gate. | Up to 410 Jev calls; not attached to Sonnet frontier |
| Failure-only fallback | `routing.fallback_route=fallback_grok_4_20` in `config/models.yaml`; `x-ai/grok-4.20`, pinned `xai/zdr`. Only Gemini's NLU/phrasing model failure after its bounded attempts invokes Grok; Grok also gets at most one retry. If both fail, use the deterministic path. No fallback is attached to B1, Sonnet frontier, or judge. | Observed, not scheduled |
| P frontier comparison | `AGENT_SYSTEM=P`, `LLM_PROVIDER=openai_compat`, `LLM_MODEL_ROUTE=openrouter_sonnet`; `anthropic/claude-sonnet-5` for NLU and eligible phrasing, same prompts/schema/retry policy, no Grok fallback | Same 100 cases, 102 messages, once |
| Subjective dual judge | `anthropic/claude-sonnet-5` via OpenRouter, `prompts/judge/v1.md`, ZDR `google-vertex/global`, strict four-score schema, no rationale, at most one retry; alongside direct `jev-1.13.0`, one five-level `Score` per applicable rubric dimension and no retry. Both see identical blinded wording inputs; neither sees objective outcomes. Use `aclara.llm.dual_judge.score_pair` and persist both results/usage under the final gate. | 50 synthetic human-validation items + 50 frozen cases × 2 replies (B1 and Gemini) = 150 paired assessments |

The prepared configuration pins `provider.only=["google-vertex/global"]` for the Gemini default and Sonnet frontier routes, with `allow_fallbacks=false` supplied by the adapter, while retaining their exact model IDs. The standard Gemini ZDR route is priced above the earlier flex route; the estimate below uses the **standard rate**. Grok is already pinned to `xai/zdr`. The judge's Google Vertex Sonnet route passed a three-item synthetic smoke; the advertised Amazon Bedrock global route returned HTTP 404 in the smoke and is not the planned route. The judge is still an Anthropic model, distinct from the Gemini system model. To avoid Sonnet self-preference, do not apply it to Sonnet-system replies; compare the frontier Sonnet system on objective metrics and human-reviewed wording separately.

The direct TypeSafe route has a published no-training claim but standard-account zero retention is **not verified**; see [data provenance](../data-provenance.md). Recheck the account terms and approved payload scope before lead activation. The NLU execution record stores Gemini's raw boolean risk flags, Jev's raw `Noul` probabilities and threshold flags, their union, cost and any degradation; Gemini prompt v4 does not return per-cue probabilities, so those fields remain `null` rather than fabricated.

Use `max_output_tokens=2048` for selected Gemini, Grok fallback, and Sonnet frontier system calls, and `max_output_tokens=256` for Sonnet judge calls. The selected and frontier system calls retain the current two-attempt limit (initial call plus one retry); Sonnet judge has the same bound. Jev's typed calls use no retry and its output is free at the published rate. Only after Sebastian's start signal and green gates, the final-run process may set process-local `LLM_FINAL_RUN_STARTED=1` and `LLM_REAL_CALLS_APPROVED=1`, inject `TYPESAFE_API_KEY`, and pin `EVAL_BUDGET_DSN` to the same final-program Postgres budget for every system and judge process. Persistent `.env` values stay mock and unapproved. Save the exact resolved configuration with the final artifacts.

The integrated `scripts.final_program` below is the single final entry point. It reuses the held-out binding/execution code and selects the real routes, fresh state per case/repeat and the cumulative Postgres gate, together with the Jev risk-cue union and the paired Sonnet/Jev judge (`aclara.llm.dual_judge.score_pair`) on the preselected sample. The ordinary `evals.heldout --run` remains a mock diagnostic. Save per-call usage/cost and typed judgments under ignored `artifacts/`, and read back the final action before reporting it. The release must record the implementation SHA, suite manifest/binding hashes, prompt hashes, exact served model IDs, provider tags, policy/matcher versions, price-table date, and every test access. One cumulative gate across **OpenRouter and TypeSafe** and across restarts/processes must stop before the approved ceiling; the per-client `LLM_RUN_BUDGET_USD` alone is not a cross-process cap. Neither key nor model reasoning belongs in Git or reports.

## Model-call cost estimate

Prices are USD per million input/output tokens, checked against the [OpenRouter model catalog](https://openrouter.ai/docs/api/api-reference/models/get-models) and [ZDR endpoint list](https://openrouter.ai/docs/api/api-reference/endpoints/list-endpoints-zdr) on 2026-09-27: Gemini standard `google-vertex/global` **$0.50/$3.00** (flex was $0.25/$1.50), Sonnet `google-vertex/global` **$2.00/$10.00**, and Grok `xai/zdr` **$1.25/$2.50**. Recheck the pinned endpoints, availability, and rates during the start preflight. Do not estimate from the shared key-level balance change.

The 150-case dev NLU measurements with v3 averaged **1,699 input / 138 output tokens** for Gemini and **2,689 / 319** for Sonnet. The new 40-case synthetic denial check averaged **1,986 input / 137 output** for Gemini with v4. To cover longer final conversations and schema/provider variation, this revised plan uses **2,500/250** for Gemini NLU and **3,200/500** for Sonnet NLU. Phrasing has no comparable paid end-to-end measurement, so its estimates are deliberately higher and its count is an upper bound of one model draft per customer message; many response types use templates. The three-item Sonnet judge smoke averaged **1,140 input / 40 output tokens**, while the plan uses **2,500/120**. Jev's 150-case NLU comparison averaged about **933 input tokens** per call; its three judge-smoke calls averaged about **984**. The plan uses **1,500** per risk call and **2,000** per judge call to cover longer final records. These are planning assumptions, not measured final usage. The counts below exclude retries except for the contingency.

| Component | Planned calls | Input / output tokens per call | Rate input / output per 1M | Estimated USD |
|---|---:|---:|---:|---:|
| B1, 200 cases | 0 | — | — | **$0.000** |
| P/Gemini NLU, 400 case-runs | 410 | 2,500 / 250 | $0.50 / $3.00 | **$0.820** |
| Jev risk-cue second opinion, Gemini NLU only | 410 | 1,500 / free output | $0.042 / $0 | **$0.026** |
| P/Gemini phrasing, upper-bound | up to 410 | 2,000 / 300 | $0.50 / $3.00 | **$0.779** |
| P/Sonnet NLU, 100 case-runs | 102 | 3,200 / 500 | $2.00 / $10.00 | **$1.163** |
| P/Sonnet phrasing, upper-bound | up to 102 | 2,500 / 350 | $2.00 / $10.00 | **$0.867** |
| Sonnet judge, 50 calibration + 100 B1/Gemini replies | 150 | 2,500 / 120 | $2.00 / $10.00 | **$0.930** |
| Jev second judge, same 150 paired items | 150 | 2,000 / free output | $0.042 / $0 | **$0.013** |
| Grok fallback sensitivity at 5% of 820 possible Gemini calls | 41 | 2,000 / 300 | $1.25 / $2.50 | **$0.133** |
| **Illustrative total with maximum phrasing and 5% fallback** | | | | **$4.730** |

The total uses unrounded Jev estimates ($0.02583 risk and $0.01260 judge) before display rounding.

Without Grok fallbacks, the same upper-bound phrasing scenario is **$4.597**. At a 1% fallback-attempt rate, about eight Grok calls add **$0.026**; 5% adds **$0.133**, before any cost of failed primary attempts. Sebastian approved a **$12 final-program ceiling** to absorb retries (each OpenRouter route allows one), output-token variance, no-usage attempts with reserved exposure, and provider price drift. That ceiling is **not a start signal or a prediction of the bill**. Stop before it is reached, including conservative reserves for calls without usage/cost from either provider. The prior development comparisons, separately approved $0.008042 Sonnet judge smoke, $0.106686 v4 dev check, and $0.217601 Jev/Gemini comparison are outside this future estimate. Monthly cloud infrastructure remains separate.

Report the optional **fallback-attempt rate** as logical Gemini NLU/phrasing requests that invoked Grok divided by all logical Gemini NLU/phrasing requests, with NLU and phrasing shown separately. Also report fallback success/failure, case-run rate, additional latency, billed per-call cost, and the primary failure category. Count primary retries and fallback attempts in all-attempt JSON validity and cost. Fallback prose never supplies identity, authorization, policy, write authority, or objective gold.

## Wall-clock and validation plan

At the existing serial case-runner setting, budget **60–90 minutes** of machine wall-clock time plus up to 30 minutes for preflight/readback; stop and investigate if it exceeds two hours or the approved cost ceiling. A planning breakdown is B1 1–5 minutes; Gemini 25–45 minutes for 410 NLU and up to 410 phrasing calls with Jev risk calls in parallel; Sonnet frontier 9–18 minutes for 102 NLU and up to 102 phrasing calls; paired judging 5–13 minutes for 150 short assessments; the remainder covers API/database work, verification, bounded retries, and checkpointing. The paired dev replay gives a **1.897-second median max-of-two latency proxy**, equal to Gemini alone, but no live parallel latency was measured. The three-item Jev judge smoke median was 0.132 seconds; phrasing and final end-to-end latency remain unmeasured. These ranges are scheduling estimates. Human review of 50 calibration samples is additional time, approximately 30–60 minutes.

Before the paid final run, verify the frozen manifest and private bindings, merged lead acceptance fixes and matcher v2, merged prompt v4 and green gates, pinned provider routes, output directories, cross-process budget breaker, unchanged scope under the $12 approval, and Sebastian's explicit start signal. Run B1 and P on the same frozen cases without editing labels or prompts between systems or repeats. Use the existing 100 repeat IDs and record flips and per-scenario majority outcome as the protocol requires. Deterministic code computes SAR, unsafe outcomes, action/readback correctness, routing, cost, latency and intervals. The LLM judge receives only the requested locale, customer message, delivered reply, and optional handoff summary. It produces the four subjective scores in [judge-rubric.md](judge-rubric.md); objective outcomes are never delegated to it.

For the judged final sample, preselect 50 of the repeated-subset IDs by sorting `SHA-256("judge-v1:" + scenario_id)` within category and taking 18/10/10/12 normal/ambiguous/human-required/security cases. Both judges score the B1 and Gemini reply for each, blind to system identity and objective gold. Both also score the same 50 synthetic calibration items; judge-versus-human claims wait for Sebastian to complete the ignored human sheet. Report Jev–Sonnet exact/within-one agreement and quadratic-weighted κ for the 50 calibration pairs and 100 frozen reply pairs separately; report **each judge versus human** per dimension only when all 50 human pairs are complete. `aclara.llm.dual_judge.calibration_agreement` reads the ignored paired 50-row sheets and refuses incomplete human claims; `agreement_report` computes the 100-reply judge-to-judge comparison. Handoff usefulness is `null` where no summary exists. Do not use calibration or held-out judge scores to retune the final system. Record ES/PT wording limitations and any same-vendor risks explicitly.

## Integrated final program: exact start and resume commands

**Prepared only. Do not execute these commands until Sebastian gives the final-run go.**
Estimated model spend remains **$4.730**, with one hard **$12 cumulative ceiling**.
Production's $3/day and the new $0.10 Azure smoke are separate budgets.

Run from this checkout, with its existing `.venv`, Azure CLI sign-in and private
binding artifacts present. No credentials are placed in shell arguments or logs.
The launcher fetches both keys and TLS database connections from Key Vault in
memory, explicitly using **Seb Azure Sandbox**. It uses the Azure organizer
serving ledger with forced customer RLS and the 120-day bank-clock window.

### Legacy separate calibration command — avoid duplicate paid scoring

The single start command already scores the 50 synthetic calibration items alongside the 100 frozen reply assessments. Do not also execute the standalone calibration harness: that would duplicate paid scoring. The standalone harness remains available for a separately authorized recovery/calibration workflow after human ratings are complete. It requires process-local `LLM_FINAL_RUN_STARTED=1`, `LLM_REAL_CALLS_APPROVED=1` and `LLM_JUDGE_FULL_RUN_APPROVED=1`, and pin `EVAL_BUDGET_DSN` to the same shared non-owner Postgres budget (migration 0003 applied; policy initialized once with `python -m scripts.final_budget` and an owner connection in `FINAL_BUDGET_OWNER_DSN`, which never deletes spend, raises a cap or re-enables a tripped breaker). DSNs and provider keys stay environment-only, and the production smoke's $0.10 scope is never used for evaluation.

**Start, after the explicit go:**

```bash
cd /home/megagdev/megagdev/factored-hackathon-2026/bank-agent-lab
LLM_FINAL_RUN_STARTED=1 LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.final_program start
```

This single command launches a detached background process and returns its PID.
It survives a terminal or Codex interruption while the workstation stays running.
A reboot requires the resume command; it cannot keep a process alive while the
workstation is off. Keep this checkout and its Python environment unchanged.

**Resume the same program after interruption:**

```bash
cd /home/megagdev/megagdev/factored-hackathon-2026/bank-agent-lab
LLM_FINAL_RUN_STARTED=1 LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.final_program resume
```

**Read aggregate progress without making model calls:**

```bash
cd /home/megagdev/megagdev/factored-hackathon-2026/bank-agent-lab
.venv/bin/python -m scripts.final_program status
```

The start/resume command requires clean `main == origin/main` and the accepted
SHA in `artifacts/azure/jev-release.json`, including deployment, smoke and CI
readbacks. It refuses a changed release. `launch.json` and `release.json` pin the
SHA, dataset, suite/binding/split checksums and fixed budget identity. Each frozen
access, including resume verification, is recorded in the existing access ledger.
There is no prompt, label, threshold or selection tuning between passes.

### Checkpoints, recovery and spending

- One file lock prevents concurrent workers. Completed cases and judge pairs are
  atomically committed with file and directory fsync, and never called again on
  resume. Per-call journals fsync validated outputs and raw typed judgments;
  provider envelopes and reasoning are excluded.
- A process killed inside a case or judge pair leaves its attempt journal and
  reservations intact. Resume restarts only that unfinished unit with fresh
  isolated operational state. Up to three interrupted attempts per unit are
  allowed; further interruption stops for investigation. All recovery charges
  consume the original ceiling and are disclosed. No paid case is silently
  discarded or overwritten; completed-case latency is reported separately from
  interrupted-attempt exposure.
- Both OpenRouter and TypeSafe reserve **before every network attempt** in the
  same Postgres `final-evaluation/final-program-v1` budget. Retry, fallback,
  parallel risk calls and both judges share it. Jev reserves $0.01 per call and
  settles actual token cost; timeout or missing usage retains the reserve.
  The published 64k maximum at $0.042/M input is below this reserve. A call that
  exceeds its reservation disables the breaker. SDK retries are disabled for Jev.
- Resume preserves the budget policy and all reservations. It refuses regressed
  spend history; it never resets spend, raises the cap or re-enables a breaker.
  Budget denial stops the program and writes a clearly partial aggregate report.
- `STOPPED.json` records the exception class without row data or credentials;
  `progress.json` records phase/count/spend. Inspect a run taking over two hours
  before continuing. Completion means the program finished, not that safety or
  quality gates passed; those gates are in `results.json`.

### Outputs (generated only when the authorized program runs)

Everything is private and ignored under **`artifacts/final-program-v1/`**:

| Artifact | Contents |
| --- | --- |
| `results.json` | Aggregate source of truth: every §15.4 outcome/efficiency metric, Wilson and case-bootstrap intervals, language/dialect/country/segment slices with n and small-cell flags, all eight unsafe categories and upper bounds, separate infrastructure estimate |
| `results.md` | Mandatory workload/sample/model/prompt/price-date header and the same aggregate metrics, including limitations |
| `checkpoints/` | One immutable completion per case/repeat or paired judge item, preserved attempt markers and call journals |
| `judge-inputs.json` | Private blinded wording inputs for 50 calibration and 100 frozen reply assessments; no objective gold is sent to a judge |
| `human-judge-20.csv` | Twenty deterministic locale-stratified frozen wording items for Sebastian, blank four-dimension ratings, no system label or model score; never overwritten on resume |
| `progress.json`, `STOPPED.json`, `COMPLETE.json`, `worker.log` | Aggregate progress and stop/completion receipts |

The paired comparison reports B1/P differences with case bootstrap, exact McNemar
on repeated-subset majority success, outcome/SAR/success flip rates and repeat
ranges. Sonnet/Jev agreement reports exact/within-one Wilson intervals and
quadratic-weighted kappa with bootstrap intervals, separately for calibration and
frozen replies. Missing scores are counted explicitly. Human agreement remains
**pending** until human ratings exist: the requested 20-item owner sheet does not
substitute for the protocol's 50-item calibration. PT and dialect wording remain
model-generated with no fluent-human PT review.

The frozen suite has outcome/action gold, not independent per-slot NLU or matcher
ranking gold. Those component metrics remain in the separate dev and matcher
reports; the final report labels this limitation instead of deriving labels from
system behavior. No final artifacts or frozen results were generated during
implementation tests; tests use independent authored fixtures.

TypeSafe activation uses the approved masked synthetic payload boundary. The
[model documentation](https://docs.typesafe.ai/models) was checked on 2026-09-27:
Jev 1.13.0 costs $0.042/M input, output free. Its [legal documentation](https://docs.typesafe.ai/legal)
offers ZDR for enterprise accounts; this standard account's ZDR is unverified.
The new key is a server-only Key Vault reference through managed identity.

### Judge wiring (implemented in `evals/final_program.py`)

The 100 blinded frozen reply assessments use `aclara.llm.final_run.client_for` with `route="openrouter_sonnet", judge=True` and `score_pair` plus `jev_judge_adapter`, which keeps the 256-token Sonnet route while reserving and settling Jev against the identical cumulative gate. The 50 frozen judge IDs are predeclared by `SHA-256("judge-v1:" + scenario_id)` within category. Jev–Sonnet agreement and each judge's agreement with the completed human calibration sheet are reported by `aclara.llm.dual_judge`; adapter tests do not imply that any lead-run judge or human review has completed.
