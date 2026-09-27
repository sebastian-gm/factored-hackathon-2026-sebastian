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
- Real provider adapters/comparison have mock checks; no lead real-model comparison, chosen default or cross-vendor judge run. Keep `LLM_PROVIDER=mock`.
- Human dual labels and Spanish/fluent PT review remain pending. The frozen PT authoring lane used generation and second-vendor review under its separate prior US$3 approval (reported US$0.6073573); language remains model-authored. Catalog translation review remains pending.
- Frontend PR #17 compatibility/live BFF integration, shared browser CI and manual visual review remain pending. The minimal current-main UI is the deployed UI.
- Azure PITR/regional DR, realistic-volume recovery, automatic retention, sustained load, actual charges/free grants and budget-email delivery are unverified. Alert thresholds have not been triggered in a test.
- The persistent `LAKE_DIR` default is `~/aclara-lake`; this checkout's missing promoted lake was not rebuilt/migrated. Organizer transactions are not bound to the cloud API; it serves authored ledger fixtures plus the contract-allowed real routing projection.
- Exact cause of the older 120-second health timeout is unproven. New cold-start evidence is narrower and recorded separately.

## Next-blocked

- Next layer: integrate the compatible frontend and address policy/NLU/handoff acceptance gaps using **independent development fixtures**. Preserve the frozen diagnostic; do not tune on held-out cases or silently rerun/replace its report.
- Await frontend lane fixes for PR #17. Production staff identity, task-scoped cross-session authorization, durable model spend accounting and independent audit anchors remain implementation work.
- Before any real-model run, show a concrete cost estimate and await Sebastian's approval. Choose the default after the same-dev-suite comparison; the judge vendor must differ. No real-model approval is implied by this handoff.
- No additional permission is needed to complete the already-approved restricted release. Any expanded resources/access or estimate above US$40/month requires approval. Preserve the known dev PostgreSQL Azure-services firewall exception; VNet/private access is [production work](../production-readiness.md).

## Access and continuation

- Restricted web: https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io/
- Login: `demo.es.mx`. Retrieve `demo-password` from `kv-aclara-dev-eastus2` through the authenticated Azure portal; never put it in chat, Git or logs. OTP is shown in the simulated panel.
- Release inputs/control evidence stay in ignored `infra/terraform.tfvars` and `artifacts/azure/verified.json`; do not print private inputs. The local Compose stack remains running.

For the next session: **Continue from docs/status/progress-log.md. Next layer: frontend integration and independent dev acceptance fixes. Same rules.**

## Frontend lane — 2026-09-26/27

### Completed (verified)

- Read the new frontend handoff, brief §§6.4/8/12.4/16.5, repository rules and frozen OpenAPI. Created `feat/frontend` from latest main, then rebased the unpublished implementation onto `ad62e9c` after the lead's durable-operations merges. The longer, dotted OTP challenge identifiers are supported. No backend, policy, schema, harness or infrastructure files are changed.
- Built customer chat, Agent Desk and Ops under `apps/web/`: ES-MX/CO/AR and PT-BR formatting, password/OTP persona access, SMS panel, masked fixture products, top-three choices, exact-proposal Confirm/Cancel, read-back receipts, handoff status and a customer-safe records/rules drawer. Added queue priority/SLA/language/reasons, evidence and action timelines, claim/resolve, execution stages and model metadata, DQ/freshness/version, the existing aggregate dbt lineage image, illustrative results/cost and verified fixture reset.
- Replaced JavaScript-held access/preauth tokens with same-origin HTTP-only, SameSite=Strict cookies (Secure in production). Added route/input/output validation, Origin checks, role separation for fixtures and explicit read-back before success. Missing live staff/Ops contracts are clearly unavailable; typed fixtures require the explicit server-side feature flag and a configured password. There are no frontend model calls and no fallback from live errors to fixtures.
- Eight Playwright fixture tests passed: the three requested stories, cancellation, phone layouts, language switching, keyboard/dialog behavior, automated WCAG 2.1 AA checks, cookie visibility, CSRF/role rejection, idempotent confirmation replay, cross-browser ownership and five-attempt OTP lockout/restart. Desktop and phone screenshots were inspected and remain in ignored `artifacts/frontend/`.
- The separate live-proxy Playwright test passed against current main's B1 mock API: password/OTP, pending-charge explanation, actual dispute confirmation and case read-back, with unsupported Agent Desk correctly unavailable. It used only team-generated ledger fixtures and an ephemeral credential.
- TypeScript and ESLint passed. The production build passed using supported Webpack mode; Turbopack hit host watcher/worker-port failures, so local browser tests use Webpack polling. The worktree's ignored `.env` now uses `aclara-frontend` / ports 15442, 8212 and 3212; read-back confirmed all other entries were preserved. The separate OpenRouter key was not used, printed or committed. An explicit scan verified key exclusion and ignored screenshot paths.
- All six pre-commit hooks and the tracked-file data/secret/size policy passed after the rebase. The final production browser chunks contain neither the provider key nor the fixture-password environment reference. `apps/web/public/dbt-lineage.svg` matches the existing aggregate diagram byte-for-byte.
- Private [PR #17](https://github.com/sebastian-gm/bank-agent-lab/pull/17) is open and ready for review. GitHub `checks`, `postgres`, `invariants` and `web` all passed on implementation head `94eb350`; remote branch and PR state were read back. This documentation follow-up records those results and includes polling in the manual development command.

### Done but not verified

- Agent Desk, Ops, reset and richer metadata use labeled frontend fixtures because their live endpoints are absent from the frozen API. Signed confirmation nonces, card-freeze proposals, product masks, staff identity, step-up refresh and logout revocation remain lead-owned API dependencies, specified in `apps/web/API-PROPOSAL.md`.
- No Azure deployment or real-model run was performed. Native ES/PT human copy review and additional browser engines remain unverified. Illustrative Ops figures are not measured evaluation results; no held-out suite was executed.

### Next / blocked

- Lead review of PR #17 and its additive API proposal. Wire staff/Ops contracts and add the documented browser-test command to the shared CI workflow; this lane does not edit that workflow.
- Deploy only through the lead's existing authorized release process. No approval is needed for this private frontend PR; any future use of the worktree's OpenRouter key requires Sebastian's explicit approval.

### Frontend follow-up — submission assignment

#### Completed (verified)

- Read handoff `07-docs-submission.md` and checked PR #17 reviews/inline comments (none at the check). Integrated main through `dd957c7`; rebased locally and retained published ancestry with a merge so no force-push is needed.
- Adapted the customer BFF to the shipped account/card, fresh-OTP, freeze, duplicate-case status and security plans. Live handoffs are independently read back even when the bank omits the optional verified flag. No success is inferred from missing evidence; revoked sessions show refusal without a handoff receipt.
- Initial browser verification passed eight fixture stories and three live B1 API stories, including fresh-OTP freeze confirmation/cancellation and independent card/handoff read-back. Only project-generated fixtures and ephemeral credentials were used; no provider calls or Azure actions.

#### Done but not verified

- Agent Desk/Ops APIs and staff identity remain absent; their typed fixture mode stays explicit. Native language review and deployed frontend behavior remain pending.
- The B1 phrase “Perdí mi tarjeta” did not offer a freeze in the local probe; “Me robaron la tarjeta” exercises the implemented path. Language coverage remains a lead/AI follow-up, not a frontend policy override.

#### Next / blocked

- Final local verification: eight fixture tests, three live API tests (including freeze-dialog accessibility), ESLint and production build passed. PR #17 follow-up is ready to push; author the submission documents on `docs/submission-kit` next. Interrupt that work for lead reviews or new staff/Ops endpoints.

### Frontend follow-up — shipped staff contracts (PR #21)

#### Completed (verified)

- Interrupted submission drafting for the lead's review and merged main through `d10ac48` into PR #17 without rewriting published history. Live persona/identity, Agent Desk, traces, Ops and reset now consume the typed APIs. Versioned claim/resolve and reset require independent readbacks. Handoffs require both the API verified flag and scoped GET.
- Upstream logout revokes and verifies the capability; customer refusal/session-end and duplicate status render correctly. Live Ops uses measured current-workspace counts, keeps SAR/unsafe unmeasured, and does not display fixture results. Reset defaults to disabled and requires trusted flags, ops identity and fresh OTP.
- Four live customer browser tests, one live staff workflow and eight fixture tests passed with generated records and ephemeral credentials. Coverage includes upstream revocation, customer staff denial, freeze/cancel, claim/resolve, measured Ops, reset and automated accessibility checks. The credential-free API-hop probe passed against the local API. Initial refusal test failures were locator/authentication-wait issues corrected before the passing run.
- ESLint, TypeScript and production Webpack build passed. No Azure operations, provider calls or `.env` reads were made for these checks.

#### Done but not verified

- Azure web-container-to-API reachability under owner-IP restrictions remains unverified. The new `apps/web/scripts/check-api-hop.mjs` is packaged in the web image for the lead to run inside that runtime before deployment. Staff remains current-workspace only; Azure keeps customer role and reset disabled.
- Native language review, additional browser engines and deployed behavior of this revision remain pending. The frozen mock diagnostic predates these API/UI changes and failed its acceptance gates.

#### Next / blocked

- Publish the PR #17 review follow-up after repository hooks; lead owns shared Playwright CI wiring and release connectivity verification. No ingress expansion is authorized. Resume the submission kit with corrected held-out aggregate results and explicit failed-gate limitations.

- Published staff follow-up `1bec955` and read back its remote/PR head. All six repository hooks passed. Merged lead documentation/recovery follow-ups through `6bc0c4e`, preserving both progress records; no frontend implementation changed in this merge.
