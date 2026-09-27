"""Load only routing attributes into the existing approved database; aggregate output."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import astuple
from pathlib import Path

import psycopg
from dotenv import dotenv_values
from psycopg.conninfo import make_conninfo

from aclara.handoff.routing import aggregates, read_source
from aclara.ops.migrate import migrate


def load(dsn: str, source: Path) -> dict:
    rows = read_source(source)
    expected = sorted(astuple(r) for r in rows)
    with psycopg.connect(dsn) as connection:
        connection.execute("LOCK TABLE reference.service_agents IN EXCLUSIVE MODE")
        connection.execute("DELETE FROM reference.service_agents")
        with connection.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO reference.service_agents VALUES (%s,%s,%s,%s,%s,%s)", expected
            )
        assert (
            connection.execute(
                "SELECT * FROM reference.service_agents ORDER BY agent_ref"
            ).fetchall()
            == expected
        )
    with psycopg.connect(dsn) as connection:
        assert (
            connection.execute(
                "SELECT * FROM reference.service_agents ORDER BY agent_ref"
            ).fetchall()
            == expected
        )
    return {
        **aggregates(rows),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "committed_readback": "passed",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("local", "azure"), default="local")
    args = parser.parse_args()
    values = dotenv_values(".env")
    raw = os.getenv("LOCAL_RAW_DIR") or values.get("LOCAL_RAW_DIR")
    if not raw:
        raise ValueError("LOCAL_RAW_DIR is required")
    source = Path(raw) / "service_agents.csv"
    if args.target == "azure":
        from scripts.azure_migrate_ops import connection_string

        # Uses the same explicitly selected sandbox/KV boundary as the approved migration.
        dsn = connection_string("aclara_admin")
        role = "aclara_app"
    else:
        dsn = make_conninfo(
            host="127.0.0.1",
            port=values.get("POSTGRES_HOST_PORT") or "15432",
            user=values.get("POSTGRES_USER") or "postgres",
            password=values.get("POSTGRES_PASSWORD") or "",
            dbname=values.get("POSTGRES_DB") or "aclara",
        )
        role = "aclara_app"
    migrate(dsn, role)
    result = load(dsn, source)
    target = Path("artifacts/routing")
    target.mkdir(parents=True, exist_ok=True)
    (target / f"{args.target}-load.json").write_text(json.dumps(result, indent=2) + "\n")
    sys.stdout.write(json.dumps(result) + "\n")


if __name__ == "__main__":
    try:
        main()
    except (psycopg.Error, ValueError):
        raise SystemExit(
            "Routing load failed; database details and source records are redacted"
        ) from None
