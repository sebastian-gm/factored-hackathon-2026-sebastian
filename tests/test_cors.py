"""Verify the browser origin used by the local demo can call the API."""

from __future__ import annotations

import asyncio

from httpx import ASGITransport, AsyncClient

from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.settings import Settings


def test_local_web_origin_can_call_api() -> None:
    async def check_preflight() -> None:
        app = create_app(
            Settings(),
            TransactionRepository(rows=()),
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://api.test"
        ) as client:
            response = await client.options(
                "/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "authorization,content-type",
                },
            )
            denied = await client.options(
                "/auth/login",
                headers={
                    "Origin": "https://untrusted.example",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "authorization,content-type",
                },
            )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert denied.status_code == 400
        assert "access-control-allow-origin" not in denied.headers

    asyncio.run(check_preflight())
