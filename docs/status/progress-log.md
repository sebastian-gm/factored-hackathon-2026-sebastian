# Progress log

Session: 2026-09-26 America/Vancouver (verification continued 2026-09-27 UTC).
Current status below supersedes the earlier lane handoffs; their detailed reports remain in Git history.

## Completed-verified

### Handoff 06 — frozen-suite review (in progress)

- Routing PR #19 merged after all four CI gates passed at `8812dbc`. Reviewed PR #13's adapter handoff and full frozen protocol before any held-out execution; preserving all pinned suite, schema, template, tool and protocol bytes.
- The release contains 200 independently authored scenarios. Its prior lane provenance records Portuguese generation/cross-vendor review costing $0.6073573 under Sebastian's separate $3 authorization; this lead session made no model call. Human dual-label/fluent-language review remains pending.
- Sebastian authorized copying the four private artifacts from the linked Data/ML worktree. Copied canonical customer bindings and three matcher splits into ignored storage with mode 0600, verified source/destination checksums and the frozen binding SHA, and printed no rows. Frozen release validation passed; `make checks` passed 53 tests (6 database skips), B1 32/32, hooks and interface/catalog gates.


### Handoff 06 — policy and card-freeze slice (in progress)

- Read handoff 06 fully; began tasks in order without inspecting held-out labels or running real models.
- Added complete synthetic-policy decisions for status/window/type, ownership/status restrictions, verified USD amounts and uncertainty, strict fraud score >30 / three recent cases, duplicate status, complaint review flags, deterministic legal/distress/language/security guards and customer-safe explanations. Catalog version 1.2.0 links every brief rule to tests.
- Added authenticated accounts/card reads, session-bound step-up OTP, action-hash freeze proposals, confirmation/cancellation, idempotency, policy recheck, independent committed readback and Fraudes handoffs containing the freeze outcome. Non-card products only escalate. Fraud chat offers the optional freeze workflow while preserving the v1 handoff response.
- `make checks`: 51 passed, 5 database-dependent skips; B1 v1 32/32 with 12 readbacks; six hooks and generated interfaces/catalog passed. V2 B1 dev suite also passed 32/32.
- `python -m scripts.test_postgres`: 5 passed, including step-up/proposal, freeze and handoff recovery across separate app instances. No existing application database was modified by those disposable tests.
- Next in this handoff: attribute-based agent routing, then frozen-suite binding/evaluation, fault/security coverage and frontend interface requests. Azure still runs the previous verified release until this layer's green merges and final redeploy.


### Handoff 06 — routing slice (in progress)

- Policy PR #18 merged after all four PR gates passed; main CI and safety also passed at `97bfb4d`.
- Implemented deterministic routing from the six contract-allowed service-agent attributes. PT fraud fallback is PT/Fraudes → PT/Quejas y Reclamos → ES/Fraudes, with explicit specialty/language flags and an opaque assigned reference. No eligible agent produces a pending assignment instead of invented availability.
- `python -m scripts.load_service_agents --target local` loaded and independently read back all 1,200 routing projections in the existing local Postgres: 1,090 Active; exactly 7 PT/Fraudes, all Active. Names/contact details and raw IDs are excluded. The shared reference table is read-only to the API role; ops RLS is unchanged.
- `python -m scripts.routing_report` reproduced 492,414 owned transactions in the UTC 120-day window and 254 score flags (>30), **0.05158%**. Initial CSV inference/local-time conversion differed; explicit string-to-UTC casts reproduce the promoted pipeline aggregates. Score flags are reported separately from lost/stolen and synthetic case-burst triggers.
- `make checks`: 53 passed, 6 database-dependent skips; B1 v1 32/32 with 12 readbacks and all hooks/contracts passed. `python -m scripts.test_postgres`: all 6 passed, including reference-table write denial. No held-out/model run yet. Cloud projection load is scheduled with the final deployment.

### Lead integration — handoff 04 tasks 1–6

- Read the brief and amended handoff fully. Verified the existing restricted Azure deployment before integration. Only the private `origin` was used; every Git command targeted this repository. No organizer credential-bearing document was opened, no organizer rows or secrets were committed, and no real-model call ran.
- Reviewed and merged AI PR #4, Data/ML PR #6 and additive scenario-v2 PR #9 after green checks. Resolved shared dependency/documentation conflicts, preserved both optional extras, repaired schema generation and kept every v1 definition valid.
- Merged reactive evaluation PR #10, P/matcher integration PR #11, durable operations PR #14 and policy/deployment verification PR #15. Main CI and safety passed after each integration; PR #11 needed formatting and an explicit `pytz` dependency before it was green.
- V2 supports authored fixture personas, per-scenario clocks, transaction overlays, reactive response-keyed replies, bounded default replies and injected faults. Every system/scenario/repeat gets fresh state and a run ID. Gold is independent of policy. Aggregate `results.json` is the source for the rendered report: SAR denominators, attempts, containment, escalation errors, routing, handoff completeness/rubric, eight unsafe categories with upper bounds, latency intervals and costs. Organizer persona bindings and non-transaction overlays are explicitly rejected until implemented.
- P now runs through the API with structured NLU, guarded phrasing, deterministic authorization and B1 fallback. Configured mock tests exercise extraction, slots, unsafe-draft fallback, confirmation and readback. Default unconfigured mock intentionally degrades to B1; its dev results are not model-quality evidence.
- MATCH pins and checksum-verifies the calibrated v1 artifact, with scoped customer/window features and propose / choose-from-three / no-match decisions. Tests exercise all three decisions, cross-customer rejection and corrupted artifacts. No retraining or paid inference ran in this lead session.
- Alembic creates durable `ops.*` cases, card states, handoffs, conversations, turns, execution records, idempotency, auth records and audit entries. Runtime uses a non-owner role, forced customer/run/session RLS, explicit transactions and at most four pooled connections. Writes commit before independent readback. Tokens are hashed; opaque prefixes select context without granting authority. The API refuses owner/BYPASSRLS roles and returns an error when storage is unavailable.
- Audit appends use a scoped database function, sequential hashes and restricted privileges. The verifier checks scope, sequence, linkage and content hashes. A privileged owner could rewrite a whole unanchored chain; independent anchors remain future work.
- Generated the ES/PT/EN policy catalog from versioned rules with the brief's IDs, parameters, implementation references and tests. Added deterministic pending-age, amount/age-borderline and missing-FX guards. Partial/planned rules are labeled honestly. Card-state persistence is tested; the customer-facing freeze workflow remains unfinished.

### Local verification

| Command | Observed result |
|---|---|
| `PRE_COMMIT_HOME=/tmp/aclara-precommit-cache UV_CACHE_DIR=/tmp/aclara-uv-cache make checks` | Six hooks, file policy, compilation, 44 Python tests passed / 4 database-dependent tests skipped; B1 v1 32/32 with 12 readbacks and safety guards; interfaces and catalog current. |
| `.venv/bin/python -m scripts.test_postgres` | All 4 database tests passed in a disposable local database: migrations, RLS tables/views/functions, no-context/autocommit/pool reuse, cross-customer/run/session isolation, rollback, concurrent audit append, forbidden mutations, tamper detection, app restarts and serving-loader checksums. Database and temporary login removed afterward. |
| `.venv/bin/python -m evals.runner --system B1 --scenarios evals/dev_scenarios_v2.yaml --repeats 2` | 64/64 with distinct run IDs. |
| `.venv/bin/python -m evals.runner --system P --scenarios evals/dev_scenarios_v2.yaml --output artifacts/evaluation-p` | 32/32 in mock/B1 fallback; aggregate source rendered to `docs/evaluation/results.md`. |
| `UV_CACHE_DIR=/tmp/aclara-uv-cache make up` | API/migration/web images built; migration succeeded; Postgres/API/web healthy. Startup now waits for health. |
| `.venv/bin/python -m scripts.local_smoke` | 32/32 ES/PT scenarios, 12 dispute/handoff readbacks; login/OTP, scope, auth denial, CORS, web, mock and database readiness passed. |
| `terraform -chdir=infra validate` | Passed with provider execution outside the restricted process sandbox. |

The first immediate Compose smoke before health waiting hit a web startup connection failure. After services became healthy, the same smoke passed; `make up` now waits explicitly.

### Restricted Azure release — task 7

- Used only `Seb Azure Sandbox`, `rg-aclara-dev-eastus2`, East US 2, with explicit subscription selection. Never changed or used the CLI's other default subscription. The authorized owner-IP boundary and application login remain in place.
- `.venv/bin/python -m scripts.azure_prices`: live East US 2 check at 2026-09-27 01:10 UTC. B1ms US$0.017/hour, storage US$0.115/GB-month, ACR Basic US$0.1666/day. Modeled **US$34.63/month before tax**, below the US$40 stop threshold. Assumptions: 730 database hours, 32 GiB, 30 registry days, 100 hours with both small apps active, 100,000 requests, no ACA free grants and usage allowances. With grants: US$24.19–$29.19. This is not a hard spending cap.
- `.venv/bin/python -m scripts.azure_migrate_ops`: existing Azure database migrated; non-owner TLS/RLS write/readback passed. No new cloud resources were required. Admin and app credentials stay separate in Key Vault; API uses `verify-full` TLS.
- Built/pushed API and web images from clean, green main to authenticated private ACR. Temporary Docker credentials were removed. Plan and apply reported **0 added, 2 changed, 0 destroyed**.
- `.venv/bin/python -m scripts.azure_smoke`: HTTP portion passed **32/32 ES/PT scenarios with 12 readbacks**, login/OTP, scoped fixture ledger, denial checks, CORS, web, mock and database readiness. All **150 audit entries** verified, then a different API process read the existing case using the original authenticated session after a revision restart. The initial 30-poll restart check timed out; the bounded four-minute readiness check passed. It requires an actual instance-ID change, so an old replica cannot produce a false recovery result.
- `.venv/bin/python -m scripts.azure_verify`: read back both owner-only HTTPS ingress rules, image SHA, min 0/max 1 replicas, 0.25 vCPU/0.5 GiB sizes, managed image pulls, Key Vault references, approved PostgreSQL firewall exception, required TLS, private ACR and state firewall. P and Postgres runtime settings were verified too.
- `.venv/bin/python -m scripts.azure_dev plan`: final read-only drift check reported **No changes. Your infrastructure matches the configuration.**
- Credential-free `azure-access` workflow run `36285202131` passed: both endpoints return HTTP 403 from the non-allowlisted GitHub runner.
- Budget readback verified C$69.41 with 60%/100% actual-spend notifications, approximately C$41.65/C$69.41, to the confirmed owner email. These correspond to US$30/US$50 at the fixed 1.3882 CAD/USD reference. Review monthly; delivery and actual threshold crossing were not tested.

### Earlier data evidence retained from the merged lane

- P1 initially validated 150,000 customers, 400,000 products and 4,425,008 transactions from 1,097 transaction objects. Brief-reference differences were reported from pipeline output. Staged fake CSV and fake-key probes were blocked and removed during initial scaffolding.
- The merged Data/ML lane extended contracts to ten sources and nine gold marts, ran DQ gates and promoted dataset `b86f445cb468332bde984a788ef24f72f7070952b2d9292e0259e7b8f36397c9`. Six local serving tables were loaded with full projected-row checksum readback, including 492,414 serving transactions. Detailed aggregate facts and anomalies are in `docs/data-quality-report.md` and `docs/problem-analysis.md`.
- The lane's synthetic matcher benchmark had 6,000 train, 3,000 validation and 3,000 test queries. Validation selected LightGBM; its normalized-slot test top-1 was 95.22%, with 10 wrong proposals out of 1,871. These are prior lane results, not a rerun or human-language validation in this session. Model card and paired aggregate report retain the trade-offs.
- The lead reran fixture data/matcher tests and the isolated serving-loader test, not the organizer build or benchmark. Organizer lake outputs remain local. `LAKE_DIR` defaults to persistent `~/aclara-lake`; migration of the former temporary lake location is not claimed.

## Done-not-verified

- Real provider adapters and comparison code have mock tests only. Real-model comparison, final default selection and cross-vendor judge validation have not run.
- Spanish human review, PT/MX/AR cross-vendor language review and catalog translation review remain pending. No fluent Portuguese reviewer is available; model-authored language is labeled as such.
- Actual monthly charges/free-grant availability, budget email delivery, backup restore/DR, automatic retention, sustained load and manual browser visual review remain unverified. API HTTP flows and production builds were tested.
- The persistent home lake has not been rebuilt/migrated in this session. Organizer serving data is not bound to the API; cloud data contains authored fixtures only.

## Next-blocked

- No additional approval is needed for the completed restricted deployment. Keep the same owner-only access boundary for subsequent releases.
- Next layer: complete policy workflows (including card freeze and remaining catalog gaps), bind authorized serving/persona data, and build held-out evaluation. Add durable model spend accounting before any real-model public demo. These are implementation gaps, not completed features awaiting tests.
- Keep `LLM_PROVIDER=mock`. Before each real-model run, show a concrete cost estimate and wait for approval. Choose the default from the same-suite comparison; the judge vendor must differ.
- Any expanded cloud scope, access beyond the owner's IP, or estimate above US$40/month needs approval. Preserve the documented PostgreSQL Azure-services exception only for dev; VNet/private access remains production work.

## Access and continuation

- Restricted web: https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io/
- Login: `demo.es.mx`. Retrieve `demo-password` from `kv-aclara-dev-eastus2` through the authenticated Azure portal. Never put it in chat, Git or logs. OTP is shown in the simulated panel.
- Release inputs and control readback are in ignored `infra/terraform.tfvars` and `artifacts/azure/verified.json`; do not print private inputs. The local Compose stack remains running.

For the next session: **Continue from docs/status/progress-log.md. Next layer: policy workflows and held-out evaluation bindings. Same rules.**

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
