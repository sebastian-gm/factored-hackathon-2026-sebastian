"""Normalize stated ES/PT kind expressions to this ledger's six enum values.

Unrecognized or ambiguous expressions are missing evidence, never a new kind.
The transaction contract groups fee/commission under Adjustment (DSP-03).
"""

from __future__ import annotations

from typing import Literal

from aclara.agent.nlu.rules import normalize_text

TransactionType = Literal["Purchase", "Withdrawal", "Payment", "Transfer", "Deposit", "Adjustment"]

_ALIASES: dict[TransactionType, tuple[str, ...]] = {
    "Purchase": ("purchase", "purchases", "compra", "compras", "consumo", "consumos"),
    "Withdrawal": (
        "withdrawal",
        "withdrawals",
        "atmwithdrawal",
        "atm withdrawal",
        "retiro",
        "retiros",
        "retiro de efectivo",
        "retiro en cajero",
        "saque",
        "saques",
        "saque em dinheiro",
        "saque no caixa eletronico",
        "extraccion",
        "extracciones",
    ),
    "Payment": ("payment", "payments", "pago", "pagos", "pagamento", "pagamentos"),
    "Transfer": (
        "transfer",
        "transfers",
        "transferencia",
        "transferencias",
        "pix",
        "envio",
        "envios",
        "envio de dinero",
        "envio de dinheiro",
        "transferencia pix",
    ),
    "Deposit": ("deposit", "deposits", "deposito", "depositos", "consignacion", "consignaciones"),
    "Adjustment": (
        "adjustment",
        "adjustments",
        "ajuste",
        "ajustes",
        "fee",
        "fees",
        "commission",
        "comision",
        "comisiones",
        "comissao",
        "comissoes",
        "tarifa",
        "tarifas",
        "taxa",
        "taxas",
        "cobro de comision",
        "cobro por comision",
        "cobro de tarifa",
        "cobranca de tarifa",
        "cobranca de taxa",
        "cobranca de comissao",
        "comision bancaria",
        "tarifa bancaria",
    ),
}
_CANONICAL_BY_ALIAS = {alias: kind for kind, aliases in _ALIASES.items() for alias in aliases}


def normalize_transaction_type(expression: str | None) -> TransactionType | None:
    """Return an exact canonical alias; do not infer a kind from arbitrary prose."""
    if expression is None:
        return None
    plain = " ".join(normalize_text(expression).split())
    return _CANONICAL_BY_ALIAS.get(plain)
