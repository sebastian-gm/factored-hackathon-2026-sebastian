"""Independent policy/context/packet dev reproductions; no frozen-suite inputs."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.handoff.routing import AgentDirectory, ServiceAgent


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize(
    "status,text,rule",
    [
        ("Pending", "Taller Prisma aparece pendiente; ¿qué significa?", "TXN-01"),
        ("Reversed", "Taller Prisma figura reversado; necesito una explicación", "TXN-03"),
        ("Declined", "Taller Prisma figura rechazado; ¿salió dinero?", "TXN-04"),
        ("Pending", "Taller Prisma aparece pendente; o que significa?", "TXN-01"),
        ("Reversed", "Taller Prisma aparece estornado; pode explicar?", "TXN-03"),
        ("Declined", "Taller Prisma aparece recusado; saiu dinheiro?", "TXN-04"),
    ],
)
def test_scoped_status_context_is_an_inquiry(system, status, text, rule):
    async def check():
        repo = ledger()
        repo._rows = (replace(repo._rows[0], transaction_status=status),)
        app = create_app(_settings(), repo, runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, _ = await message(client, headers, text)
            assert result["response_type"] == "explain_status"
            assert result["policy_rules"] == [rule]
            assert result["transaction"]["status"] == status
            if any(t in text for t in ["pendente", "estornado", "recusado"]):
                assert "cobrança" in result["reply"]
            assert not app.state.cases

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
def test_currency_contradiction_requires_clarification(system):
    async def check():
        app = create_app(_settings(), ledger(), runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, _ = await message(
                client, headers, "No hice el cargo de Taller Prisma por 17.43 BRL"
            )
            assert result["response_type"] == "clarify"
            assert not app.state.cases

    asyncio.run(check())


def test_policy_packet_keeps_reasons_facts_auth_and_redacted_statement():
    async def check():
        repo = ledger()
        clock = _settings().bank_clock
        repo._rows = (
            replace(
                repo._rows[0],
                transaction_date=clock - timedelta(days=95),
                process_date=(clock - timedelta(hours=6, microseconds=1)).date()
                - timedelta(days=95),
            ),
        )
        app = create_app(_settings(), repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, conv = await message(
                client,
                headers,
                "No hice el cargo de Taller Prisma; escríbeme a demo@example.test",
            )
            packet = result["handoff"]
            assert packet["conversation_id"] == conv
            assert packet["reason_codes"] == ["DSP-01"]
            assert packet["customer"]["auth"]["amr"] == ["pwd", "otp"]
            assert packet["customer_statements"]
            assert packet["customer_statements"][0]["verified"] is False
            assert "demo@example.test" not in str(packet)
            assert packet["verified_facts"][0]["handle"] == "txn_1"
            assert packet["suggested_next_steps"] and packet["open_questions"]
            assert packet["trace_ref"] and packet["transcript_ref"] and packet["sla_due_at"]
            read = (await client.get("/handoffs/" + packet["handoff_id"], headers=headers)).json()
            assert read["customer_statements"] == packet["customer_statements"]
            assert read["conversation_id"] == conv and result["verified"]

    asyncio.run(check())


def test_pt_preference_survives_spanish_routing_fallback():
    async def check():
        app = create_app(_settings(), ledger())
        # An authored roster forces the documented Spanish-language fallback.
        app.state.agent_directory = AgentDirectory(
            (ServiceAgent("authored-es", "Active", "Digital", "español", "Fraudes", 1),)
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, _ = await message(client, headers, "Roubaram meu cartão de débito")
            assert result["handoff"]["route"]["language"] == "es"
            assert result["handoff"]["customer"]["preferred_language"] == "pt"
            assert result["handoff"]["risk_flags"] == ["fraud_review"]

    asyncio.run(check())


def test_existing_case_readback_uses_current_persisted_status():
    from aclara.ops.store import Scope

    async def check():
        app = create_app(_settings(), ledger())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            proposal, conv = await message(client, headers, "No hice el cargo de Taller Prisma")
            filed = (
                await client.post(
                    f"/chat/sessions/{conv}/confirm",
                    headers=headers,
                    json={
                        "proposal_hash": proposal["proposal"]["proposal_hash"],
                        "confirmed": True,
                    },
                )
            ).json()
            principal = app.state.sessions[token]
            case_id = filed["case"]["case_id"]
            with app.state.store.transaction(
                Scope(principal.customer_id, principal.run_id, principal.session_id)
            ):
                app.state.cases[case_id]["status"] = "under_review"
            result, _ = await message(client, headers, "¿Cómo sigue el caso " + case_id + "?")
            assert result["outcome"] == "status_reported" and result["verified"]
            assert result["case"]["status"] == "under_review"
            assert len(app.state.cases) == 1

    asyncio.run(check())


def test_taxonomy_does_not_count_unrequired_packet_fields():
    from evals.failure_taxonomy import reduce_cases

    sample = {
        "unsafe": {"unauthorized_action": False},
        "passed": True,
        "gold": {
            "must_escalate": False,
            "required_handoff_fields": [],
            "outcome": "abstained_out_of_scope",
            "reason_codes": ["SCOPE-01"],
            "required_actions": [],
            "forbidden_actions": [],
        },
        "handoff": True,
        "completeness": None,
        "outcome": "abstained_out_of_scope",
        "missing_actions": [],
        "routing_correct": None,
        "category": "ambiguous_unsupported",
        "language": "es",
        "responses": [],
    }
    assert reduce_cases([sample])["incomplete_handoff"]["n"] == 0
