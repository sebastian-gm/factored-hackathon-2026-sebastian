.PHONY: up down checks eval-smoke pipeline

up:
	docker compose up --build -d

down:
	docker compose down

checks:
	PRE_COMMIT_HOME=/tmp/aclara-precommit-cache uv run pre-commit run --all-files
	uv run python scripts/check_staged_files.py --working-tree
	uv run python -m compileall -q src evals scripts
	uv run pytest
	uv run python -m evals.runner --system B1

eval-smoke:
	uv run python -m evals.runner --system B1

pipeline:
	uv run python -m aclara.data.cli build
