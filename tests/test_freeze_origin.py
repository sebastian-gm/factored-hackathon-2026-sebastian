"""Authored freeze provenance regressions; no suite or organizer records."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_workflow_api import message, step_up

from aclara.api.app import create_app
from aclara.bank.repository import Product, TransactionRepository
from aclara.ops.store import Scope


@pytest.mark.parametrize("confirmed", [True, False])
def test_freeze_keeps_origin_reasons_and_conversation_despite_later_fraud(confirmed):
    async def check():
        app = create_app(_settings())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            first, conversation = await message(
                client, headers, "Me robaron la tarjeta. Voy a reclamar al regulador."
            )
            origin = first["handoff"]["handoff_id"]
            await step_up(client, headers)
            p = await client.post(
                "/cards/prod_1/freeze/proposal", headers=headers, json={"handoff_id": origin}
            )
            assert p.status_code == 200
            proposal = p.json()
            assert proposal["handoff_id"] == origin and proposal["conversation_id"] == conversation
            second, other_conversation = await message(client, headers, "Me robaron la tarjeta")
            assert (
                other_conversation != conversation
                and "ESC-02" not in second["handoff"]["reason_codes"]
            )
            response = await client.post(
                "/cards/prod_1/freeze",
                headers=headers,
                json={"proposal_hash": proposal["proposal_hash"], "confirmed": confirmed},
            )
            assert response.status_code == 200
            result = response.json()
            assert result["handoff"]["reason_codes"] == first["handoff"]["reason_codes"]
            assert result["handoff"]["conversation_id"] == conversation
            assert result["handoff"]["freeze_outcome"] == ("verified" if confirmed else "declined")
            assert (await client.get("/cards/prod_1", headers=headers)).json()["status"] == (
                "Frozen" if confirmed else "Active"
            )
            packet = (
                await client.get("/handoffs/" + result["handoff"]["handoff_id"], headers=headers)
            ).json()
            assert packet["reason_codes"] == first["handoff"]["reason_codes"]
            original = (await client.get("/handoffs/" + origin, headers=headers)).json()
            assert original["reason_codes"] == first["handoff"]["reason_codes"]

    asyncio.run(check())


def test_freeze_origin_is_required_owned_fraud_offer_and_immutable():
    async def check():
        app = create_app(_settings())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            first, _ = await message(
                client, headers, "Me robaron la tarjeta. Voy a reclamar al regulador."
            )
            other, _ = await message(client, headers, "Quiero hablar con una persona")
            await step_up(client, headers)
            assert (
                await client.post("/cards/prod_1/freeze/proposal", headers=headers, json={})
            ).status_code == 422
            assert (
                await client.post(
                    "/cards/prod_1/freeze/proposal",
                    headers=headers,
                    json={"handoff_id": other["handoff"]["handoff_id"]},
                )
            ).status_code == 404
            another = {"Authorization": f"Bearer {await _sign_in(client)}"}
            await step_up(client, another)
            assert (
                await client.post(
                    "/cards/prod_1/freeze/proposal",
                    headers=another,
                    json={"handoff_id": first["handoff"]["handoff_id"]},
                )
            ).status_code == 404
            p = (
                await client.post(
                    "/cards/prod_1/freeze/proposal",
                    headers=headers,
                    json={"handoff_id": first["handoff"]["handoff_id"]},
                )
            ).json()
            principal = app.state.sessions[token]
            with app.state.store.transaction(
                Scope(principal.customer_id, principal.run_id, principal.session_id)
            ):
                value = app.state.idempotency["freeze-proposal:" + p["proposal_hash"]]
                value["handoff_id"] = other["handoff"]["handoff_id"]
                app.state.idempotency["freeze-proposal:" + p["proposal_hash"]] = value
            assert (
                await client.post(
                    "/cards/prod_1/freeze",
                    headers=headers,
                    json={"proposal_hash": p["proposal_hash"], "confirmed": True},
                )
            ).status_code == 409
            assert (await client.get("/cards/prod_1", headers=headers)).json()["status"] == "Active"

    asyncio.run(check())


def test_origin_cannot_authorize_an_owned_card_it_did_not_offer():
    async def check():
        row = replace(
            TransactionRepository()._rows[0],
            merchant_name="Origen Ensayo",
            transaction_type="Purchase",
            transaction_status="Approved",
            amount=80,
            currency="USD",
        )
        ledger = TransactionRepository(
            (row,),
            policy_fields={row.record_id: {"fraud_score": 31, "amount_usd": 80}},
            products=(
                Product(row.product_id, row.customer_id, "Credit Card"),
                Product("authored-other-card", row.customer_id, "Debit Card"),
            ),
        )
        app = create_app(_settings(), ledger)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            offer, _ = await message(client, headers, "No hice el cargo de Origen Ensayo")
            assert len(offer["freeze_offer"]) == 1
            offered = offer["freeze_offer"][0]["handle"]
            others = [
                p["handle"]
                for p in (await client.get("/accounts", headers=headers)).json()
                if p["handle"] != offered
            ]
            assert others
            await step_up(client, headers)
            response = await client.post(
                f"/cards/{others[0]}/freeze/proposal",
                headers=headers,
                json={"handoff_id": offer["handoff"]["handoff_id"]},
            )
            assert response.status_code == 404

    asyncio.run(check())


def test_renewed_otp_requires_a_new_freeze_proposal_with_same_origin():
    async def check():
        app = create_app(_settings())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            offer, conversation = await message(
                client, headers, "Me robaron la tarjeta. Voy a reclamar al regulador."
            )
            origin = {"handoff_id": offer["handoff"]["handoff_id"]}
            await step_up(client, headers)
            old = (
                await client.post("/cards/prod_1/freeze/proposal", headers=headers, json=origin)
            ).json()
            app.state.sessions[token] = replace(
                app.state.sessions[token], step_up_at=datetime.now(UTC) - timedelta(minutes=11)
            )
            confirm = {"proposal_hash": old["proposal_hash"], "confirmed": True}
            r = await client.post("/cards/prod_1/freeze", headers=headers, json=confirm)
            assert r.status_code == 401 and r.json()["detail"] == "Step-up verification required"
            await step_up(client, headers)
            assert (
                await client.post("/cards/prod_1/freeze", headers=headers, json=confirm)
            ).status_code == 401
            fresh = (
                await client.post("/cards/prod_1/freeze/proposal", headers=headers, json=origin)
            ).json()
            assert fresh["proposal_hash"] != old["proposal_hash"]
            assert (
                fresh["handoff_id"] == origin["handoff_id"]
                and fresh["conversation_id"] == conversation
            )
            result = (
                await client.post(
                    "/cards/prod_1/freeze",
                    headers=headers,
                    json={"proposal_hash": fresh["proposal_hash"], "confirmed": False},
                )
            ).json()
            assert result["handoff"]["reason_codes"] == offer["handoff"]["reason_codes"]
            assert result["handoff"]["freeze_outcome"] == "declined"
            assert (await client.get("/cards/prod_1", headers=headers)).json()["status"] == "Active"

    asyncio.run(check())
