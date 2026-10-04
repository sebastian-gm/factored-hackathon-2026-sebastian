"""Authored corrections narrow scoped choices; typed observations cannot authorize writes."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any, Literal

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from test_api_security import _settings, _sign_in
from test_workflow_api import message

from aclara.agent.contracts import DisputeCaseView
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import Customer, Transaction, TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec
from aclara.ops.store import Scope

Language = Literal["es", "pt"]


def repository(
    language: Language, *, same_amount: bool = False, single_row: bool = False
) -> TransactionRepository:
    details = ((14, 24.0 if same_amount else 12.0), (13, 24.0))
    return TransactionRepository(
        tuple(
            Transaction(
                f"correction-{index}",
                "demo-customer-01",
                "correction-card",
                datetime(2026, 6, day, 9, tzinfo=UTC),
                date(2026, 6, day),
                "Purchase",
                amount,
                "USD",
                "Taller Boreal",
                "Approved",
            )
            for index, (day, amount) in enumerate(details[:1] if single_row else details, 1)
        ),
        customers=(Customer("demo-customer-01", country="BR" if language == "pt" else "MX"),),
    )


def application(
    language: Language,
    observation: dict[str, Any],
    *,
    same_amount: bool = False,
    single_row: bool = False,
    opening_updates: dict[str, Any] | None = None,
    followup_observations: tuple[dict[str, Any], ...] = (),
) -> FastAPI:
    observations: Iterator[dict[str, Any]] = iter(
        (
            {
                "language": language,
                "intent": "dispute_charge",
                "intent_confidence": 0.99,
                "merchant_expr": "Taller Boreal",
                **(opening_updates or {}),
            },
            {
                "language": language,
                "intent": "charge_inquiry",
                "intent_confidence": 0.99,
                **observation,
            },
            *(
                {
                    "language": language,
                    "intent": "charge_inquiry",
                    "intent_confidence": 0.99,
                    **extra,
                }
                for extra in followup_observations
            ),
        )
    )

    def respond(_system: str, _user: str, schema: type[BaseModel]) -> str:
        assert schema is ExtractedNlu
        return json.dumps(next(observations), ensure_ascii=False)

    llm = StructuredClient(
        {route: ModelSpec("mock", "candidate-correction") for route in ("nlu", "phrase")},
        {},
        mock_response=respond,
        budget_usd=0.0,
    )
    settings = replace(_settings(), demo_locale="pt-BR" if language == "pt" else "es-MX")
    return create_app(
        settings,
        repository(language, same_amount=same_amount, single_row=single_row),
        Runtime(system="P"),
        llm,
    )


def case_count(app: FastAPI, headers: dict[str, str]) -> int:
    principal = app.state.sessions[headers["Authorization"].removeprefix("Bearer ")]
    with app.state.store.transaction(
        Scope(principal.customer_id, principal.run_id, principal.session_id)
    ):
        return len(app.state.cases)


def opening(language: Language) -> str:
    return (
        "Quero contestar uma compra de Taller Boreal"
        if language == "pt"
        else "Quiero disputar una compra de Taller Boreal"
    )


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("field", ["amount", "date", "both"])
def test_new_details_select_the_scoped_charge_and_preserve_dispute_intent(
    language: Language, field: str
) -> None:
    async def check() -> None:
        text = {
            "amount": ("El valor correcto es 24.00 USD.", "O valor correto é 24.00 USD."),
            "date": (
                "Corrijo la fecha: fue el 2026-06-13.",
                "Corrigindo a data: foi em 2026-06-13.",
            ),
            "both": (
                "Corrijo los datos: fue el 2026-06-13, por 24.00 USD.",
                "Corrigindo os dados: foi em 2026-06-13, por 24.00 USD.",
            ),
        }[field][language == "pt"]
        observation = {"amount_expr": "24.00", "currency_expr": "USD"} if field != "date" else {}
        if field != "amount":
            observation["date_expr"] = "2026-06-13"
        app = application(language, observation)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            choice, conversation = await message(client, headers, opening(language))
            assert choice["response_type"] == "choose_transaction"
            assert {item["amount"] for item in choice["candidates"]} == {12.0, 24.0}
            proposal, _ = await message(client, headers, text, conversation)
            assert proposal["response_type"] == "confirm_action"
            assert proposal["transaction"]["handle"] == "txn_2"
            assert proposal["transaction"]["transaction_date"].startswith("2026-06-13")
            assert proposal["transaction"]["amount"] == 24.0
            assert case_count(app, headers) == 0
            typed_assent = await client.post(
                f"/chat/sessions/{conversation}/messages",
                headers=headers,
                json={"message": "Sim" if language == "pt" else "Sí"},
            )
            assert typed_assent.status_code == 409
            invalid = await client.post(
                f"/chat/sessions/{conversation}/confirm",
                headers=headers,
                json={"proposal_hash": "0" * 64, "confirmed": True},
            )
            assert invalid.status_code == 409
            assert case_count(app, headers) == 0
            filed = await client.post(
                f"/chat/sessions/{conversation}/confirm",
                headers=headers,
                json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True},
            )
            assert filed.status_code == 200
            receipt = filed.json()
            assert receipt["verified"] and receipt["case"]["transaction_handle"] == "txn_2"
            assert case_count(app, headers) == 1
            read = await client.get("/disputes/" + receipt["case"]["case_id"], headers=headers)
            assert read.status_code == 200
            assert DisputeCaseView.model_validate(read.json()) == DisputeCaseView.model_validate(
                receipt["case"]
            )
            assert app.state.ai.client.spent_usd == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("scenario", ["invalid_date", "conflict", "competing_amounts", "currency"])
def test_invalid_or_conflicting_corrections_cannot_choose_or_write(
    language: Language, scenario: str
) -> None:
    async def check() -> None:
        text, observation = {
            "invalid_date": (
                ("La fecha fue 2026-02-31.", "A data foi 2026-02-31."),
                {"date_expr": "2026-02-31"},
            ),
            "conflict": (
                ("Fue el 2026-06-13 por 12.00 USD.", "Foi em 2026-06-13 por 12.00 USD."),
                {"date_expr": "2026-06-13", "amount_expr": "12.00", "currency_expr": "USD"},
            ),
            "competing_amounts": (
                ("Fueron 12 o 24 USD, no estoy seguro.", "Foi 12 ou 24 USD, não tenho certeza."),
                {"amount_expr": "24", "currency_expr": "USD"},
            ),
            "currency": (
                ("Eran 24 EUR.", "Eram 24 EUR."),
                {"amount_expr": "24", "currency_expr": "EUR"},
            ),
        }[scenario]
        app = application(language, observation)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            choice, conversation = await message(client, headers, opening(language))
            assert choice["response_type"] == "choose_transaction"
            result, _ = await message(client, headers, text[language == "pt"], conversation)
            assert result["response_type"] in {"clarify", "choose_transaction", "offer_human"}
            assert not result.get("proposal") and not result.get("case")
            denied = await client.post(
                f"/chat/sessions/{conversation}/confirm",
                headers=headers,
                json={"proposal_hash": "0" * 64, "confirmed": True},
            )
            assert denied.status_code == 409
            assert case_count(app, headers) == 0
            assert app.state.ai.client.spent_usd == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_amount_shared_by_two_candidates_stays_a_choice(language: Language) -> None:
    async def check() -> None:
        app = application(
            language, {"amount_expr": "24.00", "currency_expr": "USD"}, same_amount=True
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            choice, conversation = await message(client, headers, opening(language))
            assert choice["response_type"] == "choose_transaction"
            text = "El valor era 24.00 USD." if language == "es" else "O valor era 24.00 USD."
            unresolved, _ = await message(client, headers, text, conversation)
            assert unresolved["response_type"] in {"choose_transaction", "clarify"}
            assert not unresolved.get("proposal") and not unresolved.get("case")
            assert case_count(app, headers) == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_stated_wrong_date_requires_correction_then_valid_cancel(language: Language) -> None:
    async def check() -> None:
        app = application(
            language, {"date_expr": "2026-06-13"}, opening_updates={"date_expr": "2026-06-10"}
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            first = (
                "No hice la compra de Taller Boreal el 2026-06-10."
                if language == "es"
                else "Não fiz a compra de Taller Boreal em 2026-06-10."
            )
            mismatch, conversation = await message(client, headers, first)
            assert mismatch["response_type"] == "clarify"
            assert not mismatch.get("proposal") and case_count(app, headers) == 0
            correction = (
                "Corrijo la fecha: fue el 2026-06-13."
                if language == "es"
                else "Corrigindo a data: foi em 2026-06-13."
            )
            proposal, _ = await message(client, headers, correction, conversation)
            assert proposal["response_type"] == "confirm_action"
            assert proposal["transaction"]["handle"] == "txn_2"
            assert case_count(app, headers) == 0
            cancelled = await client.post(
                f"/chat/sessions/{conversation}/confirm",
                headers=headers,
                json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": False},
            )
            assert cancelled.status_code == 200 and cancelled.json()["response_type"] == "cancelled"
            assert case_count(app, headers) == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_missing_date_still_presents_owned_choices(language: Language) -> None:
    async def check() -> None:
        app = application(language, {})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            text = opening(language) + (
                ", pero no recuerdo la fecha." if language == "es" else ", mas não lembro a data."
            )
            choice, _ = await message(client, headers, text)
            assert choice["response_type"] == "choose_transaction"
            assert {item["handle"] for item in choice["candidates"]} == {"txn_1", "txn_2"}
            assert not choice.get("proposal") and case_count(app, headers) == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_correction_refilters_current_scoped_facts(language: Language) -> None:
    async def check() -> None:
        app = application(language, {"amount_expr": "24.00", "currency_expr": "USD"})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            choice, conversation = await message(client, headers, opening(language))
            assert choice["response_type"] == "choose_transaction"
            # The bank corrects a displayed amount while the customer is choosing.
            first, second = app.state.ledger._rows
            app.state.ledger._rows = (first, replace(second, amount=240.99))
            text = "El valor era 24.00 USD." if language == "es" else "O valor era 24.00 USD."
            result, _ = await message(client, headers, text, conversation)
            assert result["response_type"] in {"clarify", "choose_transaction", "offer_human"}
            assert not result.get("proposal") and case_count(app, headers) == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("scenario", ["different_raw_date", "amount_only"])
def test_model_only_date_cannot_select_a_candidate(language: Language, scenario: str) -> None:
    async def check() -> None:
        observation = {"date_expr": "2026-06-13"}
        if scenario == "amount_only":
            observation.update(amount_expr="24.00", currency_expr="USD")
        app = application(language, observation, same_amount=True)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            choice, conversation = await message(client, headers, opening(language))
            assert choice["response_type"] == "choose_transaction"
            texts = {
                "different_raw_date": (
                    "Corrijo la fecha: fue el 2026-06-14.",
                    "Corrigindo a data: foi em 2026-06-14.",
                ),
                "amount_only": ("El valor correcto es 24.00 USD.", "O valor correto é 24.00 USD."),
            }
            result, _ = await message(
                client, headers, texts[scenario][language == "pt"], conversation
            )
            assert result["response_type"] in {"clarify", "choose_transaction", "offer_human"}
            assert not result.get("proposal") and not result.get("case")
            assert case_count(app, headers) == 0
            denied = await client.post(
                f"/chat/sessions/{conversation}/confirm",
                headers=headers,
                json={"proposal_hash": "0" * 64, "confirmed": True},
            )
            assert denied.status_code == 409
            assert case_count(app, headers) == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_rejected_model_date_does_not_leak_into_next_correction(language: Language) -> None:
    async def check() -> None:
        amount = {"amount_expr": "24.00", "currency_expr": "USD"}
        app = application(
            language,
            {**amount, "date_expr": "2026-06-13"},
            same_amount=True,
            followup_observations=(amount,),
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            choice, conversation = await message(client, headers, opening(language))
            assert choice["response_type"] == "choose_transaction"
            text = (
                "El valor correcto es 24.00 USD."
                if language == "es"
                else "O valor correto é 24.00 USD."
            )
            for _ in range(2):
                result, _ = await message(client, headers, text, conversation)
                assert not result.get("proposal") and not result.get("case")
                assert case_count(app, headers) == 0
            denied = await client.post(
                f"/chat/sessions/{conversation}/confirm",
                headers=headers,
                json={"proposal_hash": "0" * 64, "confirmed": True},
            )
            assert denied.status_code == 409
            assert app.state.ai.client.spent_usd == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_competing_dates_with_identity_uncertainty_cannot_select(language: Language) -> None:
    async def check() -> None:
        app = application(language, {"date_expr": "2026-06-13"})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            choice, conversation = await message(client, headers, opening(language))
            assert choice["response_type"] == "choose_transaction"
            text = (
                "Fue el 2026-06-13 o el 2026-06-14, no estoy seguro."
                if language == "es"
                else "Foi em 2026-06-13 ou em 2026-06-14, não tenho certeza."
            )
            result, _ = await message(client, headers, text, conversation)
            assert result["response_type"] in {"clarify", "choose_transaction", "offer_human"}
            assert not result.get("proposal") and not result.get("case")
            denied = await client.post(
                f"/chat/sessions/{conversation}/confirm",
                headers=headers,
                json={"proposal_hash": "0" * 64, "confirmed": True},
            )
            assert denied.status_code == 409 and case_count(app, headers) == 0

    asyncio.run(check())


@pytest.mark.parametrize("language", ["es", "pt"])
def test_currency_only_after_clarification_does_not_identify_a_single_row(
    language: Language,
) -> None:
    async def check() -> None:
        app = application(
            language,
            {"currency_expr": "USD"},
            single_row=True,
            opening_updates={"merchant_expr": None, "currency_expr": "pesos"},
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer " + await _sign_in(client)}
            first = (
                "No hice una compra en pesos, pero no sé la moneda exacta."
                if language == "es"
                else "Não fiz uma compra em pesos, mas não sei a moeda exata."
            )
            clarification, conversation = await message(client, headers, first)
            assert clarification["response_type"] == "clarify"
            correction = "La moneda es USD." if language == "es" else "A moeda é USD."
            result, _ = await message(client, headers, correction, conversation)
            assert result["response_type"] in {"clarify", "choose_transaction", "offer_human"}
            assert not result.get("proposal") and not result.get("case")
            denied = await client.post(
                f"/chat/sessions/{conversation}/confirm",
                headers=headers,
                json={"proposal_hash": "0" * 64, "confirmed": True},
            )
            assert denied.status_code == 409 and case_count(app, headers) == 0
            assert app.state.ai.client.spent_usd == 0

    asyncio.run(check())
