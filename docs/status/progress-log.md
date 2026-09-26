# Progress log

Session date: 2026-09-26

## Completed-verified

- Read `BANK_AGENT_LAB_BUILD_BRIEF.md` through §19 before writing code. Sent the §19 questions together; the user confirmed this is a solo project with one private repository and one `origin`, kept the name Aclara, and answered the data, model, reviewer, and Azure questions. No team repository or second remote is configured.
- Added the requested scaffold: `AGENTS.md`, `CLAUDE.md` symlink, README, sanitized `docs/00-build-brief.md`, this progress log, R1–R14 requirements traceability, ADR index/template/ADR 0001, and related safety/readiness notes. Traceability includes the seven judging criteria.
- Configured `.gitignore`, local pre-commit hooks, GitHub CI/safety workflows, and the staged-file policy. Verified all three data, secret, and size hooks with `PRE_COMMIT_HOME=/tmp/aclara-precommit-cache UV_CACHE_DIR=/tmp/aclara-uv-cache uv run pre-commit run --all-files`.
- Proved the staged guard rejects a fake CSV (`pre-commit run staged-data-file-policy --files staged-guard-probe.csv`) and a fake PEM key (`pre-commit run staged-secret-policy --files staged-guard-probe.pem`). Both probes were removed from the index and worktree immediately after the checks.
- Built the local Compose stack. `docker compose config --quiet` passed; `docker compose ps --format '{{.Service}} {{.State}} {{.Health}}'` showed Postgres, API, and web running and healthy. The database is internal to Compose; API/web bind to loopback.
- Verified the live flow through `docker compose exec -T api python -`: login, simulated OTP, six fixture transactions scoped to the demo customer, Spanish dispute proposal, explicit confirmation, and dispute read-back with status `received`. The live web page returned 200 and reached `/healthz` through the Compose network.
- Ran `UV_CACHE_DIR=/tmp/aclara-uv-cache uv run python -m evals.runner --system B1`: 32 scenarios passed, 0 failed, 12 read-backs, safety guards passed. Scenarios cover Spanish and Portuguese normal, ambiguous, and human-handoff paths.
- Ran local checks successfully: `uv run ruff check .`, `uv run mypy --strict src/aclara`, `uv run python -m compileall -q src evals scripts`, `uv run pytest` (1 passed), and `uv run python scripts/check_staged_files.py --working-tree`.
- Ran web checks successfully in `apps/web`: `pnpm typecheck`, `pnpm lint`, and `pnpm build`.
- Ran the P1 pipeline with `LOCAL_RAW_DIR=/home/megagdev/megagdev/factored-hackathon-2026/data/data UV_CACHE_DIR=/tmp/aclara-uv-cache uv run python -m aclara.data.cli build`. Bronze, manifest, typed silver, and Pandera sample contracts completed for customers (150,000 rows), products (400,000), and transactions (4,425,008 across 1,097 source objects). The aggregate-only report is `docs/data-quality-report.md`; no source rows are included.
- Compared the §4 facts from pipeline output. The fraud band matches when defined as `27 < score ≤ 30` (353,682 rows, 111 fraud rows). Eight differences remain explicitly flagged: 120/365-day transaction totals, two 120-day candidate statistics, two full-ledger candidate statistics, and two pending counts. The 120-day UTC window and candidate percentile method are not fully specified in §4, so these differences have not been silently normalized away.
- Verified `.env` and `lake/` outputs are ignored. No cloud resources were created, no real-model call was made, and no publication took place.
- Committed in four conventional commits and pushed to `origin/feat/layer-1-vertical-slice`: `9d0fbde` (docs scaffold), `6fc185b` (API and B1 harness), `a8ff8b2` (P1 pipeline), and `c2111aa` (Compose, web UI, and CI). Verified the branch tracks `origin/feat/layer-1-vertical-slice` and was synchronized after push.

## Done-not-verified

- The GitHub Actions workflow has not run on GitHub. The equivalent Python and web commands above passed locally.
- The P1 pipeline covers only customers, products, and transactions. Other source tables, their source-regeneration comparison, and broader business findings remain unverified.
- Model comparison and the LLM judge have not started. `LLM_PROVIDER=mock` remains the default; no real model was used.
- Azure deployment, Terraform remote state, GitHub OIDC/environment setup, and public demo deployment have not started.

## Next-blocked

- Get explicit user approval before the first Azure/public deployment. The user asked to be asked before that step; no resources or cost have been incurred.
- Before any real-model run, provide a cost estimate and wait for approval. Run the provider comparison on the synthetic dev suite and show its metrics table before selecting a default.
- Continue the next implementation layer only after reviewing this Layer 1 result. Terraform, dbt, JWKS/ES256, hash-chained audit, Ops UI, LLM judge, Locust, Trivy, and Optuna remain deferred.

The local Compose stack is left running for review.
