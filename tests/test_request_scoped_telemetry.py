"""Concurrent authored requests: exact telemetry, no network or model spend."""

import asyncio
import json
import re
from dataclasses import replace
from threading import Barrier

from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in

from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec, ProviderResponse, TokenUsage
from aclara.ops.store import Scope, Store


def test_five_requests_keep_exact_call_attribution_and_no_process_history():
    barrier = Barrier(5)

    class Adapter:
        def complete(self, spec, system, user, schema, key):
            marker = re.search(r"authored-turn-\d", user).group()
            barrier.wait(timeout=5)  # All provider calls must overlap.
            return ProviderResponse(
                json.dumps(
                    {
                        "language": "es",
                        "intent": "charge_inquiry",
                        "intent_confidence": 0.99,
                        "merchant_expr": "Taller Prisma",
                        "amount_expr": "17.43",
                        "currency_expr": "USD",
                    }
                ),
                spec.model_id,
                TokenUsage(),
                generation_id=marker,
            )

    async def check():
        store = Store()
        client = StructuredClient(
            {r: ModelSpec("mock", "authored") for r in ("nlu", "phrase")},
            {},
            budget_usd=0,
            mock_response=lambda *_: "{}",
        )
        client._adapters["mock"] = Adapter()
        base = TransactionRepository()._rows[0]
        ledger = TransactionRepository(
            (replace(base, merchant_name="Taller Prisma", amount=17.43, currency="USD"),)
        )
        runtime = Runtime(system="P", capture_history=False)
        app = create_app(_settings(), ledger, runtime, client, store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
            scopes = []
            for i in range(5):
                token = await _sign_in(api)
                headers = {"Authorization": "Bearer " + token}
                cid = (await api.post("/chat/sessions", headers=headers)).json()["conversation_id"]
                scopes.append((i, token, headers, cid))
            results = await asyncio.gather(
                *[
                    api.post(
                        f"/chat/sessions/{cid}/messages",
                        headers=headers,
                        json={
                            "message": f"¿Qué es el cargo de Taller Prisma por 17.43 USD? authored-turn-{i}"
                        },
                    )
                    for i, _, headers, cid in scopes
                ]
            )
            assert all(r.status_code == 200 and r.json()["outcome"] == "explained" for r in results)
            for i, token, _, cid in scopes:
                p = app.state.sessions[token]
                with store.transaction(Scope(p.customer_id, p.run_id, p.session_id)):
                    records = [
                        r for r in app.state.executions.values() if r["conversation_id"] == cid
                    ]
                assert len(records) == 1
                calls = [e for e in records[0]["events"] if e["event"] == "llm_call"]
                assert len(calls) == 1 and calls[0]["generation_id"] == f"authored-turn-{i}"
                assert sum(e["event"] == "nlu" for e in records[0]["events"]) == 1
                assert calls[0]["cost_usd"] == 0
            assert not runtime.events and not client.records and app.state.ai.cursor == 0
            assert not app.state.session_turns.sessions and app.state.session_turns.waiting == 0

    asyncio.run(check())
