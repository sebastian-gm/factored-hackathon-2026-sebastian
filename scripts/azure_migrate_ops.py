"""Apply reviewed operations migrations in the explicitly approved sandbox only."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime

import psycopg
from psycopg.conninfo import make_conninfo
from scripts.azure_dev import ROOT, VAULT, az
from scripts.azure_targets import database_host

from aclara.ops.migrate import migrate


def connection_string(role: str) -> str:
    secret = "postgres-admin" if role == "aclara_admin" else "postgres-app"
    password = az("keyvault", "secret", "show", "--vault-name", VAULT, "--name", secret)["value"]
    return make_conninfo(
        host=database_host(),
        dbname="aclara",
        user=role,
        password=password,
        sslmode="verify-full",
        sslrootcert="/etc/ssl/certs/ca-certificates.crt",
        connect_timeout=15,
    )


def main() -> None:
    prices = json.loads((ROOT / "artifacts/azure/prices.json").read_text())
    if (
        not prices["gate_passed"]
        or prices["monthly_without_free_grant_with_margin"] > 40
        or (datetime.now(UTC) - datetime.fromisoformat(prices["checked_at"])).total_seconds()
        > 21600
    ):
        raise RuntimeError("Fresh approved price gate required before migration")
    migrate(connection_string("aclara_admin"), "aclara_app")
    with psycopg.connect(connection_string("aclara_app")) as connection:
        assert connection.execute(
            "SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()"
        ).fetchone() == (True,)
        assert connection.execute(
            "SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user"
        ).fetchone() == (False, False)
        assert connection.execute(
            "SELECT pg_has_role(current_user,'aclara_owner','MEMBER')"
        ).fetchone() == (False,)
        assert connection.execute("SELECT count(*) FROM ops.cases").fetchone() == (0,)
    sys.stdout.write("Operational migration and non-owner TLS/RLS readback verified.\n")


if __name__ == "__main__":
    main()
