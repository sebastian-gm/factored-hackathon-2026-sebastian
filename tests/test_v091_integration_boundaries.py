"""Authored safety regressions from the v0.9.1 held-batch review."""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _sign_in
from test_candidate_corrections import Language, application, case_count, opening
from test_conversation_reply_language import _client, _settings_for, _state
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.runtime import Runtime
from aclara.api.app import create_app


@pytest.mark.parametrize("language", ["es", "pt"])
def test_rejected_correction_reaches_existing_clarification_limit(language: Language) -> None:
    async def check() -> None:
        app = application(
            language,
            {"date_expr": "2026-06-13"},
            followup_observations=({"date_expr": "2026-06-13"},),
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            choice, cid = await message(client, headers, opening(language))
            assert choice["response_type"] == "choose_transaction"
            first, _ = await message(client, headers, "24.00 USD", cid)
            assert first["response_type"] == "clarify"
            second, _ = await message(client, headers, "24.00 USD", cid)
            assert second["response_type"] == "offer_human"
            assert "ESC-04" in second["handoff"]["reason_codes"]
            assert not second.get("proposal") and not second.get("case")
            assert case_count(app, headers) == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("selected_date", ["2026-06-13", "2026-06-14"])
def test_negated_date_is_rejected_but_positive_correction_remains_usable(
    language: Language, selected_date: str
) -> None:
    async def check() -> None:
        app = application(language, {"date_expr": selected_date})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            choice, cid = await message(client, headers, opening(language))
            assert choice["response_type"] == "choose_transaction"
            correction = (
                "Corrijo la fecha: no fue el 2026-06-13; fue el 2026-06-14."
                if language == "es"
                else "Corrigindo a data: não foi em 2026-06-13; foi em 2026-06-14."
            )
            reply, _ = await message(client, headers, correction, cid)
            if selected_date == "2026-06-13":
                assert reply["response_type"] == "clarify"
                assert not reply.get("proposal")
            else:
                assert reply["response_type"] == "confirm_action"
                assert reply["transaction"]["handle"] == "txn_1"
            assert not reply.get("case") and case_count(app, headers) == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_denial_of_purchase_keeps_its_date_as_positive_evidence(language: Language) -> None:
    async def check() -> None:
        app = application(language, {"date_expr": "2026-06-13"})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            _, cid = await message(client, headers, opening(language))
            denial = (
                "No hice la compra el 2026-06-13."
                if language == "es"
                else "Não fiz a compra em 2026-06-13."
            )
            reply, _ = await message(client, headers, denial, cid)
            assert reply["response_type"] == "confirm_action"
            assert reply["transaction"]["handle"] == "txn_2"
            assert case_count(app, headers) == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_terminal_handoff_switches_display_language_without_new_authority(
    language: Language,
) -> None:
    async def check() -> None:
        app = create_app(_settings_for(language), ledger(), Runtime(system="P"), _client(language))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await _sign_in(client)
            headers = {"Authorization": "Bearer " + token}
            request = (
                "Quiero hablar con una persona."
                if language == "es"
                else "Quero falar com uma pessoa."
            )
            first, cid = await message(client, headers, request)
            assert first["response_type"] == "offer_human"
            instruction = (
                "Agora, responda em português, por favor."
                if language == "es"
                else "Ahora, responde en español, por favor."
            )
            repeated, _ = await message(client, headers, instruction, cid)
            assert repeated["response_type"] == "offer_human"
            assert repeated["handoff"]["handoff_id"] == first["handoff"]["handoff_id"]
            assert repeated["handoff"]["reason_codes"] == first["handoff"]["reason_codes"]
            assert repeated["reply"].startswith("Vou encaminhar" if language == "es" else "Voy a")
            state = _state(app, token, cid)
            assert state["conversation"]["language"] == ("pt" if language == "es" else "es")
            assert not state["cases"] and not state["cards"]
            assert not state["conversation"]["proposal"]

    asyncio.run(check())


@pytest.mark.parametrize(
    ("text", "current", "merchants", "expected"),
    [
        ("Agora responda em português, por favor.", "es", (), "pt"),
        ("Ahora responde en español, por favor.", "pt", (), "es"),
        ("El cargo de Responde en Português", "es", ("Responde en Português",), "es"),
        ("O cargo de Responde en Español", "pt", ("Responde en Español",), "pt"),
    ],
)
def test_explicit_language_request_does_not_use_merchant_words(
    text: str, current: str, merchants: tuple[str, ...], expected: str
) -> None:
    from aclara.api.reply_language import conversation_language

    assert conversation_language(text, current, merchants) == expected
