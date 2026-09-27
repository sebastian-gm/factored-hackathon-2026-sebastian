# Progress log

## AI lane — after-v2 explain/offer dev confirmation, 2026-09-27 UTC

### Completed (verified)

- Read handoff 13 and authored the 20-case synthetic [explain/offer confirmation set](../../src/aclara/llm/dev_explain_offer_20.yaml) before any v5 prompt, NLG, or scenario implementation change. Its separate first commit `0692881` freezes the file and [SHA-256 manifest](../../src/aclara/llm/dev_explain_offer_20.sha256). Structural validation passed: 20 unique cases, 10 ES/10 pt-BR, 10 denial/10 recognition follow-ups, and no verbatim opening overlap with dev-v2.

### Done but not verified

- The new set is semantic-only until the lead's Step 1 ADR defines state and outcome names; no API or real-model run has used it. Its slang and labels are AI-authored, not fluent-human reviewed.

### Next / blocked

- Merge the lead's Step 1 ADR before finalizing NLU v5 and the scenario adapter. The lead must initialize `dev-gate/after-v2` before any shared $1 dev paid call. Do not open suite-v3 rows; lead merges AI PRs after CI.

---

## 2026-09-27 — Handoff 13 Step 1: accepted behavior specification

### Completed (verified)

- Routine merges finished: #46 analysis at `7914022`, then #45 reviewed wording
  at **`4470ba4957c7f90f54ac28e887bc3119ed99a02e`**. Each exact PR head passed
  all four CI checks before merge. Only A20/W02 wording was applied; local
  `make checks` passed (174 tests / 13 skips, B1 32/32).
- Read handoff 13 fully. Wrote [ADR-0015](../adr/0015-post-v2-conversation-and-policy-contract.md)
  and the [normative v3 behavior contract](../../contracts/interfaces/conversation-policy-v3.md)
  before behavioral code changes: nonterminal explanation/dispute offer,
  recognition/denial transitions, SAR, multi-reason handoffs, cross-customer
  actions, business-date age, and type/data rule precedence.
- Independently calculated the worked boundary: bank date 2026-06-17 minus
  84/85 days gives 2026-03-25/2026-03-24. Document links, whitespace and staged
  safety checks are checked before committing this specification.
- Orchestrator identified confirmation freeze PR #47, `0692881`, with log
  commit `857228e`, authored before fixes. Its rows have not been opened here.

### Done but not verified

- This is an accepted specification, not a claim that Step 3 is implemented.
  Runtime schemas will be regenerated with the additive interface changes.
- Prompt v5/NLG/dev integration is still being prepared by the AI lane on
  `feat/ai-explain-offer-v5`; it waits for this contract's merged SHA.

### Next / blocked

- Merge this specification with green CI and report its exact SHA immediately
  so the independent lane can author v3. Merge #47 after its remaining CI passes.
- Implement lead Step 3 on dev only, using `dev-gate/after-v2` for any approved
  real calls (new $1 cap). Never rerun v2 held-out cases or open suite-v3 rows.
  Keep official v2 outputs unchanged; saved-slice reporting corrections must be
  separate, disclosed artifacts. No release/v3 run before Sebastian's later go.

## 2026-09-27 — Routine post-v2 merges and accepted pt-BR wording

### Completed (verified)

- Opened and merged analysis PR **#46** after all four checks passed: Python,
  Postgres, web/browser and safety. Merge SHA: `791402214a2d8d5829c6c6e9e1208e80a2679945`.
- Reviewed #45's documentation and proposed patch against the actual workflow.
  Accepted A20 (destination is a person on the team) and W02 (verification code,
  then confirmation); retained A15 because the handoff already exists and is
  durably read back before the reply. Applied exactly two pt-BR string changes.
- Exact source replacement and normalized AST comparison confirmed no logic
  change. `git apply --check` passed before application. With
  `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 LLM_FINAL_RUN_STARTED=0`,
  `make checks` passed: six hooks, strict mypy, file policy, compilation,
  **174 tests passed / 13 database-dependent skips**, B1 **32/32**, interfaces
  and policy catalog. No paid calls, deployment, held-out access or reruns.
- Updated #45 from main with a history-preserving merge, retaining both
  progress-log entries. Fresh PR CI is required before merge.

### Done but not verified

- Fluent-human pt-BR review is still pending. The two strings have not been
  redeployed to Azure; final v2 remains tied to its original evaluated SHA.

### Next / blocked

- Complete #45's green-CI merge and check main. Sebastian then authorized
  handoff 13: merge the explain/offer/dispute and handoff/security/age/policy
  specification first, report its SHA, then implement lead-owned fixes on dev
  only. Never rerun v2 held-out cases or open suite-v3 rows. No release or v3 run
  is authorized by this step.

## AI lane — lead-owned pt-BR wording review, 2026-09-27 UTC

### Completed (verified)

- Reconciled the previously stated 34-string inventory to **35 active strings**, all found in current lead-owned API, workflow, handoff and staff source; Sebastian explicitly approved reviewing all 35 under the unchanged new $0.30 cap.
- Created and read back separate durable scope `pt-review/lead-strings` / run `lead-strings`, cap $0.30. Nine sequential Sonnet calls reviewed 35/35 in batches of at most four with 3072 maximum output tokens. All nine responses were valid and complete; scope readback was **$0.048878 known and charged, zero unknown-cost attempts**. No final-v2 budget scope was used.
- Rejected one model suggestion after checking the handoff packet's real creation/readback order. Proposed two wording changes only in [the lead-review patch](../ml/pt-review-lead-proposed.patch); `git apply --check` passed and lead-owned source files remain unchanged. [Before/after decisions](../ml/pt-review.md) are recorded.

### Done but not verified

- Model review is not a fluent-human pt-BR review. The proposed wording has not been applied or verified in an app build.

### Next / blocked

- Lead reviews the proposed patch after final v2 finishes, applies any accepted wording in the lead lane, and merges this documentation PR. Keep this PR unmerged during the freeze.

---
## 2026-09-27 — Final v2 COMPLETE; post-hoc analysis; STOP

### Completed (verified)

- Authorized v2 finished on release **`fd34c7dce11cf9db6f71e84ae4fbb2ccc19de415`**:
  700 system case-runs and 150 judge items, about 2h20m, no restart/resume.
  `final_program status`, the completion receipt and host process inspection
  confirmed COMPLETE and no remaining worker. The watchdog extension preserved
  the original start time and used 15-minute stale-progress / 3h30m limits.
- Main equaled origin/main and was clean after completion. Evaluation/runtime
  code, frozen suite and official results remained unchanged during the run.
  No abandoned-v1 artifact was opened or modified.
- Durable budget aggregate readback: v2 **$2.94519961**, 1,801 reservations,
  zero unknown costs; known cumulative **$3.06646189**, charged/reserved exposure
  **$3.07369789**, below $12. Older scope exposure was read only from aggregate
  Postgres budget accounting. The v2 scope limit remains $11.87.
- Official SAR: B1 **41/193**, Gemini **39/193**, Sonnet **26/98** on its fixed
  subset. Pass: **65/200, 63/200, 37/100**. **None passed all safety gates**;
  the report does not claim acceptance or improvement. Judge pairs: 143/150;
  seven ModelFailure items were not rerun. The human sheet has 20 blank items at
  `artifacts/final-program-v2/human-judge-20.csv`.
- Wrote [final v2 error analysis](../evaluation/final-v2-error-analysis.md),
  including all seven requested questions, headline metrics and cost. Ran the
  ignored offline `posthoc-analysis.py`, `posthoc-causes.py`, `posthoc-checks.py`
  and `posthoc-final-counts.py` under `artifacts/final-program-v2/`.
  Reads are logged through `evals.access`; SHA-256 checks confirmed **863 inputs
  unchanged**, including all result checkpoints, frozen metadata and official
  result/completion files. No model calls, reruns, rescoring or code fixes.
- `git diff --check` and staged `pre-commit run` passed: strict mypy, data-file,
  secret and large-file policies. Ruff hooks correctly skipped the Markdown-only
  change. No application tests or paid calls were rerun for documentation.
- Findings: category rates; fixture 85/84-day mismatch behind the forbidden
  filing; gold-target versus actual-action readback distinction; 15 absent and
  24 reason-mismatched Gemini transfers; 47 terminal-dispute gold conflicts
  with the inquiry label rule; confirmed presence/strict slice metric bug;
  dev/final contract and B1 numeric-merchant matching gaps. One intentional B1
  readback fault handed off without reporting successful filing.

### Done but not verified

- Human judge ratings and fluent-human Portuguese review remain pending.
  Post-hoc causes have not been tested by reruns, and no adjusted/improved
  held-out score is claimed. No live per-action database reconciliation was
  performed during this documentation-only analysis.
- #37's additional backend API work and the separate video redeploy remain
  deferred. The unchanged Azure deployment is not being re-released here.

### Next / blocked

- **STOP after reporting.** Sebastian reviews the human sheet and decides the
  next development task. V2 remains the official failed-gate result. Future
  fixes need fresh evaluation evidence; never reuse this analysis to claim a
  held-out improvement, and never access the abandoned v1 directory.
- No new cost or deployment approval is requested for this completed analysis.
  Later: **Continue from docs/status/progress-log.md. Next layer: [X]. Same rules.**

## 2026-09-27 — Option A re-release verified; STOP before final v2

### Completed (verified)

- Merged #39 first, followed by the cumulative-budget preparation (#42) and
  exact smoke-run Terraform allowlist fix (#43). Runtime smoke SHA:
  **`a52a8f3389a72e321c3b587a8063215a38383564`**. CI `36343084749`, safety
  `36343084792`, and external-access workflow `36343714530` all passed.
- Built and pushed both private images, set the ignored `image_tag`, reviewed
  both Terraform plans, and ran `python -m scripts.azure_dev apply` for mock
  and real stages. Ingress/capacity, database and storage stayed unchanged.
  `python -m scripts.azure_verify` passed in both stages: owner IPv4 HTTPS,
  internal API, app login, TLS database, approved Azure-services firewall
  exception, managed identity/Key Vault and $30/$50 budget alerts.
- `python -m scripts.azure_smoke` passed in mock mode: four personas, 15 scoped
  transaction projections, two cases, four handoffs, two claims/resolutions,
  and case recovery in the same session after an API replica replacement.
  All three surfaces used organizer serving; no model calls in this stage.
- `python -m scripts.azure_llm_smoke` passed all three real paths (ES dispute,
  PT ambiguity, fraud). `python -m scripts.serving_browser --target azure`
  passed customer chat, Agent Desk and Ops, with one handoff resolved.
  Combined durable smoke readback: **$0.00778471 / $0.10**, 11 attempts,
  four conversations, zero unknown-cost attempts. API cases had no fallback.
- Private evidence is under `artifacts/azure/`: `option-a-serving-smoke.json`,
  `option-a-release-smoke.json`, `option-a-browser.json`, image/plan receipts,
  and `jev-release.json`. The release receipt binds the final main SHA to the
  smoked digests and records any documentation-only retag, its fresh controls,
  no-model-call BFF readback, CI/safety and external-denial workflow.
- V2 budget prepared and read back with **zero attempts / $0**: scope
  `final-evaluation-v2`, run `final-program-v2`, cap **$11.87**. Prior scopes are
  closed without resetting history. V1 reserved exposure **$0.02058083** plus
  dev **$0.10791745** plus the v2 limit = **$11.99849828**, below $12.
  The unsettled v1 reserve is retained. No abandoned-v1 artifact was accessed.
  Preparation receipt: `artifacts/final-program-v2/prepared-budget.json`.
- Local Python tests, 15 Postgres integration tests, Ruff, strict mypy,
  Terraform formatting/validation and private-image import checks passed
  during release preparation. Live East US 2 estimate remains **$34.63/month**.

### Done but not verified

- No final-v2 evaluation, results, judge agreement or human ratings yet.
  V2 is prepared only; no launcher or worker was started.
- #37's optional backend API additions remain deferred until after v2 and a
  separate video deployment. The Azure-services database firewall exception
  remains the documented dev limitation; private access is future work.

### Next / blocked

- **STOP. Await Sebastian's separate final-v2 go after the release gates.**
  Start/resume commands and cumulative-cap enforcement are documented in
  [final-run-plan.md](../evaluation/final-run-plan.md). Never resume v1.
- Continue from docs/status/progress-log.md. Next layer: explicitly approved
  final-program-v2 execution. Same rules.
- Disclosure: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed.

## 2026-09-27 — Approved Option A re-release preparation

### Completed (verified)

- Merged #39 at its all-green head; merge `5608e6b73a68c69b562f9a9c897b3109e3f0b868`.
  Corrected its stale deployment/confirmation status in this follow-up.
- `python -m scripts.azure_prices`: live East US 2 estimate **$34.63/month**,
  below the approved $40 stop gate (no new resource class or public access).
- Aggregate Postgres budget readback: v1 exposure **$0.02058083**, including one
  unsettled reserve; dev **$0.10791745**. The earlier v1 $0.0119 figure omitted
  part of reserved exposure. No abandoned-v1 artifact was opened.
- `python -m scripts.test_postgres`: **15 passed**, including v2 preparation,
  cumulative cap, preserving unsettled reserves, closing prior budgets and
  refusing to re-enable a tripped breaker. Focused final-run tests passed;
  Ruff and strict mypy passed.
- Prepared the launcher/budget support for `artifacts/final-program-v2/`, scope
  `final-evaluation-v2`, run `final-program-v2`, **$11.87** cap. Combined maximum
  at current reserved exposure: **$11.99849828**. Runtime start/resume verifies
  the closed prior scopes and reduced cap; it cannot initialize/reset budgets.
- Fresh release smoke identity is `production/option-a-release-smoke`, **$0.10**
  across API and browser, maximum five attempted conversations. Old smoke
  accounting remains intact. Estimated new smoke usage: **$0.01–$0.03**.

### Done but not verified

- New image build/push, Terraform plan/apply, deployed smoke, browser, external
  access and release receipt remain pending the prepared main release SHA.

### Next / blocked

- Run the approved Step 4 release gates, update this log with evidence, report
  the exact SHA and **STOP**. Do not start v2 without Sebastian's separate go.
- Skip #37's backend API additions until after v2 and a separate video redeploy.

## 2026-09-27 — Option A Step 3 complete; STOP before re-release

### Completed (verified)

- Merged #40 after all four checks passed (CI `36340363242`, safety
  `36340363197`). Tested candidate: **`f6813279620feb1869498fcbcc40cc8c59ad53ae`**.
- Ran `LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.dev_gate real`
  once on the clean committed candidate; exit 0, all **52/52** checkpoints saved.
  **No-fault 20/20 (ES 10/10, PT 10/10); confirmation 20/20 (10/10 each);
  faults 12/12 (6/6 each), all triggers fired; zero observed unsafe outcomes in
  every category and zero forbidden actions.** No remaining failed gate cases.
- The route made 50 Gemini NLU + 17 Gemini phrasing + 50 Jev risk calls, all
  valid, with zero degraded NLU events or unknown-cost attempts. Known gate cost
  **$0.08043419**. Postgres readback: **$0.10791745 / $1.00**, 157 reservations,
  scope **`dev-gate/option-a`**, run **`option-a`**, enabled. This includes the
  AI lane's earlier diagnosis and conservative reservation rounding.
- Original B1 **32/32**, reactive B1 **32/32**, structured mock P **32/32**;
  local pytest, Ruff, strict mypy, interface/catalog checks, schema validation,
  and changed-file pre-commit checks passed. Details and commands are in the
  preceding preparation entry.
- [Acceptance report](../ml/dev-p-failure-analysis.md) and
  [aggregate JSON](../ml/dev-p-gate-results.json) record the tested SHA. Private
  evidence: `artifacts/option-a-dev/gate-real/`. No code, fixtures, prompts,
  thresholds or confirmation bytes changed after the real gate began.
- Frozen choice audit remains counts only: 200 explicit behaviors; 152 usable
  target-matching overlay references; 48 not statically proven (45 without a
  target, 3 with one); zero new fallback users. No outcome/text report or binding
  access. Abandoned v1 artifacts stayed untouched.

### Done but not verified

- No Azure verification of this new candidate: deployment, Azure smoke and
  browser checks are deliberately pending the next approval.
- No final v2 evidence, new judge agreement, or human ratings. Dev acceptance
  is one authored-fixture pass, not an organizer-ledger final evaluation.
- Optional glass-box API additions remain deferred.

### Next / blocked

- **STOP. Await Sebastian's re-release approval.** The later release must pass
  the Azure gates and return its exact SHA for a separate final-v2 start signal.
- V2 must enforce $12 minus preserved v1 spend and all Option A dev charges;
  no v2 budget/output run has been initialized in this step.
- Continue from docs/status/progress-log.md. Next layer: approved re-release and
  Azure verification, then stop before final v2. Same rules.
- Disclosure: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed.

## 2026-09-27 — Option A lead integration and dev gate preparation

### Completed (verified)

- Merged #36, #28, #24, #37 in order after all four checks passed on each
  updated head. Conflicting branches used history-preserving merge updates as
  requested. #37 merge: `b3e8f1501ab932970626478457d751e958a26cca`.
- Reviewed and merged #38, including the AI root-cause report and generic
  transaction-type normalization. Fresh CI: `36339767762`, safety:
  `36339767753`; merge `55cea748f539fa8589b008f75edccf1e748f6ae6`.
- Shared durable dev budget is **scope `dev-gate/option-a`, run `option-a`**,
  cumulative cap **$1.00**. Initial readback was zero; AI reports 40 attempts and
  $0.02748308 charged before lead acceptance. Every lane must share both names.
- Generic simulated customer selects its known target only when offered;
  explicit replies/refusals win. Corrected authored dispute/fault requests to
  explicit denial/filing, leaving gold outcomes, MATCH thresholds and policy
  unchanged. Faults without a gold transaction declare customer knowledge.
- `.venv/bin/python -m scripts.dev_gate mock`: structured P diagnostic **20/20**
  no-fault, **12/12** faults with all triggers reached; zero unsafe/forbidden
  actions. `.venv/bin/python -m evals.runner --system B1`: original **32/32**, safety
  guards passed. Direct `evals.reactive.execute(..., "B1")` on corrected v2:
  **32/32**, all 12 faults reached, zero unsafe. Receipts in ignored
  `artifacts/option-a-dev/`.
- `.venv/bin/pytest -q`: suite passed (Postgres-only tests skipped locally;
  their CI job passed on #38). `.venv/bin/ruff check .` and strict mypy passed.
- Confirmation metadata verified without reading conversation text: 20 cases,
  10 ES / 10 PT, no faults; bytes unchanged from pre-fix commit `88288a9`.
- Authorized static frozen choice audit, `.venv/bin/python -m
  scripts.audit_simulator_choices`: 200 explicit behaviors, 152 target-matching
  overlay references; 48 unproven explicit behaviors (45 without a target,
  3 with a target). Zero frozen cases use the new fallback. Counts only;
  suite hashes unchanged, no bindings/results accessed. These are structural
  counts, not executed path coverage. The abandoned v1 directory stayed untouched.

### Done but not verified

- Real Step 3 acceptance runner is prepared with per-case checkpoints,
  metadata-only/validated call journals, and the shared reserve-before-call
  Postgres cap. Paid acceptance and confirmation results are not yet available.
- Optional #37 backend glass-box additions are deferred to keep this layer
  focused on acceptance; no new deployed behavior is claimed.

### Next / blocked

- Run the committed candidate's real 20 dev + 12 fault + 20 confirmation cases
  under the approved shared $1 cap; report numbers and remaining failures.
- **Stop before re-release.** No cloud deployment or final v2 start is authorized.
  No changes based on confirmation results. The 3 target-bearing frozen explicit
  behaviors remain a disclosed static limitation; do not tune or edit suite bytes.
- Disclosure: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed.

## AI lane — Option A dev-P gate, 2026-09-27 UTC

### Completed (verified)

- Read handoff 12 and froze a fresh 20-case synthetic confirmation set (10 ES, 10 pt-BR) in the first commit of this branch **before** changing NLU. Schema and unique IDs passed; it has not been run or tuned.
- Reproduced the 9 original no-fault failures and 8 unreached fault fixtures on the mock path: 9/9 no-fault objectives passed and 8/8 faults fired. Traced all 17 real-P synthetic dev cases under the lead's existing shared Postgres `dev-gate/option-a` $1 scope; [per-case analysis](../ml/dev-p-failure-analysis.md) separates generic-type NLU extraction from choice/customer-simulator and conflicting fixture expectations.
- Tightened NLU v4 and normalized generic `cargo/cobro/cobrança/charge` out of `type_expr`; a matcher-backed dev regression passed. A single post-fix `pt.pending.v2` real-P check passed with the correct target and explanation. Scope readback: 40 settled attempts, $0.02748308 known and charged, zero unknown-cost attempts. The local `.env` approval flag was not changed; approval was process-local for the authorized calls.

### Done but not verified

- The complete 20-case no-fault and 20-case confirmation real-P acceptance gates have not run on the merged candidate. The original P study omitted intermediate slots, so the new trace is a same-case reproduction; the original `pt.pending.v2` slot cause remains a supported hypothesis rather than a recorded original fact. No NLG cause was found.

### Next / blocked

- Lead reviews the fixture/simulated-customer and matcher handoff in the analysis, merges the AI PR, then runs the full Step 3 gate under the same shared scope. Stop before re-release and final v2 until Sebastian's later signal. Never open the abandoned final-v1 artifacts or frozen held-out inputs in this diagnosis.

---

## Option A — dev gate before any re-release (in progress)

### Completed-verified

- Read handoff 12. The first final attempt is abandoned: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed. Its artifacts remain untouched; do not open or resume them.
- Initialized and read back the shared Option A Postgres budget: **scope `dev-gate/option-a`, run ID `option-a`, cumulative cap $1.00**, zero attempts and $0 charged at initialization. Both lead and AI lanes must use `PostgresSpendGate(store, scope="dev-gate/option-a", run_id="option-a")` before every provider attempt, including Jev, retries and fallbacks. Unknown usage retains its reservation. Never create separate run IDs, reset reservations, raise the cap, or re-enable a tripped breaker. Prior closed study budgets are excluded from this new allowance.

### Done-not-verified

- Merged #36 after rebase and green CI, then #28 and #24 after the owner-selected history-preserving updates and fresh green CI. #37 and the Step 3 real P dev gate remain in progress. No paid Option A dev run has been made by the lead.

### Next-blocked

- Obtain the AI lane's dev-only failure breakdown and previously authored 10 ES / 10 pt-BR confirmation set. Diagnose and fix only dev-supported causes, run the dev gate, report and stop before re-release. No final v2 run or deployment is authorized in this step.

---

## Frontend handoff 11 — historical PR refresh (freeze lifted by handoff 12)

### Completed (verified)

- Read the complete parallel-work handoff. Refreshed PR #28 against main `3ed98c9` while preserving published history under the no-force-push rule. Resolved documentation conflicts by retaining both the original human spot-check and v2 evidence; labels, measurements and private artifacts are unchanged.

### Done but not verified

- Updated PR #28 CI is pending. Submission refresh and frontend recording improvements are separate follow-ups in this handoff.

### Next / blocked

- Keep PRs open. Do not merge into main until Sebastian announces that the final run has finished; the lead merges afterward.

## 2026-09-27 — Frontend handoff 11: historical submission refresh (freeze lifted by handoff 12)

### Completed (verified)
- Refreshed PR #24 against main with history-preserving merge; retained the failed mock diagnostic.
- Updated six-slide pitch, narration and checklist with selected Gemini/Grok/Jev roles, measured development costs, matcher v2/human before-after and private real-model release evidence. Final-run metrics stay explicitly pending.
- Refreshed PR #28 separately; no paid inference, Azure change or frozen-suite execution.

### Done but not verified
- Exported slides/video and judge-access rehearsal remain unperformed.

### Next / blocked
- Keep these PRs open throughout Sebastian's merge freeze. Add frontend glass-box and recording helper on a separate branch; lead merges only after final-run completion.

## 2026-09-27 — Frontend handoff 11: historical recording helper and glass box

### Completed (verified)
- Refreshed open PRs #24 and #28 against main `3ed98c9` with history-preserving merges (no force push). Exact-head checks, web, Postgres and safety CI passed for both; PR #24 records current Gemini/Grok/Jev roles, matcher v2/human evidence and real-model deployment.
- Added precise per-call cost/latency/tokens and conversation known-subtotal/unknown-count rendering; additive allowlisted risk-union, retry/status and Grok-route display. Missing metadata stays unavailable, Gemini risk probabilities stay absent, and risk decisions come from the server.
- Added an authenticated recording helper using existing fixture reset plus read-back, then ES/PT/fraud persona shortcuts and Agent Desk. Prepared messages never auto-send or authorize actions. Live shortcuts require optional trusted persona bindings; existing live reset flags, fresh OTP, confirmation and scope remain enforced.
- Fixture Playwright suite: 12 passed; local B1/mock API customer suite: 6 passed; staff claim/resolve/OTP-reset suite: 1 passed. Production build, lint, TypeScript and repository pre-commit checks passed; final targeted glass-box rerun also passed after copy/mobile-table corrections. Authored-fixture phone screenshot inspected; no paid inference, organizer-row access, Azure changes or frozen-suite execution.

### Done but not verified
- Real-model/cloud recording of these changes is not performed. Current staff trace drops risk judgments/route and current personas omit story bindings; `apps/web/API-PROPOSAL.md` specifies the additive lead changes. Live reset remains disabled in cloud and cannot clear other personas' workspaces.

### Next / blocked
- [PR #37](https://github.com/sebastian-gm/bank-agent-lab/pull/37) is open; keep it and PRs #24/#28 unmerged until Sebastian announces final-run completion. Lead supplies reviewed trace/persona projections and decides any separately authorized bulk reset; UI does not widen RLS or bypass authentication.


## Jev release and final-program preparation — 2026-09-27 UTC (current)

### Completed-verified

- Read handoff 10 fully and verified the orchestrator's merges of #33/#34. Clean main runtime release **`07bccdc630e2b5eeb2dc746a7c3fe000718fd22c`** passed exact-main CI **36301043518** and safety **36301043504**. CI recorded **162 passed / 13 skips**, separate Postgres **14 passed**, B1 **32/32** with 12 readbacks, and browser suites **8 + 4 + 1 passed**. Earlier lead local checks passed 161 tests before the AI follow-up; its reported local total was 163.
- Reviewed PR #31's risk union and judges, integrated each Jev attempt with the durable shared Postgres reserve/settlement, and merged it after all four gates passed. Jev is a supporting risk opinion; Gemini retains intent/slots/phrasing, and deterministic code retains authorization and action authority. The same $12 cumulative gate covers final Gemini/Grok/Sonnet/Jev and restarts.
- `pytest tests/test_final_program.py`: independent authored fixtures passed interruption/resume, completed-case reuse, changed-pin rejection, duplicate-writer denial, deterministic judge selection, preservation of the 20-item human sheet and report metrics. `make checks` passed; no frozen input was opened or final model run started. Private input presence was checked without opening contents.
- Prepared the single detached `scripts.final_program start|resume|status` entry point. Exact commands are in [final-run-plan.md](../evaluation/final-run-plan.md). Atomic per-case/judge checkpoints and fsynced call journals preserve completed results and interrupted attempts; all retries/recovery retain spend. Outputs when authorized include `results.json`, `results.md`, all §15.4 outcomes/efficiency metrics and intervals/slices, repeat flips, paired B1/P comparison, Sonnet/Jev agreement, and `human-judge-20.csv`. This is implementation verification, not final evaluation evidence.
- TypeSafe key copied into `typesafe-api-key` in the approved Key Vault, equal-value readback verified in memory, then removed from local `.env`. Both model keys are absent locally; local provider remains mock/unapproved. The production API image independently passed imports for the SDK, API and six risk questions.
- `python -m scripts.azure_prices`: live East US 2 estimate **$34.63/month before tax**, checked **06:55 UTC**, below the $40 stop gate. Pushed both private ACR images using a temporary Docker config, then removed its token. `azure_dev plan` was reviewed: one TypeSafe-secret-only managed-identity grant and two app updates; ingress/capacity unchanged. `azure_dev apply`: **1 added / 2 changed / 0 destroyed**.
- `python -m scripts.azure_verify`: deployed SHA, owner-IP-only web HTTPS, internal-only API, replicas 0..1, Key Vault references/MI, Postgres TLS/firewall, private registry/state and existing approximate $30/$50 budget alerts passed. The prior Azure-services firewall limitation remains documented.
- `python -m scripts.azure_smoke` stopped at its intentional real-provider guard, before model calls. Equivalent no-model BFF checks in `artifacts/jev_readonly_smoke.py` passed **4 personas, 15 scoped organizer transactions, 4 customer-role denials**, OTP/logout and unchanged spend. Paid conversations used the capped helper below, not the uncapped generic smoke.
- `artifacts/jev_smoke_with_recovery.py` invokes `scripts.azure_llm_smoke` under **`jev-support-smoke`**, adding a replacement-replica GET before the ES dispute readback. ES normal explanation/denial/proposal/confirmation/readback, PT ambiguity/clarification/handoff and fraud handoff passed. Jev returned **5/5 valid** risk-call records across these three flows; recorded unions were checked, and no Grok fallback occurred. Original-session dispute recovery after a new API replica passed.
- `python -m scripts.serving_browser --target azure`: **3 surfaces**, **1 handoff claimed/resolved** passed. Across all four conversations: **14 paid calls, $0.00925008**, **zero unknown-cost attempts**, below the approved $0.10. The previous handoff-09 smoke ledger and exhausted allowance remain intact. Do not spend the remaining smoke allowance without a specific need under the owner's instructions.
- External workflow **36301783139** passed at the runtime SHA: non-allowlisted web **403**, internal API **404**. Required private receipt **`artifacts/azure/jev-release.json`** records the verified implementation SHA, controls/smoke/CI flags and evidence. A documentation-only release follow-up records final SHA/control/CI readbacks there; its application image contents must match the smoked runtime before acceptance.

### Done-not-verified

- No real frozen final evaluation, final subjective judge agreement or completed human judge sheet. The 20-item sheet is generated only when the authorized program runs. PT/MX/AR model-generated wording and lack of fluent-human PT review remain limitations. Standard-account TypeSafe ZDR and actual budget-alert email delivery remain unverified.
- The detached final command has been tested with authored fixtures; its full organizer workload remains deliberately unrun. The generic mock smoke is not a real-provider test; the capped release smoke and separate read-only/restart checks provide the deployed evidence above.

### Next-blocked

- **STOP for Sebastian's explicit final-run go.** The $12 ceiling is already approved; it is not a start signal. No new public ingress, cloud capacity or paid evaluation is authorized by this log.
- After the go, use the documented single start/resume command on the pinned verified main release. Do not independently rerun the 50 calibration items under the separate legacy judge command; they are already included in this program. Human validation remains a separate, unpaid review step.

---

## Handoff 09 integration — 2026-09-27 UTC (prior release)

### Completed-verified

- Reviewed and merged PR #12 (prompt v4, Gemini default, failure-only Grok, judge) and PR #29 (matcher v2), each with all four CI checks green. Matcher v2 is now the default MATCH artifact and is included in the API image; v1 remains available. Lane-authored training/human measurements below are their reported evidence, not lead reruns.
- Independent tests verify v2 scoped choices, rejection of all choices, explicit confirmation/readback, and denial of foreign or out-of-window candidates. No frozen inputs, labels, bindings or private matcher splits were opened during this layer.
- Added migration 0003 and Postgres reservations before every paid attempt. Production cap US$3/UTC day, smoke cumulative US$0.10, unknown costs retained, owner-only configuration; fallback/retries share the gate. A tripped reserve cannot trigger another model.
- Owner-authorized real-route final adapter uses fresh state, v4/v2, Gemini full/repeats and Sonnet subset; final system/judge clients share a cumulative US$12 database gate. Budget denial aborts. Journals save validated output/metadata only, never reasoning. Explicit final start gate tested without opening frozen inputs.
- `UV_CACHE_DIR=/tmp/aclara-uv-cache make checks`: **149 passed, 12 database skips**, six hooks, strict mypy, interfaces/catalog current; B1 **32/32**, **12 readbacks**. `python -m scripts.test_postgres`: **14 passed**, including concurrent reservations, restart/rollback exposure, cumulative cap and runtime privilege denial. `pnpm typecheck`, `pnpm lint`, `pnpm build`: passed.
- `python -m scripts.azure_prices`: live East US 2 **US$34.63/month before tax**, checked 05:33 UTC, below US$40 gate. OpenRouter public endpoint rates rechecked: Gemini standard $0.50/$3 per million input/output; Grok $1.25/$2.50. No model call in these price checks.
- `python -m scripts.azure_openrouter_key`: uploaded owner-supplied key to the approved vault, matching readback in memory, removed local entry and temporary file. No secret value printed or committed.

- Merged integration PR #30; all four PR gates and exact-main CI/safety passed. Runtime smoke release: `5b6e34e15908372d307042a01292201c3bbd8d8d`. Main CI `36297937359`, safety `36297937382`; PR CI `36297745728`, safety `36297745767`.
- `python -m scripts.azure_migrate_ops`: migration and non-owner TLS/RLS readback passed. `terraform -chdir=infra validate`: passed. Reviewed private plan: one API-identity grant limited to the OpenRouter secret, two app updates, no deletions or ingress/capacity changes. `python -m scripts.azure_dev apply`: **1 added / 2 changed / 0 destroyed**. API remains internal; web stays owner-IP-only HTTPS plus login.
- `python -m scripts.azure_verify`: passed deployed SHA, model flags, Key Vault/MI references, source serving, replica limits, Postgres firewall/TLS, private ACR/state and existing approximate US$30/50 alert settings. Budget alert delivery is still untested.
- Real Azure smoke: ES explanation → explicit denial → proposal → confirmation → case readback passed; PT ambiguity → clarification → ESC-04 handoff passed; fraud FRD-01 handoff passed. Staff claim/resolve readbacks and live Ops passed. Required flows used valid, non-degraded Gemini NLU v4 and matcher v2 on charge flows, with no fallback attempts. The first PT smoke failed a verifier assumption that every ambiguous input immediately gets choices. Its corrected verifier permits clarification only with a missing-expression or matcher no-match event; the retry measured v2 no-match, then safe handoff. No model, prompt, threshold or policy was tuned.
- `python -m scripts.serving_browser --target azure`: real browser **3 surfaces**, **1 handoff resolved**, organizer source label and measured workspace verified. Additional local `pnpm test:e2e --live`: **4/4 passed** on authored fixtures.
- **Five conversations attempted total** (including the failed verifier attempt); **10 paid calls, US$0.0107415**, **zero unknown-cost attempts**, all below the approved US$0.10. The allowance is exhausted: do not run another real smoke without new approval. Preserve `artifacts/azure/llm-smoke-conversations.json` and the database cost ledger.
- External access workflow **36298514693** passed: non-allowlisted web HTTP 403 and internal API HTTP 404.
- Aggregate receipts: `artifacts/azure/handoff09-smoke.json`, `verified.json`, and the final session release receipt `handoff09-final.json`. The smoke above is pinned to the runtime SHA; the follow-up changes only documentation and the smoke verifier. Final deployed SHA/control/CI readbacks are recorded in the final receipt and owner report.

### Done-not-verified

- The real final evaluation, judge agreement, human PT/MX/AR language review, broad model safety and actual final cost remain unverified. The prior frozen diagnostic remains failed acceptance.

### Next-blocked

- Runtime layer is verified on the SHA above. The final receipt identifies the documentation/verifier-only follow-up and its control checks. Next layer: AI-lane final evaluation after Sebastian's signal. No further real conversation is authorized in this layer.
- Sebastian must give the AI lane the separate final-run start signal. Public/judge ingress remains unapproved. No new paid evaluation or cloud capacity requested.

---

# Prior release and lane evidence

Session: handoff 08, 2026-09-26 America/Vancouver; continued 2026-09-27 UTC.
This summary supersedes earlier task lists. Earlier release evidence remains in Git history and linked reports.

## Frontend lane — submission kit (2026-09-27 UTC)

### Completed (verified)

- Read handoff `07-docs-submission.md` fully and followed its priority order. Interrupted docs for PR #17 when the lead shipped #21; integrated trusted roles, staff/trace/Ops endpoints, upstream revocation and gated reset with independent readbacks. Private PR #17 is mergeable at `3d63bca`; GitHub `ci` run `36291326889` and `safety` run `36291326877` passed all four jobs. Local evidence: eight fixture, four customer API and one staff API browser tests, accessibility checks, TypeScript, ESLint, production build and repository hooks. Lead owns Azure connectivity verification and shared browser CI.
- Authored the eleven requested submission documents on `docs/submission-kit`: README, R1–R14/seven-criterion traceability, system/state diagrams, STRIDE/OWASP test mapping, actual payload/provider/retention boundaries, trade-offs, projection sensitivity, limitations/readiness, six slides and the video draft. Corrected mock diagnostic aggregates remain explicitly failed-gate evidence; final model/human/deployment metrics retain visible `TODO(results)` entries.
- Read aggregate JSON and verified quoted headline, matcher and problem-analysis values. Corrected the brief's broad charge/fee automation claim and highest-handling-time claim against pipeline output. Read named implementation/tests and linked local restore/cold-start evidence; no outcome rerun, policy tuning or frozen-suite edit.
- A local documentation audit passed 241 link/fence/test-ID checks across the eleven documents; all requirement/criterion mappings, six-slide count and aggregate assertions passed. Narration is 297 words before rehearsal. `git diff --check` and the working-tree data/secret/size policy passed. Provider statements cite official sources; account-specific terms remain unverified. No organizer rows, credentials, Azure actions or model calls were used for this assignment.

- Private [PR #24](https://github.com/sebastian-gm/bank-agent-lab/pull/24) was opened and read back with only the assigned documents plus this log. All four CI jobs passed at `a98203a` (`ci` run `36291808092`, `safety` run `36291808097`); mypy and data/secret/size hooks also passed locally. This log-only follow-up records that evidence.

### Done but not verified

- Mermaid source is provided; final deck export and deployed video recording/rehearsal are not performed. The requested PT staff scene depends on an authorized deployed staff workspace. Judge access and a separate access-code gate are not established; the owner-IP boundary remains.
- Azure BFF-to-API connectivity, latest deployed browser behavior, native language/human label review, selected-provider account terms and real-model evaluation remain pending. The projection intentionally has no invented hours/savings.

### Next / blocked

- Lead review of PR #24 and PR #17. Keep the documentation PR review-ready only after the latest CI is green, and continue prioritizing PR #17 feedback. Lead owns release/network checks; owner approval is required for any future model spending, public submission or wider judge access. No new approval is needed for the completed local documentation work.

### Pitch pass on PR #24 — 2026-09-27 UTC

#### Completed (verified)

- Reworked the six slides into takeaway sentences, each with three short bullets and one table or diagram. Moved methods/caveats into collapsed speaker notes and kept one explicit production/limits slide. The final real-model scorecard uses only `TODO(results)` cells, with separate B1/P and planned Gemini 3 Flash/Claude comparisons and conversation-cost definitions.
- Rewrote the video as 248 spoken words with a customer hook, deployed product on screen at 0:10, separate stage directions and the final fifteen seconds reserved for limits. Added `docs/submission/checklist.md` for access/role/reset details, deadline confirmation, release/recording SHA, full-history Gitleaks/data review, owner-approved publication and email delivery. The sandbox remains private; checklist actions are not executed.
- Checked the priority PR #17: no new review beyond the previously addressed backend-contract review. Merged current main `6aa0cf7` into the published docs branch without rewriting history. New lead changes preserve endpoint schemas; no frontend implementation edit was needed for this pitch pass.
- Local structural/source audit passed: six slide headlines, three bullets and one visual each; 248 narration words; 44 links/reference targets; displayed pipeline/matcher values matched aggregate JSON. `git diff --check` passed. Checked official organizer date, Gitleaks syntax and GitHub visibility documentation; deadline time/zone still requires organizer confirmation. No Azure/model calls, credential reads, public release or email send.

#### Done but not verified

- Final held-out real-model B1/P and Gemini/Claude measurements, human review, actual recording duration and deployed rehearsal remain pending. The AI lane's comparison document still has no measured default; Gemini 3 Flash is explicitly a planned choice. Full-history Gitleaks and publication/access steps are checklist tasks, not completed audits.

#### Next / blocked

- Update PR #24 and verify final-head CI before reporting it ready. Lead review/deployed access verification and the AI lane's final model comparison remain release follow-ups. No permission is needed for this documentation edit; future spending, visibility changes and sending the submission need explicit owner authorization.

## Completed-verified

### Human es-CL spot-check — Data/ML follow-up, 2026-09-27 UTC

- Preserved Sebastian's nine recollections and intentional typos. Independently authored and hashed gold intent/slots before inference from brief §5.2/§9. Verified nine owned targets, nine distinct customers and no overlap with any v1 matcher benchmark split. No frozen scenario-suite access or policy execution.
- Ran the approved `google/gemini-3-flash-preview` NLU → unchanged v1 MATCH chain at `c8588f4fc39593ab60ab0bfe9eeaab6bb6309a84`: nine valid calls, zero fallbacks, **US$0.009933** provider-reported cost against the US$0.50 cap. Kept the worktree key private and process-local; no model thinking stored.
- Published aggregates in the [result review](../ml/result-review.md#human-spot-check-n9-es-cl) and [model card](../ml/model-card-charge-matcher.md#human-spot-check-n9-es-cl): intent 5/9, corrected core slots 7/9, top-1 6/9, recall@3 8/9, **nine no-match decisions**. A documented post-inference annotation serialization correction changes core-slot accuracy from 6/9 to 7/9; original frozen labels and predictions remain intact. No model, prompt or threshold changed.
- Wrote and read back all nine detailed intent/slot/transaction/decision reports, gold, billing, runner and manifests under ignored `artifacts/human-validation/spanish-40/spotcheck-es-cl-v1/`. Source recollection bytes remain unchanged. No card field values entered Git.
- Independent aggregate/billing recomputation, all artifact hash checks, verbatim recollection readback, 13 local documentation links, diff whitespace and staged-file policy passed. This change touches only the two requested ML documents plus this additive session entry.

### Matcher v2 follow-up — 2026-09-27 UTC

- Implemented versioned choice-first decisions while retaining v1 behavior; added deterministic sparse-language synthetic variants and a train/validation-only v2 training entry point. The [v2 protocol](../ml/matcher-v2-protocol.md) fixes noise, cost preferences, selection grids and test/human access order before fitting.
- Ten matcher/MatchState checks passed, including scoped retrieval, legacy behavior, low-existence choice fallback, all-low/empty abstention, literal-format noise and evaluator/export policy consistency. Ruff and strict mypy passed. No frozen held-out scenario-suite access or paid calls in this implementation stage.
- Trained v2 on 18,000 synthetic train / 9,000 validation queries using 20 seeded trials. Froze the model at 05:03:59 UTC before synthetic-test/human access; verified exact code/export hashes and v1 artifact bytes unchanged. Synthetic 3,000-case wrong proposals fell 30→13 under identical serving features and the v2 cost table. Sparse-language diagnostics and their generator limitations are in the [v2 model card](../ml/model-card-charge-matcher-v2.md).
- Ran the single authorized human after-check: nine valid Gemini calls, no retries/fallbacks, **US$0.009762**. On identical fresh NLU slots, v1 returned nine no-matches; v2 returned six correct proposals, two choices containing the target and one no-match. Target top-1 was 9/9 for v2 versus 6/9 for v1. No post-check tuning. Original gold plus the existing separator erratum, recollection bytes and v1 reports remain unchanged.
- Verified zero overlap between human customers and the actual v2 fitting splits; wrote and read back all nine private before/after cases, billing, frozen inputs and manifests under ignored artifacts. No frozen held-out scenario-suite access or card values in Git.
- Final local regression: **123 passed, 9 database-dependent skips**, including **11 matcher checks**; Ruff, strict mypy and all pre-commit hooks passed. Verified 15 local documentation links, serving-boundary loading/ownership denial, exact training/protocol hashes, v2 checksums and unchanged v1 artifact bytes.

### Safety and resolution (tasks 1–2)

- Read handoff 08 fully and followed its order. PR #25 merged after all four gates passed. No credential-bearing organizer document was opened, no organizer rows/secrets entered Git or CI, and no real-model call ran.
- Reduced saved run-01 observations to [aggregate taxonomy](../evaluation/dev-acceptance-fixes.md). Both B1/P had six forbidden dispute writes, all ESC-04: four ambiguous/unsupported and two human-required, ES 2/PT 4. The required-packet denominator is 54, not the additional 60 handoffs with no required-field rubric.
- Independently authored dev regressions fixed missing/contradictory identification, uncertain or negated choice, stale proposals, changed source facts and reopening terminal handoffs. Scoped status inquiry and existing-case status readback were repaired. Packets now include bounded redacted customer statements and preserve preferred language separately from fallback route.
- **50 independent dev checks passed**, including zero forbidden writes, two positive dispute/readback controls, ES/PT status recovery and packet redaction. **No suspected gold-label error was established** from aggregate evidence. System, adapter and unproven label causes are separated in the report.
- The original frozen result remains **failed acceptance**: 67/193 SAR, six forbidden writes per system, incomplete required handoffs. No new full diagnostic or paid model run was made. Every observation reduction and the metadata-only search touch is recorded in the [access log](../evaluation/test-access-log.md); future preflight/run entry points log hashes and started/completed/failed access automatically. The one remaining pre-final diagnostic remains reserved.

### Frontend and organizer serving (task 3 plus owner clarification)

- Integrated frontend PR #17 and its follow-ups: HTTP-only BFF authentication, trusted roles, live Customer Chat, scoped Agent Desk claim/resolve and measured Ops/traces. Added all three browser suites to shared CI. Reset remains disabled in Azure.
- Rebuilt and promoted organizer gold from `LOCAL_RAW_DIR` into persistent ignored `lake/`. Dataset hash matches the pinned `b86f445...97c9`; no source-version difference. Gold/serving counts: **150,000 customers, 400,000 products, 492,414 120-day transactions, 13,164 FX rows, 1,200 agents and 150,000 complaint aggregates**.
- Local serving load passed full sorted-row checksums and independent committed metadata readback. Four private personas bind to distinct development-partition organizer customers; 15 owned scoped transactions total. IDs remain private Postgres configuration. Two Ops personas can demonstrate all surfaces in their own workspace; two customer personas are denied staff routes. Shared demo password/OTP remain dev simulations.
- Runtime source reads use the non-owner pool, forced customer RLS, ownership join and half-open 120-day UTC window. Dataset/clock/build identity is pinned and refresh reads coordinate with the atomic loader. Missing serving state fails closed. No authored-ledger fallback in the deployed mode. See [serving runbook](../serving-demo.md) and [ADR 0004](../adr/0004-serving-isolation.md).
- Held-out adapter now requires that same serving source with RLS on every base read, plus only declared frozen counterfactual overlays in isolated memory. An independent authored dev case verified source-plus-overlay execution. Frozen inputs/labels and run-01 observations remain unchanged. The new adapter has not run the frozen suite.
- Local BFF smoke passed ES/PT normal/ambiguous/human flows: **4 personas, 15 scoped transactions, 2 cases, 4 handoffs, 2 claims, 2 resolutions and 80 audit entries**. Separate browser verification rendered all three surfaces on organizer-backed activity and verified a claimed/resolved handoff and organizer source label. No source screenshots, DOM dumps or browser traces were saved.

### Commands run

| Command | Observed result |
|---|---|
| `PRE_COMMIT_HOME=/tmp/aclara-precommit-cache UV_CACHE_DIR=/tmp/aclara-uv-cache make checks` | Six hooks, staged-file policy, compile, interfaces/catalog; **118 passed, 9 database-dependent skips**. B1 **32/32**, **12 readbacks**. |
| `.venv/bin/python -m scripts.test_postgres` | **9/9 passed** on a disposable local database, including serving RLS/ownership, identity realms, cross-customer denial, original-session restart recovery, build-change rejection and independent serving-plus-overlay execution. |
| `pnpm typecheck`, `pnpm lint`, `pnpm build` in `apps/web` | Passed. |
| `PLAYWRIGHT_BROWSERS_PATH=../../artifacts/frontend/browsers pnpm test:e2e` (`--live`, `--staff`) | **8 fixture**, **4 live customer**, **1 live staff** tests passed; authored test data only. |
| `.venv/bin/python -m aclara.data.cli build --lake lake --no-reports` | Pinned dataset promoted with the counts above; zero invalid silver rows. |
| `.venv/bin/python -m scripts.load_demo_serving --target local` | Full table checksum/commit readbacks and four private bindings passed. |
| `UV_CACHE_DIR=/tmp/aclara-uv-cache make up` | Compose images built; migration succeeded; Postgres, serving API and web healthy. |
| `.venv/bin/python -m scripts.local_smoke` | Organizer BFF three-surface counts above; no model calls. |
| `.venv/bin/python -m scripts.serving_browser --target local` | Real browser Chat/Agent Desk/Ops and resolved handoff passed. |
| `.venv/bin/python -m scripts.azure_prices` | **2026-09-27 04:00 UTC**, live East US 2 modeled **US$34.63/month before tax**, below US$40 gate; no capacity/resource additions. |

### Restricted Azure release

- Read-only probe from the existing Azure web container reproduced API HTTP 403 under the API's owner-IP rule. Deployed an **internal-only API in the same existing Container Apps environment** and retained owner-IP-only HTTPS on web plus login. No new resources, networking products, replicas or broader internet ingress. The web BFF keeps bearer tokens out of browser JavaScript.
- Azure full gold load was initially interrupted during slow small-batch checksum readback, rolling back its uncommitted transaction. Restarted with 5,000-row batches and the same full checks. The restarted Azure load passed full checksums and independent committed readback for all six tables, four private personas and 15 scoped transactions. The serving BFF smoke and replacement-replica recovery also passed.
- Existing approved PostgreSQL Azure-services firewall exception, Key Vault passwords, managed identities, TLS verify-full and approximate US$30/50-equivalent budget alerts remain required. [Network plan](../azure-private-dev-plan.md), [production limits](../production-readiness.md).

- PR #26 merged after all five gates passed; GitHub also marked frontend PR #17 merged. Main `c8588f4fc39593ab60ab0bfe9eeaab6bb6309a84` passed CI **36294472055** and safety **36294472075**. Built/pushed exact clean-main images to private ACR; temporary registry credentials were removed.
- Reviewed the saved Terraform plan in memory, including exact image SHA, internal API, owner-IP-only web, HTTPS, mock, non-owner DB role and unchanged sizing. Apply: **0 added, 2 changed, 0 destroyed**.
- `.venv/bin/python -m scripts.azure_smoke` passed organizer-backed ES/PT normal/ambiguous/human paths and all three surfaces: **4 personas, 15 scoped transactions, 2 cases, 4 handoffs, 2 claims/resolutions, 80 audit entries**. A replacement API replica recovered the original authenticated case; logout then revoked access.
- `.venv/bin/python -m scripts.azure_verify` passed exact-image, restricted ingress, single revision, min 0/max 1, managed pulls, Key Vault references, non-owner Postgres/TLS, approved firewall exception, state firewall and converted USD30/50 budget controls.
- `.venv/bin/python -m scripts.azure_dev plan` returned **No changes**. Credential-free external workflow **36294730475** passed: web **403**, internal API **404**. Consumed plans were removed.
- `.venv/bin/python -m scripts.serving_browser --target azure` passed actual browser Chat → handoff → Agent Desk claim/resolve → measured Ops with organizer provenance. No screenshots or row-level traces were recorded.
- This documentation-only follow-up is released through the same restricted process. Exact final main SHA and control/smoke receipts remain in ignored `artifacts/azure/verified.json` and `serving-smoke.json`, avoiding a self-referential commit SHA in this log.

## Done-not-verified

- Human es-CL spot-check: independent human gold review and agreement are unavailable. This is NLU → MATCH only, not full conversation/action or production validation; the remaining 31 private Spanish cards are blank.

- Matcher v2: application integration and final evaluation remain unverified. NLU intent errors and abbreviation parsing persist; one human target remains rejected by the preselected very-low-score floor. These small, synthetic-card diagnostics do not establish production accuracy or complete agent safety.
- Frozen acceptance after these fixes remains unknown; the preserved run-01 failure is the only full-suite result. Human labels, Spanish owner review and fluent Portuguese review remain pending. PT/dialect phrases are model-authored; prior cross-vendor authoring checks do not replace human review.
- No lead real-model comparison, selected default or different-vendor judge run. Keep `LLM_PROVIDER=mock`. Durable model spend accounting remains future work.
- Azure PITR/regional DR, realistic-volume restore, automatic retention, sustained concurrency, actual charges and budget-email delivery are unverified. Tiny local restore evidence remains in [recovery report](../ops-recovery.md).

## Next-blocked

- Human es-CL follow-up: review the private per-case report with Sebastian; investigate disputed-charge intent handling, abbreviated amounts, unrelated date binding and rejection by the frozen match-exists threshold on separate development examples. Preserve current gold/predictions and the frozen model; this session makes no tuning changes.

- Matcher v2: lead must integrate the new artifact and policy dispatch before the final run, preserving confirmation and rejection of all offered choices. Keep the frozen v1/v2 results; investigate remaining language gaps on independent development cases. This lane leaves orchestration and the frozen suite untouched.
- Next layer after this release: provider comparison on the independent dev suite, broader independently authored language cases and human review. Show the cost estimate and wait for Sebastian's go before any real-model run. No cloud expansion, access broadening or estimate above US$40/month is authorized.
- Reserve the one remaining full held-out diagnostic; log every access, preserve frozen bytes and publish only aggregates. The final evaluation must use organizer serving source and declared overlays.

## AI lane integration evidence

The following sections retain the AI lane’s historical reports; later dated decisions supersede earlier next steps. Lead production wiring and final-run adapter work are in progress under handoff 09. No lead real-model or frozen-suite run has started.

## AI lane — 2026-09-27 (label decision and round two)

### Completed (verified)

- Applied Sebastian's recognition-versus-denial rule to ten derived 32-case NLU labels. Kept the two explicit-denial cases as disputes. Added frozen v3 prompt and a matching deterministic P fallback; retained B1's legacy routing so its lead-owned end-to-end dispute readbacks remain intact. `charge_inquiry` ↔ `dispute_charge` is now graded as an intent error only when the authorized end state is correct. Stored v2 predictions regrade from 32/32 to 22/32 under the new labels for each of four models; old metrics are marked historical.
- Built a separate 150-case AI-authored, unreviewed hard NLU dev fixture: 30 each ES-MX, ES-CO, ES-AR, pt-BR and mixed, 219 scored slot annotations, slang/false-friend/pesos/vague-date and amount/code-switch/injection slices, and no exact-message overlap with the 32-case suites. The frozen held-out end-to-end suite was not used to tune or choose a model.
- Ran the six requested full-suite model IDs plus `anthropic/claude-opus-5` on a fixed 30-case sample: 930 scored model-case outcomes, 930 valid finals, 932 provider attempts. Five full-suite models scored 150/150 intent; Haiku scored 149/150; Opus 30/30. Intent remains saturated; slot, language-ID, injection-flag, latency and per-call cost differ. The table, 95% intervals, dialect slices and confusion matrix are in [model comparison](../ml/model-comparison.md). No default was selected.
- Response-cost ledger: $0.402383 round one, $0.034314 round-two pilot, $0.072047 archived Haiku first pass and $3.012058 scored round two = **$3.520801 known per-call spend**. Two Haiku interruptions had no response usage/cost and are excluded from per-case cost; a separate $0.30 guard keeps the run below Sebastian's $10 cap. Full Haiku results came from the schema-capable ZDR Amazon Bedrock global route after pacing. Production `.env` remains `LLM_PROVIDER=mock`, `LLM_REAL_CALLS_APPROVED=0`, with unique `COMPOSE_PROJECT_NAME=aclara-ai`.

### Done but not verified

- The 150 AI-authored labels lack human verification and ES/PT fluency ratings. Perfect observed intent macro-F1 gives degenerate bootstrap intervals; this set cannot decide among the five perfect full-suite models. The exact bill for the two no-usage Haiku interruptions cannot be assigned from per-call fields. B1's lead-owned explain-then-offer transition is still needed before its rules classifier can adopt the new NLU label without changing end-to-end behavior.

### Next / blocked

- Sebastian will decide a default after reviewing the aggregate trade-offs and obtaining stronger independent human-checked NLU evidence. Lead review of PR #12 and the B1 workflow transition remain. No further paid run is authorized by this section; keep production in mock mode.

## AI lane — 2026-09-27 (selected default and round three)

### Completed (verified)

- Configured Sebastian's selected `google/gemini-3-flash-preview` route for both NLU and phrasing. `LLM_PROVIDER=mock` still selects the mock entries; a lead-enabled `openai_compat` deployment selects the reviewed `default` route. The runtime NLU prompt now uses the evaluated v3 taxonomy. Persistent `.env` remains mock with its approval flag unchanged; the real-call gate was process-local for this approved comparison.
- Ran six cheap challengers on the same frozen 150-case unreviewed NLU dev suite and v3 prompt: GPT-5 nano/mini, Grok 4.20, Qwen3 Next 80B instruct, DeepSeek V4 Flash 0731, and Mistral Small 4. All 900 model-case outcomes are checkpointed under ignored `artifacts/ai-round-three/`. The [comparison](../ml/model-comparison.md) reports exact IDs, 95% intervals, all-attempt JSON validity, injection flags/false flags, latency, per-call cost and paired slot-F1 differences. No challenger matched Gemini 3 Flash's 10/10 injection flags and 95.7% slot F1.
- DeepSeek's `wafer/fast` ZDR route was fastest in a fixed three-case/provider probe: 2.65-second median versus 5.37 on DeepInfra and 7.08 on OpenInference. DeepSeek used `reasoning=none`; OpenAI required `minimal`; Mistral was pinned to `mistral/us` after an unpinned 429. The scored OpenAI failures were `content_filter` stops, four non-valid attempts and two missing finals per model, not output truncation.
- Known round-three per-call spend, including successful pilot and provider probes, was **$0.292253**. Known cumulative spend across rounds was **$3.813054**, below the $10 cap. Six initial HTTP 400/429 attempts had no usage/cost response and remain unassigned; a separate $0.12 guard plus $0.30 reserve protects the cap. No key-level account delta was used for model cost.
- `make checks` passed: six hooks, file policy, compilation, **76 tests passed and 7 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog. No model messages, model thinking, credentials, or organizer rows were committed.

### Done but not verified

- The 150-case dev set and ES/PT fluency judgments still lack independent human review. Ten synthetic injection cases measure suspicion flags, not arbitrary attack resistance. The chosen Gemini route has not been exercised in deployed production; deployment needs the lead's production key and activation.

### Next / blocked

- Superseded by Sebastian's later choice of Grok 4.20 as the failure-only fallback. Claude remains reserved for the independent final held-out frontier comparison and judge validation. A new approval is needed before additional paid model runs.

## AI lane — 2026-09-27 (fallback, judge and final-run plan)

### Completed (verified)

- Configured `x-ai/grok-4.20` on the ZDR `xai/zdr` route as Gemini 3 Flash's **failure-only** cross-vendor fallback. The structured client retries Gemini once before invoking Grok; the same run budget and approval gate cover both, and non-default frontier routes have no fallback. Persistent production settings remain `LLM_PROVIDER=mock`, `LLM_REAL_CALLS_APPROVED=0`; no production key or route was activated.
- Added [subjective judge rubric](../evaluation/judge-rubric.md), score-only Sonnet 5 OpenRouter harness, and quadratic-weighted κ/paired-agreement computation. The judge input excludes gold and objective outcomes; scoring is limited to language/register, clarity, empathy, and handoff-summary usefulness. Generated an ignored mode-0600, 50-row synthetic human sheet at `artifacts/judge/human-validation-50.csv` (SHA-256 `4f862e442d1cce88c8f90b38a22cb53691ed8efe9352bf4ca878c952520f5794`), with all human ratings blank and no frozen held-out cases.
- Sebastian authorized only a sub-$0.50 judge smoke. Sonnet 5 on ZDR `google-vertex/global` returned **3/3 valid** strict score-only responses; known per-call cost **$0.008042**. An advertised Bedrock route returned six no-usage provider errors and a diagnostic HTTP 404; all seven unknown-cost attempts are kept in ignored metadata with a conservative **$0.35** guard. Known spend plus guard is **$0.358042**, below the $0.50 limit. No 50-case judge calibration or final held-out real-model run was made.
- Wrote the [priced final-run plan](../evaluation/final-run-plan.md): B1 200; Gemini P 200 full plus two additional 100-case passes (three total subset runs, 400 P case-runs); Sonnet P once on the same 100; 50 human-calibration and 100 B1/Gemini judge assessments. It gives exact route/prompt settings, per-component token and cost estimates, a 5% Grok fallback sensitivity, a **$4.590 illustrative model-cost total**, a proposed **$12 future stop ceiling**, and **60–90 minutes** estimated serial machine time. It explicitly requires lead acceptance fixes and a separate approval before execution.
- `make checks` passed: six hooks, strict mypy, file policy, compilation, **81 tests passed / 7 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog.

### Done but not verified

- The human sheet has no ratings, so no judge agreement or weighted κ is claimed. The three-item smoke proves route/schema operation only; the 50-item judge run, human ES/PT wording review, final system costs/latency, and real-model safety remain unmeasured. The final-run cost and time are estimates using current public ZDR rates and conservative token assumptions.

### Next / blocked

- Sebastian to fill the 50 human scores and approve a fresh priced judge calibration/final run after the lead's independent acceptance fixes, frozen SHA, production-key deployment, and a cross-process spend breaker. The current `evals.heldout` adapter still hardcodes mock metadata/execution and needs the lead's real-route integration. Do not run the frozen real-model test or additional paid judge calls under this session's smoke approval.

## AI lane — 2026-09-27 (denial prompt v4 and final preflight)

### Completed (verified)

- Added [NLU prompt v4](../../prompts/nlu/v4.md) for explicit ES/PT denial cues, including Chilean informal speech and merchant nonattendance, while keeping recognition or uncertain memory as `charge_inquiry`. The runtime P NLU route now selects v4. No human spot-check utterance or frozen held-out label was added to development fixtures.
- Paired Gemini 3 Flash v3/v4 on 40 new synthetic, team-authored denial/inquiry cases. The first 24 were saturated (24/24 each); the 16 harder contrastive cases yielded v3 **11/16** versus v4 **16/16**, with five v3 explicit-denial→inquiry errors and zero v4 errors. Combined: v3 **35/40**, v4 **40/40**; all **80/80 attempts** valid schema JSON. The [comparison](../ml/model-comparison.md) reports aggregate evidence and limitations. Per-call cost **$0.106686**, no unknown-cost attempts, below the separately approved $0.49 cap. These authored cases do not establish independent production accuracy.
- Pinned selected Gemini and Sonnet frontier to ZDR `google-vertex/global` for the priced final configuration and updated Gemini's reserve rate to the standard $0.50/$3 per million. Production `.env` stays mock/unapproved. `make checks` passed six hooks, strict mypy, staged-file policy, compilation, **83 tests passed / 7 database-dependent skips**, B1 **32/32** with 12 readbacks, interfaces and policy catalog. PR CI follows this section.
- Sebastian pre-approved the [final-run plan](../evaluation/final-run-plan.md) with a $12 ceiling but withheld the start signal until lead acceptance fixes, matcher v2 and prompt v4 merge with green gates. The revised v4 token assumption raises the illustrative model estimate to **$4.692**, still within the approved ceiling. Read-only [preflight](../evaluation/final-preflight.md) verified the frozen 200-case manifest/counts but stopped on a missing private customer-binding artifact; it made no system/model run and wrote no final output.

### Done but not verified

- Human ES-CL and fluent PT review of v4 wording, independent validation, and final end-to-end behavior remain unverified. The current held-out adapter is still P/mock only; a durable cross-process spend gate is not wired in this branch. The private binding artifact is absent here.

### Next / blocked

- Lead supplies/verifies the frozen private binding, merges acceptance fixes and matcher v2, integrates the real-route final adapter and spend breaker, and reads back green gates. Merge prompt v4 without held-out tuning. Do **not** begin the $12 final program until Sebastian's explicit start signal.

## AI lane — 2026-09-27 (TypeSafe Jev challenger)

### Completed (verified)

- Read the live TypeSafe SDK/model/primitive and legal documents and the user-specified local SDK example. Added `typesafe-sdk` 0.7.2 to the optional LLM and dev dependencies, a separate typed-judgment-only adapter, versioned intent/risk and rubric questions, and a checkpointed cross-provider comparison. No Jev slot extraction, phrasing, identity, policy or write route was added. [Data provenance](../data-provenance.md) records TypeSafe's no-training claim, ordinary retention/US hosting, and unverified ZDR status; only synthetic text was sent.
- Under Sebastian's new **$1 combined** OpenRouter/TypeSafe cap, reran Gemini 3 Flash with v4 and Jev 1.13 on the same unreviewed 150-case NLU dev set. All 300 attempts returned valid finals. Gemini: **150/150 intent**, **9/10 injection flags**, **0/140 false flags**, p50 **1.897 s**, **$0.211601**. Jev: **146/150 intent**, **6/10 flags**, **0/140 false flags**, p50 **0.090 s**, **$0.005877**. The [comparison](../ml/typesafe-jev-comparison.md) includes ES/PT/mixed slices, ten-bin ECE, 95% intent intervals, risk-cue counts and limits. Jev's four intent misses include three inquiry→dispute errors under Sebastian's label rule.
- Scored the same three previously saved Sonnet synthetic judge-smoke items with four Jev rubric Scores, without any objective gold or new Sonnet call. Jev cost **$0.000124**; dimension-level exact agreement and weighted κ are in the report. New known per-call total **$0.217601**, no unknown-cost attempts or retries, under the $1 cap. Production remains mock; Gemini remains default, Grok remains failure-only fallback, and Sonnet remains judge candidate. No final frozen-suite run started.
- On this follow-up branch from current `main`, `make checks` passed six hooks, strict mypy, staged-file policy, compilation, **141 tests passed / 9 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog. The pinned-served-model validation test also passed. The ignored `.env` and TypeSafe checkpoints are excluded from Git.

### Done but not verified

- The 150-case development labels and ES/PT fluency still lack independent human review. The three-item Jev–Sonnet judge agreement is not human validation; the 50 human-sheet ratings are blank. Other risk-cue labels have no independent gold in this suite, so only injection flags were graded. TypeSafe standard-account zero retention is not verified and Jev was not selected for production.

### Next / blocked

- Sebastian decides whether any later Jev experiment is useful; this PR does not change the selected default or judge. Keep the $12 final program on hold until the lead's acceptance fixes, matcher v2, prompt v4 merge, private binding/preflight, spend breaker and green gates are read back, then wait for Sebastian's explicit start signal.

## AI lane — 2026-09-27 (Jev supporting roles)

### Completed (verified)

- Added risk-only Jev `Noul` second opinion in the NLU lane for selected Gemini 3 Flash calls. It runs concurrently, unions each cue at `>=0.5`, and records Gemini raw booleans, unavailable Gemini per-cue probabilities as `null`, Jev raw probabilities/flags, the union, usage/cost and degradation in the existing execution-record path. Ordinary Jev failure, timeout or missing key leaves Gemini flags intact; a durable final-budget denial aborts the program. No orchestrator or `NluFrame` interface changed. Mock and Sonnet frontier routes do not invoke Jev.
- Replayed the 150 saved paired development cases without new paid calls: Gemini injection **9/10**, Jev **6/10**, union **9/10**, all **0/140 false flags**. Jev adds two distress flags without independent distress gold. The paired max-of-two latency **proxy** is 1.897 s median / 2.224 s p95, unchanged from Gemini; live parallel latency is not measured. [Aggregate report](../ml/typesafe-jev-comparison.md).
- Integrated a gated [dual subjective judge helper](../../src/aclara/llm/dual_judge.py) into the full 50-item Sonnet judge command. It scores both on the same items, reserves Jev against the lead's merged durable Postgres gate, checkpoints raw Jev distributions, and supports Jev–Sonnet plus separate judge–human weighted κ once all human ratings exist. Its offline tests made no final or new judge paid calls. [Final plan](../evaluation/final-run-plan.md) prices 410 Jev risk calls and 150 Jev judge calls at $0.02583 and $0.01260 before rounding, for an illustrative **$4.730** total below the existing $12 ceiling. The final start is still withheld.
- After reconciling the lead's current final-route and durable-budget changes, `make checks` passed six hooks, strict mypy, staged-file policy, compilation, **159 tests passed / 12 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog. The merged tests cover Jev reservation/settlement in the shared journal and budget store. No organizer rows, credentials, model thinking or paid-call artifacts were staged.

### Done but not verified

- Concurrent provider latency, Jev failure rate in production, the five non-injection risk-cue accuracies and 50-item judge–human agreement remain unmeasured. Gemini prompt v4 supplies Boolean risk flags, not per-cue probabilities. TypeSafe standard-account zero retention remains unverified. PR #31 merged while this branch was being reconciled; its follow-up integration and frozen private-binding preflight are not yet merged/verified together.

### Next / blocked

- PR #34 subsequently merged into the pinned `07bccdc` main before the merge freeze. The lead should read back `score_pair` on the 100 frozen reply assessments, TypeSafe payload terms, and both providers in the shared durable $12 gate. Keep production mock until the authorized deployment route is enabled, and do not begin frozen final evaluation until Sebastian's explicit start signal and all preflight gates are green.

## AI lane — 2026-09-27 (parallel development before final run; merge freeze)

### Completed (verified)

- Read handoff 11 in full and kept the merge freeze: work is on a new AI feature branch; no main merge or frozen held-out access occurred. PR #34 had already merged as the pinned `07bccdc` main commit; this branch follows it. PR #36 is open, targets main and passed all four CI checks without merging.
- Measured 20 synthetic no-fault dev conversations through the real local ASGI P path, including parallel Jev risk calls, Gemini phrasing and one forced no-network Gemini failure followed by a valid Grok fallback. Turn p50/p95 **1.782/4.354 s**, case-sum p50/p95 **2.002/8.126 s**, known per-call cost **$0.032765**, conservative cap charge **$0.052947/$0.50**. Full aggregate and limits: [live dev path study](../ml/live-dev-path-study.md).
- Compared templates with grounded LLM phrasing on **30 assessable dev conversations** (38 attempted, eight fault-trigger misses). Four replies changed; no grounding catch in four eligible phrase calls. Both Sonnet and Jev scored clarity/empathy; the aggregate score, marginal latency and cost are in the study. All 38 attempts charged **$0.166451/$0.50** from per-call costs/reserves, with no held-out access.
- Sonnet model-reviewed **17/17 active AI-lane pt-BR template and prompt-example strings** using only an explicit synthetic-string payload. Accepted three wording improvements in `agent/nlg` and `agent/ai`; [before/after log](../ml/pt-review.md) is labeled model-reviewed. Valid call cost **$0.044504**. An extra-scope lead-owned review returned two truncated responses; its $0.255 local reserve plus the valid call stayed below the separate $0.30 ceiling. No more Portuguese-review spend occurred.
- `make checks` passed six hooks, strict mypy, file/secrets policy, compilation, **163 tests passed / 12 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interface and policy catalog checks. No organizer rows, credentials, model thinking, or row-level output were staged.

### Done but not verified

- The local ASGI timing excludes container/network and production database overhead. The dev wording labels and pt-BR naturalness lack human review; only four LLM drafts changed the final reply, so judge-score differences are exploratory. The 34 lead-owned pt-BR strings were not successfully model-reviewed after Sonnet truncation. The final held-out results remain pending Sebastian's start/completion signal.

### Next / blocked

- Open and keep this AI-lane PR unmerged until Sebastian announces the final run is finished. The lead can then merge it after review. No further paid development run is planned under these caps; a complete second-vendor review of lead-owned strings would need a separate cost authorization and coordinated lead-lane edits.

## Access and continuation

Restricted web: https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io/
Use `demo.es.mx` or `demo.pt.br` for the three-surface workspace; `demo.es.co` and `demo.es.ar` are customer-only. Retrieve `demo-password` from the authenticated Key Vault portal; never paste it into chat, Git or logs. OTP is simulated. Re-login after the identity-source migration; prior fixture sessions do not grant organizer access.

For later sessions, paste: **Continue from docs/status/progress-log.md. Next layer: final evaluation after Sebastian's explicit go. Same rules.**
