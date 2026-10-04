"""Local browser-test API using only the repository's generated fixture ledger."""

import hmac
import json
import os
from dataclasses import replace
from datetime import UTC, datetime

import uvicorn
from fastapi import Header, HTTPException

from aclara.api.app import create_app
from aclara.api.judge_access import PROFILE_LOCALES
from aclara.bank.repository import Customer, TransactionRepository
from aclara.bank.serving import Persona
from aclara.handoff.routing import AgentDirectory
from aclara.ops.store import Scope
from aclara.settings import Settings


class AuthoredJudgeLedger(TransactionRepository):
    """Four invented customers; real identity/queue actions, no serving DB."""

    def __init__(self) -> None:
        original = TransactionRepository()._rows[0]
        rows = tuple(
            replace(
                original,
                record_id="browser-judge-" + key,
                customer_id="browser-customer-" + key,
                product_id="browser-product-" + key,
                merchant_name="Fixture " + key,
                transaction_type="Purchase",
                transaction_status="Approved",
                amount=20,
                currency="USD",
                transaction_date=datetime(2026, 6, 15, 12, tzinfo=UTC),
            )
            for key in PROFILE_LOCALES
        )
        super().__init__(rows, customers=tuple(Customer(row.customer_id) for row in rows))

    def personas(self) -> list[Persona]:
        return [
            Persona(
                "authored." + key,
                "browser-customer-" + key,
                locale,
                "ops" if key == "mx-es" else "customer",
            )
            for key, locale in PROFILE_LOCALES.items()
        ]

    def directory(self) -> AgentDirectory:
        return AgentDirectory()

    def ready(self) -> bool:
        return True


if __name__ == "__main__":
    judge_staff = os.environ.get("FRONTEND_E2E_JUDGE_STAFF") == "1"
    repository = None
    if judge_staff:
        # The unit-test authored serving boundary pattern: no real DB or rows.
        # Install only in this disposable test process, never in product code.
        import aclara.api.app as api_module

        api_module.ServingRepository = AuthoredJudgeLedger  # type: ignore[misc]
        repository = AuthoredJudgeLedger()
        os.environ.pop("LLM_BUDGET_RUN_ID", None)
    app = create_app(
        settings=Settings(
            demo_username="demo.es.mx",
            demo_role="ops" if os.environ.get("FRONTEND_E2E_STAFF") == "1" else "customer",
            allow_demo_reset=os.environ.get("FRONTEND_E2E_STAFF") == "1",
            demo_password=os.environ["FRONTEND_FIXTURE_PASSWORD"],
            llm_provider="mock",
            agent_system="B1",
            judge_access_enabled=judge_staff,
            judge_password=os.environ.get("FRONTEND_FIXTURE_JUDGE_PASSWORD", ""),
            judge_persona=json.dumps(
                {
                    "username": "judge.authored",
                    "profiles": {key: "authored." + key for key in PROFILE_LOCALES},
                }
            )
            if judge_staff
            else "",
        ),
        repository=repository,
    )

    if os.environ.get("FRONTEND_E2E_STAFF") == "1":
        # Test-only authored identities; independent customer/staff OTP sessions.
        for username, role in (("demo.customer", "customer"), ("demo.agent", "agent")):
            app.state.personas[username] = Persona(
                username, app.state.settings.demo_customer_id, "es-MX", role
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
