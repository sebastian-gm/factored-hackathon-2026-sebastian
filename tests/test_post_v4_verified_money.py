"""Code-rendered money is not a phone number; real identifiers stay blocked."""

from datetime import UTC, datetime

import pytest

from aclara.agent.contracts import ResponsePlan, TransactionView
from aclara.agent.nlg.builder import build_reply
from aclara.agent.nlg.grounding import scan_dlp, verify_draft


@pytest.mark.parametrize(
    ("language", "country", "currency"),
    [("es", "CO", "COP"), ("es", "AR", "ARS"), ("pt", "BR", "BRL")],
)
@pytest.mark.parametrize("kind", ["explain_status", "offer_dispute", "confirm_action"])
def test_large_verified_monetary_slot_survives_dlp(
    language: str, country: str, currency: str, kind: str
) -> None:
    transaction = TransactionView(
        handle="txn_1",
        transaction_date=datetime(2026, 6, 15, tzinfo=UTC),
        transaction_type="Purchase",
        amount=200000000,
        currency=currency,
        merchant="Comercio de Ensayo",
        status="Approved",
    )
    fields = {
        "response_type": kind,
        "outcome": {
            "explain_status": "explained",
            "offer_dispute": "awaiting_dispute_decision",
            "confirm_action": "dispute_proposed",
        }[kind],
        "reply": "",
        "transaction": transaction,
    }
    if kind == "confirm_action":
        fields["proposal"] = {
            "action": "create_dispute",
            "proposal_hash": "0" * 64,
            "expires_at": datetime(2026, 6, 18, tzinfo=UTC),
            "policy_rules": ["DSP-01"],
        }
    plan = ResponsePlan.model_validate(fields)
    built = build_reply(plan, language=language, country=country)
    assert built.used_template and not built.violations
    assert "2" in built.plan.reply and "[VERIFIED_AMOUNT]" not in built.plan.reply


def test_unverified_number_and_merchant_identifier_are_never_exempted() -> None:
    assert "phone" in scan_dlp("Teléfono 1234567890")
    assert not verify_draft("Teléfono 1234567890", [], ()).safe
    transaction = TransactionView(
        handle="txn_1",
        transaction_date=datetime(2026, 6, 15, tzinfo=UTC),
        transaction_type="Purchase",
        amount=2000000,
        currency="COP",
        merchant="Teléfono 1234567890",
        status="Approved",
    )
    plan = ResponsePlan(
        response_type="offer_dispute",
        outcome="awaiting_dispute_decision",
        reply="",
        transaction=transaction,
    )
    with pytest.raises(ValueError, match="grounding"):
        build_reply(plan, language="es", country="CO")


def test_actual_approved_reply_uses_canonical_money_but_does_not_hide_other_identifiers() -> None:
    transaction = TransactionView(
        handle="txn_1",
        transaction_date=datetime(2026, 6, 15, tzinfo=UTC),
        transaction_type="Purchase",
        amount=2000000,
        currency="COP",
        merchant="Comercio de Ensayo",
        status="Approved",
    )
    reply = "El cargo de 2000000.00 COP aparece aprobado."
    plan = ResponsePlan(
        response_type="explain_status", outcome="explained", reply=reply, transaction=transaction
    )
    assert build_reply(plan, language="es").plan.reply == reply
    with pytest.raises(ValueError, match="sensitive"):
        build_reply(
            plan.model_copy(update={"reply": reply + " Teléfono 1234567890."}), language="es"
        )
    # Even a merchant matching the monetary slot remains independently scanned.
    plan = plan.model_copy(
        update={
            "response_type": "offer_dispute",
            "outcome": "awaiting_dispute_decision",
            "reply": "",
            "transaction": transaction.model_copy(
                update={"amount": 200000000, "merchant": "$200.000.000,00"}
            ),
        }
    )
    with pytest.raises(ValueError, match="grounding"):
        build_reply(plan, language="es", country="CO")
