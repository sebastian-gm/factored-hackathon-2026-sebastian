"""Security boundaries for the local synthetic demo API."""

from __future__ import annotations

import asyncio
import secrets
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

from httpx import ASGITransport, AsyncClient

from aclara.api.app import create_app
from aclara.bank.repository import Transaction, TransactionRepository
from aclara.settings import Settings

TEST_USERNAME = "test-user"
TEST_PASSWORD = secrets.token_urlsafe(16)


def _settings() -> Settings:
    return Settings(demo_username=TEST_USERNAME, demo_password=TEST_PASSWORD)


async def _sign_in(client: AsyncClient) -> str:
    login = await client.post(
        "/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    assert login.status_code == 200
    challenge = login.json()
    sms = await client.get(
        f"/auth/challenges/{challenge['challenge_id']}/sms",
        headers={"X-Preauth-Token": challenge["preauth_token"]},
    )
    assert sms.status_code == 200
    verified = await client.post(
        "/auth/otp/verify",
        headers={"X-Preauth-Token": challenge["preauth_token"]},
        json={"challenge_id": challenge["challenge_id"], "code": sms.json()["code"]},
    )
    assert verified.status_code == 200
    return str(verified.json()["access_token"])


def test_protected_routes_require_a_live_bearer_session() -> None:
    async def check() -> None:
        app = create_app(_settings())
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://api.test"
        ) as client:
            requests = [
                await client.get("/me"),
                await client.get("/transactions"),
                await client.post("/chat/sessions"),
                await client.post("/chat/sessions/missing/messages", json={"message": "hola"}),
                await client.post(
                    "/chat/sessions/missing/confirm",
                    json={"proposal_hash": "0" * 64, "confirmed": True},
                ),
                await client.get("/disputes/DSP-missing"),
                await client.get("/handoffs/HO-missing"),
            ]
            bad_scheme = await client.get("/me", headers={"Authorization": "Basic token"})
            unknown_token = await client.get(
                "/me", headers={"Authorization": "Bearer not-a-session"}
            )
            token = await _sign_in(client)
            app.state.sessions[token] = replace(
                app.state.sessions[token],
                expires_at=datetime.now(UTC) - timedelta(seconds=1),
            )
            expired_token = await client.get("/me", headers={"Authorization": f"Bearer {token}"})

        assert [response.status_code for response in requests] == [401] * len(requests)
        assert (
            bad_scheme.status_code == unknown_token.status_code == expired_token.status_code == 401
        )
        assert token not in app.state.sessions

    asyncio.run(check())


def test_otp_is_bound_to_preauth_and_limited_to_five_attempts() -> None:
    async def check() -> None:
        app = create_app(_settings())
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://api.test"
        ) as client:
            login = await client.post(
                "/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
            )
            challenge = login.json()
            path = f"/auth/challenges/{challenge['challenge_id']}/sms"
            no_preauth = await client.get(path)
            wrong_preauth = await client.get(path, headers={"X-Preauth-Token": "wrong"})
            sms = await client.get(path, headers={"X-Preauth-Token": challenge["preauth_token"]})
            correct_code = sms.json()["code"]
            wrong_code = "000000" if correct_code != "000000" else "000001"
            wrong_attempts = [
                await client.post(
                    "/auth/otp/verify",
                    headers={"X-Preauth-Token": challenge["preauth_token"]},
                    json={"challenge_id": challenge["challenge_id"], "code": wrong_code},
                )
                for _ in range(5)
            ]
            correct_after_limit = await client.post(
                "/auth/otp/verify",
                headers={"X-Preauth-Token": challenge["preauth_token"]},
                json={"challenge_id": challenge["challenge_id"], "code": correct_code},
            )

            second_login = await client.post(
                "/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
            )
            second = second_login.json()
            second_sms = await client.get(
                f"/auth/challenges/{second['challenge_id']}/sms",
                headers={"X-Preauth-Token": second["preauth_token"]},
            )
            valid = await client.post(
                "/auth/otp/verify",
                headers={"X-Preauth-Token": second["preauth_token"]},
                json={"challenge_id": second["challenge_id"], "code": second_sms.json()["code"]},
            )
            replay = await client.post(
                "/auth/otp/verify",
                headers={"X-Preauth-Token": second["preauth_token"]},
                json={"challenge_id": second["challenge_id"], "code": second_sms.json()["code"]},
            )

        assert no_preauth.status_code == wrong_preauth.status_code == 404
        assert [response.status_code for response in wrong_attempts] == [401] * 5
        assert correct_after_limit.status_code == 401
        assert valid.status_code == 200
        assert replay.status_code == 401

    asyncio.run(check())


def test_transactions_are_customer_scoped_and_mask_internal_identifiers() -> None:
    async def check() -> None:
        own = Transaction(
            record_id="internal-record-own",
            customer_id="demo-customer-01",
            product_id="internal-product-own",
            transaction_date=datetime(2026, 6, 17, 9, 0, tzinfo=UTC),
            process_date=date(2026, 6, 17),
            transaction_type="Purchase",
            amount=24.5,
            currency="USD",
            merchant_name="Fixture Merchant",
            transaction_status="Approved",
        )
        other = Transaction(
            record_id="internal-record-other",
            customer_id="other-customer",
            product_id="internal-product-other",
            transaction_date=datetime(2026, 6, 16, 9, 0, tzinfo=UTC),
            process_date=date(2026, 6, 16),
            transaction_type="Purchase",
            amount=999.0,
            currency="USD",
            merchant_name="Other Customer Merchant",
            transaction_status="Approved",
        )
        app = create_app(_settings(), TransactionRepository(rows=(own, other)))
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://api.test"
        ) as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/transactions", headers=headers)
            attempted_override = await client.get(
                "/transactions", headers=headers, params={"customer_id": "other-customer"}
            )

        assert response.status_code == attempted_override.status_code == 200
        for result in (response, attempted_override):
            rows = result.json()
            assert len(rows) == 1
            assert rows[0]["merchant"] == "Fixture Merchant"
            assert set(rows[0]) == {
                "handle",
                "transaction_date",
                "transaction_type",
                "amount",
                "currency",
                "merchant",
                "status",
            }
            assert "Other Customer Merchant" not in result.text
            assert "internal-record" not in result.text
            assert "internal-product" not in result.text
            assert "customer_id" not in result.text

    asyncio.run(check())


def test_action_proposal_is_session_bound_and_single_use() -> None:
    async def check() -> None:
        app = create_app(_settings())
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://api.test"
        ) as client:
            owner = await _sign_in(client)
            other_session = await _sign_in(client)
            owner_headers = {"Authorization": f"Bearer {owner}"}
            other_headers = {"Authorization": f"Bearer {other_session}"}
            conversation = await client.post("/chat/sessions", headers=owner_headers)
            conversation_id = conversation.json()["conversation_id"]
            proposal = await client.post(
                f"/chat/sessions/{conversation_id}/messages",
                headers=owner_headers,
                json={"message": "No reconozco el cargo de Mercado Verde"},
            )
            proposal_hash = proposal.json()["proposal"]["proposal_hash"]
            unauthorized = await client.post(
                f"/chat/sessions/{conversation_id}/confirm",
                headers=other_headers,
                json={"proposal_hash": proposal_hash, "confirmed": True},
            )
            assert unauthorized.status_code == 404
            assert not app.state.cases

            confirmation = await client.post(
                f"/chat/sessions/{conversation_id}/confirm",
                headers=owner_headers,
                json={"proposal_hash": proposal_hash, "confirmed": True},
            )
            replay = await client.post(
                f"/chat/sessions/{conversation_id}/confirm",
                headers=owner_headers,
                json={"proposal_hash": proposal_hash, "confirmed": True},
            )
            case_id = confirmation.json()["case"]["case_id"]
            readback = await client.get(f"/disputes/{case_id}", headers=owner_headers)

        assert proposal.status_code == 200
        assert proposal.json()["outcome"] == "dispute_proposed"
        assert confirmation.status_code == 200
        assert confirmation.json()["verified"] is True
        assert "customer_id" not in confirmation.text
        assert "transaction_id" not in confirmation.text
        assert replay.status_code == 409
        assert readback.status_code == 200
        assert readback.json()["status"] == "received"
        assert len(app.state.cases) == 1

    asyncio.run(check())


def test_tampered_or_expired_proposals_fail_closed() -> None:
    async def check() -> None:
        app = create_app(_settings())
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://api.test"
        ) as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            tampered_conversation = await client.post("/chat/sessions", headers=headers)
            tampered_id = tampered_conversation.json()["conversation_id"]
            tampered_proposal = await client.post(
                f"/chat/sessions/{tampered_id}/messages",
                headers=headers,
                json={"message": "No reconozco el cargo de Mercado Verde"},
            )
            changed_hash = await client.post(
                f"/chat/sessions/{tampered_id}/confirm",
                headers=headers,
                json={"proposal_hash": "0" * 64, "confirmed": True},
            )

            expired_conversation = await client.post("/chat/sessions", headers=headers)
            expired_id = expired_conversation.json()["conversation_id"]
            expired_proposal = await client.post(
                f"/chat/sessions/{expired_id}/messages",
                headers=headers,
                json={"message": "No reconozco el cargo de Mercado Verde"},
            )
            app.state.conversations[expired_id].proposal.expires_at = datetime.now(UTC) - timedelta(
                seconds=1
            )
            expired = await client.post(
                f"/chat/sessions/{expired_id}/confirm",
                headers=headers,
                json={
                    "proposal_hash": expired_proposal.json()["proposal"]["proposal_hash"],
                    "confirmed": True,
                },
            )

        assert tampered_proposal.status_code == expired_proposal.status_code == 200
        assert changed_hash.status_code == expired.status_code == 409
        assert not app.state.cases

    asyncio.run(check())


def test_confirmation_requires_recent_step_up_authentication() -> None:
    async def check() -> None:
        app = create_app(_settings())
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://api.test"
        ) as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            conversation = await client.post("/chat/sessions", headers=headers)
            conversation_id = conversation.json()["conversation_id"]
            proposal = await client.post(
                f"/chat/sessions/{conversation_id}/messages",
                headers=headers,
                json={"message": "No reconozco el cargo de Mercado Verde"},
            )
            principal = app.state.sessions[token]
            app.state.sessions[token] = replace(
                principal, otp_at=datetime.now(UTC) - timedelta(minutes=11)
            )
            confirmation = await client.post(
                f"/chat/sessions/{conversation_id}/confirm",
                headers=headers,
                json={
                    "proposal_hash": proposal.json()["proposal"]["proposal_hash"],
                    "confirmed": True,
                },
            )

        assert proposal.status_code == 200
        assert confirmation.status_code == 401
        assert not app.state.cases


def test_request_models_reject_extra_fields_bad_otp_and_oversized_messages() -> None:
    async def check() -> None:
        app = create_app(_settings())
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://api.test"
        ) as client:
            extra_login_field = await client.post(
                "/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD, "role": "admin"},
            )
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            oversized = await client.post(
                "/chat/sessions/unknown/messages",
                headers=headers,
                json={"message": "a" * 1001},
            )
            malformed_otp = await client.post(
                "/auth/otp/verify",
                headers={"X-Preauth-Token": "not-a-token"},
                json={"challenge_id": "missing", "code": "12345"},
            )

        assert (
            extra_login_field.status_code
            == oversized.status_code
            == malformed_otp.status_code
            == 422
        )

    asyncio.run(check())
