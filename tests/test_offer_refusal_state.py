"""New authored offer-refusal regressions; no frozen suite or paid providers."""

from __future__ import annotations

import asyncio
import json

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.conversation import declines_dispute
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec
from aclara.ops.store import Store


@pytest.mark.parametrize("reply", ["no", "não", "no sé", "não sei"])
def test_isolated_assent_or_uncertainty_is_not_an_explicit_filing_refusal(reply):
    assert not declines_dispute(reply)


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("recognizes", [False, True])
def test_polite_refusal_cancels_but_actual_recollection_still_explains(
    system, language, recognizes
):
    async def check():
        calls = 0

        def answer(_system, _user, schema):
            nonlocal calls
            if schema is not ExtractedNlu:
                return "{}"  # Explanation falls back safely; no phrase/network call.
            calls += 1
            return json.dumps(
                {
                    "intent": "charge_inquiry",
                    "intent_confidence": 0.99,
                    "language": language,
                    "merchant_expr": "Taller Prisma" if calls == 1 else None,
                    "unfamiliar_charge": calls == 1,
                    # Saved-style false recognition is corrected by #85 before
                    # orchestration. Actual recollection is preserved.
                    "recognition": None if calls == 1 else "recognized",
                    "customer_confirms": None if calls == 1 else "yes",
                }
            )

        llm = StructuredClient(
            {route: ModelSpec("mock", "authored-refusal") for route in ("nlu", "phrase")},
            {},
            mock_response=answer,
        )
        settings = _settings()
        store = Store()
        app = create_app(
            settings, ledger(), runtime=Runtime(system=system), store=store, llm_client=llm
        )
        opening = (
            "No reconozco el cargo de Taller Prisma"
            if language == "es"
            else "Não reconheço a cobrança de Taller Prisma"
        )
        refusal = (
            "Gracias, prefiero no abrir una disputa; déjalo así."
            if language == "es"
            else "Obrigada, prefiro não abrir contestação; pode deixar como está."
        )
        if recognizes:
            refusal = (
                "Ya me acordé, la compra era mía. "
                if language == "es"
                else "Agora lembrei, essa compra foi minha. "
            ) + refusal
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            offer, cid = await message(client, headers, opening)
            assert offer["response_type"] == "offer_dispute"
            response, _ = await message(client, headers, refusal, cid)
            assert response["outcome"] == ("explained" if recognizes else "cancelled")
            assert not response.get("proposal") and not response.get("handoff")
            assert not app.state.cases
            rejected = await client.post(
                f"/chat/sessions/{cid}/confirm",
                headers=headers,
                json={"proposal_hash": "0" * 64, "confirmed": True},
            )
            assert rejected.status_code == 409
        # Serialized cancellation survives application restart. A later ordinary
        # inquiry does not inherit the cancelled offer or claim unfamiliarity.
        app = create_app(settings, ledger(), runtime=Runtime(system=system), store=store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            result, _ = await message(client, headers, "Estado del cargo de Taller Prisma", cid)
            assert result["outcome"] == "explained"
            assert not app.state.cases

    asyncio.run(check())
