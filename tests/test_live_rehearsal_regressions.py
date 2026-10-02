"""Authored serving-shaped regressions for the live rehearsal, with no bank rows."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.runtime import Runtime
from aclara.api.app import _explanation, create_app
from aclara.bank.repository import TransactionRepository
from aclara.ops.store import Scope, Store


@pytest.mark.parametrize("language,expected", [("es", "aprobado"), ("pt", "aprovada")])
def test_approved_explanation_localizes_the_serving_status(language, expected):
    row = ledger()._rows[0]
    text = _explanation(language, row, "inquiry")
    assert expected in text
    assert "approved" not in text.casefold()


@pytest.mark.parametrize("backend", ["memory", "postgres"])
def test_packet_contains_only_identified_conversation_facts_and_completed_actions(backend):
    dsn = os.getenv("TEST_OPS_DSN")
    if backend == "postgres" and not dsn:
        pytest.skip("Disposable non-owner Postgres required")

    async def check():
        store = Store(dsn if backend == "postgres" else None)
        settings = replace(
            _settings(), demo_role="ops", demo_customer_id="fixture-packet-" + uuid4().hex
        )
        repo = ledger(two=True)
        repo = TransactionRepository(
            tuple(replace(row, customer_id=settings.demo_customer_id) for row in repo._rows)
        )
        # Serving data can contain blank merchants; their existence does not
        # authorize treating them as a selected movement in a generic handoff.
        repo._rows = (repo._rows[0], replace(repo._rows[1], merchant_name=""))
        app = create_app(settings, repo, store=store, runtime=Runtime(system="P"))
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
                proposed, selected = await message(
                    client, headers, "No hice el cargo de Taller Prisma por 17.43 USD"
                )
                assert proposed["outcome"] == "dispute_proposed"
                # Another tab must not receive the selected tab's facts or proposal.
                bare, unrelated = await message(client, headers, "Quiero hablar con una persona")
                assert unrelated != selected
                assert bare["handoff"]["verified_facts"] == []
                assert bare["handoff"]["actions_taken"] == ["create_handoff"]
                referred, _ = await message(
                    client, headers, "Quiero hablar con una persona", selected
                )
                packet = referred["handoff"]
                assert [x["handle"] for x in packet["verified_facts"]] == [
                    proposed["transaction"]["handle"]
                ]
                assert packet["actions_taken"] == ["create_handoff"]  # No confirmation, no write.
                assert packet["conversation_id"] == selected
                assert referred["verified"] is True
                public = (
                    await client.get("/handoffs/" + packet["handoff_id"], headers=headers)
                ).json()
                assert public["actions_taken"] == packet["actions_taken"]
                detail = (
                    await client.get("/agent/handoffs/" + packet["handoff_id"], headers=headers)
                ).json()
                assert detail["actions"] == [
                    {
                        "action": "create_handoff",
                        "status": "verified",
                        "evidence_ref": packet["trace_ref"],
                    }
                ]
                assert len(detail["evidence"]) == 1
                assert "customer_id" not in str(detail) and "fraud_score" not in str(detail)
                # PostgreSQL persists the selected handle and packet. Restore the
                # app and verify the same session/packet, not an in-memory fixture.
                if backend == "postgres":
                    store.close()
                    store = Store(dsn)
                    app = create_app(settings, repo, store=store)
                    async with AsyncClient(
                        transport=ASGITransport(app=app), base_url="http://test"
                    ) as restored:
                        assert (
                            await restored.get(
                                "/agent/handoffs/" + packet["handoff_id"], headers=headers
                            )
                        ).json() == detail
        finally:
            store.close()

    asyncio.run(check())


def test_packet_reports_previous_verified_dispute_but_no_unselected_fraud_transaction():
    async def check():
        app = create_app(replace(_settings(), demo_role="ops"), ledger())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            proposal, cid = await message(client, headers, "No hice el cargo de Taller Prisma")
            filed = (
                await client.post(
                    f"/chat/sessions/{cid}/confirm",
                    headers=headers,
                    json={
                        "proposal_hash": proposal["proposal"]["proposal_hash"],
                        "confirmed": True,
                    },
                )
            ).json()
            assert filed["verified"] is True
            referred, _ = await message(client, headers, "Perdí mi tarjeta y necesito ayuda", cid)
            assert referred["handoff"]["actions_taken"] == ["create_dispute", "create_handoff"]
            assert len(referred["handoff"]["verified_facts"]) == 1
            detail = (
                await client.get(
                    "/agent/handoffs/" + referred["handoff"]["handoff_id"], headers=headers
                )
            ).json()
            assert [a["action"] for a in detail["actions"]] == ["create_dispute", "create_handoff"]
            bare, _ = await message(client, headers, "Perdí mi tarjeta y necesito ayuda")
            assert bare["handoff"]["verified_facts"] == []
            assert bare["handoff"]["actions_taken"] == ["create_handoff"]
            assert "FRD-01" in bare["handoff"]["reason_codes"]

    asyncio.run(check())


def test_missing_committed_handoff_is_never_reported_as_a_verified_action():
    class LostPacketStore(Store):
        lost = False

        @contextmanager
        def transaction(self, scope: Scope) -> Iterator[None]:
            nested = self.current.get() is not None
            with super().transaction(scope):
                yield
            if not nested and not self.lost:
                for key in list(self.memory):
                    if key[0] == scope and key[1] == "handoffs":
                        del self.memory[key]
                        self.lost = True

    async def check():
        store = LostPacketStore()
        app = create_app(_settings(), ledger(), store=store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            cid = (await client.post("/chat/sessions", headers=headers)).json()["conversation_id"]
            response = await client.post(
                f"/chat/sessions/{cid}/messages",
                headers=headers,
                json={"message": "Quiero hablar con una persona"},
            )
            assert store.lost and response.status_code == 503
            principal = app.state.sessions[token]
            with store.transaction(
                Scope(principal.customer_id, principal.run_id, principal.session_id)
            ):
                assert not any(
                    r.get("outcome") == "handoff_verified" for r in app.state.executions.values()
                )
                assert all(
                    "create_handoff"
                    not in r.get("response", {}).get("handoff", {}).get("actions_taken", [])
                    for r in app.state.executions.values()
                )

    asyncio.run(check())
