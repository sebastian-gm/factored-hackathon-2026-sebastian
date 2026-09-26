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

### Done but not verified

- Native Gemini and Anthropic adapters, OpenRouter routes, model pricing in a billed request, and ES/PT model quality have no live-call evidence. The comparison table is pending keys, a reviewed dev utterance set, and approval of the estimated run cost.
- The AI modules are not yet wired into the lead-owned orchestrator. The frozen `NluFrame` cannot carry mixed/other language and rich slots; the proposal documents how to integrate safely and what needs versioned lead review.

### Next / blocked

- Review the AI interface proposal with the lead lane, wire `understand` and `build_reply` through the orchestrator, and verify end-to-end degraded-mode behavior.
- Build and review the same labeled dev utterance suite before model comparison. For 150 cases × five round-1 models, assuming 2,500 input and 300 output tokens per case, the dated rates imply about US$1 in token charges or about US$2 if every call retries; propose a US$3 run cap. This estimate excludes any provider routing difference, taxes, and later Claude tests. Show Sebastian the concrete suite and cost before the first paid run; wait for his approval and local `.env` keys.
- Confirm organizer data-use terms and provider terms for a public demo; choose no default until the measured comparison table is reviewed. Move PR #4 to ready for lead review now that remote CI is green, and merge only after the lead accepts the shared-file additions and interface proposal.
