"""Local browser-test API using only the repository's generated fixture ledger."""

import hmac
import os

import uvicorn
from fastapi import Header, HTTPException

from aclara.api.app import create_app
from aclara.ops.store import Scope
from aclara.settings import Settings

if __name__ == "__main__":
    app = create_app(
        settings=Settings(
            demo_username="demo.es.mx",
            demo_role="ops" if os.environ.get("FRONTEND_E2E_STAFF") == "1" else "customer",
            allow_demo_reset=os.environ.get("FRONTEND_E2E_STAFF") == "1",
            demo_password=os.environ["FRONTEND_FIXTURE_PASSWORD"],
            llm_provider="mock",
            agent_system="B1",
        )
    )

    @app.post("/_fixture/reset-bank-state")
    async def reset_bank_state(x_fixture_secret: str = Header(default="")) -> dict[str, bool]:
        # Test server only: never installed on the product API. Each test gets
        # fresh authored bank state; logins inside a test still share that state.
        if not hmac.compare_digest(x_fixture_secret, os.environ["FRONTEND_FIXTURE_PASSWORD"]):
            raise HTTPException(403, "Fixture reset denied")
        with app.state.store.transaction(
            Scope(app.state.settings.demo_customer_id, "fixture_reset", "fixture_reset")
        ):
            app.state.cases.clear()
            app.state.card_states.clear()
        return {"reset": True}

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("FRONTEND_E2E_API_PORT", "8212")),
        access_log=False,
        log_level="warning",
    )
