# Progress log

## Option A — dev gate before any re-release (in progress)

### Completed-verified

- Read handoff 12. The first final attempt is abandoned: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed. Its artifacts remain untouched; do not open or resume them.
- Initialized and read back the shared Option A Postgres budget: **scope `dev-gate/option-a`, run ID `option-a`, cumulative cap $1.00**, zero attempts and $0 charged at initialization. Both lead and AI lanes must use `PostgresSpendGate(store, scope="dev-gate/option-a", run_id="option-a")` before every provider attempt, including Jev, retries and fallbacks. Unknown usage retains its reservation. Never create separate run IDs, reset reservations, raise the cap, or re-enable a tripped breaker. Prior closed study budgets are excluded from this new allowance.

### Done-not-verified

- Ordered rebased merges #36 → #28 → #24 → #37 and the Step 3 real P dev gate are in progress. No paid Option A dev run has been made by the lead.

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
