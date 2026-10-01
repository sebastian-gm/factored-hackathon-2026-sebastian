"""Authored serving-like story availability; no organizer or frozen-suite rows."""

import secrets
from dataclasses import replace
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.bank.serving import Persona, demo_story_mappings
from aclara.settings import Settings


def ledger_and_personas():
    clock = Settings().bank_clock
    seed = TransactionRepository()._rows[0]
    first = replace(
        seed,
        record_id="authored-choice-a",
        customer_id="authored-owner",
        product_id="authored-card",
        transaction_date=clock - timedelta(days=3),
        transaction_type="Purchase",
        amount=20,
        currency="USD",
        merchant_name="",
        transaction_status="Approved",
    )
    second = replace(first, record_id="authored-choice-b", amount=30)
    personas = {
        "demo.pt.br": Persona("demo.pt.br", first.customer_id, "pt-BR", "ops"),
        "demo.es.mx": Persona("demo.es.mx", first.customer_id, "es-MX", "ops"),
    }
    return clock, first, second, personas


@pytest.mark.parametrize("missing_merchant", ["", "   "])
def test_missing_merchants_allow_owned_choices_but_not_named_explanation(missing_merchant):
    clock, first, second, personas = ledger_and_personas()
    ledger = TransactionRepository(
        (
            replace(first, merchant_name=missing_merchant),
            replace(second, merchant_name=missing_merchant),
        )
    )
    hints = demo_story_mappings(ledger, personas, clock)
    assert hints == {"demo.es.mx": ["fraud"], "demo.pt.br": ["ambiguous"]}
    assert all(
        row.merchant_name == missing_merchant
        for _, row in ledger.for_customer(first.customer_id, clock)
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"amount": float("nan")},
        {"amount": float("inf")},
        {"amount": -1},
        {"currency": "   "},
        {"transaction_status": "Unknown"},
        {"customer_id": "authored-other"},
        {"transaction_date": Settings().bank_clock - timedelta(days=121)},
        {"transaction_date": Settings().bank_clock},
    ],
)
def test_insufficient_reviewable_owned_movements_keep_choice_hint_off(changes):
    clock, first, second, personas = ledger_and_personas()
    ledger = TransactionRepository((first, replace(second, **changes)))
    assert demo_story_mappings(ledger, personas, clock)["demo.pt.br"] == []


def test_unowned_product_and_unreviewed_identity_keep_hint_off():
    clock, first, second, personas = ledger_and_personas()
    ledger = TransactionRepository(
        (first, replace(second, product_id="unowned-card")),
        products=TransactionRepository((first,)).products,
    )
    assert demo_story_mappings(ledger, personas, clock)["demo.pt.br"] == []
    ledger = TransactionRepository((first, second))
    for persona in (
        replace(personas["demo.pt.br"], role="customer"),
        replace(personas["demo.pt.br"], locale="es-MX"),
    ):
        assert "demo.pt.br" not in demo_story_mappings(ledger, {"demo.pt.br": persona}, clock)


def test_pt_hint_prepares_authentication_and_real_missing_merchant_choices_only():
    clock, first, second, _ = ledger_and_personas()
    settings = Settings(
        demo_username="demo.pt.br",
        demo_password=secrets.token_urlsafe(24),
        demo_customer_id=first.customer_id,
        demo_locale="pt-BR",
        demo_role="ops",
        bank_clock=clock,
    )
    app = create_app(settings, TransactionRepository((first, second)))
    with TestClient(app) as client:
        public = client.get("/personas")
        assert public.json()[0]["demo_stories"] == ["ambiguous"]
        assert "authored-owner" not in public.text
        assert client.get("/transactions").status_code == 401
        challenge = client.post(
            "/auth/login",
            json={"username": settings.demo_username, "password": settings.demo_password},
        ).json()
        pre = {"X-Preauth-Token": challenge["preauth_token"]}
        code = client.get(f"/auth/challenges/{challenge['challenge_id']}/sms", headers=pre).json()[
            "code"
        ]
        session = client.post(
            "/auth/otp/verify",
            headers=pre,
            json={"challenge_id": challenge["challenge_id"], "code": code},
        ).json()
        headers = {"Authorization": "Bearer " + session["access_token"]}
        cid = client.post("/chat/sessions", headers=headers).json()["conversation_id"]
        response = client.post(
            f"/chat/sessions/{cid}/messages",
            headers=headers,
            json={
                "message": "Quero entender uma cobrança no meu cartão. Quais compras posso revisar?"
            },
        ).json()
        assert response["response_type"] == "choose_transaction"
        assert len(response["candidates"]) == 2
        assert all(row["merchant"] == "—" for row in response["candidates"])
        assert all(row["handle"] for row in response["candidates"])
        assert response["proposal"] is None and response["case"] is None
        assert response["verified"] is False
