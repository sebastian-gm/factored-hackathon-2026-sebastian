# Progress log

Session: 2026-09-26 America/Vancouver (verification continued 2026-09-27 UTC).
This summary supersedes earlier task lists; detailed evidence remains in the linked reports and Git history.

## Completed-verified

### Handoff 06 — policy, freeze and routing

- Read the full brief and handoff 06; completed tasks in order. Used only this private repository and `origin`. No credential-bearing organizer document was opened, no organizer rows/secrets were committed, and no real-model call ran in this lead session.
- PR #18 implements every requested brief §9 rule, with boundary tests and the generated [policy catalog](../policy-catalog.md). Includes strict `fraud_score > 30`, supplied loss/theft and case-burst triggers, duplicate status, complaint review flags, age/amount/FX uncertainty and deterministic language/security guards. Catalog coverage means implementation coverage, not successful handling of every phrasing.
- Card-only freeze requires fresh simulated OTP, an action-hash confirmation, authorization/policy recheck and independent committed readback. A Fraudes handoff includes the freeze outcome; non-card products only escalate. Idempotency, cancellation, stale/tampered confirmation and recovery across app instances were tested.
- PR #19 routes from six contract-allowed service-agent attributes, preferring Active Digital/Hybrid agents with least load. PT fraud fallback: PT/Fraudes → PT/Quejas y Reclamos → ES/Fraudes, with explicit flags. No eligible agent yields pending assignment. Raw identifiers, names and contact fields are excluded.
- `python -m scripts.load_service_agents --target local` and `--target azure`: committed readback passed for 1,200 projected records, 1,090 Active and exactly 7 PT/Fraudes, all Active. The API role cannot write the reference table. Azure migration and non-owner TLS/RLS readback passed.
- `python -m scripts.routing_report`: reproduced 492,414 owned transactions in the UTC 120-day window and 254 supplied fraud-score flags (>30), **0.05158%**. Explicit string-to-UTC casts resolved the initial CSV/timezone discrepancy; this is separate from loss/theft and synthetic case-burst triggers.

### Frozen evaluation and fault/security harness

- Merged frozen PR #13 after green gates. With Sebastian's explicit permission, copied only four private binding/matcher-split artifacts from the linked Data/ML worktree into ignored mode-0600 storage. Checksums matched, including the frozen binding SHA; no rows were printed.
- PR #20 preflight verified all 200 persona ownership/country/segment/partition bindings, dataset and binding hashes, zero matcher overlap and declared overlay/fault boundaries. The promoted lake was absent; authorized local raw hashes and identity projections were used instead. Twelve inconsistent redundant USD values on fictional distractors were flagged before execution without changing frozen inputs.
- `python -m evals.heldout --run`: **600 saved observations** at system `564f008` — B1 200, P/mock 200 and two P/mock repeats on the frozen 100-case subset. Model cost **US$0**. B1 has two unreachable NLU-outage boundaries (198 executed); all workload denominators retained.
- Independent dev regressions reproduced a measurement bug in generic created-state and explanation target mapping. `python -m evals.rescore --source artifacts/heldout/run-01 --output artifacts/heldout/run-01-measurement-v2` corrected measurements at `25c1c4f` using the same observations, with **zero system reruns**. Frozen labels, inputs and actions were unchanged; original aggregates are preserved.
- **Acceptance gates failed.** Both systems: 67/200 workload passes, SAR **67/193 (34.72%; Wilson 95% 28.36–41.67%)**, six forbidden dispute writes, nine materially incorrect outcomes. Handoff presence 54/66 versus complete correct transfers 0/66; required readbacks 123/140. No improvement over B1, paired difference 0, exact McNemar p=1, 0/100 flips. See [full results and slices](../evaluation/heldout-run01.md).
- No observed disclosure, step-up bypass, unverified success or refund promise in this diagnostic; bounded detectors and small samples do not establish zero risk. In-process latency excludes real models and network/cloud time. Complete aggregate language/dialect/segment/country and policy-by-segment metrics include uncertainty and sample caveats.
- Fault/security dev tests cover HTTP timeout/outage with bounded retry, DB/tool failures, expired sessions, confirmation tamper/replay, cross-customer revocation and direct/indirect injection. See [fault coverage](../evaluation/fault-security.md) and [adapter limitations](../evaluation/adapter-implementation.md). Arbitrary-language safety remains unproven.

### Additive frontend API support

- Reviewed frontend PR #17 and shipped its additive backend contracts in PR #21: trusted role/locale discovery, real logout revocation, handoff metadata, scoped Agent Desk queue/detail/claim/resolve, redacted execution traces, measured Ops counts and confirmed fresh-OTP workspace reset. Existing endpoints and customer/run/session RLS remain in force.
- Staff operations are restricted to the current authenticated workspace. The role comes from server configuration after login/OTP, never a username claim. Azure retains the customer default and reset disabled. Ops SAR/unsafe metrics are null without gold; fixture activity is labeled.
- Staff API tests passed denial/isolation, claim conflicts/idempotency/readback, OTP/reset/logout. Postgres tests recovered a claim across app instances and verified that reset retains the audit chain.
- [Frontend contract/review](../api/frontend-additions.md): PR #17 needs newer response-plan schemas, real staff BFF routes, trusted role handling and live integration tests. Its server-to-API hop must work within the owner-IP boundary. Lead did not edit frontend-owned files or merge the incompatible UI.
- These additions follow the already-proposed frontend contracts. They were made after the diagnostic and have **not** been re-evaluated on the frozen suite. No held-out-driven policy/NLU tuning occurred.

### Local recovery and startup investigation

- PR #22: `python -m scripts.backup_restore` passed on two disposable local Postgres 16 databases. All 11 operational-table row hashes matched; original session/case/handoff/trace and card state recovered; 16 audit entries and forced RLS verified. Temporary databases/login/archive were removed. The existing application database was unchanged. [Recovery report](../ops-recovery.md).
- `python -m scripts.azure_health_diagnostics` reproduced scale-from-zero startup (0 → 1 replicas), two 20-second health timeouts and readiness after about 49 seconds. Events show activation, image pull/start and a probe failure; warm requests took 0.29–0.38 seconds. The exact historical 120-second timeout remains unproven. [Startup diagnosis](../azure-startup-diagnosis.md).
- Smoke now polls only idempotent health/readiness GETs within a bounded startup period; it does not retry writes. Min replicas remains zero.

### Verification commands

| Command | Observed result |
|---|---|
| `PRE_COMMIT_HOME=/tmp/aclara-precommit-cache UV_CACHE_DIR=/tmp/aclara-uv-cache make checks` | Six hooks, file policy, compilation, interfaces/catalog; **68 passed, 7 database-dependent skips**. B1 v1 **32/32**, **12 readbacks**, safety guards. |
| `.venv/bin/python -m scripts.test_postgres` | **7/7 passed** in an isolated disposable database: migrations, forced RLS/no-context/cross-scope/pool reuse, rollback, audit/concurrency/tamper, restarts, freeze, routing projection and staff/reset persistence. Temporary database/login removed. |
| `.venv/bin/python -m scripts.backup_restore` | Full row hashes, recovered API access, audit and RLS passed on authored data; cleanup passed. Tiny-fixture duration is not an RTO claim. |
| `UV_CACHE_DIR=/tmp/aclara-uv-cache make up` | API/migration/web images built; migration succeeded; Postgres/API/web healthy. |
| `.venv/bin/python -m scripts.local_smoke` | **32/32 ES/PT**, **12 readbacks**, login/OTP, scope, auth denial, CORS, web, mock and readiness passed. |
| `gh pr checks` / main workflow readback | PRs #18, #19, #13, #20, #21 and #22 merged after all required gates passed; main CI and safety passed at `04b3d25`. |

### Restricted Azure release

- Only `Seb Azure Sandbox`, `rg-aclara-dev-eastus2`, East US 2, with explicit subscription selection. Owner IPv4/32 HTTPS ingress plus app login, private ACR, Key Vault references and managed pulls remain required.
- `.venv/bin/python -m scripts.azure_prices`: live East US 2 recheck at **2026-09-27 02:54 UTC**: **US$34.63/month before tax**, below the US$40 stop threshold. B1ms US$0.017/hour, storage US$0.115/GB-month, ACR Basic US$0.1666/day. Assumes 730 DB hours, 32 GiB, 30 registry days, 100 active hours for both small apps, 100,000 requests, no ACA free grants plus allowances. With grants: US$24.19–29.19. Estimate is not a hard spending cap.
- Built/pushed clean main `04b3d25` to private ACR after green main CI/safety. Reviewed Terraform plan in memory: only API/web image SHA and release metadata changed; **0 added, 2 changed, 0 destroyed**. Apply passed; temporary registry credentials and saved plans were removed.
- `.venv/bin/python -m scripts.azure_smoke`: **32/32 ES/PT**, **12 readbacks**, login/OTP, scoped fixture ledger, auth denial, CORS, web, mock and database readiness passed. All **182 audit entries** verified. A different API process recovered the existing case with the original authenticated session after a revision restart.
- `.venv/bin/python -m scripts.azure_verify`: both owner-only HTTPS ingress rules, release SHA, min 0/max 1 replicas, 0.25 vCPU/0.5 GiB sizing, managed image pulls, Key Vault references, non-owner Postgres runtime, required TLS, approved firewall exception, private ACR and state firewall passed control readback.
- `.venv/bin/python -m scripts.azure_dev plan`: final drift check returned **No changes**. Credential-free `azure-access` workflow **36290790744** passed; both endpoints returned **HTTP 403** from a non-allowlisted GitHub runner.
- Budget readback verified C$69.41 with 60%/100% actual-spend notifications to the confirmed owner email: approximately C$41.65/C$69.41, corresponding to US$30/US$50 at the fixed 1.3882 CAD/USD reference. Review exchange assumptions monthly; email delivery/threshold crossing were not tested.
- This documentation-only follow-up is released through the same private-image and verification process; final exact main SHA/control evidence is retained in ignored `artifacts/azure/verified.json` and the session report. It does not change the pinned diagnostic implementation.

### Earlier evidence retained

- Initial P1 validated 150,000 customers, 400,000 products and 4,425,008 transactions from 1,097 transaction objects; reported brief-reference differences. Staged fake CSV and fake-key probes were blocked and removed.
- Merged Data/ML lane evidence covers ten source contracts, nine gold marts and dataset `b86f445cb468332bde984a788ef24f72f7070952b2d9292e0259e7b8f36397c9`; six serving projections passed row-checksum readback, including 492,414 transactions. [DQ report](../data-quality-report.md) and [problem analysis](../problem-analysis.md).
- Matcher v1 lane benchmark: 6,000 train / 3,000 validation / 3,000 test queries; validation selected LightGBM, normalized-slot test top-1 95.22%, 10 wrong proposals/1,871. These are prior lane results, not a human-language benchmark rerun. Lead verified pinned artifacts and fixture integration; no retraining.
- Durable ops use non-owner Postgres, forced customer/run/session RLS, bounded pooling, transactional idempotency and committed readback. Hashed auth capabilities and append-only hash chains survive process restarts; privileged-owner rewrites of an unanchored chain remain possible.

## Done-not-verified

- Frozen evaluation acceptance failed; latest post-diagnostic packet/API changes have no frozen-suite outcome claim. Broader language coverage, full handoff correctness and safe automation remain gaps despite green engineering checks.
- AI-lane real-model rounds one through three are reported in [model comparison](../ml/model-comparison.md). Sebastian selected Gemini 3 Flash as the configured NLU/phrasing default; no real model or cross-vendor judge has been deployed. Keep `LLM_PROVIDER=mock`.
- Human dual labels and Spanish/fluent PT review remain pending. The frozen PT authoring lane used generation and second-vendor review under its separate prior US$3 approval (reported US$0.6073573); language remains model-authored. Catalog translation review remains pending.
- Frontend PR #17 compatibility/live BFF integration, shared browser CI and manual visual review remain pending. The minimal current-main UI is the deployed UI.
- Azure PITR/regional DR, realistic-volume recovery, automatic retention, sustained load, actual charges/free grants and budget-email delivery are unverified. Alert thresholds have not been triggered in a test.
- The persistent `LAKE_DIR` default is `~/aclara-lake`; this checkout's missing promoted lake was not rebuilt/migrated. Organizer transactions are not bound to the cloud API; it serves authored ledger fixtures plus the contract-allowed real routing projection.
- Exact cause of the older 120-second health timeout is unproven. New cold-start evidence is narrower and recorded separately.

## Next-blocked

- Next layer: integrate the compatible frontend and address policy/NLU/handoff acceptance gaps using **independent development fixtures**. Preserve the frozen diagnostic; do not tune on held-out cases or silently rerun/replace its report.
- Await frontend lane fixes for PR #17. Production staff identity, task-scoped cross-session authorization, durable model spend accounting and independent audit anchors remain implementation work.
- Sebastian approved the completed AI-lane comparison under a $10 cumulative cap and a separate sub-$0.50 judge smoke. Any further paid run needs a new approval; keep the selected default and Grok failure-only fallback in mock production mode. The Sonnet judge vendor remains distinct from Gemini.
- No additional permission is needed to complete the already-approved restricted release. Any expanded resources/access or estimate above US$40/month requires approval. Preserve the known dev PostgreSQL Azure-services firewall exception; VNet/private access is [production work](../production-readiness.md).

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

## Access and continuation

- Restricted web: https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io/
- Login: `demo.es.mx`. Retrieve `demo-password` from `kv-aclara-dev-eastus2` through the authenticated Azure portal; never put it in chat, Git or logs. OTP is shown in the simulated panel.
- Release inputs/control evidence stay in ignored `infra/terraform.tfvars` and `artifacts/azure/verified.json`; do not print private inputs. The local Compose stack remains running.

For the next session: **Continue from docs/status/progress-log.md. Next layer: frontend integration and independent dev acceptance fixes. Same rules.**
