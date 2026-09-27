"""Local-only PostgreSQL 16 dump/restore rehearsal on disposable authored databases."""

# ruff: noqa: S603, S607 -- fixed Docker/pg tools, no shell, generated database names.
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path
from time import perf_counter
from typing import Any

import psycopg
from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
from psycopg import sql
from psycopg.conninfo import make_conninfo
from scripts.verify_audit_chain import verify

from aclara.api.app import create_app
from aclara.ops.migrate import migrate
from aclara.ops.store import TABLES, Scope, Store
from aclara.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


async def seed(dsn: str, settings: Settings) -> dict[str, Any]:
    store = Store(dsn)
    app = create_app(settings, store=store)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            c = (
                await client.post(
                    "/auth/login",
                    json={"username": settings.demo_username, "password": settings.demo_password},
                )
            ).json()
            pre = {"X-Preauth-Token": c["preauth_token"]}
            code = (
                await client.get(f"/auth/challenges/{c['challenge_id']}/sms", headers=pre)
            ).json()["code"]
            token = (
                await client.post(
                    "/auth/otp/verify",
                    headers=pre,
                    json={"challenge_id": c["challenge_id"], "code": code},
                )
            ).json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            cid = (await client.post("/chat/sessions", headers=headers)).json()["conversation_id"]
            proposal = (
                await client.post(
                    f"/chat/sessions/{cid}/messages",
                    headers=headers,
                    json={"message": "No reconozco el cargo de Mercado Verde"},
                )
            ).json()
            receipt = await client.post(
                f"/chat/sessions/{cid}/confirm",
                headers=headers,
                json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True},
            )
            assert receipt.status_code == 200 and receipt.json()["verified"]
            handoff = (
                await client.post(
                    f"/chat/sessions/{cid}/messages",
                    headers=headers,
                    json={"message": "Quiero un agente"},
                )
            ).json()["handoff"]["handoff_id"]
            principal = app.state.sessions[token]
            scope = Scope(principal.customer_id, principal.run_id, principal.session_id)
            with store.transaction(scope):
                app.state.card_states["fixture-card"] = {"status": "Frozen"}
            return {
                "token": token,
                "conversation": cid,
                "case": receipt.json()["case"],
                "handoff": handoff,
                "scope": scope,
            }
    finally:
        store.close()


def digest(dsn: str) -> dict[str, Any]:
    result = {}
    with psycopg.connect(dsn) as connection:
        for table in sorted(TABLES | {"audit_log"}):
            key = "sequence" if table == "audit_log" else "id"
            rows = connection.execute(
                sql.SQL(
                    "SELECT to_jsonb(t)::text FROM ops.{} t ORDER BY customer_id,run_id,sid,{}"
                ).format(sql.Identifier(table), sql.Identifier(key))
            ).fetchall()
            result[table] = {
                "rows": len(rows),
                "sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            }
    return result


async def recover(dsn: str, settings: Settings, original: dict[str, Any]) -> int:
    store = Store(dsn)
    app = create_app(settings, store=store)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + original["token"]}
            result = await client.get("/disputes/" + original["case"]["case_id"], headers=headers)
            assert result.status_code == 200
            from aclara.agent.contracts import DisputeCaseView

            assert (
                DisputeCaseView.model_validate(result.json()).model_dump(mode="json")
                == original["case"]
            )
            assert (
                await client.get("/handoffs/" + original["handoff"], headers=headers)
            ).status_code == 200
            assert (
                await client.get(
                    f"/chat/sessions/{original['conversation']}/trace", headers=headers
                )
            ).status_code == 200
        with store.transaction(original["scope"]):
            assert app.state.card_states["fixture-card"]["status"] == "Frozen"
        with psycopg.connect(dsn) as connection:
            scope = original["scope"]
            for key, value in (
                ("app.customer_id", scope.customer_id),
                ("app.run_id", scope.run_id),
                ("app.sid", scope.sid),
            ):
                connection.execute("SELECT set_config(%s,%s,true)", (key, value))
            entries = connection.execute(
                "SELECT sequence,canonical,prev_hash,row_hash FROM ops.audit_log ORDER BY sequence"
            ).fetchall()
            return verify(entries, (scope.customer_id, scope.run_id, scope.sid))
    finally:
        store.close()


def main() -> None:
    values = dotenv_values(ROOT / ".env")
    owner = make_conninfo(
        host="127.0.0.1",
        port=values.get("POSTGRES_HOST_PORT") or "15432",
        user=values.get("POSTGRES_USER") or "postgres",
        password=values.get("POSTGRES_PASSWORD") or "",
        dbname=values.get("POSTGRES_DB") or "postgres",
    )
    suffix = secrets.token_hex(6)
    source, target, actor = (
        "aclara_backup_" + suffix,
        "aclara_restore_" + suffix,
        "aclara_recovery_" + suffix,
    )
    password = secrets.token_urlsafe(32)
    folder = ROOT / "artifacts/recovery"
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / ("fixture-" + suffix + ".dump")
    environment = {**os.environ, "PGPASSWORD": values.get("POSTGRES_PASSWORD") or ""}
    base = ["docker", "compose", "exec", "-T", "-e", "PGPASSWORD", "postgres"]
    with psycopg.connect(owner, autocommit=True) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS").format(
                sql.Identifier(actor), sql.Literal(password)
            )
        )
        for name in (source, target):
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        try:
            source_owner, target_owner = (
                make_conninfo(owner, dbname=name) for name in (source, target)
            )
            migrate(source_owner, actor)
            settings = Settings(
                demo_username="recovery-fixture",
                demo_password=secrets.token_urlsafe(32),
                demo_role="ops",
            )
            original = asyncio.run(
                seed(make_conninfo(source_owner, user=actor, password=password), settings)
            )
            expected = digest(source_owner)
            started = perf_counter()
            descriptor = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as output:
                dump = subprocess.run(
                    [
                        *base,
                        "pg_dump",
                        "-h",
                        "127.0.0.1",
                        "-U",
                        values.get("POSTGRES_USER") or "postgres",
                        "-Fc",
                        source,
                    ],
                    cwd=ROOT,
                    env=environment,
                    stdout=output,
                    stderr=subprocess.PIPE,
                    check=False,
                )
            if dump.returncode:
                raise RuntimeError("Local dump failed; details redacted")
            with archive.open("rb") as data:
                restored = subprocess.run(
                    [
                        *base,
                        "pg_restore",
                        "--exit-on-error",
                        "-h",
                        "127.0.0.1",
                        "-U",
                        values.get("POSTGRES_USER") or "postgres",
                        "-d",
                        target,
                    ],
                    cwd=ROOT,
                    env=environment,
                    stdin=data,
                    capture_output=True,
                    check=False,
                )
            if restored.returncode:
                raise RuntimeError("Local restore failed; details redacted")
            assert digest(target_owner) == expected
            app_dsn = make_conninfo(target_owner, user=actor, password=password)
            entries = asyncio.run(recover(app_dsn, settings, original))
            with psycopg.connect(app_dsn) as connection:
                assert connection.execute("SELECT count(*) FROM ops.cases").fetchone() == (0,)
                assert connection.execute(
                    "SELECT bool_and(relrowsecurity AND relforcerowsecurity) FROM pg_class JOIN pg_namespace n ON n.oid=relnamespace WHERE n.nspname='ops' AND relkind='r'"
                ).fetchone() == (True,)
            report = {
                "status": "passed",
                "fixture_only": True,
                "tables": expected,
                "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "archive_bytes": archive.stat().st_size,
                "dump_restore_verify_seconds": round(perf_counter() - started, 3),
                "audit_entries_verified": entries,
                "original_session_case_handoff_trace_recovered": True,
                "no_context_rls_denied": True,
                "existing_application_database_modified": False,
            }
            (folder / "report.json").write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report))  # noqa: T201 -- aggregates only.
        finally:
            for name in (source, target):
                admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(actor)))
            archive.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit(
            "Local recovery rehearsal failed: " + type(error).__name__ + "; details redacted"
        ) from None
