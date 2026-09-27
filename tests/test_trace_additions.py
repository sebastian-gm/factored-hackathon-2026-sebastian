from __future__ import annotations

import asyncio
import secrets

from evals.runner import _new_authenticated_client

from aclara.bank.repository import TransactionRepository
from aclara.bank.serving import Persona, demo_story_mappings, persona_views
from aclara.ops.store import Scope
from aclara.settings import Settings


def test_trace_metadata_keeps_failures_nulls_and_filters_private_fields():
    async def check():
        app, client, token, cid = await _new_authenticated_client(
            Settings(
                demo_username="staff-fixture",
                demo_password=secrets.token_urlsafe(24),
                demo_role="agent",
            )
        )
        principal = app.state.sessions[token]
        with app.state.store.transaction(
            Scope(principal.customer_id, principal.run_id, principal.session_id)
        ):
            app.state.executions["risk-fixture"] = {
                "conversation_id": cid,
                "events": [
                    {
                        "event": "llm_call",
                        "provider": "typesafe",
                        "model_id": "jev",
                        "prompt_id": "risk-v1",
                        "input_tokens": 2,
                        "output_tokens": 3,
                        "cost_usd": None,
                        "latency_ms": 4,
                        "route": "nlu_risk_second_opinion",
                        "status": "provider_error",
                        "attempt": 2,
                        "judgments": {
                            "gemini_raw_flags": {"distress": True, "customer_id": "private"},
                            "gemini_raw_probabilities": {"distress": None},
                            "jev_raw_probabilities": {"distress": 0.7, "legal": None, "bad": 0.9},
                            "jev_threshold_flags": None,
                            "union_flags": {"distress": True},
                            "threshold": 0.5,
                            "degradation": "incomplete_risk_answers",
                            "primary_failed": False,
                            "thinking": "private",
                            "gemini_intent_confidence": 0.99,
                        },
                    },
                ],
            }
        try:
            response = await client.get(
                f"/chat/sessions/{cid}/trace", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            llm = response.json()["events"][0]["llm"]
            assert llm["attempt"] == 2 and llm["status"] == "provider_error"
            assert llm["route"] == "nlu_risk_second_opinion" and llm["cost_usd"] is None
            assert llm["judgments"]["jev_raw_probabilities"] == {"distress": 0.7, "legal": None}
            assert llm["judgments"]["jev_threshold_flags"] is None
            assert "private" not in response.text and "thinking" not in response.text
            assert "gemini_intent_confidence" not in response.text
        finally:
            await client.aclose()

    asyncio.run(check())


def test_story_hints_require_approved_identity_role_and_scoped_facts():
    ledger = TransactionRepository()
    customer = ledger._rows[0].customer_id
    personas = {
        "demo.es.mx": Persona("demo.es.mx", customer, "es-MX", "ops"),
        "demo.pt.br": Persona("demo.pt.br", customer, "pt-BR", "ops"),
        "unreviewed": Persona("unreviewed", customer, "es-MX", "ops"),
    }
    mappings = demo_story_mappings(ledger, personas, Settings().bank_clock)
    assert mappings == {"demo.es.mx": ["explain", "fraud"], "demo.pt.br": ["ambiguous"]}
    assert persona_views(personas, mappings)[2]["demo_stories"] == []
    personas["demo.es.mx"] = Persona("demo.es.mx", "no-owned-records", "es-MX", "ops")
    assert demo_story_mappings(ledger, personas, Settings().bank_clock)["demo.es.mx"] == []
