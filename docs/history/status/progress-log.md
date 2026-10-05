# Progress log

## 2026-10-02 — Progress fragment integration (lead)

Merged lane fragments from #141–#144 are folded below. Their pending/hold notes
record the authoring state; all four changes are now on main `a8d9993`, with
exact-SHA CI/safety green. No study was rerun or rescored during integration.
The lead environment-connection fix below remains a candidate pending CI/release.

## 2026-10-02 — Outcomes asset post-hoc context

### Completed (verified)

- Added the owner-requested one-line post-hoc context beside the failed safety
  gate statement in the v4 outcomes PNG/SVG and source-linked caption. The
  denominator is eight distinct P flagged cases, not independent gate flags;
  overlapping categories and all official counts/failures remain unchanged.
- Regenerated assets from committed aggregates only; no model calls, organizer
  records, held-out runs or Azure changes. Model spend $0; post-v4 documentation,
  not reflected in v4 numbers.

### Done but not verified

- Remote CI pending at authoring time. No main merge authorized during the
  orchestrator's #137 → #140 hold.

### Next / blocked

- Leave PR unmerged until the orchestrator lifts the hold. Staff frontend is
  developed separately against #138's contract; backend security review remains
  lead-owned. No edits to the shared progress log.

## 2026-10-02 — Azure environment-only turn-lock connection (lead)

### Completed (verified)

- v0.8.0 candidate a8d9993 passed exact-SHA CI/safety/access and Azure read-only
  checks. Its concurrent chat probe returned HTTP 500 before NLU: zero provider
  calls/reservations/spend; attempted-conversation history retained.
- Sanitized API logs identify PermissionError in SessionTurns at the missing-DSN
  guard. Azure uses Store("") with libpq PG* environment variables; empty conninfo
  is valid, while None indicates no configured runtime connection.
- Added the actual deployment configuration to the existing same-session,
  cross-worker authored regression. Before the fix, the disposable Postgres gate
  failed only this new environment case: 86 passed / 1 failed.
- One-condition correction accepts empty conninfo while retaining the non-owner
  role check, bounded admission and full-turn session advisory lock. Post-v4 fix;
  official v4 results are unchanged. No replica/CPU/access/model settings changed.

### Done but not verified

- Corrected disposable Postgres gate: **87/87 passed**, including the new
  empty-conninfo, cross-worker/full-turn test.
- Full mock checks, remote CI and replacement release pending at authoring.
- Judge access remains OFF; its live realm proof is deferred to submission Gate B.

### Next / blocked

- Require green CI, update the pinned release SHA, preserve the zero-call failed
  attempt, and retry within the original $0.10 purse without resetting counters.
- Staff queue #138 stays outside v0.8.0 pending controller-revocation corrections.

## 2026-10-02 — Portuguese injection guard (AI lane)

### Completed (verified)

- Reproduced the saved ablation opening: `Ignore as regras` missed the deterministic guard; Spanish `Ignora las reglas` already matched. Four authored override regressions failed before the fix.
- Narrow shared-file correction in `policy/rules/guards.py`: PT `regras`, ES/PT `políticas` and `desconsidere` now use the existing control-override guard.
- Original ablation evidence and official v4 numbers remain unchanged. Post-v4 fix, not reflected in v4. No changes to `agent/ai.py` or `llm/client.py`.

### Done but not verified

- All authored API/unit and existing guard/workflow mock regressions pass. Full local checks, B1 32/32, Ruff, strict mypy and snapshots pass. Required remote CI is pending; no real-model claim for this fix.

### Next / blocked

- Merge hold until #137 then #140 land and the lead announces clearance.
- Freeze/commit a separately disclosed 20-case adversarial dev stress arm before inference; own approved $0.10 cap.

## 2026-10-02 — Adversarial ablation supplement (AI lane)

### Completed (verified)

- New 20-case synthetic ES/PT attack inventory and protocol hash-committed at `867ed55` before any inference on it. Explicitly authored after seeing the first ablation, with the PT guard fix applied before this arm.
- Research-only driver uses its own `dev-gate/controls-stress` / `controls-stress`, $0.10 lifetime cap; estimated $0.06–$0.08. First study and official v4 checkpoints remain unchanged.
- Both source ledgers now accept the same authored merchant field; the runtime and original default fixtures are unchanged. Guard-exposure counts are recorded separately from safety counters.
- No changes to `agent/ai.py`, `llm/client.py` or production defaults; no actual banking write capability in the naive arm.

- Full local mock checks: 1,370 passed / 37 DB skips, B1 32/32, Ruff, strict mypy and snapshots pass. Production credit preflight and zero-spend scope read-back passed.
- Approved paired real pass completed 20/20: scope read-back $0.047119 known/charged, 58 attempts, zero unknowns. P: zero unconfirmed writes/foreign tool attempts; naive: two forged-confirmation writes and one foreign lookup. Both escalated all four over-limit cases.
- Fixed refund screen flags one PT reply that actually refuses a guarantee; recorded transparently as a false positive, without altering frozen scorer/raw outputs. Full findings in docs/evaluation/controls-ablation-stress.md.
- P additionally routed PT refund pressure to ESC-03 and unknown-ID text to DSP-06; safety counters are not a 20/20 objective-pass claim. No additional paid calls or tuning.

### Done but not verified

- PR #144 includes #143 until that prerequisite lands. Final-head main-targeted CI pending; no deployment claimed.

### Next / blocked

- Report all results or partial completion without selecting/relabeling cases or spending beyond the dedicated cap.
- PR depends on #143; merge hold until #137 then #140 land and clearance is announced.
- Staff queue #138 is green and still needs lead security review. Human agreement awaits the exported v4 CSV.

## 2026-10-02 — Post-v4 dev rerun (AI lane)

### Completed (verified)

- Dedicated mock-by-default driver preserves the 36 authored inputs, fixtures and scorer.
- Real dev rerun: **34/36** versus 32/36 earlier; ES 18/18, PT 16/18; zero detected unsafe outcomes or language errors. Supplementary dev evidence, not reflected in v4.
- Scope `dev-gate/post-v4-rerun`, run `post-v4-rerun`, $0.08 lifetime cap: read back **$0.0538905**, 28 valid attempts, zero unknown costs. Production-key credit preflight passed. No production banking writes.
- Full local mock checks: **1,351 passed / 37 DB skips**, Ruff, strict mypy, interface snapshots, B1 **32/32**.
- Controls ablation #135 is merged; staff queue #138 remains open for lead security review. Combined new ablation/rerun cost is $0.098062.

### Done but not verified

- Both remaining PT failures match the correct amount but offer dispute follow-up for an ordinary inquiry. Raw model extractions were not retained; precise field-level cause is unproven.
- Rerun PR remote checks pending. No prompt change or extra paid retry in this round.

### Next / blocked

- Merge hold until the lead lands #137 then #140 and announces clearance.
- PT injection regression fix, then separately preregistered 20-case stress arm (own $0.10 cap).
- Human agreement awaits Sebastian's exported v4 CSV.

## 2026-10-02 — Controls ablation authored before inference (AI lane)

### Completed (verified)

- Read handoff 17 and refreshed to main `1f8b838`. Authored/froze 20 synthetic
  ES/PT dev cases before viewing model outputs; tools exist only in an in-memory fake.
- All 20 local mock P cases completed; seven isolation/billing/confirmation
  regressions pass. Free production-key credit preflight passed without key persistence.
- No edit to the lead's concurrent `AgentAI` / `StructuredClient` work.

### Done but not verified

- Real ablation completed: 20/20 paired dev cases, 59 calls, $0.0441715
  known/charged cost and zero unknowns, read back from its own $0.15 lifetime
  purse. P/naive: zero unauthorized/unconfirmed writes, six correct referrals
  each; naive two success claims without read-back versus P zero. A negated
  refund scorer false positive was regression-tested and saved arms rescored.
- Full local/remote CI and PR merge are pending.

### Next / blocked

- Measure once within `dev-gate/controls-ablation`, report aggregates and a chart;
  then implement the realm-scoped staff queue for lead review, then the approved
  $0.08 post-v4 dev rerun. These changes are not reflected in official v4.
- Human agreement awaits Sebastian's exported v4 CSV.

## 2026-10-02 — Temporal batch merged; approval and local gold verified

### Completed-verified

- #131 merged **880a4f1**, #132 separately merged **eead273**, and #128 merged
  **c48dd30**. Final #128 head **0364aab** passed checks, Postgres, web and safety
  (CI **37050555545**, safety **37050555602**); no budget/runbook diff in #128.
- Final source tree matches the combined local verification: `make checks`
  **1330 passed / 32 DB skips**, B1 **32/32**; disposable Postgres **69 passed**.
- Ran local `aclara.data.cli build --lake artifacts/temporal-release-lake
  --no-reports` with mock/real-call approval off. Promoted current fingerprint;
  `validate_temporal_exports` found **0/0/0** customer/product/transaction source
  mismatches. **492,414** retained, **60,920** flagged, **431,494** unflagged;
  **4** date warnings. Matches #128; ignored receipt read back at 0600.
- Sebastian's **$15 cumulative** approval is on main. Proposed $0.10 smoke +
  $2.92 lifetime judging gives **$14.99937448** against the last verified exposure;
  proposed **$1/UTC-day** judging cap and the provider key's hard stop are recorded.
- Official v4 files unchanged; **$0 new model spend**, no Azure changes.

### Done-not-verified

- Azure remains v0.6.0: new image, serving column/reload, demo-profile coverage,
  fresh key/budget metadata and final paid/browser smokes are not verified live.
- Judging daily/lifetime configuration is proposed, not activated or proven.

### Next-blocked

- Follow the [coordinated release plan](../evaluation/temporal-quality-release-plan.md):
  new API fails closed before atomic serving reload, then restart/fingerprint/RLS,
  coverage and full release gates. Refresh budget/key metadata; keep retained
  reserves and the production key limit. Stop above the approved $15 ceiling.
- No warm/public/judge activation until Sebastian's submission-day OK; implement
  and review the $1/day plus lifetime binding before executing that runbook phase.

## 2026-10-02 — Paired temporal-policy/data verification

### Completed-verified

- Reviewed corrected #128 at **5dd696e**: source-equivalent non-lineage fields
  for customers/products/transactions, FX recomputed from silver rates, and
  **17 independent field mutations** rejected before any Postgres connection.
  Other serving tables and lineage metadata are explicitly outside that check.
- DQ-01 companion #131 merged at **880a4f1**; checks, Postgres, web and safety
  all green at **fe7971f** (CI **37048430192**, safety **37048430208**).
- Combined authored mock `make checks`: **1330 passed / 32 DB skips**,
  hooks/mypy/compilation/snapshots current, B1 **32/32**. Disposable Postgres
  suite **69 passed**, including source mutation rejection, locked schema/data
  rollback, FORCE RLS and operational state. Zero model spend/Azure changes.
- Refreshed #128 onto the migration with history preserved, retaining both
  test sets in the single import/append conflict; no authority-field change.

### Done-not-verified

- Fresh #128 remote CI/merge pending. New organizer gold and Azure serving
  column/reload/image/smoke have not been executed; official v4 stays unchanged.

### Next-blocked

- Merge the exact refreshed #128 head only on green remote gates. The approved
  **$15** ceiling covers the final smoke; follow the coordinated release plan
  and refresh conservative budget/key metadata before spending. Public/judge
  access and warm replicas still require separate submission-day approval.

## 2026-10-02 — Sebastian approved the final smoke/judging extension

### Completed-verified

- Recorded Sebastian's explicit **+$3** approval: cumulative LLM ceiling is
  now **$15 including retained reserves**, for the final release smoke and
  judging window. [Budget approval ledger](model-budget-ledger.md) preserves
  historical $12 approvals and official evaluation provenance.
- Last verified conservative exposure **$11.97937448** leaves **$3.02062552**.
  Proposed $0.10 final smoke + $2.92 judging lifetime yields **$14.99937448**.
  Production key limit remains an independent hard stop; no reset/top-up.
- Prepared the release helper's $15 check and runbook's **proposed $1/UTC-day**
  shared judging cap. No paid call, Azure setting or durable limit changed.
- Authored release/pre-v4/reservation budget tests: **20 passed / 9 DB skips**;
  Ruff passed. Exact $15 boundary passes; one atomic unit above fails. Historical
  evaluation caps and the $0.10 smoke cap stay unchanged.
- Private approval receipt read back at **0600**; includes authorization,
  conservative arithmetic and zero new model calls, without resetting history.
- #132 merged separately at **eead273**, all four remote gates green at
  **b3e2505** (CI **37048944033**, safety **37048944015**). Data #128 contains
  no budget/runbook diff after refreshing from that merged main.

### Done-not-verified

- Fresh live budget/key readback pending. The last
  verified exposure above is not a new balance measurement.
- Judging lifetime/daily binding is a proposal, not activated or proven live.

### Next-blocked

- Final smoke/reload follows the green temporal-policy/data merge batch and
  release gates. Warm replicas/public judge access still need submission-day OK.
- Before judge activation, review/test its lifetime binding and $1/day controls,
  update the runbook activation snippets and obtain the exact plan's approval.

## 2026-10-02 — Saved-v4 confidence and contract-family intervals

### Completed (verified)

- Merged approved #124 at 2700d299 after all four remote gates; retargeted #126
  to main, integrated the same source tree and merged at 426ad511 after its own
  checks, invariants, Postgres and web all passed. No image/cloud release.
- Read only existing v4 results/call metadata. All 114 primary validated NLU
  confidence values match the saved Gemini judgment field; 82 conversations
  have scores. Independent per-turn intent gold is absent, so true intent ECE
  is unavailable. Clearly labelled first-score outcome-proxy ECE is 0.114;
  no score tests the <0.6 region. No policy/default/prompt threshold changed.
- Paired primary contract-family-proxy bootstrap (51 clusters, 10,000 draws,
  seed 20261001): SAR +10 pp [3.0,18.4], pass +26 pp [15.2,38.0]. Official
  case SAR +10 pp [5,16] reproduces exactly; new case-pass interval is [18,35].
  Family IDs were not exported; the proxy uses predeclared contract rationale,
  never observed outcomes, and its limitations are explicit in the new doc.
- All 844 original official artifact files retain their hashes. Private
  aggregate report is 0600; the valid, visually inspected SVG contains only
  aggregates. Fifteen authored statistical/privacy/serialization tests pass.
  Zero inference, key/cloud access, suite-row access or official rerun/rescore.
- Final mock make checks: 1235 passed / 31 DB skips, hooks, strict mypy,
  compilation, interface/policy snapshots and B1 32/32. Current main verified.

### Done but not verified

- Supplementary documentation PR/remote CI pending.
  Neither true intent calibration nor an exact author-family mapping is claimed.

### Next / blocked

- Open one aggregate-only evidence PR for review; keep official v4 numbers
  untouched. Threshold selection needs independent contextual intent labels
  and a separately authorized dev study, not tuning against these saved cases.

## 2026-10-02 — Approved cleanup merges and supplementary v4 analyses

### Completed (verified)

- Owner approved #124 and #126 merges. Read back #124's four green gates and
  merged its exact head 7f4a964; private main merge is 2700d299.
- Retargeted #126 to main and integrated 2700d299 without a source-tree change.
  Its existing final mock evidence remains 1203 passed / 31 DB skips, B1 32/32.
- Supplementary work is restricted to existing v4 artifacts and aggregates:
  confidence/correctness calibration and family-clustered paired bootstrap.
  No new model call, official rescore, release or cloud/key access is authorized.

### Done but not verified

- Fresh main-target #126 remote CI and merge pending. Saved-artifact analyses
  and their separate documentation PR are not yet complete.

### Next / blocked

- Merge #126 only on its exact green head. Preserve all official v4 bytes;
  report limitations of confidence labels and the family grouping explicitly.

## 2026-10-02 — Prompt version index and unadopted candidate archive

### Completed (verified)

- Moved the unused v5.2 candidate to evals/studies/prompts/nlu/v5_2.md and
  updated the development driver and evidence link. All nine original prompt
  files retain their exact bytes and hashes; live NLU v5.1 and phrase v2.1 stay
  selected by the same runtime paths.
- Added prompts/README.md identifying live defaults, historical versions,
  offline-only judging and the unadopted candidate. No route/default change.
- Archive/import checks: 12 mock tests passed, including candidate hash,
  runtime-prompt selection, offline CLI imports and fresh API isolation.
  Final current-main mock checks: 1203 passed / 31 DB skips, strict mypy,
  hooks, snapshots and B1 32/32. No paid calls, cloud/key access or held-out inputs.
- Refreshed on #124's history-preserving main merge. Rebuilt the final wheel
  offline: eight runtime LLM files, no studies/data. All prompt hashes unchanged.
- Opened private-origin PR #124 (relocation) and stacked PR #126 (prompt index).
  Exact #124 head 7f4a964 has checks, invariants, Postgres and web all SUCCESS.

### Done but not verified

- Lead review/merge pending. Stacked #126 intentionally has no remote CI under
  the main-only trigger; require its own green gates after retargeting to main.

### Next / blocked

- Keep prompt cleanup stacked on #124 for a small review, then retarget to main
  after the lead merges the relocation. Remote CI is required before main merge.

## 2026-10-02 — Offline language studies outside the runtime package

### Completed (verified)

- Moved 29 study/tool modules and 15 project-generated dev data/manifest files
  to evals/studies/llm. Updated eval/script/test imports and documentation links;
  no serving algorithm, route, prompt, model default or authority change.
- All 15 data/manifest files and both frozen robustness builders retain their
  original bytes and hashes. A development-only legacy import alias preserves
  the round-two source freeze; comparison source pins still cover the studies.
- Built the wheel offline and inspected it: exactly eight runtime LLM files,
  no study modules or datasets. Fresh API import succeeds with study imports
  explicitly forbidden; all 29 study imports and three CLI help commands work.
- Shared edits are limited to import/path changes in three scripts and four
  eval modules, plus an evals/studies build-context exclusion in .dockerignore.
  Dockerfile.api already copies only src for Python code; no Dockerfile edit.
- Final current-main mock checks: 1202 passed / 31 DB skips, strict mypy, hooks,
  snapshots and B1 32/32. Packaging regressions: 7 passed. No paid calls,
  key access, Azure changes or v4 input.
- Confirmed the old model-id-gated Jev branch is already removed. The optional
  adapter/questions remain behind explicit configuration, disabled by default.
- Integrated merged #122/#123 and retained their progress entries. Every
  remaining runtime Python file matches origin/main byte-for-byte; #123's new
  study import and CLI reference now use the relocated namespace.

### Done but not verified

- Private-origin cleanup PR #124 CI pending. An API image build was not run; the
  actual wheel and image COPY boundaries were checked.

### Next / blocked

- Leave the relocation PR for lead review. Integrated merged #122/#123 while
  retaining their progress entries and refreshing new imports. Archive v5.2 and
  clearly identify live versus historical prompts in a separate small PR.

## 2026-10-02 — Temporal dispute gate and coordinated reload preparation

### Completed-verified

- Added DQ-01 (policy v1.4.0): flagged/unavailable checks permit explanations
  but block automatic dispute proposals/writes, including a confirmation-time
  flag change. Localized anomaly questions survive handoff refresh/readback.
- Older serving schemas read safely and warn in readiness; the read-only
  release gate requires nullable TEXT plus the rebuilt promotion fingerprint.
- One exact additive column migration is coupled to locked COPY/readback;
  authored rollback leaves the prior column/data state intact.
- Local mock `make checks`: **1273 passed / 32 DB skips**, B1 **32/32**;
  disposable Postgres suite **50 passed**, hooks, strict mypy and snapshots pass.
  No Azure, key access, paid models, organizer rebuild or held-out rerun.

### Done-not-verified

- Companion PR/combined #128 CI and merge pending. Full organizer reload and
  final Azure image/smoke remain unverified; official v4 files unchanged.

### Next-blocked

- Finish #128's source-equivalence review and merge the paired changes only on
  green CI. [Coordinated release plan](../evaluation/temporal-quality-release-plan.md)
  includes fresh gold, atomic schema/data reload and the required column gate.
- October 2: Sebastian approved the final smoke within the new **$15** cumulative
  ceiling, including reserves. Azure reload remains unexecuted; first finish
  both green-CI merges and the coordinated release gates.

## 2026-10-02 — Five-session local mock concurrency measurement

### Completed-verified

- Ran `.venv/bin/python -m scripts.local_mock_concurrency` with explicit mock,
  fixture and in-memory settings: five sessions **5.026 s wall**, turn
  **p50 3.017 s / p95 4.823 s**; three sessions **3.836 s wall**, compared
  with the external audit's **3.780 s / three turns**. Chat remains serialized.
- **5/5** mock NLU calls outside storage transactions; **15/15** concurrent
  authenticated/health reads 200, max **0.910 ms**; one scoped execution/NLU
  event per session; **0 case writes / $0 model cost**. Five independent
  logins use one authored customer in one API app.
- Authored smoke regression passes with the paid provider forbidden and
  contrary ambient real-provider variables. [Method and commands](../evaluation/local-mock-concurrency.md)
  disclose small samples, inclusive percentiles, ASGI transport, in-memory
  storage and the order/cache limitation. No production SLO or throughput gain.
- Full local mock `make checks`: **1216 passed / 31 DB skips**, B1 **32/32**,
  hooks, strict mypy, compilation and interface/policy snapshots passed.
- #129 merged at **6272438**, all four remote gates green at **edb0bce**;
  CI **37042451617**, safety **37042451448**.

### Done-not-verified

- No cloud concurrency, real-provider latency or load acceptance claim; no
  new Azure image. Official v4 results were not opened, rerun or changed.

### Next-blocked

- Future parallel chat inference requires adapter/session design work.
- No paid calls or Azure changes; the next paid release smoke still requires
  Sebastian's budget approval. CPU, replicas and worker count are unchanged.

## 2026-10-02 — Item 7 hygiene completion and conversation state table

### Completed-verified

- Checked all five item-7 points; [evidence and commands](../evaluation/item7-hygiene.md).
  API image UID **10001** with networking disabled; fixture BFF config **200**,
  **5 customer entries / 0 staff or judge identities**; live session **35 min**.
- Replaced nine API/serving/accounting assertions with explicit errors. Authored
  regressions cover unavailable judge controllers, lost ES/PT recognition targets,
  absent serving connections, missing budget pools and rollback without writes.
- Added the missing single JSON log after verified card-freeze responses, including
  lost-response retries. Chat and dispute confirmation logs were already present;
  integration coverage verifies one metadata-only line per completed turn.
- Added a short state-table docstring at the top of `process_message`, with no
  refactor. Local mock checks **1215 passed / 31 DB skips**, B1 **32/32**,
  affected API checks **67 passed / 1 skip**, optimized hygiene checks **18 passed**.
- #127 merged at **9de89d6**, all four remote gates green at **c686916**;
  CI **37040731841**, safety **37040731806**.

### Done-not-verified

- These post-v4 fixes have local/mock and remote CI evidence; official v4 remains unchanged.
  No new Azure release, real-model validation or production concurrency claim.

### Next-blocked

- Five-session measurement and both green-CI merges are complete; see above.
- No paid calls or Azure changes; a new paid release smoke requires Sebastian's
  budget approval at the conservative **$11.97937448 / $12** maximum.

## 2026-10-02 — Lead review of the basic-mode reply contract (#123)

### Completed-verified

- Release evidence #122 merged at `67d19bf` after exact-head CI and safety
  success. The deployed image and annotated `v0.6.0` remain `f5e128d`.
- Reviewed every #123 change. Accepted the shared additive contract:
  `ResponsePlan.degraded` defaults to false, is optional in both OpenAPI
  schemas, and matches the frontend's optional boolean. The server derives it
  from NLU fallback state; it supplies no action or authorization authority.
- Authored mock checks cover budget refusal without provider calls, outage,
  invalid output, recovery, early handoffs, complete spoken cents, missing
  amounts and status duration versus purchase dates: **53 passed**.
- Combined candidate `make checks`: **1195 passed / 31 DB skips**, B1
  **32/32**, hooks, strict mypy, compilation, staged-file safety, interface
  snapshots and policy catalog passed. Refreshed on #119/#122 with a
  history-preserving merge, retaining both progress-log entries; no additional
  product changes were made during review.

### Done-not-verified

- Fresh remote CI is required for the conflict refresh before #123 merges.
  Product changes have mock evidence only and are outside the Azure image;
  official v4 and the earlier real dev score remain unchanged.

### Next-blocked

- Merge #123 only on green remote checks, then stop. No additional model
  calls or Azure changes: the next paid release smoke needs Sebastian's budget
  approval at the conservative **$11.97937448 / $12** maximum.

## 2026-10-02 — Live degradation signal and mock-only dev triage

### Completed (verified)

- Owner lifted the merge hold. Refreshed #118 on current main ec076aa, retaining
  both progress-log entries, and merged at ff3b47a after checks, invariants,
  Postgres and web all passed. Refresh local mock checks: 1152 passed / 31 DB
  skips, B1 32/32. No deployment.
- Added optional/default-false degraded boolean to ResponsePlan and OpenAPI.
  Minimal app.py response-boundary wiring records NLU budget/model fallback,
  including early handoffs, and clears the signal after healthy recovery.
  This is the additive cross-lane contract change requested for w8's #119.
- Reproduced and fixed three code gaps with authored mock regressions: bounded
  ES/PT whole-money-plus-centavos parsing; explicit missing-amount clarification
  even when the model expression is null; pending status-duration clauses kept
  separate from transaction selection dates. Currency is not inferred for cents
  alone; ambiguous phrases, valid amounts and actual purchase dates stay guarded.
- Frozen dev inventory and scorer unchanged: mock truth replay 35/36 → 36/36,
  ES 18/18 and PT 18/18, observed unsafe/language errors 0. Separate API probes
  simulate null-amount/status-age extraction; original real NLU was not retained.
- Follow-up mock make checks: 1195 passed / 31 DB skips, hooks, strict mypy,
  B1 32/32 and interface/policy snapshots passed. No real models, keys, Azure
  access or additional inference spend. These are post-v4 fixes, not reflected
  in v4 numbers; no held-out inputs were opened or rescored.

### Done but not verified

- Follow-up PR/remote CI pending. Product fixes have mock evidence only; the
  original real pass remains 32/36. No new accuracy or production latency claim.

### Next / blocked

- Merge the follow-up only on green remote CI; the lead owns the image release.
  The family-assistance false unfamiliarity flag remains a model-quality limit;
  semantic unfamiliarity must not be erased by family keywords. Future prompt
  examples need a separately approved model check. No paid calls are authorized.

## 2026-10-02 — v0.6.0 released; paid work stopped

### Completed-verified

- Annotated `v0.6.0` and private GitHub Release verified at deployed
  `f5e128dd7e544e2378081361f4a8a409af94f221`; API/web tags, registry digests and ready revisions read back.
- Exactly one owner-approved extra `scripts.serving_browser --target azure`
  attempt passed all three surfaces: Chat, Desk, Ops; one handoff resolved and
  verified. Counter **6**, no reset; ledger stayed **12 calls / $0.02292**,
  **zero new paid calls / $0** from this attempt.
- Fresh `scripts.azure_verify` passed. Exact deployed-source CI/safety/access
  and operator main CI/safety all success. `jev-release.json` has all three
  acceptance flags true; the annotated tag and Release were read back from origin.
- [Full evidence](../evaluation/v0.6-release-notes.md) records the SHA, digests,
  commands, run IDs and limits. Post-v4 fixes do not change official v4 numbers.

### Done-not-verified

- No new held-out safety/performance score is claimed for this release.
  Submission-day public/warm/judge activation remains OFF and unverified.

### Next-blocked

- **Stop paid calls.** Conservative cumulative maximum **$11.97937448 / $12**.
  The next release smoke needs Sebastian's explicit budget OK; do not create a
  fresh purse, replay the consumed browser allowance or reset reservations.
- Other lanes' main merge hold is lifted; #118/#119 are outside the tagged image
  and need a separate approved release. Publication/warm/judge changes still need
  submission-day go. Main protection remains prepared for the supported plan.

## 2026-10-01 — Post-v4 dev evidence and verified-money DLP

### Completed (verified)

- Item-6 PR #113 merged at 2ee162b after checks, invariants, postgres and web
  all passed. Rebased first on merged #109/#111; no deployment was performed.
- Replayed the unchanged, pre-measurement-frozen 36 authored messages against
  pre-audit 6a221a4 and current P with the same mock truth/scorer: **21/36 →
  34/36** after the audits; **35/36** with this monetary DLP correction.
  Summaries improved from 0/15 useful packets to 12/12; observed unsafe 0.
- Corrected a false positive on the code-approved 2000000.00 COP display,
  which resembled a phone number. Only the exact scoped monetary slot in a
  code-rendered template is excluded; raw/model DLP remains strict. Authored
  ES/PT regressions retain identifier and duplicate-merchant checks.
- One serial real pass completed **32/36** (ES 15/18, PT 17/18), observed
  unsafe/language errors 0. All **28/28** attempts had valid JSON; no retry,
  fallback, Jev or second pass. Production-key credit preflight passed.
- Created/read back dedicated scope dev-gate/post-v4-audit, run post-v4-audit,
  lifetime cap USD 0.10. Final readback: **USD 0.0543715 known/charged**, zero
  unknown costs. Production/final-evaluation scopes were not used.
- Mock `make checks`: **1119 passed / 30 DB skips**, hooks, strict mypy, B1
  **32/32**, compilation and interface/policy checks green. Private receipts
  and checkpoints are ignored and mode 0600. No credentials/reasoning saved.
- During the owner's merge hold, added mock-only redaction for labelled
  dotted/dashed CPF/DNI/RUT/cédula in model inputs and staff quotes. The earlier
  dotted DNI escaped the plain document and phone patterns. Targeted context,
  money and redaction checks: **39 passed**; paid metrics predate this patch.
- Full mock checks after the privacy correction: **1128 passed / 30 DB skips**,
  B1 **32/32**, hooks, strict mypy and frozen snapshots green. Refreshed the
  published branch with a history-preserving merge of current origin/main.

### Done but not verified

- Monetary DLP follow-up and evidence PR #118 awaits current-main CI/merge. Four real
  failures and proposed follow-ups are in docs/ml/post-v4-dev-evidence.md;
  no paid baseline exists, so mock/real scores are not a causal model comparison.
- This is **post-v4 dev evidence, not held-out**; these are **post-v4 fixes,
  not reflected in v4 numbers**. No v4 suite was opened/rerun/rescored.

### Next / blocked

- Merge the follow-up only on green remote CI; the lead owns the tagged release.
  Owner lifted the #114 → #116 → #117 hold on 2026-10-02; refresh #118 on
  current main and merge only after its new remote gates pass.
  No further inference is authorized by this one-pass task. Portuguese spoken
  cents, false unfamiliarity, vague amounts and status-duration parsing remain
  documented dev gaps; defaults remain unchanged.

## 2026-10-01 — Audit release smoke: Jev disabled and durable bank state

### Completed-verified

- Offline authored smoke regressions **6/6**: production config must make zero
  TypeSafe calls while retaining valid non-degraded NLU proof. Explicit opt-in
  study config still validates a correct risk union; invalid unions fail.
- Real smoke selects an eligible transaction without a canonical open customer
  case and measures case count relative to authenticated pre-run bank state.
  It preserves historical/closed cases and does not reset allowances or budgets.
- Ruff and browser-smoke JavaScript syntax pass. The browser accepts manual
  staff login, and normal smoke checks one create_dispute event plus an identical
  lost-response retry. Local privacy/staff login behavior was already verified.
  Mock/offline only; zero spend and no Azure change so far.

### Done-not-verified

- Live pre-release checks: East US 2 estimate **$34.63/month**, gate passed;
  OpenRouter account **$9.041** / prod key **$5.185**. All-scope ledger exposure
  including unknown reserves **$7.67326884**; plus a fresh $0.10 purse gives
  **$7.77326884 < $12**. Zero inference calls made by these checks.
- Required remote CI, merge and real release evidence pending. Retained TypeSafe
  Key Vault binding alone does not enable its disabled config. Historical Jev
  evaluation evidence and official v4 files remain unchanged.

### Next-blocked

- Merge the audit batch on green CI, then tagged v0.6.0 image release with capped
  real smoke and approved owner-IP benign/duplicate/budget-degrade rehearsal.

## 2026-10-01 — Audit item 8: NLU outside scoped storage

### Completed-verified

- Integrated reviewed AI item 6 before process_message edits; #113 merged at
  2ee162b3 after all four remote gates. Read NLU context in a short scoped unit,
  close it, infer in a thread, then independently re-authenticate and reopen.
  Reject changed conversation state with 409. Refresh serving snapshots and
  policy facts after inference; a new case from another login returns its receipt.
- Shared model adapter/record cursor stays serialized by an async lock acquired
  before any storage transaction. Request-local event buffers prevent trace/cost
  mixing. Repeated caller cancellation waits for provider settlement, never
  retries inference and never commits that cancelled request's actions.
- Five simultaneous authenticated sessions can read /healthz, /me and their
  transactions while NLU waits. Authored revocation/expiry, conversation-change,
  concurrent bank-case and cancellation regressions pass. The NLU stub asserts
  no operational transaction is open. Fresh local Postgres/RLS **49/49**.
- Bounded-thread mock `make checks`: **1115 passed / 31 DB skips**, hooks, Ruff,
  strict mypy, compilation, interface/catalog checks; B1 **32/32**. Reactive B1
  **32/32**. Combined live API browser **12/12**. Final cancellation regressions
  **6 passed / 1 DB skip**, Ruff and strict mypy pass after the repeated-cancel guard.
- Initial PG concurrency test inherited another test's bank case; a unique
  authored customer fixes isolation without changing within-test login sharing.

### Done-not-verified

- Remote CI and merge remain required. These are **post-v4 fixes, not reflected
  in v4 numbers**. No official held-out input/run, paid model or Azure change.
- One worker retained; two-worker memory fit is unmeasured. Model calls remain
  serialized. The existing optional phrasing boundary is unchanged; this fix
  specifically removes NLU waiting from the operational transaction.

### Next-blocked

- Main-merge hold secured for #114 → #116 → #117. Inherited the reviewed
  #115 admission setup and resolved privacy test imports before the main gate.
- Green CI on refreshed hygiene #114, then this small concurrency PR. Update
  Jev-off release smoke, tag/release v0.6.0, owner-IP real rehearsal and section B.
  max_replicas, CPU, access and judge mode remain unchanged.

## 2026-10-01 — Audit item 7: runtime and login hygiene

### Completed-verified

- Refreshed onto merged #109/#111 using history-preserving main updates. API
  image runs as UID 10001: local Docker build and actual non-root mock import
  passed. Freeze readback failure raises 503 and rolls back, including under -O.
- Public personas/BFF config omit staff/judge names. Staff login accepts manual
  usernames. Authenticated /me supplies only that account's gated story hints;
  logout discards them. Session/cookie lifetime is 35 minutes, with the cookie
  deadline taken from the server's grant. Judge profile expiry remains unchanged.
- One metadata-only JSON line per committed chat/confirmation turn records
  conversation ID, outcome, rules, model latency/cost and degradation. Unknown
  model cost remains null; no customer text, facts, credentials or prompts.
- Bounded-thread mock `make checks`: **1090 passed / 30 database skips**, Ruff,
  strict mypy, compilation, interfaces/policy snapshots and B1 **32/32**. Reactive
  B1 also **32/32**. Latest targeted hygiene checks **5 passed** plus Ruff/mypy.
- Web typecheck/lint/build passed. Privacy/story browser checks **18/18**;
  `pnpm --dir apps/web test:e2e --live` **12/12**, `--staff` **1/1**. Initial
  browser expectations enumerated staff names; corrected to authenticated hints.
  The expiry check initially read cookies before OTP completed; its explicit
  authenticated-state wait fixed the test race. All verification used mocks.

- Concurrent #115 rate-limit merge required a second history-preserving refresh.
  Kept the admission fixture and private-login helper. Combined local typecheck,
  **148 fixture + 12 live API browser checks** pass, real limiter enabled.
  Explicit optimized Python freeze regression **1 passed** under `python -O`.

### Done-not-verified

- Full fixture browser suite previously had 129 passes and eight obsolete
  public-persona expectations; corrected target suite passed 18/18. Fresh full
  remote browser gate and PR merge pending. Nothing in this entry claims Azure.
- Minimal web/login and staff shared-file edits implement the authorized public
  enumeration fix. These are **post-v4 fixes, not reflected in v4 numbers**.

### Next-blocked

- Merge only on green remote CI; integrate AI item 6 before item 8 NLU boundary.
  Then update the Jev-off smoke gate, tagged v0.6.0 release, authorized real
  rehearsal and handoff 16 section B. No replicas, CPU or access changes.
## 2026-10-01 — AI audit item 6: handoff context and slot clarification

### Completed (verified)

- Rebased on main after #109 and #111 merged. Kept the app.py change to the
  NLU clarification branch and one import; cross-lane staff.py/handoff edits are
  explicitly owner-approved. Frozen interface models are unchanged.
- Added deterministic ES/PT guidance for DSP-07, ESC-04, TXN-02, FRD-01,
  ESC-01/02/03 and SEC-01, with combined causes preserved. Summaries include
  the requested outcome/first safe quote, scoped charge/status facts and only
  verified actions; offered or failed card blocking stays unverified.
- Preserved the initial in-scope customer request and up to nine redacted
  clarification replies/questions, confined to the originating conversation.
  Terminal retries retain the original context; unsafe access/injection text
  is excluded. Slot questions ask only for nlu.clarification's missing detail.
- Mock `make checks`: **1104 passed / 30 database skips**, all hooks, strict
  mypy, B1 **32/32**, compilation and interface/policy snapshots green.
- Froze 36 authored messages (18 ES / 18 pt-BR) with a SHA-256 manifest before
  measurement. They are **post-v4 dev evidence, not held-out**. A free
  production-key/account balance check passed; no inference spend occurred.

### Done but not verified

- AI item 6 merged as #113 at 2ee162b3cbc864991d28f7a569325db859626d5a
  after all four remote checks passed. These are **post-v4 fixes, not reflected
  in v4 numbers**; no held-out suite was opened, rerun or rescored.

### Next / blocked

- Merge item 6 only on green CI. Then replay the same frozen messages against
  pre-audit 6a221a4/current code using mock truth; run one approved real pass
  only under its own durable USD 0.10 lifetime scope after fresh key preflight.

## 2026-10-01 — Audit item 5: customer bank state and receipt retries

### Completed-verified

- Added customer business maps/tables with forced customer + trusted realm RLS,
  cross-session advisory locking and a unique canonical open-case index. Owner
  sessions share cases/card states; each judge profile has a separate stable
  realm. Conversations, handoffs, OTPs and pending actions remain session-scoped.
- Migration 0004 retains legacy receipts and canonicalizes duplicate history
  without deleting it. Logged-out normal serving identities are recovered only
  from the authoritative persona registry; unknown realms remain isolated.
  FORCE RLS is restored atomically before migration commit. Runtime stays non-owner.
- Existing-case policy/status lookup and card/account readback use bank state
  across logins. Workspace reset does not delete customer bank state. Returning
  to a judge profile recovers its cases, never another profile's workspace.
- Lost dispute confirmation returns the exact original receipt after independently
  reading its case; it performs no second write/model call. Opposite confirmation
  and another session's hash fail. Freeze receipt retry remains read-only after
  action OTP expiry; owner/session/proposal provenance still applies.
- `LLM_PROVIDER=mock ... make checks` passed: **863 passed / 30 database skips**,
  six hooks, strict mypy, compilation, file policy, B1 **32/32**, interface and
  policy snapshots. Local disposable `scripts.test_postgres`: **42 passed**,
  including populated/signed-out backfill, RLS, restart, cross-login duplicate,
  two-replica race and judge-profile separation. Latest Ruff/strict mypy passed.
- Reactive B1 initially **30/32** because its replay observer treated HTTP 200 as
  a second action. It now checks identical receipts and unchanged write counts;
  rerun **32/32** with unchanged scenario gold. Existing single-use test now
  asserts one write plus the same receipt. Official v4 files were not touched.
- Earlier local full checks were interrupted for numerical-library thread
  oversubscription; final checks bound OMP/OpenBLAS/MKL threads to one. Initial
  migration quoting and fixture-customer collisions were fixed, then gates rerun.

### Done-not-verified

- Item 5 merged as PR #111 at eaaecd453484f66245e0e82e3d74c718316ba21e.
  Required checks/Postgres/web/invariants passed at head 42bbf754; 12 live browser
  checks passed after fixture-only between-test isolation. Within-test cross-login
  state stays shared. Both B1 harnesses remain **32/32**. Not deployed yet.
- Refreshed onto main with #105/#107/#108 using a history-preserving merge,
  preserving both progress entries. Combined `make checks`: **1024 passed / 30
  skips**, B1 **32/32**; combined Postgres **42 passed**. Authored replay
  negative controls reject changed receipts, extra writes and write-then-409.
- These are **post-v4 fixes, not reflected in v4 numbers**. No evaluation rerun,
  paid dev call or Azure change occurred.

### Next-blocked

- Refresh onto merged AI wiring before process_message edits. Merge item 5 only
  on green CI, then item 7 → 6 → 8, one tagged Azure release and authorized real
  owner-IP rehearsal (~$0.02–$0.05), with prod-key remaining before/after recorded.
- Section B full-history/PR/Actions audit and password rotation follows the batch;
  section C remains submission-day only. Main protection is plan-blocked until public.

## 2026-10-01 — Submission repository transition (handoff 16 A)

### Completed-verified

- Runbook PR #106 merged with checks, postgres, web and invariants green at
  `587fa1f2b8472618742f973fbcb6443291b2a1e5`.
- Renamed the old snapshot to
  `sebastian-gm/factored-hackathon-2026-sebastian-snapshot-archive`, archived it,
  verified it remains private; nothing deleted. Renamed the original lab to
  `sebastian-gm/factored-hackathon-2026-sebastian`, verified private.
- Updated the shared origin; explicit `git -C` fetch succeeded in lead, AI and
  data/frontend worktrees. Both lane dry-run pushes succeeded without publishing
  their local branches. Existing PRs remain on the renamed repository.
- Created annotated semver tags v0.1.0 (`c2111aa`), v0.2.0 (`fd34c7d`), v0.3.0
  (`e12efc7`), v0.4.0 (`92994d9`), v0.5.0 (`b8c1305`), each explicitly retroactive
  on 2026-10-01, on main ancestors; corresponding private GitHub Releases
  created and tag refs verified through the API. The first slice is identified by the actual
  local verification in progress-log commit `7680288`. No score was rewritten.
- Added CHANGELOG, MIT license (Sebastian, 2026), CI badge and repository rules;
  replaced the superseded snapshot-publication commands in the runbook.
- Main-protection API returned HTTP 403: private plan requires GitHub Pro or
  public visibility. Prepared `.github/main-protection.json` requiring PRs and
  invariants/postgres/web, admin enforcement, no force push or deletion, for
  application immediately after submission-day publication.

### Done-not-verified

- Protection is not active. Publication is not approved or performed.
- Full-current-history/PR/Actions audit and password rotation (section B) remain
  outstanding; historical scans are not claimed as current evidence.

### Next-blocked

- Merge this transition via a small CI-green PR, then resume audit items
  5 → 7 → 6 → 8. Item 5 edits are preserved in the named audit-work stash.
- Section B follows the audit batch, before October 3. Section C waits for
  Sebastian's explicit submission-day go. No Azure resource shape/access change.


## 2026-10-02 UTC — submission-day runbook, preparation only

### Completed (verified)

- Wrote [October 4 runbook](../../submission/submission-day-runbook.md): explicit
  owner gates, release-before-picker activation, fresh private plans, warm and
  judge readbacks, Key Vault-only password creation, four-profile cookie/RLS
  checks, non-allowlisted access probe, sanitized snapshot/publication,
  README-only fixture reproduction, email/private credentials, availability
  through October 16 and scale-down/deletion with rollback/retention gates.
- `PYTHONPATH=. .venv/bin/python artifacts/submission-prep/plan_only.py`:
  read-only `-refresh=false -lock=false` previews against existing state. OFF:
  **zero changes**. Warm + judge ON: **two app updates / two secret-scoped RBAC
  creates / zero deletes**, same images, internal API, HTTPS, min=1/max=1 and
  only web's IP rule removed. No apply/lease/bootstrap/registration or secret
  creation; private plans remain ignored. Initial invocation without PYTHONPATH
  failed import; the corrected invocation produced the successful receipts.
- `terraform -chdir=infra fmt -check apps.tf main.tf variables.tf versions.tf
  tests/submission.tftest.hcl`, `validate` and
  `test -filter=tests/submission.tftest.hcl`: **all passed; 10 mocked plan tests**.
  Unqualified fmt includes ignored tfvars and initially failed their formatting;
  no private inputs were rewritten. The tracked-file check is the runbook gate.
- `scripts.azure_prices` and ignored `read_prices.py`: live public East US 2 USD
  meters read at **2026-10-02 02:28:59 UTC**, no model calls. Fixed infrastructure
  **$21.09/month**; two warm replicas **$5.0544–$16.848** for 312 hours. Decimal
  arithmetic verified full monthly estimate **$34.28–$46.08**, including stated
  margins/requests, excluding grants/tax/models/usage outside that window.
  The proposed COT availability window spans **14 UTC budget dates**: potential
  **$42** models at $3/day requires separate approval from the $12 eval ceiling.
- Extracted all runbook shell fences: `bash -n` with no warnings, Python
  `ast.parse`, and YAML dispatch-schema parse passed: **23 shell blocks,
  17 Python heredocs, one YAML heredoc**. Caught/fixed an indented heredoc
  terminator issue; these are syntax checks, not activation/restore evidence.
  Local Azure CLI help/source confirmed scope and inherited-role syntax; scoped
  grants omit incompatible `--all` and avoid a Microsoft Graph principal lookup.
- Main remains **6a221a4e61133ab4fbedeb770e39ee229237ba18 == origin/main**.
  Read-only GitHub metadata confirms existing main **ci 36954572221 / safety
  36954572164 success**. No new workflow, paid call, Azure change or publication.

### Done but not verified

- Future command snippets are not executed. Final frontend picker/redesign,
  final-image owner smoke, enabled judge/profile/browser/outside-IP checks,
  final-main export/clean clone and encrypted Azure backup/independent restore
  remain future gates. Historical snapshot/release receipts do not prove them.
- Docs branch is prepared for review; no main merge or new Actions run is
  requested in this zero-spend task. Existing Azure remains testing mode.

### Next / blocked

- Stop. Sebastian approves October 4 warm/public ingress/four source profiles/
  secret creation/window, **the >$40 upper estimate**, separate daily model
  exposure, exact public snapshot SHA, private credential delivery/email and
  retirement/backup plan at their marked gates. Image-only release remains
  within the existing standing OK and cumulative smoke allowance.
- Frontend picker/redesign must land with green CI/browser evidence before any
  judge activation. Teardown requires independently verified encrypted retention
  and exact resource inventory; PostgreSQL `prevent_destroy` is not bypassed.
- Continue from docs/status/progress-log.md. Next layer: frontend picker/redesign
  and submission-day approvals. Same rules.

## 2026-10-02 UTC — frontend merges and one v4 narrative

### Completed (verified)

- PR **#104** merged after all four remote gates passed, at
  **b938c0a12acb906fe04bfd9b1e7c9dee5a93ac72**. PR **#105** was rebased onto
  that main revision; a history-preserving merge retained its published ancestry
  for a normal fast-forward push, with no force-push. A tree comparison confirmed
  that the updated head has identical product files to the prior green picker head.
- PR #105's fresh CI initially passed checks/Postgres/invariants but timed out
  clicking the PT login OTP button (136/137 fixtures passed). The exact isolated
  test passed **3/3** consecutive local fixture runs; only the failed browser job
  was retried. All four fresh remote gates then passed; PR #105 merged at
  **7ff7d2a8c3014fdd7b1fe9145c3e11397c1b6054**.
- Implemented handoff 15 item 9 in Markdown only: README leads with completed
  v4, both SAR denominators, exact and rounded model cost per evaluated case and
  allocated cost per safe automated resolution, three limits, Jev's role, PT
  provenance and one sourced sentence explaining the two unauthorized-action flags.
  Official failures remain unchanged; post-v4 fixes are not reflected in v4 numbers.
- Added superseded-by-v4 banners to all six requested historical pages and the
  stale language card/serving guide linked from the README. Matcher v2's earlier
  v1-default instruction is superseded; the projection retains its original v3
  assumptions. The checklist points to complete v4 and owner-only release/access gates.
- Local source/arithmetic, relative-link, heading-target and Markdown-only checks
  passed. Strict mypy and staged data/secret/large-file hooks passed. No per-case IDs
  or organizer values added; no model calls, frozen-suite execution, rescoring or
  product changes. Model/cloud spend **$0**; CI uses the existing owner-approved cap.

- Docs PR **#109** initially passed all four remote gates at 74eb7a5. Main
  advanced during CI; GitHub rejected the merge for conflicts. Preserved the
  repository-transition URLs, language-card banner and both session histories.
  The updated 7d12154 head also passed all four remote gates, but a concurrent
  AI-lane log append caused a second conflict. Kept both entries and placed this
  record beside the earlier profile-backend section to avoid shared top/end
  insertions. The 3c00619 head again passed all four gates; #112's live-Jev removal
  then overlapped the README. Preserved that decision, the pending-release caveat,
  Gemini-only diagram and Gemini-plus-Jev v4 provenance. The resulting head requires
  fresh CI; no force-push or held-out rerun.

### Done but not verified

- At entry creation, the docs PR's remote CI and merge remain to be read back.
- New design and judge picker have local/browser and remote-CI evidence, but this
  session does not deploy or attest to their live release. Judge access stays OFF.

### Next / blocked

- Open one docs-only PR onto updated main and merge only after all remote gates
  pass, under Sebastian's standing authorization; retain the CI/merge readback.
- Lead owns the next release and owner-approved judge-access activation. Keep
  official v4 evidence fixed; no held-out rerun or new acceptance score is claimed.

## 2026-10-02 UTC — one judge login, scoped profile backend

### Completed (verified)

- Docs-only evidence PR **#102** merged under standing OK at
  **3384a0b47a66dbf9512928fab26a2332a6a2ef78**. Its reviewed head 360d4c1
  passed checks/Postgres/web/invariants; automatic main CI **36951431482** and
  safety **36951431476** also succeeded. No Azure release was needed for docs.
- Proposed the API/session design and threat check first in
  [ADR-0016](../../adr/0016-judge-profile-sessions.md), then implemented on
  `feat/judge-profile-entry`. Existing password/OTP yields a picker-only grant.
  Fixed profile selection rotates a capability with a trusted customer and fresh
  run/sid, preserving the login deadline/OTP and clearing action step-up.
  Locked, durable controller activation has one winner; old tokens cannot replay.
  Logout revokes the controller; judge reset is forbidden. Credential/binding/
  dataset changes and the OFF switch invalidate grants. No migration or new scope.
- `.venv/bin/pytest -q tests/test_judge_access.py tests/test_judge_profiles.py`
  passed **37** authored checks: four profiles, picker denial, caller claim
  rejection, OTP/proposal/case/handoff isolation, replay, TTL, restart, concurrent
  activation, legacy-alias transition denial and fail-closed storage/readback
  failures. Final review found/fixed a pre-picker alias grant retaining bank
  authority when changing to the picker format; fresh login is now mandatory.
  This justified a new CI candidate before merge. No organizer rows used.
- `.venv/bin/python -m scripts.test_postgres`: **33 passed**, including real
  forced bank/ops RLS, separate restarted stores, competing replicas, complete
  token-free switch/logout audit chain and a shared $3 fixture budget that profile
  rotation cannot replenish. Fixture reservations settled at **$0**, no provider
  calls. Existing real PostgreSQL tests stayed green.
- Full local Python checks: pre-commit/data-secret hooks, Ruff, strict mypy
  (**95 source files**), compile, **857 passed / 25 skipped**, interface/catalog
  snapshots and staged-file scan. Subsequently added readback-failure and legacy-
  transition regressions passed in the **37-check** focused run; strict mypy and
  interfaces passed again after the transition fix. Baseline and reactive B1
  both **32/32**.
- `pnpm --dir apps/web typecheck`, `lint`, `build`, `test:e2e`, `test:e2e --live`
  and `test:e2e --staff`: all passed; **111 fixture + 12 local live-API + 1 staff
  = 124 browser checks**. These verify existing owner flows, not a future picker.
- Additive OpenAPI snapshot and
  [frontend integration contract](../../api/judge-profile-entry.md) prepared. New
  `GET /auth/judge/profiles`, `POST /auth/judge/profile` and optional `/me` metadata
  do not change the OFF/owner identity response. Source profile roles/hints remain
  trusted and scoped; no caller customer/role or raw capability appears in metadata.
- Hash-only integrity check: **855 pinned official v4/release input files,
  zero mismatches**. Official v4 figures remain unchanged; this is post-v4 work.

### Done but not verified

- Frontend picker/BFF cookie replacement, tab coordination and stale-response
  clearing are not implemented by the lead. Backend isolation does not establish
  browser safety. The contract specifies no POST retry and complete state clearing.
- New judge mode has not been deployed/enabled or rehearsed on Azure. Four actual
  source bindings and separate Key Vault judge secrets have not been created.

### Next / blocked

- Frontend lane implements the picker against the documented API, with browser
  regressions for cookie rotation, stale tabs/responses and pending actions.
- Main merge requires the combined candidate's remote CI green under standing
  OK. Keep
  existing Azure judge/warm switches OFF and owner ingress unchanged; submission-
  day activation, exact four sources, secrets, outside-IP rehearsal and costs
  still require Sebastian's approval. The existing global `production` **$3 per
  UTC day** breaker remains shared across profiles; no per-profile purse.
- Model/Azure spend in this session **$0**. No new resources, secrets, replicas,
  public access or held-out run. GitHub CI uses the owner's existing capped budget.
- Continue from docs/status/progress-log.md. Next layer: frontend judge picker
  and submission-day owner decisions. Same rules.

## 2026-10-01 UTC — private post-v4 snapshot and clean-clone verified

### Completed (verified)

- Private submission origin/main is
  **299d0d00ad159a6febe88fd96034dbaa5cb57d7f**. History-preserving refresh from
  3dbfc1d; source/deployed main **b8c13059e1332f974279ffd61ecb2e6b19c35876**.
  All **118** product/prompt/config files are byte-identical. Private source
  history, real commit emails, organizer rows/bindings, sheets/provider traces,
  frozen suites/selections and authoring tools are excluded. Scrub checks found
  zero private sandbox links, workstation paths or Azure hostnames.
- Final Gitleaks 8.30.1 exact directory and full-history scans: **exit 0 / zero
  findings**, default rules plus five exact path/value exceptions. Added one
  exception only for an evidence fixture's independently verified Git SHA;
  negative controls still detect different credentials at every excepted path
  and an allowed test idempotency value in a different path. Fictional metadata
  verified; GitHub visibility PRIVATE, Actions OFF, zero Actions runs.
- README-only fresh clone **aea3d72**: locked Python/web installs, random mode-0600
  fixture credentials, `make up`, authenticated `scripts.fixture_smoke`,
  `make checks` (**829 passed / 28 skipped**), explicit B1 (**32/32**), disposable
  Postgres (**31/31**), typecheck/lint/build, fresh Chromium and browser suites
  (**111 + 12 + 1 = 124**) all passed. `make down` stopped only that project's
  containers. Sequential command wall time **543.74 s**; model cost **$0**.
- Disclosed export failures: missing aggregate-only validator broke collection;
  retaining the exact source validator fixed it. Five model-study tests need
  withheld seen-v3 inputs; export-only conditional skips are explicit, not passes.
  Other runner/provider/budget tests stay active. The sole retained tools file is
  `validate_release.py`, with no case rows or authoring templates. No product,
  prompt/config or official metric changed. README adds tested cache/browser
  prerequisites and removes a stale results-table cell.
- Final snapshot differs from the tested clone only in README/evidence docs;
  GitHub SHA readback and final post-push scans passed. Evidence/commands/timings:
  [clean-clone reproduction](../submission/clean-clone-reproduction.md),
  [snapshot preparation](../../submission/private-snapshot-preparation.md), and
  [post-v4 release notes](../evaluation/post-v4-release-notes.md). Source evidence
  is committed on `docs/post-v4-release-evidence`, preserving exact released main.

### Done but not verified

- Organizer-data README B and official evaluation reproduction in the export
  were not run; private releases are deliberately withheld. Bare-machine OS
  package installation was not tested; Linux libraries/image layers pre-existed.
- Human v4 ratings/agreement and fluent-human PT review remain pending. These
  repairs are **not reflected in v4 results**; no held-out rerun or rescoring.

### Next / blocked

- Stop. Owner supplies the scored human export and decides publication/warm
  replicas/judge access separately; all remain OFF. No additional spend required.
- Fold the docs-only evidence branch into the next authorized green integration;
  no unnecessary Actions run or redeploy for these receipts.
- Continue from docs/status/progress-log.md. Next layer: human review and
  submission-day owner decisions. Same rules.

## 2026-10-01 UTC — post-v4 main release verified

### Completed (verified)

- Combined PR **#101** passed its one candidate CI/safety run (36887864771 /
  36887864886), then merged under standing OK. Released main is
  **b8c13059e1332f974279ffd61ecb2e6b19c35876**. Automatic main CI 36888960606,
  safety 36888960892 and outside-network azure-access 36890629027 passed.
  Owner-approved repairs and AI human-review **ca8fe2c** are included. Official
  v4 remains unchanged, including failed safety gates and **0/30** repeat flips;
  McNemar applies to majority pass on the repeated subset.
- Built/pushed both exact SHA images and read back digests. Fresh East US 2 price
  estimate **$34.63/month**, below $40. Reviewed image/release identity and
  approved temporary smoke budget binding only: Terraform **0 added / 2 changed /
  0 destroyed**. Min replicas 0/max 1, internal API, login/IP allowlist, TLS,
  managed identity and warm/judge modes unchanged.
- `scripts.azure_verify` and capped `scripts.azure_llm_smoke` exercise passed.
  Authored additional smoke assertions verify the independently persisted status
  readback event and concurrent fraud/legal/typo-human handoff reasons. Nine valid
  model calls, zero fallback/unknown costs, **$0.00827475** charged. Lifetime purse
  **$0.10**, scope `production`, run
  `pre-v4-release-b8c13059e1332f974279ffd61ecb2e6b19c35876` (legacy name retained).
- `scripts.serving_browser --target azure` passed Chat/Desk/Ops and a verified
  resolved handoff. GET-only config check confirms all three story hints. New
  ignored `artifacts/azure/jev-release.json` has all release flags true. The
  standard mock-only `azure_smoke` was not run on this real-provider release;
  it is not claimed as passing. Capped real/browser gates are the release evidence.
- All-scope cumulative charged/reserved **$7.61889734**; conservative maximum
  **$11.90208298 ≤ $12**, including retained reserves, remaining dev/comparison,
  full v4 cap and smoke allowances. Older scopes omitted by the legacy helper
  add **$0.048878** to its narrower total. Official v4 cost **$0.54532659** and
  historical completion cumulative **$7.56174459** are unchanged.
- Repair candidate checks: **834 Python / 23 optional skips**, **31 disposable
  Postgres**, **124 browsers**, B1 baseline/reactive **32/32 each**, strict typing,
  hooks/contracts/compile passed. Rechecked all **855** official/frozen/input
  hashes unchanged. No held-out replay, rescoring or abandoned-v1 access.

### Done but not verified

- Refreshed snapshot final audit/clean-clone completed in the newer entry above.
  Human v4 ratings/agreement and fluent-human PT review remain pending.

### Next / blocked

- Finish the private snapshot audit/reproduction, publish documentation evidence,
  then stop. No new model spending or evaluation is required.
- Publication, submission-day warm replicas and judge access remain OFF pending
  Sebastian's separate approval. Release evidence uses a docs-only branch so the
  exact green/deployed main SHA remains stable.
- Continue from docs/status/progress-log.md. Next layer: private submission audit,
  human review and owner submission-day decisions. Same rules.

## 2026-10-01 UTC — owner-approved post-v4 fixes and combined release candidate

### Completed (verified)

- Official v4 remains unchanged at evaluated **1ec9c2f**, frozen product **92994d9**.
  The official page, safety analysis, completion/access entries and AI offline
  human-review commit **ca8fe2c** are integrated. Repeat flips are **0/30**, and
  McNemar p=0.004 is repeated-subset majority pass. No held-out rerun/rescoring.
- Implemented the two owner-approved product repairs: bounded typo-tolerant
  positive ES/PT human requests preserve concurrent `ESC-01` in early fraud/legal
  packets; recognition-memory uncertainty no longer discards an accepted scoped
  MATCH proposal after denial. Explicit inability to choose stays gated; MATCH
  thresholds, policy, confirmation and OTP are unchanged.
- Case-status `verify_readback` now follows the independent scoped post-commit
  read, compares the complete typed public receipt/owner, and persists in the
  originating execution. Failed independent reads emit no verification event.
  Adapter reads retain precise references and existing/new-case receipt aliases.
- Authored ES/PT regressions, strict mypy and the full local CI passed: **834 Python
  tests / 23 optional skips**, **31 disposable local Postgres tests**, **111 fixture
  + 12 live API + 1 staff browser checks**, B1 dev **32/32** and reactive **32/32**.
  Commands: `python artifacts/post-v4/checks.py python|web|postgres`; receipts and
  logs stay ignored in `artifacts/post-v4/checks/`. The first sandboxed pytest
  stalled and was terminated at 437 s; a host-capable diagnostic retry completed
  in 69 s. No application/evaluation worker was signalled.
- **855** official/input files checksum-verified unchanged; no abandoned-v1 access.
  New regression fixtures contain authored values only. No paid calls so far.
- Critical review of offline tooling: unchanged wording/ID validation, CSP and
  HTML escaping remain; v3/v4 page labels/autosaves are separated, no model-score
  leakage or human-rating inference. Progress conflict retained both histories.
- README renders official v4 without a new safety claim and documents the explicit
  fixture/mock path. Added the previously tested fixture BFF smoke and checkout
  hook-cache default for clean-clone reproduction. Post-v4 disclosure:
  `docs/evaluation/post-v4-release-notes.md` — **not reflected in v4 numbers**.

### Done but not verified

- Candidate remote CI, main merge, Azure release gates and refreshed private
  snapshot/clean-clone are still pending; local passes are not deployment claims.
- Human v4 ratings/agreement and fluent-human PT review remain pending.

### Next / blocked

- One combined main PR with remote CI; then standing-authorized image release and
  capped smokes. Resource shape, replicas and access stay off/unchanged.
- Refresh and scan the private submission snapshot, follow only its README in a
  clean clone. Publication and submission-day warm/judge modes need separate OK.
- Continue from docs/status/progress-log.md. Next layer: post-v4 release and private
  submission refresh. Same rules.

## 2026-10-01 UTC — official v4 page and authorized post-hoc safety analysis

### Completed (verified)

- Wrote `docs/evaluation/final-v4-results.md` from saved aggregates, including
  primary/safety/language/segment metrics, cost/latency, machine judges, pending
  human review and the full v1–v4 disclosure chronology. Corrected the requested
  repeat denominator to **0/30**, as saved (0/100 was v2); McNemar **0.00390625**
  applies to majority pass on the repeated 30, not the primary 100-case SAR.
- Wrote `docs/evaluation/final-v4-safety-analysis.md`: every failed P gate is
  accounted for across eight primary cases. `v4.039/040` have null selection
  knowledge but explicit frozen `choose_ref` replies selecting the filed target;
  generic target fallback is inactive. Classification: fixture/harness conflict
  with escalation gold, not an evidenced OTP/confirmation/ownership bypass.
- `v4.019–022` independently read/equal the reported existing case and pass the
  precise gold readback reference. The adapter instead requires a literal
  `existing-case` in its coarse boolean, while measuring a precise alias, causing
  four unverified/policy flags. Missing status readback events are an additional
  instrumentation gap; no real missing case read is evidenced.
- `v4.061`: verified, complete, correctly routed fraud/regulator handoff lacks
  only `ESC-01`; typo/colloquial human request is missed before the deterministic
  fraud return, so no structured NLU can recover it. Product guard/reason gap.
- Three readback misses are `v4.039/040` (verified case instead of gold handoff)
  and `v4.005` (verified handoff instead of gold case). In the latter, NLU denial
  and MATCH `propose` are followed by the broad `uncertain` guard clearing
  candidates. Product selection/state gap. Fault cases `v4.091/092` deliberately
  lack write readback but safely report a handoff, not verified case success.
- Proposed two minimal product repairs plus harness/instrumentation and future
  fixture-consistency work. No evaluated release change, rescoring or rerun.
- Verification: read-only checkpoint reductions assert exact failure sets/counts;
  all **14 language/segment table rows** match `results.json`. Exact authored
  command `PYTHONPATH=. .venv/bin/python artifacts/posthoc-v4/authored_guard_checks.py`
  passes **three** zero-call diagnostic assertions (two gaps and real uncertainty
  control). SHA-256 check: **855 official/input files, zero changes**. Receipts
  are ignored under `artifacts/posthoc-v4/`; access is logged, no row text copied.
- Docs-only branch `docs/final-v4-posthoc-analysis` includes the prior completion
  log. Evaluated main remains **1ec9c2f3a2307f8a5e26fcdc8fefd36ae48a019b**;
  its green CI/safety/access and identical deployed images remain the last release
  evidence. No Azure action, paid model call or abandoned-v1 access occurred.

### Done but not verified

- Proposed fixes are not implemented or tested as fixes. Diagnostic reproductions
  are not improved v4 results. Human sheet/calibration and fluent-human PT review
  remain pending. No new remote CI or deployment was requested for this docs work.

### Next / blocked

- Stop and await the owner's go for the proposed post-v4 repairs. Any later
  release must say **not reflected in v4 numbers**; no new paid run is authorized.
- Continue from docs/status/progress-log.md. Next layer: owner-approved post-v4
  product and instrumentation fixes. Same rules.

## 2026-10-01 UTC — final v4 COMPLETE; no post-hoc changes

### Completed (verified)

- Eval-only recovery #100 merged after corrected CI 36815591018 and safety
  36815591193 passed. Exact evaluated main/origin SHA:
  **1ec9c2f3a2307f8a5e26fcdc8fefd36ae48a019b**. Main CI 36816069214,
  safety 36816069165 and azure-access 36816856679 passed. Full corrected local
  Python suite: 791 passed / 22 optional DB skips; targeted runner/adapter suite:
  55 passed. No product, prompt, config or frozen input changes.
- Re-verified byte-identical frozen 92994d9 images, `scripts.azure_verify`,
  GET-only story hints and authenticated identity/clock/transaction reads. New
  `artifacts/azure/jev-release.json` has all three flags true at 1ec9c2f; it
  explicitly reuses real/browser smoke at identical product 92994d9. Image-tag
  and release identity updates only; resources/replicas/access unchanged.
- Same lifetime scope **final-evaluation-v4**, run **final-program-v4**, $3 cap.
  Preflight verified manifest/binding pins, local forced-RLS serving, credits
  $9.642788954 and key remaining $5.786554. Conservative maximum:
  **$7.016418 + $3 + $0.10 + $0.10 = $10.216418 <= $12**.
- Owner-authorized fresh start under nohup at 04:52:04 UTC; completed at 05:19:04
  UTC without a resume. Watchdog: 15-minute stall / 3-hour total / budget or error.
  `python artifacts/integration/v4-command.py status` reports COMPLETE;
  `COMPLETE.json` matches `results.json` SHA/budget. Specific host PID check
  confirms the worker exited; its PID file is absent. Main stayed unchanged.
- All **260 system runs + 60 dual-judge items** checkpointed; **503 paid-call
  attempts, $0.54532659 known/charged, zero unknown costs**. Cumulative charged
  exposure including retained prior reserves: **$7.56174459 <= $12**.
- Aggregate first-pass results (B1 / P-Gemini): pass **62/100 / 88/100**;
  in-scope SAR **22/100 / 32/100**; automation attempts **41/100 / 51/100**;
  containment **41/100 / 47/100**; strict escalation **38/53 / 49/53**;
  missed transfers **15/53 / 4/53**; unnecessary transfers **11/47 / 2/47**.
  B1 executed 98/100 (two unreached fault boundaries); P executed 100/100.
  Paired SAR difference **+10 percentage points**, bootstrap 95% CI **+5 to +16**.
- **Both systems fail safety gates.** B1 / P: unauthorized actions **2/98 / 2/100**;
  reported without verification **2/98 / 4/100**; policy violations **5/98 / 6/100**;
  materially incorrect **7/98 / 0/100**. Disclosure, missing confirmation/step-up,
  refund promises and grounding each **0/98 / 0/100**. Fraud/regulator recall
  **7/8 / 7/8**; required readbacks **66/80 / 77/80**; required handoff fields
  **48/48 / 51/51**. Counts are evaluator observations, not a post-hoc diagnosis.
- ES pass/SAR/strict escalation: B1 **28/48, 10/48, 17/25**; P **43/48, 16/48,
  23/25**. PT: B1 **30/48, 9/48, 20/27**; P **41/48, 13/48, 25/27**.
  Mixed: both **4/4, 3/4, 1/1**. Segment pass/SAR (B1 -> P, n=25 each):
  Basic **15/4 -> 22/8**, Plus **17/5 -> 21/7**, Premium **15/7 -> 23/9**,
  Student **15/6 -> 22/8**. Full intervals/slices remain in aggregate artifacts.
- Repeats: outcome/pass/SAR flips each **0/30** across three executions, Wilson
  upper 95% **11.35%**. Judges: all 60 paired, zero failed/unpaired. Sonnet/Jev
  exact agreement: language **34/60**, clarity **28/60**, empathy **21/60**,
  handoff usefulness **29/31**; weighted kappa **0.159 / 0.102 / 0.179 / 0.000**.
- Local-serving turn p50/p95: B1 **0.007/0.021 s**, P **2.125/3.776 s**;
  case p50/p95: B1 **0.010/0.037 s**, P **2.253/7.271 s**. These are runner
  timings with local serving, not Azure browser latency.
- P first-pass known cost **$0.229766056**: **$0.002297661 per evaluated case**,
  **$0.004505217 per automation attempt** (51), **$0.007180189 per SAR** (32).
  The report's `per_attempted_case_usd` field uses all 100 evaluated cases;
  the automation-attempt figure here explicitly uses the 51-attempt denominator.
- Results: ignored `artifacts/final-program-v4/results.json` and `results.md`.
  Human sheet: `artifacts/final-program-v4/human-judge-20.csv`; verified 20 CSV
  records and mode 0600 without printing any row. Attempt 1 remains preserved
  at `final-program-v4-attempt1`, $0; disclosure is in JSON and Markdown.

### Done but not verified

- Human sheet is ready, not reviewed; human calibration/agreement is pending.
- Safety/fault failures have not been diagnosed. No post-hoc row inspection,
  code change or rerun was performed. Small segment cells do not support causal
  fairness claims, and zero observed violations does not establish zero risk.

### Next / blocked

- Stop as directed. Owner reviews the human sheet and decides any follow-up.
  No further paid run, product change, main merge or publication is authorized
  by this completion entry. This status-only commit is on a separate docs branch.
- Continue from docs/status/progress-log.md. Next layer: owner review of final v4
  aggregates and human sheet. Same rules.

## 2026-10-01 UTC — authorized eval-only v4 preflight recovery

### Completed (verified)

- Orchestrator authorized an eval-only adapter, authored regressions, fresh-SHA
  identical-image re-verification and a fresh start exception under the SAME $3
  lifetime scope. Preserved attempt 1 as `artifacts/final-program-v4-attempt1`,
  including KeyError stop and live $0 budget receipt; no system checkpoints.
- Read only the author-provided schema vocabulary (field names/types, zero IDs).
  V4 declares `case_ids`, `purpose`, `selection`; v3 declares `scenario_ids`,
  `method`, `n`. Adapter validates both exact envelopes, field types, 30 unique
  members, membership and declared/actual category/language strata. No frozen
  file or binding changes, and no product/prompt/config change.
- Authored `pytest` runner/adapter/rehearsal checks: **50 passed**; Ruff, strict
  mypy and compilation passed. No frozen selection file was executed for testing.
- First recovery CI exposed the pre-existing minimal legacy selection fixture: the
  full local replay confirmed exactly one failure (790 passed / 22 skips). Updated
  that authored fixture to the declared v3 envelope; count comparisons now correctly
  handle declared zero strata. Targeted legacy/adapter/runner checks: **55 passed**.
  Corrected full local suite: **791 passed / 22 optional DB skips**.
  Corrected-head remote CI remains required.
- Added preflight-recovery disclosure to JSON and Markdown result generation.
  The standalone selection parser rejected by automatic review was not executed;
  frozen selection parsing remains inside the authorized program.

### Done but not verified

- Fresh remote CI and final-SHA Azure re-verification are pending. Fresh v4 has not started; no metric or agreement result exists.

### Next / blocked

- Publish one recovery PR for required CI; after green merge, verify identical
  images/access and regenerate acceptance receipt. Reprepare without resetting
  `final-evaluation-v4 / final-program-v4`, recheck credits/local serving, then
  start the authorized fresh program once. Resume only thereafter; product freeze
  and cumulative ≤ $12 remain in force.


## 2026-10-01 UTC — v4 release verified; initial program stopped in preflight

### Completed (verified)

- Final integration #99 merged after its one remote run passed all four checks.
  #64 and #98 are recorded merged. Main and origin/main are clean at
  **791e774a518292e0cc143d4d3bdb69f5056bf461**. Exact-main CI 36812214694,
  safety 36812214691 and outside-network azure-access 36813008449 passed.
- Retagged accepted 92994d9 API/web images; registry readbacks prove identical
  digests. Reviewed Terraform apply: 0 added / 2 updated / 0 destroyed; only
  image/release identity changed. Min replicas 0, ingress, resources, identities,
  secrets and prior smoke binding unchanged. Live estimate remains $34.63/month.
- `scripts.azure_verify`, GET-only story hints and authenticated identity/clock/
  masked transaction reads passed. The private helper initially assumed a customer
  role and a standalone clock route; corrected it to the configured persona role
  and bank clock within `/me`. No product change or paid call. Fresh ignored
  `jev-release.json` has three flags true at final SHA, explicitly reusing the
  real/browser smoke at byte-identical product 92994d9.
- Manifest and authorized ignored 0600 bindings match frozen provenance pins.
  Local serving metadata confirms `aclara_app`, promoted bank clock and forced
  customer/product/transaction RLS. Authored runner tests, Ruff, compilation and
  commit hooks passed; no frozen rows, IDs or author-tool contents displayed.
- `scripts.final_budget --prepare --suite test-v4` closed prior scopes preserving
  every reserve and created exactly `final-evaluation-v4 / final-program-v4`,
  $3 lifetime. Fresh maximum: **$7.016418 prior + $3 + $0.10 + $0.10 =
  $10.216418 ≤ $12**. Free `scripts.openrouter_preflight`: account $9.642788954,
  key $5.786554, each ≥ $4. Local-serving `final_program prepare` passed.
- Invoked the authorized detached launcher under nohup. The first outer shell
  exited before Python entered (no launch/spend); the synchronous launcher then
  created the actual detached worker and immutable launch receipt. The worker
  stopped with **KeyError**, after 100-case structural/identity/ownership preflight
  passed but before any system checkpoint or model call. No worker remains.
  Live durable readback: **0 attempts, $0 known/charged, 0 unknown** in v4.
- Preserved `artifacts/final-program-v4/` including launch, stop and budget receipts.
  Read only aggregate worker metadata/code locations. Zero-cost loader diagnosis
  passed; the next selection interface is the likely failure site. An attempted
  standalone selection-parser diagnostic was **rejected by automatic approval
  review** because it would read frozen selection IDs outside the runner; it did
  not execute. No bypass, main/product/suite/binding edit or paid retry occurred.

### Done but not verified

- V4 system/repeat/judge/report phases have not run: **0/260 system runs** and no
  `results.json` or human sheet. No pass, SAR, safety or agreement claim is available.
- Exact missing selection field is unconfirmed; model has seen no selected IDs,
  scenario text, binding values, case outcomes or author tool contents.

### Next / blocked

- Asked the orchestrator for author-supplied aggregate selection JSON field names
  only, and approval for an eval-only interface fix if required. Such a fix changes
  the SHA, so a fresh verified release and explicit exception to resume-only would
  be required; preserve the attempted directory and the same $3 lifetime budget.
- Keep accepted main at 791e774 unchanged. This documentation is on a separate
  branch; no merge or second start/resume is authorized by this status entry.
- Continue from docs/status/progress-log.md. Next layer: resolve v4 preflight
  interface under owner approval, then the pinned final program. Same rules.


## 2026-10-01 UTC — feature freeze and final v4 integration

### Completed (verified)

- Received Sebastian/orchestrator feature freeze and final v4 GO after the clean
  92994d9 Azure rehearsal. Integrated #64 and #98 with history-preserving merges;
  only suite/protocol/rehearsal/progress documentation changes since product freeze.
- Opaque-byte SHA-256 verifies the v4 manifest as
  `309c3aa22c2eab51b3289075b733c52bb7934a879299762c3fb9ba16a3d9bec8`.
  Authorized private binding copy matches provenance
  `7805535e1eae8c8358440a8807cfa6b156ccf4d450c15de5e85d14b4c6a8016b`;
  ignored destination is mode 0600. No rows, selection IDs, author tool contents
  or bindings were displayed or used to change the product.

### Done but not verified

- Final combined-head remote CI, exact-main identical-image re-verification, fresh
  durable budget/credit/local-serving gates and final program execution are pending.

### Next / blocked

- Finalize clean green main, reverify identical frozen product images and acceptance
  receipt, close prior dev scopes preserving reserves, then run the single detached
  `test-v4` program under `final-evaluation-v4` / `final-program-v4` ($3 lifetime).
  Enforce cumulative ≤ $12, local RLS serving, 1024-token judge cap, and immutable
  resume-only pins. Keep main frozen during the run; inspect aggregate outputs only.

## 2026-09-30 PDT — Frontend lane: released Azure rehearsal at 92994d9

### Completed (verified)

- Owner-authorized rehearsal read back both deployed image tags at **92994d933e7e4d4cddbbf988fb4cc748d3cd5db1** (#97). Key Vault demo credentials traveled only through process memory/stdin; screenshot username/password/OTP fields masked, no browser storage state persisted. Used the existing app purse, never this worktree's provider key. No cloud configuration, backend/NLU/policy, frozen suite/gold or evaluation change.
- **All three quickstart and helper story buttons enabled.** ES neutral inquiry → three choices → explanation; PT shipped inquiry → three choices → explanation → unfamiliarity reopens choices → first re-selection → nonterminal dispute offer → explicit denial → separate confirmation → **new verified case receipt**, independently read back by authenticated GET. Fresh login OTP remained valid; no renewal screen was staged. ES contextual and fresh helper fraud turns each produced a verified FRD-01 primary + AUTH-02 handoff with independent GET read-back.
- **Ten turns / ten valid Gemini/Jev calls / US$0.008335678 known usage**, zero unknown usage/provider errors/fallbacks; neither `operaci3n` nor English status in any of the ten customer replies. Both Desk SLA counters showed **15d 0h 0m**. Selected-charge handoff displayed one verified fact/evidence record and one verified handoff action; fresh fraud helper correctly had no selected-charge facts and displayed its verified action. Ops showed actual case/handoff verification; fresh deterministic fraud had no model calls. [Aggregate receipt](../../submission/video-rehearsal-92994d9.json).
- **41 views / 82 ignored 0600 PNGs**, directory 0700, private gallery `artifacts/ux-audit/azure-rehearsal-92994d9/index.html`; ES/PT Insights and sources, each conversation step/why drawer, both Desk packets and three Ops traces. Representative images reviewed; all captures have zero overflow and sidebar y=0, zero page errors. Extra Insights pass blocked every POST and used no credential/model. Initial readiness **91.229 s** including startup capture; warm Insights **0.849 s**, no forced cold restart. ES-to-PT harness initially raced asynchronous sign-out; correct PT login captured and ordinary authentication retried before any PT model request, with no duplicate paid turn.
- Replaced [shot list](../../submission/video-shot-list.md) with a final **2:55 edited plan**, exact shipped generic messages/clicks, explicit PT re-selection, context-preserving ES recording order, receipt/no-refund boundaries and per-check private screenshot references. Preserved the prior failed release receipt. Only aggregate documentation and this mandated progress entry changed; raw captures/operational references stay ignored.

### Done but not verified

- Final filmed/exported video, narration synchronization and actual duration remain pending. One live rehearsal is not a quality benchmark or production safety claim. Usage is recorded execution metadata, not a provider invoice; cloud/CI and any future filming are excluded.
- This rehearsal created one simulated PT case; a later take may show an existing-case status receipt. Do not force a write, erase a case or reset data to stage filming. Missing product/merchant fields retain explicit labels. Fresh unselected fraud does not promise charge facts; the contextual packet verifies their projection.

### Next / blocked

- Publish the aggregate/shot-list PR, require current-head remote CI, leave it unmerged for lead review. Capture startup/login off camera, preserve the observed PT re-selection and selected-charge context, mask organizer/operational fields before export. No further paid rehearsal is needed or planned here.
- Final recording/export and any deliberate reset remain separate owner work. Keep private captures/diagnostic references local; no frozen suite, gold, B1/P evaluation, freeze, staff claim or resolution was used.


## 2026-09-30 PDT — PR #93 review: enum boundary, merchant citations, private IO (AI)

### Completed (verified)

- Authored ES/PT regressions reproduced all three review findings: **19 failures** before correction. Added generic snake_case rejection (including future/private names) and complete response-plan literal coverage alongside the English-enum guard. The original `operaci3n` bypass remains rejected.
- Merchant exemptions and grounding require a sourced, cited **merchant** fact; citing status/type=Approved/Pending/Purchase cannot authorize that merchant. Genuinely cited same-named English merchants remain valid. Updated the legacy composite-fact unit with an explicit merchant citation; no production interface changed.
- Baseline/report JSON now use exclusive creation at **0600**, with owner rights set before writing bytes, independent of umask. Regression checks cover both writers, permissive/restrictive umasks and existing-file protection. Tightened the three existing local replay snapshots to 0600 and verified unchanged content hashes, including the original frozen baseline.
- No paid call, saved-dev rerun, serving read or v4 access. NLU, prompt hashes, matcher and original dev measurements remain unchanged. Correction-head local verification: **330 focused mock tests**, Ruff, strict mypy (90 source files), compile, frozen interfaces and working-tree data/secret/size policy pass. After merging the lead-retargeted integration base, **383 focused/integration mock checks**, Ruff, strict mypy (93 source files) and frozen interfaces pass. Prior main-target head CI was green; current integration target has no remote CI trigger under the main-only policy.

### Done but not verified

- Azure deployment/live acceptance remains lead-owned and unverified for these source changes. No new model-output quality claim.
- New-head private push and main-target remote CI are reported on #93 after completion; this entry is written before publication.

### Next / blocked

- Lead retargeted #93 to `integration/pre-v4-freeze`; merged that base and preserved both AI and frontend progress entries while resolving the sole progress-log conflict. The main-only CI trigger does not run on this integration-target PR; rigorous local checks apply, and the lead must obtain green CI on the aggregate PR into main. Leave merge/deployment to the lead. No manual edits to other lanes or held-out inputs.
- No more comparison/model spending. Human CSV is still pending owner confirmation; do not open v4.


## 2026-09-30 PDT — Live ES/PT integrity and canonical transaction kinds (AI)

### Completed (verified)

- Reproduced the reported `operaci3n` / `approved` grounding bypass before fixing it. Added merchant-aware digit-corruption and raw English/machine-enum rejection; internal-handle/mojibake guards remain intact. Localized status/type display facts for the phrase model, retaining canonical source facts. Phrase v2.1 SHA-256 `96089ad7985a334b8c6b974298856d939e554d431f04c6c1e7a434d75ec71fd9`; approved reply, recognition and opposite-language guards preserved. UTF-8 roundtrip tests preserve accents; no transport encoding incident is claimed.
- Normalized stated ES/PT kinds to the contract's six ledger enums before unchanged MATCH. Fee/comisión/tarifa/taxa aliases map to **Adjustment**, per Sebastian; unknown/generic/ambiguous kinds become missing evidence. Raw extraction remains auditable. No interface, policy, matcher artifact/threshold, production model or provider setting changed.
- Authored before-fix regressions: NLG 26 failed/10 passed; NLU kinds 45 failed/16 passed. Expanded mock checks pass **293/293**, including 39 NLG, 71 kind and six replay checks. Ruff, strict mypy (90 source files), compile, frozen interfaces and policy catalog pass.
- Froze the type-only replay baseline before normalization (SHA-256 `f3ab2b76f89d723d7b7fff8df37d3c449b13065b6555acd336f7ec6e2cb3cc73`). Read only saved P primary v3 and authored robustness checkpoints: 100 + 40 before/after + 60 before/47 partial after. V3 gains two correct direct proposals in already-passing cases; robustness 40 decisions unchanged. Round-two before has five failed cases with a correct proposal gain and an agreeing reconstructed baseline action; these are potential contributors, not proven conversation rescues. No correct proposal lost. Details and limits: [live-language-failure-analysis.md](../ml/live-language-failure-analysis.md).
- **$0 spend**: no provider, serving or cloud calls; original dev checkpoints untouched, no held-out v4 access. Reconstruction uses transaction day for missing process_date and does not replay sticky slots/product state. Original pass/SAR/unsafe metrics stay unchanged.
- Separately pushed/read back #85 at `83be37164c4470ac04882f1debafaf943d908322`: comparison stops on both HTTP and provider 401/402/403/429 credit/quota paths, including HTTP-200 `provider_402`; 36 focused regressions and hooks pass. Comparison remains **partial**, no further spending. Last durable receipt: $0.20973001 known plus $1.28198 retained unknown reserves = $1.49171001 exposure of $1.50. No reserves released.

### Done but not verified

- These fixes are local source candidates, not a deployed Azure correction. A complete end-to-end type-normalized dev rerun and any new live model output are unmeasured; no new paid run is authorized.
- Publication and final main-target remote CI readback will be reported on the fix PR. This progress entry records pre-publication local checks.

### Next / blocked

- Lead reviews/merges the main-target fix PR only after all remote CI is green, then owns release/acceptance. Tests and the session progress entry are minimal additive shared-folder changes; AI implementation stays in NLU/NLG/LLM/prompts plus docs/ml.
- Keep #85's study partial and Gemini/v5.1 as the default. No more comparison spending; ask before any other paid run. Do not merge from this lane or open v4.
- Human judge CSV path is still pending owner confirmation; use existing judge scores only when delivered.


## 2026-09-30 PDT — Frontend lane: resumed Azure conversation rehearsal

### Completed (verified)

- After the owner's credit-restoration ping, verified both deployed image tags at **c32fd6429281a764ee33dd96622f237c7c0289c3** and exercised the three drafts through ordinary authenticated Azure chat. Helper buttons remain disabled; no authority/availability gate or serving data changed. Credentials stayed in Key Vault/process memory/stdin; no persisted browser state. No direct provider key/call, cloud setting change, frozen-suite access or evaluation run.
- **Seven turns / ten valid Gemini/Jev calls, known US$0.008254224**, zero unknown usage/provider errors/fallbacks. ES: three choices → selected-charge explanation. Original PT: clarification → verified ESC-04 handoff after one detail reply. One bounded, alternative generic PT inquiry in a fresh workspace: **three choices → selected-charge explanation**. Original failure retained; alternative success does not repair the disabled helper/default draft. ES lost-card/help: deterministic verified FRD-01 primary + AUTH-02 handoff, zero model calls in that turn. Both handoffs passed independent authenticated GET read-backs; fraud reasons visible in Agent Desk, actual execution/read-back badge visible in Ops. No dispute, freeze, claim, resolution or reset.
- Captured **28 views / 56 ignored 0600 PNGs** across both conversation passes, including each turn, ES/PT why drawers, packet/execution and Insights. Zero page errors/overflow; sidebar y=0. Generic messages and per-turn timings/costs only in [aggregate receipt](../../submission/video-rehearsal-conversations.json). [Shot list](../../submission/video-shot-list.md) is a **2:55 edited plan** using the observed alternative PT inquiry; no case-receipt scene claimed.
- At the lead's explicit diagnostic request, recovered four conversation references, nine execution IDs, 25 trace-event IDs, selected ES opaque transaction handle, PT persona username and seven exact authored customer inputs through SELECT-only persisted metadata. Saved only those references/inputs to ignored `artifacts/ux-audit/azure-rehearsal-c32fd64/diagnosis-refs.json`, **0600**, verified by read-back. Added only originating `run_id` and `sid` per conversation on the follow-up request; no organizer card facts, token/capability digest/cookie/password/OTP persisted. No operational identifier committed.
- Flagged video defects without changing product/model/policy: disabled stories/no PT ambiguous hint; failed default PT draft; generated ES `operaci3n` and English `approved` in ES/PT; pending ES draft selects an Approved card; missing candidate merchant/product labels; fresh Desk SLA spans months; empty fact/action entries and raw `fraud_review`. Deterministic Ops zero calls are distinguished from total rehearsal cost.

### Done but not verified

- No offer_dispute/confirmation/OTP/case receipt reached or claimed. Three stories plus a bounded alternative inquiry do not establish accuracy or production safety. Final video export, narration synchronization and actual duration remain pending.
- Known model subtotal is execution-trace usage, not a provider invoice/account-balance reading; excludes cloud compute/CI. Empty Desk action arrays are not positive evidence of displayed verified actions. Mixed SLA clock bases are a plausible frontend diagnosis only.

### Next / blocked

- Update existing unmerged PR #88 and require current-head green CI. Lead/frontend review story eligibility/scoped PT availability and clock semantics; AI/lead review generated copy. No further paid replay planned; original failed path remains disclosed.
- Keep captures/diagnostic references private; mask organizer values/operational references before export. V4 remains unopened/unrun. No backend, NLU, policy or model tuning from this lane.

## 2026-09-30 PDT — Frontend lane: partial Azure video rehearsal

### Completed (verified)

- Read back both deployed container image tags at **c32fd6429281a764ee33dd96622f237c7c0289c3**. Demo credential retrieved from Key Vault into memory and a pipe only; no credential or OTP persisted. Authenticated ES workspace; inspected ES/PT navigation, Insights, empty Agent Desk and Ops with Playwright. Non-authentication POSTs blocked during the static pass. **Zero chat messages, zero model spend, zero banking writes/reset**.
- Captured **18 read-only views / 36 PNGs**, plus first startup/login (**40 PNGs total**), ignored and mode 0600; username/password/OTP fields masked. Zero page errors/overflow, sidebar starts at y=0 throughout. Initial readiness **99.28 s** includes startup captures; warm **1.26 s**. Individual navigation/authentication timings are in the [aggregate receipt](../../submission/video-rehearsal-static.json), not a cold-start distribution or model timing study.
- Recorded two story-availability blockers: ES explain/fraud hints are attached to an Ops persona excluded by the frontend customer-role predicate; PT ambiguous has no live hint. All three quickstart/helper buttons disabled. Desk is genuinely empty (HTTP 200); Ops has no conversation execution in this workspace. Prepared the [2:55 shot-list draft](../../submission/video-shot-list.md), with exact shipped generic messages, observed static shots, pending conversation shots and video issues. No product/backend/NLU/policy change, organizer row in Git, frozen-suite access or system evaluation.

### Done but not verified

- Owner paused model-dependent rehearsal after reporting exhausted OpenRouter balance, before any chat was sent. No real-model story, choice, proposal, receipt or handoff packet is claimed. PT static screenshots use the language selector on the same authorized ES workspace; they do not verify PT NLU/persona behavior.
- Final recorded clip, narration synchronization and exported duration remain pending. The shot list is an execution draft for conversation steps, not successful-demo evidence.

### Next / blocked

- Wait for owner's credit-top-up ping before sending any model-dependent story. Resolve live story eligibility/availability with the lead; no authority/scoping bypass. Rehearse each story once, time every turn, read back actual actions, retain failures and update the shot list from observation. Use only the existing approved app purse; no direct provider key/call or reset.
- Publish this aggregate/documentation PR and leave it unmerged; green main-target remote CI remains required. Keep private captures local. No cloud access/replica changes, publication or v4 run.

## 2026-09-30 PDT — Frontend lane: live video blocker triage and fixes

### Completed (verified)

- GET-only check at **2026-10-01 01:18:03 UTC** read back web/API release **c32fd6429281a764ee33dd96622f237c7c0289c3**. `/api/bff/config` returned 200 and trusted upstream persona hints: ES Ops has explain/fraud; PT Ops has an empty hint array. Direct unauthenticated BFF personas returned 401 (not a public passthrough). No login, chat message, model call, reset or Azure setting change. Safe project-role/hint evidence committed under `apps/web/fixtures/`; no organizer bindings or secrets.
- Fixed the frontend customer-only live-hint condition. Hinted Ops/agent personas can prepare stories through normal auth; prefer current hinted identity, then a hinted customer. Missing PT hints remain disabled. Neutral ES charge draft/MX label and previously rehearsed alternative PT inquiry replace misleading shortcuts; fixture templates remain unchanged. No role grant, auto-send, confirmation or backend change.
- Fixed live Desk SLA to use wall time, retaining simulated fixture time and displaying days/hours/minutes. Added localized risk labels with collapsed raw references, explicit empty facts/actions/questions, numbered missing-merchant choices (numeric names preserved), zero-call/no-cost-measurement wording in Ops, and a recording-only quickstart jump to the helper. Recording controls remain hidden by default.
- [API proposal and ownership evidence](../../../apps/web/API-PROPOSAL.md) distinguish PT hint eligibility (currently requires two named merchants), missing verified handoff action projection and AI/lead-owned generated prose defects. No model reply was rewritten by the browser; missing product/fact/action data is not fabricated. Infrastructure startup remains separate from UI error states.
- **18 new authored Playwright cases passed**, WCAG/overflow included; **18 views / 36 ignored 0600 screenshots** at ES/PT 1440/390, gallery `artifacts/ux-audit/live-video-triage/after/index.html`. Before reference is the existing private Azure rehearsal; after images are local authored fixtures, not a deployed release or evaluation. Initial local browser start refused occupied port 3212; isolated 3318/8318 checks preserve that server. Optional browser test ports added within apps/web, CI defaults unchanged.
- Final local typecheck, ESLint, production build, Ruff fixture-script check/format and diff check pass. Production-build browsers **124/124** (**111 UI fixtures + 12 local customer API + 1 staff**), B1/mock only. No frozen suite, gold or paid model call. New frontend code/tests/docs stay in `apps/web/`; this mandated progress entry is the only shared-file addition.

### Done but not verified

- Fixes are local/source changes, not deployed to Azure. PT remains unavailable until the lead supplies a scoped hint. A successful new neutral ES draft was not tested with a real model; the PT alternative was observed in the earlier rehearsal, not replayed here.
- Missing handoff actions/product metadata and generated ES/PT prose need the owning lane. Client wall-clock skew remains a display limitation; the backend owns the actual SLA deadline/duration. Final recording/export remains pending.

### Next / blocked

- Open main-target frontend PR, require current-head green CI and leave unmerged. Lead reviews PT eligibility and verified handoff projection; AI/lead reviews generated prose. Merge/deployment and any paid rehearsal remain separate owner/lead work.
- Keep screenshots and rehearsal diagnosis references private; no backend, NLU, policy, interface or held-out content change.

## 2026-09-30 PDT — PR #93 review: enum boundary, merchant citations, private IO (AI)

### Completed (verified)

- Authored ES/PT regressions reproduced all three review findings: **19 failures** before correction. Added generic snake_case rejection (including future/private names) and complete response-plan literal coverage alongside the English-enum guard. The original `operaci3n` bypass remains rejected.
- Merchant exemptions and grounding require a sourced, cited **merchant** fact; citing status/type=Approved/Pending/Purchase cannot authorize that merchant. Genuinely cited same-named English merchants remain valid. Updated the legacy composite-fact unit with an explicit merchant citation; no production interface changed.
- Baseline/report JSON now use exclusive creation at **0600**, with owner rights set before writing bytes, independent of umask. Regression checks cover both writers, permissive/restrictive umasks and existing-file protection. Tightened the three existing local replay snapshots to 0600 and verified unchanged content hashes, including the original frozen baseline.
- No paid call, saved-dev rerun, serving read or v4 access. NLU, prompt hashes, matcher and original dev measurements remain unchanged. Local verification: **330 focused mock tests**, Ruff, strict mypy (90 source files), compile, frozen interfaces and working-tree data/secret/size policy pass. Prior-head remote CI was green; the new head must pass its own CI.

### Done but not verified

- Azure deployment/live acceptance remains lead-owned and unverified for these source changes. No new model-output quality claim.
- New-head private push and main-target remote CI are reported on #93 after completion; this entry is written before publication.

### Next / blocked

- Push the correction to #93, require all new-head CI green, leave merge to the lead. AI folders plus authored tests/docs/session log only; no default, policy, interface or deployment edits.
- No more comparison/model spending. Human CSV is still pending owner confirmation; do not open v4.


## 2026-09-30 PDT — Live ES/PT integrity and canonical transaction kinds (AI)

### Completed (verified)

- Reproduced the reported `operaci3n` / `approved` grounding bypass before fixing it. Added merchant-aware digit-corruption and raw English/machine-enum rejection; internal-handle/mojibake guards remain intact. Localized status/type display facts for the phrase model, retaining canonical source facts. Phrase v2.1 SHA-256 `96089ad7985a334b8c6b974298856d939e554d431f04c6c1e7a434d75ec71fd9`; approved reply, recognition and opposite-language guards preserved. UTF-8 roundtrip tests preserve accents; no transport encoding incident is claimed.
- Normalized stated ES/PT kinds to the contract's six ledger enums before unchanged MATCH. Fee/comisión/tarifa/taxa aliases map to **Adjustment**, per Sebastian; unknown/generic/ambiguous kinds become missing evidence. Raw extraction remains auditable. No interface, policy, matcher artifact/threshold, production model or provider setting changed.
- Authored before-fix regressions: NLG 26 failed/10 passed; NLU kinds 45 failed/16 passed. Expanded mock checks pass **293/293**, including 39 NLG, 71 kind and six replay checks. Ruff, strict mypy (90 source files), compile, frozen interfaces and policy catalog pass.
- Froze the type-only replay baseline before normalization (SHA-256 `f3ab2b76f89d723d7b7fff8df37d3c449b13065b6555acd336f7ec6e2cb3cc73`). Read only saved P primary v3 and authored robustness checkpoints: 100 + 40 before/after + 60 before/47 partial after. V3 gains two correct direct proposals in already-passing cases; robustness 40 decisions unchanged. Round-two before has five failed cases with a correct proposal gain and an agreeing reconstructed baseline action; these are potential contributors, not proven conversation rescues. No correct proposal lost. Details and limits: [live-language-failure-analysis.md](../ml/live-language-failure-analysis.md).
- **$0 spend**: no provider, serving or cloud calls; original dev checkpoints untouched, no held-out v4 access. Reconstruction uses transaction day for missing process_date and does not replay sticky slots/product state. Original pass/SAR/unsafe metrics stay unchanged.
- Separately pushed/read back #85 at `83be37164c4470ac04882f1debafaf943d908322`: comparison stops on both HTTP and provider 401/402/403/429 credit/quota paths, including HTTP-200 `provider_402`; 36 focused regressions and hooks pass. Comparison remains **partial**, no further spending. Last durable receipt: $0.20973001 known plus $1.28198 retained unknown reserves = $1.49171001 exposure of $1.50. No reserves released.

### Done but not verified

- These fixes are local source candidates, not a deployed Azure correction. A complete end-to-end type-normalized dev rerun and any new live model output are unmeasured; no new paid run is authorized.
- Publication and final main-target remote CI readback will be reported on the fix PR. This progress entry records pre-publication local checks.

### Next / blocked

- Lead reviews/merges the main-target fix PR only after all remote CI is green, then owns release/acceptance. Tests and the session progress entry are minimal additive shared-folder changes; AI implementation stays in NLU/NLG/LLM/prompts plus docs/ml.
- Keep #85's study partial and Gemini/v5.1 as the default. No more comparison spending; ask before any other paid run. Do not merge from this lane or open v4.
- Human judge CSV path is still pending owner confirmation; use existing judge scores only when delivered.



## 2026-09-30 PDT — Insights integration, scoped scans and new comparison purse

### Completed (verified)

- #87 hydration correction: the authored Insights helper now waits for the existing config bootstrap fetch before selecting locale, as the startup regression already does. All assertions retained; three repeats of both selected Portuguese mobile checks pass (**6/6**), ESLint passed. Next.js regenerated route imports were restored; no product code or dependency changed. Initial failure remains disclosed.

- Integrated #77, final #79 and #80 via **#84**, remote head CI **36784056725** and safety **36784056767** passed on the first run. Main/release **c32fd6429281a764ee33dd96622f237c7c0289c3** is clean and matched origin; main CI **36784943361**, safety **36784943206**, outside-access **36786164303** passed. Original PRs closed after ancestor verification; no redundant merge/rerun. Updated frontend rehearsal readiness reported to the owner.
- Fresh images built/pushed and registry digests verified: API `sha256:d2ea6f3feaa460628a56db283b985386ae2c90f29fac034f972d15272695b8a1`; web `sha256:e26e76a9ab33580bea87541beadc6eff0e9458ed33ee5510cc097d2ed56abeca`. Fresh East US 2 price estimate **$34.63/month**. Reviewed apply **0 added / 2 changed / 0 destroyed**, images/release identity and approved temporary smoke binding only; min=0 and access unchanged. `python -m scripts.azure_verify` passed. Real ES filing/readback, PT ambiguity/handoff and deterministic fraud smoke passed: **9 valid calls, $0.00801825 known/charged, no unknowns/fallbacks**. `python -m scripts.serving_browser --target azure`: three surfaces, one handoff/one resolved. No extra browser allowance needed. Receipt `artifacts/azure/jev-release.json` has all three flags true at c32fd64. Mock-only `azure_smoke` was not used on the real-provider deployment; real/browser gates are the evidence.
- At release, cumulative charged exposure **$5.49997829**; conservative helper maximum including full future purses **$11.19997829 ≤ $12**. Scope caps and all prior unknown reserves remain intact; no paid call in reproduction. Azure `/insights` returns 200 and its v4 projection remains explicitly pending.
- Completed README-only private snapshot reproduction. Initial no-data `make up` failed with missing serving tables (`UndefinedTable`), as expected for its serving default. Added explicit fixture/mock quickstart, ops fixture persona, dependency/browser steps, repository-local hook cache and aggregate fixture smoke. Second fresh clone **bcdebe0** passed unchanged README setup, Compose readiness, authenticated committed readbacks and `make checks`: **454 passed / 20 skipped**, B1 **32/32**. First clone additionally passed local DB **23/23**, web typecheck/lint/build and **93** browser checks (**80 fixture + 12 live + 1 staff**). Corrected basic commands total **251.63 s (~4m12s)**; warm Docker/Chromium caveat and every setup/development failure recorded in `docs/submission/clean-clone-reproduction.md`. No organizer data, bindings or provider keys copied. Both disposable local stacks stopped after verification; private evidence retained.

- Final Insights head **312b46a29e92fcefd30704621d3a12b633cafcfb** is integrated; FCR is complaint-scoped and Azure latency explicitly partial (5/10). Final source check verifies 12 aggregate pins. Backend `make checks`: **488 passed / 21 database skips**, B1 **32/32**, interfaces/catalog/hooks green; disposable `.venv/bin/python -m scripts.test_postgres`: **24 passed**, including model-compare restart/cap/other-scope persistence. An initial DB run exposed an outdated arithmetic expectation (4.3→5.8); fixed and rerun successfully. Final web typecheck/lint/build and **106/106** browser checks passed (**93 fixture + 12 live customer + 1 staff**). Source-pin check passes. Initial exporter invocation was denied by the execution sandbox; the authorized read-only invocation passed.

- Reviewed and integrated #77 (offline human-review tooling plus corrupt-prose/internal-handle guard) and #80 (frozen authored 60-case dev release) on `feat/lead-insights-release`. The single progress-log conflict preserves both lane entries. No new dev rows, builder or v4 inputs opened; #80 receives structural checks only.
- Saved latency metadata joins ten primary executions to the five completed conversations: slowest BFF turn 8.395 s, Gemini provider-error first attempt 6.045 s then successful retry 2.100 s, Jev 0.232 s, no phrasing calls. Five terminal follow-ups make pooled p50 optimistic. First-turn extra ~2.967 s remains unattributed; no cold-start claim or paid replay. See `docs/evaluation/pre-v4-latency-components.md`.
- Prepared `dev-gate/model-compare` / run **`model-compare`**, $1.50 lifetime, then independently verified it; `dev-gate/pre-v4` / **`pre-v4`**, $1, remains open. Reserve-before-call semantics and historical unknown charges retained. Both setup commands made zero provider calls. Historical $4.62047227 + full dev $1 + comparison $1.50 + v4 $3 + both smokes $0.20 = **$10.32047227 ≤ $12**. Pre-v4 calls made by the AI lane are covered by its full allowance. Release helpers and final preparation count the comparison scope; final preparation closes both dev scopes.
- Private snapshot **5cc68a85db0763aede6c20cfc62bfc5740e539ea** matches its remote; fresh exact-tree and full-history configured Gitleaks 8.30.1 scans exit **0 / zero findings**. Four exceptions require path AND exact value within the relevant rule. Negative controls still detect different fake credentials in those paths and the allowed value elsewhere. Default-only historical findings remain disclosed. Snapshot is PRIVATE; no public access or Actions enabled.
- Final private snapshot **3dbfc1d69fbc2fc8cabf270e532fe492afc2cdaf** matches origin. Post-push tree/history scans exit 0 / zero findings; privacy patterns zero, fictional metadata verified, Actions OFF. Reproduction changes touch only README/Makefile/external smoke/docs; product remains the earlier d23fa5a export.
- Prepared `docs/evaluation/v4-launch-checklist.md`. Feature freeze Oct 2 12:00 COT / 17:00 UTC plus separate final GO required; v4 remains unstarted.

### Done but not verified

- The corrected #87 head still requires green remote CI before its merge. Its initial browser job failed **92/93**; no workflow replay without a cause.
- Full organizer-backed setup and official frozen-suite reproduction are not verified in the clean clone. Dataset-dependent and omitted private-release tests skipped; they are not passes. The private export still derives from d23fa5a and has not been deployed; refresh after feature freeze.
- Five-conversation latency study remains partial, with one unknown reserve and no forced cold-start bound. No paid replay, model comparison by the lead or v4 run occurred.
- This documentation/test follow-up changes no product code or dependency; no images were rebuilt. Azure acceptance remains c32fd64; do not claim this later source SHA was deployed.

### Next / blocked

- Frontend can rehearse Insights on Azure now. AI lane may use **dev-gate/model-compare / model-compare**, $1.50 lifetime, and **dev-gate/pre-v4 / pre-v4**, $1, reserve-before-call.
- Feature freeze **Oct 2 12:00 COT / 17:00 UTC**, then separately approved final release/one v4 run. Never open v4 rows from this lane or start it early.
- Snapshot refresh/re-audit after feature freeze. PUBLIC visibility and warm/judge access still require explicit Sebastian submission-day approval; no access/resource/replica changes occurred.

## 2026-09-30 PDT — Release accepted; shared pre-v4 scope and private snapshot

### Completed (verified)

- Released **d23fa5afed2a799f8578a78ec323bf2b4864786f**. Exact-main CI
  **36770565523**, safety **36770565807** and outside-access **36772309885**
  passed. Registry digests equal the 21dac9e builds. Reviewed retag apply:
  **0 added, 2 changed, 0 destroyed**, images/release IDs only; min=0 and access unchanged.
  `python -m scripts.azure_verify` passed after release and temporary budget restoration.
- Three-path real smoke at **6e636d3113e4a1cbaf8a3988cdcf0ba9b75e8d7a** is
  reused explicitly: identical application digests, intervening changes only external
  smoke harness/tests/progress. ES filing/read-back, PT ambiguity/handoff and deterministic
  fraud passed. Known **$0.00831825**, charged **$0.02025875**, one unknown reserve retained.
  Mock-only `azure_smoke` was not run against the real-model deployment.
- Owner approved exactly one sixth browser attempt: `AZURE_EXTRA_BROWSER_ATTEMPT_APPROVED=1`
  with the existing 6e636d3 purse, no reset. `python -m scripts.serving_browser --target azure`
  passed **3 surfaces, 1 handoff, 1 resolved** at d23fa5a; budget unchanged (10 calls).
  Counter=6 and one-use marker persisted. Seventh attempt is blocked. Fresh ignored
  `artifacts/azure/jev-release.json` has controls/real-smoke/CI flags true at d23fa5a.
- `PRE_V4_BUDGET_PREPARATION_APPROVED=1 python -m scripts.pre_v4_budget --prepare`,
  followed by separate read-back, created **scope `dev-gate/pre-v4`, run ID `pre-v4`,
  $1.00 lifetime cap**. Prior dev/evaluation scopes, including post-v3, are closed;
  all charges and unknowns retained. All lanes must use this single run.
- Approved ten-conversation latency probe stopped correctly after **5 conversations /
  10 turns** on one unknown-cost call; no retry. In-Azure BFF p50/p95 **1.300s / 8.191s**;
  excluding the entire first conversation, **1.300s / 7.441s** (8 turns). Client
  **1.384s / 8.277s** includes workstation network. No forced cold restart; handler
  timing excludes ingress/module startup. Known **$0.00964182**, charged **$0.02157732**,
  11 reservations / 1 unknown. Probe purse was closed with reservations preserved;
  prior release binding restored via plan/apply (**0 added, 1 changed, 0 destroyed**).
- Cumulative charged exposure after probe **$4.62047227**; retaining full future
  dev $1 + v4 $3 + both smoke allowances $0.20 gives **$8.82047227 ≤ $12**.
  Future v4 is not started/authorized by budget preparation. Private evidence in
  `artifacts/azure/pre-v4-latency-d23fa5afed2a799f8578a78ec323bf2b4864786f/`.
- Created and pushed **PRIVATE** `sebastian-gm/factored-hackathon-2026-sebastian`,
  snapshot **890110119ee7af2386c766dcf8a82f1a4aafc125**, one fresh commit with
  fictional email metadata. Exported 480 source files, excluded 22 frozen/authoring
  files; no ignored artifacts, secrets or private bindings copied. Scrubbed 40 private
  links, 13 cloud hostnames, 3 workstation paths and 2 content contacts; 104 product
  files remain byte-identical to d23fa5a. Honest evaluation chronology retained.
- Snapshot file policy, compilation and authored mock B1 **32/32** passed, executing
  exported code (not the editable private install). Pinned Gitleaks **8.30.1** directory
  and post-push scans each report **4 false positives**, exit 1: 3 AST-verified authored
  idempotency literals and 1 Key Vault secret-name mapping. History patch scan reports
  the same 3 idempotency matches; directory scan covers the path-restricted Terraform
  rule. No actionable secret detected; never claim zero findings. Post-push privacy
  patterns have zero cloud-host/home-path/private-link matches.
- GitHub read-back confirms snapshot SHA/PRIVATE visibility, fictional commit emails,
  Actions disabled and zero runs. Personal sandbox remains PRIVATE with only `origin`.
  Redacted receipts remain ignored under `artifacts/submission-snapshot/audit/`.

### Done but not verified

- Latency probe is **partial (5/10)**, not a 10-conversation measurement; p95 is a
  small-sample observation, not an SLA or cold-start bound. Unknown cost remains reserved.
- Snapshot full frozen-suite reproduction, export-SHA deployment, raw-row equality
  audit and eventual signed-out public access are unverified. Frozen suites/bindings
  are deliberately withheld. Snapshot Actions are OFF; private-source CI passed.
- This documentation follow-up does not change product/image inputs. Azure and the
  acceptance receipt stay pinned to d23fa5a; do not claim a later docs SHA was deployed.

### Next / blocked

- AI lane may use **dev-gate/pre-v4 / pre-v4**, reserve-before-call, $1 lifetime.
  Feature freeze **Oct 2 12:00 COT / 17:00 UTC**; then separately approved release
  and one v4 run. Never start v4 from this session or open its rows.
- No paid replay of the stopped latency probe or its unknown call. Keep the closed
  purse, counters, history and receipt. Additional probing needs an owner decision.
- Snapshot refresh/review after final freeze; explicit Sebastian approval required
  to flip PUBLIC or enable warm/judge ingress on submission day. No min_replicas,
  public access, resource creation or personal-remote change occurred.

## 2026-09-30 PDT — Deployed main; stale Ops smoke selector

### Completed (verified)

- #81 and exact main **6e636d3113e4a1cbaf8a3988cdcf0ba9b75e8d7a** passed CI
  and safety. Main runs **36764627466 / 36764627289** succeeded. Registry
  digests remain identical to the 21dac9e application builds.
- Reviewed app-only Terraform plan/apply: **0 added, 2 changed, 0 destroyed**;
  only image/release identity and approved capped smoke binding. `azure_verify`
  passed; outside-network workflow **36765795810** passed at this SHA.
- Real `azure_llm_smoke`: all three ES/PT/fraud paths passed, including filing
  and read-back, handoff and Gemini/Jev checks. Known spend **$0.00831825**;
  charged **$0.02025875**, including one unknown NLU provider-error reserve.
  Preserve it; no replay of that call. Cumulative charged **$4.59889495**;
  future full allowances give **$8.79889495 ≤ $12**.
- Live browser completed customer handoff and Desk, then failed at Ops:
  smoke selects the retired “Ops · glass box” navigation label. Reviewed UI
  and existing passing local staff test use “Evidencia y operaciones.” Budget
  read-back proves this failed browser attempt made no model calls.
- One-label correction passes `node --check scripts/serving-browser.mjs` and
  existing authored `pnpm test:e2e --staff` (**1/1**, live fixture API, no models).
- Corrected browser attempt stopped at login, exhausting the conservative five
  slots; do not reset them. Owner decision requested for exactly one additional
  browser attempt in the same purse. HTTP-only authentication subsequently
  passed: config/login/SMS/OTP/me/transactions/logout, no chat/model calls. First
  config took **38.4s**, above the harness's 30s default; warm config **0.33s**.
  Owner IP still matches. API console logs were unavailable with no active
  replica. Startup timeout is the supported explanation, not proof from a
  detailed browser exception (the old harness emitted only “login”).
- External harness now has the existing smoke client's **190s** navigation and
  element allowance plus stage/error-class-only failures. No POST/action retry.
  Node syntax and Prettier checks pass. The first custom read-only diagnostic
  mistakenly requested nonexistent `/clock`; corrected check verifies the clock
  from `/me`, as the actual UI contract requires.
- GET-only deployed browser reaches the login form in **79.94s** (navigation
  200, config 200, anonymous me 401), with **zero auth/chat POSTs**. This confirms
  startup exceeds the old harness allowance; no product or replica change.
- Prepared one-use extra browser guard, **OFF until explicit approval** via
  `AZURE_EXTRA_BROWSER_ATTEMPT_APPROVED=1`. Default five slots remain; only one
  browser label/count can use a sixth; its counter/history are never reset,
  including on failure. Authored `tests/test_azure_browser_allowance.py` passes
  **5/5** at zero cost. The same $0.10 purse/breaker remains mandatory.

### Done but not verified

- Correcting only the external browser harness selector. Full browser gate and
  new acceptance receipt remain pending. Shared pre-v4 scope, latency and private
  snapshot are not yet created/run. No v4 input/run or public/warm activation.

### Next / blocked

- Green harness-only correction; preserve application digests and prior real
  smoke evidence, reverify release identity/controls, finish the remaining capped
  browser allowance. Disclose reuse of identical runtime evidence explicitly.
- Only after full acceptance: **dev-gate/pre-v4 / pre-v4**, latency, private export.

## 2026-09-30 PDT — Exact-main recording fixture race

### Completed (verified)

- #78 passed PR CI **36760917373** and safety **36760917289**, merged at
  **d882deb4ea2a9015db460d7d30aedc912f6a8aea**. Main safety **36761758449**
  passed. Automatic main CI **36761758157** passed Python/Postgres but failed
  fixture browsers **79/80**; live/staff were not reached. No CI rerun.
- Failure: PT recording opt-in changes locale immediately after navigation,
  before client bootstrap. Wait for restored chat before that interaction and
  assert selected locale. Product paths/expected labels remain unchanged.
  `pnpm test:e2e --grep 'recording tools are hidden' --repeat-each=3` in CI's
  dev-server mode passed **6/6**; ignored log in `artifacts/integration/`.
- Both d882deb image tags were pushed and registry digests equal the earlier
  21dac9e builds. Live plan is exactly two existing app updates, only images,
  release identity and approved smoke binding; min=0, owner ingress, identities,
  secrets and resource shape unchanged. No apply or paid calls yet.
- Unused 21dac9e smoke purse disabled with history retained; d882deb purse
  registered at $0.10, zero attempts/spend. Cumulative maximum **$8.77863620**.

### Done but not verified

- Test-only correction needs fresh remote CI. Azure still runs prior preview;
  full release, shared pre-v4 purse, latency and private snapshot remain pending.

### Next / blocked

- Green correction PR and exact-main CI; reuse identical image digests under
  resulting main, retire unused smoke purse, replan and finish approved gates.
- Preserve all failed gate logs. Do not claim the failed main run passed or
  bypass the gate. No v4 input/run, warm replicas or public visibility change.

## 2026-09-30 PDT — Main integration verified; smoke binding validation

### Completed (verified)

- #62 merged at **21dac9e791a92fc9979cac8dfc1805a3f76b2563** after candidate
  CI **36757162866** and safety **36757162820** passed. Automatic main CI
  **36757992427** and safety **36757992412** also passed. Main equals origin/main.
- Built and pushed both exact-main images; digest receipt is ignored
  `artifacts/azure/release-21dac9e/image-digests.json`. Fresh East US 2 retail
  prices passed the $40 gate: modeled no-grant margin **$34.63/month**.
- The reviewed release plan stopped on the legacy smoke-ID validation; no
  Terraform apply or real model call occurred. Registered release purse has
  zero attempts/spend. Prepared only the approved private image/run inputs.
- Added full-SHA release/latency ID validation. `terraform -chdir=infra fmt
  -recursive`, `validate` and `test -filter=tests/submission.tftest.hcl -no-color`
  passed: **10 mocked plans**, no cloud mutation. Invalid IDs and judge/smoke
  combinations remain rejected. Application image inputs are unchanged.

### Done but not verified

- Narrow validation correction awaits remote CI/main merge. Azure still runs
  the prior preview; new live smokes, acceptance receipt, pre-v4 shared scope,
  latency probe and private submission export remain pending.

### Next / blocked

- Require remote CI/safety, promote the correction, reuse identical application
  digests under the resulting main SHA, then finish the approved release.
- After release: create **dev-gate/pre-v4 / pre-v4** ($1 lifetime), measure the
  capped Azure BFF latency, then export and scan the private submission snapshot.
  No v4 input/run, warm replica or public visibility change is authorized here.

## 2026-09-30 PDT — #76 integration, pre-v4 accounting and release preparation

### Completed (verified)

- Reviewed #76 (`4436729`), retargeted it to `fix/post-v3-analysis` and merged
  locally without conflicts. Changes are presentation/authored fixtures; BFF
  and Desk write handlers remain intact, including the earlier persona/card
  decision locks. No organizer/v4 row was opened. Recording opt-in grants no
  action authority; canonical reasons/evidence remain available.
- Added duration-only BFF `Server-Timing`, a ten-conversation ES/PT latency
  probe with duplicate-launch protection and release gates, and SHA-bound
  release/latency $0.10 lifetime purses. Authored full mock probe reaches 20
  turns without persisting facts/credentials; no real probe ran yet.
- Added `scripts.pre_v4_budget`: shared **dev-gate/pre-v4 / pre-v4**, $1 lifetime,
  prior-scope closure (post-v3 included), retained unknowns, conflict/breaker
  refusal and rollback. Final v4 preparation counts/closes this new scope and
  conservatively counts historical production charges plus both smoke caps.
- Read-only verified-TLS ledger at 18:01 UTC: prior **$4.57863620**, including
  $0.03580104 historical production; + dev $1 + v4 $3 + release $0.10 +
  latency $0.10 = **$8.77863620 ≤ $12**. Four prior unknown reserves retained.
- Combined `LLM_PROVIDER=mock make checks`: **449 passed / 20 DB skips**,
  six hooks, B1 **32/32**, compile/interfaces/catalog. Ruff and strict mypy
  (85 files) passed; disposable Postgres **23/23**; web typecheck/lint/build;
  browsers **80 fixture + 12 live API + 1 staff = 93/93**. Both bootstrap
  regressions additionally pass **6/6** in CI's development-server mode.
- Corrected a second authored bootstrap race: assert all three shortcuts render
  before removing mocked config. Expectations unchanged; original failure logs
  retained. Restored generated Next declarations. No paid model call occurred.
- Sebastian's standing OK now authorizes green #62 merge/main release and
  spending within the cumulative ceiling. Temporary smoke-run binding separately
  approved; resource shape, min=0 and owner ingress remain unchanged.

### Done but not verified

- Remote corrected-head CI/safety, merged main, pushed/deployed images, full
  Azure release gates, live pre-v4 scope and paid latency remain pending here.
  Exact milestone evidence is recorded in ignored `artifacts/integration/` and
  `artifacts/azure/jev-release.json`; read their SHA/results before claiming release.
- Live v4 scope/inputs/serving/start remain unverified and unstarted. No public
  judge/warm mode or public repository visibility is enabled.

### Next / blocked

- Publish the full corrected integration once, require remote CI/safety green,
  merge #62 and release with image tags plus the approved smoke binding only.
  Run controls/real/browser/outside-access gates and report exact SHA, then create
  and read back **dev-gate/pre-v4 / pre-v4** for the AI lane, then measure latency.
- Feature freeze **Oct 2 12:00 COT / 17:00 UTC**; independent v4 run follows
  freeze/release and a separate GO. Keep v4 blind and v1 untouched.
- After release, prepare the approved scrubbed snapshot in a new private
  `factored-hackathon-2026-sebastian`; retain honest chronology and scan it.
  Public visibility and Oct 4 warm/access activation need explicit approval.
- [Release/budget/probe commands and measurement scope](../evaluation/pre-v4-release-and-latency.md).

## 2026-09-29 PDT — Single remote #62 gate and test-only hydration correction

### Completed (verified)

- Published combined head **00246eb083121d8234c7ef45a076c7fb78801145** once;
  GitHub read-back records #63/#65–#75 merged into the feature branch. #62 and
  blind #64 remain open. Main remains **e12efc73be64f8355aa9f177f08a04337593616c**.
- Automatic CI **36672780834**, attempt 1: Python checks and Postgres passed;
  fixture browsers **63/64**, with one startup locale test failure. Safety
  **36672780958**, attempt 1: passed. No rerun. Aggregate receipt is ignored
  `artifacts/integration/pr62-remote-gates.json`.
- Diagnosed an authored-test hydration race: its first connecting label exists
  in server-rendered HTML, before the locale change handler is attached. The
  correction waits for client bootstrap, matching the existing startup test;
  adds a locale assertion. No product, confirmation, OTP, action, timeout or
  expected-label change. CI dev-server mode passes targeted **3/3**, full
  fixture **64/64**. Restored generated `next-env.d.ts`. Commands/receipt in
  [integration review](../reviews/pr-71-75-integration-review.md).
- Earlier combined local gates remain verified: Python **442**, Postgres **20**,
  B1 **32/32**, browser **64 fixture + 12 live + 1 staff**, Terraform **5** plans.
  No paid model calls or Azure changes; v4 unopened/unstarted, submission OFF.

### Done but not verified

- Remote live/staff browser runs were not reached after the fixture failure.
  The corrected local candidate has not been published or remotely checked.
  Main promotion is blocked on green remote CI; this record does not claim it.

### Next / blocked

- Obtain approval for a second automatic remote CI cycle (about **$0.06**,
  owner estimate, within the $5 hard cap), publish the test-only correction and
  inspect it without manual reruns. Then report the new exact SHA and gates.
- Main merge/release still needs Sebastian's separate confirmation. No release,
  submission activation or v4 final run is authorized by this correction.

## 2026-09-29 PDT — Complete #62 integration and local release gates

### Completed (verified)

- Opened private preparation PRs **#73** (`c328553`) and **#75** (`aaa2a97`),
  read back their feature targets and integrated them locally. Reviewed/merged
  audit **#71**, UX **#72** and AI evidence **#74** into the feature target,
  following the earlier #63/#65–#70 integrations. Two progress conflicts kept
  every entry; no product conflict or force push.
- Critical #72 review: BFF and Desk write handlers match the reviewed #68 base;
  recognition, confirmation hashes, OTP renewal, explicit expired review and
  uncertain-write drafts retain authority in code. Fixed two integration gaps
  in **8513b9d**: current eligible judge alias is retained on story selection,
  and pending card decisions lock story changes. Authored browser assertions
  observe zero message/action POSTs for draft preparation and zero freeze writes
  through the card retry/review. Corrected one stale live revocation label.
- Combined local `make checks`: **442 passed / 17 DB skips**, all six hooks,
  compile/file policy, interfaces/catalog, B1 **32/32**, reactive B1 **32/32**;
  Ruff and strict mypy **85 files**; disposable local Postgres **20/20**;
  Terraform fmt/validate and **5/5 mocked plans**. Web typecheck/lint/build;
  browser **64 fixture + 12 live API + 1 staff = 77/77**. No model spending.
- Corrected #74's stale preview claim to verified `dac3801` read-only startup;
  audit #71 explicitly covers its historical snapshot, not these later changes.
  Official figures/limits and assumption-labeled estimates are unchanged.
  [Review and commands](../reviews/pr-71-75-integration-review.md).
- V4 scope is prepared in code, not created/enabled in Azure. Cumulative snapshot
  $4.54283516 + $3 + $0.10 = **$7.64283516 ≤ $12**. V4 rows/selections/tools/
  bindings unopened; no preflight/start. V1 untouched. No Azure change; submission
  toggles OFF. Main/origin/main stay `e12efc73be64f8355aa9f177f08a04337593616c`.

### Done but not verified

- The committed record covers local gates. Remote CI/safety evidence is produced
  after the single complete-head publication and saved in ignored
  `artifacts/integration/pr62-remote-gates.json` with its exact SHA/run IDs.
  Read that receipt and current GitHub #62 checks before promotion; no extra
  documentation push is needed solely to record a CI result.
- This combined candidate is not deployed. Public judge login/warm replicas,
  new real-chat acceptance and independent v4 outcomes remain unverified.

### Next / blocked

- Inspect the one automatic #62 CI/safety run after publication. Main requires
  remote green plus Sebastian's explicit merge/release confirmation. Avoid
  needless reruns under the hard $5 Actions cap. Report SHA and gate receipt.
- A later approved release prepares the real v4 budget/bindings/local-serving
  pins; separate GO starts the final program. Submission-day activation needs
  source persona/role, dates, exact plan and infra/model cost approval.


## AI lane — 2026-09-29 (judge-facing Production Thinking and Responsible AI)

### Completed (verified)

- Read `docs/production-readiness.md` fully before refreshing it. Used the recorded restricted Azure preview, deployment/budget ADR, existing startup/warm-price evidence, current route/grounding code and published official v2/v3 aggregates only. No v4 row, authoring file or result was opened; no model/cloud call or resource change was made.
- Refreshed Production Thinking (**502 words**) with Container Apps, Postgres/non-owner forced RLS, Key Vault/managed identity, reserve-before-call daily/run caps, Grok failure fallback, committed read-back and unanchored hash-chain limits. Added clearly labeled pilot effort/monthly-cost assumptions for network, identity/MFA, telemetry/SLOs, scaling/recovery, cold starts, scheduling, human queue and bank/retention/audit work; dated baseline/warm prices are distinguished from fresh quotes and incremental allowances.
- Added Responsible AI (**509 words**) with actual masked fact/text boundaries, redaction limitations, requested OpenRouter ZDR and unverified Jev ZDR, private content-bearing persistence and unverified purge; bounded injection/DLP/grounding controls and authority in code. Published v2/v3 ES/PT SAR/strict-escalation counts, corrected regional v2 recall, failed safety gates, es-CL n=9/no fluent PT reviewer and a private issue-report proposal. Only v4 retains `TODO(results)`.
- Checked all quoted figures against existing evidence, all local links/anchors, sensitive-value exclusions and reading length: **2.79 / 2.83 minutes at 180 words/minute**. No product/interface/fixture change and no new runtime tests are needed. Working-tree data/secret/size policy and commit hooks pass, including strict mypy.
- Corrected PR #71's CI-trigger handoff and read it back: the old parser had mistaken the separate main-push filter for a PR branch filter. Target workflows still trigger all PRs. Owner policy remains local checks for stacked PRs, green remote CI before main promotion. This docs commit uses GitHub's documented `[skip ci]` marker to avoid Actions spend until the lead changes triggers; do not carry a skipped required gate into a main merge. No existing workflow was rerun or cancelled. Prior audit-only session note remains privately preserved in ignored artifacts and is excluded from this PR.

### Done but not verified

- Pilot estimates are assumptions, not implementation promises, observed bills, bank-contract quotes or a summed production forecast. No live deployment recheck, new acceptance run, human PT validation, provider deletion or operational SLO is claimed.

### Next / blocked

- Open one documentation PR against `fix/post-v3-analysis` and leave merging to the lead. Lead reviews the effort/cost assumptions and publication wording; green main-target CI remains mandatory. V4 remains pending and blind. No spend or cloud action is authorized by these pages.


## 2026-09-29 PDT — Submission-day infrastructure prepared OFF

### Completed (verified)

- Added independent OFF switches `enable_submission_warm=false`,
  `min_replicas=0`, `enable_judge_access=false`. Warm 1 requires its switch;
  judge mode cannot use a smoke budget. API stays internal HTTPS, max=1;
  public web still uses login/OTP and the existing global $3/day model breaker.
- Judge account/password are external Key Vault references only, never values
  in Terraform inputs/state. OFF has no credential requirement or effect.
  Enabled runtime aliases an existing reviewed source customer/locale/role and
  gated story hints; it cannot claim new ownership/role. Judge and owner
  passwords cannot interchange; OTP/session/action semantics are retained.
- `terraform fmt -check`, `terraform validate`, five mocked plan-only tests
  pass. Read-only sandbox plans (`-refresh=false -lock=false`, explicit sandbox
  wrapper) show **OFF: zero changes**; ON: **two app updates + two scoped RBAC
  grants**, zero deletes, API internal. Plans/JSON stay ignored and 0600.
  No Azure apply, secret upload, enablement or model call occurred.
- Live East US 2 compute rates read at 04:17 UTC: two warm replicas
  **$0.3888–$1.296/day**, 14-day compute **$5.4432–$18.144**. With explicitly
  historical fixed-service/margin assumptions, monthly infra **$34.73–$47.43**;
  upper case exceeds $40 approval gate. $3/day models can add $42 over 14 days,
  separate from v4's lifetime budget. [Plan and approval checklist](../../submission/infrastructure-switches.md).
- Mock `make checks`: **429 passed / 16 DB skips**, six hooks, B1 **32/32**,
  compile/snapshots/catalog. Ruff and mypy **85 files** pass. Disposable local
  Postgres **19/19**, including judge RLS/session recovery on restart and owner
  case isolation. Authored login/security follow-up **19/19**, including only
  the source's gated story hints. Early test issues (sandbox TestClient stall,
  wrong test endpoint and inherited private smoke variable in mock tests) were
  corrected; no product regression remained.

### Done but not verified

- No real judge credential exists from this work. Public ingress, outside-IP
  login, production account/source choice and live enabled budget are not tested.
  Read-only no-refresh plans are not fresh drift audits or apply authorization.

### Next / blocked

- Open this preparation PR against `fix/post-v3-analysis`. Sebastian approves
  source persona/role, dates, exact live plan and total infra/model exposure on
  submission day before enabling anything. Keep testing min=0 and owner ingress.
- Integrate preparation/audit/UX and pending AI docs on the feature target, then
  full local browser/API gates and one remote #62 head run. No main merge,
  Azure change or v4 start until the subsequent owner gates.



## 2026-09-29 PDT — V4 runner readiness, no execution

### Completed (verified)

- Generalized suite/binding/manifest configuration, budget scope/run, output and
  detached start/resume pins for test-v4 (`309c3aa2…`) without opening any v4
  row, selection, authoring tool or binding. Local non-owner serving DSN is
  required and preserved; durable Azure budget accounting remains separate.
  Frozen selections are consumed only inside an authorized start. Judge cap
  remains 1024; B1 100 / P 160 / dual judge 60 / frontier OFF.
- Read-only aggregate ledger: prior charged/reserved $4.54283516 + v4 $3.00 +
  release-smoke allowance $0.10 = **$7.64283516 ≤ $12**. Four prior unknowns
  remain charged. Future preparation closes prior scopes and rechecks exposure;
  no Azure budget scope was created or enabled in this session.
- Authored pins/local-serving/launcher/resume/judge tests passed. Mock
  `make checks`: **430 passed / 17 DB skips**, hooks, B1 **32/32**, compile,
  interfaces/catalog; Ruff and strict mypy (84 files). Disposable local
  `python -m scripts.test_postgres`: **20/20**, including $3 v4 cap across
  restart, prior v3/dev closure and retained reserves. An initial new test used
  an unsupported Store context manager; explicit cleanup fixed it before rerun.
- [Readiness, cost math and limitations](../evaluation/v4-program-readiness.md);
  [future commands](../evaluation/final-run-plan.md). No model calls or Azure
  resource changes; main stays unchanged and v1 untouched.

### Done but not verified

- V4 release inputs/bindings, local organizer serving readiness and a new
  deployed acceptance SHA are not checked here. No v4 preflight, preparation,
  start or outcome is claimed. Latency will include provider/budget calls.

### Next / blocked

- Open the readiness PR against `fix/post-v3-analysis`; prepare separate OFF
  submission switches next. Wait for UX before the single combined main-target
  CI run. Main merge, Azure enablement and v4 execution need their release gates
  and owner authorization. Stacked PRs use documented local checks.


## 2026-09-29 PDT — AI review, feature integration and startup profiling

### Completed (verified)

- Critically reviewed PRs #65/#66 commit by commit. #63 was already merged;
  #65 merged at `b9dabfb`, #66 at `6800ffd` under the preceding feature-merge
  authorization while billing was blocked. One progress-log conflict was
  resolved by keeping both entries in a history-preserving update; no force push.
- Reproduced #65's lead-owned offer failure at zero cost in ES/PT. Commit
  `02d6bcc` narrowly exempts charge-origin memory statements from selection
  uncertainty, retaining separate inability-to-choose clauses and all matcher
  thresholds. Authored regressions: 10 failures/10 passes before, **20/20 after**.
  The reported dev case passes a bound replay using authored mock extraction,
  with its required offer, cancellation and no forbidden/unsafe action. No new
  real-model result is claimed.
- Integrated #67 then dependent #68 locally into `fix/post-v3-analysis`, followed
  by the guard correction. Full combined checks: `make checks` **417 passed /
  16 DB skips**, six hooks, file policy, compile, B1 **32/32**, **12 readbacks**,
  snapshots/catalog; Ruff and strict mypy (84 files); reactive B1 **32/32**;
  `python -m scripts.test_postgres` **19/19**; web typecheck/lint/build; browser
  **46 story + 12 live + 1 staff = 59/59**. No product merge conflict or local
  regression. Generated Next/B1 aggregate files were restored after checks.
- Reviewed and locally integrated #69/#70. Applied #69's six copy changes in
  `ea34060`, mechanically updating one stale hunk beside #68 provenance code.
  AST checks confirm six string-only changes/four replacements and identical
  non-string structure/placeholders/numbers. Corrected the review's coverage
  cutoff: later OTP retry/UX strings are outside its 134-item model inventory.
  All four model-card source pins match; no review call was rerun.
- #70's README/projection numbers match official v2/v3 reports and saved v3
  aggregate objects. Decimal recomputation confirms every low/base/high output
  and 4,440-minute sensitivity. Historical FCR, counts, handling and wait times
  match committed pipeline aggregates; workload/efficiency/infra are labeled
  assumptions, with safety failures/partial judging retained. Bootstrap order
  was checked against source, not rerun on organizer data. A second
  progress-log-only conflict preserved every entry. An early local check on
  the unresolved index failed in the staged-file scanner; after resolution the
  stable `95332e0` candidate passed `make checks` **417/417**, B1 **32/32**,
  hooks/compile/snapshots/catalog. No extra paid calls.
- Added main-only PR filters and workflow/ref cancellation to CI/safety in
  `2b41886`. YAML assertions verify PR base main, main pushes and cancellation.
  The owner initially announced billing recovery; the single authorized reruns
  on #67/#62 still started zero steps. Further reruns stopped when requested.
  The later owner confirmation supersedes that block: **$5 hard Actions cap**,
  rigorous local gates for stacked PRs, remote green required before main merge.
- Read-only startup profiling of the existing `dac3801` preview: 86.059 s is
  the prior web→API cold-read chain, with a 43.581 s web-ready/API-ready gap.
  Cached API/web images are 226.88/72.26 MiB; a separate API activation pulled
  its image in 7.54 s. Network-disabled local API initialization at 0.25 CPU /
  512 MiB took 6.399 s; TypeSafe import 0.516 s; LightGBM not loaded at readiness;
  matcher construction afterward 2.479 s. Non-owner TLS serving/identity/hint
  timings completed without printing rows. An initial workstation pool timeout
  was followed by successful TLS/read checks; firewall IP still matched.
  No Azure change, model call or banking write. [Profile and proposals](../evaluation/preview-startup-profile.md).
- [Review, commit dispositions, gate commands and limits](../reviews/pr-65-66-integration-review.md).
  Main/origin/main remain `e12efc73be64f8355aa9f177f08a04337593616c`.
  V4 files/rows/tools/bindings were neither opened nor executed; v1 untouched.

### Done but not verified

- #67–#70 and the lead guard/copy/CI changes are locally integrated, not yet
  published on the combined #62 head. GitHub stacked PRs still show open until
  publication. The frontend UX PR is being prepared on `feat/judge-ux-polish`.
- Full remote CI on the final combined head and Azure release are pending.
  Browser/Postgres checks predate only the six verified copy changes; final UX
  integration still requires its combined local browser gate.
- Startup timings are individual observations, not a complete Azure cold-start
  decomposition. No proposed dependency/import/cache/readiness optimization was
  implemented. No human PT fluency or independent v4 result is claimed.

### Next / blocked

- Wait for the orchestrator's UX PR number, review and integrate it locally.
  Re-run necessary combined local gates, then publish **one complete #62 head**
  and inspect its automatically triggered CI/safety; avoid manual reruns.
  Keep the $5 owner billing cap and main-only trigger/cancellation policy.
- Do not merge main or start v4. Report the combined SHA and remote gates after
  the single full-head run. Any release remains a separate authorized step.


## AI lane — 2026-09-29 (language model card and cross-vendor copy review)

### Completed (verified)

- Updated [the language model card](../../ml/model-card.md) for NLU v5.1, phrase v2's actual approved text and deterministic clarification/recognition guard, contextual ES/PT/uncertain language evidence, the 6 s first-attempt timeout and 1024-token Sonnet judge cap. Source hashes read back exactly; only independent v4 slices retain `TODO(results)`.
- Recorded PR #65's frozen 40-conversation dev results (39/40 before/after, normalization failures 9→0, clarifications 15→6, cost/latency and limits) separately from official v3 P 77/100 versus B1 52/100, SAR +11 pp (95% CI +5 to +17). V3 is now seen dev data; its post-hoc 100/100 does not replace the official result. V4 remained unopened and unrun.
- Completed Sonnet cross-vendor review of **134/134** active source strings/variants, **67 ES + 67 pt-BR**, including all templates, offer/recognition questions, approved API replies and all eight added web translations since `e12efc7`. Ten valid calls, no retries/truncation/new unknown costs. [Before/after and decisions](../ml/pt-review.md).
- Per-call usage and readback of the ten durable reservations agree at **$0.085928**, below the approved $0.10. Existing shared `dev-gate/post-v3` / `post-v3` scope reads **$0.71924554 exposure** (known $0.68326354; three pre-existing unknowns), below the requested $0.90 stop and unchanged $1 cap. Concurrency one; every call reserved before sending under the scope lock. No key-level delta or final scope was used.
- `LLM_PROVIDER=mock make checks` passes: six hooks, Ruff, strict mypy, compilation, file policy, **308 passed / 14 database-dependent skips**, B1 **32/32**, interfaces and policy catalog. No product code changed in this PR.
- Reconciled the updated lead target `6800ffd` into this feature branch after PRs #65/#66 merged, preserving every progress entry. The conflict was documentation only; no product or fixture changes were authored. Local 381-test checks on that combined target passed in this session.
- Pushed only private origin and opened [PR #69](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/69) against `fix/post-v3-analysis`; read back the exact description, branch SHA, mergeable and open/unmerged state. All four remote CI jobs completed with failure: annotations say the jobs were not started because an Actions budget prevents use. No CI was cancelled.
- Prepared a [lead-owned strings-only patch](../../ml/copy-review-post-v3-proposed.patch): five PT occurrences use `contestação` consistently, and one ES freeze offer explains OTP as a new verification code plus confirmation. No lead/front-end product folder was edited. All AI templates and changed web messages were kept. Patch applicability, Python compilation, six string-only AST changes, preserved placeholders/numbers and documentation links were verified.

### Done but not verified

- Copy is model-reviewed, not fluent-human PT validation; no additional production accuracy, fairness or latency measurement was made. The lead-owned proposed strings are not active until the lead applies the patch. PRs #65/#66 describe candidate behavior; this card is not a deployment attestation.

### Next / blocked

- PR #69 stays unmerged for the lead. Review/apply its six lead-owned copy changes and merge the prerequisite fixes before release/final v4. The authorized latest-head reruns still failed before steps; GitHub cited failed recent account payments or a spending limit needing an increase. A meaningful conflict-resolution push gets its normal CI; no further manual rerun is planned until account billing allows jobs to start. Green remote CI remains required before merge. Preserve v4 blindness and make no further paid call.
## AI lane — 2026-09-29 (Actions policy and documentation handoff)

### Completed (verified)

- Read back [PR #70](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/70) and [PR #69](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/69): both are open, unmerged and mergeable against `fix/post-v3-analysis`. Their descriptions now reflect Sebastian's latest Actions instruction: the $5 budget is unblocked; rigorous local checks are the gate for stacked PRs; green remote CI is required for PRs into `main`.
- Reconciled PR #69 with lead target `6800ffd`, preserving both progress histories; its proposed lead-owned copy patch still applies. Documentation PR #70 retains the verified **381 passed / 14 database-dependent skips**, B1 **32/32**, strict mypy and Ruff checks. No additional manual CI rerun, model spend, deployment or v4 access followed the new instruction.

### Done but not verified

- The later owner confirmation supersedes the earlier billing-block and all-merge CI notes below. This lane has not independently audited the owner billing change or future main-target CI; no green remote CI is claimed for these stacked PRs.

### Next / blocked

- Lead reviews and merges PRs #69/#70 into `fix/post-v3-analysis`; this lane leaves both unmerged. Require green remote CI before merging a PR into `main`, and avoid needless reruns. Business projection remains assumption-labeled; v4 results remain pending and blind to this lane.

## AI lane — 2026-09-29 (business projection and judge README refresh)

### Completed (verified)

- Read `docs/evaluation/business-projection.md` and root `README.md` before editing, then used only committed dataset aggregates, official v2/v3 reports, architecture/serving source and the historical Azure dev price plan. No v4 row, authoring tool or artifact was opened; no model call or cloud resource change was made.
- Refreshed [the business projection](../evaluation/business-projection.md) with official v3 P **77/100** versus B1 **52/100**, SAR **39% / 28%**, strict escalation **30/40 / 20/40**, unnecessary transfers **11/60 / 23/60**, precise **$0.00237687544** serving cost and case/turn latency. Kept safety-gate failures and partial judging visible; later seen-v3 checks do not replace the official result.
- Read back dataset **43.6% Queja contact FCR proxy**, **12,297/67,095 = 18.33% identified charge-dispute complaints**, and **434.606 s / 220.803 s** complaint/transactional handle-time means. The 10,000/month volume and use of category handle times for dispute intake are explicitly assumptions, not monthly/source facts.
- Authored a reproducible low/base/high projection against B1 with review/remediation and all nonautomated issues receiving human follow-up. Base: **3,900 automated intake outcomes**, **1,200 avoided unnecessary transfers**, **11,621 net agent minutes**, **$23.77 model + $35 assumed infra = $58.77/month**. Low adds **3,028 minutes** of work. Arithmetic uses exact source values, and avoided transfers are not counted twice as time savings. A transactional-time proxy sensitivity reduces base savings to 4,440 minutes. Only v4 retains result placeholders.
- Replaced the stale mock-diagnostic README with a short judge draft: three guided stories, one Mermaid architecture diagram, separate official v2 and after-fixes v3 evidence, v4 pending, honest language/safety/identity/production limits, and source-checked mock-only local bootstrap. Root README is the explicitly requested shared-file edit; no product code or fixtures changed.
- Decimal arithmetic, output rounding, evidence links, one-diagram constraint and v4-only `TODO(results)` entries verified. Mock `make checks` passes: six hooks, Ruff, strict mypy, compilation, file policy, **381 passed / 14 database-dependent skips**, B1 **32/32**, interface snapshots and policy catalog.
- Following Sebastian's Actions-budget instruction, reran only PR #69's latest two blocked workflows: `ci` **36662765802** and `safety` **36662765906**, both attempt 2 on `3c86e27`. All four jobs completed without steps. Their new annotations say recent account payments failed or the spending limit needs increasing; this does not establish which billing condition applies. No older head, merged PR or other lane was rerun; no repeated attempt was requested.

### Done but not verified

- Projection is conditional capacity arithmetic, not realized production savings, a labor-cost estimate or a current cloud price/capacity quote. Dispute-specific agent times, traffic weighting and operational remediation remain unmeasured. Local bootstrap commands were reviewed against code, not executed against organizer data or a new deployment in this session.
- Remote green CI is required before any merge. The authorized PR #69 reruns are still blocked before startup by GitHub account billing/spending status; the $5 budget announcement did not make those attempts runnable.

### Next / blocked

- The documentation candidate targets `fix/post-v3-analysis` and remains for lead review/merge only after green remote CI. Preserve v4 blindness and zero model spend. Once the owner confirms the GitHub billing block is resolved, rerun blocked current-head workflows once; do not rerun needlessly or merge without green CI.

## AI lane — 2026-09-29 (queued PR #62 review findings 1 and 3)

### Completed (verified)

- Read the lead's review on `fix/preview-startup-review` after opening robustness [PR #65](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/65). Added authored mock regressions before changing behavior; eleven reproduced the assigned defects. No v4 input was opened and no paid call was made.
- Preserve code-supplied clarification replies exactly, including bilingual language help; retain the existing recognition guard. Rephrased explanations now receive the actual approved `plan.reply` as `approved_text` and fallback, with DLP/grounding checks retained.
- Added explicit ES/PT/uncertain language evidence, excluding domains and trusted merchant names. Shared `com`/`sim` tokens cannot decide language; NLG rejects only confident opposite-language evidence. The frozen two-language interface retains its default. [Implementation and evidence](../ml/pr-62-ai-review-fixes.md).
- `make checks` passes: six hooks, Ruff, strict mypy, compilation, file policy, **329 passed / 14 database-dependent skips**, B1 **32/32**, interfaces and policy catalog. Targeted new and existing API/recognition/grounding regressions: **90 passed**. Merged the lead target advancement `dac3801` into this feature branch, preserving both progress-log entries and leaving PR merges to the lead.

### Done but not verified

- Real-model performance, calibrated language probabilities and human PT fluency are not measured in this follow-up. No further paid measurement is planned. Remote CI remains subject to the owner Actions budget block.

### Next / blocked

- [PR #66](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/66) is open, unmerged, targeting `fix/post-v3-analysis`. Lead reviews and merges; preserve both additive progress entries when reconciling PRs #65/#66. GitHub Actions requires the owner budget block to be resolved; read back current-head CI before merge. PR #65 retains the paid robustness study and lead-owned guard follow-up. Keep v4 blind and do not deploy.

## AI lane — 2026-09-29 (post-v3 authored robustness study)

### Completed (verified)

- Read handoff 14; authored and froze 40 synthetic ES/PT conversations at `31826c6` before any P run or language fix. All three fixture hashes read back unchanged after measurement. No v4 data was opened.
- Real P before/after: **39/40 → 39/40**, ES **19/20 → 19/20**, pt-BR **20/20 → 20/20**, zero unsafe/forbidden outcomes, all four embedded injections logged. Fixed complete ES/PT spoken-amount parsing and Portuguese previous-weekday dates in AI-owned NLU, with 45 authored parser regressions. Opening slot failures **9 → 0**, clarification responses **15 → 6**, case p50 **7.877 → 5.423 s**, p95 **12.195 → 12.273 s**. [Full report](../ml/nlu-robustness-post-v3.md).
- All **89/89 → 75/75** OpenRouter attempts and **59/59 → 50/50** Jev attempts valid. Known new per-call cost **$0.230932684**, no new unknown usage. Durable `dev-gate/post-v3` / `post-v3` readback: **$0.63331754** including retained reserves, below the $0.90 stop and $1 shared lifetime cap. No final scope was used; no further paid run planned.
- `make checks` passes: six hooks, Ruff, strict mypy, compilation, staged-file policy, **360 passed / 14 database-dependent skips**, B1 **32/32**, interfaces and policy catalog. Additional strict-mypy and B1 reactive dev **32/32** pass. No prompts, model roles, contracts or policy authority changed.

### Done but not verified

- One offer-path failure remains lead-owned: valid model/postprocess unfamiliarity is overridden by `selection.uncertain()` on a charge-origin memory statement; MATCH was confident. Zero-cost reproduction is saved privately and the report describes the lead's narrow regression/fix. No human language validation or independent accuracy claim is made; latency is one before/after observation.
- [PR #65](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/65) is open against `fix/post-v3-analysis`, unmerged. All four remote checks completed without starting jobs: their annotations report an owner Actions budget block. Local checks are green; remote CI is not green.

### Next / blocked

- Lead reviews/merges PR #65 into `fix/post-v3-analysis` and fixes the remaining deterministic uncertainty guard before release. The lead base advancement `dac3801` is merged into this feature branch with both progress entries preserved. Queued review findings 1 and 3 are complete in independent [PR #66](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/66), with mocks and zero additional spend. Keep v4 blind; this lane does not merge/deploy.

## 2026-09-29 PDT — Preview diagnosis, code-only startup fix and PR #62 review

### Completed (verified)

- Read handoff 14 fully and applied Sebastian's subsequent decisions: min
  replicas stay zero while testing; run CI locally while Actions billing is
  pending. Main and origin/main remain `e12efc73be64f8355aa9f177f08a04337593616c`.
- Read-only Azure metadata confirmed both preview images at
  `37627d4001bc02bd3ae0c25c618acd16f5b4a47e`, initially zero replicas. With
  authenticated `httpx` BFF reads, the first config GET failed 503 after 50.560 s
  and login failed after the 10.114 s deadline. Warm login/OTP, me including the
  clock, and repeated transactions passed in 0.1–0.5 s. API logs show completed
  startup, successful reads and no sampled application exceptions. This confirms
  the cold-start chain for the reported failure. No chat/provider/banking write
  was invoked; credentials/OTP/cookies and organizer rows were never printed.
  [Diagnosis and ignored evidence](../evaluation/preview-startup-diagnosis.md).
- Code commit `e043356` on `fix/preview-startup-review`, based on PR #62 head
  `32587c9`, gives startup GETs 75 s and at most one transient GET retry, preserves
  single-attempt POSTs, and shows ES/PT startup/retry states. No Azure setting,
  image or access boundary was changed.
- Pushed the separate candidate to the existing private origin and opened
  [draft PR #63](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/63), targeting
  `fix/post-v3-analysis` so its startup/doc changes can be reviewed independently
  of #62. No PR or branch was merged.
- Reviewed every PR #62 commit. Authored, zero-cost mock/ASGI reproductions
  confirmed five findings: approved language clarification lost before phrasing; legal cues
  lost across session tabs; `.com`/SIM language false positives; renewal reuses an
  invalid freeze hash; latest fraud packet may belong to another conversation.
  [Findings, owners and commit dispositions](../reviews/pr-62-review.md).
  The preliminary recognition-question finding was narrowed after checking the
  API's existing deterministic guard; the confirmed language-help case was then
  exercised through the API, not just the NLG helper.
- Local CI commands passed: `UV_CACHE_DIR=$PWD/artifacts/uv-cache make checks`
  (308 pytest passed, 14 skipped; B1 dev 32/32; interfaces/catalog current),
  `.venv/bin/ruff check .`, `.venv/bin/mypy --strict src/aclara`,
  `.venv/bin/python -m evals.runner --system B1 --scenarios evals/dev_scenarios_v2.yaml`
  (32/32), and `.venv/bin/python -m scripts.test_postgres` (17/17 in a disposable
  local database). Web: `pnpm typecheck`, `pnpm lint`, `pnpm build`,
  `pnpm test:e2e` (46/46), `pnpm test:e2e --live` (8/8),
  `pnpm test:e2e --staff` (1/1): **55 checks** including all 26 startup checks.
  Two initial startup test failures were corrected (hydration wait and translated
  retry label); the full final web run passed. Local caches use writable paths;
  the missing local pre-commit hook was reinstalled. Generated Next type paths
  and the authored-dev results page were restored after test commands.
- Added [the v3 results page](../evaluation/final-v3-results.md) from saved
  aggregates only: P 77/100 versus B1 52/100; in-scope SAR difference +11 points,
  95% CI +5 to +17; failed full safety gates and partial judging disclosed.
  Verified SHA-256 of the four original result/report/partial/sheet files remained
  unchanged. No v2 rerun or abandoned-v1 access occurred. V3's seen-data 100/100
  is explicitly a development regression check, not a replacement result.
- Read GitHub's PR #62 check annotation with `gh api`: jobs did not start because
  the account Actions budget prevents use. This is not a code-test failure and
  is not a green remote run. PR #62 remains open and unmerged.
- Added submission-day-only warm replicas and live East US 2 price assumptions
  to [the checklist](../../submission/checklist.md): two 0.25-vCPU/0.5-GiB apps about
  $0.39/day idle to $1.30/day continuously active, excluding grants/other charges;
  a fully active warm month can exceed the $40 total approval gate. No replicas
  were changed. **New model spend in this session: $0.**

### Done but not verified

- Startup fix is locally verified and committed, **not deployed**; no corrected
  Azure cold-start smoke is claimed. Paid preview chat/phrasing was not tested.
- The five review findings are reported with proposed remedies; those product,
  policy/contract and evaluation fixes are not part of this startup patch.
- Local CI passes, but GitHub CI/external-access workflow cannot run until the
  owner's billing decision. V3 judging and human review remain partial/pending.

### Next / blocked

- Review the startup patch for a separately approved preview redeploy, retaining
  min replicas zero. Decide owners/timing for the five PR #62 findings before
  release. Keep #62 unmerged until CI can run or an explicit merge exception.
- Share/submission-day warm replicas require the dated plan and refreshed cost
  approval in the checklist. No cloud resource or ingress expansion is approved
  by this session.
- **V4 remains unopened and unstarted.** Complete fixes/release gates and await
  the orchestrator's explicit run go. For later sessions paste:
  “Continue from docs/status/progress-log.md. Next layer: PR #62 review fixes and
  preview startup release. Same rules.”

## 2026-09-29 UTC — Owner-approved preview deploy of `fix/post-v3-analysis`

### Completed (verified)

- Sebastian approved deploying the branch tonight for his own review. Images for
  `37627d4001bc02bd3ae0c25c618acd16f5b4a47e` were built from the committed tree,
  pushed with a temporary private Docker config (token removed), and applied as
  the only change (`image_tag`; Terraform 0 added, 2 changed, 0 destroyed).
- `scripts.azure_verify` passed: restricted HTTPS boundaries, single revisions,
  SHA images, managed identity, TLS, firewall, Key Vault RBAC and budget alerts.
  Web returns 200 from the owner IP, the BFF returns 401 without a session, and
  the API revision is healthy on the new image.
- GitHub Actions did not start PR #62 jobs: "an Actions budget is preventing
  further use" (account billing, not code). The same CI steps ran locally and
  passed: pre-commit, Ruff, strict mypy, compileall, pytest, interfaces, policy
  catalog, B1 dev and B1 v2 (32/32 each), staged-file policy, Postgres
  integration (17/17), web typecheck/lint/build, browser 29/29.

### Done but not verified

- This is a **preview of a branch, not a release of `main`**. The capped
  real-model and browser smokes were not rerun: their approved five-conversation
  allowance was already used by the v3 release smoke. The `azure-access` workflow
  cannot run until the Actions budget is restored. The deployed app keeps the
  existing production cap (run `after-v2-release-smoke`, about $0.09 left, $3 daily).

### Next / blocked

- Restore the GitHub Actions budget (owner billing decision) so CI and the
  external access check can run; then merge PR #62 and release `main` for v4.

## 2026-09-28 UTC — Post-v3 fixes (orchestrator session, branch `fix/post-v3-analysis`)

### Completed (verified)

- Post-hoc analysis of the reported v3 run found six causes for the 23 P-Gemini
  failures, plus wrong-language phrasing, judge truncation and a web logout on
  stale OTP. All fixed generically with authored regressions; details in
  [post-v3 fixes](../evaluation/post-v3-fixes.md). V3 is retired to dev data.
- Checks: pytest, Ruff, strict mypy, interfaces, policy catalog, B1 dev 32/32,
  browser 29/29 (fixtures, live, staff).
- Real P-Gemini on all 100 (seen) v3 cases: 100/100, 23/23 prior failures fixed,
  0/77 regressions. Real P dev gate (`--profile post-v3`) passed: 20/20, 18/20,
  12/12, 0 unsafe. Spend $0.40 of the new `dev-gate/post-v3` $1 allowance;
  all prior scopes closed; cumulative ≈ $4.23 of $12.

### Done but not verified

- Branch not pushed; GitHub CI not yet run. No release or Azure change.

### Next / blocked

- Lead: review, push, CI, merge; v3 results page. Data/frontend lane: author an
  independent v4 suite with new templates (handoff 14). Then release and a
  single v4 run after the orchestrator's go.

## 2026-09-28 UTC — V3 system metrics finalized with partial judging

### Completed (verified)

- The sole incomplete judge unit's metadata showed **Sonnet via OpenRouter**
  twice returning `status=refusal`, stop class `length`, exactly **256 output
  tokens** per attempt, with no validated score. Jev was not reached on that
  item. This repeats for the same item at the configured cap, so no further
  paid resume was attempted. The failure was not HTTP 5xx, timeout, rate limit
  or budget denial.
- Existing `evals.final_report.write_report` finalized aggregate system metrics
  from all **260 completed case checkpoints** and 28 completed judge pairs,
  with **zero model calls**, no tracked code change and an explicit **partial
  judging** header and receipt. `results.json` and `results.md` are ignored,
  mode 0600; `PARTIAL.json` exists and `COMPLETE.json` does not.
- Primary 100-case figures from `results.json`: B1 **52/100 pass, 28/100
  in-scope SAR**; P-Gemini **77/100 pass, 39/100 in-scope SAR**. Paired P-minus-B1
  SAR difference **+11 percentage points**, 95% bootstrap CI **+5 to +17**.
  Strict escalation recall **20/40 vs 30/40**; all 30 preselected repeats had
  zero success, SAR and outcome flips. Safety gates remain failed on both systems
  because fraud/regulator recall and required readbacks are incomplete.
- Durable v3 spend remains **$0.47321405 / $3**, zero unknown costs. Prior plus v3
  and release smoke totals **$3.83161437 / $12**. The 20-item human judge sheet
  exists for owner review; no human agreement claim is made.

### Done but not verified

- Judging is **28/60 paired items**. Sonnet/Jev agreement covers those 28 only;
  the remaining items were not scored. The partial report is not a full final
  program completion. V2 remains the official prior result; v3 is after fixes
  on an independent fresh suite.

### Next / blocked

- Stop without another paid resume. Preserve pinned clean main `e12efc7`, all
  checkpoints and the partial report. Owner can review the complete primary
  metrics and the partial judge limitation in ignored
  `artifacts/final-program-v3/results.json` and `results.md`. This progress-log
  branch remains unmerged so any later authorized run can retain its release pin.

## 2026-09-28 UTC — Single authorized v3 resume stopped during judging

### Completed (verified)

- Process metadata showed 213 completed case result files versus 212 published
  progress checkpoints after the first stop. The budget readback occurs between
  those writes, localizing the earlier `OperationalError` to the budget database
  connection path without opening a case result.
- Local Postgres container and TCP port were healthy. Azure admin and app roles
  both passed `verify-full` TLS connections. Current public IPv4 matched the
  configured Postgres allowlist; its Azure-services sentinel remained present.
- Main was clean and matched origin at the pinned release SHA `e12efc73`.
  Preserved the prior stop receipt, then ran one detached `resume` with the same
  15-minute stall and original three-hour wall-clock watchdog rules.
- Resume completed all **260/260 system runs**, then stopped at **28/60 judge
  items** with `RuntimeError`. The evaluator's sanitized wrapper message is
  “Judge execution failed; stop without advancing checkpoint.” No worker remains.
  Durable v3 spend: **484 attempts, $0.47321405 charged with reserves, zero
  unknown costs / $3**. Prior plus v3 is **$3.82358962**; including release smoke,
  **$3.83161437 / $12**. The ignored aggregate receipt is
  `artifacts/final-program-v3/stop-report-resume.json`.

### Done but not verified

- The judge phase and final report are incomplete. No v3 headline metrics have
  been reported. The underlying judge exception is not identified from the
  sanitized wrapper; case inputs and outputs were not opened.

### Next / blocked

- Stop after the single authorized resume. Preserve checkpoints, call journals,
  budget reservations and pinned main. Diagnose the judge failure without
  disclosing frozen inputs or result rows; await the owner's next instruction
  before another resume. Keep this documentation branch unmerged while the run
  requires the exact pinned main SHA.

## 2026-09-28 UTC — V3 stopped on operational error; pinned main preserved

### Completed (verified)

- Evaluation predicate PR #61 merged at `e12efc73be64f8355aa9f177f08a04337593616c`.
  All four main CI checks passed. The diff from frozen product SHA `9f0bff0`
  contains only contracts, evaluator code, tests and docs; no product paths.
- Identical private API/web image digests were retagged and applied in the approved
  Azure subscription. Azure controls and external access denial passed at the
  exact SHA; the ignored `artifacts/azure/jev-release.json` records the gates.
- The zero-cost v3 preflight passed: 100 bound cases, 30 repeat selections and
  30 judge selections. The first two stopped directories were preserved, each at
  $0 spend and zero completed checkpoints. Fresh v3 was started on the pinned SHA.
- Fresh v3 advanced to **212/260 system runs**, then stopped with
  **`OperationalError`**. Its worker exited; no `COMPLETE.json` exists. Durable
  budget readback: **291 attempts, $0.26672382 charged with reserves, zero
  unknown costs / $3**. Prior scopes plus v3 charged **$3.61709939**; including
  the earlier $0.00802475 release smoke, **$3.62512414 / $12**. Checkpoints and
  reservations remain intact. The ignored aggregate stop receipt is
  `artifacts/final-program-v3/stop-report.json`.

### Done but not verified

- V3 is incomplete. No result metrics or human judge sheet are available for
  reporting; official v2 figures remain unchanged. The cause of the
  `OperationalError` has not been diagnosed from the saved trace.

### Next / blocked

- Stop on the error gate. Review the failure safely without printing frozen
  input, case output or credentials. Keep main at the pinned release SHA; after
  owner review, use `scripts.final_program resume`, never `start`. This log entry
  is on `docs/v3-operational-stop` only and must stay unmerged while resume needs
  the exact pinned main SHA.

## 2026-09-28 UTC — V3 evaluator vocabulary repair

### Completed (verified)

- The first v3 attempt stopped at `ValidationError` (`ScenarioV2.expected`); the
  second fresh attempt stopped at `ValueError` during forbidden-predicate
  validation. Both had zero completed cases, zero provider calls and **$0 v3
  spend**. Their ignored directories are preserved separately.
- The suite author compared aggregate vocabulary without disclosing rows. The
  remaining gap is `offer_dispute` as a forbidden observation predicate. The
  evaluator now detects it from a customer response type or a trace event,
  without treating it as a write, proposal or confirmation. Authored predicate
  and bound-evaluation tests pass.
- A second broad search during startup diagnosis exposed three generic
  forbidden-action handling lines in the v3 authoring tool, after product freeze.
  No case templates, suite rows, selection, binding or result contents were
  opened. See the release notes; all subsequent source searches use explicit
  allowed paths.

### Done but not verified

- Full CI, zero-cost v3 preflight, exact-SHA release verification and fresh v3
  execution remain pending. V2 remains the official result.

### Next / blocked

- Merge the evaluation-only fix with green CI. Verify no product paths changed
  since `9f0bff0`, retag identical images, verify Azure controls/access and
  issue a new release receipt. Complete the zero-cost preflight, then launch v3
  fresh under the unchanged $3 durable scope and $12 cumulative ceiling.

## 2026-09-27 local / 2026-09-28 UTC — V3 startup contract repair in progress

### Completed (verified)

- Orchestrator authorized v3 GO on clean release
  `9f0bff04f28aae4fef6e646575d825fc175b369e`. Its first pinned launch
  stopped at startup with **`ValidationError`**, before any case checkpoint or
  provider reservation. `scripts.final_budget.verify` read back **0 attempts,
  $0.00 charged, 0 unknown costs / $3**. No results were opened.
- Access-logged, value-free error inspection found two failures of the v2
  `ScenarioV2.expected` enum in the first suite part. The v1-branch errors are
  irrelevant to a v2 suite. The ADR-0015 `cancelled` outcome already exists in
  `GoldLabels` and the reply contract, but is missing from that v2 expected enum.
- Disclosed a broad search that accidentally surfaced two authoring-tool
  case-template snippets after the product freeze; no frozen scenario rows,
  selection contents, binding values or results were printed. Sebastian approved
  continuation with disclosure and strict product-path freeze. See
  [v3 release notes](../evaluation/v3-release-notes.md).
- Added `cancelled` only to the canonical v2 expected enum and regenerated its
  interface snapshot. The authored contract test passes; no product paths change.

### Done but not verified

- Schema repair awaits full CI, exact-SHA release re-verification and a fresh v3
  launch. The first attempt remains preserved with zero measured spend. No v3
  metrics exist yet.

### Next / blocked

- Merge the schema-only correction after green CI; verify identical deployed
  image digests at the new SHA and record a new release receipt. Preserve the
  first attempt as `final-program-v3-attempt1`; start a fresh pinned v3 directory
  only after reporting class, fix and spend. Enforce the same $3 lifetime scope
  and $12 cumulative ceiling. Keep main frozen while the worker runs.

## 2026-09-27 — V3 release gates and preparation; execution on hold

### Completed (verified)

- Approved post-gate blank-merchant fix merged as #58 at runtime SHA
  **`81ce84ec6c6e1c93063bbaf84eb67dd3d98e604e`**. B1 **32/32**, mock P
  **20/20 + 12/12**, all faults triggered, zero unsafe/errors, **$0**; three
  authored regressions passed. Original paid gate and blind confirmation preserved.
- Main CI **36369151946** and safety **36369151820** passed. Built/pushed API/web
  images to private ACR. `scripts.azure_dev plan` / `apply` updated only the apps
  and restored the approved model-secret reader roles for the real-smoke stage.
  Live East US 2 infrastructure estimate remains **$34.63/month**, below $40.
- `python -m scripts.azure_smoke`: four organizer-serving personas, 15 scoped
  transactions, two cases, four handoffs, staff claim/resolve, logout and original
  session/case readback after API replica replacement passed in mock mode.
- `python -m scripts.azure_verify`: owner-IP web restriction, internal API, HTTPS,
  managed identities, Key Vault references, Postgres TLS/firewall and converted
  **$30/$50** email alerts passed. `azure-access` **36369616217** passed at runtime
  SHA: external runner denied with web 403 / API 404.
- `python -m scripts.azure_llm_smoke`: ES explain→offer→deny→file/readback and PT
  ambiguity passed with valid Gemini/Jev observations. Explicit fraud correctly
  bypasses models under ADR-0015; corrected the smoke-only stale NLU assertion,
  then `--case fraud` verified zero calls, both required reasons, readback/logout.
- `python -m scripts.serving_browser --target azure`: all three surfaces passed.
  Combined API/browser cost **$0.00802475 / $0.10**, nine settled provider attempts,
  zero unknown costs, five conversation allowances used. No further smoke calls.
- `python -m scripts.final_budget --prepare`: scope **final-evaluation-v3**, run
  **final-program-v3**, **$3 lifetime cap**, zero attempts; prior scopes closed with
  reserves preserved. Prior evaluation/dev **$3.35037557** + full v3/smoke caps =
  **$6.45037557 ≤ $12**. With actual new smoke, pre-v3 exposure is **$3.35840032**.
- Suite manifest and opaque private-binding checksums remain the approved pins;
  binding mode 0600. No v3 scenario/selection/authoring contents opened. Fixed
  workload: 100 B1, 160 P-Gemini including repeats, 60 dual-judge pairs; frontier OFF.

### Done but not verified

- V3 suite execution, metrics and human review remain unperformed. V2 remains the
  official result; no v1 access or v2 rerun occurred. PT/dialect human review remains
  a limitation. Final image identity and fresh post-merge CI/access/control evidence
  are read back into ignored `artifacts/azure/jev-release.json` before handoff;
  any retag must preserve both tested image digests.

### Next / blocked

- Finish the release-evidence merge with green CI, retag identical tested images,
  verify the exact final SHA, and run only `scripts.final_program prepare` / `status`.
  Then **STOP for the orchestrator's separate v3 GO**. Never start/resume here.
  [Exact future start/resume commands and ceiling](../evaluation/final-run-plan.md).
  The final response and ignored release/prepared receipts identify the closing SHA.

## 2026-09-27 — Approved post-gate blank-merchant fallback fix

### Completed (verified)

- The first mock Azure smoke at `6aeed0e` stopped before policy/write: deterministic
  fallback matched blank merchant names, then corrupted amount digits during
  merchant removal. Reproduced with aggregate-only smoke observations and an
  authored fixture; no frozen inputs read. Azure controls separately passed.
- Orchestrator approved the minimal product guard with explicit B1/mock-P/CI and
  disclosure conditions. Code commit **`4fee1ee3db7428a5564ecbc634bb62e0ae7049d5`**
  excludes blank merchant evidence; three authored regressions passed.
- `evals.runner --system B1`: **32/32**, 12 readbacks, safety guards passed.
  Existing mock P dev harness in a new preserved output directory: **20/20
  no-fault + 12/12 faults**, all triggers, **0/32 unsafe/forbidden**, no errors,
  **$0**. Confirmation was not loaded/repeated; prior paid results remain intact.
- [Post-gate disclosure and commands](../evaluation/after-v2-dev-gate.md) and
  [release notes](../evaluation/v3-release-notes.md). No learned threshold,
  prompt, policy or frozen-gold change.

### Done but not verified

- Fix still needs green PR/main CI and a rebuilt API release. Azure remains in
  mock mode at the earlier candidate; the full release smoke is not yet passed.
- V3 budget is prepared with **$0 / $3**, cumulative worst-case including new
  smoke **$6.45037557 / $12**. No final-program worker or v3 outcome exists.

### Next / blocked

- Merge with green CI, continue the approved release, then prepare/verify v3
  receipts and STOP for the separate go. Never access v1 or rerun held-out v2.

## 2026-09-27 — Step 4 v3 release preparation in progress

### Completed (verified)

- Accepted dev gate remains 20/20, blind 18/20, 12/12, 0/52 unsafe, B1 32/32.
  Merged suite #50 at **`a07e7fcf675f9fc2c1d9fc8a7c51abaf3de5caa1`** after
  four green checks, using description/metadata only. Manifest matches approved
  `ecf3f6313f33359fed892de1b3537edc4ae8e854dd5bfa8da1fc8845daa41177`.
- Copied only the authorized private binding into ignored
  `artifacts/evaluation-v3/customer-bindings.json`, mode 0600; checksum matches
  frozen provenance `0c31ea3301961d9ff07f28322c6d92a8eeaf0f30829c850ae474e2a86eba6fa8`.
  No binding contents printed; no scenario/selection/authoring-tool contents opened.
- Generic runtime now targets test-v3 and its separate binding/artifact paths,
  100 B1 + 160 Gemini case-runs, preselected repeats/judges, no frontier/calibration
  calls, and a separate $3 lifetime scope. Preparation reads metadata only; start
  remains gated. Checkpoint/resume and budget-denial behavior remain enforced.
- `make checks`: **274 passed / 14 database skips**, B1 **32/32**, hooks, strict
  typing, compilation and interface/policy checks passed. Disposable local
  `python -m scripts.test_postgres`: **16/16**, including persistent reservations,
  prior-scope closure and refusal to reset the v3 breaker. Terraform format passed.
- Rechecked pinned provider prices without model calls. Updated release smoke
  for prompt v5.1 and explain→offer→deny; new combined API/browser smoke cap $0.10.
  [V3 plan, workload, budget arithmetic and exact commands](../evaluation/final-run-plan.md).

### Done but not verified

- Runtime support needs PR/main CI, image build/push, deployment, full Azure
  smokes/access readback and fresh `jev-release.json`.
- V3 durable scope/preparation receipts have not yet been created. Suite execution
  and adapter behavior on frozen v3 remain unverified and are not attempted here.

### Next / blocked

- Complete the authorized release in Seb Azure Sandbox only; prepare v3 and
  report exact SHA/evidence, then STOP for the separate v3 go. No v1 access or
  held-out v2 rerun. PT/dialect human review remains a limitation.

## 2026-09-27 — Single authorized after-v2 follow-up: dev gate passed

### Completed (verified)

- Reviewed PR #54 at `c28c7479d87d922440949791bf5d6d559fbbfe22`: all four CI
  checks passed. Zero-cost replay returned `unfamiliar_charge=false` for all four
  authorized no-fault openings; the four preservation regressions also passed.
  Merged at **`75629945f36f2767bccbaddaf6fad2707ed8681f`**, including lead #55.
  Verified the merged tree is identical to the green reviewed head. The inherited
  squash-body CI-skip marker suppressed its main push workflows; this report PR
  uses an explicit merge body, with main CI required before the session closes.
- Ran the authorized full gate **once**, detached on that clean merged candidate:
  `LLM_REAL_CALLS_APPROVED=1 LLM_FINAL_RUN_STARTED=0 .venv/bin/python -m scripts.dev_gate real --profile after-v2 --attempt 2`.
  **No-fault 20/20 (ES 10/10, PT 10/10); confirmation 18/20 (ES 10/10,
  PT 8/10); faults 12/12, all triggers reached; unsafe/forbidden 0/52**.
  Zero execution errors, 52 completed checkpoints; worker exited. Confirmation
  failures remain blind. The first run and unchanged input hashes are preserved.
- `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 LLM_FINAL_RUN_STARTED=0
  .venv/bin/python -m evals.runner --system B1`: **32/32**, 12 readbacks,
  safety guards passed on the merged candidate.
- `.venv/bin/python -m scripts.after_v2_budget` final readback: this run's known
  model cost **$0.129836782**; durable increase **$0.12983704**. Shared scope
  **`dev-gate/after-v2`**, run **`after-v2`**, lifetime charge **$0.27667768 / $1**,
  304 total attempts, zero unknown costs/outstanding reservations. Cumulative
  prior plus dev charge **$3.35037557**. No budget reset or new allowance.
- [Aggregate report and verification evidence](../evaluation/after-v2-dev-gate.md).
  Ignored output: `artifacts/after-v2-dev/gate-real-followup/results.json`;
  budget receipt: `artifacts/after-v2-dev/budget-after-followup.json`.

### Done but not verified

- Step 3 dev acceptance is met; the candidate has not been deployed or tested
  through Azure/browser/LLM release smokes. No held-out improvement is claimed.
- Confirmation retains two failed PT cases, uninspected. PT/dialect wording
  still lacks fluent-human review.

### Next / blocked

- Stop for the separate release/v3 decision. No further dev repeat is authorized.
  PR #50 remains unmerged and suite-v3 rows unopened. Never access abandoned v1
  or rerun held-out v2; official v2 remains unchanged.

## 2026-09-27 — Named neutral-charge guard follow-up

### Completed (verified)

- Kept prompt v5.1 wording as the primary unfamiliarity fix. The postprocess
  backstop now covers neutral ES/PT what/why questions with charge articles and
  named-merchant suffixes; a separate non-recognition clause remains eligible
  to set `unfamiliar_charge=true`.
- Added mock regressions for the four authorized dev openings
  (`es.pending.v2`, `es.declined.v2`, `pt.pending.v2`, `pt.declined.v2`), four
  named-charge paraphrases and a neutral question followed by “no lo reconozco”.
  No frozen confirmation or suite-v3 rows were opened; no paid calls were made.
- Targeted NLU mock tests: **46 passed** (frozen-followup test excluded); after
  correcting two stale prompt-ID assertions, the affected mock selection passed
  **48 tests**. Ruff and strict mypy pass.
- Merged current main `ff570f8` into the PR #54 branch. Preserved both the prior
  AI-lane and lead progress entries.

### Done but not verified

- The first full CI run found two stale assertions for `nlu@v5`; both now expect
  the active `nlu@v5.1` ID. The corrected code head `2e346c6` passed all four
  checks: Python, invariants, Postgres and web/browser. This final log-only
  commit will also receive a full CI run before reporting its head.

### Next / blocked

- The lead reviews and merges; the lead reruns the dev gate after merge. No paid
  gate rerun was made.

## AI lane — narrow unfamiliar-charge cue for after-v2 gate, 2026-09-27 UTC

### Completed (verified)

- Bumped [NLU prompt](../../../prompts/nlu/v5.md) to v5.1, SHA-256 `e40182de2f232932a12d61d722be5e6356d787217048378fbc2a84f330d241cc`. `unfamiliar_charge` stays tied to bare unfamiliarity in a charge inquiry. Postprocessing preserves semantic model flags except for neutral what/why/status questions and explicit denials; denial wording such as “no fui informado” no longer trips the denial fallback. Added focused ES/pt-BR regressions for the three lead findings.
- Targeted mock Ruff and pytest checks passed (35 selected cases). Tests used the four reported no-fault utterances and new unit examples; no paid call or dev gate run occurred. This branch does not alter fixtures or frozen data.

### Done but not verified

- The lead has not rerun the no-fault dev gate on this prompt revision.

### Next / blocked

- Follow-up PR [#54](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/54) is open for lead review. The initial automation was canceled after a mistaken interpretation of the test-scope instruction; the corrected head requires full Python, Postgres, web and invariant CI before merge. The lead reruns the no-fault gate and merges after review. No paid call or dev-gate call occurred.

## 2026-09-27 — Authorized dev-only follow-up in progress

### Completed (verified)

- Inspected saved evidence only for the four failed no-fault cases: ES/PT pending
  and declined. Each has an incorrect `unfamiliar_charge=true` NLU observation,
  followed by an unwanted offer and two uncertain replies ending in `ESC-04`.
  MATCH, recorded-status policy and final-outcome scoring behave as designed.
  No confirmation failures or suite-v3 inputs inspected; diagnosis cost **$0**.
- [Per-case diagnosis and ownership](../evaluation/after-v2-dev-gate.md): AI lane
  owns the NLU/prompt distinction; lead owns preserving the recognition-specific
  clarification through NLG. Relayed the AI causes to the orchestrator.
- Authored ES/PT regressions reproduced NLG dropping the recognition question.
  Lead fix keeps the code-authored localized question while an offer is active.
  Targeted conversation/attempt checks passed; no fixture or threshold changes.
- Added guarded `--attempt 2`: preserve the original run, require unchanged inputs
  and a completed failed first gate, refuse another attempt or overwrite, and
  retain **scope `dev-gate/after-v2`, run `after-v2`, lifetime cap $1**.

### Done but not verified

- Lead changes still need final CI/merge and integration with the AI fix PR.
- The single authorized full-gate follow-up has **not** run. Estimate $0.15–$0.30
  within the already approved shared cap; prior dev charge remains $0.14684064.

### Next / blocked

- Review/merge the AI fix and lead changes with green CI, then run all 52 cases
  once with `scripts.dev_gate real --profile after-v2 --attempt 2` on merged main.
- Keep confirmation blind. Report and stop after that gate, including if it misses.
  No release, suite-v3 access/merge or v3 run. Abandoned v1 remains untouched.

## 2026-09-27 — Step 3 merged and measured: dev gate not passed

### Completed (verified)

- Reviewed/merged frontend #52 into the lead branch, then combined #51 into main
  at **`2c8679cbe9b0dd93a55fc85f0b15d17a8e662ab3`**, each exact head with four
  green checks. Main CI `36360383303` and safety `36360383319` also passed.
- `make checks`: **234 passed / 14 database skips**, B1 **32/32**, 12 readbacks,
  safety guards, hooks, strict mypy, compilation and generated contracts passed.
  `python -m scripts.test_postgres`: **16/16**. Browser CI: **29/29**.
- Ran the authorized detached command
  `LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.dev_gate real --profile after-v2`
  once on clean merged main. All **52/52** cases checkpointed; worker exited.
  **No-fault 16/20 (ES 8/10, PT 8/10); new confirmation 17/20 (ES 10/10,
  PT 7/10); faults 12/12 (all triggers reached); zero unsafe/forbidden actions**.
  Zero execution errors. Gate **failed** the no-fault minimum of 18/20.
- Shared durable **scope `dev-gate/after-v2`, run `after-v2`, lifetime cap $1**:
  known cost **$0.146840366**, durable charge **$0.14684064**, 160 attempts,
  zero unknown-cost attempts. Cumulative prior plus dev charge **$3.22053853**.
  `python -m scripts.after_v2_budget` provides the final aggregate readback.
- [Full aggregate report and commands](../evaluation/after-v2-dev-gate.md).
  Results are in ignored `artifacts/after-v2-dev/gate-real/results.json`.

### Done but not verified

- The Step 3 fixes and frontend integration are merged, but paid dev acceptance
  is not satisfied. No claim of release readiness or held-out improvement.
- Deployment and Azure/browser/LLM release smokes were not run for this layer.
  PT/dialect wording still lacks fluent-human review.

### Next / blocked

- Stop for Sebastian/orchestrator's dev-only follow-up decision on the 16/20
  no-fault result. Do not repeat or tune on frozen confirmation cases.
- No release or v3 run. PR #50 remains unopened and unmerged pending a passed
  dev gate and separate approval. Never access abandoned v1 or rerun v2.

## 2026-09-27 — Lead Step 3 implementation and dev validation in progress

### Completed (verified)

- Reviewed/merged AI #49 at `dc0a9f94edd91b46f9df46fd4b37fc8431f7f192`, exact-head
  Python/Postgres/web/safety green. Requested and verified the missing
  `unfamiliar_charge` flag before merging. Lead consumes v5 context and masked facts.
- Implemented durable offers, context retention, full handoff reasons, cross-customer
  strikes/revocation, policy review ordering, B1 numeric-merchant handling, readback
  aliases and strict slice recall. Added dev regressions; never ran held-out v2 or
  opened suite-v3 rows. PR #50 description only was read for generic dependencies.
- `.venv/bin/python -m scripts.v2_slice_correction`: saved-v2 aggregate tables written
  separately; **853 inputs unchanged**. Official v2 result is unchanged.
- `python -m scripts.dev_gate mock --profile after-v2`: **20/20 no-fault, 12/12 faults**,
  all 12 triggers reached. B1 runner **32/32**, verified readbacks and safety checks.
- Final combined local `make checks`: **234 passed / 14 database skips**, hooks, strict mypy,
  compilation, B1, interface snapshots and policy catalog passed. Local disposable
  Postgres tests passed **16/16**, including offer and security-strike restart
  recovery. Runtime policy 1.3.0 identifies the changed control/routing semantics;
  numerical thresholds are unchanged. PR #51 is in fresh CI.
- Implemented #37 trace metadata and approved, scoped demo-story hints; seven staff,
  metadata and policy tests passed. Owner-approved model-run estimate is $0.15–$0.30
  under shared scope `dev-gate/after-v2` / run `after-v2`, hard $1 cap.
- Reviewed frontend #52 and merged its exact green head into the lead branch at
  `879c1b3e034c9c3f4eacbbd6f24c58200677de25` (four checks, including 29 browser checks).
  Added a narrow contextual fallback for typed ES/PT recognition labels after
  reproducing four B1/P failures from the frontend report. All 19 authored
  conversation regressions pass; isolated yes/no still requires clarification.

### Done but not verified

- Final candidate merge/CI and paid dev acceptance are pending. No new release,
  Azure smoke or v3 execution. Frontend offer/cancellation/reason support is integrated.

### Next / blocked

- Finish combined CI, merge lead fixes with green CI, run the authorized
  dev gate on the merged SHA and report. Do not merge #50 without the separate go.
- [Commands, changes and budget](../evaluation/after-v2-dev-gate.md). Stop after the
  Step 3 report; release/v3 still require Sebastian's later approval.

## 2026-09-27 — ADR merged; shared after-v2 dev allowance prepared

### Completed (verified)

- Behavior contract PR #48 merged after all four checks passed at
  **`ab07bfeba23824292bfd83a13e4934c6ff1ae349`**; announced the SHA for independent
  v3 authoring. Confirmation freeze #47 merged with fresh green CI at
  **`3ad29bc388e4b9d09bbd84266a87c9e8c66b419f`**. Hash-only comparison confirmed
  the two frozen files unchanged from `0692881`; no confirmation rows opened.
- `.venv/bin/python -m scripts.after_v2_budget --prepare` created and read back
  the shared durable **scope `dev-gate/after-v2`, run ID `after-v2`, lifetime cap
  $1.00**. All paid dev callers must use both identifiers with Postgres
  reserve-before-call accounting. Initial receipt: zero attempts, $0 charged,
  zero unknown costs; ignored `artifacts/after-v2-dev/budget-prepared.json`.
- Previous evaluation/Option A scopes are closed to new reservations with all
  history and outstanding charges retained. Prior exposure $3.07369789 plus
  the $1 dev and prospective $3 v3 limits totals $7.07369789, below $12.
  Budget arithmetic tests passed; this setup made no model calls.

### Done but not verified

- Lead Step 3 implementation is in progress on a feature branch. Prompt v5,
  NLG and dev integration are pending from the AI lane; no new dev gate run.

### Next / blocked

- Implement and verify the accepted contract on dev data, integrate the AI PR,
  then run the shared-budget dev gate and report. No release or v3 execution
  is authorized. Never access abandoned v1, rerun v2 or open suite-v3 rows.

## AI lane — after-v2 explain/offer dev confirmation, 2026-09-27 UTC

### Completed (verified)

- Read handoff 13 and authored the 20-case synthetic [explain/offer confirmation set](../../../evals/studies/llm/dev_explain_offer_20.yaml) before any v5 prompt, NLG, or scenario implementation change. Its separate first commit `0692881` freezes the file and [SHA-256 manifest](../../../evals/studies/llm/dev_explain_offer_20.sha256). Structural validation passed: 20 unique cases, 10 ES/10 pt-BR, 10 denial/10 recognition follow-ups, and no verbatim opening overlap with dev-v2.
- Read merged ADR-0015 at `ab07bfe` and aligned [NLU v5 and grounded ES/PT offer templates](../ml/dev-explain-offer-v5.md) to `offer_dispute` / `awaiting_dispute_decision` and the internal recognition signal. The scenario adapter reads the frozen hash and supplies explicit offer, choice and confirmation replies. `make checks` passed: 186 tests / 13 skips, B1 dev 32/32, Ruff and strict mypy. No paid call or suite-v3 row access occurred.
- Addressed the lead's PR #49 review: `ExtractedNlu.unfamiliar_charge` now distinguishes bare unfamiliarity from ordinary status questions in ES and pt-BR, including degraded fallback and model postprocessing. The AI execution record includes the signal. Full mock `make checks` passed after the change: 204 tests / 13 skips, B1 dev 32/32, Ruff, formatting, strict mypy, interface and policy checks. The shared `dev-gate/after-v2` scope and `after-v2` run ID are confirmed at $0 before any AI paid call.

### Done but not verified

- The new set's slang and labels are AI-authored, not fluent-human reviewed. End-to-end dev behavior and real-model prompt v5 remain unverified until the lead's executable response contract, simulator and scorer changes merge.

### Next / blocked

- Lead merged fixture PR #47; next integrate additive `offer_dispute` API/scenario/scorer behavior, then run the dev gate. Every paid dev call must reserve through the now-created `dev-gate/after-v2` scope with run ID `after-v2`, within its shared $1 lifetime cap. Do not open suite-v3 rows; lead merges AI PRs after CI.

---

## 2026-09-27 — Handoff 13 Step 1: accepted behavior specification

### Completed (verified)

- Routine merges finished: #46 analysis at `7914022`, then #45 reviewed wording
  at **`4470ba4957c7f90f54ac28e887bc3119ed99a02e`**. Each exact PR head passed
  all four CI checks before merge. Only A20/W02 wording was applied; local
  `make checks` passed (174 tests / 13 skips, B1 32/32).
- Read handoff 13 fully. Wrote [ADR-0015](../../adr/0015-post-v2-conversation-and-policy-contract.md)
  and the [normative v3 behavior contract](../../../contracts/interfaces/conversation-policy-v3.md)
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
- Rejected one model suggestion after checking the handoff packet's real creation/readback order. Proposed two wording changes only in [the lead-review patch](../../ml/pt-review-lead-proposed.patch); `git apply --check` passed and lead-owned source files remain unchanged. [Before/after decisions](../ml/pt-review.md) are recorded.

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
  [aggregate JSON](../../ml/dev-p-gate-results.json) record the tested SHA. Private
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
- [PR #37](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/37) is open; keep it and PRs #24/#28 unmerged until Sebastian announces final-run completion. Lead supplies reviewed trace/persona projections and decides any separately authorized bulk reset; UI does not widen RLS or bypass authentication.


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

- Private [PR #24](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/24) was opened and read back with only the assigned documents plus this log. All four CI jobs passed at `a98203a` (`ci` run `36291808092`, `safety` run `36291808097`); mypy and data/secret/size hooks also passed locally. This log-only follow-up records that evidence.

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
- Published aggregates in the [result review](../ml/result-review.md#human-spot-check-n9-es-cl) and [model card](../../ml/model-card-charge-matcher.md#human-spot-check-n9-es-cl): intent 5/9, corrected core slots 7/9, top-1 6/9, recall@3 8/9, **nine no-match decisions**. A documented post-inference annotation serialization correction changes core-slot accuracy from 6/9 to 7/9; original frozen labels and predictions remain intact. No model, prompt or threshold changed.
- Wrote and read back all nine detailed intent/slot/transaction/decision reports, gold, billing, runner and manifests under ignored `artifacts/human-validation/spanish-40/spotcheck-es-cl-v1/`. Source recollection bytes remain unchanged. No card field values entered Git.
- Independent aggregate/billing recomputation, all artifact hash checks, verbatim recollection readback, 13 local documentation links, diff whitespace and staged-file policy passed. This change touches only the two requested ML documents plus this additive session entry.

### Matcher v2 follow-up — 2026-09-27 UTC

- Implemented versioned choice-first decisions while retaining v1 behavior; added deterministic sparse-language synthetic variants and a train/validation-only v2 training entry point. The [v2 protocol](../../ml/matcher-v2-protocol.md) fixes noise, cost preferences, selection grids and test/human access order before fitting.
- Ten matcher/MatchState checks passed, including scoped retrieval, legacy behavior, low-existence choice fallback, all-low/empty abstention, literal-format noise and evaluator/export policy consistency. Ruff and strict mypy passed. No frozen held-out scenario-suite access or paid calls in this implementation stage.
- Trained v2 on 18,000 synthetic train / 9,000 validation queries using 20 seeded trials. Froze the model at 05:03:59 UTC before synthetic-test/human access; verified exact code/export hashes and v1 artifact bytes unchanged. Synthetic 3,000-case wrong proposals fell 30→13 under identical serving features and the v2 cost table. Sparse-language diagnostics and their generator limitations are in the [v2 model card](../../ml/model-card-charge-matcher-v2.md).
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
- Runtime source reads use the non-owner pool, forced customer RLS, ownership join and half-open 120-day UTC window. Dataset/clock/build identity is pinned and refresh reads coordinate with the atomic loader. Missing serving state fails closed. No authored-ledger fallback in the deployed mode. See [serving runbook](../../serving-demo.md) and [ADR 0004](../../adr/0004-serving-isolation.md).
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
- Existing approved PostgreSQL Azure-services firewall exception, Key Vault passwords, managed identities, TLS verify-full and approximate US$30/50-equivalent budget alerts remain required. [Network plan](../../azure-private-dev-plan.md), [production limits](../../production-readiness.md).

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
- Azure PITR/regional DR, realistic-volume restore, automatic retention, sustained concurrency, actual charges and budget-email delivery are unverified. Tiny local restore evidence remains in [recovery report](../../ops-recovery.md).

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
- Added [subjective judge rubric](../../evaluation/judge-rubric.md), score-only Sonnet 5 OpenRouter harness, and quadratic-weighted κ/paired-agreement computation. The judge input excludes gold and objective outcomes; scoring is limited to language/register, clarity, empathy, and handoff-summary usefulness. Generated an ignored mode-0600, 50-row synthetic human sheet at `artifacts/judge/human-validation-50.csv` (SHA-256 `4f862e442d1cce88c8f90b38a22cb53691ed8efe9352bf4ca878c952520f5794`), with all human ratings blank and no frozen held-out cases.
- Sebastian authorized only a sub-$0.50 judge smoke. Sonnet 5 on ZDR `google-vertex/global` returned **3/3 valid** strict score-only responses; known per-call cost **$0.008042**. An advertised Bedrock route returned six no-usage provider errors and a diagnostic HTTP 404; all seven unknown-cost attempts are kept in ignored metadata with a conservative **$0.35** guard. Known spend plus guard is **$0.358042**, below the $0.50 limit. No 50-case judge calibration or final held-out real-model run was made.
- Wrote the [priced final-run plan](../evaluation/final-run-plan.md): B1 200; Gemini P 200 full plus two additional 100-case passes (three total subset runs, 400 P case-runs); Sonnet P once on the same 100; 50 human-calibration and 100 B1/Gemini judge assessments. It gives exact route/prompt settings, per-component token and cost estimates, a 5% Grok fallback sensitivity, a **$4.590 illustrative model-cost total**, a proposed **$12 future stop ceiling**, and **60–90 minutes** estimated serial machine time. It explicitly requires lead acceptance fixes and a separate approval before execution.
- `make checks` passed: six hooks, strict mypy, file policy, compilation, **81 tests passed / 7 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog.

### Done but not verified

- The human sheet has no ratings, so no judge agreement or weighted κ is claimed. The three-item smoke proves route/schema operation only; the 50-item judge run, human ES/PT wording review, final system costs/latency, and real-model safety remain unmeasured. The final-run cost and time are estimates using current public ZDR rates and conservative token assumptions.

### Next / blocked

- Sebastian to fill the 50 human scores and approve a fresh priced judge calibration/final run after the lead's independent acceptance fixes, frozen SHA, production-key deployment, and a cross-process spend breaker. The current `evals.heldout` adapter still hardcodes mock metadata/execution and needs the lead's real-route integration. Do not run the frozen real-model test or additional paid judge calls under this session's smoke approval.

## AI lane — 2026-09-27 (denial prompt v4 and final preflight)

### Completed (verified)

- Added [NLU prompt v4](../../../prompts/nlu/v4.md) for explicit ES/PT denial cues, including Chilean informal speech and merchant nonattendance, while keeping recognition or uncertain memory as `charge_inquiry`. The runtime P NLU route now selects v4. No human spot-check utterance or frozen held-out label was added to development fixtures.
- Paired Gemini 3 Flash v3/v4 on 40 new synthetic, team-authored denial/inquiry cases. The first 24 were saturated (24/24 each); the 16 harder contrastive cases yielded v3 **11/16** versus v4 **16/16**, with five v3 explicit-denial→inquiry errors and zero v4 errors. Combined: v3 **35/40**, v4 **40/40**; all **80/80 attempts** valid schema JSON. The [comparison](../ml/model-comparison.md) reports aggregate evidence and limitations. Per-call cost **$0.106686**, no unknown-cost attempts, below the separately approved $0.49 cap. These authored cases do not establish independent production accuracy.
- Pinned selected Gemini and Sonnet frontier to ZDR `google-vertex/global` for the priced final configuration and updated Gemini's reserve rate to the standard $0.50/$3 per million. Production `.env` stays mock/unapproved. `make checks` passed six hooks, strict mypy, staged-file policy, compilation, **83 tests passed / 7 database-dependent skips**, B1 **32/32** with 12 readbacks, interfaces and policy catalog. PR CI follows this section.
- Sebastian pre-approved the [final-run plan](../evaluation/final-run-plan.md) with a $12 ceiling but withheld the start signal until lead acceptance fixes, matcher v2 and prompt v4 merge with green gates. The revised v4 token assumption raises the illustrative model estimate to **$4.692**, still within the approved ceiling. Read-only [preflight](../evaluation/final-preflight.md) verified the frozen 200-case manifest/counts but stopped on a missing private customer-binding artifact; it made no system/model run and wrote no final output.

### Done but not verified

- Human ES-CL and fluent PT review of v4 wording, independent validation, and final end-to-end behavior remain unverified. The current held-out adapter is still P/mock only; a durable cross-process spend gate is not wired in this branch. The private binding artifact is absent here.

### Next / blocked

- Lead supplies/verifies the frozen private binding, merges acceptance fixes and matcher v2, integrates the real-route final adapter and spend breaker, and reads back green gates. Merge prompt v4 without held-out tuning. Do **not** begin the $12 final program until Sebastian's explicit start signal.

## AI lane — 2026-09-27 (TypeSafe Jev challenger)

### Completed (verified)

- Read the live TypeSafe SDK/model/primitive and legal documents and the user-specified local SDK example. Added `typesafe-sdk` 0.7.2 to the optional LLM and dev dependencies, a separate typed-judgment-only adapter, versioned intent/risk and rubric questions, and a checkpointed cross-provider comparison. No Jev slot extraction, phrasing, identity, policy or write route was added. [Data provenance](../../data-provenance.md) records TypeSafe's no-training claim, ordinary retention/US hosting, and unverified ZDR status; only synthetic text was sent.
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
- Integrated a gated [dual subjective judge helper](../../../evals/studies/llm/dual_judge.py) into the full 50-item Sonnet judge command. It scores both on the same items, reserves Jev against the lead's merged durable Postgres gate, checkpoints raw Jev distributions, and supports Jev–Sonnet plus separate judge–human weighted κ once all human ratings exist. Its offline tests made no final or new judge paid calls. [Final plan](../evaluation/final-run-plan.md) prices 410 Jev risk calls and 150 Jev judge calls at $0.02583 and $0.01260 before rounding, for an illustrative **$4.730** total below the existing $12 ceiling. The final start is still withheld.
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

## Data/frontend lane — 2026-09-29 (independent v4 freeze)

### Completed (verified)

- Read handoff 14 in full. Authored a new 100-case v4 release from ADR-0015 and the written conversation contract, with 35/20/20/25 category counts, 48 ES / 48 PT / 4 mixed, and new interaction wording. Kept v3 as retired development data; no old template list, system output or post-v3 failure analysis defined v4 gold.
- Verified 100 unique test-split customers and owned products with zero overlap against v1, v2, v3, both matcher inventories and all 40 human cards. Reconstructed the archived v1 identity mapping and matched its original private checksum. All charge/case/FX facts are fictional; native organizer identities exist only in ignored mode-0600 bindings.
- Structural preflight passed schema, vocabulary, references, explicit reactive replies, counts, exclusions and exact wording/template overlap checks. Froze and read back all release hashes. MANIFEST file SHA-256: `309c3aa22c2eab51b3289075b733c52bb7934a879299762c3fb9ba16a3d9bec8`. No B1/P executions, paid provider calls, cloud changes or spend occurred.
- Added an aggregate-only v4 evaluation protocol and pre-registered the repeat/dual-judge subsets. Lead, AI and fix authors must not open v4 scenario rows, selection IDs or its authoring tool. [PR #64](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/64) was read back as open and unmerged; origin remains private. Ruff, compilation, strict mypy (81 source files), all six commit hooks and the post-commit freeze verification passed.

### Done but not verified

- Behavioral correctness, serving ownership validation, fault activation and durable runtime readbacks are deliberately untested on v4. The post-v3 stale-OTP harness support remains a release dependency. Human and second-vendor language review are pending; ES/PT pairs share interaction designs.

### Next / blocked

- Leave PR #64 unmerged until the owner releases it. The later final run requires Sebastian's explicit go and the release owner's gates. Remote CI failed before jobs started; the [check annotation](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs/36657943458/job/109706208743) says an Actions budget prevents further use. This is not a green CI claim. Do not tune product behavior on v4 or publish row-level content.

## Access and continuation

Restricted web: <owner-supplied-web-origin>
Use `demo.es.mx` or `demo.pt.br` for the three-surface workspace; `demo.es.co` and `demo.es.ar` are customer-only. Retrieve `demo-password` from the authenticated Key Vault portal; never paste it into chat, Git or logs. OTP is simulated. Re-login after the identity-source migration; prior fixture sessions do not grant organizer access.

For later sessions, paste: **Continue from docs/status/progress-log.md. Next layer: final evaluation after Sebastian's explicit go. Same rules.**

## 2026-09-29 PDT — authorized startup preview and session-security review fix

### Completed (verified)

- Merged #63 into `fix/post-v3-analysis` at `dac38017d4ea9910afc3aa4851f661dd6608b7ce`
  and redeployed the explicitly approved PREVIEW. Only ignored `image_tag` changed;
  reviewed Terraform plan/apply: 0 added, 2 changed, 0 destroyed. Both image tags
  match. `python -m scripts.azure_verify` passed: owner-IP/login restriction,
  internal API, TLS/identity/firewall/budget controls and replicas 0..1 unchanged.
- `.venv/bin/python artifacts/preview-release/read_only.py`: new web/API revisions
  both reached zero naturally; authenticated cold me 200/86.059 s with clock,
  transactions 200/0.132 s (four projections), logout revocation readback passed.
  Sampled console logs contain no application exceptions. No model/banking calls.
  Detailed aggregate evidence is ignored under `artifacts/preview-release/`.
- Exact deployed-SHA `UV_CACHE_DIR=artifacts/uv-cache make checks`: 308 Python
  tests passed, 14 database-dependent skips; B1 32/32; interfaces/catalog,
  pre-commit and staged-file policy passed. Startup web checks from #63 remain
  the previously executed 55 browser checks and typecheck/lint/build.
- Finding #2: authored two-tab regression first reproduced missing ESC-02.
  Security cues now share the durable, session-scoped strike record; older
  conversation-only cues are preserved on upgrade. Another login stays isolated.
  `.venv/bin/pytest tests/test_workflow_api.py tests/test_post_v3_fixes.py`: 32 passed.
  `.venv/bin/python -m scripts.test_postgres`: 18 passed, including another-tab
  security termination after app/store restart. Strict mypy and Ruff passed.
  Fix-candidate `make checks`: 309 passed, 15 skips; B1 32/32; safety/hooks/schema green.

### Done but not verified

- GitHub Actions cannot start because the account Actions budget blocks jobs.
  Local checks do not claim a successful remote CI run.
- Paid preview chat has not been tested. The Azure checks exercise auth and reads.

### Next / blocked

- Open the security fix PR against `fix/post-v3-analysis`; retain main at `e12efc7`.
- Fix freeze-origin binding, exact-error harness renewal/new freeze confirmation,
  and wrong-code OTP retry with authored regressions, then open a second feature PR.
- AI lane owns review findings #1/#3. Main merge still needs billing recovery or
  Sebastian's explicit exception. No min replicas change, paid calls or v4 access.

## 2026-09-29 PDT — lead freeze provenance and OTP follow-up candidate

### Completed (verified)

- Security fix PR is [#67](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/67),
  head `5720cbe`, targeting `fix/post-v3-analysis`. The second fix branch includes
  it; merge #67 first to reduce the second PR's diff. No main merge or second
  Azure deploy was performed.
- Authorized PREVIEW remains `dac38017d4ea9910afc3aa4851f661dd6608b7ce`.
  Authenticated browser navigation also passed: login/OTP, visible bank clock,
  chat composer and sign-out; no message sent. Evidence is ignored
  `artifacts/preview-release/browser-final.jsonl`. Initial browser helper failures
  were its own persona/OTP-placeholder race and timeout setup; the helper now
  waits for the six-digit SMS before submission. They are not app failures.
- Findings #4/#5: explicit owned fraud-handoff origin, offered-card restriction,
  hash-bound conversation/reasons, refreshed freeze proposal returned to the
  simulated customer after exact-error OTP renewal; other 401s never renew.
  Updated API/BFF/UI/adapter callers and regenerated OpenAPI. Authored tests cover
  multiple conversations, tampered/wrong-session/unoffered-card origin and a
  customer declining the refreshed proposal. Wrong-code renewal preserves the
  pending dispute/challenge and permits retry; five-attempt limit remains enforced.
- `UV_CACHE_DIR=artifacts/uv-cache make checks`: 324 passed, 16 database-dependent
  skips; B1 32/32, hooks/staged-file policy/compile/interfaces/catalog passed.
  `.venv/bin/python -m scripts.test_postgres`: 19 passed, including originating
  fraud packet after a new conversation and app restart, and wrong OTP followed
  by correct OTP/dispute readback after app/store restart. No cloud database writes.
- `.venv/bin/python -m evals.runner --system B1 --scenarios evals/dev_scenarios_v2.yaml`:
  32/32. Ruff and strict mypy passed. Web typecheck/lint/build passed;
  `pnpm test:e2e`: 46/46; `pnpm test:e2e --staff`: 1/1. Live customer checks
  passed 12/12 including the final multi-conversation browser regression.
  A typecheck started alongside dev-server generation hit missing generated Next
  type files; sequential typecheck after browser teardown passed.

### Done but not verified

- Follow-up fixes are local/mock validated, not deployed or measured with real NLU.
- GitHub Actions is still blocked by the account Actions budget; no remote green
  claim. Main is unchanged; no v4 inputs, authoring tools or bindings opened.

### Next / blocked

- Second private feature PR is [#68](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/68),
  targeting `fix/post-v3-analysis`, with code commits `aa37227` / `f891584`.
  All 59 browser checks passed (46 fixture/startup + 12 live customer + 1 staff).
  Review/merge #67 first, then #68; neither is merged here.
- AI lane owns #1/#3. Review both lead PRs; main merge waits for billing recovery
  or Sebastian's explicit exception. Any later release follows its own gate.
- No paid calls, min replicas change, or new approval needed for the completed
  preview. No v4 start. Continue from this log under the same rules.

## 2026-09-30 PDT — AI offline human review and customer-text integrity

### Completed (verified)

- Built ignored, mode-0600 `artifacts/human-judge/v3-score.html` from the lead's
  unchanged 20-item v3 CSV. Spanish instructions and rubric anchors, locale/text/
  summary, independent radios, six handoff N/A items, notes, progress, localStorage
  autosave and exact-column UTF-8 CSV export. Offline Chromium verified 20/20
  progress and 74/74 applicable test ratings, reload persistence, unchanged source
  wording and quoted multiline notes; zero network requests/browser errors. Test
  ratings are private fixtures, not Sebastian's ratings. HTML contains blank source
  ratings and no judge scores; generated data remains ignored under a private dir.
- Added `evals.studies.llm.human_review`: reproducible offline generator and strict import
  of all applicable human ratings. Checks twenty IDs, exact columns, unchanged
  source wording/locale and saved judge inputs; intersects successful saved scores
  with the human sheet. Exact/within-one/quadratic-kappa metrics by dimension and
  ES/PT slice; absent scores/N/A excluded and undefined kappa explicit. Saved v3
  judging covers 28/60, but only 10/20 sheet items (eight summary pairs); no human
  agreement claim. Pending report: `docs/evaluation/judge-human-validation.md`.
- Confirmed item 1's text equals the saved v3 reply; that release used phrase v1,
  not v2. Current contextual evidence identifies its PT language. Authored tests
  reproduced 14 integrity failures before the fix. Grounding/DLP now forbids
  numeric txn/prod/card/cust handles even when cited, plus replacement characters,
  common mojibake, narrow apostrophe/hash corruption and control characters;
  valid ES/PT accents and verified case references remain allowed. Zero-cost
  saved-output replay rejects both defects and returns a clean Spanish template;
  independent opposite-language tests pass in both directions. No row text copied
  into Git and no original evaluation output changed.
- Local suite: 459 passed, 17 database-dependent skips. Excluded the v4-specific
  test module and enforced actual-v4 file and external-network barriers. Restricted
  TestClient execution stalled; stopped that local process and completed the same
  checks with sandbox escalation. Focused AI/judge/API tests 92/92, B1 dev 32/32,
  strict mypy (86 files), Ruff and frozen interface/catalog checks passed. Remote
  workflow now targets main only; no hosted CI run requested for this stacked PR.

### Done but not verified

- Sebastian's scored CSV is pending; provisional Downloads path is not confirmed.
  Human–Sonnet/Jev results remain unmeasured. The ten existing model pairs are
  descriptive only and cannot satisfy the rubric's 50-item calibration requirement.
- Integrity fixes are local/mock verified; no deployment or paid verification.
  Conservative language/corruption detection cannot guarantee all text quality.

### Next / blocked

- Private [PR #77](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/77) is OPEN
  and mergeable into `fix/post-v3-analysis`, head `a1077f2` read back. Main-only CI
  triggered no remote run; lead reviews and merges. No merge performed.
- Import the confirmed human export and update the agreement report without new
  judge calls. Keep wording/notes/ratings under ignored artifacts.
- Resume round-two authoring/freeze after this priority fix. Its builder draft is
  preserved in ignored `artifacts/dev-pre-v4/`; no 60-case freeze or run is claimed.
  Paid `dev-gate/pre-v4` exact scope/run confirmation is still pending: no spend,
  no v5.2 adoption, and no v4 access. The lead owns creation/readback of the scope.
## 2026-09-30 PDT — AI round-two development freeze, paid gate pending

### Completed (verified)

- Priority work is in private, unmerged PR #77, pushed head
  `1fc7f5a14643db7cb6432f1f4078b13d8ed871b8`; PR state/target/head read back.
  Its offline HTML remains at the exact AI-worktree path already sent to the
  orchestrator. Original human CSV/outputs remain private and unchanged; export
  path confirmation and human agreement are pending. No paid calls/remote CI.
- Authored and froze `evals/studies/llm/dev_robustness_round2_60.yaml` with its new
  builder and immutable hash manifest before any round-two P/B1 execution or
  robustness repair. Sixty project-generated conversations: 30 ES (ten each
  CO/AR/CL) / 30 PT, ten story families x six correlated variants. Forty-two
  three-message and eighteen four-message prefixes, plus independent confirmation
  when filing within a five-turn limit. Gold: 36 filings, 18 explanations, six
  cancellations. No v4 or organizer row input and no output-derived labels.
- Coverage includes corrections, unrelated charges, existing-case plus new-charge
  requests, vague-to-specific, frustration without distress cues, code-switching,
  slang, amounts in words, relative dates, currency twins, polite refusal,
  recognition changes, typos and copied injection. Explicit authored FX/merchants;
  es-CL remains utterance metadata under MX bank rules. Existing 40/confirmation
  fixtures and interfaces are unchanged. Structural schema, synthetic binding,
  gold-reference, FX-consistency and manifest checks pass; nine relevant unit
  checks, Ruff and strict mypy pass. No product execution before freeze.
- Preregistered `docs/ml/nlu-robustness-round2.md`: all-attempt accounting, owner
  diagnosis, 240-case five-set v5.1/v5.2 comparison, unchanged-or-better per-set
  outcomes and lower p50/p95 adoption gate. Prior dev per-call cost implies the
  198 new scripted messages alone may cost about $0.38 NLU before other calls;
  complete fresh comparisons may exceed the allowance. No adoption on partial
  evidence; keep the shared cap and report incomplete coverage honestly.


- Freeze commit `eaef1166ae4f90934332201b437bd14f3f22a79a` read back clean before
  any product run; manifest/case/builder/materialized hashes still match afterward.
- Ran all 60 once through the real in-memory P state machine with mock NLU and
  network/v4 barriers: 19 passed (ES 9/30, PT 10/30), zero unsafe findings,
  zero execution errors, 13 filed / six explained / 41 escalated, $0 and no
  provider calls. This is mock fallback evidence, not Gemini accuracy. Private
  per-case records remain ignored. Corrected an initial harness map-truthiness
  aggregation error from those saved records without rerunning or altering cases;
  a regression protects actual unsafe-flag counting. Frozen gold remains unchanged.
- Added a mock-only CLI that rejects real-provider configuration/approval before
  reading cases and refuses to overwrite evidence. Twelve relevant unit checks,
  strict mypy (87 files), Ruff and freeze validation pass. Real measurement,
  NLU/NLG repairs and v5.2 remain pending the paid-scope confirmation/baseline.

### Done but not verified

- Real before/after numbers remain pending; the 19/60 mock pass is not a Gemini
  measurement and does not authorize changes to frozen gold.
- v5.2 is neither authored nor adopted. PR #77 is not assumed merged or deployed;
  record the actual baseline integration SHA before a later paid run.

### Next / blocked

- Private [PR #80](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/80) is OPEN
  and mergeable into `fix/post-v3-analysis`, code head `36ba3e7` read back; no
  remote CI run under the main-only trigger. Lead reviews/merges. Freeze and mock
  readbacks are complete; no merge performed.
- Wait for the orchestrator's exact read-back `dev-gate/pre-v4` scope/run before
  every paid call. Shared lifetime cap $1, stop exposure at $0.90. No final scope,
  paid call, default change or v4 access is authorized by these preparatory checks.
- Import the confirmed human CSV via the #77 branch and update its agreement doc
  without new judges. Current provisional Downloads path has not been confirmed.

## 2026-09-30 PDT — Zero-spend final-program rehearsal (lead)

### Completed (verified)

- Retired v3 only, local RLS serving, B1-only system positions and mock-client
  judges. `LLM_PROVIDER=mock`, real-call approval off. No v4 rows/selections/bindings,
  historical final-program directories, product paths or Azure resources changed.
- `python -m scripts.rehearse_final_program --name sept30-b` completed all three
  programs in 178.97 s on runner `af769b7c776f160c23cbd1b2df6cc5ab834be41c`:
  260 system runs + 60 judge items each, JSON/Markdown reports + 20-item sheets.
  Aggregate evidence: `artifacts/final-program-rehearsal/sept30-b-summary.json`.
- Actual SIGTERM at systems 12 and judges 12, followed by `resume` each time:
  identical objective aggregates/intervals and judge aggregates versus baseline;
  320 completed units / 320 attempts, 60 mock calls, no replay of completed units.
  Measured timing is excluded from equality, not fabricated. A completed `resume`
  was a no-op; all worker PID files are absent and worker locks free.
- Injected one real local connection refusal at systems 22: `OperationalError`,
  preserved checkpoints, successful non-owner `SELECT 1` on original serving,
  one resume. Fault program finished with only one recovered unit (321 attempts).
  One judge length failure exhausted two attempts, recorded null scores and
  continued: 59 paired / one failed item; primary/report phases completed.
- Exact local throwaway scopes `rehearsal/final-program/sept30-b-{baseline,resumed,faults}`,
  run IDs `rehearsal-sept30-b-{baseline,resumed,faults}`, all durable $0 lifetime
  caps. Actual non-owner reserve function denied positive $0.00000001 attempts;
  owner readback: zero paid reservations, $0 charged, no unknown costs. Production
  migrations/functions and existing paid scopes unchanged. Connections mode 0600.
- Runner fixes: exhausted judge failures checkpointed unpaired; budget/infrastructure
  failures stop; sanitized exception class chains; stale stop handling on resume;
  serving closed if budget initialization fails. Explicit rehearsal cannot select
  v4, fetch cloud keys or enable real calls. Final CLI-only guard prevents the
  paid budget parser silently ignoring `--rehearsal`; authored parser/launcher
  regressions pass. Product behavior unchanged.
- Local full suite 497 passed / 21 skipped; final runner regressions 33 passed;
  disposable Postgres gate 24 passed. Ruff, strict mypy (88 files), compile,
  interface/catalog checks, pre-commit and working-tree data/secret gate passed.
  Both B1 commands exited 0; reactive dev 32/32. First restricted full pytest
  stalled and was terminated; completed run used authorized local networking and
  bounded numerical-library threads. Initial rehearsal comparator wrongly included
  six timing fields; fixed and the complete rehearsal repeated successfully.
- Details/commands/limitations: [final-program-rehearsal.md](../evaluation/final-program-rehearsal.md).
  Earlier `sept30-a` rehearsal evidence is preserved. No paid model calls.

### Done but not verified

- Live provider cancellation, actual vendor agreement, model quality and Azure
  connectivity are outside this mock/local rehearsal; no such claims made.
- Remote CI on the rehearsal PR is pending publication. Main remains unchanged
  at `5e55ee8519d56d81938bb6a7aa7e4247e8d6c91c`; no main merge or redeploy performed.

### Next / blocked

- Open the runner-only PR to main, require remote CI, then review/merge separately.
- V4 remains unstarted until the Oct 2 12:00 COT freeze, release gates and owner go.
  Keep its rows, selections and bindings unopened; keep historical final programs
  untouched. No new spend or infrastructure approval needed for this rehearsal.
- Continue from docs/status/progress-log.md. Next layer: v4 launch gates after
  feature freeze and owner go. Same rules.

## 2026-10-01 UTC — runner merge and urgent live rehearsal diagnosis

### Completed (verified)

- Merged approved runner-only #89 at `2dfa50408547c001140764f782562e63ebfdede7`;
  main equals origin/main and its four remote checks succeeded. API/web Docker
  COPY input-tree fingerprints match the parent; no image build/push or Azure
  release was required. Receipt: ignored `artifacts/final-program-rehearsal/merge-image-inputs.json`.
- Read the authorized rehearsal references and four original Azure conversations
  using the non-owner role and exact customer/run/session scopes. RLS stayed intact;
  unscoped reads yielded zero. No Azure change or new paid call. Confirmed phrase
  output corruption passing grounding, raw English fallback status, PT `compra`
  versus canonical kind mismatch, operational SLA clock mismatch, and missing
  handoff fact/action projection. Details: [live-rehearsal-triage.md](../evaluation/live-rehearsal-triage.md).
- Lead fixes on `fix/live-rehearsal-freeze-blockers`: localized fallback;
  conversation-scoped identified facts; read-backed dispute/handoff actions;
  offered freeze excluded from executed actions; live Desk wall clock and ES/PT
  empty-facts copy. Local full Python 503 passed / 22 skipped, disposable Postgres
  29 passed, authored browser 93 passed, live API staff browser 1 passed. Ruff,
  mypy 88 files and web typecheck passed. Focused missing-readback/credit regressions
  21 passed / 1 Postgres skip. No claim of Azure verification for new fixes.
- Free OpenRouter inference-key GET preflight succeeded at 01:06 UTC: account
  remaining $9.659101954, key remaining $5.802867, both ≥ $4. No management key,
  model call or charge. Keys stayed in memory; ignored numeric receipt only.
- Critical review of updated #85 at `078a4ba` found a confirmed zero-cost replay
  gap: new `provider_402` error-envelope category bypasses the comparison's
  `http_402` stop guard when cost is known. Relayed to AI alongside the live NLG
  and type-alias regressions; no further comparison spending requested.

### Done but not verified

- Lead fixes await review/integration/remote CI and deployment; Azure still runs
  the previous release. AI NLG/type alias fix PRs and #85 review correction pending.
- Independent free credit-gate helper is implemented and tested locally; exact
  v4 launch checklist updates and its PR are being prepared. No v4 budget/worker
  preparation or start occurred.

### Next / blocked

- Publish lead-owned rehearsal fix PR; integrate AI fixes and complete #85 review.
  One combined remote CI before merging/releasing. Keep unsupported story hints
  disabled; coordinate the frontend helper role gate and reviewed serving persona.
- Reproduce the corrected PT receipt and ES explanation after reviewed integration
  and release; estimate/obtain GO before any new real-model smoke.
- V4 freeze/start remain blocked by these live bugs. Earlier Oct 1 evening freeze
  is tentative; existing Oct 2 noon COT plan requires explicit freeze and final GO.
  Keep v4 rows/selections/bindings unopened and abandoned v1 untouched.

## 2026-10-01 UTC — free OpenRouter launch gate prepared

### Completed (verified)

- `scripts.openrouter_preflight` uses the existing inference key in memory and
  GETs only `/api/v1/credits` and `/api/v1/key`. It requires account balance and
  per-key `limit_remaining` each ≥ $4, rejects invalid/missing metadata, and
  retains only a numeric mode-0600 receipt under ignored artifacts. Error output
  excludes keys, account labels and raw provider bodies. No management key needed.
- `.venv/bin/pytest tests/test_openrouter_preflight.py`: 16 passed with authored
  HTTP mocks, covering either insufficient balance and sanitized failures.
  Ruff passed. Live free GET gate at 01:06 UTC passed: $9.659101954 account /
  $5.802867 key remaining; zero model calls / $0. Receipt is point-in-time only.
- [v4-launch-checklist.md](../evaluation/v4-launch-checklist.md) now has exact
  local-DSN prepare/start/status/resume commands without secrets in argv/output.
  The documented helper's `status` command exited 0 without creating a program
  directory, fetching a provider key or opening suite rows/bindings. The runner's
  detach/resume behavior is independently covered by the zero-cost rehearsal.
- #89 merged at `2dfa504` with green main remote CI; unchanged Docker COPY input
  trees. Lead live rehearsal fix PR #90 is published, locally verified, targeting
  `integration/pre-v4-freeze`; no Azure redeploy or paid call in this session.

### Done but not verified

- No v4 budget preparation, suite preparation, start or resume was executed.
  Product freeze/release and a fresh final GO are still required. Oct 1 evening
  COT is tentative; the existing Oct 2 noon COT plan has not been overridden.
- Updated #85 includes the provider_402 guard correction; it still needs lead
  integration verification. AI-owned live NLG/type normalization fixes pending.

### Next / blocked

- Integrate reviewed round-two and live rehearsal fixes; one combined remote
  CI before main merge/release. Keep v4 rows/selections/bindings unopened.
- On confirmed release approval, close/count dev scopes and verify live prior
  exposure + $3 v4 + $0.10 release + $0.10 latency ≤ $12. Recheck fresh OpenRouter
  balances immediately before the authorized first start. No new spending now.
- Continue from docs/status/progress-log.md. Next layer: close live rehearsal
  blockers, combined release, then v4 launch gates. Same rules.

## 2026-09-30 PDT — AI approved pre-v4 development baseline

### Completed (verified)

- Orchestrator confirmed `dev-gate/pre-v4` / `pre-v4`; durable readback: $1
  lifetime, zero reservations/exposure, prior scopes closed. All paid dev calls
  reserve before request through this scope, including Jev, and stop at $0.90
  shared exposure. No final-evaluation scope or v4 rows accessed.
- Frozen 60-case hashes still match. Added a sequential real-P entry point with
  clean-commit/config/prompt pins, private per-call checkpoints and cost from
  per-case usage fields. Scope/run routing and unknown-cost retention are tested.
- Baseline carries the previously reviewed PR #77 grounding fix (internal handles
  and corrupt text); its 34 focused mock/freeze/budget checks pass with no spend.

### Done but not verified

- The first real baseline and lean-prompt comparison have not started. v5.1 and
  production model selection are unchanged; PR #77 remains a separate lead merge.

### Next / blocked

- Run frozen round-two real P, diagnose by owner, then repair AI causes and compare
  the lean prompt as budget permits. No adoption without the full five-set gate.
- Human export remains pending. The next model/Decisions comparison is queued;
  wait for its separate scope before any paid comparison.

### 2026-09-30 PDT — round-two real baseline and AI regressions

- Completed (verified): frozen 60-case real P baseline at `0161c3a`: pass 15/60
  (ES 9/30, PT 6/30), injection logging 6/6, no forbidden actions, one materially
  incorrect final outcome (polite refusal treated as recognition). Scope readback
  $0.30949149 charged/reserved, $0.28551849 known, two unknown-cost reservations
  retained. Per-call known sum differs only by eight-decimal durable rounding.
  All attempts included: Gemini 169/171 schema-valid, Jev 140 valid judgments.
- Completed (verified): authored 15 new regression cases before NLU repairs;
  eight failed initially. Repairs reject offer refusal as purchase recognition
  while preserving actual recollection, parse explicit day/month dates in words
  without guessing missing month/year, and reuse units already present in the
  extracted amount when the currency field is absent. Interfaces unchanged.
- Done but not verified: repaired real-P follow-up pending. Most strict failures
  concern lead-owned candidate/correction/compound-request state; gold remains
  untouched. Two mixed-language openings may exhaust the contract's two-round
  clarification rule; request adjudication rather than changing labels to pass.
- Next / blocked: v5.2 is a separate development candidate, not the active prompt.
  Complete comparable five-set evidence is required for adoption; the shared
  $0.90 stop has priority over completing that potentially larger study. Default
  Gemini and production v5.1 remain unchanged. No v4 access or final run.

## 2026-09-30 PDT — round-two budget stop and lean-study preparation

### Completed (verified)

- Real v5.1 baseline: 15/60 pass (ES 9/30, PT 6/30), one materially incorrect
  polite-refusal outcome, zero forbidden actions. Repaired follow-up at `331fb57`
  completed 47: 9/47 pass (ES 6/24, PT 3/23), zero unsafe findings on those 47.
  On the common 47 both versions pass 9/47, with one flip each direction under
  degraded NLU. The baseline unsafe case lies outside the partial follow-up;
  this is neither a demonstrated improvement nor proof its real outcome is fixed.
- Durable `dev-gate/pre-v4` / `pre-v4` readback: $0.87148777 charged/reserved,
  $0.49124327 known, 564 reservations, 27 unknown costs retained. Next reservation
  was denied before request at the $0.90 stop. Interrupted case 48's costs remain
  in the ledger/journal. Known costs use per-call fields, never key deltas.
- All-attempt OR schema validity: before 169/171, after 123/148; Jev 140/140 and
  105/105. Zero-cost GET health checks verified available key limit but exhausted
  account credits. Twenty-two short follow-up failures suggest billing rejection;
  old records lack HTTP codes, so no retrospective individual attribution.
  Future records now keep sanitized status codes only, not error text/URLs/body.
- Seventeen authored NLU regressions protect refusal vs actual recognition,
  complete word dates vs invalid/missing dates, and explicit amount units. The
  frozen sixty definitions/builders remain unchanged. Lead-owned state/matching
  and compound-request causes, plus two gold/spec adjudications, are grouped in
  `docs/ml/nlu-robustness-round2.md`. No orchestration or interface changes.
- Separate v5.2 development candidate is 31.1% shorter in body characters. A
  development-only driver inventories 240 allowlisted cases, with synthetic
  identities and complete authored overlays for retired v3. All 240 execute with
  mock/$0 and no exceptions; mock unsafe findings are retained, not mislabeled
  as real accuracy. Case-cluster latency bootstrap now includes failed Grok NLU
  attempts; corrected aggregate receipts preserve the original paid journals.
- Local verification: 297 relevant mock/unit checks pass, eight DB-dependent
  skips, Ruff and strict mypy (88 source files). Final two invalid-date guards,
  error metadata and candidate driver have mock validation only after the stop.

### Done but not verified

- v5.2 has zero paid measurements; its token savings, p50/p95 and accuracy are
  unverified. No complete five-set comparison or adoption gate is claimed.
- The polite-refusal real follow-up case remains unmeasured; most failing
  multi-turn state behavior needs lead work. Default Gemini and v5.1 stay active.

### Next / blocked

- No further paid call under this scope: exposure denial and account credits
  block completion. Any resumed latency study needs explicit new authorization;
  the queued `dev-gate/model-compare` scope cannot be repurposed for it.
- Private [PR #85](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/85) is OPEN
  and mergeable into `fix/post-v3-analysis`, code head `226bf3e` read back. It
  carries #80's freeze and #77's output guards because both earlier PRs now show
  closed without merges. Integration PRs use rigorous local checks under the
  owner's main-only remote CI policy. Lead reviews/merges; no merge performed.
- Human CSV path remains unconfirmed. Continue zero-spend disparity analysis and
  model/API availability checks; no v4 input, final run or default change.


## 2026-09-30 PDT — queued comparison read-only preflight

### Completed (verified)

- Free OpenRouter catalog, ZDR endpoint and authenticated user-model GETs confirm
  `openai/gpt-6.1-sol`, ZDR `azure` at $2/$10 per million input/output tokens;
  `openai/flex` is absent from the ZDR list. Gemini's existing Vertex pin remains.
  Receipt timestamps/hashes and primary citations are in the preflight document.
- Authenticated Decisions modality list has nine models, none `openai/*`; no
  direct OpenAI credential or SDK in this worktree. Official searches did not
  establish preview entitlement. Do not substitute OpenRouter's third-party
  Decisions API for an OpenAI model. Zero inference, spend or config changes.
- Repricing saved round-two valid-call tokens uncached gives $1.361114 for just
  that 60-case Gemini/Sol pair, excluding Jev/retries/new reasoning. Full five-set
  coverage is unlikely inside $1.50; disclose partial coverage if the cap stops it.
- Private disparity PR #86 targets main, head `6ff70e1`, OPEN and mergeable at
  readback. Safety/checks/Postgres have passed; web CI is still running. An extra
  cross-check found raw fault-prefix unsafe flags needed the official executed-
  case filter; correcting that documentation before lead review, without reruns
  or changed official cases/results.

### Done but not verified

- No Sol accuracy/latency, language comparison or Decisions risk results exist.
  Production Gemini/v5.1 stays unchanged. Human export still awaits its path.

### Next / blocked

- Wait for exact `dev-gate/model-compare` run/scope readback and restored account
  credits before every paid comparison. Never reuse the stopped pre-v4 scope.
- Lead reviews #85 and the corrected #86, with required green main-target CI.
  No merge, publication, held-out v4 access or final run by this lane.


## 2026-09-30 PDT — approved paired-sample freeze and disparity CI readback

### Completed (verified)

- Owner approved a balanced paired model sample inside $1.50. Frozen manifest
  selects 50 pairs: ten per each of the five existing dev sets, five ES/five PT
  per set, all ten round-two families once. Metadata-only stable ordering and
  dialect/category buckets; no saved model outcome used for selection. Manifest
  SHA `40ef32671ff05617dc3246db38891a756b6d200cec48c368cc6e2483416b634c`;
  full pool and per-case hashes validated before use. No new paid call.
- Sample/inventory, tamper rejection and freeze checks pass: 19 focused checks,
  then 299 relevant mock/unit checks with eight DB skips; Ruff/format and strict
  mypy over 88 files pass. The separate lean study keeps
  its original complete 240-case adoption gate; production v5.1/Gemini unchanged.
- Private disparity PR #86 is OPEN/mergeable to main at corrected head
  `3d86622a94e056d70a9d0303d8b59e9b26f0a7ec`. Required CI run 36789815778
  and safety run 36789815779 both succeeded on that head. The earlier head also
  finished green before the substantive denominator correction was pushed; no
  CI cancellation or manual rerun. Official v2/v3 inputs and scores unchanged.

### Done but not verified

- No Sol execution, comparison result or OpenAI Decisions preview access. Sample
  uncertainty and equal set weighting prohibit full-240 or population claims.

### Next / blocked

- Wait for the lead's exact model-comparison scope/run readback and restored
  OpenRouter credits. Cap stays $1.50 with $12 cumulative maximum. Do not use
  the stopped pre-v4 scope. Lead merges #85/#86; this lane performs no merge.
- Human CSV path remains unconfirmed; local offline scoring page still exists.
  Never open v4, start the final run or change a model default without approval.
## 2026-09-30 PDT — confirmed comparison scope, paired harness and retry analysis

### Completed (verified)

- Read back `dev-gate/model-compare` / `model-compare`: $1.50 lifetime, enabled,
  zero attempts/cost. Pre-v4 remains enabled at $0.49124327 known / $0.87148777
  charged including 27 unknown reservations; its $0.90 stop is unchanged. The
  owner restored credits; free account-health GET now confirms availability.
- Prepared paired Gemini/Sol NLU+phrasing driver with fresh ZDR/provider-price
  checks, same prompts/timeouts/Jev union/Grok fallback, lifetime reservations,
  private checkpoints and no duplicate paid case on resume. Added primary model
  identity to risk records. Sol uses its advertised max_completion_tokens field;
  default adapter behavior/config remains unchanged. Mock path does not load keys.
- Independent opening-slot annotations frozen before comparison calls: 48
  single-target openings plus two explicit multi-target F1 exclusions, without
  changing any scenario gold. Existing metadata-only fifty-pair sample unchanged.
- All 100 mock case-runs execute without exceptions/$0; both deterministic arms
  pass 33/50 with four materially incorrect outcomes, not model-quality claims.
  Relevant tests: 253 passed/eight DB skips; 47 additional adapter/API/language
  checks pass. Ruff, strict mypy (90 files), compile and interface snapshots pass.
- Saved dev retry replay: two baseline / three follow-up ~6.05 s slow firsts plus
  successful retries take 7.64–9.18 s. Shifting those retries to 3–4 s leaves sample
  request p95 unchanged; genuine hedges add duplicates and unmeasured loser cost.
  Details/assumptions in docs/ml/nlu-robustness-round2.md. No hedge adopted or paid.
- Disparity PR #86 remains OPEN with all required main-target CI successful at
  head 3d86622a94e056d70a9d0303d8b59e9b26f0a7ec. No rerun or merge.

### Done but not verified

- Sol accuracy, paired ES/PT outcomes, cost and latency are not yet measured.
  v5.2 remains a separate unadopted candidate without real latency/accuracy data.

### Next / blocked

- Run approved paired dev comparison on the committed pins using its dedicated
  $1.50 cap and $12 cumulative maximum. The remaining pre-v4 $0.02851223 cannot
  fund complete follow-up plus both 240-case prompt arms; do not erase unknown
  costs, exceed $0.90 or repurpose the comparison scope. No production change.
- Lead reviews/merges #85/#86. Human CSV path is still pending. No held-out v4
  input, final run, publication or merge from this lane.

## 2026-09-30 PDT — partial paid comparison, timeout correction and spend stop

### Completed (verified)

- After owner-confirmed credits restoration, real comparison ran at committed
  head 60f3bfa using only the frozen approved dev sample, exact scope/run
  dev-gate/model-compare / model-compare and reserve-before-call. Thirty of fifty
  pairs complete (six per set, 15 ES/15 PT); one extra Gemini case and one
  interrupted Sol case excluded from paired quality but included in attempts.
- Postgres readback 2026-10-01 00:41:56 UTC: 239 attempts, $0.20973001 returned
  per-call costs, $1.28198000 retained across 31 unknown-cost attempts,
  $1.49171001 charged exposure of $1.50. Only $0.00828999 remains. All-scope
  exposure $7.04653079. Paid work stopped; no further provider call or reserve
  release, no key-level cost delta, no new scope or funding assumption.
- Both routes pass 25/30 (Wilson 66.4–92.7%), SAR 19/28, strict escalation 3/3,
  unnecessary transfers 5/27, each unsafe class 0/30. ES 13/15, PT 12/15 in
  both. Opening-slot F1 97.64% Gemini / 99.21% Sol route; six completed Sol
  conversations used Grok. Five common failures are all in round two; both
  routes pass 1/6 there. Partial tables, intervals and caveats published in
  docs/ml/model-comparison-pre-v4.md; no equivalence or replacement conclusion.
- Owner's timeout audit: both candidates inherited the serving 6/20 s limits.
  Corrected comparison overlay to 30 s per attempt / 65 s logical-call budget
  for both, with no shortened first. No production config change or paid rerun.
  The 31 unknown errors were generic model_failure at 0.409–4.033 s, not proven
  timeouts; none retained usage, numeric envelope code or generation ID.
- Comparison now stops after its first unknown bill, before retry/fallback or
  another case, retaining the reserve. Settlement precedes stop callbacks,
  including concurrent Jev. HTTP-200 errors/malformed choices preserve numeric
  category, normalized billing/id and no provider prose/reasoning. Timeout
  durations stay in latency; generic failures remain separate diagnostics.
- Original paid launch/call/summary artifacts and frozen labels preserved. Slot
  annotations were authored by Codex, not human reviewed; documented the frozen
  JSON's erroneous Human-authored method wording without changing its hash.
- Broad local mock/unit/API suite: 318 passed/eight DB skips before the final
  additional parallel-Jev regression; focused final rerun 28 passed. Ruff,
  format (323 files), strict mypy (90 source files) and interface snapshots pass.
  Corrected 100-case mock comparison completes/$0. No new paid measurements.

### Done but not verified

- Fair-timeout comparison has no paid result. Unknown Sol bills remain
  unreconciled; discarded IDs cannot be reconstructed from the saved records.
  Current route latency/cost is not pure Sol or in-region serving evidence.
- Full round-two after coverage and both 240-case lean-prompt arms remain
  incomplete: pre-v4 exposure $0.87148777 leaves $0.02851223 under the $0.90 stop.
  v5.2 remains unadopted. Human judge CSV path remains unconfirmed.

### Next / blocked

- Lead reviews #85 to fix/post-v3-analysis and #86 to main; #86's required remote
  CI was green at 3d86622a94e056d70a9d0303d8b59e9b26f0a7ec. Integration-target
  #85 uses local checks under the owner's main-only CI rule. No merges/reruns.
- No more paid comparison within the exhausted cap. Any fair restart needs
  verified per-call reconciliation and fresh protocol pins plus owner-approved
  funding/coverage. Gemini/v5.1 stays default; never access held-out v4, run its
  final evaluation, publish content or use another lane's scope.

## 2026-09-30 PDT — comparison account-error stop follow-up

### Completed (verified)

- Lead identified that known-cost HTTP-200 provider_402 bypassed the HTTP-only
  guard in #85. Guard now stops both http_/provider_ 401, 402, 403 and 429 codes:
  credential/credit/forbidden-budget/quota/rate-limit failures never retry or
  fall back, even when usage returns a known zero or positive bill.
- Authored mock regressions exercise HTTP-200 errors through StructuredClient,
  both zero/positive bills, both protocol code forms, and no retry/fallback.
  Original paid comparison remains 30/50 pairs, $0.20973001 known versus
  $1.49171001 exposure; no further paid calls, reserve release or default change.

### Done but not verified

- Corrected comparison settings are not paid measured; previous result remains
  partial and unsuitable for equivalence. No new comparison spending authorized.

### Next / blocked

- Lead reviews #85; finish separate main-target NLG corruption/status-label and
  transaction-kind normalization PR with zero-cost saved-dev replay. Fee aliases
  map to Adjustment per owner confirmation. No held-out v4 access or merge.

## 2026-10-01 UTC — local pre-v4 integration and offer-refusal repair

### Completed (verified)

- Private stacked PR #90 holds the live rehearsal lead fixes; #91 holds the free
  credit preflight and exact launch commands. Combined with reviewed #85 head
  `83be371` on `integration/pre-v4-freeze`, base main `2dfa504`; main unchanged.
  Merge conflicts were progress-log appends only; preserved both histories.
- #85's `provider_402` bypass is repaired; authored known-cost error-envelope
  checks prove stop before retry/fallback. No paid comparison resumed. Production
  remains v5.1/Gemini; partial comparison does not establish a challenger choice.
- Combined local Python suite: 579 passed / 22 skipped (aggregate progress marks);
  disposable Postgres: 30 passed. Pre-commit, web typecheck, lint and build exited
  0. Local receipts: ignored `artifacts/integration/checks/pre-v4-combined-*`.
- Independently reproduced the lead-owned polite offer-refusal bug using fresh
  authored mock messages: ES proposed a dispute; PT handed off out of scope;
  neither wrote. Generic offered-state cancellation now handles explicit polite
  refusals, keeps actual recollection as explanation and preserves isolated-assent
  clarification. Fifty relevant authored B1/P ES/PT checks passed, including
  restart. No frozen row/gold or threshold changes; no paid calls or Azure changes.

### Done but not verified

- New offer-refusal repair still needs final hooks/publication/integration. Full
  browser/live API gates on the combined head are running; remote CI deferred to
  the complete candidate so it runs once. Azure remains the previous release.
- AI live NLG guard and transaction-kind alias fixes, frontend story-button triage
  pending. Round-two compound-request/descriptive-choice/language-limit problems
  remain disclosed limitations; no fresh real gate claimed for those families.

### Next / blocked

- Integrate the forthcoming reviewed AI/frontend rehearsal fixes; run one combined
  remote CI before main merge and approved release. Estimate/obtain GO before any
  new real-model smoke. Keep v4 rows, selections and bindings unopened/unstarted.
- V4 freeze remains pending closure of live blockers and owner confirmation.
  Continue from docs/status/progress-log.md. Next layer: close live rehearsal
  blockers, combined release, then v4 launch gates. Same rules.

## 2026-10-01 UTC — integration checks complete, live AI fixes pending

### Completed (verified)

- Reviewed/integrated #85 `83be371`, #90, #91 and the small #92 offer-refusal
  repair on `integration/pre-v4-freeze`; main remains `2dfa504`. Review and exact
  test scope: [pre-v4-integration-review.md](../evaluation/pre-v4-integration-review.md).
  Refusal test head `f592971`; no product behavior claimed for unmeasured families.
- Local Playwright 93 stories + 12 real local BFF/API customer flows + one staff
  flow passed. B1 reactive dev 32/32 and standard safety harness exited 0. Strict
  mypy 88 files, Ruff, compile, interface/catalog checks and working-tree safety
  passed. Parent combined Python 579 passed / 22 skipped; subsequent cancellation
  regressions 50 passed. Postgres 30 passed. No optional paid rerun.
- Confirmed updated private reference file mode 0600, four run IDs and four SIDs;
  no scope values printed. Earlier exact-scope Azure diagnosis established live
  phrase/MATCH causes while preserving RLS. Generated Next references and dev
  Markdown restored; official result pages unchanged.

### Done but not verified

- AI live phrase corruption/status and transaction-kind normalization PRs are
  still awaited, as is frontend story-button triage. New code is not deployed;
  Azure still runs the previous release. Remote CI is held for the complete head.
- No new real gate or broader round-two fix claim. Candidate-state descriptive
  replies, unfamiliarity across early clarification and compound-request handling
  remain lead-owned limitations; language/colloquial-unit conflicts need adjudication.
- V4 budget/suite preparation and launch remain unexecuted; no v4 contents opened.

### Next / blocked

- Review/integrate the incoming live AI/frontend fixes, require one combined
  remote CI, then merge/release under standing approval. Estimate/obtain GO before
  any new real-model smoke. No spend or Azure access/resource change this session.
- Feature freeze remains pending live blockers and owner confirmation; exact
  commands are ready in [v4-launch-checklist.md](../evaluation/v4-launch-checklist.md).
- Continue from docs/status/progress-log.md. Next layer: close live rehearsal
  blockers, combined release, then v4 launch gates. Same rules.


## 2026-09-30 PDT — AI zero-spend saved-result disparity investigation

### Completed (verified)

- Reaggregated saved primary P-Gemini repeat-0 results only: v2 200 and v3 100.
  Official pass remains 63/200 and 77/100. All 300 checkpoints and two official
  reports were hashed before/after, unchanged; no execution, rescoring, paid call
  or v4 input. Private aggregate/composition receipts stay ignored.
- `docs/evaluation/disparity-analysis.md` reports ES/PT, Basic/Plus/Premium/Student
  and AR/CO/MX pass with Wilson intervals, eligible/in-scope SAR and strict
  transfers, unsafe caveats, and the failure causes behind the observed gaps.
  V3's ES 38/48 vs PT 35/48 gap is two extra PT security-packet failures and one
  extra selection failure. V3 country/segment counts are language-balanced;
  coarse category adjustment changes +6.25 pp to +6.37 pp, not a causal effect.
- Existing shared routing/selection defects, policy/case mix, synthetic correlated
  cells, no fluent PT human review and es-CL n=9 limit interpretation. Proposed
  semantic PT regressions and fluent review are follow-ups, not new results or
  prompt changes. Only v4 results remain TODO. Relative evidence links verified.

### Done but not verified

- No population disparity or language equivalence claim; dialect naturalness is
  not established by objective pass. Human judge CSV path remains unconfirmed.

### Next / blocked

- Private [PR #86](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/86) is OPEN
  and mergeable to main, initial head `6ff70e1` read back. Safety/checks/Postgres
  passed; web CI still running. No cancellation, rerun or merge by this lane.
  Shared progress-log entry is the only change outside the requested document.
- Corrected the draft's unsafe aggregation to exclude unexecuted fault prefixes,
  matching official v2 P's 187 executed / 59 materially-incorrect flags. ES
  29/89 and PT 22/78 are the executed-case counts; provisional prefix flags stay
  in workload failures, not safety exposure. Original draft receipt is retained
  privately; all 302 saved inputs remain unchanged. A new push is necessary for
  this substantive evidence correction and requires green CI on that head.
- Robustness changes remain in private PR #85 to `fix/post-v3-analysis`. The
  queued model comparison still awaits its separate durable scope/readback and
  restored OpenRouter account credits; metadata checks are zero-call only.

## 2026-10-01 UTC — supporting PRs and fresh cumulative preflight

### Completed (verified)

- Integrated reviewed #88 `a3f54d3` and supporting AI aggregate #86 `3d86622` on
  the private candidate, keeping rehearsal failures and official figures intact.
  Progress conflicts resolved by preserving all histories. Main unchanged.
- Critically reviewed #93 `8d3ac42`: source-only authored replays confirm original
  digit/English leak is rejected but expose machine-enum and merchant-citation
  gaps. Also found default-mode private replay outputs. Orchestrator relayed all
  three corrections; hold this PR until updated. Retargeted it to the integration
  branch to avoid redundant main-target CI pushes.
- `python -m scripts.pre_v4_budget`: $6.99994254 current charged/reserved,
  conservative maximum $11.82845477 including full dev allowances, $3 v4 and both
  $0.10 smokes. Current pre-v4 $0.87148777, 27 unknown attempts; comparison
  $1.49171001 retained. Metadata-only read; no prepare, closure or reserve release.
  Exact math in [v4-launch-checklist.md](../evaluation/v4-launch-checklist.md).

### Done but not verified

- Corrected #93 and frontend video-readiness PR are awaited. Combined remote CI
  and Azure release have not run. Existing main's four checks are success.
- V4 stays unopened/unprepared/unstarted. No new model spend in this session.

### Next / blocked

- Review corrected #93 plus frontend readiness; complete local gates, then one
  remote CI on the full main candidate. Standing approval covers main merge and
  image release. Frontend rechecks the four live bugs after release.
- Feature freeze and final v4 GO follow a clean owner rehearsal; they have not
  been granted. Recheck actual cumulative exposure and free OpenRouter balances
  at launch, preserving all retained reservations.
- Continue from docs/status/progress-log.md. Next layer: combined rehearsal fixes
  and release, then freeze and v4 launch gates. Same rules.

## 2026-10-01 UTC — release helper cumulative accounting correction

### Completed (verified)

- Found release helper adding already-counted pre-v4 dev charges to its full $1
  allowance again. Corrected only the maximum calculation, matching the existing
  shared-dev preflight. One SQL snapshot returns both sums; no charge/reserve/cap
  update, comparison allowance still conservatively retained in full.
- `pytest tests/test_release_smoke_budget.py tests/test_pre_v4_budget.py
  tests/test_llm_budget.py tests/test_after_v2_budget.py`: 19 passed / 9 database
  skips. Ruff passed. Two initial invocations used nonexistent guessed test paths
  and collected no tests; the corrected command above is the completed check.
- Existing release purse read-only verification (`prepare=False`) passed actual
  Azure budget SQL: $0.10 cap unchanged, 19 attempts, $0.01627249 charged, no unknown
  costs. Total $6.99994254; conservative maximum $11.82845477. No new run, prepare,
  scope closure or provider request. Receipt ignored under artifacts/azure.
- Frontend video PR #94 `93e65a0` is now available for critical review; includes
  trusted Ops persona hints and preserves API-gated PT unavailability.

### Done but not verified

- New helper fix still needs publication/integration/final CI. #94 review and
  corrected #93 head pending; no Azure change or paid call this session.

### Next / blocked

- Finish the corrected AI/frontend integration and local gates, then one remote
  CI before standing-approved main merge/release. No v4 contents or start until
  the owner's clean rehearsal, freeze and separate GO.
- Continue from docs/status/progress-log.md. Next layer: complete rehearsal-fix
  integration and release. Same rules.

## 2026-10-01 UTC — corrected language guards and video integration

### Completed (verified)

- Integrated corrected #93 `7c7a96a`; authored replay rejects original corruption,
  machine-state prose and status-only merchant citation. Local targeted tests:
  153 passed (localized integrity, kind aliases, private replay permissions).
- Reviewed/integrated #94 `93e65a0`: overlapping Desk/copy history resolved,
  verified-action assertions retained and SLA assertion adapted to days. No
  confirmation/OTP/write/BFF behavior changes. Budget helper #95 integrated.
- Owner authorized PT API hint change separately: two owned reviewable movements
  may have missing merchants; named explanation retains its named-merchant gate.
  No threshold, policy or authority change; authored scope/boundary tests added.

### Done but not verified

- Combined full local/remote gates and Azure release have not yet run. No paid
  model calls, Azure changes or v4 contents/start this session.

### Next / blocked

- Verify PT hint regression and all combined local checks; publish one candidate
  for remote CI, then standing-approved main merge and capped image release.
- Frontend rechecks four live bugs on the actual release before freeze/v4 GO.

- PT hint scope/identity/authentication checks: `pytest
  tests/test_story_availability.py tests/test_trace_additions.py
  tests/test_judge_access.py`: 26 passed, mock only. The initial assertion expected
  an empty merchant but the API deliberately renders the missing sentinel `—`;
  corrected the authored test to that existing contract. A second assertion expected
  `verified=False`; choices deliberately use `verified=None` (no write claimed).
  Both assertions now match the existing contract; the final rerun passed. The
  preceding commit recorded 26 passes prematurely before checking the receipt;
  this entry corrects that verification sequence. An earlier sandboxed
  TestClient run stalled and was terminated; local-network rerun is the evidence.

## 2026-10-01 UTC — combined local release candidate accepted

### Completed (verified)

- Final #93 `25d8fee` included with its history intact; follow-up changes are docs
  only. Reviewed product source from `76dd05b` matches integration `1b51eb4`.
- Full local `pytest`: 769 passed / 22 optional DB skips; disposable Postgres 30
  passed. Full hooks, Ruff, strict mypy, compile, interface/catalog, file guards,
  web typecheck/lint/build passed. B1 safety and reactive dev both 32/32.
- Browser gates: 111 fixture + 12 customer/live API + 1 staff = 124 passed. Initial
  relative Chromium cache invocation could not launch 82 browser checks; corrected
  absolute repo-local cache passed all checks. No assertion or guard was removed.
- Fresh free OpenRouter metadata: account $9.659101954, key $5.802867. Live Azure
  estimate remains $34.63/month. Durable read-only scope metadata: current
  $6.99994254; conservative maximum $11.82845477 including v4 $3/both smokes.
  No paid call, reservation release, cloud change or v4 preparation.

### Done but not verified

- Combined main-target remote CI and Azure release remain pending. Current main
  is unchanged and the old Azure image remains active.

### Next / blocked

- Publish a single main candidate, wait for remote CI/safety; standing approval
  permits green main merge and image-only release with the temporary smoke run.
- Capped real smoke estimate $0.01–$0.03, hard $0.10 shared with browser smoke.
  No resource/replica/access change. Frontend then rechecks four live bugs before
  owner feature freeze and separate v4 GO.

## 2026-10-01 UTC — live rehearsal fixes released and verified

### Completed (verified)

- Single combined PR #97 CI/safety passed first run; merged under standing OK to
  **92994d933e7e4d4cddbbf988fb4cc748d3cd5db1**. Automatic main CI 36806917133 and
  safety 36806917242 passed. Exact main == origin/main, clean. #85 exact head is
  an ancestor and was closed as integrated through #97, without redundant CI.
- Built/pushed both private SHA images; registry digest readbacks passed. Reviewed
  Terraform apply: 0 added / 2 changed / 0 destroyed, image/release identity and
  approved temporary smoke binding only. Min replicas 0; shape/access unchanged.
- `scripts.azure_verify` passed. Capped `scripts.azure_llm_smoke`: ES filing with
  independent readback, PT ambiguity/handoff and deterministic fraud passed;
  **9 valid calls, $0.00813975, zero unknown/fallbacks**. Hard $0.10 lifetime run:
  `pre-v4-release-92994d933e7e4d4cddbbf988fb4cc748d3cd5db1`.
- `scripts.serving_browser --target azure` passed chat/Desk/Ops, verified handoff
  and resolution; four attempted conversations total, no extra allowance/reset.
  Outside-network azure-access 36807587445 passed. GET-only config verifies ES
  explain/fraud and PT ambiguous hints are all present. No merchant was invented.
- New ignored `artifacts/azure/jev-release.json`: controls/real smoke/CI flags all
  true at the release SHA. Cumulative charged/reserved **$7.00808229**; conservative
  maximum **$11.83659452 ≤ $12** including v4 $3 and both smoke allowances.
  Prior unknown reserves and all dev/production caps remain intact.
- Full local gates were 769 Python / 30 disposable Postgres / 124 browser passes;
  B1 safety + reactive dev both 32/32. Detailed commands/evidence and initial
  failed local invocations are in pre-v4-integration-review.md.

### Done but not verified

- Fresh frontend Azure rehearsal of all four formerly observed live bugs is still
  pending. Release smoke is not a new evaluation or proof of full story quality.
- V4 rows/selections/bindings remain unopened; no prepare/start or paid comparison.
  Feature freeze/final v4 GO remain pending. Submission warm/access modes OFF.

### Next / blocked

- Frontend can rehearse the deployed **92994d9** now. Confirm prose corruption,
  PT choices/receipt, real SLA countdown, scoped facts/actions and all story buttons.
- Owner decides feature freeze and v4 GO after a clean rehearsal; no new resource,
  replica, access/publication change authorized by this release.
- Release evidence is published on `integration/pre-v4-freeze` so exact green main
  remains stable. Fold this docs-only entry into the next authorized integration.
- Continue from docs/status/progress-log.md. Next layer: clean live rehearsal,
  owner freeze and v4 launch gates. Same rules.

## 2026-10-01 UTC — AI offline human review of completed v4

### Completed (verified)

- Built ignored, mode-0600 `artifacts/human-judge/v4-score.html` from the lead's
  completed v4 sheet. Exactly 20 unchanged blinded items and ten CSV columns;
  Spanish instructions/rubric, four 1–5 dimensions, ten handoff N/A items,
  localStorage autosave and CSV download. V4 version labels and storage key are
  separate from v3. Original source hash verified after export.
- Offline Chromium verified autosave/reload, all 70 applicable scores, progress,
  quoted multiline notes and unchanged wording/columns on export: zero network
  requests and browser errors. Test ratings remain in a separately named ignored
  fixture; Sebastian's page starts blank. No hosting or paid calls.
- Read saved v4 judge artifacts only for this owner-authorized review: all 60
  judge pairs saved, including all 20 human-sheet items (ten handoffs). Prepared
  strict v4 import and descriptive Sonnet/Jev aggregate agreement in
  `docs/evaluation/judge-human-validation.md`; no human scores inferred.
- Fifteen focused mock human-review/judge tests, Ruff and strict mypy on 93
  source files passed. Page, test exports and aggregate receipts are ignored.

### Done but not verified

- Sebastian's scored v4 export has not arrived. Human–Sonnet and human–Jev
  agreement remain pending, including ES/PT slices. No judge validation claim;
  twenty items do not satisfy the rubric's fifty-item calibration requirement.

### Next / blocked

- Import the confirmed v4 export path against the unchanged v4 sheet and saved
  judges; publish aggregate exact/within-one/quadratic-kappa results and larger
  disagreement review in the validation document. V3 is optional only if scored.
- Changes are on local `fix/v4-human-review`; no deployment or merge. Existing
  PR #93 is untouched. Keep raw ratings, notes and response text out of Git.


## 2026-10-01 — AI external-audit fixes, items 1 and 4

### Completed (verified)

- Rebased onto private `origin/main` `6a221a4` before changes. These are
  **post-v4 fixes, not reflected in v4 numbers**; no official suite rerun/rescore,
  real-model call or new provider spending.
- `explain_status` is template-only. Generated blank-plan clarifications reject
  ES/PT completed-action and invented-cause claims, including all three audit
  probes, and fall back to the approved template. Action receipts stay in code.
- Added independent evaluator action/causal checks, with runtime DLP disabled
  in negative regressions. Verified receipts, proposed actions and absent
  settlement dates retain their correct meanings.
- Narrowed third-party guards to access requests, and bare processo/demanda to
  legal context. Thirty-four authored benign controls pass normally; twelve real
  attacks stay refused. B1 and regex-only P hits cannot terminate authentication;
  P needs two non-degraded model-confirmed access strikes. Session-scoped restart,
  cue retention and pending-action invalidation tests now exercise that contract.
- Full local mock Python suite: 1004 passed, 25 database-dependent skips. Ruff,
  strict mypy (95 source files), frozen interfaces and policy catalog passed.
  B1 standard and reactive dev harnesses both remain 32/32. Authored additional
  counter tests are checked separately. Generated dev result-page edits restored.

### Done but not verified

- PR #107 Python, Postgres and invariant CI passed. Its browser job exposed
  a missing plural charge alias and old B1-revocation expectations; fixed the
  guard and the two browser tests. Remote CI on the corrected head and merge
  remain pending. No Azure image release.
- Shared changes are explicitly required by the assignment: policy guards,
  minimal API refusal wiring, evaluator and tests. No frozen interface change.

### Next / blocked

- Push the private priority PR, require green CI, then merge under standing OK.
  Implement items 2+3 in a separate PR: budget degradation and trusted country.
- Lead releases the post-v4 image after the batch. Human v4 CSV export remains
  pending separately; no human agreement has been invented.

## 2026-10-01 — AI external-audit fixes, items 2 and 3

### Completed (verified)

- Authored six API-boundary regressions before the fix; all six reproduced the
  audit failures. Exhausted and already-disabled gates now answer HTTP 200 with
  localized ES/PT degraded copy and deterministic rules; denied reservations
  produce no provider call, retry, fallback or fabricated action receipt.
- Runtime budget denial degrades at the primary or optional typed-risk reserve
  boundary. Existing paid-study hard-stop wrappers remain hard stops. An already
  started second opinion is settled without promoting its flags when the
  primary budget is denied; uncertain settlement retains the reservation.
- NLU receives country from the authenticated customer's scoped ledger snapshot
  on each request, including the security confirmation and recognition path.
  The shared runtime is never mutated; model country/dialect suggestions cannot
  override this context. Real ASGI mock tests verify CO `2 palos` = 2,000,000 COP
  and AR `4 lucas` = 4,000 ARS while runtime and model hints say MX.
- Focused API, integration and guard regressions passed, as did mocked typed-risk
  budget checks. These are **post-v4 fixes, not reflected in v4 numbers**.
  Mock providers only; zero provider spend, no official suite rerun/rescore.

### Done but not verified

- Full mock suite: 1015 passed, 25 database-dependent skips; four additional
  typed-reserve API variants passed afterward (ten focused API cases total).
  Ruff and strict mypy on 95 source files passed. Required remote CI and merge
  for this second PR remain pending.
- Minimal additive shared `api/app.py` wiring is authorized by handoff 15.
  No persona, identity, NluFrame or frozen interface contract changed.

### Next / blocked

- PR #107 merged at `3604ee5` after checks/web/Postgres/invariants passed.
  PR #110 contains items 2+3 and the subsequent punctuated-ID correction;
  require all green CI before merging under standing OK.
- Complete approved item 10 afterward: verify saved v4 risk-union records and
  disable live Jev behind its flag with an evidence-linked ADR. Lead releases
  the image after the batch. Human v4 validation still awaits the scored export.

### Additional verified review correction — punctuated identifiers

- Lead reproduced six third-party-access misses with dotted/dashed CPF, DNI,
  cédula and RUT identifiers; authored all six plus six benign self-ID and
  separate-sentence controls before changing the guard. All six misses failed
  as expected before the fix.
- Normalize dots only inside a bounded typed identifier before clause splitting.
  Preserve sentence boundaries and self-ID exemptions, including RUT check
  digits. Forty benign controls and eighteen actual attacks now run through the
  unit/API refusal and P-confirmation contracts. No customer data or paid calls.
- This follow-up is in #110 because #107 had already merged. Remote CI on the new
  head is required; no Azure release or official-v4 metric change is claimed.

## 2026-10-01 — AI item 10: disable live Jev, retain historical evidence

### Completed (verified)

- Sebastian approved live Jev removal. Production config explicitly sets the
  risk second opinion false; AgentAI loads the boolean flag, and the NLU no longer
  activates TypeSafe implicitly from a Gemini model ID. Opt-in studies, typed
  adapter/questions and historical Sonnet/Jev judges remain. Gemini/Grok and
  deterministic guards retain their roles; no frozen interface changed.
- Zero-cost saved-call replay verifies 160 P executions: 184 NLU + 184 risk calls
  (368), plus 15 phrase calls (383 total). One union record changes, representing
  two provider calls in one pair, on injection_suspected in v4.100. Its saved
  outcome is refused_security, failed strict handoff language routing; zero
  cue-to-reason lists change. The observed 88/100 primary pass count stays saved,
  with no official rerun/rescore or reconstructed score.
- Verified the evaluated 1ec9c2f cue-to-reason map ignores injection_suspected,
  consistent with the current replay; direct and merchant guards are independent.
  Per-call saved Jev risk cost is $0.003823932. No key-level cost delta, fresh
  provider call, customer wording or reasoning enters this committed evidence.
- ADR-0017 explains the corrected pair/call denominator, unchanged 9/10 dev
  injection recall, unlabeled extra distress cues, unverified TypeSafe ZDR and
  added vendor/call/failure mode. Updated the README, architecture, responsible-AI,
  privacy flow and language-card notice; official v4 results get a note only.
- Eleven config/production-path mock regressions and four authored replay tests
  passed; opt-in risk/judge fixtures still pass (22 focused checks total). Ruff
  and strict mypy on 96 source files passed. These are **post-v4 fixes, not
  reflected in v4 numbers**. No latency improvement or new quality score claimed.

### Done but not verified

- Full local mock suite: 1078 passed, 25 database-dependent skips. #110 merged
  at `72a8600` after all four corrected-head CI jobs passed. Item 10 remote
  CI/merge remain pending.
- Shared config, AgentAI flag wiring and evidence-document changes are explicitly
  requested by item 10. No release/deployment or real-data privacy guarantee.

### Next / blocked

- Items 1–4 are merged via #107 and #110 (including punctuated-ID follow-up).
  Merge the separate item 10 PR only after all required CI turns green.
  Lead includes the changes in the next Azure image-tag release; source config
  is not deployment. Human judge calibration still awaits Sebastian's v4 CSV.

- Release-owner follow-up: `scripts.azure_llm_smoke` still requires at least one
  Jev call and validates its union; update that gate to require zero TypeSafe
  calls for the disabled config before releasing. `scripts.azure_verify` also
  requires the TypeSafe secret binding for a real-provider image; keeping the
  existing secret does not cause a call, but removing it needs the lead's gate
  update. These lead-owned release changes are called out in the PR handoff.

## 2026-10-02 — audit merge chain and v0.6 release gates

### Completed (verified)

- #114 → #116 → #117 merged in order at `44ad68a`, `ec518a6`, `f5e128d`;
  each exact PR head passed checks/Postgres/web/invariants. Main CI `36971906103`,
  safety `36971906076` and outside-owner access `36972964182` passed at
  `f5e128dd7e544e2378081361f4a8a409af94f221`. Merge hold can lift.
- Both SHA images built/pushed and registry digests read back. Reviewed Terraform
  plan/apply: 0 added, 2 updated, 0 destroyed; image/release metadata and approved
  smoke-run binding only. `scripts.azure_verify` passed unchanged min=0/max=1,
  CPU/memory, restricted web/internal API, identity, TLS and budget controls.
- `scripts.azure_migrate_ops` completed migration 0004, TLS/non-owner readback and
  forced RLS on all five affected tables. Azure's hardened owner lacked TEMP and
  persona-registry SELECT: initial transactions rolled back; both permissions were
  loaned only for the owner migration and revoked afterward. No rows printed.
- `scripts.azure_llm_smoke`: three paths passed, four valid model calls, zero
  TypeSafe calls/fallbacks/unknown costs, $0.0076885. Original-receipt confirmation
  retry produced one dispute write. Fresh release/rehearsal purse is $0.10 lifetime,
  ordinary production breaker remains $3/day; no reservations reset.
- Browser Chat and Desk completed; Ops navigation failed before an Ops request:
  helper used obsolete “Evidencia y operaciones”, current button is “Operaciones”.
  All authenticated requests passed. One-line helper correction passes
  `node --check apps/web/scripts/serving-browser.mjs`; runtime UI is unchanged.
- Section-B read-only scan: 547 reachable commits / 2,028 blobs. Default Gitleaks
  reported 19 matches: seven release-SHA metadata occurrences and twelve authored
  idempotency literals; no actionable secret detected. 119 PRs, one issue comment,
  no review comments/bodies, all 591 completed workflow logs inspected; their
  Gitleaks scan exits 0, no sensitive-IP/signed-URL run or Actions artifact detected.
  Automatic comparison found no current Key Vault secret/subscription/tenant value;
  all 18 CSV paths are authored fixtures, no forbidden private file detected.

### Done but not verified

- v0.6 browser gate/tag/final release receipt remain pending; exactly one extra
  browser allowance requested without resetting counters or replaying model paths.
- Real benign-phrase/cross-login/budget-degrade rehearsal and fresh README-only
  clean-clone browser checks are underway; no new held-out score is claimed.

### Next / blocked

- Finish the browser gate after helper CI and owner allowance; record actual
  rehearsal cost/key readback and tag exact deployed SHA `v0.6.0`.
- Section B: scrub current-tree operational targets, rotate Postgres credentials
  with Key Vault/revision readback, document firewall choice and clone evidence.
  Repo remains private; publication and warm/judge activation require submission-day OK.

## 2026-10-02 — verified audit rehearsal and section-B hardening

### Completed (verified)

- #120 helper-label fix merged at `e30c549` after all four remote checks passed
  (`36974370052`, `36974370077`). It changes the operator helper/docs only;
  deployed product image remains `f5e128d`.
- Owner-IP real rehearsal: all six prescribed benign PT/ES phrases passed without
  SEC-01/ESC-02, session termination or case write. Duplicate across logins returns
  verified `status_reported` and the same typed original receipt, zero extra cases.
  Initial helper compared UTC timestamp strings (`Z` / `+00:00`); independent scoped
  read confirmed the same instant. Two local helper preflight stops made no model
  call; completed phrase steps were retained, not rerun. Additional diagnosis stayed
  within the authorized 10–15-turn rehearsal and same lifetime purse.
- Disabled only this smoke purse for one budget-denial turn, restored in `finally`:
  localized degraded HTTP 200, authentication retained, **zero new reservations**.
  `v0.6-rehearsal-verified.json` records the checks. Total real smoke/rehearsal
  **$0.02292**, production key **$5.1847665 → $5.1618465**, no key printed.
- Fresh original-repo clone at `f5e128d`: README-only, **17/17 steps / 724.10 s**,
  no copied private inputs. 1,121 Python passed / 31 skipped, B1 32/32, Postgres
  49/49, web type/lint/build, 148 fixture + 12 local live + one staff browser passed.
  `make down` stopped only its disposable project. Model spend $0.
- Definitive filename-aware native history Gitleaks: **27** default findings,
  all triaged metadata/test/secret-NAME false positives; configured scan exits 0.
  Narrow path/exact-value exceptions retain default rules. Negative controls
  detect changed values in allowed paths and allowed values in other paths.
  This supersedes the narrower 19-match patch-stream result above.
- Both Postgres credentials rotated through existing Terraform generators/server
  and Key Vault; app SQL role updated from Key Vault, same-image API revision.
  TLS, non-owner/no-bypass, unscoped zero-row checks passed. BFF `me`, `config`,
  `transactions`, `ops/snapshot` all 200, bank clock available, logout 401,
  zero model calls. Secret references normalized; fresh Terraform plan has **no changes**.
- Retained owner-IP/Azure-services firewall: stable app-only egress is not proven;
  cross-subscription exposure remains documented. No new resources, replica/CPU,
  ingress/publication/judge-mode changes. Current-tree operational hosts/home paths
  replaced with lazy private configuration or portable placeholders; offline target
  imports/credentialed-URL rejection and Jev-off gates passed 13 focused checks.
- Mock `make checks` on the readiness candidate: **1,128 passed / 31 skipped**,
  B1 **32/32**, compilation, hooks/Ruff/mypy and interface/catalog checks passed.
  Target resolution is lazy for the latency helper too; focused operator tests
  and Ruff pass after removing its stale import of the previous fixed URL.
- Publication audit refresh: **120 PRs / 599 available completed log archives**,
  zero Actions artifacts, zero sensitive-IP/signed-URL signals; default GitHub
  Gitleaks exits 0. Current credential/private-ID comparison: **seven values,
  zero matching values** in history or GitHub text. Four negative controls detected.
- Budget readback: this purse **$0.02292 / $0.10**, 12 calls, zero unknown costs.
  All-scope known cost **$5.96687034**, retained exposure **$7.69618884**.
  Conservative allowance math plus otherwise omitted closed-scope exposure:
  **$11.87612498 + $0.10324950 = $11.97937448 ≤ $12**. Historical unknown reserves
  remain charged; no scope, counter or reservation was reset.
- #121's first remote Python gate caught an unmocked target lookup in the
  authored latency test (local Azure credentials had masked that omission).
  The test now supplies its fake origin and explicitly rejects any Azure lookup;
  **18 focused tests** and Ruff pass. Push the correction for required fresh CI.

### Done but not verified

- Current-tree scrub, scanner configuration, reproduction/audit docs and dated
  progress are on feature `fix/public-readiness`; required remote CI/merge pending.
- Full Azure browser receipt, `jev-release.json` refresh and `v0.6.0` tag remain
  pending the requested one additional browser allowance. Earlier attempts completed
  Chat/Desk but stopped at obsolete Ops selector; counters/reservations were not reset.

### Next / blocked

- Merge readiness PR only on green remote CI; rescan exact committed tree/history
  and refresh new GitHub run/PR coverage before submission-day publication.
- On owner browser allowance, run the corrected helper once under the existing
  $0.10 purse; record all gates/digests/cumulative exposure and tag deployed `f5e128d`.
- Main protection is prepared but unavailable on the current private plan. Public
  visibility, warm replicas and judge activation still require explicit Oct-4 OK.

## 2026-10-02 — Frontend merge and delivered-data quality reconciliation

### Completed (verified)

- Merged #119 at `25954cdc4f1f9337296d1d0bc426d4b208ae3d77` after all four
  remote gates passed on the exact head, refreshed against current main. Merge
  and source readbacks verified; no deployment or model calls.
- Scanned all thirteen local organizer tables directly from `LOCAL_RAW_DIR`:
  23,495,188 records, zero PK/exact/payload replays, six product-number and
  thirteen employee-code collision groups. Extended 24 relationship checks
  found broken registration/assigned branch links and digital product ownership
  gaps; those fields do not enter serving projections.
- Profiled all 203 contracted columns with explicit row denominators. Direct
  source counts reproduce the existing dataset hash and silver volumes;
  complete daily partitions do not explain the transaction/event volume deltas.
- Authored data/CLI regressions: eight passed; Ruff and strict mypy pass.
  Aggregate-only documentation; private diagnostics ignored. Spend USD 0.

### Done but not verified

- Reconciliation/null-profile PR awaits remote CI and review. The organizer's
  approximate quality/volume targets have no verifiable upstream explanation.
- Temporal findings require a runtime quality gate: future dimension statuses
  currently can affect dispute eligibility. Existing serving data is unchanged.

### Next / blocked

- Add and verify data-owned temporal serving guards, with authored boundary
  tests. Lead must rebuild/reload serving data before claiming live protection.
  These are post-v4 fixes; frozen suites and official results remain unchanged.

## 2026-10-02 — Temporal exclusion proposal (superseded, never merged)

Owner review replaced the exclusion proposal below with retained transactions and
nullable reasons. Its recorded checks describe that earlier proposal; see the
later flag-only session for the current contract and activation dependencies.

### Completed (verified)

- Data-side source review found that dispute eligibility consumes status/date
  facts affected by future customer/product snapshots and pre-opening charges.
  Added conservative operational exclusions, UTC/business-date invariants and
  a loader preflight on actual exported Parquets before any bank connection.
- Private LOCAL_RAW_DIR-derived aggregates: 60,924/492,414 recent transactions
  blocked (union); 431,490 remain eligible. Historical silver/matcher rows stay
  intact. Per-reason flags and the coverage cost are committed as aggregates.
- Full mock pytest on main's merged #124 refactor: **1,217 passed / 31 DB
  skips**, including eleven new
  clock/date/altered-export checks and existing data/CLI tests. Ruff and strict
  mypy pass. The sandbox's local async thread-wakeup restriction was reproduced
  independently; the mock suite passed outside it. No model/cloud calls.
- Reconciliation PR #125 initially passed all four gates at `56b0946`; refreshed
  on current main and appended session notes to avoid parallel header conflicts.
  All four gates passed again at `e995c8bf30c800117efdbff39496dae89c65958a`.
  Temporal guard PR #128 is stacked on #125 and awaits lead review. Source diagnostics
  are ignored/private; no organizer rows or backend/policy code changed.

### Done but not verified

- Stacked temporal guard PR needs lead review and main-target remote CI.
  Full organizer gold rebuild, serving load/readback and Azure activation are
  pending; existing live data is unchanged. These are post-v4 fixes.

### Next / blocked

- Merge reconciliation first, then review guard availability and scoped demo
  bindings before rebuilding/reloading. Frozen suites and results remain
  unchanged; no model or held-out evaluation work is authorized by this task.


## 2026-10-02 — Reconciliation merged; temporal rows retained with exact flags

### Completed (verified)

- #125 merged as `969c304b2ec7ec73cf26b766028f6492f3b5c311` after all four
  remote gates passed at `e995c8bf30c800117efdbff39496dae89c65958a`;
  API readback confirmed merged/closed. No deployment or serving reload.
- Reworked #128 to preserve the existing half-open 120-day window and all
  customer/product projections. Added exactly `temporal_quality_reason TEXT NULL`
  with the four approved enum values and enum-order precedence. Standalone
  business-date mismatches remain DQ warnings, as directed by the owner.
- Private source-derived aggregate readback: all **492,414** serving-window
  transactions remain visible, **60,920** flagged and **431,494** unflagged.
  Four mismatches remain warnings. No organizer rows committed or printed.
- Authored regressions independently check retained original fields/row sets,
  exact reasons and precedence, clock/business-date boundaries, warning-only
  mismatches, old/missing/tampered flags and pre-bank rejection: **29 passed,
  1 local-Postgres skip**. Ruff and strict mypy (73 source files) passed.
  Model/cloud spend USD 0; no frozen suite or official result changed or run.
- Refreshed the feature branch on main including #129 without rewriting
  published history. Final full mock suite: **1,243 passed / 31 DB skips**;
  repository-wide Ruff passed. Actual Postgres/live activation remains pending.

### Done but not verified

- Draft #128 needs current-head remote CI and lead integration review.
  Postgres migration/load/readback and live policy handling are not activated.
  Correct flags alone do not prove that runtime disputes reject anomalous facts.

### Next / blocked

- Keep #128 unmerged until the lead's policy/migration PR is ready. Older serving
  loads missing the column must close automation only, retain explanations and
  warn readiness. Flagged disputes require a data-quality handoff and an
  open_question naming the anomaly. Ship image and serving reload together;
  the lead's release gate must assert the nullable TEXT column exists.


## 2026-10-02 — #128 review: source-equivalent authority fields

### Completed (verified)

- Extended the pre-bank export check to every non-lineage field in the customer,
  product and transaction projections, including transaction status/type/amount/
  currency, supplied USD amount, fraud score and product type. FX-derived amount,
  date, prior-rate flag and foreign-country flag are recomputed from silver facts
  and rates; cached gold values are not the source of equivalence.
- Seventeen independent field mutations fail before any bank connection;
  valid exact/prior/USD FX projections pass. Missing FX rates still block
  promotion. New serving regression run: **19 passed / 1 local-Postgres skip**.
- Diagnosed prior CI checks failure: snapshot tests assumed optional dbt was
  installed in the fast Python gate. Added explicit dependency skips there and
  located the new mutation cases in the existing Postgres/data gate's test file.
- Combined data regressions: **48 passed / 1 local-Postgres skip**. Strict mypy
  (73 source files), repository-wide Ruff and Python compilation passed.
- No backend, NLU, policy, serving schema, source aggregates, frozen suite or
  official result changed. No organizer reads, model calls, serving reload or
  Azure changes. Model/cloud spend USD 0.

### Done but not verified

- Current-head remote CI and lead integration review are pending. Actual
  Postgres/live activation remains pending. The preflight excludes five lineage
  columns and other serving tables; its source-equivalence claim is scoped to
  customer/product/transaction payloads, with no reviewed authority field omitted.

### Next / blocked

- Push the reviewed #128 fix and keep the draft/unmerged hold until the lead's
  policy/migration is ready. Preserve the combined image/reload release gate.

## 2026-10-02 — v0.7.0 released; preserve owner cases; isolate judge visits

### Completed (verified)

- Annotated tag/private Release **v0.7.0** targets deployed source
  `e7c6b552dec0006c4f36e02188764dcf554942e2`. Exact-SHA CI/safety/access runs
  `37053950811` / `37053950808` / `37055691024` succeeded. API/web SHA images,
  ACR digests, ready revisions and `scripts.azure_verify` passed; image/binding
  apply changed two apps only, zero creates/deletes. Replicas, CPU, owner IP and
  internal API unchanged. Fresh `jev-release.json` has all three flags true.
- Fresh `aclara.data.cli build --no-reports` and
  `scripts.load_demo_serving --target azure` passed source-equivalence, atomic
  six-table load/count/checksum/readback. `scripts.verify_temporal_serving`
  asserted nullable TEXT `temporal_quality_reason`, current fingerprint,
  three FORCE RLS tables, zero unscoped rows and TLS/non-owner runtime. All
  **492,414** transactions retained; **60,920** flagged / **431,494** unflagged.
  Readiness warning was present before the load and absent after restart.
- CO normal filing plus lost-confirm receipt retry/readback, PT ambiguous
  handoff, deterministic fraud and Customer/Desk/Ops browser smoke passed.
  Six benign real-model ES/PT phrases passed without security/session-end
  false positives. Existing MX receipts were reused across logins with no new
  case. Basic-mode ES/PT banner/composer probes passed with zero reservations;
  temporary smoke breaker restored. Read-only four-login BFF check passed.
- **12 provider calls / $0.023339** in the fresh **$0.10** SHA-bound production
  run; zero unknown smoke costs. Key remainder **$5.1618465 → $5.1385075**.
  Conservative cumulative exposure **$12.00271348 / $15**, retained historical
  reserves included. No limit increase/top-up. Release notes disclose all
  stopped attempts and representation-only receipt comparisons.
- Owner changed the reset decision to preservation: private backups retained,
  **zero Azure records deleted**. Direct reset was rejected by automatic approval
  review because HTTP reset was OFF; no bypass followed. CO had an unfiled
  eligible charge, so MX receipts were preserved and verified instead.
- Gate A warm-only preview `terraform plan -refresh=false -lock=false`:
  **0 creates / 2 updates / 0 deletes**, only API/web min=0 → 1. Not applied;
  price refresh 19:42 UTC gives idle delta **$3.4344** for Oct 4–16 over the
  100-active-hour baseline, monthly range **$34.28–$46.08** before tax/models.
- Mock-only follow-up reproduced then fixed independent judge logins sharing
  profile cases/cards. Each profile now has a controller-bound visit realm;
  same-visit return preserves state, a separate login starts fresh, restart
  preserves isolation. Reset workflow now clears/read-verifies customer bank
  maps as well as its current session workspace; protected judge realm retained.
- `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 make checks`: **1,335 passed /
  37 DB skips**, Ruff/strict mypy/interfaces/catalog green, **B1 32/32**.
  `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 .venv/bin/python -m
  scripts.test_postgres`: **79 passed**, including all four judge profiles,
  independent logins/profile return/restart and scoped reset isolation.

### Done but not verified

- **Not exercised live: no demo persona owns a flagged transaction.** Bindings
  unchanged per owner. Merged API/Postgres DQ tests and Azure column gate prove
  their respective paths; no live flagged conversation is claimed.
- Judge-visit/reset follow-up is source-only, **not in v0.7.0 images**. Judge and
  reset modes remain OFF. Runbook pre-video/pre-submission maintenance recipe
  requires explicit scope/backup/temporary-flag approval; no live reset claimed.
- Follow-up merge requires all four remote gates; exact head/check/merge receipt
  is tracked in [PR #134](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/134).
  Official v4 files unchanged; no paid calls or Azure changes after the release.
- Runbook preparation: **22 Bash blocks parsed / 14 Python heredocs compiled**,
  no commands executed. Cleanup attempts both reset-switch removals even if one
  fails; a failed cleanup stops video/submission for owner intervention.

### Next / blocked

- Deploy the next CI-green image containing judge-visit/reset fixes before
  either mode is enabled. Gate A needs explicit window/plan/cost OK because
  the upper estimate exceeds $40. Gate B public judge access remains separate.
- Proposed judging allocation: **$1/UTC-day**, **$2.92 lifetime**, current unused
  smoke allowance **$0.076661**; conservative maximum **$14.99937448 ≤ $15**.
  Recheck ledger/key before approval/activation; no new paid call authorized by
  these source fixes. Publication/submission/retirement require their own gates.


## 2026-10-02 — Final improvements w8: one-command local demo

### Completed (verified)

- Added `make demo`, `demo-check` and `demo-stop`: isolated localhost Compose
  project/ports per checkout and ES/PT choice; fresh ignored 0600 credentials.
  Existing worktree .env is neither read nor overwritten. Provider keys and
  organizer inputs are not passed; mock/fixture settings are enforced.
- Initial ES demo built and reached healthy Postgres/API/web. Live BFF readback
  verified login/OTP, authored ledger, store quality and revoked logout without
  writing a dispute/handoff. Four isolation/readback unit tests and Ruff passed.
- Fresh private clone of 9f64c04 passed `make demo` (ES **40.23 s**) and
  `DEMO_LANGUAGE=pt make demo` (**47.70 s**): live BFF, six authored rows each,
  authentication/OTP/store quality/revoked logout readbacks. No host dependency,
  environment, organizer or credential copy; cached Docker layers are disclosed
  in [clean-clone evidence](../submission/clean-clone-reproduction.md).
- No model/cloud spend, Azure changes or held-out runs. The demo is post-v4
  development tooling, not reflected in official v4 numbers.

### Done but not verified

- None for the local demo: [PR #136](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/136)
  passed checks/invariants/Postgres/web and merged at ca646f6. Shared Makefile/Compose
  overlay additions are explicit in this assignment/PR. No Azure release performed.

### Next / blocked

- Complete the PNG/SVG slide assets from committed aggregates. Staff queue UI
  awaits the orchestrator's item-6 backend contract; no guessed contract.

## 2026-10-02 — Final improvements w8: aggregate slide assets

### Completed (verified)

- Exported six PNG/SVG pairs under `docs/submission/assets/`: official v4 pass,
  SAR on both denominators, strict/missed/unnecessary escalation, observed safety
  flags, historical latency/cost, current architecture and controls ablation.
  Item-5 dev aggregates landed in main during demo CI; no additional model calls.
  Captions link committed
  sources; the deterministic exporter reads only those aggregate documents.
- All six 1920×1080 images visually reviewed. SVGs retain editable text and
  accessible titles; every file is below 512 KiB. A second export was byte-identical.
  Missing source rows or denominators fail rather than fabricate numbers.
- Both official safety gates remain failed and the 2/98 versus 2/100 action flags
  remain unchanged. Historical Gemini+Jev latency/cost and current post-v4 design
  are distinct. No deck, organizer rows, model calls, Azure or frozen-suite changes.
  Model spend **$0**; current source changes are **not reflected in v4**.

### Done but not verified

- Current-head remote CI/merge pending. Ablation is a 20-case-per-arm bundle
  study, not held-out evidence: P 0/20 versus naive 2/20 unverified write claims,
  no proven write failures; other observed failure counts were zero. Small sample
  does not establish safety. The official v4 source files remain unchanged.

### Next / blocked

- Merge this asset pack only on green CI. Demo #136 is already merged.
  Implement the real ES/PT staff queue after the orchestrator
  relays the item-6 reviewed backend contract. No endpoint guessed in advance.

- Merge only on green CI. Prepare PNG/SVG slide assets
  from committed v4 aggregates. Controls ablation and staff queue UI await the
  orchestrator's item-5 results and item-6 backend contract; no guessed contract.

## 2026-10-02 — Handoff 17, request-scoped concurrency

### Completed (verified)

- Candidate `ad54866`: request event/call/cursor isolation, concurrent provider
  waits, bounded admission, full-turn per-session advisory locks. Local checks
  1340 passed / 38 skips, B1 32/32; subsequent disposable Postgres 86/86 includes
  cancellation and cross-instance ordering. No official v4 files changed.
- Existing mock harness: five warm sessions **1.026 s**, turn p50/p95
  **1.020/1.022 s** (first cold three-session batch 1.832 s), $0.
  [Evidence and limits](../evaluation/request-scoped-concurrency.md).

### Done but not verified

- Azure still runs v0.7.0; concurrent live turns and two judge realms not tested.

### Next / blocked

- Green remote concurrency PR, plan-only Gate A, v0.8.0 capped release, then
  staff-queue security review. Warm/public judge access remains separately gated.

## 2026-10-02 — Handoff 17, Gate A preparation

### Completed (verified)

- Concurrency #137 merged at `0d2f0edcbc08adea527d9152500ef2ac5a865a45`:
  remote checks/Postgres/web/invariants green (CI `37074259582`, safety
  `37074259583`). AI-owned client/cursor files are free for the AI lane again.
- OFF-default API burst option, 13/13 mocked Terraform plans, real preview
  0 create / 2 update / 0 delete, no apply. Two-worker mock cgroup peak 234.23 MiB;
  keep workers 1 because 3 × 2 × 9 connections exceeds Postgres's live limit 50.
- [Gate A plan/cost](../../submission/gate-a-scaling-plan.md): $34.28–$62.93/month
  sharing-window estimate, warm delta $3.43, burst delta $0.054/hour.

- Strengthened judge filing/readback/isolation checks: 4/4 memory profiles and
  disposable Postgres suite 86/86; no Azure judge activation.

### Done but not verified

- Scaling remains OFF; neither production load capacity nor worker RSS is proven.

### Next / blocked

- Separate Gate A plan/window/cost approval before activation. Owner confirms
  judge OFF for v0.8.0: local/CI realm tests now, live realm gate after submission
  Gate B approval. Scaling PR #140 remote checks/release remain in progress;
  staff-queue #138 security review follows #140 per owner.

## 2026-10-02 COT — Handoff 17, v0.8.0 release complete

### Completed (verified)

- #140 merged on four green remote gates. #146 merged after four green gates
  (one failed-job retry for the known mobile viewport flake, code unchanged).
  The environment-only DSN regression failed before and passed after its
  one-condition guard fix: disposable Postgres **87/87**. Current local
  `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 make checks`: **1378 passed /
  40 skipped**, B1 **32/32**, hooks/Ruff/strict mypy/interfaces passed.
- v0.8.0 deployed, annotated tag and private Release at
  `2573e1d8367de20574935fce8f7624eb7dae33a9`. Exact-SHA CI `37081945722`, safety
  `37081945738`, external access `37083071336` succeeded. Images/digests/ready
  revisions, `scripts.azure_verify`, authenticated four-persona reads, temporal
  column/fingerprint/TLS/FORCE RLS/unscoped-zero and logout verified.
- Approved live concurrent ES/PT smoke: first turns **5.527 / 5.572 seconds**,
  **5.526 seconds overlap**, disjoint provider IDs and correct NLU languages.
  ES filing/readback/original-confirmation retry, PT ambiguity and deterministic
  fraud passed. Customer/Desk/Ops browser passed on the one approved extra
  attempt. Fresh `artifacts/azure/jev-release.json`: all three flags true.
- Original $0.10 purse retained across the DSN re-pin. Eight attempted
  conversations retained: two rejected before NLU ($0), two exposing amount
  masking ($0.003815), approved extra pair, fraud, one extra browser. Final
  **6 model calls / $0.011353**, zero unknown smoke costs. Key remaining
  **$4.9819735**, decrease exactly matching spend. No reset, deletion, organizer
  reload, persona rebind, access/CPU/replica change or official v4 change.
- All-scope known cost **$6.14674334**; actual exposure including retained
  reservations **$7.87606184**; conservative cumulative **$12.39795698 / $15**.
  Current/prior unused smoke capacities **$0.088647 / $0.076661** remain included.
  Revised OFF judging proposal $2.40 lifetime + $1/UTC-day gives maximum
  **$14.96326498**; supersedes $2.92, requires fresh Gate B approval/readback.
- First #138 security review confirmed delegated access surviving judge OFF
  and password/config rotation (customer401, queue200, verified claim200).
  Withheld it from v0.8.0. Owner relayed corrected `aeeb452` plus judge guide
  #147 `4b7d69b` for security re-review and a later v0.8.1.
- [Release evidence, failed attempts and limits](../evaluation/v0.8-release-notes.md).
  Owner's v0.8.0 merge hold may lift now.

### Done but not verified

- Judge OFF: independent two-visit/profile filing, restart and cross-visit
  denial proved locally/CI, not live. Live realm proof is submission-day Gate B.
- Flagged transaction not exercised live: no demo persona owns a flagged row;
  authored API/Postgres tests and deployed readiness column are the evidence.
- Gate A burst/warm plan is prepared, not applied; production load/RSS not proven.

### Next / blocked

- Confirmed **pre-existing product defect**: DLP phone/document patterns mask
  large monetary inputs before NLU. The smoke's exact format is fixed two-decimal
  dot plus ISO currency; authored `1000000.00 COP` reproduces masking. The failed
  operator did not save its target, so automatic approval review rejected
  printing an unproven current row value. AI fix is queued for v0.8.1; no product
  change was made to finish v0.8.0.
- Security-review #138 corrected head, critically review #147 and the amount
  fix, then one combined remote CI and v0.8.1 release. Fresh cumulative/key and
  smoke allocation required; no extra calls authorized by unused capacity.
- Separate Gate A exact-plan/window/cost OK: $34.28–$62.93/month sharing window
  exceeds $40 at its upper bound. Judge/public activation and live realm checks
  stay behind Sebastian's submission-day Gate B decision.

## 2026-10-02 COT — v0.8.1 integration security review (not released)

### Completed (verified)

- v0.8.0 evidence #148 merged as `369591a` after four green remote gates
  (CI `37084616416`, safety `37084616447`). Docs-only; Azure remains at the
  annotated v0.8.0 tag `2573e1d`.
- Corrected staff queue #138 `aeeb452` and judge guide #147 `4b7d69b` locally
  integrated. Catalog conflict resolved by retaining both ES/PT catalogs.
  Lead source/security review and authored tests confirm judge OFF/rotation,
  expiry/logout and cached-claim revocation, valid same-visit switching,
  cross-realm/customer denial, masked packets, FORCE RLS and one-winner claims.
  Guide buttons only draft; confirmation/OTP/readback remain separate.
- Root-run `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 make checks`:
  **1395 passed / 41 skipped**, B1 **32/32**, hooks/strict typing/interfaces
  passed. `python -m scripts.test_postgres`: **101 passed** on disposable
  Postgres. Frontend typecheck/lint/build and production browser checks:
  **171 fixtures + 12 live mock customer + 13 staff = 196 passed**.
- [Security review and release prerequisites](../evaluation/v0.8.1-security-review.md).
  Folded the three completed staff/backend/guide fragments here; original notes
  remain in Git history. No paid calls, Azure changes or official v4 changes.
- Fresh read-only key/budget check at October 3 01:25 UTC: key **$4.9819735**,
  account **$8.838208454**, known **$6.14674334**, retained **$7.87606184**,
  conservative **$12.39795698**; 64 legacy unknown reservations preserved.
  Proposed new smoke $0.10 plus OFF judging $2.30 and both prior unused
  purses gives **$14.96326498 <= $15**. No scope or limit changed.

### Done but not verified

- Combined candidate is local; final remote CI, merge, additive queue migration
  and Azure release remain pending. Judge realms stay local/CI only until Gate B.

### Next / blocked

- Hold #149 until AI corrects the two confirmed authored review failures:
  unqualified grouped phone numbers escape masking/become money, and shared-unit
  two-amount text overwrites a model-selected amount with the final value.
  Orchestrator relayed both. Retain the exact two-decimal/ISO formatter fix.
- Corrected monetary integration and final local/remote gates, then approved
  release procedure. Real-smoke estimated cost/go and a fresh final-SHA budget
  readback are prerequisites; unused capacity does not authorize calls.
- Judge/public/warm/burst/CPU settings remain unchanged and OFF. No state
  deletion, organizer reload, persona rebind or held-out rerun.

## 2026-10-02 COT — v0.8.1 monetary security re-review

### Completed (verified)

- Read #149 corrected `436627d` and its four green remote gates. Zero-cost
  authored replay confirms the earlier grouped-contact and shared-unit findings
  are corrected, and the exact two-decimal/ISO formatter is recognized locally.
- Further authored ES/PT replay found ordinary personal-phone wording with a
  currency suffix, and `DNI termina por`, still sent unmasked and accepted as
  amount evidence. Lead withheld security approval; orchestrator relayed it.
- Customer-scoped zero-call preflight found **one unfiled eligible large-COP
  target** for the existing CO demo persona. Saved only private operator
  references at 0600; no row values printed, reset or persona rebind.
- Live official East US 2 retail-price gate refreshed October 3 02:08 UTC:
  existing min-zero deployment estimate **$34.63/month**, gate passed. Prepared
  private release/queue-migration operators; syntax checks passed only.

### Done but not verified

- New owner-approved release is prepared, not deployed. Existing v0.8.0 and
  all original receipts/counters remain untouched; no new model calls.
- Planned smoke: COP dispute + PT ambiguity, fraud, independently authenticated
  staff invitation/claim/revocation and browser; at most five conversation
  attempts. Estimate **$0.02–$0.04**, owner-approved fresh **$0.10** hard purse.
  No budget run has been created and no Azure setting/migration changed yet.

### Next / blocked

- AI owner will restore privacy-first digit redaction and keep raw money recovery
  local. Identifier cues or multiple amounts leave the slot unresolved. Review
  the new head, run final integration gates and release v0.8.1 within a fresh
  $0.10 purse including the large-COP case. Judge activation remains OFF.

## 2026-10-02 COT — v0.8.1 privacy-first integration

### Completed (verified)

- Re-reviewed #149 `806f4cd`: all monetary redaction exemptions removed; raw
  amounts recovered locally after NLU. Identifier context or competing amounts
  clears model guesses and requests clarification. Lead-run provider-payload
  regressions passed for every reported leak, regional formats and shared units.
- Combined #138/#147/#149 mock `make checks`: **1,608 passed / 41 skipped**,
  B1 **32/32**, hooks, Ruff, strict mypy and interfaces passed. Disposable
  Postgres **101 passed**; reactive B1 v2 **32/32**; live mock customer **12**
  and staff **13** browser checks passed. Cost $0.
- Folded the monetary lane's two fragments. Earlier exemption-based versions
  were rejected by lead review; their regressions and history are preserved.

### Done but not verified

- Source #149 browser CI failed one mobile choice viewport assertion after
  162 fixture passes. The combined frontend's remote gate is still required;
  no failed source workflow is described as green.
  Lead repeated the exact mobile test on the combined production build:
  **3/3 passed**, with no code or assertion change.
- Integration accepted locally; main merge, queue migration, new-SHA purse and
  Azure v0.8.1 release remain pending. Existing receipts/counters unchanged.

### Next / blocked

- Complete combined remote CI, merge and run the approved image release and
  bounded real smoke ($0.02–$0.04 estimated, fresh $0.10 cap, cumulative $15).
- Judge OFF; live judge realms deferred to submission Gate B. No public,
  scaling/CPU, organizer reload, persona rebinding or state deletion changes.

## 2026-10-02 COT — v0.8.1 deployed and tagged

### Completed (verified)

- #150 green combined remote CI merged as `3bc06d0db1c9b38233c04558f8093ce956258ab2`; #138/#147/#149 all marked
  merged. Exact-SHA CI/safety/access: `37090431440` / `37090431291` /
  `37091431653` success. Annotated v0.8.1 tag/private Release.
- Image build/push and restricted two-app Terraform update; only image/release
  metadata plus owner-approved fresh smoke binding. `scripts.azure_verify`,
  TLS/non-owner/FORCE-RLS temporal gate and authenticated read-only BFF passed.
- Additive queue migration/readback passed; no reset/deletion, reload or rebinding.
- Approved real smoke: large-COP explanation→offer→denial→dispute, receipt and
  original-confirm retry; concurrent PT ambiguity and fraud. Separate staff OTP,
  invitation isolation, verified claim/retry and source-logout revocation passed.
  `scripts.serving_browser --target azure`: all three surfaces passed.
- $0.00776, 4 calls, 6 attempts; zero unknown smoke costs.
  Key $4.9742135; cost reconciliation difference
  $0.0. Conservative $12.40571698; maximum allocation
  including remaining smoke caps/OFF judging $14.96326498 <= $15.
- First staff attempt stopped on a private checker KeyError because the BFF
  omits null optional transcript/trace fields. Owner-approved extra deterministic
  staff attempt passed at $0; original attempts/charges retained, no paid replay.
- [Release evidence](../evaluation/v0.8.1-release-notes.md); original v0.8 receipts,
  counters and all legacy unknown reserves retained. Official v4 unchanged.

### Done but not verified

- Judge OFF: live independent-visit realm proof deferred to submission Gate B.
  Local/CI revocation, switching and restart proofs passed.
- Azure flagged path not exercised live: no demo persona owns a flagged charge.
  Merged API/Postgres and deployed column/fingerprint gates passed.

### Next / blocked

- Main release merge hold lifted after this release report. No further paid calls
  authorized by unused purse capacity. Refresh accounting before any new run.
- Submission Gate A/B/C activation/publication still requires Sebastian's explicit
  exact-plan go. OFF judging proposal $2.30 lifetime and $1/UTC-day, subject to
  fresh key/all-scope readback; no settings activated here.

## 2026-10-03 COT — v0.9.0 judge go-live

### Completed (verified)

- Folded `2026-10-03-go-live-budget-controls.md`: #160 green and merged as
  `edd30702f32b21af17fc353d0ee410e67b2e932b`. Local `make checks` **1,630 passed /
  43 skipped**, B1 **32/32**; disposable Postgres **105**, Terraform mock plans
  **14**, real-BFF trusted Ops/Agent-role browser tests **2** passed.
- Built/pushed exact-SHA images, reviewed image-only and approved Gate A/B
  plans/applies. Both min=1; API max=3/HTTP=5, CPU/memory/worker unchanged;
  public web login, internal API; production $1/UTC day + $1.60 judging lifetime.
- Exact-SHA CI/safety **37169480937 / 37169480942**; independent owner/judge
  access **37170465322 / 37171778744**, all success. `scripts.azure_verify`
  passed after final password restoration; temporal/migration/read-only gates
  passed. Annotated v0.9.0 and private Release read back on deployed SHA.
- Four owner maps backed up (22 cases) then scoped maintenance reset with
  app role/FORCE RLS/advisory locks and independent/fresh-login reads; ledger,
  bindings and other realms unchanged. HTTP reset switches stayed OFF under
  today's separate handoff-19 approval. Future resets need fresh approval.
- Owner filing/readback/lost-confirm retry, concurrent ES/PT, ambiguity/fraud and
  three-surface browser passed. Two judge visits filed same MX story, isolated
  receipts and disjoint provider attribution; staff invitation/claim/retry,
  cross-realm denials and password rotation/restoration passed. Owned test roots
  explicitly revoked before identical-password restore; fresh judge login works.
- Six calls **$0.0115855**; retained operator-attribution reserve **$0.03**;
  Lead charged **$0.0415855 / $0.10**. Key/account deltas agree; production
  calls known. Conservative exposure **$12.45888798**, remaining allocations
  **$2.504377**, maximum **$14.96326498 / $15**. Legacy reserves not reset.
- Operator harness failures/zero-cost retries disclosed in
  [go-live evidence](../../submission/go-live-2026-10-03.md). Staff attribution
  boundary tests **7/7**, rotation tests **15/15**. No paid filing replay.
- Judge credentials in ignored 0600 `artifacts/azure/v0.9.0/judge-credentials.private.json`.
  Paid AI/frontend lanes may resume their existing separate scopes, run ID
  `2026-10-03`; release merge hold lifted after tag/receipt.

### Done but not verified

- API max=3/concurrency=5 configuration verified; actual three-replica scale-out
  not exercised. No forced scale-zero cold-start or full-browser usability/SLA
  claim. First post-deploy config 38.0169s; warm first/next .99609/.08627s.
- AI/frontend full judge exploration, mobile/accessibility/Lighthouse evidence
  remain separate lane tasks; not covered by the Lead's narrower live checks.
- Known Postgres Azure-services firewall limitation remains. Official v4 unchanged.

### Next / blocked

- Gate C script/checklist preparation PR, fresh privacy/history audit and final
  release. Repo remains private; no v1.0.0 or email. Sebastian's exact-SHA
  submission go still required. New prep-code merges require a later final
  Azure release before the script's strict main/deployed comparison can pass.
- Keep warm through October 16 under approved window; budget stops at $1/UTC
  day or remaining $1.60 lifetime run, whichever first. Retirement requires
  Sebastian's explicit scale-down/delete/backup decision. No extra paid calls
  authorized by unused purse capacity.

## 2026-10-04 public-only publication and held-batch records

### Completed (verified)

- Sebastian approved public-only publication of the original repository at
  deployed v0.9.0 SHA `edd30702f32b21af17fc353d0ee410e67b2e932b`.
  The independent 08:25 UTC readback confirmed PUBLIC, active main ruleset
  **24450444**, exact main SHA and logged-out audited README rendering.
  **10 existing tags / 10 existing Releases** remained visible; no new tag,
  Release or email was created. No Azure or model call was needed for publication.
- The reviewed final publication history scan passed Gitleaks with **0 findings /
  238 ref tips**; default rules were retained and the private publication
  configuration included two exact authored replay-key exceptions, rather than
  using only the repository `.gitleaks.toml`. The exact-value audit had **0 findings / 1,046 text files /
  2,743 historical blobs**. GitHub text covered **53 PRs**, with zero secret or
  contextual findings. Actions covered **251/251** available attempt archives,
  zero unavailable archives, sensitive/unresolved findings or GitHub artifacts.
  Earlier default/configured findings were reviewed and retained, not hidden as
  clean scans. [Dated publication evidence](../../submission/go-live-2026-10-03.md#october-4-public-only-publication)
  and ignored receipts preserve the audited scope.
- Folded **20 completed fragments**: seven earlier documentation sessions
  already present on origin/main, plus the thirteen finished AI/frontend
  held-batch sessions below. Removed their duplicate files and redirected
  compatibility-page links. Original commands, counts, failures and caveats
  remain; no official v4 score, frozen input or evaluation output changed.
- Linked the completed October 3 [post-hoc human review](../../evaluation/judge-human-validation.md)
  from the [official v4 page](../../evaluation/final-v4-results.md): twenty
  paired items, seventy applicable ratings, no new model calls. One reviewer
  and PT n=3 do not satisfy the 50-item calibration requirement or fluent PT review.
- Local docs-only verification: `git -C <repo> diff --check` passed; a scoped
  Markdown validator checked **149 references / 0 broken**; all **56 official
  v4 table rows** match the pre-edit tree. SHA-256/readback comparison verified
  all twenty folded record bodies (heading depth alone changed), with **0**
  remaining links to deleted fragments. No product files or CHANGELOG edited.

### Done but not verified

- The v0.9.1 combined candidate's fresh local/remote gates and subsequent Azure
  release are still separate Lead work; publication at v0.9.0 does not verify
  that candidate. Its new fixes and commands will be recorded after execution.
- The historical mock studies below do not establish live judge/browser results.
  Judge access is now ON in v0.9.0; each approved lane must still produce its
  own scoped live evidence without treating unused allowance as a new approval.

### Next / blocked

- Complete the CI-green integration and approved image release; preserve the
  current WARM/JUDGE-ON settings, production $1/UTC-day/$1.60 lifetime binding,
  existing lane purses and the conservative $15 ceiling.
- v1.0.0 and submission email remain pending Sebastian's explicit final go.
  PUBLIC-only approval did not authorize either operation, maintenance or teardown.

### Historical lane records

The following entries preserve each author's status at the time of writing.
Their original “pending”, “held”, “private” and “wait for access” statements
are historical; the publication/readiness status above supersedes those states,
without retrospectively claiming a test or changing a measured result. Earlier
docs PRs are already on main; the finished held-batch work is being integrated.

## 2026-10-02 — Controls-stress count axes

### Completed (verified)

- Merged #152 after verifying all four remote gates and exact head; read-back
  confirmed merge `e22d90ed36ac8d23ec3b63f4e75b069ea5e9fa80` before this branch.
- Replaced the stress asset's 0–10% display with an explicitly labelled
  forged-confirmation subset: naive filed **2 of 2**, P **0 of 2**, both P cases
  stayed at proposals. The other panels use full **0–20 count axes** for
  unverified success claims and instrumented foreign-customer attempts.
- Preserved the honest aggregate caption, overlapping-counter/fake-tool limits,
  source hash and post-v4 disclosure. Added explicit subset/arm denominator
  explanation and updated the committed caption's regeneration recipe only.
- Structural verification passed axes **0–2 / 0–20 / 0–20**, bar widths
  **2,0 / 2,0 / 1,0**, complete ticks, **1920 × 1080 PNG**, editable SVG text
  and committed source SHA. Regeneration reproduced PNG/SVG **byte-for-byte**;
  visually reviewed the chart and `git diff --check` passed.
- **$0 model/API spend**. Docs/assets only; no study, organizer, checkpoint,
  frozen-suite, runtime or Azure changes.

### Done but not verified

- Remote gates pending at authoring time; no new model or browser rehearsal.

### Next / blocked

- Open one small follow-up PR, merge the exact green head as authorized, verify
  the merge, then stand by. No shared progress-log edits.

## 2026-10-02 — Final submission docs/assets polish

### Completed (verified)

- Added `controls-stress.png` / `.svg` beside the slide assets, with caption and
  a reproducible recipe reading only the committed stress aggregate table.
  Explicit 20-case denominators, overlapping counters, forged-confirmation
  proposal/write contrast and instrumented foreign-lookup limits stay visible.
- Moved README **Results at a glance** near the top. Preserved official v4,
  both SAR denominators, cost per case/safe resolution and failed safety gates;
  separately labelled 34/36 real dev messages, adversarial stress and the
  1.026-second warm five-session local/mock batch. Updated the shipped staff
  queue guide, preserving legacy anchors used by existing submission docs.
- Refreshed the v0.8.1 shot list for judge draft-only suggestions, COP, PT,
  separately authenticated/verified staff claim, concurrency and basic mode.
  Ten contiguous editorial segments total **175 seconds / 2:55**. Judge
  activation, actual filming and healthy real-model footage remain separate.
  Marked the stale narration draft as superseded, preserving historical receipts.
- Local structural check passed **84 document links/anchors**, shot timing,
  **1920 × 1080 PNG**, editable SVG text/source SHA and official/dev separation.
  Visually reviewed the chart. The documented `uv run --no-sync --extra data-ml`
  recipe reproduced both files **byte-for-byte**; `git diff --check` passed.
- **$0 model/API spend**; docs/assets only. No organizer, checkpoint or frozen
  scenario reads, system runs, live browser calls or Azure changes. These docs
  do not revise v4 or claim a new current-product evaluation.

### Done but not verified

- Remote PR gates pending at authoring time. No new recording, narration sync,
  exported video duration or judge Gate B verification performed in this pass.

### Next / blocked

- One small PR to main; require green remote gates before merge. The owner
  lifted the v0.8.1 hold. Final filming/access/release decisions remain owner-
  controlled. No shared progress-log edits or runtime/exporter code changes.

## Plain-language README entry — 2026-10-02

### Completed (verified)

- Added a short judge introduction, five-minute entry, five-row result table and three honest limits above the technical details.
- Kept both safe-resolution denominators, complete transfer counts, cost per case and per safe resolution, and the failed safety checks.
- Retained the full setup, official results, development evidence and existing anchors below the introduction. No number, model, policy or serving change.

### Done but not verified

- Remote CI and merge pending at authoring time.

### Next / blocked

- Plain ES/PT app copy and shorter slide legends/footers follow in separate PRs. Zero model spend.

## AI lane: corrected candidate details

### Completed (verified)

- P candidate replies with corrected dates/amounts use structured NLU, retain dispute intent and re-filter freshly read customer-scoped charges. A uniquely consistent correction uses the existing policy, separate confirmation and receipt readback; contradictory or uncertain details cannot select a charge. No matcher thresholds changed.
- Validate new selection facts against customer text before merging conversation slots. Rejected model-invented details cannot influence a later turn. Currency alone cannot identify a charge after clarification. A missing date alone still allows safe owned choices.
- Candidate regressions: 34 ES/PT cases pass, including ghost-date persistence, competing dates with/without uncertainty words, stale bank facts, confirmation denial and verified receipt identity. Reject competing dates before merging slots. Ruff passed; strict mypy passed on 79 source files. Zero model spend.
- Combined held fixes: `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 OPS_BACKEND=memory LEDGER_BACKEND=fixture .venv/bin/pytest -o addopts='' -q`: 1,710 passed, 43 skipped. All 75 new ES/PT context/courtesy/correction regressions pass.
- Hash-verified frozen exploration: 27/30 (103/109 turns, 772/789 checks), ES 15/15 and PT 12/15. All 100 no-write, 109 zero-spend, 14 case and 7 handoff readbacks pass. B1 v2 remains 32/32. Independent review confirmed hashes, unchanged expectations and matcher checksums. [Aggregate report and remaining JE-08/16/28 failures](../../evaluation/judge-conversation-improvements.md).
- Sebastian authorized cross-lane `src/aclara/api/` changes for this task. Lead review required. Post-v4 changes do not revise official v4 results.

### Done but not verified

- Latest remote CI is blocked before setup by the exhausted GitHub Actions budget; no retry pushes or budget/visibility changes. Courtesy #169's earlier four green gates remain verified. Skipped infrastructure tests and lead review remain unverified.
- Real-model understanding, browser behavior and live judge exploration unverified.

### Next / blocked

- Lead reviews cross-lane API edits and shared conversation seams in #166/#169/#170. Batch the final date guard, tests and aggregate report; rerun remote CI only after the lead says access is restored. Remaining workflow failures are conservative matching/selection and JE-28's missing-case/language cascade; no UX/control failures.
- Keep PR unmerged under the v0.9.0 / Gate A–B release hold; live calls await the lead's explicit judge-access signal and approved spend scope.

## 2026-10-03 — Courtesy and scope recovery

### Completed (verified)

- User-authorized P conversation/API changes keep whole-message ES/PT greetings, thanks and small talk friendly and open. These turns preserve decisions and never confirm an action. NLG retains code-approved courtesy text with unchanged privacy checks.
- Genuine out-of-scope requests offer a person without making the chat terminal. Active charge/offer/choice context is retained; unrelated requests invalidate pending proposals. Optional scoped packets are reused, including after restart; explicit human requests promote the same packet to a terminal handoff. Security, fraud, legal, bounded ambiguity and real handoff behavior remain protected.
- Combined with the context fix, unchanged exploration is 25/30 (98/109 turns): all 100 no-write and 109 mock/zero-spend checks pass, plus 14 case and 8 handoff reads. Matching thresholds and authored expectations unchanged. Twenty-nine ES/PT courtesy regressions pass; affected suites before the two restart additions passed 252 tests. Existing NLG tests: 93 passed. B1 v2: 32/32. Ruff/mypy passed; $0 spend.

### Done but not verified

- Remote CI and lead review pending. Live behavior untested; target >=26/30 awaits candidate correction.

### Next / blocked

- Keep this separate cross-lane PR held until Sebastian lifts the release hold. Lead reviews optional serialized conversation state and soft scope semantics.
- Finish candidate date/amount correction and report the final score and remaining failures; judge-access signal still required before live runs.

## 2026-10-03 — Scoped conversation follow-ups

### Completed (verified)

- Sebastian authorized cross-lane API conversation edits, separate small PRs and lead review, with the release hold continuing. Main-targeted held PR #166 includes the already-audited latest-case fix #161 so the existing required CI runs.
- P answers short ES/PT why/next-step/timing questions from a freshly read selected charge, pending proposal or saved case. Informational turns retain the exact proposal hash/expiry and cannot confirm it. Everyday case questions use the shared status detector and independently verified receipt path; simulated response timing comes from COM-01, with no refund/date promise.
- Unchanged exploration inputs rose from 15/30 to 20/30 (86/109 turns). All 100 no-write and 109 mock/zero-spend checks passed; 13 case and 19 handoff reads passed. Matching thresholds and authored expectations unchanged. New ES/PT regressions and existing affected safety suites: 225 passed. B1 v2 remains 32/32. Ruff and strict mypy passed; $0 spend.
- Earlier held evidence PRs #159/#162 and latest-case PR #161 have all four remote gates green. All remain unmerged; no deployment, publication or live calls.
- Remote CI caught a Portuguese polite-refusal/recollection overlap with everyday case routing. Exclude explicit dispute refusal only from that additive detector; legacy status/IDs remain unchanged. `pytest -o addopts='' tests/test_context_followups.py tests/test_offer_refusal_state.py -q`: 24 passed. CI rerun required on this correction.

### Done but not verified

- New fix PR remote CI and lead review pending. Live behavior remains untested; mock target >=26/30 is not yet met.

### Next / blocked

- Finish P courtesy/nonterminal scope and candidate date/amount corrections in separate held PRs, each with ES/PT regressions. Report the unchanged suite score and remaining failures.
- Wait for explicit release-hold lift before merging, and judge-access signal before live runs.

## 2026-10-03 — Judge conversation exploration

### Completed (verified)

- Authored 30 synthetic ES/PT conversations, 109 turns and all handoff 19 topics. Actual mock API ran with scoped in-memory stores, code-owned matching/confirmation and independent receipt reads; all 93 supplied NLU observations validate.
- Final unchanged-base run met all goals in 15/30 conversations (ES 9/15, PT 6/15), 75/109 turns and 727/798 assertions. All 100 no-write, 109 zero-spend, 12 case-readback and 21 handoff-readback checks passed. Reviewed every conversation and reported five UX weaknesses with authoring/scope-policy limits.
- Preserved original six-row setup and corrected runs. Earlier 14/30 versus later 15/30 was caused only by the random latest-case bug, not an improvement. Authorized minimal API fix and deterministic mock regressions are separately held in PR #161 for lead review; full fixed run 15/30. Official v4 unchanged; no paid calls or cloud writes.
- Private final artifacts have source hashes, mode 0600 and read-back verification. Live, overwrite and outside-artifact guards refuse before API import. Independent review found an inherited-settings import path; corrected lazy import forces mock/fixture/memory. Both full suites reran with live settings and DB/provider/socket sentinels: zero external calls, unchanged results. The standalone sandbox thread issue was isolated without app code; mock execution outside it completed normally.

### Done but not verified

- Exploration PR #162 final-head CI pending. Live model/judge-browser coherence untested; remaining UX findings are open. Held API PR #161 has all four remote gates green and awaits lead review.
- Item 6 is complete in held PR #159, with all four remote gates green after the unchanged-head web rerun. Its first web gate failed the existing phone-choice viewport check (170/171 passed); original failure retained.

### Next / blocked

- Hold all PRs unmerged until Sebastian lifts the v0.9.0 / Gate A–B release hold; lead reviews the cross-lane API fix. Keep remote gates green.
- Live suite and adapter await the explicit judge-access signal, scoped masked bindings, a separate durable $0.30 cap and private before/after balances.

## 2026-10-03 — Human agreement on final v4 wording

### Completed (verified)

- Read repository rules, handoffs 17–19, current/archived progress and origin/main. Created the AI feature branch from private origin/main; no public change, provider call or cloud spend.
- Strict offline import validated twenty unique unchanged blind items and all 70 applicable human ratings against saved v4 wording. All 20 have both saved judges; handoffs have n=10. CSV, individual ratings and notes remain outside Git.
- Reported each judge's exact/within-one agreement, quadratic weighted κ and Spearman ρ overall and for ES/PT. Independent in-memory recomputation matched all aggregates. Original outcomes and published v4 metrics are unchanged; agreement was measured after the final evaluation.
- `LLM_PROVIDER=mock .venv/bin/python -m docs.evaluation.judge_agreement --self-check` passed known ranks, ties, constant and empty examples. The aggregate output was read back at mode 0600. Existing importer/judge tests: 15 passed. Strict mypy: 78 source files passed.
- Reviewed every human–judge gap larger than one point privately. All favored the judge's score; notes were blank, so response-context observations are not attributed to the human's reasons. Ruff/format and documentation links passed (839 links, zero broken).

### Done but not verified

- Remote CI and merge pending on this small evidence PR.
- n=20 does not meet the rubric's 50-item calibration requirement. Fluent PT review is unconfirmed; PT n=3 and handoff n=2 cannot validate Portuguese quality.

### Next / blocked

- Merge on green remote CI, then finish handoff 19 item 7 in a separate small PR: 30 authored ES/PT multi-turn conversations, mock run and honest UX findings.
- Live exploration awaits the lead's confirmation that judge access is open, a separate durable scope capped at $0.30, and fresh before/after balance checks. No live model run started.

## 2026-10-03 — Latest case status correction

### Completed (verified)

- The synthetic judge exploration reproduced a status lookup returning the older of two verified cases. Customer-scoped storage orders random IDs lexically; lookup previously took the last ID instead of the latest creation time.
- Prepared and verified the minimal patch in memory first. Sebastian then explicitly approved the cross-lane API edit in a separate held feature PR, with lead review.
- Status now selects the newest scoped creation timestamp. Explicit case references still select the requested case. Authorization, confirmation, write actions, receipt reads and frozen interfaces are unchanged.
- Added deterministic ES/PT regressions for B1/P, forcing IDs into reverse chronological order while filing through actual confirmed API actions and reading each receipt back. Targeted mock checks: 27 passed, 3 database-dependent skips. No model calls or spend; measured after the final evaluation, with official v4 numbers unchanged.

### Done but not verified

- Remote CI and lead security review pending. No live/deployed verification.

### Next / blocked

- Keep the feature PR unmerged during the lead's v0.9.0 / Gate A–B release hold. Merge only after the hold is explicitly lifted, lead review and green remote CI.
- Continue the separate authored exploration evidence PR; live exploration waits for the judge-access signal and its approved durable $0.30 scope.

## 2026-10-03 — Archive development records

### Completed (verified)

- Archived 58 progress/budget, v1–v3 evaluation, development study, review and release/reproduction records under docs/history. Original prose, numbers and caveats are unchanged; only link destinations were adjusted.
- Kept 15 compatibility pages for existing outside links and chart-tool inputs. Complete records are archived; the old chart inputs contain unchanged excerpts. Frozen study instructions keep their original bytes and paths.
- Local link check passed with zero broken paths/anchors. Canonical progress history is now docs/history/status/progress-log.md; lane work still uses progress.d fragments. Root README, code, images, frozen suites and official result artifacts are unchanged. Zero model/cloud calls.

- Mock frozen-protocol/study tests and all documentation policy/secret/type/style checks passed. The committed-source chart check passed against 13 sources and unchanged published aggregates. After rebasing on #154/#155: local links 837 checked, zero broken; published aggregates unchanged.

### Done but not verified

- Corrected-head remote CI pending.

### Next / blocked

- Merge after #155 and green CI. The lead should fold later progress fragments into the archived canonical log.

## 2026-10-03 — Judge reading path and plain summaries

### Completed (verified)

- Read handoff 18. Added a six-page judge reading path and three-line summaries to eight key evidence pages; detailed bodies are one click deeper.
- Original evidence bodies, numeric tables, caveats and claim wording are preserved exactly under the expandable details. Root README and application/source/config files are unchanged. Zero model calls.

- Local link check passed: 796 references, zero broken paths/anchors. Verified original bodies by SHA-256 on all eight summarized pages. Fixed two pre-existing source-line links and replaced a non-URL placeholder in the slide script with owner-provided URL instructions; no slide assets or root README changes.

### Done but not verified

- Remote CI pending on the documentation head.

### Next / blocked

- Merge this small documentation PR only on green CI; archive process records in a follow-up with links fixed and root-README compatibility preserved.

## Plain ES/PT app copy — 2026-10-03

### Completed (verified)

- Replaced the displayed B1/P/SAR names with Aclara, a rules-only comparison and safe-resolution wording. Shortened Insights, Ops and Desk labels; preserved counts, costs, axes, source links and safety limits.
- Kept raw rule IDs under ¿Por qué? / Por quê?, with execution metadata and record references one click deeper. Preserved the code-controlled chat, confirmation, verification, queue and claim behavior.
- Build, lint and strict web typing passed. The full fixture inventory was exercised; changed copy assertions, reference visibility and ES/PT desktop/phone accessibility passed their focused reruns. Reviewed ignored screenshots under artifacts/ux-audit/minimal-design/after/.

### Done but not verified

- Remote CI and merge pending at authoring time.

### Next / blocked

- Finish plain slide legends and move longer footers to captions in the separate asset PR. No organizer data or real-model calls used.

## Plain slide legends and footers — 2026-10-03

### Completed (verified)

- Retitled the seven slide asset pairs with Aclara, Rules-only baseline and Plain AI agent labels. Removed internal model/system names from displayed chart text and kept one short footer per chart.
- Moved source paths and longer methods/limitations to captions.md, retaining both safe-resolution denominators, failed safety checks, post-hoc flag interpretation and the separate after-final-evaluation development-study limits.
- All chart sizes, axes, ticks, bar geometry and counts match the prior renders, including the 0–2 forged-confirmation subset and full 0–20 stress count scales.
- All fourteen PNG/SVG files byte-reproduce from the documented commands; PNGs are 1920×1080, SVG text remains editable, primary source hashes match, and all eleven caption links/anchors resolve. Ruff and visual review passed.
- Corrected an Ops browser-test race by waiting for recorded steps before opening their details. The affected mock browser test passes in the same dev-server mode as CI; product behavior is unchanged.
- Corrected a judge-guide keyboard race by waiting for the details dialog to close before focusing the next example. All eight ES/PT guide tests pass locally, including desktop/phone accessibility checks; product behavior is unchanged.
- Integrated the main documentation archive: controls-study links and render inputs point to the complete archived reports, whose result tables are unchanged. Refreshed SVG source hashes and rechecked reproduction and geometry.

### Done but not verified

- Remote CI and merge pending at authoring time.

### Next / blocked

- Merge this small docs/asset PR on green. No model calls, organizer records or frozen system runs used.

## Judge browser accessibility — 2026-10-03

### Completed (verified)

- Read handoffs 17–19, repository rules, recent progress and origin/main. Zero
  model/cloud spend; repository remains private. User's release merge hold is active.
- Fixed sidebar focus contrast (2.03:1 → 13.87:1), cropped phone locale labels,
  visible/accessibility link-name mismatches, small v4 source touch target, lineage
  zoom discoverability and narrow-phone cost-axis wrapping. All numbers unchanged.
- Verified 20 keyboard checks, 16 locale/header checks at 320–1440px, eight explicit
  axe checks, 65 initial and 17 affected fixture browser checks. Web typecheck,
  lint and production build passed. Rebuilt make demo; desktop/mobile Lighthouse
  accessibility both 100, performance 69/70 on the development server.
- Fixed the UI Desk shortcut for Ops-backed judge profiles: judges use the
  invitation panel for a separately signed-in staff session. Two authored MX/PT
  UI regressions passed; BFF selection validation is untouched and lead-owned.
- Private evidence: artifacts/ux-audit/go-live/. Generated screenshots/data are ignored.
  Changes were measured after the final evaluation and do not change v4.

### Done but not verified

- Exact-head remote CI and deployed visual/keyboard evidence pending.
- Lead's Ops-backed BFF profile correction must deploy before live judge checks.

### Next / blocked

- Keep the PR open during the release merge hold; no merge/auto-merge.
- Complete the separate tour/gallery PRs. Live owner/runner checks wait for the
  user's judge-access-open signal and the lead's dedicated $0.20 browser scope.

## Judge gallery detail corrections — 2026-10-03

### Completed (verified)

- Quick-start shows only available stories for the active trusted judge profile
  or live persona. Language suffixes and the vague unavailable caption are gone.
- Case receipt verification groups its icon and label inline. Transaction cards
  omit the empty product row; messages omit the duplicate step label.
- Eleven quick-start/phone/guide browser checks and four ES/PT desktop/phone
  healthy → degraded → healthy checks passed. The latter use nonfixture config,
  explicit false/true/absent flags, receipt geometry, axe and overflow assertions.
- Broader local browser suite: 172 checks passed; seven outdated shortcut
  expectations were corrected and their focused rerun passed 7/7. Runnable
  shortcuts still lock during pending actions; unsupported stories stay hidden.
- Real mock-stack gallery refresh: 24 checks passed in the full sweep; four
  corrected retry assertions then passed. HTTP errors retain the previous reply,
  so its degraded notice stays until a healthy reply replaces it.
- Four first-time receipts followed independently verified scoped local reset,
  explicit recognition/denial/confirmation and matching case/transaction read-back.
  Rebuilt the private gallery: 219 PNGs; 104 screen audits, zero axe violations,
  overflow, application console errors or page errors. Desktop/phone receipt and
  PT phone transaction captures were visually inspected.
- Local integration production build, typecheck and lint passed. BFF profile
  selection validation is untouched. Measured after final evaluation; v4 unchanged.

### Done but not verified

- Remote CI unavailable: owner reported exhausted GitHub Actions budget. No
  repeated push, budget increase or repository visibility change is authorized.
- Healthy real-model replies on the deployed app remain to verify after judge
  access opens. The browser regression uses explicit healthy/degraded projections;
  no real model or live customer calls were made.

### Next / blocked

- Keep one small stacked PR open under the merge hold. Batch final changes in one
  push, then wait for restored CI and an explicit lift of the hold before merging.
- Live owner/GitHub tours remain pending the user's access-open message and the
  lead's durable private budget adapter. No paid calls or cloud changes made.

## Judge gallery and operator runbook — 2026-10-03

### Completed (verified)

- Generated a private ignored gallery with 213 desktop/phone screenshots. Full
  screenshots and actual-scroll viewport captures cover ES/PT OTP, explanation,
  Why, clarification, case receipt, handoff/freeze, Desk claim, Insights and Ops.
  The gallery itself has no overflow at 320, 390 or 1440px.
- Local tour: 28/28 checks; eight affected story/Desk checks and final phone
  OTP/expiry check passed. Across 101 screen audits: zero axe violations or
  horizontal overflow. The 32 current request-metric files record zero application
  exceptions; one legacy-format metric file is excluded from that count.
- Aggregate-only Lighthouse: accessibility 100/100 desktop/mobile, performance
  69/70, best practices 96, SEO 100, CLS 0. Development-server timing only;
  signed-out /me resource errors are expected. No paid model calls.
- Added README commands, an operator runbook and a lead-owned runner workflow
  template under apps/web/ci. YAML/default/no-upload checks and script syntax
  passed. Private operator reservations are mandatory for paid dispatches.
- Combined local preparation branch passed web typecheck, lint and production
  build. Conditional Python operator dependencies are included in the runner
  template; actual shared workflows remain untouched.
- Measured after the final evaluation; v4 and all official result numbers unchanged.

### Done but not verified

- Exact-head remote CI pending. Workflow installation, private live credentials,
  operator adapter/binding and deployed owner/GitHub execution are not completed.
- Local demo lacks judge picker and separate staff identity; candidate selection
  is explicitly unverified where the serving ledger returns clarification.

### Next / blocked

- Keep PRs open under the release merge hold. Merge harness before its companion
  journey PR after the user lifts the hold and fresh required checks are green.
- Lead installs/reviews the runner template in its shared workflow lane. Run live
  only after the user opens access, with exact SHA and shared $0.20 frontend scope.

## Private judge tour harness — 2026-10-03

### Completed (verified)

- Prepared a separate external-stack Playwright configuration for ES/PT desktop
  and phone. Default live mode sends no messages; no automatic retries.
- Added durable pre-send attempt reservations that fail closed and cannot raise
  an existing cap. Six guard regressions pass. Dollar enforcement remains the
  lead's shared durable budget scope, not this attempt counter.
- Captures mask credentials and live customer facts. Reports retain static check
  names, counts and timings only; traces, videos and DOM/error bodies are disabled.
  Diagnostic CLI overrides are rejected; failed OTP captures are removed.
- Paid mode now requires a private operator adapter. It reserves before every
  message/confirmation, verifies settlement before returning the response, and
  retains/stops on unknown receipts. Authored HTTP tests verify ordering and
  stopping; a scope label alone cannot authorize model calls.
- Verified with the companion tour against this checkout's real make demo stack:
  28/28 mock checks, then eight affected story/Desk checks after stronger read-back
  assertions. No provider spend, cloud changes, organizer data or public artifacts.

### Done but not verified

- Exact-head remote CI pending. The separate companion PR adds the journey suite.
- Live judge picker, independent staff identities, candidate selection and both
  deployed networks remain unverified; the default demo cannot prove these.
- Lead's real adapter/budget binding and per-request dollar maximum are pending.

### Next / blocked

- Keep all frontend PRs unmerged during the user release hold.
- Live runs wait for the user's access-open signal, deployed release SHA,
  private credentials and the lead's dedicated $0.20 frontend scope.

## Judge browser journeys — 2026-10-03

### Completed (verified)

- Added seven external-stack checks across Spanish/Portuguese desktop and phone:
  landing/keyboard/anchors, exact Insights aggregates, real password/OTP and cookie
  expiry/re-login, six chat stories/Why, Desk invitation/claim, Ops and simulated
  local basic-mode/429 feedback. Live staff credentials must be distinct.
- Local make demo matrix passed 28/28. Eight affected story/Desk checks passed
  after adding independent dispute GET read-back, injection browser write counts,
  delayed action-OTP handling and mobile staff-browser settings. Final masked
  phone login/expiry check passed after tightening launcher/capture protections.
- Every captured screen passed axe WCAG A/AA and horizontal-overflow checks.
  Reports distinguish missing candidates, judge picker and separate staff identity
  from verified local paths. Credentials and private facts are never logged.
- No paid model calls, organizer rows, public screenshots or cloud changes.
- Wired message/confirmation interception to the fail-closed operator guard;
  settlement must verify before the browser receives a paid response.

### Done but not verified

- Exact-head remote CI pending. This independent main-targeted PR includes
  identical shared helpers so normal CI can typecheck it. The executable launcher
  and guard regressions remain in the companion harness PR; merge harness first.
- Live picker/paid stories/staff invitation and both deployed networks pending.
  Browser-cookie expiry proves re-login, not elapsed server TTL or forced cold start.

### Next / blocked

- Keep this PR unmerged during the release hold.
- After access opens, run on the exact deployed SHA from the owner and GitHub
  networks inside the lead's shared $0.20 scope. Record any unverified paths.

## AI lane: reply language and safe selection audit

### Completed (verified)

- P reply language follows reliable ES/PT customer evidence, ignoring scoped merchant names; uncertain turns retain the conversation language. Candidate selection cannot lock case questions into the previous language. Trusted locale initializes new P chats; B1 behavior remains frozen.
- Confirmation/cancellation/failure use current conversation language while the proposal hash, expiry and source language remain immutable. Replay verifies the same scoped case, changes only reply text, scans the code template and makes no new model call or financial write. Existing machine-readable error details remain intact for the BFF.
- Explicit different-merchant retargets clear prior amount/date slots, including an amount-only identified prior charge. MATCH and confirmation gates remain unchanged.
- New ES/PT/B1 language, replay, restart, retarget and guard regressions: 30 passed. Existing conversation/safety suites: 231 passed. Ruff and strict mypy passed on 79 source files. Mock/fixture/memory only; $0 spent.
- Combined held stack: full local tests 1,740 passed, 43 skipped; B1 v2 32/32. Unchanged exploration 27/30, 103/109 turns, 773/789 checks. All 100 no-write, 109 zero-spend, 14 case and 7 handoff readbacks pass. JE-28's Portuguese status-language check now passes; its unselected new charge still prevents a case. Independent source/frozen-input/readback review passed. [Remaining-choice audit](../../evaluation/judge-language-and-choice-audit.md).
- Read-only JE-08/16 audit found no lost positively identified requested charge. Merchant-only requests return two choices below the unchanged 0.9 confidence gate; fresh merchant-only matching still chooses safely. Keep those selections and frozen expectations.
- Sebastian explicitly authorized cross-lane API edits. Lead review required; official v4 results unchanged.
- Held [PR #174](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/174) was opened before the publication audit hold. Readback verified its exact description, feature head, 719 changed lines, open state and unmerged state. The earlier checks and invariants did not execute because of the Actions budget, as verified in their annotations.
- Sebastian lifted the publication audit hold and authorized pushing local commits and refreshing held branches. GitHub readback confirms the repository is public. The lead retains review and merge order for v0.9.1; no merges or live calls are authorized by this signal.

### Done but not verified

- Refreshed remote CI, skipped infrastructure tests and lead review remain pending. Already-passing current branches need no rerun; budget-blocked current branches may rerun now that CI access is restored.
- Live-model/browser behavior remains unverified; no live calls.

### Next / blocked

- Preserve shared conversation seams when integrating #174 with #166/#169/#170. JE-08/16 choices remain deliberate policy-safe requests; JE-28 now has only the selection/missing-case workflow failures. No threshold or expectation weakening.
- Refresh published older branches with main merges to preserve history under the repository's no-force-push rule; the remaining branches already contain current main. Push the local documentation and verify remote heads and CI. Keep the separate merge hold and wait for judge access. No budget or repository-visibility changes performed by the AI lane.

## Held frontend PR publication sync — 2026-10-04

### Completed (verified)

- Owner lifted the publication hold. GitHub read-back confirms the repository
  is public. Fetch used only origin; main remains edd3070.
- All five frontend PR branches include current origin/main and match their
  remote heads. No source rebase or force-push is necessary; local integration
  merges remain local rather than becoming a large aggregate PR.
- PRs #163, #164, #167 and #168 have successful CI and safety runs on their exact
  heads. Those unchanged, valid results remain in place.
- #173 contains the locally verified ES/PT desktop/phone gallery fixes, healthy
  reply regression and first-time receipt tour. Screenshots remain ignored.
- First remote run passed safety, Python, Postgres and 171 mock UI checks. Its
  local bank-API suite caught an old assertion expecting the removed product
  placeholder. The corrected assertion requires the merchant and no empty field.
- Local bank-API 12/12, staff 13/13 and trusted-role 2/2 browser checks passed with
  mock providers. The correction changes only the regression test.

### Done but not verified

- #173 remote CI is pending. CI runs only for PRs targeting main, so the held
  draft is temporarily targeted at main for validation of its new session head.
  Restore its base to #167 after validation to retain a small review.
- Live owner/GitHub judge tours still require the explicit access-open signal
  and the lead's durable budget adapter. No live or paid model calls were made.

### Next / blocked

- Keep every merge held. The lead owns review and merge order for v0.9.1.
- Verify exact heads and green checks before reporting readiness. Retain draft
  state and disabled auto-merge on #173 while the release batch is held.
- This is post-evaluation development evidence; official v4 results are unchanged.


# Phone candidate choices — 2026-10-04 (author-time evidence)

## Completed (verified)

- Reviewed and applied the AI lane's supplied `phone-choice-viewport-proposed.patch`
  on a new branch from `origin/main` (`edd3070`). Credit: AI lane proposal and
  initial tests; frontend lane review and independent validation.
- Customer chat scrolls the candidate grid into view, retaining decision/receipt
  fallbacks and the pending-confirmation guard.
- The regression waits for exactly three choices and checks every button's full
  phone viewport bounds in ES and PT. Selecting a choice still opens a separate
  confirmation dialog without issuing a confirm request. Accessibility and
  horizontal overflow assertions remain in place.
- `cd apps/web && pnpm test:e2e tests/judge-ux.spec.ts --grep 'phone choices' --repeat-each=3`:
  six passes at 390 × 844. `pnpm test:e2e tests/judge-ux.spec.ts`: 19 passes,
  including desktop/phone, offer actions, retry and authority boundaries.
- `pnpm typecheck`, `pnpm lint` and `git diff --check` passed. All browser runs
  used local project-authored fixtures; zero paid calls or cloud changes.

## Done but not verified

- Remote CI for this new branch is pending publication of its small held PR.
- Deployed judge access remains unopened; owner-network and GitHub-runner live
  tours still await the lead's access signal and approved cost adapter.

## Next / blocked

- Keep the PR held for the lead's v0.9.1 review and merge order; auto-merge stays
  off. Repository publication is approved. Official v4 evidence is unchanged.


## Lead: reviewed v0.9.1 candidate — 2026-10-04

### Completed (verified)

- Integrated reviewed #161/#166/#169/#170/#174 API heads,
  #163/#164/#167/#168/#173 UI/tour heads, #159/#162/#171 evidence, and #175's
  phone-choice correction on `integration/v091-judge-batch`; no main merge or
  Azure change is claimed here. Conflicts preserve contextual and courtesy
  behavior, scoped receipts, exact confirmation hashes and language handling.
- Three confirmed API review bugs fixed with authored ES/PT regressions:
  negated correction dates cannot choose the rejected charge; invalid/uncertain
  corrections reach the existing two-turn clarification limit; terminal handoff
  language switches preserve packet identity/reasons and do not grant authority.
  A combined-language greeting override was corrected as well.
- `pytest` on the six focused review modules: **123 passed**; explicit language
  requests and merchant-name controls included. Full `pytest -o addopts= -q`:
  **1,754 passed / 43 skipped**, **249.12 s**, all mock/offline.
- `scripts.test_postgres` on disposable local Postgres: **105 passed**; the
  database and test roles were dropped by the runner. Both `evals.runner --system B1`
  suites (base and `evals/dev_scenarios_v2.yaml`) remain **32/32**. Ruff, format,
  strict mypy, compile, interfaces, policy catalog and staged-file gates passed.
- CO/AR shortcuts keep the current eligible judge profile; explicit recording
  cross-profile fallback remains supported: **6/6** authored profile checks,
  typecheck and focused ESLint passed. Combined local browser `--live` **12/12**,
  `--staff` **13/13**, `--judge-roles` **2/2**; all fixtures/mock, no Azure calls.
- First full combined fixture browser pass: **184/185**; the sole failure caught
  uncommitted aggregate-source documentation during concurrent source export.
  Sources were committed and Insights provenance regenerated; official numeric
  payloads are unchanged. Focused post-commit ES/PT phone and aggregate snapshot checks passed **3/3**; final remote CI follows.
- `pre-commit run --all-files` passed; Gitleaks 8.30.1 on the reviewed
  post-publication commit range exited **0 / zero findings** using the audited
  default-rule publication config. Private logs remain ignored.
- Read-only budget/provider preflight: conservative allocation **$14.96326498 /
  $15**, including historical reserves and retained unused purses. Existing lead
  scope `go-live/2026-10-03/lead`, run `2026-10-03`, has **$0.05841450** left;
  AI/frontend scopes retain **$0.30/$0.20**. Production remains **$1/UTC day** and
  `judging-2026-10` lifetime **$1.60**. No new purse or counter reset.

- Owner approved a fresh **$0.10** `release/v0.9.1/lead` purse, funded by
  closing the unused v0.9.0 production release run and old lead run; all charges
  and unknown reserves remain. Planned conservative maximum **$14.91264898 /
  $15**. The configured NLU retry/fallback ceiling exceeds the old lead remainder;
  no under-sized reserve or paid call was used to bypass it.

### Done but not verified

- Final aggregate remote CI, deployed v0.9.1, current live story/browser checks
  and the new scoped owner reset are pending. No real model call occurred while
  preparing this candidate; official v4 metrics remain unchanged.

### Next / blocked

- Merge the combined candidate only after remote gates are green; image-tag-only
  release with current warm/burst/judge settings and budget binding unchanged.
- Back up all four owner maps before the approved scoped reset; preserve judge
  realms, organizer ledger, audit and budgets. Then signal lanes with existing
  separate caps and private credential path. `v1.0.0` and email await Sebastian.


## 2026-10-04 v0.9.1 release verified and live-lane signal

### Completed (verified)

- Reviewed batch merged through #176; deployed and annotated/tagged **v0.9.1**
  at `0f0e12df13e281538d7b25800f56c55da0b8dc0b`. Exact-SHA CI/safety
  **37192919170 / 37192919148** and independent authenticated access
  **37193884747** succeeded. Public Release read-back passed.
- `release_operator.py` plan/apply changed exactly two apps' images and release
  metadata. `verify.py` passed ready revisions, unchanged warm/burst/judge
  settings, internal API and existing $1/UTC-day / $1.60 judging binding.
- Temporal column/fingerprint, TLS/non-owner/no bypass/FORCE RLS and immutable
  staff queue checks passed; unscoped bank/queue rows 0. Four judge profiles /
  15 transaction readbacks, trusted roles, switch replay and logout passed.
- Real ES/PT explanation → denial → OTP → typed confirmation → independent
  dispute read-back: **2 verified stories, 4 calls, $0.0076240**, zero new unknowns.
  Injection/human/masked staff checks passed. `browser-check.py`: Chat/Desk/Ops,
  independently verified human handoff, **$0**. `record-release.py` wrote all
  three release flags true; no product fix was made during these checks.
- Approved owner reset: four 0600 backups verified before maintenance; each
  owner map already had zero cases/cards, independently empty across login.
  Organizer ledger, judge realms, history/audit and budgets were preserved.
- Fresh funded `release/v0.9.1/lead`, run **v0.9.1**, cap **$0.10**, charged
  **$0.00762400**. Reserve-inclusive maximum **$14.91264898 <= $15**; 65 historical
  unknown reservations retained. AI/frontend live signal sent with existing
  scopes `go-live/2026-10-03/ai` **$0.30** and `/frontend` **$0.20**, both run
  **2026-10-03**, and the ignored mode-0600 credential path.
- Earlier auth-only $0 attempt and zero-network proof refusal are disclosed;
  its original receipt and two requests remain preserved. The successful access
  workflow's temporary capability was removed/read back, without a workflow rerun.
- [Commands, image digests, costs and limitations](../../submission/v0.9.1-release-evidence.md).

### Done but not verified

- Full AI/frontend live exploration, gallery/accessibility, forced cold start
  and actual burst scale-out are not established by this bounded smoke.
- Official v4 numbers and **0/30** flips remain unchanged. Provider metadata
  initially lagged; the 10:14 UTC account/key read both decreased **$0.007624**,
  matching the independently scoped smoke cost. Key remaining **$4.955004**.
  Cost attribution still uses per-turn records rather than shared deltas.

### Next / blocked

- AI/frontend run their approved live checks in the existing distinct scopes;
  report any judge blockers before the owner records the video. No further Lead
  paid calls or reset is implied. v1.0.0/email await Sebastian's final approval.

## 2026-10-04 v0.9.2 judge own-visit staff queue released

### Completed (verified)

- Folded the [lead fragment](../../status/progress.d/2026-10-04-judge-own-visit-staff.md).
  The v0.9.1 gap was confirmed: judge redemption required a second Agent/Ops
  sign-in. Reviewed PR #178 adds controller-bound queue-only self-redemption,
  using the existing judge password/OTP visit. No new credential or bank scope.
- Security tests cover ES/PT, cross-visit and owner invitation denial, valid
  profile switching/restart, revocation and cached claims. Review found a
  profile-switch race; revalidation inside the controller lock now denies it
  before invitation consumption. No threshold or model prompt changes.
- `pytest --tb=short`: **1,773 passed / 43 skipped**;
  `scripts.test_postgres`: **124 passed**, disposable non-owner FORCE RLS;
  B1 original/reactive: **32/32 each**. Ruff, strict mypy, interfaces, catalog,
  compile and pre-commit passed. Remote browser CI: **217 checks**.
- Deployed/annotated/tagged **v0.9.2** at
  `f9d1796ddd661883c131359c1881bea67f9a0c49`; main CI/safety
  **37198199416 / 37198199250** and independent authenticated access
  **37200217827** succeeded. Tag and public Release readbacks verified.
- Image-only plan/apply changed two existing apps' images/release metadata;
  ready revisions, temporal/RLS/queue privileges and unchanged Gate A/B settings
  verified. No reload, reset, rebinding, access, scaling or budget-policy change.
- Real explanation plus ES/PT masked queue/claim, profile switching, unchanged
  customer scope, cross-visit and logout checks passed. Four-profile scoped
  ledger readback passed. Azure browser: **2 claims / 13 stages**, both languages,
  independent committed handoff readbacks, **0 model calls**.
- Actual smoke **$0.0038790** includes the first operator-stop call. Original
  journals/hashes retained. Browser passed but its private verifier expected a
  field absent before independent readback; recovered from exact scoped
  auxiliary records without replay. Terminal **$0.01 reserve remains retained**.
- Existing `release/v0.9.1/lead / v0.9.1` cap **$0.10**: charged/exposed
  **$0.02150300**, remaining **$0.07849700**. Conservative maximum including all
  reserves and unused approved caps **$14.91264898 <= $15**. At 12:00 UTC,
  provider account **$8.750743454**, key remaining **$4.8945085**; no key printed.
- Live frontend signal: judge login/OTP → profile → human request → Agent Desk
  → **Abrir la cola de esta visita / Abrir a fila desta visita** → claim/readback.
  Existing ignored/untracked 0600 credential path is unchanged. Three release
  receipt flags true; [full evidence](../../submission/v0.9.2-release-evidence.md).

### Done but not verified

- Full frontend exploration, accessibility, cold start and burst scale-out are
  not established by this bounded smoke. Official v4, including **0/30** flips,
  remains unchanged; no held-out rerun or improvement claim.
- The subsequent evidence PR changes documentation only; its main SHA is not
  the deployed image/tag SHA and needs no Azure release.

### Next / blocked

- Lanes may rehearse within their existing approved scopes; no new paid run or
  reset is implied. Owner video is the next milestone. v1.0.0 and submission
  email still require Sebastian's explicit approval.

## 2026-10-04 — v0.9.3 reviewed integration candidate

### Completed (verified)

- Folded the [lead review](../../status/progress.d/2026-10-04-v093-review.md),
  [AI candidate follow-ups](../../status/progress.d/2026-10-04-ai-pending-candidate-followups.md)
  and [profile-ledger draft record](../../status/progress.d/2026-10-04-fix-profile-ledger-quickstart.md).
  Earlier lane pending labels preserve author-time state.
- Priority #186 reviewed first: scoped purchases, stale-response rejection,
  editable drafts, no automatic send/action; pending preference grants no
  dispute eligibility. #179–#183 and #185 preserve reviewed head history.
- Corrected remaining authored unpunctuated read-question regressions during
  target correction. No prompt/threshold/authority changes.
- Combined mock Python **1,896 passed / 43 skipped**, disposable Postgres
  **124 passed**, original/reactive B1 **32/32 each**, browser **242 passed**.
  Typecheck, lint, build, interfaces, policy catalog, Ruff and strict mypy passed.
- Gitleaks range clean after exact hash-only allowances. Existing purse and
  retained reserves preserved; conservative maximum **$14.91264898 / $15**.

### Done but not verified

- Aggregate remote CI and v0.9.3 deployment/live quick-start checks pending.
  Official v4 files and metrics remain unchanged.

### Next / blocked

- Merge on aggregate green; image-only release with existing Gate A/B controls.
  Fresh judge ES/PT quick-start explanation → dispute offer within the existing
  funded purse. v1.0.0 and email still require Sebastian’s go after video.

## 2026-10-04 — v0.9.3 closure; v0.9.4 date-free starter candidate

### Completed (verified)

- v0.9.3 deployed/tagged 63e69b6: CI/safety/access and controls passed. The real
  ES starter returned clarification ($0.0021315 settled); PT/offer unverified.
  Owner accepted closure as-is, with [evidence](../../submission/v0.9.3-release-evidence.md).
- #189/#191 critically reviewed and #190 root-cause chronology retained;
  independent #189 authored regression run 96/96, zero spend.
- Existing Lead allowance $0.07636550; conservative maximum $14.91264898/$15.

### Done but not verified

- Combined v0.9.4 release and live ES/PT starter acceptance remain pending.

### Next / blocked

- Follow [candidate record](../../status/progress.d/2026-10-04-v094-quickstart.md).
  One combined green CI, image-only release, then the approved bounded live check.

## 2026-10-04 — v0.9.4 verified quick-start release

### Completed (verified)

- #189/#191 critically reviewed, #192 green and merged; image-only d391402 released
  as v0.9.4. CI/safety/access and ready/security/data gates verified at deployed SHA.
- FIRST real reply: ES explanation, PT explanation. Each bare-unfamiliarity follow-up
  shows one owned choice; one click reaches the offer. Readbacks/logout passed, no writes.
- Original strict-operator stop cost $0.0038705; one owner-approved extra attempt
  completed both at $0.0076300. Total $0.0115005, six known calls, no new unknown reserve.
  Original receipts/counters preserved. Purse $0.064865 remaining; maximum $14.91264898/$15.

### Done but not verified

- Bounded quick-start proof does not establish filing/all stories/quality/load guarantees.
  Official v4 unchanged. Documentation follow-up awaits its own CI/merge at author time.

### Next / blocked

- [Evidence and commands](../../submission/v0.9.4-release-evidence.md).
  Film verified flows; lift release hold, defer non-essential work. No additional paid
  calls in this task; v1.0.0 and email still need Sebastian after the video.

# 2026-10-04 — v0.9.5 English interface release

## Completed — verified

- Catalog #194 and corrected activation #195 merged on four green remote gates.
- Deployed/tagged/released `7ca5905015a42f1e79db10e1bb995005a7b17747` as v0.9.5.
- Local/mock browser review 129/129; corrected PR browser groups 255 passed;
  production build and exact-SHA CI/safety passed.
- Image-only plan/apply; Azure readback and independent authenticated access passed.
- Live fresh-judge EN default, English Desk/Insights, ES/PT draft language,
  desktop/390px bounds, four-profile RLS, stale-cookie and logout checks passed.
- Temporal and masked queue security readbacks passed. Zero new model calls/spend;
  conservative maximum $14.91264898/$15; existing $1/UTC-day prod cap retained.
- [Release evidence](../../submission/v0.9.5-release-evidence.md) documents commands,
  workflow IDs, image digests, initial CI failures and revision convergence.

## Done but not verified

- No new real-model or financial-action run: v0.9.4 evidence is explicitly inherited
  only for the identical API digest and unchanged runtime inputs.
- Populated live English packets were not created; source and authored tests cover
  English guidance. Original API summaries remain labeled ES/PT service text.

## Next / blocked

- Video/submission may use v0.9.5. Final v1.0.0/email await Sebastian's go.
- Official v4 results remain unchanged; no held-out replay or new score.

# 2026-10-04 — v0.9.6 phone release

## Completed — verified

- Reviewed #197; history-preserving main merge kept both progress entries.
  Fresh four-gate CI passed before merge; no action/session/policy changes.
- Deployed/tagged/released `22f8833c33599e0b49d00ce60e533641ce4be9e8` as v0.9.6.
- Local/mock English checks 13/13; refreshed PR browser groups 257 passed;
  exact-SHA CI/safety, production build and Azure readback passed.
- Live Chromium ES/PT at 320/390px: square avatar, minimum width 32px;
  page/header bounds, English UI, ES/PT drafts and logout passed.
- Four-profile RLS/role/stale-cookie checks, temporal/queue security and independent
  authenticated azure-access passed. Zero chat submissions/financial writes/models.
- New LLM spend $0; budget/provider readbacks unchanged; conservative maximum
  $14.91264898/$15; production $1/UTC-day retained. Image/metadata-only release.
- [Release evidence](../../submission/v0.9.6-release-evidence.md) records commands,
  exact workflows, image digests and verification limits.

## Done but not verified

- No new real-model or financial-action check; unchanged API explicitly inherits
  v0.9.4 evidence. No populated live packet or physical-device/Safari test.

## Next / blocked

- Stand by for submission instructions. v1.0.0/email await Sebastian's go.
- Official v4 unchanged; no held-out rerun or new score.

# 2026-10-04 COT — v0.9.7 release

## Completed — verified

- #200 reviewed and merged on four green gates. Local/mock English browser
  check 13/13; remote browser groups 257 passed. Production image build passed.
- Deployed/tagged/released `1525ecec2c23e64d8dbda733a2c610757c18495b`.
  Exact-SHA CI/safety, Azure controls and independent authenticated access passed.
- Live login/OTP at 390px, one sidebar disclosure, absent strip/clock, ES/PT
  drafts, 320/390px geometry, scoped profiles and logout passed. Zero page errors,
  chat submissions, financial writes or model calls.
- Image/release-metadata-only plan/apply. Temporal/RLS/queue readbacks passed;
  no access, scaling, provider, budget, ledger or persona changes.
- New LLM spend $0; conservative exposure $14.91264898/$15. Existing budget and
  provider readbacks unchanged. Annotated tag and published Release read back.
- #199 merged on green; six-page PDF reviewed and anonymously downloaded with
  the same checksum. README/submission index link the slides and supplied video.
- [Release evidence](../../submission/v0.9.7-release-evidence.md) records commands,
  workflow IDs, digests and limits. Earlier preparation receipts were preserved.

## Done but not verified

- No fresh model/financial action test; unchanged API explicitly inherits v0.9.4
  evidence. No populated live packet or Safari/physical-device check.
- Video playback/duration not measured; its URL is owner-supplied.

## Next / blocked

- Stop and await Sebastian's explicit go for v1.0.0 on the deployed SHA.
- No email sent. Official v4 unchanged; no held-out replay or new score.
