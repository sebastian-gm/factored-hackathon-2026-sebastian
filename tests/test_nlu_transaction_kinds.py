"""Serving-shaped kind aliases normalize before unchanged MATCH; synthetic only."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from aclara.agent.matching import MatchState
from aclara.agent.nlu.structured import ExtractedNlu, postprocess
from aclara.agent.nlu.transaction_types import normalize_transaction_type
from aclara.bank.repository import Transaction

CLOCK = datetime(2026, 6, 18, 6, tzinfo=UTC)


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("compra", "Purchase"),
        ("compras", "Purchase"),
        ("consumo", "Purchase"),
        ("retiro", "Withdrawal"),
        ("saque", "Withdrawal"),
        ("retiro de efectivo", "Withdrawal"),
        ("pago", "Payment"),
        ("pagamento", "Payment"),
        ("pagamentos", "Payment"),
        ("transferencia", "Transfer"),
        ("transferência", "Transfer"),
        ("PIX", "Transfer"),
        ("envío", "Transfer"),
        ("depósito", "Deposit"),
        ("consignación", "Deposit"),
        ("ajuste", "Adjustment"),
        ("comisión", "Adjustment"),
        ("tarifa", "Adjustment"),
        ("cobro de comisión", "Adjustment"),
        ("cobrança de tarifa", "Adjustment"),
        ("Purchase", "Purchase"),
        ("Withdrawal", "Withdrawal"),
        ("Payment", "Payment"),
        ("Transfer", "Transfer"),
        ("Deposit", "Deposit"),
        ("Adjustment", "Adjustment"),
    ],
)
@pytest.mark.parametrize("language", ["es", "pt"])
def test_ledger_vocabulary_aliases_are_canonical_before_match(
    alias: str,
    canonical: str,
    language: str,
) -> None:
    day = datetime(2026, 6, 12, 14, tzinfo=UTC)
    country, currency = ("BR", "BRL") if language == "pt" else ("MX", "USD")
    raw = ExtractedNlu(
        language=language,
        intent="charge_inquiry",
        intent_confidence=0.9,
        amount_expr="145.50",
        currency_expr=currency,
        date_expr="2026-06-12",
        merchant_expr="Loja Modelo",
        type_expr=alias,
        product_hint="cartão de crédito" if language == "pt" else "tarjeta de crédito",
    )
    parsed = postprocess(raw, country=country, bank_clock=CLOCK)
    expected = postprocess(
        raw.model_copy(update={"type_expr": canonical}), country=country, bank_clock=CLOCK
    )
    assert parsed.slots.type_expr == canonical
    assert parsed.extracted.type_expr == alias  # raw extraction remains auditable
    row = Transaction(
        "authored-row",
        "authored-customer",
        "authored-card",
        day,
        day.date(),
        canonical,
        145.50,
        currency,
        "Loja Modelo",
        "Approved",
    )
    candidates = [("txn_1", row)]
    match = MatchState()
    decision = match.match(parsed.slots, candidates, row.customer_id, CLOCK)
    reference = match.match(expected.slots, candidates, row.customer_id, CLOCK)
    assert decision == reference
    assert decision.action == "propose" and decision.transaction_ids == ("txn_1",)


@pytest.mark.parametrize(
    "kind",
    [
        None,
        "cargo",
        "cobrança",
        "charge",
        "refund",
        "extraña",
        "cartão de crédito",
        "compra ou saque",
        "MysteryKind",
    ],
)
def test_unknown_generic_or_ambiguous_kind_is_null(kind: str | None) -> None:
    result = postprocess(
        ExtractedNlu(language="pt", intent="charge_inquiry", intent_confidence=0.9, type_expr=kind),
        country="BR",
        bank_clock=CLOCK,
    )
    assert result.slots.type_expr is None


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("  TRANSFERÊNCIA  ", "Transfer"),
        ("comissão", "Adjustment"),
        ("COBRO   DE   COMISIÓN", "Adjustment"),
        ("taxas", "Adjustment"),
        ("Fee", "Adjustment"),
        ("consumos", "Purchase"),
        ("saques", "Withdrawal"),
    ],
)
def test_kind_aliases_handle_case_accents_spacing_and_plurals(alias: str, canonical: str) -> None:
    assert normalize_transaction_type(alias) == canonical


def test_normalizer_vocabulary_matches_committed_transaction_contract() -> None:
    from pathlib import Path

    import yaml

    contract = yaml.safe_load(Path("contracts/transactions.yaml").read_text())
    assert {
        normalize_transaction_type(kind) for kind in contract["columns"]["transaction_type"]["enum"]
    } == {"Purchase", "Withdrawal", "Transfer", "Payment", "Deposit", "Adjustment"}


@pytest.mark.parametrize("language", ["es", "pt"])
def test_stated_purchase_alias_avoids_an_unnecessary_serving_choice(language: str) -> None:
    day = datetime(2026, 6, 12, 14, tzinfo=UTC)
    raw = ExtractedNlu(
        language=language,
        intent="charge_inquiry",
        intent_confidence=0.9,
        merchant_expr="Loja Modelo",
        type_expr="compra",
        product_hint="cartão de crédito" if language == "pt" else "tarjeta de crédito",
    )
    rows = [
        (
            "txn_1",
            Transaction(
                "authored-purchase",
                "authored-customer",
                "authored-card",
                day,
                day.date(),
                "Purchase",
                145.50,
                "BRL",
                "Loja Modelo",
                "Approved",
            ),
        ),
        (
            "txn_2",
            Transaction(
                "authored-withdrawal",
                "authored-customer",
                "authored-card",
                day - timedelta(days=1),
                (day - timedelta(days=1)).date(),
                "Withdrawal",
                299.00,
                "BRL",
                "Cajero Modelo",
                "Approved",
            ),
        ),
    ]
    normalized = postprocess(raw, country="BR", bank_clock=CLOCK).slots
    matcher = MatchState()
    old = matcher.match(
        normalized.model_copy(update={"type_expr": "compra"}), rows, "authored-customer", CLOCK
    )
    fixed = matcher.match(normalized, rows, "authored-customer", CLOCK)
    assert old.action == "choose"
    assert fixed.action == "propose" and fixed.transaction_ids == ("txn_1",)
