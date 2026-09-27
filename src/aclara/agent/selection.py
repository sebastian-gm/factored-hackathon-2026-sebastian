"""Deterministic transaction-identification gates before any action proposal."""

from __future__ import annotations

import re

from aclara.agent.nlu import extract_amount, normalize_text, selected_candidate
from aclara.bank.repository import Transaction


def uncertain(text: str) -> bool:
    return bool(
        re.search(
            r"\b(no se|nao sei|no recuerdo|nao lembro|tal vez|talvez|no estoy segur\w*|nao tenho certeza|no puedo elegir|nao consigo escolher|ninguno|nenhum)\b",
            normalize_text(text),
        )
    )


def explicit_choice(text: str, count: int) -> int | None:
    value = normalize_text(text).strip(" .,!¿?¡")
    # A choice is a complete positive selection, not an ordinal embedded inside
    # a negation, question or competing alternatives. Models cannot override it.
    if re.fullmatch(r"[123]", value):
        index = int(value) - 1
        return index if index < count else None
    if not re.fullmatch(
        r"(?:(?:el|la|o|a) )?(?:primero|primera|primeiro|primeira|segundo|segunda|tercero|tercera|terceiro|terceira)(?: (?:cargo|compra|cobrança|cobranca|opcion|opcao))?(?:,? por favor)?",
        value,
    ):
        return None
    return selected_candidate(value, count)


def candidates(
    text: str, rows: list[tuple[str, Transaction]]
) -> tuple[list[tuple[str, Transaction]], bool]:
    """Return consistent candidates and whether explicit customer choice is needed."""
    value = normalize_text(text)
    merchants = [
        (h, r)
        for h, r in rows
        if r.merchant_name != "—" and normalize_text(r.merchant_name) in value
    ]
    amount = extract_amount(text)
    currencies = set(re.findall(r"\b(?:usd|mxn|brl|cop|ars|eur)\b", value))
    selected = merchants if merchants else rows
    if amount is not None:
        selected = [(h, r) for h, r in selected if abs(r.amount - amount) < 0.011]
    if currencies:
        selected = [(h, r) for h, r in selected if {r.currency.lower()} == currencies]
    # Unknown/missing evidence is not positive identification, including when a
    # scoped ledger happens to contain only one row.
    needs_choice = uncertain(text) or (not merchants and amount is None)
    return selected, needs_choice
