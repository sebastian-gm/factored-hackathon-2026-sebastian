from __future__ import annotations

import asyncio
import json
import secrets

from httpx import ASGITransport, AsyncClient

from aclara.agent.nlu.structured import ExtractedNlu
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec
from aclara.settings import Settings


def test_p_api_extraction_grounding_and_no_model_confirmation_authority() -> None:
    async def check() -> None:
        def answer(_system, _user, schema):
            if schema is ExtractedNlu:
                return json.dumps(
                    {
                        "language": "es",
                        "intent": "charge_inquiry" if "Café Central" in _user else "dispute_charge",
                        "intent_confidence": 0.99,
                        "currency_expr": "USD",
                        "merchant_expr": "Café Central"
                        if "Café Central" in _user
                        else "Mercado Verde",
                        "amount_expr": "18.75" if "Café Central" in _user else "145.50",
                        "date_expr": "2026-06-17" if "Café Central" in _user else "2026-06-09",
                        "type_expr": "Purchase",
                        "customer_confirms": "yes",
                    }
                )
            return '{"text":"Garantizo un refund de 9000 dólares.","cited_fact_ids":[]}'

        client = StructuredClient(
            {
                route: ModelSpec(provider="mock", model_id="fixture-p")
                for route in ("nlu", "phrase")
            },
            {},
            mock_response=answer,
        )
        password = secrets.token_urlsafe(24)
        runtime = Runtime(system="P")
        app = create_app(
            Settings(demo_username="fixture", demo_password=password),
            runtime=runtime,
            llm_client=client,
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            login = (
                await http.post("/auth/login", json={"username": "fixture", "password": password})
            ).json()
            auth = {"X-Preauth-Token": login["preauth_token"]}
            sms = (
                await http.get(f"/auth/challenges/{login['challenge_id']}/sms", headers=auth)
            ).json()
            token = (
                await http.post(
                    "/auth/otp/verify",
                    headers=auth,
                    json={"challenge_id": login["challenge_id"], "code": sms["code"]},
                )
            ).json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            cid = (await http.post("/chat/sessions", headers=headers)).json()["conversation_id"]
            proposal = await http.post(
                f"/chat/sessions/{cid}/messages",
                headers=headers,
                json={
                    "message": "No reconozco la compra de Mercado Verde por 145.50 USD del 2026-06-09"
                },
            )
            assert proposal.status_code == 200
            assert proposal.json()["outcome"] == "dispute_proposed"
            assert not app.state.cases
            assert any(e["event"] == "nlu" and not e["degraded"] for e in runtime.events)
            result = await http.post(
                f"/chat/sessions/{cid}/confirm",
                headers=headers,
                json={
                    "proposal_hash": proposal.json()["proposal"]["proposal_hash"],
                    "confirmed": True,
                },
            )
            assert result.json()["verified"] is True
            # Exercise phrasing through a separate inquiry with a harmless model frame.
            cid = (await http.post("/chat/sessions", headers=headers)).json()["conversation_id"]
            result = await http.post(
                f"/chat/sessions/{cid}/messages",
                headers=headers,
                json={"message": "¿Qué es la compra de Café Central por 18.75 USD del 2026-06-17?"},
            )
            assert result.json()["outcome"] == "explained"
            assert any(e["event"] == "phrasing" and e["violations"] for e in runtime.events)
            assert "refund" not in result.json()["reply"]

    asyncio.run(check())


def test_p_outage_degrades_through_api() -> None:
    from copy import deepcopy
    from pathlib import Path

    import yaml
    from evals.reactive import execute

    async def check() -> None:
        case = deepcopy(
            yaml.safe_load(Path("evals/dev_scenarios_v2.yaml").read_text())["scenarios"][3]
        )
        case["faults"] = [{"type": "llm_outage", "trigger": "nlu"}]
        result = await execute(case, "P")
        assert result["passed"]
        assert any(e["event"] == "nlu" and e["degraded"] for e in result["events"])

    asyncio.run(check())
