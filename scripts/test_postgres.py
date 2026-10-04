"""Run database tests in a disposable local database, never the application database."""

# ruff: noqa: S603 -- fixed Python pytest entry point, no shell.
from __future__ import annotations

import os
import secrets
import subprocess
import sys

import psycopg
from dotenv import dotenv_values
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from aclara.ops.migrate import migrate


def main() -> int:
    values = dotenv_values(".env")
    owner = os.getenv("TEST_POSTGRES_ADMIN_DSN") or make_conninfo(
        host="127.0.0.1",
        port=values.get("POSTGRES_HOST_PORT") or "15432",
        user=values.get("POSTGRES_USER") or "postgres",
        password=values.get("POSTGRES_PASSWORD") or "",
        dbname=values.get("POSTGRES_DB") or "postgres",
    )
    options = conninfo_to_dict(owner)
    if options.get("host") not in {"127.0.0.1", "localhost"}:
        raise ValueError("Disposable database tests are local-only")
    suffix = secrets.token_hex(6)
    database, role = "aclara_test_" + suffix, "aclara_test_" + suffix
    password = secrets.token_urlsafe(32)
    with psycopg.connect(owner, autocommit=True) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS").format(
                sql.Identifier(role), sql.Literal(password)
            )
        )
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        try:
            migration_dsn = make_conninfo(owner, dbname=database)
            app_dsn = make_conninfo(owner, dbname=database, user=role, password=password)
            migrate(migration_dsn, role)
            environment = {
                **os.environ,
                "TEST_OPS_OWNER_DSN": migration_dsn,
                "TEST_OPS_DSN": app_dsn,
                "TEST_DATA_LOAD_DSN": migration_dsn,
            }
            return subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/test_operational_store.py",
                    "tests/test_customer_business_state.py",
                    "tests/test_nlu_transaction_boundary.py",
                    "tests/test_session_turns.py",
                    "tests/test_request_scoped_telemetry.py",
                    "tests/test_serving_load.py",
                    "tests/test_serving_api.py",
                    "tests/test_llm_budget.py",
                    "tests/test_go_live_budget.py",
                    "tests/test_live_rehearsal_regressions.py",
                    "tests/test_judge_profiles_postgres.py",
                    "tests/test_staff_realm_queue_postgres.py",
                    "tests/test_staff_realm_revocation.py",
                    "--tb=short",
                ],
                env=environment,
                check=False,
            ).returncode
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


if __name__ == "__main__":
    raise SystemExit(main())
