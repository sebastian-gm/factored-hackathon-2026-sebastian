# Progress log

Session: handoff 08, 2026-09-26 America/Vancouver; continued 2026-09-27 UTC.
This summary supersedes earlier task lists. Earlier release evidence remains in Git history and linked reports.

## Completed-verified

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

- Frozen acceptance after these fixes remains unknown; the preserved run-01 failure is the only full-suite result. Human labels, Spanish owner review and fluent Portuguese review remain pending. PT/dialect phrases are model-authored; prior cross-vendor authoring checks do not replace human review.
- No lead real-model comparison, selected default or different-vendor judge run. Keep `LLM_PROVIDER=mock`. Durable model spend accounting remains future work.
- Azure PITR/regional DR, realistic-volume restore, automatic retention, sustained concurrency, actual charges and budget-email delivery are unverified. Tiny local restore evidence remains in [recovery report](../ops-recovery.md).

## Next-blocked

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
- After rebasing onto the lead's current PR branch, `make checks` passed six hooks, strict mypy, staged-file policy, compilation, **136 tests passed / 9 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog. The pinned-served-model validation test also passed. The ignored `.env` and TypeSafe checkpoints are excluded from Git.

### Done but not verified

- The 150-case development labels and ES/PT fluency still lack independent human review. The three-item Jev–Sonnet judge agreement is not human validation; the 50 human-sheet ratings are blank. Other risk-cue labels have no independent gold in this suite, so only injection flags were graded. TypeSafe standard-account zero retention is not verified and Jev was not selected for production.

### Next / blocked

- Sebastian decides whether any later Jev experiment is useful; this PR does not change the selected default or judge. Keep the $12 final program on hold until the lead's acceptance fixes, matcher v2, prompt v4 merge, private binding/preflight, spend breaker and green gates are read back, then wait for Sebastian's explicit start signal.

## Access and continuation

Restricted web: https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io/
Use `demo.es.mx` or `demo.pt.br` for the three-surface workspace; `demo.es.co` and `demo.es.ar` are customer-only. Retrieve `demo-password` from the authenticated Key Vault portal; never paste it into chat, Git or logs. OTP is simulated. Re-login after the identity-source migration; prior fixture sessions do not grant organizer access.

For later sessions, paste: **Continue from docs/status/progress-log.md. Next layer: provider comparison and independent language coverage. Same rules.**
