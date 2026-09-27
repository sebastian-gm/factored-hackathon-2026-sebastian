# Progress log

Session: 2026-09-26 America/Vancouver (verification continued 2026-09-27 UTC).
This summary supersedes earlier task lists; detailed evidence remains in the linked reports and Git history.

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
