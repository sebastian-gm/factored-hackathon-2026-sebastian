"""Explicit owner-only Alembic migration entry point."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool


def migrate(dsn: str, app_role: str | None = None) -> None:
    with psycopg.connect(dsn) as connection:
        for role in ("aclara_owner", "aclara_api", "aclara_ops"):
            if not connection.execute(
                "SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)
            ).fetchone():
                connection.execute(
                    sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOBYPASSRLS").format(
                        sql.Identifier(role)
                    )
                )
        connection.execute("GRANT aclara_owner TO CURRENT_USER")
        if app_role:
            password = os.getenv("OPS_APP_PASSWORD")
            if (
                password
                and not connection.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname=%s", (app_role,)
                ).fetchone()
            ):
                if len(password) < 32:
                    raise ValueError("Application password must have at least 32 characters")
                connection.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS").format(
                        sql.Identifier(app_role), sql.Literal(password)
                    )
                )
            row = connection.execute(
                "SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s", (app_role,)
            ).fetchone()
            if row != (False, False):
                raise ValueError("Application login must exist and must not bypass RLS")
            connection.execute(sql.SQL("GRANT aclara_api TO {}").format(sql.Identifier(app_role)))
    engine = create_engine(
        "postgresql+psycopg://", creator=lambda: psycopg.connect(dsn), poolclass=NullPool
    )
    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[3] / "migrations")
    )
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-role", default=os.getenv("OPS_APP_ROLE", "aclara_app"))
    args = parser.parse_args()
    migrate(os.getenv("OPS_OWNER_DSN", ""), args.app_role)


if __name__ == "__main__":
    main()
