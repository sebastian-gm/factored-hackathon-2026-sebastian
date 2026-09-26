# Progress log

Session date: 2026-09-26

## Completed-verified

- Read the build brief through §19 before implementation. Sebastian's follow-up at `agent-handoffs/01-lead-reply.md` was read fully and applied: solo/private repo, keep Aclara, local-first dev, pipeline output is authoritative, and no Azure provisioning before explicit approval. His later revision accepts owner-IP-allowlisted public HTTPS for restricted development only, still pending provisioning approval.
- Scaffolded the repository and Layer 1 slice in five conventional commits. The first four were pushed to `origin/feat/layer-1-vertical-slice`; the progress-log update was pushed as `7680288`.
- Created `main` from the verified Layer 1 branch at `7680288`, pushed it to `origin`, and set it as the private GitHub repository's default. `gh repo view` reported `main` and `isPrivate=true`. The remote `ci` and `safety` workflows both completed successfully on that commit.
- Merged the parallel-work prep as PR #1 into `main` at `88d84ca6b78f51eae4e41d4992794ec466ed5670`. `gh pr checks 1` showed `checks`, `invariants`, and `web` passing before merge; `gh run list` showed `ci` and `safety` successful on the merged `main` SHA. `gh repo view` still reports the repository private with `main` as default. Fetched and fast-forwarded the local `main` to `origin/main`.
- Revised the Azure proposal in `docs/azure-private-dev-plan.md` for Sebastian's under-$30/month target: public HTTPS with owner-IP ingress allowlisting and app login/OTP, ACA Consumption scale-to-zero, PostgreSQL firewall entries for current ACA egress plus owner IP, Key Vault, managed identities, and an authenticated ACR. The public-list estimate is about $24–$29/month under stated low-traffic/free-grant assumptions. Recorded ACA's changing egress addresses as a limitation. No subscription lookup, resource creation, or paid service use occurred.
- Added API security coverage for bearer/session expiry, OTP binding and five-attempt cap, customer scoping and field masking, session-bound single-use proposals, hash/expiry/step-up checks, and strict request validation. Added degraded-mode and fault-injection coverage for database readiness failure/recovery and a failed fixture read returning a generic 500.
- Ran `PRE_COMMIT_HOME=/tmp/aclara-precommit-cache UV_CACHE_DIR=/tmp/aclara-uv-cache make checks`. All six pre-commit hooks, the working-tree file policy, compileall, pytest (16 passed), B1 (32/32; 12 read-backs), and interface snapshot check passed. Updated Makefile targets to use `uv run --no-sync`; the first `make checks` attempt tried to reach PyPI despite the local environment being installed, while the final command completed offline.
- Changed `.env.example`, README, and the pipeline CLI fallback to use persistent `~/aclara-lake` rather than `/tmp`; the pipeline expands the home-directory shorthand before building. Added the private Container Apps/PostgreSQL/Key Vault network design as future production-readiness work. This config change did not rebuild or move existing lake files.
- Merged PR #2 into `main` at `f0ec6b591ed9eb94d03decc688b9e23795089bc5`. PR-head `checks`, `invariants`, and `web` passed; `ci` and `safety` both completed successfully on that merged `main` SHA. The repository remains private with `main` as default.
- On merged `main`, `PRE_COMMIT_HOME=/tmp/aclara-precommit-cache UV_CACHE_DIR=/tmp/aclara-uv-cache make checks` passed: six hooks, working-tree file policy, compileall, pytest (16 passed), B1 (32/32; 12 read-backs), and interface snapshots. `docker compose config --quiet` passed. `docker compose ps --format '{{.Service}} {{.State}} {{.Health}} {{.Ports}}'` showed API, Postgres, and web healthy; `curl --fail --silent --show-error http://127.0.0.1:8000/healthz` returned `{"status":"ok","service":"aclara-api","llm_provider":"mock"}` and the web request to `http://127.0.0.1:3000/` returned HTTP 200.
- Created the local work branch `feat/parallel-work-prep` from `main` for this lane's additive parallel-work preparation.
- Made Compose worktree-configurable through `.env`: project name plus Postgres, API, and web host ports. Postgres remains loopback-only. A Compose config check with project `aclara-ai` and ports 15433/18001/13001 reported those mappings and matching API/web origin values.
- Initially set the shared `LAKE_DIR` default to `/tmp/aclara-shared-lake`, outside the checkout. The pipeline CLI reads only its path/clock settings from `.env`; source and output directory guards prevent either from containing the other. The existing P1 output was built at that former path.
- Rebuilt the Compose stack. `docker compose ps --format '{{.Service}} {{.State}} {{.Health}}'` reported API, Postgres, and web healthy. The live API test passed login, OTP, six scoped fixture transactions, Pydantic response validation, dispute creation, and read-back. The web page and its API connection returned 200.
- Moved deterministic rules NLU into `src/aclara/agent/nlu/` and added frozen Pydantic `NluFrame` and `ResponsePlan` models in `src/aclara/agent/contracts.py`. FastAPI validates chat and confirmation responses against `ResponsePlan`.
- Added Pydantic validation for the scenario YAML, exported OpenAPI and JSON Schema snapshots, and added versioned gold/serving transaction contracts. `make interfaces` regenerates the snapshots; CI checks they are current. The gold table contract is a target interface and is not yet materialized by P1.
- Updated the DQ generator so its windows derive from the configured UTC `BANK_CLOCK`; documented exact half-open window bounds, full-dimension zero inclusion, `quantile_cont` p50/p90 definitions, and pending-age predicate. The pipeline output remains the source of truth; eight §4 values are retained as reference differences.
- Rebuilt P1 to the shared external path with `LOCAL_RAW_DIR=/home/megagdev/megagdev/factored-hackathon-2026/data/data LAKE_DIR=/tmp/aclara-shared-lake UV_CACHE_DIR=/tmp/aclara-uv-cache uv run --no-sync python -m aclara.data.cli build`. Pandera validated all three tables; output counts were 150,000 customers, 400,000 products, and 4,425,008 transactions from 1,097 objects. The report contains aggregates, not source rows.
- Local checks passed after the interface changes: pre-commit, Ruff, strict mypy (19 source files), compileall, pytest (7 passed), B1 (32/32, 12 read-backs, safety guards passed), and the interface snapshot check.
- `.env`, the shared lake, and generated artifacts are not in Git. The fake staged CSV/key guard probes were both blocked and removed. No organizer credentials or row records were added.

## Done-not-verified

- The revised estimate uses public USD price references; the subscription's offer, credits, tax, and currency conversion have not been checked. Its free-grant and low-traffic assumptions have not been validated against subscription usage. No Azure resources exist; deployment awaits Sebastian's separate explicit approval.
- ACA ingress, PostgreSQL firewall behavior, Key Vault access, Azure managed identities, runtime performance, and actual monthly charges have not been tested in Azure. ACA outbound addresses may change, as documented in the plan.
- Existing P1 lake files at `/tmp/aclara-shared-lake` were not moved or rebuilt. `~/aclara-lake` is the default for future builds.
- Non-P1 source tables, model comparison, judge evaluation, and the final public demo remain unverified/deferred.

## Next-blocked

- Do not provision Azure until Sebastian gives separate explicit approval. Before any approved apply, check the live East US 2 rates and subscription offer against the under-$30/month target and confirm acceptance of the documented ACA egress-IP limitation.
- Keep real-model runs on hold until each estimated cost is shown and approved. The judge must remain a different vendor from the chosen system model.

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
