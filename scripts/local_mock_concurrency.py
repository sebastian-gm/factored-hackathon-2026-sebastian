"""Local ASGI concurrency measurement with authored fixtures and mock NLU only."""

from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from statistics import median, quantiles
from threading import Event
from typing import Any

from httpx import ASGITransport, AsyncClient

from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec
from aclara.ops.store import Scope, Store
from aclara.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


async def measure(sessions: int, delay_seconds: float) -> dict[str, Any]:
    if not 2 <= sessions <= 10 or not 0 < delay_seconds <= 5:
        raise ValueError("Use 2-10 sessions and a mock delay above zero, at most five seconds")
    settings = Settings(
        demo_username="authored-concurrency",
        demo_password=secrets.token_urlsafe(32),
        agent_system="P",
        llm_provider="mock",
        ops_backend="memory",
        ledger_backend="fixture",
    )
    base = TransactionRepository()._rows[0]
    repository = TransactionRepository(
        (replace(base, merchant_name="Taller Prisma", amount=17.43, currency="USD"),)
    )
    store = Store()
    entered = Event()
    outside_transactions: list[bool] = []

    def answer(_system: str, _user: str, schema: Any) -> str:
        if schema.__name__ != "ExtractedNlu":
            raise RuntimeError("Expected one mock NLU call per explained turn")
        outside = store.current.get() is None
        outside_transactions.append(outside)
        entered.set()
        if not outside:
            raise RuntimeError("NLU held operational storage during the mock wait")
        time.sleep(delay_seconds)
        return json.dumps(
            {
                "language": "es",
                "intent": "charge_inquiry",
                "intent_confidence": 0.99,
                "merchant_expr": "Taller Prisma",
                "amount_expr": "17.43",
                "currency_expr": "USD",
            }
        )

    llm = StructuredClient(
        {role: ModelSpec("mock", "local-concurrency") for role in ("nlu", "phrase")},
        {},
        budget_usd=0,
        mock_response=answer,
        risk_second_opinion_enabled=False,
    )
    app = create_app(settings, repository, Runtime(system="P"), store=store, llm_client=llm)
    turns: list[float] = []
    reads: list[float] = []
    headers_and_ids = []
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://local.test") as api:
        for _ in range(sessions):
            challenge = (
                await api.post(
                    "/auth/login",
                    json={"username": settings.demo_username, "password": settings.demo_password},
                )
            ).json()
            preauth = {"X-Preauth-Token": challenge["preauth_token"]}
            code = (
                await api.get(f"/auth/challenges/{challenge['challenge_id']}/sms", headers=preauth)
            ).json()["code"]
            verified = await api.post(
                "/auth/otp/verify",
                headers=preauth,
                json={"challenge_id": challenge["challenge_id"], "code": code},
            )
            if verified.status_code != 200:
                raise RuntimeError("Authored login/OTP did not succeed")
            header = {"Authorization": "Bearer " + verified.json()["access_token"]}
            created = await api.post("/chat/sessions", headers=header)
            if created.status_code != 200:
                raise RuntimeError("Authored conversation creation did not succeed")
            headers_and_ids.append((header, created.json()["conversation_id"]))

        async def turn(header: dict[str, str], cid: str) -> None:
            started = time.perf_counter()
            response = await api.post(
                f"/chat/sessions/{cid}/messages",
                headers=header,
                json={"message": "¿Qué es el cargo de Taller Prisma por 17.43 USD?"},
            )
            turns.append(time.perf_counter() - started)
            if response.status_code != 200 or response.json()["outcome"] != "explained":
                raise RuntimeError("Mock turn did not produce the expected scoped explanation")

        started = time.perf_counter()
        pending = [asyncio.create_task(turn(header, cid)) for header, cid in headers_and_ids]
        if not await asyncio.to_thread(entered.wait, 10):
            raise RuntimeError("Mock NLU did not start")
        for header, _ in headers_and_ids:
            for path in ("/healthz", "/me", "/transactions"):
                before_read = time.perf_counter()
                response = await asyncio.wait_for(api.get(path, headers=header), 2)
                reads.append(time.perf_counter() - before_read)
                if response.status_code != 200:
                    raise RuntimeError("Concurrent authenticated read did not succeed")
        await asyncio.wait_for(asyncio.gather(*pending), sessions * (delay_seconds + 5))
        wall_seconds = time.perf_counter() - started

    if len(llm.records) != sessions or any(
        record.provider != "mock" or record.cost_usd != 0 for record in llm.records
    ):
        raise RuntimeError("Measurement must contain exactly the zero-cost mock NLU calls")
    for header, cid in headers_and_ids:
        token = header["Authorization"].removeprefix("Bearer ")
        principal = app.state.sessions[token]
        with store.transaction(
            Scope(principal.customer_id, principal.run_id, principal.session_id)
        ):
            records = [r for r in app.state.executions.values() if r.get("conversation_id") == cid]
            if len(records) != 1 or sum(e["event"] == "nlu" for e in records[0]["events"]) != 1:
                raise RuntimeError("Concurrent turn trace attribution failed")
            if app.state.cases:
                raise RuntimeError("Read-only measurement unexpectedly created a case")
    return {
        "mode": "local/mock/ASGI",
        "operational_store": "memory",
        "customer_count": 1,
        "sessions": sessions,
        "delay_seconds_per_nlu": delay_seconds,
        "wall_seconds": wall_seconds,
        "turn_p50_seconds": median(turns),
        "turn_p95_seconds": quantiles(turns, n=100, method="inclusive")[94],
        "turn_seconds": sorted(turns),
        "concurrent_reads": len(reads),
        "read_max_seconds": max(reads),
        "nlu_outside_transaction": all(outside_transactions),
        "nlu_calls": len(llm.records),
        "scoped_execution_records": sessions,
        "case_writes": 0,
        "model_cost_usd": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, nargs="+", default=[3, 5])
    parser.add_argument("--delay-seconds", type=float, default=1)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "artifacts/local-mock-concurrency/results.json"
    )
    args = parser.parse_args()
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git is required to record measurement provenance")
    source = subprocess.run(  # noqa: S603 -- fixed Git metadata command with repository -C.
        [git, "-C", str(ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    report = {
        "source_sha": source,
        "batches": [asyncio.run(measure(n, args.delay_seconds)) for n in args.sessions],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    args.output.chmod(0o600)
    sys.stdout.write(json.dumps(report) + "\n")


if __name__ == "__main__":
    main()
