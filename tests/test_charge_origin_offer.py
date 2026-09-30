"""Authored ES/PT charge-origin regressions; no held-out inputs or paid calls."""

from __future__ import annotations

import asyncio
import json

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.conversation import unfamiliar_charge
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.agent.runtime import Runtime
from aclara.agent.selection import uncertain, unfamiliar_about_charge
from aclara.api.app import create_app
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec

ORIGINS = (
    ("es", "No recuerdo de dónde vino ese cobro de Taller Prisma."),
    ("es", "No me acuerdo de dónde salió este cargo de Taller Prisma."),
    ("pt", "Não lembro de onde veio essa cobrança de Taller Prisma."),
    ("pt", "Não me lembro de onde surgiu esse lançamento de Taller Prisma."),
)


@pytest.mark.parametrize("language,text", ORIGINS)
def test_charge_origin_memory_is_unfamiliarity(language, text):
    assert unfamiliar_about_charge(text)
    assert unfamiliar_charge(text)
    assert not uncertain(text)


@pytest.mark.parametrize(
    "text",
    [
        "No recuerdo de dónde vino ese cobro; no sé cuál de los dos cargos es.",
        "Não lembro de onde veio essa cobrança; não sei qual das duas é.",
        "No recuerdo de dónde vino ese cobro; no puedo elegir.",
        "Não lembro de onde veio essa cobrança; não consigo escolher.",
        "No recuerdo de dónde vino el monto.",
        "Não lembro de onde veio o valor.",
        "No recuerdo cuál de los cargos vino de Taller Prisma.",
        "Não lembro qual das cobranças veio de Taller Prisma.",
    ],
)
def test_selection_uncertainty_is_not_erased(text):
    assert uncertain(text)


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize("language,opening", ORIGINS)
def test_origin_memory_offers_then_cancels_without_write(system, language, opening):
    async def check():
        nlu_calls = 0

        def answer(_system, _user, schema):
            nonlocal nlu_calls
            assert schema is ExtractedNlu  # offers/clarifications stay deterministic
            nlu_calls += 1
            return json.dumps(
                {
                    "intent": "charge_inquiry" if nlu_calls == 1 else "dispute_charge",
                    "intent_confidence": 0.99,
                    "language": language,
                    "merchant_expr": "Taller Prisma" if nlu_calls == 1 else None,
                    "unfamiliar_charge": nlu_calls == 1,
                    "recognition": None if nlu_calls == 1 else "denied",
                }
            )

        llm = StructuredClient(
            {route: ModelSpec("mock", "authored-origin") for route in ("nlu", "phrase")},
            {},
            mock_response=answer,
        )
        app = create_app(_settings(), ledger(), runtime=Runtime(system=system), llm_client=llm)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            offered, conv = await message(client, headers, opening)
            assert offered["response_type"] == "offer_dispute"
            assert offered["outcome"] == "awaiting_dispute_decision"
            assert offered["transaction"]["merchant"] == "Taller Prisma"
            assert not offered["proposal"] and not app.state.cases
            filing = (
                "Quiero disputar ese cargo" if language == "es" else "Quero contestar essa cobrança"
            )
            proposed, _ = await message(client, headers, filing, conv)
            assert proposed["response_type"] == "confirm_action"
            cancelled = await client.post(
                f"/chat/sessions/{conv}/confirm",
                headers=headers,
                json={"proposal_hash": proposed["proposal"]["proposal_hash"], "confirmed": False},
            )
            assert cancelled.status_code == 200
            assert cancelled.json()["outcome"] == "cancelled"
            assert not app.state.cases

    asyncio.run(check())
