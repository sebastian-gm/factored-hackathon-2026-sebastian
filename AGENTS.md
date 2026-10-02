# Repository working rules

- Work only in this repository. Run every Git command as `git -C <repo>` with this repository path.
- This is the submission repository, `sebastian-gm/factored-hackathon-2026-sebastian` (formerly `bank-agent-lab`). Keep it private until Sebastian's explicit submission-day publication approval. Configure and push only `origin`.
- Never add organizer rows, credentials, keys, passwords, connection strings, or local secrets to Git.
- Read organizer records only from a local `LOCAL_RAW_DIR`; write generated data only under ignored `lake/` or `artifacts/`.
- Commit aggregates, schemas, contracts, and project-generated fixtures only. Do not put row-level data in logs, docs, or CI artifacts.
- Use `LLM_PROVIDER=mock` by default. Do not run a real model until the owner has approved the estimated cost.
- Ask before spending money, creating cloud resources, or making any content public.
- Implement deterministic identity, policy, authorization, and write actions in code. Never let model prose grant access or authority.
- Verify every action by reading it back before reporting success.
- Update `docs/status/progress-log.md` each session under Completed (verified), Done but not verified, and Next / blocked.
- Use small conventional commits on a feature branch. Do not force-push.
- Every change goes through a small PR (aim below 800 lines). Require green remote CI before merging. Tag every Azure release with an annotated semver tag; reserve `v1.0.0` for the exact submission-day release SHA.
- Python style: typed functions, timezone-aware datetimes, Ruff, and strict mypy on `src/aclara`.
- Do not persist or display model thinking. Store only inputs needed for execution records and explain decisions from facts and rules.

## Parallel lane ownership

- **Lead lane:** shared project files (`pyproject.toml`, `uv.lock`, `Makefile`, `docker-compose.yml`, `config/`, CI workflows, and `infra/`); `src/aclara/bank/`, `policy/`, `api/`, agent orchestration/state machine, `handoff/`, and the frozen interface models in `src/aclara/agent/contracts.py`.
- **AI lane:** `src/aclara/llm/`, `src/aclara/agent/nlu/`, `src/aclara/agent/nlg/`, grounding, and `prompts/`. Preserve the interfaces in `agent/contracts.py` and `contracts/interfaces/`.
- **Data/ML lane:** `contracts/` data contracts, `src/aclara/data/`, `dbt/`, `analysis/`, `ml/`, `models/`, and `tests/fixtures/incremental/`. Shared interface contracts under `contracts/interfaces/` require an additive change proposal in the PR and lead review.
- **Frontend lane (later):** `apps/web/`.

Each lane changes only its assigned folders. Keep shared-file changes minimal and additive, and call them out in the PR. Rebase on `main` daily. Each worktree uses a unique Compose project name and host ports, while all lanes share the same absolute `LAKE_DIR` outside the repository.
