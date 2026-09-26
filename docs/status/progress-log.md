# Progress log

Session date: 2026-09-26

## Completed-verified

- Read the build brief through §19 before implementation. Sebastian's follow-up at `agent-handoffs/01-lead-reply.md` was read fully and applied: solo/private repo, keep Aclara, private dev first, no public access yet, pipeline output is authoritative, and no Azure provisioning before explicit approval.
- Scaffolded the repository and Layer 1 slice in five conventional commits. The first four were pushed to `origin/feat/layer-1-vertical-slice`; the progress-log update was pushed as `7680288`.
- Created `main` from the verified Layer 1 branch at `7680288`, pushed it to `origin`, and set it as the private GitHub repository's default. `gh repo view` reported `main` and `isPrivate=true`. The remote `ci` and `safety` workflows both completed successfully on that commit.
- Merged the parallel-work prep as PR #1 into `main` at `88d84ca6b78f51eae4e41d4992794ec466ed5670`. `gh pr checks 1` showed `checks`, `invariants`, and `web` passing before merge; `gh run list` showed `ci` and `safety` successful on the merged `main` SHA. `gh repo view` still reports the repository private with `main` as default. Fetched and fast-forwarded the local `main` to `origin/main`.
- Prepared the costed, private-only Azure plan in `docs/azure-private-dev-plan.md`, using Microsoft Retail Prices API rates checked on 2026-09-26. It estimates about $270/month for Azure-native P2S (24/7), or about $112/month if an external personal Tailscale control plane is accepted. No subscription lookup, resource creation, or paid service use occurred.
- Added API security coverage for bearer/session expiry, OTP binding and five-attempt cap, customer scoping and field masking, session-bound single-use proposals, hash/expiry/step-up checks, and strict request validation. Added degraded-mode and fault-injection coverage for database readiness failure/recovery and a failed fixture read returning a generic 500.
- Ran `PRE_COMMIT_HOME=/tmp/aclara-precommit-cache UV_CACHE_DIR=/tmp/aclara-uv-cache make checks`. All six pre-commit hooks, the working-tree file policy, compileall, pytest (16 passed), B1 (32/32; 12 read-backs), and interface snapshot check passed. Updated Makefile targets to use `uv run --no-sync`; the first `make checks` attempt tried to reach PyPI despite the local environment being installed, while the final command completed offline.
- Created the local work branch `feat/parallel-work-prep` from `main` for this lane's additive parallel-work preparation.
- Made Compose worktree-configurable through `.env`: project name plus Postgres, API, and web host ports. Postgres remains loopback-only. A Compose config check with project `aclara-ai` and ports 15433/18001/13001 reported those mappings and matching API/web origin values.
- Set the shared `LAKE_DIR` default to `/tmp/aclara-shared-lake`, outside the checkout. The pipeline CLI reads only its path/clock settings from `.env`; source and output directory guards prevent either from containing the other.
- Rebuilt the Compose stack. `docker compose ps --format '{{.Service}} {{.State}} {{.Health}}'` reported API, Postgres, and web healthy. The live API test passed login, OTP, six scoped fixture transactions, Pydantic response validation, dispute creation, and read-back. The web page and its API connection returned 200.
- Moved deterministic rules NLU into `src/aclara/agent/nlu/` and added frozen Pydantic `NluFrame` and `ResponsePlan` models in `src/aclara/agent/contracts.py`. FastAPI validates chat and confirmation responses against `ResponsePlan`.
- Added Pydantic validation for the scenario YAML, exported OpenAPI and JSON Schema snapshots, and added versioned gold/serving transaction contracts. `make interfaces` regenerates the snapshots; CI checks they are current. The gold table contract is a target interface and is not yet materialized by P1.
- Updated the DQ generator so its windows derive from the configured UTC `BANK_CLOCK`; documented exact half-open window bounds, full-dimension zero inclusion, `quantile_cont` p50/p90 definitions, and pending-age predicate. The pipeline output remains the source of truth; eight §4 values are retained as reference differences.
- Rebuilt P1 to the shared external path with `LOCAL_RAW_DIR=/home/megagdev/megagdev/factored-hackathon-2026/data/data LAKE_DIR=/tmp/aclara-shared-lake UV_CACHE_DIR=/tmp/aclara-uv-cache uv run --no-sync python -m aclara.data.cli build`. Pandera validated all three tables; output counts were 150,000 customers, 400,000 products, and 4,425,008 transactions from 1,097 objects. The report contains aggregates, not source rows.
- Local checks passed after the interface changes: pre-commit, Ruff, strict mypy (19 source files), compileall, pytest (7 passed), B1 (32/32, 12 read-backs, safety guards passed), and the interface snapshot check.
- `.env`, the shared lake, and generated artifacts are not in Git. The fake staged CSV/key guard probes were both blocked and removed. No organizer credentials or row records were added.

## Done-not-verified

- The cost plan uses public USD list rates; the subscription's offer, credits, and currency conversion have not been queried. Access option and monthly cap are awaiting Sebastian's decision.
- The cost plan, tests, and Makefile change on `docs/record-parallel-lane-merge` are staged locally; they have not been pushed or checked remotely yet. `main` remains green at `88d84ca`.
- Non-P1 source tables, model comparison, judge evaluation, and the final public demo remain unverified/deferred.

## Next-blocked

- Sebastian must choose an access option and monthly cap, then explicitly approve before Azure resources are created. The two current estimates and assumptions are in `docs/azure-private-dev-plan.md`.
- Push/open a PR for the staged log/plan/security-suite/Makefile changes, wait for remote CI and safety checks, then merge and record the merged SHA.
- Keep real-model runs on hold until each estimated cost is shown and approved. The judge must remain a different vendor from the chosen system model.

The local Compose stack is left running for review.
