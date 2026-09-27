"""Independent dev cases authored from policy/code, never frozen-suite utterances."""

from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_workflow_api import message

from aclara.agent.contracts import DisputeCaseView
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository


def ledger(two=False):
    base = TransactionRepository()._rows[0]
    first = replace(base, merchant_name="Taller Prisma", amount=17.43, currency="USD")
    second = replace(
        first, record_id="authored-prisma-2", merchant_name="Estudio Nube", amount=38.61
    )
    return TransactionRepository((first, second) if two else (first,))


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize(
    "text",
    [
        "No reconozco un cargo",
        "Não reconheço uma cobrança",
        "No hice una compra por 431.29 USD",
        "Não fiz uma compra de 431.29 USD",
        "No reconozco el cargo de Taller Prisma por 431.29 USD",
        "Não reconheço a cobrança de Taller Prisma por 431.29 USD",
        "No reconozco el cargo de Taller Prisma; no estoy seguro de cuál es",
        "Não reconheço a cobrança de Taller Prisma; não tenho certeza de qual é",
    ],
)
def test_no_write_proposal_without_consistent_identification(system, text):
    async def check():
        app = create_app(_settings(), ledger(), runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, conv = await message(client, headers, text)
            assert result["response_type"] in {"clarify", "choose_transaction"}
            # Even a guessed/stale confirmation cannot bypass identification.
            denied = await client.post(
                f"/chat/sessions/{conv}/confirm",
                headers=headers,
                json={"proposal_hash": "0" * 64, "confirmed": True},
            )
            assert denied.status_code == 409
            assert not app.state.cases

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize(
    "reply",
    [
        "No el primero; no puedo elegir",
        "Não o primeiro; não consigo escolher",
        "El primero o el segundo",
        "O primeiro ou o segundo",
    ],
)
def test_ambiguous_choices_escalate_and_cannot_reopen(system, reply):
    async def check():
        app = create_app(_settings(), ledger(True), runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, conv = await message(client, headers, "No reconozco una compra")
            assert result["response_type"] == "choose_transaction"
            result, _ = await message(client, headers, reply, conv)
            assert result["response_type"] in {"clarify", "choose_transaction"}
            result, _ = await message(client, headers, reply, conv)
            assert result["handoff"]["reason_codes"] == ["ESC-04"]
            packet = result["handoff"]["handoff_id"]
            again, _ = await message(
                client, headers, "No reconozco el cargo de Taller Prisma", conv
            )
            assert again["handoff"]["handoff_id"] == packet
            assert not app.state.cases

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
def test_followup_invalidates_old_action_hash(system):
    async def check():
        app = create_app(_settings(), ledger(), runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, conv = await message(client, headers, "No reconozco el cargo de Taller Prisma")
            old = result["proposal"]["proposal_hash"]
            await message(client, headers, "Quiero consultar el estado de mi caso", conv)
            denied = await client.post(
                f"/chat/sessions/{conv}/confirm",
                headers=headers,
                json={"proposal_hash": old, "confirmed": True},
            )
            assert denied.status_code == 409
            assert not app.state.cases

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
def test_positive_identification_still_commits_with_readback(system):
    async def check():
        app = create_app(_settings(), ledger(), runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, conv = await message(
                client, headers, "No reconozco el cargo de Taller Prisma por 17.43 USD"
            )
            confirmed = await client.post(
                f"/chat/sessions/{conv}/confirm",
                headers=headers,
                json={"proposal_hash": result["proposal"]["proposal_hash"], "confirmed": True},
            )
            assert confirmed.status_code == 200 and confirmed.json()["verified"]
            case = confirmed.json()["case"]
            assert DisputeCaseView.model_validate(
                (await client.get("/disputes/" + case["case_id"], headers=headers)).json()
            ) == DisputeCaseView.model_validate(case)
            assert len(app.state.cases) == 1

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
def test_explicitly_unmatched_details_exhaust_clarification_budget(system):
    async def check():
        app = create_app(_settings(), ledger(), runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, conv = await message(client, headers, "No reconozco una compra por 431.29 USD")
            assert result["response_type"] == "clarify"
            result, _ = await message(client, headers, "431.29 USD", conv)
            assert result["handoff"]["reason_codes"] == ["ESC-04"]
            assert not app.state.cases

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
def test_changed_transaction_cannot_use_previous_confirmation(system):
    async def check():
        repo = ledger()
        app = create_app(_settings(), repo, runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, conv = await message(client, headers, "No reconozco el cargo de Taller Prisma")
            repo._rows = (replace(repo._rows[0], amount=21.19),)
            response = await client.post(
                f"/chat/sessions/{conv}/confirm",
                headers=headers,
                json={"proposal_hash": result["proposal"]["proposal_hash"], "confirmed": True},
            )
            assert response.status_code == 409
            assert not app.state.cases

    asyncio.run(check())
