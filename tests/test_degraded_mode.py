"""Health behavior and controlled dependency-failure checks."""

from __future__ import annotations

import asyncio
import secrets

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient

import aclara.api.app as api_module
from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.settings import Settings


def test_database_failure_marks_unready_but_keeps_liveness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def check() -> None:
        app = create_app(Settings())

        def fail_connect(**_: object) -> None:
            raise psycopg.OperationalError("injected connection failure")

        monkeypatch.setattr(api_module.psycopg, "connect", fail_connect)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://api.test"
        ) as client:
            liveness = await client.get("/healthz")
            readiness = await client.get("/readyz")
            assert liveness.status_code == 200
            assert readiness.status_code == 503

            class HealthyConnection:
                def __enter__(self) -> HealthyConnection:
                    return self

                def __exit__(self, *_: object) -> None:
                    return None

                def execute(self, _query: str) -> None:
                    return None

            monkeypatch.setattr(
                api_module.psycopg,
                "connect",
                lambda **_: HealthyConnection(),
            )
            recovered = await client.get("/readyz")

        assert liveness.json()["status"] == "ok"
        assert readiness.json() == {"detail": "Database unavailable"}
        assert recovered.status_code == 200
        assert recovered.json() == {"status": "ready", "database": "ok"}

    asyncio.run(check())


def test_fixture_read_failure_returns_generic_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def check() -> None:
        password = secrets.token_urlsafe(16)
        settings = Settings(demo_username="test-user", demo_password=password)
        ledger = TransactionRepository()

        def fail_read(*_: object, **__: object) -> list[tuple[str, object]]:
            raise OSError("injected fixture read failure")

        monkeypatch.setattr(ledger, "for_customer", fail_read)
        app = create_app(settings, ledger)
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://api.test",
        ) as client:
            login = await client.post(
                "/auth/login", json={"username": "test-user", "password": password}
            )
            challenge = login.json()
            sms = await client.get(
                f"/auth/challenges/{challenge['challenge_id']}/sms",
                headers={"X-Preauth-Token": challenge["preauth_token"]},
            )
            verified = await client.post(
                "/auth/otp/verify",
                headers={"X-Preauth-Token": challenge["preauth_token"]},
                json={"challenge_id": challenge["challenge_id"], "code": sms.json()["code"]},
            )
            response = await client.get(
                "/transactions",
                headers={"Authorization": f"Bearer {verified.json()['access_token']}"},
            )

        assert login.status_code == sms.status_code == verified.status_code == 200
        assert response.status_code == 500
        assert response.text == "Internal Server Error"
        assert "injected fixture read failure" not in response.text
