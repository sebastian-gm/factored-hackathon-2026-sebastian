# Progress log

Session date: 2026-09-26 (America/Vancouver)

## Completed-verified

### Restricted Azure deployment

- Read and followed Sebastian's approval: only `Seb Azure Sandbox`, East US 2, resource group `rg-aclara-dev-eastus2`; stop if the live modeled estimate exceeds US$40/month. Every Azure command selected this subscription explicitly. The CLI default was not changed. The sole remote remains `origin` and the repository remains private.
- Ran `uv run --no-sync python scripts/azure_prices.py` against Microsoft's live East US 2 Retail Prices API. B1ms is US$0.017/hour; PostgreSQL storage US$0.115/GB-month; ACR Basic US$0.1666/day. Modeled total **US$34.63/month before tax**, including 100 hours with both small apps active, 100,000 requests, no ACA free grant, and state/Key Vault/usage allowances. With available free grants, the low-traffic estimate is US$24.19–$29.19. This is an estimate, not a spending cap.
- `scripts/azure_dev.py bootstrap` created the resource group and Terraform state storage with owner-IP firewall, Entra Blob RBAC, TLS 1.2+, shared-key and anonymous access disabled, versioning and seven-day retention. Corrected the personal-account Graph ID versus tenant object-ID mismatch by using the sandbox ARM token's tenant object ID. The token was held in memory and never printed or committed.
- `scripts/azure_dev.py init` initialized protected remote state. A repository-local Azure CLI wrapper forces Terraform's account/token lookups to the sandbox, resolving a multiple-signed-in-account issue without changing global defaults or copying credential files. Subscription/tenant IDs, owner IP and alert email are only in ignored local Terraform inputs; generated secrets also reside in protected Terraform state and Key Vault.
- Foundation `plan` showed 22 additions, no changes/deletes; `apply` completed 22 additions. App `apply` completed two app additions and one budget change. The final `scripts/azure_dev.py plan` reported **No changes. Your infrastructure matches the configuration.** Preserved Azure's automatically selected PostgreSQL zone to avoid unrelated updates.
- Provisioned PostgreSQL 16 B1ms/32 GiB, no HA/autogrow; private authenticated ACR Basic; Key Vault; separate API/web managed identities; and a Consumption environment. Both apps are configured for 0.25 vCPU/0.5 GiB, minimum zero and maximum one replica, HTTPS only, and one owner IPv4 `/32` ingress allow rule applied at creation. No VPN, NAT Gateway, Private Link, dedicated profile or planned maintenance was created.
- Applied the owner's explicit PostgreSQL development exception: Azure-services firewall rule plus the workstation IP. The broad Azure-services rule includes other customers' subscriptions. Documented this limitation and future VNet/private access in `docs/production-readiness.md` and `docs/azure-private-dev-plan.md`.
- `scripts/azure_dev.py seed` initialized a separate CONNECT-only application login using a generated 40-character password read from Key Vault; revoked public database access/create privileges and verified a real TLS connection with certificate verification. The API uses `PGSSLMODE=verify-full` and Key Vault references through managed identity. Administrator and app passwords are separate; none was printed or committed.
- Created resource-group budget alerts to the owner's confirmed email. Azure readback revealed CAD billing. Converted US$30/US$50 using Microsoft's checked reference of 1.3882 CAD/USD: a **C$69.41 budget**, with 60%/100% actual-spend notifications at approximately **C$41.65/C$69.41**. Readback verified currency, thresholds and recipient. The fixed conversion needs monthly review and does not track future FX automatically.
- Merged PR #5 after green checks into main at `7429038`; built the API and production Next.js images from that clean main commit and pushed them to private ACR using temporary Docker credentials, which were removed afterward. Main `ci` and `safety` both passed on that SHA. Merged the billing-currency/zone correction as PR #7 at `d0f22ab`; both main workflows passed there too. These subsequent changes affect infrastructure, verification and documentation, not app source.
- `PRE_COMMIT_HOME=/tmp/aclara-precommit-cache UV_CACHE_DIR=/tmp/aclara-uv-cache make checks` passed on the release main: six hooks, file policy, compileall, **16 Python tests**, **32/32 B1 cases with 12 readbacks**, and frozen interface checks. `pnpm typecheck`, `pnpm lint`, `pnpm build`, production Docker builds and Terraform validation also passed. Terraform provider validation required execution outside the restricted process sandbox.
- `uv run --no-sync python -m scripts.azure_smoke` passed against Azure HTTPS: **32/32 ES/PT cases, 12 dispute/handoff readbacks**, login/OTP, six scoped fixture transactions, invalid-login and unauthenticated denial, CORS, web delivery, mock mode, and database readiness. Only aggregates were logged.
- `uv run --no-sync python -m scripts.azure_verify` passed: owner-only ingress on both apps, Key Vault references, managed image-pull identities, deployed SHA, resource sizes/replica limits, two PostgreSQL firewall rules, TLS required, private registry, state firewall, and converted budget alerts. The checker handles case-insensitive ARM resource IDs and Azure's null representation of the documented zero-replica default.
- Added a credential-free `azure-access` workflow to verify HTTP 403 for both app endpoints from a non-allowlisted GitHub runner. Run `36281385648` completed successfully. It does not log in to Azure or receive secrets.

### Prior verified local work

- Brief and handoff read fully; scaffold, agent rules, ADRs, sanitized brief and R1–R14 traceability created. Staged fake CSV/key probes were blocked and removed. No organizer credentials or records were added to Git.
- Layer 1 has login/simulated OTP, code-scoped synthetic transactions, ES/PT rules NLU, deterministic policy, confirmation, dispute creation/readback, handoff packets and minimal chat UI. Operational state is still in process memory.
- Docker Compose previously passed health and end-to-end tests with Postgres/API/web healthy on loopback. Unique project names and host ports support parallel lanes. The local stack is left running.
- P1 bronze/manifest/silver/Pandera contracts validated 150,000 customers, 400,000 products and 4,425,008 transactions from 1,097 local objects. Eight brief-reference differences are documented; pipeline output is authoritative. BANK_CLOCK window/quantile definitions are explicit. This session did not rerun P1.
- `LAKE_DIR` defaults to persistent `~/aclara-lake`. Existing P1 output remains at the former `/tmp/aclara-shared-lake`; it has not been moved. Frozen NLU/response/OpenAPI/scenario and gold/serving contracts remain checked by CI.

## Done-not-verified

- Actual monthly charges, remaining ACA free grants, tax/discounts, and budget email delivery at a threshold have not been observed. Alerts notify; they do not stop spending. Currency conversion is a fixed reference.
- Browser visual behavior has not been manually reviewed in Azure. HTTPS API flow, served page, runtime API URL, CORS, and production build were tested.
- Simulated OTP is not independent MFA. Sessions/cases/handoffs are not durable and may disappear when a replica restarts or scales to zero. Backup restore/DR, load tests and production networking remain unverified.
- The persistent home lake has not been built/migrated. Non-P1 sources, model comparison and judge evaluation remain outside this session. Portuguese and dialect material still needs the previously agreed review and model-generated labeling.

## Next-blocked

- **No further approval is needed for the completed restricted dev deployment.** Keep only the owner's IP allowed. Any judge/public access change, expanded cloud scope, or new estimate above the approved US$40 threshold needs approval.
- Next layer: durable PostgreSQL operational state and resilience; then integrate the other lanes through green PRs. Do not treat the current in-memory demo as a durable banking service.
- Keep real-model runs on hold until their individual cost estimates are shown and approved; the judge vendor must differ from the system model. `LLM_PROVIDER=mock` remains deployed.
- Review actual spending and the CAD budget conversion monthly. Keep VNet/private networking in production-readiness work.

The local Compose stack is left running for review.

## Data/ML lane — 2026-09-26

### Completed (verified)

- Read the lane handoff, full build brief, repository rules, prior progress log, official problem statement, kickoff deck and approved dictionary. Refreshed/rebased `feat/data-ml` on `origin/main`; it was current at `88d84ca`.
- Added ten source contracts and nine dbt gold marts. The organizer build promoted dataset `b86f445cb468332bde984a788ef24f72f7070952b2d9292e0259e7b8f36397c9`: 150,000 customers, 400,000 products, 4,425,008 matcher ledger rows, 492,414 serving transactions, 13,164 FX rates, 1,200 service agents, and 150,000 customer complaint aggregates. Evidence: `uv run --no-sync python -m aclara.data.cli build`, DQ gate, dbt contracts/tests and export read-back.
- The first organizer build failed safely on 24,029 null transcript durations. Aggregate diagnosis confirmed a dictionary mismatch; contract 1.1.0 retains nulls, with an explicit warning. The corrected build passed.
- Incremental and matcher unit tests: `pytest tests/test_data_pipeline.py tests/test_charge_matcher.py` passed 7 tests. Coverage includes no-op reuse, restatement, late arrivals, extra columns, invalid/duplicate rows, removal, clock changes, customer/time leakage, missing FX and empty candidates.
- Local Postgres fixture integration passed: full row checksums, idempotent reload, RLS with no context, table/view isolation, autocommit and pooled-connection reuse, and rollback after a failed load. No organizer rows were printed or staged.
- Ruff and strict mypy passed on 31 source files before the final reports/model export. No LLM, cloud provisioning, or paid service was used. Sebastian clarified the Azure approval was for the lead lane, then explicitly instructed this lane to ignore it.

- Completed the synthetic benchmark: 6,000 train, 3,000 validation, 3,000 test queries; 15% NONE in each. The validation partition has 1,026 tuning, 995 calibration and 979 policy queries, grouped by customer. Thirty Optuna trials and their MLflow child runs completed in the local ignored `lake/mlruns` store. Test was touched once for v1.
- Validation selected LightGBM. Test top-1: rules 86.59%, logistic 96.78%, LightGBM 95.22%. Cost/query: 0.6197 / 0.3980 / 0.4717. Wrong proposals: 29/1,684 / 41/1,958 / 10/1,871. No-match precision and calibration trade-offs are reported rather than hidden. Paired customer-bootstrap cost difference for LightGBM vs rules: -0.1480, 95% CI [-0.1921, -0.1039].
- Exported v1 and verified model score/decision parity, file checksums, training-source digest, parent MLflow FINISHED status, all 30 finished trial runs, and one test-touch record. Model parameters and aggregate results contain no row records.
- Full suite: 14 passed, 1 local-Postgres test skipped in the ordinary invocation; that Postgres test passed separately with the local owner connection. B1: 32/32, 12 read-backs, safety guards passed. Frozen interface snapshots were current. A clean CI-dependency environment passed strict mypy and 9 tests (3 optional/local integrations skipped).
- Loaded all six organizer serving tables into the private local Postgres: 150,000 customers, 400,000 products, 492,414 transactions, 13,164 FX rows, 1,200 agents and 150,000 complaint aggregates. Every projected row was checksum-compared with gold before commit, and load metadata was verified from a fresh connection.
- Hardened source-conversion cache identity to include imported conversion code; the organizer rebuild passed and its following invocation was a no-op. All ten source tables had zero invalid rows. Bronze was reused.
- Existing web checks passed: frozen dependency install, TypeScript, ESLint, and Next.js production build. Frontend source was unchanged.
- Rebased cleanly onto `origin/main` at `cb402af`, retaining the lead's security tests and persistent lake default. Final combined suite: 24 passed, 1 optional Postgres test skipped (verified separately); the clean dev-only environment passed 19 tests with 3 optional integrations skipped. Strict mypy, Ruff/format, compilation, six pre-commit hooks, working-tree data/secret/size policy, interface snapshots, and B1 32/32 with 12 read-backs passed.
- The final snapshot matches the current data-source fingerprint, reused every bronze/silver object, passed all promotion gates, and then returned a no-op. Refreshed all six organizer serving tables from that snapshot and verified full row checksums and committed metadata from a fresh connection. The serving CLI now redacts driver failures; its regression test passed.
- Pushed only `origin/feat/data-ml`; the remote commit matched local `2ecb3dd`. Opened private [PR #6](https://github.com/sebastian-gm/bank-agent-lab/pull/6) into `main` after local checks passed. Remote `checks`, `invariants`, and `web` all passed on that implementation/report head. This documentation follow-up records those results. Read-back confirmed the repository remains private and the PR is open against main.
- Rechecked the Spanish packet: exactly 40 cards and unique customers, all recollection fields blank, zero customer overlap with the benchmark, and all three packet files ignored by Git.

### Done but not verified

- Lead-lane integration of serving tables and the pinned matcher into the live API has not been performed here. Existing bank/API/policy/orchestration and frozen interfaces are unchanged.
- Human recollections and language review remain pending. Forty Spanish cards and a blank fill-in CSV were generated under ignored `artifacts/human-validation/spanish-40/`, with benchmark customers excluded; counts and ignore status were read back. Portuguese remains future model-generated data with a second-vendor cross-check, per Sebastian; no paid model call was made.

### Next / blocked

- Lead review/merge of PR #6 remains pending, including the additive shared dependency changes. No breaking frozen-interface change is proposed.
- Lead lane must wire the Postgres tables and pin `models/charge_matcher/v1/` in shared configuration.
- Sebastian can fill the 40 Spanish recollections. Human validation and any later paid Portuguese generation need their own follow-up; no Azure work is part of this lane.
## AI lane — 2026-09-26

### Completed (verified)

- Read the AI-lane handoff, the build brief, repository rules, and this log. Kept `NluFrame`, `ResponsePlan`, scenario schemas, and the lead-owned orchestrator unchanged.
- Added mock/recorded, OpenAI-compatible, Gemini SDK, and Anthropic SDK adapters; structured output validation with one retry; metadata-only call records; dated price configuration; real-call and budget gates. Added versioned NLU/phrasing prompts and optional provider key names to `.env.example`.
- Added internal structured ES/PT NLU with deterministic relative dates, slang amount normalization, currency clarification, and false-friend handling. Added template-first response building, fact citation checks, input redaction, output DLP, and template fallback. Wrote the additive interface proposal for lead review.
- Added provider data-terms notes and a pending comparison table. No default model was chosen and no real-model call was made.
- Verified `.venv/bin/ruff check .`, `.venv/bin/mypy src/aclara --strict` (30 source files), and `.venv/bin/pytest` (16 passed) after `uv sync --all-extras`. The targeted tests exercise invalid JSON retry, real-call/budget guards, schema/privacy request shape without network, ES/PT normalization, grounding violations, DLP, fallback, and aggregate comparison.
- Committed the AI implementation and docs in three conventional commits (`2f33bc3`, `24198a5`, `c7f8a6b`) and pushed them to the private `origin/feat/ai`; `git ls-remote` confirmed the branch head. Merged current `main` into the published branch without force-pushing; `main` is an ancestor of merge commit `83e8a8d`, which was also verified on `origin`.
- After the merge, Ruff, strict mypy, pytest (25 passed), the interface snapshot check, all six pre-commit hooks, the tracked-file policy, and the B1 fixture harness (32/32; 12 read-backs) passed locally.
- Opened private draft PR #4 from `feat/ai` to `main`. `gh pr view` confirmed its branches and draft state; `gh pr checks 4` reported `checks`, `invariants`, and `web` all passing on initial PR head `83e8a8d`.
- Pushed the progress-log update as `5fc1058`; `git ls-remote` confirmed that head on `origin/feat/ai`. The PR's `checks`, `invariants`, and `web` passed again on that head, then `gh pr ready 4` and `gh pr view 4` confirmed PR #4 is open and ready for review.

### Done but not verified

- Native Gemini and Anthropic adapters, OpenRouter routes, model pricing in a billed request, and ES/PT model quality have no live-call evidence. The comparison table is pending keys, a reviewed dev utterance set, and approval of the estimated run cost.
- The AI modules are not yet wired into the lead-owned orchestrator. The frozen `NluFrame` cannot carry mixed/other language and rich slots; the proposal documents how to integrate safely and what needs versioned lead review.

### Next / blocked

- Review the AI interface proposal with the lead lane, wire `understand` and `build_reply` through the orchestrator, and verify end-to-end degraded-mode behavior.
- Build and review the same labeled dev utterance suite before model comparison. For 150 cases × five round-1 models, assuming 2,500 input and 300 output tokens per case, the dated rates imply about US$1 in token charges or about US$2 if every call retries; propose a US$3 run cap. This estimate excludes any provider routing difference, taxes, and later Claude tests. Show Sebastian the concrete suite and cost before the first paid run; wait for his approval and local `.env` keys.
- Confirm organizer data-use terms and provider terms for a public demo; choose no default until the measured comparison table is reviewed. Obtain lead review of ready PR #4, especially its shared-file additions and interface proposal; merge only after that review.

## AI lane — 2026-09-26 (local Compose isolation)

### Completed (verified)

- Set this worktree's ignored `.env` to `COMPOSE_PROJECT_NAME=aclara-ai`, `POSTGRES_HOST_PORT=15532`, `API_HOST_PORT=8100`, and `WEB_HOST_PORT=3100`. Read-back confirmed all four values. The edit preserved every other line, including the existing `LLM_REAL_CALLS_APPROVED` setting and the local provider key. `git check-ignore` confirmed `.env` is ignored.

### Done but not verified

- The isolated Compose settings have not been exercised by starting services. No real-model call was made.

### Next / blocked

- Ask Sebastian before the first paid model run after showing the concrete case suite and estimated cost. Keep `LLM_REAL_CALLS_APPROVED` unchanged until that approval.
## Access and continuation

- Restricted web: https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io/
- Login name: `demo.es.mx`. Retrieve `demo-password` from `kv-aclara-dev-eastus2` using the authenticated Azure portal; do not put it in chat, Git or logs. OTP is shown in the simulated panel after login.
- Current release input and control readback are available through ignored `infra/terraform.tfvars` and `artifacts/azure/verified.json`. Do not print the private inputs.

For the next session: **Continue from docs/status/progress-log.md. Next layer: durable operational state and resilience. Same rules.**

## Lead integration — 2026-09-26/27 (in progress)

### Completed-verified

- Re-read amended `04-lead-next.md`; durable operations and hash-chained audit follow matcher integration. Fresh Azure control readback and API health passed before lane work.
- Reviewed and merged PRs #4, #6 and #9 in order after green PR checks; main CI and safety passed at each lane merge. Resolved dependency/documentation conflicts, preserved both extras, and repaired v2 schema export while retaining all v1 definitions.
- Data/ML optional fixture tests passed locally (33 tests before schema addition; Postgres owner-DSN test skipped). No organizer pipeline rerun or model call was performed.
- Reactive evaluation adds isolated run IDs, clocks, fixture personas, response-keyed customer replies, fault injection, independent gold scoring and aggregate reporting. Found and fixed candidate follow-up routing and language preservation. Verification counts and remaining work will be finalized after integration.

### Done-not-verified

- New operational persistence, learned matcher and P orchestration are not yet integrated. The deployed revision remains the prior main.

### Next-blocked

- Continue tasks 3–7 in order; retain mock provider. No additional approval is needed for the authorized restricted redeployment. Real-model calls still need a priced proposal and approval.

### Durable operations implementation (local evidence)

- PR #10 merged after green checks; PR #11 merged after correcting formatting and the previously implicit DuckDB `pytz` test dependency. Both integrations remain mock-only.
- `python -m scripts.test_postgres`: four integration tests passed, including serving load; the command creates and removes a dedicated local test database. Forced RLS, invoker views/functions, no-context/autocommit/pool-context reset, customer/run/session isolation, rollback, concurrent audit append, append-only permissions, chain tamper detection and multiple application restarts were exercised.
- `docker compose up --build -d` built the API/migration/web images and started a separate non-owner API login after successful migrations. Current source adds session/run-scoped authentication capabilities and expiry-bound proposal hashes; a final image rebuild/smoke will follow policy documentation.
- Card-state persistence is restart-tested through its repository. The customer freeze/confirmation UI/API workflow is not implemented; do not claim it is available.
