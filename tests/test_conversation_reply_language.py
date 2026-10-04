"""Authored mock regressions for conversation language and scoped charge context."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, replace
from datetime import timedelta
from html import unescape
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.contracts import DisputeCaseView
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec
from aclara.ops.store import Scope, Store
from aclara.settings import Settings


def _other(language: str) -> str:
    return "pt" if language == "es" else "es"


def _status(language: str) -> str:
    return (
        "¿Puedes mostrarme el estado de mi caso?"
        if language == "es"
        else "Agora, qual é o status do meu caso?"
    )


def _client(
    language: str, observations: dict[str, dict[str, Any]] | None = None
) -> StructuredClient:
    def answer(_system: str, user: str, schema: type[Any]) -> str:
        assert schema is ExtractedNlu
        customer_message = unescape(
            user.split("<customer_message>\n", 1)[1].split("\n</customer_message>", 1)[0]
        )
        value = {
            "language": language,
            "intent": "charge_inquiry",
            "intent_confidence": 0.99,
            **(observations or {}).get(customer_message, {}),
        }
        return json.dumps(value)

    return StructuredClient(
        {route: ModelSpec("mock", "authored-language") for route in ("nlu", "phrase")},
        {},
        mock_response=answer,
        budget_usd=0,
        daily_budget_usd=0,
    )


def _settings_for(language: str) -> Settings:
    return replace(_settings(), demo_locale="pt-BR" if language == "pt" else "es-MX")


def _scope(app: FastAPI, token: str) -> Scope:
    principal = app.state.sessions[token]
    return Scope(principal.customer_id, principal.run_id, principal.session_id)


def _state(app: FastAPI, token: str, cid: str) -> dict[str, Any]:
    with app.state.store.transaction(_scope(app, token)):
        conversation = app.state.conversations[cid]
        snapshot = asdict(conversation)
        snapshot["slots"] = conversation.slots.model_dump() if conversation.slots else None
        return {
            "conversation": snapshot,
            "cases": dict(app.state.cases),
            "cards": dict(app.state.card_states),
            "executions": len(app.state.executions),
        }


def _assert_case_reply_language(reply: str, language: str) -> None:
    # Original bank receipts and localized replay templates both express the
    # verified case; language checks accept each supported wording.
    prefixes = ("Sua contestação", "O caso") if language == "pt" else ("Tu disputa", "El caso")
    assert reply.startswith(prefixes)


def _assert_no_write(app: FastAPI, token: str, cid: str) -> None:
    state = _state(app, token, cid)
    assert not state["cases"] and not state["cards"]
    assert not state["conversation"]["proposal"]
    assert not any(
        event["event"] in {"create_dispute", "freeze_card"} for event in app.state.runtime.events
    )


async def _choose_if_needed(
    client: AsyncClient,
    headers: dict[str, str],
    result: dict[str, Any],
    cid: str,
    language: str,
    merchant: str,
) -> dict[str, Any]:
    if result["response_type"] == "choose_transaction":
        index = next(i for i, row in enumerate(result["candidates"]) if row["merchant"] == merchant)
        choices = (
            ("el primero", "el segundo", "el tercero")
            if language == "es"
            else ("o primeiro", "o segundo", "o terceiro")
        )
        result, _ = await message(client, headers, choices[index], cid)
    return result


async def _proposal(
    client: AsyncClient,
    headers: dict[str, str],
    language: str,
) -> tuple[dict[str, Any], str]:
    text = (
        "No hice el cargo de Taller Prisma por 17.43 USD"
        if language == "es"
        else "Não fiz a compra de Taller Prisma por 17.43 USD"
    )
    result, cid = await message(client, headers, text)
    result = await _choose_if_needed(client, headers, result, cid, language, "Taller Prisma")
    assert result["response_type"] == "confirm_action"
    return result, cid


def _proposal_client(language: str) -> StructuredClient:
    text = (
        "No hice el cargo de Taller Prisma por 17.43 USD"
        if language == "es"
        else "Não fiz a compra de Taller Prisma por 17.43 USD"
    )
    return _client(
        language,
        {
            text: {
                "intent": "dispute_charge",
                "merchant_expr": "Taller Prisma",
                "amount_expr": "17.43",
                "currency_expr": "USD",
            }
        },
    )


def _switch_pending(app: FastAPI, token: str, cid: str, language: str) -> dict[str, Any]:
    # Isolate rendering from the separately reviewed courtesy/follow-up stack.
    # Only trusted scoped conversation language changes; authority is immutable.
    with app.state.store.transaction(_scope(app, token)):
        conversation = app.state.conversations[cid]
        assert conversation.proposal is not None
        before = asdict(conversation.proposal)
        conversation.language = language
    after = _state(app, token, cid)["conversation"]["proposal"]
    assert after == before
    assert after["action_hash"] == before["action_hash"]
    assert after["expires_at"] == before["expires_at"]
    return before


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize("language", ["es", "pt"])
def test_switch_during_choices_and_neutral_status_survives_scoped_restart(
    system: str, language: str
) -> None:
    async def check() -> None:
        settings, store, repository = _settings_for(language), Store(), ledger(True)
        llm = _client(language)
        app = create_app(settings, repository, Runtime(system=system), llm, store)
        target = _other(language)
        expected = target if system == "P" else language
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            opening = "No reconozco una compra" if language == "es" else "Não reconheço uma compra"
            choices, cid = await message(client, headers, opening)
            assert choices["response_type"] == "choose_transaction"
            initial = _state(app, token, cid)["conversation"]
            switched, _ = await message(client, headers, _status(target), cid)
            assert switched["response_type"] == "clarify" and switched["policy_rules"] == ["DSP-06"]
            assert switched["reply"].startswith(
                "Não encontrei" if expected == "pt" else "No encontré"
            )
            neutral, _ = await message(client, headers, "status DSP-ABC12345", cid)
            assert neutral["reply"].startswith(
                "Não encontrei" if expected == "pt" else "No encontré"
            )
            saved = _state(app, token, cid)["conversation"]
            assert saved["language"] == expected
            assert saved["candidates"] == initial["candidates"]
            assert saved["rounds"] == initial["rounds"]
            _assert_no_write(app, token, cid)
        app = create_app(settings, repository, Runtime(system=system), llm, store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            neutral, _ = await message(client, headers, "??? DSP-ABC12345", cid)
            assert neutral["reply"].startswith(
                "Não encontrei" if expected == "pt" else "No encontré"
            )
            assert _state(app, token, cid)["conversation"]["language"] == expected
            if system == "P":
                fresh, fresh_id = await message(client, headers, "status DSP-ABC12345")
                assert fresh["reply"].startswith(
                    "Não encontrei" if language == "pt" else "No encontré"
                )
                assert _state(app, token, fresh_id)["conversation"]["language"] == language
                assert _state(app, token, cid)["conversation"]["language"] == target
            _assert_no_write(app, token, cid)

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("confirmed", [True, False])
def test_confirm_and_cancel_use_current_p_language_without_changing_proposal(
    system: str, language: str, confirmed: bool
) -> None:
    async def check() -> None:
        llm = _proposal_client(language)
        app = create_app(_settings_for(language), ledger(), Runtime(system=system), llm, Store())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            offer, cid = await _proposal(client, headers, language)
            original = _switch_pending(app, token, cid, _other(language))
            assert original["language"] == language
            calls = len(llm.records)
            response = await client.post(
                f"/chat/sessions/{cid}/confirm",
                headers=headers,
                json={
                    "proposal_hash": offer["proposal"]["proposal_hash"],
                    "confirmed": confirmed,
                },
            )
            assert response.status_code == 200
            result = response.json()
            expected = _other(language) if system == "P" else language
            if confirmed:
                assert result["response_type"] == "report_case" and result["verified"] is True
                _assert_case_reply_language(result["reply"], expected)
                readback = await client.get(
                    "/disputes/" + result["case"]["case_id"], headers=headers
                )
                assert readback.status_code == 200
                assert DisputeCaseView.model_validate(
                    readback.json()
                ) == DisputeCaseView.model_validate(result["case"])
                assert len(_state(app, token, cid)["cases"]) == 1
            else:
                assert result["response_type"] == "cancelled"
                assert result["reply"] == (
                    "Contestação cancelada." if expected == "pt" else "Disputa cancelada."
                )
                _assert_no_write(app, token, cid)
            assert len(llm.records) == calls
            assert not _state(app, token, cid)["conversation"]["proposal"]

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize("language", ["es", "pt"])
def test_injected_prewrite_failure_uses_current_p_language_and_verified_handoff(
    system: str, language: str
) -> None:
    async def check() -> None:
        runtime, llm = Runtime(system=system), _proposal_client(language)
        app = create_app(_settings_for(language), ledger(), runtime, llm, Store())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            offer, cid = await _proposal(client, headers, language)
            _switch_pending(app, token, cid, _other(language))
            runtime.faults.append({"type": "tool_failure", "trigger": "create_dispute"})
            calls = len(llm.records)
            response = await client.post(
                f"/chat/sessions/{cid}/confirm",
                headers=headers,
                json={
                    "proposal_hash": offer["proposal"]["proposal_hash"],
                    "confirmed": True,
                },
            )
            assert response.status_code == 200
            result = response.json()
            expected = _other(language) if system == "P" else language
            assert result["response_type"] == "offer_human"
            assert result["reply"].startswith(
                "Vou encaminhar" if expected == "pt" else "Voy a derivar"
            )
            assert result["handoff"]["route"]["language"] == expected
            readback = await client.get(
                "/handoffs/" + result["handoff"]["handoff_id"], headers=headers
            )
            assert readback.status_code == 200 and readback.json()["route"]["language"] == expected
            assert len(llm.records) == calls
            _assert_no_write(app, token, cid)

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize("language", ["es", "pt"])
def test_receipt_replay_after_real_language_switch_preserves_verified_case_and_calls(
    system: str, language: str
) -> None:
    async def check() -> None:
        llm, store = _proposal_client(language), Store()
        app = create_app(_settings_for(language), ledger(), Runtime(system=system), llm, store)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            offer, cid = await _proposal(client, headers, language)
            body = {"proposal_hash": offer["proposal"]["proposal_hash"], "confirmed": True}
            first = await client.post(f"/chat/sessions/{cid}/confirm", headers=headers, json=body)
            assert first.status_code == 200 and first.json()["verified"] is True
            original = first.json()
            case_id = original["case"]["case_id"]
            target = _other(language)
            status, _ = await message(client, headers, _status(target) + " " + case_id, cid)
            assert status["case"] == original["case"] and status["verified"] is True
            assert status["reply"].startswith("O caso" if target == "pt" else "El caso")
            before, calls = _state(app, token, cid), len(llm.records)
            replay = await client.post(f"/chat/sessions/{cid}/confirm", headers=headers, json=body)
            assert replay.status_code == 200
            result = replay.json()
            assert {k: v for k, v in result.items() if k != "reply"} == {
                k: v for k, v in original.items() if k != "reply"
            }
            expected = target if system == "P" else language
            _assert_case_reply_language(result["reply"], expected)
            if system == "B1":
                assert result["reply"] == original["reply"]
            after = _state(app, token, cid)
            assert after["cases"] == before["cases"] and len(after["cases"]) == 1
            assert after["cards"] == before["cards"]
            assert after["executions"] == before["executions"]
            assert len(llm.records) == calls
            assert (
                sum(event["event"] == "create_dispute" for event in app.state.runtime.events) == 1
            )
            readback = await client.get("/disputes/" + case_id, headers=headers)
            assert readback.status_code == 200
            assert DisputeCaseView.model_validate(
                readback.json()
            ) == DisputeCaseView.model_validate(original["case"])

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("prior_merchant_slot", [True, False])
def test_explicit_merchant_retarget_drops_old_amount_and_date_without_bypassing_match(
    language: str, prior_merchant_slot: bool
) -> None:
    async def check() -> None:
        initial = ledger(True)._rows
        second = replace(
            initial[1],
            transaction_date=initial[1].transaction_date - timedelta(days=2),
            process_date=initial[1].process_date - timedelta(days=2),
        )
        repository = TransactionRepository((initial[0], second))
        date_text = initial[0].transaction_date.date().isoformat()
        first_text = (
            f"¿Puedes explicar el cargo de Taller Prisma por 17.43 USD del {date_text}?"
            if language == "es"
            else f"Pode explicar a cobrança de Taller Prisma por 17.43 USD de {date_text}?"
        )
        new_text = (
            "¿Puedes explicar el cargo de Estudio Nube?"
            if language == "es"
            else "Pode explicar a cobrança de Estudio Nube?"
        )
        llm = _client(
            language,
            {
                first_text: {
                    "merchant_expr": "Taller Prisma",
                    "amount_expr": "17.43",
                    "currency_expr": "USD",
                    "date_expr": date_text,
                },
                new_text: {"merchant_expr": "Estudio Nube"},
            },
        )
        app = create_app(_settings_for(language), repository, Runtime(system="P"), llm, Store())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            first, cid = await message(client, headers, first_text)
            first = await _choose_if_needed(client, headers, first, cid, language, "Taller Prisma")
            assert (
                first["response_type"] == "explain_status"
                and first["transaction"]["merchant"] == "Taller Prisma"
            )
            if not prior_merchant_slot:
                # An amount/date-only identification can still have an owned
                # selected charge; simulate that persisted slot combination.
                with app.state.store.transaction(_scope(app, token)):
                    conversation = app.state.conversations[cid]
                    assert (
                        conversation.selected_handle is not None and conversation.slots is not None
                    )
                    conversation.slots = conversation.slots.model_copy(
                        update={"merchant_expr": None}
                    )
            old_slots = _state(app, token, cid)["conversation"]["slots"]
            assert old_slots["amount_value"] is not None and old_slots["date_start"] is not None
            assert bool(old_slots["merchant_expr"]) is prior_merchant_slot
            cursor = len(app.state.runtime.events)
            result, _ = await message(client, headers, new_text, cid)
            slots = _state(app, token, cid)["conversation"]["slots"]
            assert slots["merchant_expr"] == "Estudio Nube"
            assert (
                slots["amount_value"] is None
                and slots["date_start"] is None
                and slots["date_end"] is None
            )
            assert any(event["event"] == "match" for event in app.state.runtime.events[cursor:])
            assert result["response_type"] in {"choose_transaction", "clarify", "explain_status"}
            if result["response_type"] == "explain_status":
                assert result["transaction"]["merchant"] == "Estudio Nube"
                assert result["transaction"]["amount"] == second.amount
            _assert_no_write(app, token, cid)

    asyncio.run(check())


@pytest.mark.parametrize("system", ["B1", "P"])
@pytest.mark.parametrize("language", ["es", "pt"])
def test_chat_cancellation_switches_p_reply_before_pending_proposal_early_return(
    system: str, language: str
) -> None:
    async def check() -> None:
        llm = _proposal_client(language)
        app = create_app(_settings_for(language), ledger(), Runtime(system=system), llm, Store())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            offer, cid = await _proposal(client, headers, language)
            before = _state(app, token, cid)["conversation"]["proposal"]
            assert before["language"] == language
            assert before["action_hash"] == offer["proposal"]["proposal_hash"]
            calls = len(llm.records)
            target = _other(language)
            # The Spanish punctuation supplies clear ES evidence; unpunctuated
            # "no" is deliberately an uncertain language observation.
            result, _ = await message(client, headers, "¡No!" if target == "es" else "Não!", cid)
            expected = target if system == "P" else language
            assert result["response_type"] == "cancelled"
            assert result["reply"] == (
                "Contestação cancelada." if expected == "pt" else "Disputa cancelada."
            )
            assert _state(app, token, cid)["conversation"]["language"] == expected
            assert len(llm.records) == calls
            rejected = await client.post(
                f"/chat/sessions/{cid}/confirm",
                headers=headers,
                json={
                    "proposal_hash": offer["proposal"]["proposal_hash"],
                    "confirmed": True,
                },
            )
            assert rejected.status_code == 409
            _assert_no_write(app, token, cid)

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_scoped_merchant_language_cues_and_mock_nlu_do_not_override_real_switch(
    language: str,
) -> None:
    async def check() -> None:
        target = _other(language)
        merchant = "Obrigado Café" if target == "es" else "Quiero Café"
        row = replace(ledger()._rows[0], merchant_name=merchant)
        text = (
            f"¿Puedes explicar el cargo de {merchant} por 17.43 USD?"
            if target == "es"
            else f"Pode explicar a cobrança de {merchant} por 17.43 USD?"
        )
        # Deliberately retain the previous language in the observation: prose
        # evidence, scoped names and trusted conversation state decide rendering.
        llm = _client(
            language,
            {text: {"merchant_expr": merchant, "amount_expr": "17.43", "currency_expr": "USD"}},
        )
        app = create_app(
            _settings_for(language),
            TransactionRepository((row,)),
            Runtime(system="P"),
            llm,
            Store(),
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": f"Bearer {token}"}
            result, cid = await message(client, headers, text)
            assert _state(app, token, cid)["conversation"]["language"] == target
            result = await _choose_if_needed(client, headers, result, cid, target, merchant)
            assert (
                result["response_type"] == "explain_status"
                and result["transaction"]["merchant"] == merchant
            )
            assert result["reply"].startswith("O registro" if target == "pt" else "El registro")
            assert _state(app, token, cid)["conversation"]["language"] == target
            _assert_no_write(app, token, cid)

    asyncio.run(check())
