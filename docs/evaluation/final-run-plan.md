# Priced final evaluation plan — $12 approved, execution on hold

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

Use `max_output_tokens=2048` for selected Gemini, Grok fallback, and Sonnet frontier system calls, and `max_output_tokens=256` for Sonnet judge calls. The selected and frontier system calls retain the current two-attempt limit (initial call plus one retry); Sonnet judge has the same bound. Jev's typed calls use no retry and its output is free at the published rate. Only after Sebastian's start signal and green gates, the final-run process may set process-local `FINAL_RUN_START_APPROVED=1` and `LLM_REAL_CALLS_APPROVED=1`, inject `TYPESAFE_API_KEY`, use the appropriate `LLM_MODEL_ROUTE`, and set `LLM_RUN_BUDGET_USD` to the remaining amount under the approved cross-process $12 cost gate. Persistent `.env` values stay mock and unapproved. Save the exact resolved configuration with the final artifacts.

The ordinary `evals.heldout` command remains a mock diagnostic; the final program below supplies the real routes. The lead must make its final-run adapter select these real routes, invoke the paired judge on the preselected sample, preserve fresh state per case/repeat, save per-call usage/cost and typed judgments under ignored `artifacts/`, and read back the final action before reporting it. The release must record the implementation SHA, suite manifest/binding hashes, prompt hashes, exact served model IDs, provider tags, policy/matcher versions, price-table date, and every test access. A single cumulative cost gate across **OpenRouter and TypeSafe** and across restarts/processes must stop before the approved ceiling; the current per-client `LLM_RUN_BUDGET_USD` alone is not a cross-process cap. Keep the deployed production setting mock until the lead explicitly enables production keys. Neither key nor model reasoning belongs in Git or reports.

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

For the judged final sample, preselect 50 of the repeated-subset IDs by sorting `SHA-256("judge-v1:" + scenario_id)` within category and taking 18/10/10/12 normal/ambiguous/human-required/security cases. Both judges score the B1 and Gemini reply for each, blind to system identity and objective gold. Both also score the same 50 synthetic calibration items after Sebastian completes the ignored human sheet. Report Jev–Sonnet exact/within-one agreement and quadratic-weighted κ for the 50 calibration pairs and 100 frozen reply pairs separately; report **each judge versus human** per dimension only when all 50 human pairs are complete. `aclara.llm.dual_judge.agreement_report` computes all three paired comparisons. Handoff usefulness is `null` where no summary exists. Do not use calibration or held-out judge scores to retune the final system. Record ES/PT wording limitations and any same-vendor risks explicitly.

## Integrated final program: exact start and resume commands

**Prepared only. Do not execute these commands until Sebastian gives the final-run go.**
Estimated model spend remains **$4.730**, with one hard **$12 cumulative ceiling**.
Production's $3/day and the new $0.10 Azure smoke are separate budgets.

Run from this checkout, with its existing `.venv`, Azure CLI sign-in and private
binding artifacts present. No credentials are placed in shell arguments or logs.
The launcher fetches both keys and TLS database connections from Key Vault in
memory, explicitly using **Seb Azure Sandbox**. It uses the Azure organizer
serving ledger with forced customer RLS and the 120-day bank-clock window.

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
