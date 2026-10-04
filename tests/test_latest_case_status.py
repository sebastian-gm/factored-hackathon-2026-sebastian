"""Authored latest-case regression, with case IDs ordered against creation time."""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.contracts import DisputeCaseView
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize("language", ["es", "pt"])
def test_generic_status_uses_creation_time_and_explicit_reference_is_preserved(
    monkeypatch: pytest.MonkeyPatch, system: str, language: str
) -> None:
    async def check() -> None:
        app = create_app(_settings(), ledger(two=True), runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            conversation: str | None = None
            receipts = []
            for merchant, amount, nonce in (
                ("Taller Prisma", "17.43", "FFFFFFFF"),
                ("Estudio Nube", "38.61", "0000000A"),
            ):
                opening = (
                    f"No hice la compra de {merchant} por {amount} USD."
                    if language == "es"
                    else f"Não fiz a compra de {merchant} por {amount} USD."
                )
                proposal, conversation = await message(client, headers, opening, conversation)
                assert proposal["response_type"] == "confirm_action"
                # Only fixture entropy changes; policy, authorization and writes are real code.
                with monkeypatch.context() as entropy:
                    entropy.setattr(
                        "aclara.api.app.secrets.token_hex",
                        lambda _size, fixture_nonce=nonce: fixture_nonce,
                    )
                    created = await client.post(
                        f"/chat/sessions/{conversation}/confirm",
                        headers=headers,
                        json={
                            "proposal_hash": proposal["proposal"]["proposal_hash"],
                            "confirmed": True,
                        },
                    )
                assert created.status_code == 200
                result = created.json()
                assert result["verified"] is True
                record = await client.get("/disputes/" + result["case"]["case_id"], headers=headers)
                assert DisputeCaseView.model_validate(
                    record.json()
                ) == DisputeCaseView.model_validate(result["case"])
                receipts.append(result["case"])
            assert receipts[0]["case_id"] > receipts[1]["case_id"]
            generic = "¿Cómo va mi caso?" if language == "es" else "Qual o status do meu caso?"
            status, _ = await message(client, headers, generic, conversation)
            assert status["verified"] is True
            assert status["case"] == receipts[1]
            explicit = (
                f"¿Cuál es el estado del caso {receipts[0]['case_id']}?"
                if language == "es"
                else f"Qual o status do caso {receipts[0]['case_id']}?"
            )
            status, _ = await message(client, headers, explicit, conversation)
            assert status["verified"] is True
            assert status["case"] == receipts[0]
            assert len(app.state.cases) == 2

    asyncio.run(check())
