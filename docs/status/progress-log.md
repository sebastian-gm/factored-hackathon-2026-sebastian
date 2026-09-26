# Progress log

Session date: 2026-09-26

## Completed-verified

- Read the build brief through §19 before implementation. Sebastian's follow-up at `agent-handoffs/01-lead-reply.md` was read fully and applied: solo/private repo, keep Aclara, private dev first, no public access yet, pipeline output is authoritative, and no Azure provisioning before explicit approval.
- Scaffolded the repository and Layer 1 slice in five conventional commits. The first four were pushed to `origin/feat/layer-1-vertical-slice`; the progress-log update was pushed as `7680288`.
- Created `main` from the verified Layer 1 branch at `7680288`, pushed it to `origin`, and set it as the private GitHub repository's default. `gh repo view` reported `main` and `isPrivate=true`. The remote `ci` and `safety` workflows both completed successfully on that commit.
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

- The parallel-work prep changes are committed locally on `feat/parallel-work-prep`: `406d5db` (worktree Compose configuration), `8229f92` (frozen lane interfaces), and `47dd666` (external lake and clock metrics). They have not yet been pushed or run through remote PR checks. `main` still contains only the verified Layer 1 base at `7680288`.
- The private Azure cost plan has not yet been prepared. No cloud resources or paid services have been used.
- The security suite beyond the existing staged-file guards, plus degraded-mode and fault-injection checks, remain to be run.
- Non-P1 source tables, model comparison, judge evaluation, and the final public demo remain unverified/deferred.

## Next-blocked

- Push `feat/parallel-work-prep`, open a PR into `main`, wait for remote CI and safety workflows to pass, then merge. Update this log again with the verified merge.
- After repo prep, prepare a costed private Azure dev plan for `Seb Azure Sandbox`, `rg-aclara-dev-eastus2`, East US 2. Stop before provisioning and wait for Sebastian's explicit approval.
- Continue with the security suite, degraded mode, and fault injection. Keep real-model runs on hold until an estimated cost is shown and approved.

The local Compose stack is left running for review.

## AI lane — 2026-09-26

### Completed (verified)

- Read the AI-lane handoff, the build brief, repository rules, and this log. Kept `NluFrame`, `ResponsePlan`, scenario schemas, and the lead-owned orchestrator unchanged.
- Added mock/recorded, OpenAI-compatible, Gemini SDK, and Anthropic SDK adapters; structured output validation with one retry; metadata-only call records; dated price configuration; real-call and budget gates. Added versioned NLU/phrasing prompts and optional provider key names to `.env.example`.
- Added internal structured ES/PT NLU with deterministic relative dates, slang amount normalization, currency clarification, and false-friend handling. Added template-first response building, fact citation checks, input redaction, output DLP, and template fallback. Wrote the additive interface proposal for lead review.
- Added provider data-terms notes and a pending comparison table. No default model was chosen and no real-model call was made.
- Verified `.venv/bin/ruff check .`, `.venv/bin/mypy src/aclara --strict` (30 source files), and `.venv/bin/pytest` (16 passed) after `uv sync --all-extras`. The targeted tests exercise invalid JSON retry, real-call/budget guards, schema/privacy request shape without network, ES/PT normalization, grounding violations, DLP, fallback, and aggregate comparison.

### Done but not verified

- Native Gemini and Anthropic adapters, OpenRouter routes, model pricing in a billed request, and ES/PT model quality have no live-call evidence. The comparison table is pending keys, a reviewed dev utterance set, and approval of the estimated run cost.
- The AI modules are not yet wired into the lead-owned orchestrator. The frozen `NluFrame` cannot carry mixed/other language and rich slots; the proposal documents how to integrate safely and what needs versioned lead review.

### Next / blocked

- Review the AI interface proposal with the lead lane, wire `understand` and `build_reply` through the orchestrator, and verify end-to-end degraded-mode behavior.
- Build and review the same labeled dev utterance suite before model comparison. For 150 cases × five round-1 models, assuming 2,500 input and 300 output tokens per case, the dated rates imply about US$1 in token charges or about US$2 if every call retries; propose a US$3 run cap. This estimate excludes any provider routing difference, taxes, and later Claude tests. Show Sebastian the concrete suite and cost before the first paid run; wait for his approval and local `.env` keys.
- Confirm organizer data-use terms and provider terms for a public demo; choose no default until the measured comparison table is reviewed. Push this branch to `origin`, run remote checks, and open a PR into `main` only when CI is green.
