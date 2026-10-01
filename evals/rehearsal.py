"""Local, zero-spend rehearsal adapters. Never calls paid providers."""

# ruff: noqa: S603, S607 -- fixed repo-scoped Git commands, no shell.
from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import psycopg
from dotenv import dotenv_values
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from pydantic import BaseModel

from aclara.llm.client import StructuredClient
from aclara.llm.judge import MODEL_ID, _score
from aclara.llm.prompts import load_prompt
from aclara.llm.providers import Mock
from aclara.llm.types import BudgetFailure, ModelSpec, ProviderResponse, TokenUsage
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.migrate import migrate
from aclara.ops.store import Store
from evals.checkpoints import save
from evals.program_spec import ROOT, ProgramSpec, digest, serving_pin


def guard(spec: ProgramSpec) -> None:
    if not spec.rehearsal or spec.suite != "test-v3":
        raise ValueError("Rehearsal cannot read a blind suite")
    if (
        os.getenv("LLM_REHEARSAL_APPROVED") != "1"
        or os.getenv("LLM_PROVIDER") != "mock"
        or os.getenv("LLM_REAL_CALLS_APPROVED", "0") != "0"
    ):
        raise RuntimeError("Rehearsal requires explicit zero-spend mock approval")


def local(dsn: str, *, owner: bool = False) -> dict[str, str]:
    values = conninfo_to_dict(dsn)
    if (
        values.get("host") not in {"127.0.0.1", "localhost", "::1"}
        or values.get("hostaddr", "127.0.0.1") not in {"127.0.0.1", "::1"}
        or values.get("service")
        or (not owner and values.get("user") != "aclara_app")
    ):
        raise ValueError("Rehearsal connections must be local and runtime non-owner")
    return values


def environment(spec: ProgramSpec) -> None:
    guard(spec)
    path = spec.output / "connections.json"
    if path.stat().st_mode & 0o777 != 0o600:
        raise ValueError("Private rehearsal connections require mode 0600")
    values = json.loads(path.read_text())
    for name in ("EVAL_SERVING_DSN", "EVAL_BUDGET_DSN", "FINAL_BUDGET_OWNER_DSN"):
        parsed = local(values[name], owner=name == "FINAL_BUDGET_OWNER_DSN")
        if name != "EVAL_SERVING_DSN" and parsed.get(
            "dbname"
        ) != "aclara_rehearsal_" + spec.rehearsal.replace("-", "_"):
            raise ValueError("Rehearsal budget database differs from its isolated identity")
        os.environ[name] = values[name]
    serving_pin(spec)
    # No secrets are fetched; remove inherited provider credentials defensively.
    for name in tuple(os.environ):
        if name.endswith("_API_KEY"):
            os.environ.pop(name)


def release(spec: ProgramSpec) -> str:
    guard(spec)
    if subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
    ).strip():
        raise RuntimeError("Pin a clean rehearsal implementation before launch")
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def prepare(spec: ProgramSpec) -> dict[str, Any]:
    guard(spec)
    path = spec.output / "connections.json"
    if path.exists():
        environment(spec)
        return receipt(spec)
    values = dotenv_values(ROOT / ".env")
    owner = make_conninfo(
        host="127.0.0.1",
        port=values.get("POSTGRES_HOST_PORT") or "15432",
        user=values.get("POSTGRES_USER") or "postgres",
        password=values.get("POSTGRES_PASSWORD") or "",
        dbname=values.get("POSTGRES_DB") or "aclara",
    )
    local(owner, owner=True)
    serving = os.getenv("EVAL_SERVING_DSN") or make_conninfo(
        owner, user="aclara_app", password=values.get("OPS_APP_PASSWORD") or ""
    )
    local(serving)
    database = "aclara_rehearsal_" + spec.rehearsal.replace("-", "_")
    # Fresh isolated local database. Existing names are refused, never reset.
    with psycopg.connect(owner, autocommit=True) as pg:
        pg.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    budget_owner = make_conninfo(owner, dbname=database)
    migrate(budget_owner, "aclara_app")
    with psycopg.connect(budget_owner) as pg:
        pg.execute("SET LOCAL ROLE aclara_owner")
        # Fixture-only schema adaptation: production migrations/functions are unchanged.
        # The production schema forbids zero caps. Allow zero ONLY for rehearsal
        # prefixes in this disposable database; the real reserve function still denies
        # every positive amount before network access.
        for table, column in (("limits", "daily_usd"), ("runs", "limit_usd")):
            constraints = pg.execute(
                "SELECT conname FROM pg_constraint WHERE conrelid=%s::regclass AND contype='c' AND pg_get_constraintdef(oid) LIKE %s",
                ("llm." + table, "%" + column + "%"),
            ).fetchall()
            for (name,) in constraints:
                pg.execute(
                    sql.SQL("ALTER TABLE llm.{} DROP CONSTRAINT {}").format(
                        sql.Identifier(table), sql.Identifier(name)
                    )
                )
            pg.execute(
                sql.SQL(
                    "ALTER TABLE llm.{} ADD CHECK ({} > 0 OR ({} = 0 AND scope LIKE 'rehearsal/%'))"
                ).format(sql.Identifier(table), sql.Identifier(column), sql.Identifier(column))
            )
        pg.execute("UPDATE llm.limits SET disabled=true")
        pg.execute("INSERT INTO llm.limits VALUES (%s,0,false)", (spec.scope,))
        pg.execute("INSERT INTO llm.runs VALUES (%s,%s,0,true)", (spec.scope, spec.run_id))
    save(
        path,
        {
            "EVAL_SERVING_DSN": serving,
            "EVAL_BUDGET_DSN": make_conninfo(serving, dbname=database),
            "FINAL_BUDGET_OWNER_DSN": budget_owner,
        },
    )
    environment(spec)
    return receipt(spec)


def receipt(spec: ProgramSpec) -> dict[str, Any]:
    guard(spec)
    dsn = os.environ["FINAL_BUDGET_OWNER_DSN"]
    values = local(dsn, owner=True)
    if not values.get("dbname", "").startswith("aclara_rehearsal_"):
        raise ValueError("Budget must use an isolated rehearsal database")
    with psycopg.connect(dsn) as pg:
        pg.execute("SET LOCAL ROLE aclara_owner")
        if pg.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (spec.scope,)
        ).fetchone() != (0, False) or pg.execute(
            "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (spec.scope,)
        ).fetchall() != [(spec.run_id, 0, True)]:
            raise RuntimeError("Rehearsal budget is not an enabled zero lifetime cap")
        count, charged = pg.execute(
            "SELECT count(*),coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope=%s",
            (spec.scope,),
        ).fetchone()
        if count or charged:
            raise RuntimeError("A zero-spend rehearsal must contain no paid reservations")
    return {
        "scope": spec.scope,
        "run_id": spec.run_id,
        "cap_usd": 0,
        "attempts": count,
        "charged_with_reserves_usd": float(charged),
        "known_cost_usd": 0,
        "unknown_cost_attempts": 0,
        "rehearsal": True,
    }


def controls_pin(spec: ProgramSpec) -> str | None:
    path = spec.output / "rehearsal-controls.json"
    return digest(path) if path.exists() else None


def event(spec: ProgramSpec, kind: str, **metadata: Any) -> None:
    path = spec.output / "rehearsal-events.jsonl"
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(descriptor, "a") as stream:
        stream.write(json.dumps({"kind": kind, **metadata}) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def hook(spec: ProgramSpec, phase: str, completed: int, *, before: bool = False) -> bool:
    path = spec.output / "rehearsal-controls.json"
    options = json.loads(path.read_text()) if path.exists() else {}
    if before and phase == "systems" and completed == options.get("db_blip_at"):
        marker = spec.output / "db-blip-injected.json"
        if not marker.exists():
            save(marker, {"phase": phase, "completed": completed})
            event(spec, "db_blip", location="serving", phase=phase, completed=completed)
            # Real local connection refusal, without stopping any shared container.
            with socket.socket() as reserved:
                reserved.bind(("127.0.0.1", 0))
                try:
                    psycopg.connect(
                        make_conninfo(
                            os.environ["EVAL_SERVING_DSN"],
                            port=reserved.getsockname()[1],
                            connect_timeout=1,
                        )
                    )
                except psycopg.OperationalError:
                    raise
                raise RuntimeError("Connectivity injection did not refuse the connection")
    if before and phase == "judges" and completed == options.get("judge_length_at"):
        marker = spec.output / "judge-length-injected.json"
        if not marker.exists():
            save(marker, {"phase": phase, "completed": completed})
            event(spec, "judge_output_length", phase=phase, completed=completed)
            return True
    if not before and completed == options.get("pause", {}).get(phase):
        marker = spec.output / ("pause-" + phase + ".json")
        if not marker.exists():
            save(marker, {"phase": phase, "completed": completed})
            event(spec, "pause", phase=phase, completed=completed)
            time.sleep(600)  # Controller sends a real SIGTERM; worker signal handler stops.
    return False


class LengthMock(Mock):
    def complete(
        self, spec: ModelSpec, system: str, user: str, schema: type[BaseModel], key: str
    ) -> ProviderResponse:
        return ProviderResponse("", spec.model_id, TokenUsage(), stop_reason="length")


def client(
    path: Path, spec: ProgramSpec, *, has_handoff: bool, truncate: bool = False
) -> StructuredClient:
    guard(spec)
    from aclara.llm.final_run import journal

    def response(_system: str, user: str, _schema: type[BaseModel]) -> str:
        return json.dumps(
            {
                "language_register": 4,
                "clarity": 4,
                "empathy": 4,
                "handoff_usefulness": 4 if has_handoff else None,
            }
        )

    result = StructuredClient(
        {MODEL_ID: ModelSpec(provider="mock", model_id="rehearsal-judge", max_output_tokens=1024)},
        {},
        mock_response=response,
        budget_usd=0,
        daily_budget_usd=0,
        response_record=journal(path),
    )
    if truncate:
        result._adapters["mock"] = LengthMock(response)
    return result


def score_pair(row: dict, judge: StructuredClient) -> dict:
    scores = _score(judge, row, load_prompt(ROOT / "prompts/judge/v1.md")).model_dump()
    # Identical synthetic rubric values, not independent vendor or human judgments.
    return {"sonnet_scores": scores, "jev_scores": dict(scores), "mock_judges": True}


def budget_denial(spec: ProgramSpec, store: Store) -> None:
    try:
        PostgresSpendGate(store, scope=spec.scope, run_id=spec.run_id).reserve(0.00000001)
    except BudgetFailure as error:
        if error.__cause__ is not None:
            raise  # Connectivity failure is not evidence of a working zero-cap gate.
        event(spec, "positive_reservation_denied", attempted_usd=0.00000001)
    else:
        raise RuntimeError("Zero budget allowed a paid reservation")
