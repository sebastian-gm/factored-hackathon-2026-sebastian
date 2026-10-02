"""Post-v4 repairs, checked only on authored ES/PT data; no evaluation replay."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_bound_evaluation import authored, run
from test_dev_acceptance import ledger
from test_post_v3_fixes import _p_app
from test_workflow_api import message

from aclara.agent.runtime import Runtime
from aclara.agent.selection import uncertain
from aclara.api.app import create_app
from aclara.ops.store import Scope
from aclara.policy.rules.guards import escalations


@pytest.mark.parametrize(
    "text",
    [
        "Quiero hablar con una persoa",
        "quiero un ajente",
        "Kiero una persona",
        "Necesito hablar con una pesona",
        "Preciso falar com uma pessoa",
        "falar com atendente",
        "Quero falar com um atendete",
        "Una persona, por favor",
    ],
)
def test_positive_human_requests_with_bounded_typos(text):
    assert "ESC-01" in escalations(text)


@pytest.mark.parametrize(
    "text",
    [
        "No quiero hablar con una persona",
        "Não quero falar com atendente",
        "La persona que hizo la compra",
        "El agente del seguro cobró una prima",
        "Persona autorizada en la cuenta",
        "Quiero revisar el cargo de Persoa Café",
        "No necesito un agente; solo quiero el estado",
        "Não preciso de uma pessoa",
    ],
)
def test_mentions_negations_and_merchants_are_not_requests(text):
    assert "ESC-01" not in escalations(text)


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize(
    "text",
    [
        "Perdí mi tarjeta. Voy a CONDUSEF. Quiero hablar con una persoa.",
        "Perdi meu cartão. Vou ao Procon. Quero falar com um atendete.",
        "Voy a CONDUSEF y quiero un ajente.",
        "Vou ao Procon e quero falar com atendente.",
    ],
)
def test_early_handoff_preserves_concurrent_human_reason(system, text):
    async def check():
        app = create_app(_settings(), ledger(), runtime=Runtime(system=system))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {await _sign_in(client)}"}
            result, _ = await message(client, headers, text)
        packet = result["handoff"]
        assert {"ESC-01", "ESC-02"} <= set(packet["reason_codes"])
        if "tarjeta" in text or "cartão" in text:
            assert {"FRD-01", "AUTH-02"} <= set(packet["reason_codes"])
            assert packet["route"]["queue"] == "Fraudes"

    asyncio.run(check())


@pytest.mark.parametrize(
    "text",
    [
        "No estoy seguro de reconocer este cargo; no lo hice.",
        "Não tenho certeza de reconhecer essa compra; não fiz.",
        "No recuerdo haber autorizado este cargo.",
        "Não lembro de ter feito essa compra.",
    ],
)
def test_recognition_uncertainty_is_not_selection_uncertainty(text):
    assert not uncertain(text)


@pytest.mark.parametrize(
    "text",
    [
        "No estoy seguro de reconocer el cargo; no recuerdo el monto.",
        "Não tenho certeza de reconhecer a compra; não consigo escolher.",
        "No recuerdo haber autorizado nada y no sé cuál compra es.",
        "Não lembro de ter feito uma compra; não sei qual é.",
    ],
)
def test_real_identification_uncertainty_survives_recognition_clause(text):
    assert uncertain(text)


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize("language", ["es", "pt"])
def test_accepted_match_after_denial_survives_guard_and_still_needs_confirmation(
    monkeypatch, system, language
):
    async def check():
        from aclara.api import app as app_module

        matcher = SimpleNamespace(
            version="authored",
            match=lambda *args: SimpleNamespace(
                action="propose",
                transaction_ids=["txn_1"],
                top_correct_probability=0.99,
                match_exists_probability=0.99,
            ),
        )
        monkeypatch.setattr(app_module, "MatchState", lambda: matcher)
        app = (
            _p_app(
                {
                    "intent": "dispute_charge",
                    "intent_confidence": 0.99,
                    "language": language,
                    "merchant_expr": "Taller Prisma",
                    "amount_expr": "17.43",
                    "currency_expr": "USD",
                }
            )
            if system == "P"
            else create_app(_settings(), ledger(), runtime=Runtime(system="B1"))
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            first, conv = await message(
                client, headers, "No hice un cargo, no recuerdo el monto y no puedo elegir"
            )
            assert first["response_type"] == "clarify"
            text = (
                "No estoy seguro de reconocer el cargo de Taller Prisma por 17.43 USD; no lo hice, quiero disputarlo."
                if language == "es"
                else "Não tenho certeza de reconhecer a compra de Taller Prisma de 17.43 USD; não fiz, quero contestar."
            )
            proposal, _ = await message(client, headers, text, conv)
            assert proposal["response_type"] == "confirm_action"
            assert not app.state.cases
            if system == "P":
                assert any(
                    e.get("event") == "match" and e.get("action") == "propose"
                    for e in app.state.runtime.events
                )
            result = await client.post(
                f"/chat/sessions/{conv}/confirm",
                headers=headers,
                json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True},
            )
            assert result.status_code == 200 and result.json()["verified"]
            assert len(app.state.cases) == 1

    asyncio.run(check())


@pytest.mark.parametrize("lookup", ["Estado de mi caso", "No hice el cargo de Taller Prisma"])
def test_case_status_records_independent_verification_in_saved_execution(lookup):
    async def check():
        app = create_app(_settings(), ledger())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            proposed, conv = await message(client, headers, "No hice el cargo de Taller Prisma")
            await client.post(
                f"/chat/sessions/{conv}/confirm",
                headers=headers,
                json={
                    "proposal_hash": proposed["proposal"]["proposal_hash"],
                    "confirmed": True,
                },
            )
            cursor = len(app.state.runtime.events)
            reported, _ = await message(client, headers, lookup)
            assert reported["response_type"] == "report_status" and reported["verified"]
            reads = [
                e for e in app.state.runtime.events[cursor:] if e["event"] == "verify_readback"
            ]
            assert len(reads) == 1
            assert reads[0]["case_id"] == reported["case"]["case_id"]
            principal = app.state.sessions[token]
            with app.state.store.transaction(
                Scope(principal.customer_id, principal.run_id, principal.session_id)
            ):
                saved = [
                    r
                    for r in app.state.executions.values()
                    if r["response"]["response_type"] == "report_status"
                ]
                assert len(saved) == 1 and reads[0] in saved[0]["events"]

    asyncio.run(check())


def test_failed_independent_status_read_has_no_verification_event(monkeypatch):
    async def check():
        app = create_app(_settings(), ledger())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            proposed, conv = await message(client, headers, "No hice el cargo de Taller Prisma")
            await client.post(
                f"/chat/sessions/{conv}/confirm",
                headers=headers,
                json={
                    "proposal_hash": proposed["proposal"]["proposal_hash"],
                    "confirmed": True,
                },
            )
            original = app.state.store.get
            reads = 0

            def missing_on_independent_read(table, key):
                nonlocal reads
                if table == "customer_cases":
                    reads += 1
                    if reads == 2:
                        return None
                return original(table, key)

            monkeypatch.setattr(app.state.store, "get", missing_on_independent_read)
            cursor = len(app.state.runtime.events)
            session = (await client.post("/chat/sessions", headers=headers)).json()[
                "conversation_id"
            ]
            response = await client.post(
                f"/chat/sessions/{session}/messages",
                headers=headers,
                json={"message": "Estado de mi caso"},
            )
            assert response.status_code == 503
            assert not any(
                e["event"] == "verify_readback" for e in app.state.runtime.events[cursor:]
            )

    asyncio.run(check())


def test_precise_existing_case_alias_does_not_fail_generic_receipt_check():
    s = authored()
    s["overlays"].append(
        {
            "kind": "case",
            "record_ref": "opened-ticket",
            "values": {
                "customer_ref": "persona",
                "transaction_ref": "target",
                "status": "received",
                "created_at": "2026-06-08T18:00:00Z",
            },
        }
    )
    s["gold"].update(
        outcome="status_reported",
        required_actions=[
            {"type": "report_case", "target_ref": "opened-ticket"},
            {"type": "verify_readback", "target_ref": "opened-ticket"},
        ],
        forbidden_actions=["create_dispute", "report_unverified_action"],
    )
    result = run(s)
    assert result["passed"] and result["readback"]
    assert {"opened-ticket", "existing-case"} <= set(result["verified_refs"])
    assert not result["unsafe"]["reported_not_verified"]
