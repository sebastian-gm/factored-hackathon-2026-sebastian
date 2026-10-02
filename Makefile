.PHONY: up down checks eval-smoke interfaces pipeline test-recovery demo demo-stop demo-check

PRE_COMMIT_HOME ?= $(CURDIR)/artifacts/precommit-cache
export PRE_COMMIT_HOME

up:
	uv run --no-sync python -m scripts.local_ops
	docker compose up --build -d --wait --wait-timeout 120

down:
	docker compose down

checks:
	uv run --no-sync pre-commit run --all-files
	uv run --no-sync python scripts/check_staged_files.py --working-tree
	uv run --no-sync python -m compileall -q src evals scripts
	uv run --no-sync pytest
	uv run --no-sync python -m evals.runner --system B1
	uv run --no-sync python -m scripts.export_interfaces --check
	uv run --no-sync python -m scripts.generate_policy_catalog --check

eval-smoke:
	uv run --no-sync python -m evals.runner --system B1

interfaces:
	uv run --no-sync python -m scripts.export_interfaces

pipeline:
	uv run --no-sync python -m aclara.data.cli build

test-recovery:
	uv run --no-sync python -m scripts.backup_restore

# Mock-only, isolated credentials and ports; never uses the worktree .env.
demo:
	python3 -m scripts.local_demo

demo-stop:
	python3 -m scripts.local_demo --stop

demo-check:
	python3 -m scripts.local_demo --check
