"""Local browser-test API using only the repository's generated fixture ledger."""

import os

import uvicorn

from aclara.api.app import create_app
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
    uvicorn.run(app, host="127.0.0.1", port=8212, access_log=False, log_level="warning")
