.PHONY: up down checks eval-smoke interfaces pipeline

up:
	uv run --no-sync python -m scripts.local_ops
	docker compose up --build -d

down:
	docker compose down

checks:
	PRE_COMMIT_HOME=/tmp/aclara-precommit-cache uv run --no-sync pre-commit run --all-files
	uv run --no-sync python scripts/check_staged_files.py --working-tree
	uv run --no-sync python -m compileall -q src evals scripts
	uv run --no-sync pytest
	uv run --no-sync python -m evals.runner --system B1
	uv run --no-sync python -m scripts.export_interfaces --check

eval-smoke:
	uv run --no-sync python -m evals.runner --system B1

interfaces:
	uv run --no-sync python -m scripts.export_interfaces

pipeline:
	uv run --no-sync python -m aclara.data.cli build
