"""Positive detail constraints for an already customer-scoped set of choices."""

from __future__ import annotations

import re

from aclara.agent.nlu.money import inspect_money
from aclara.agent.nlu.rules import normalize_text
from aclara.agent.nlu.structured import NluResult, NormalizedSlots, parse_amount, resolve_currency
from aclara.agent.selection import uncertain
from aclara.bank.repository import Transaction


def details_requested(message: str) -> bool:
    return bool(
        re.search(r"\d|\b(hoy|hoje|ayer|ontem|anteayer|anteontem)\b", normalize_text(message))
    )


def has_details(slots: NormalizedSlots) -> bool:
    return any(
        value is not None
        for value in (slots.amount_value, slots.currency, slots.date_start, slots.date_end)
    )


def grounded_details(nlu: NluResult, message: str, country: str | None) -> bool:
    """Selection refinements need customer text evidence, never invented slots."""
    money = inspect_money(message)
    if nlu.slots.merchant_expr and normalize_text(nlu.slots.merchant_expr) not in normalize_text(
        message
    ):
        return False
    if nlu.slots.amount_value is not None and (
        money.needs_clarification
        or parse_amount(money.expression, country) != nlu.slots.amount_value
    ):
        return False
    if nlu.slots.currency is not None:
        currency, ambiguous = resolve_currency(money.expression or message, country)
        if ambiguous or currency != nlu.slots.currency:
            return False
    if nlu.slots.date_start is not None or nlu.slots.date_end is not None:
        date = r"(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(?:/\d{2,4})?|hoy|hoje|ayer|ontem|anteayer|anteontem)"
        if re.search(
            rf"{date}\W+(?:o|ou)\s+(?:(?:el|em|dia|foi|fue)\s+)*{date}", normalize_text(message)
        ):
            return False
        span = normalize_text(nlu.extracted.date_expr or "").strip()
        if not span or not re.search(rf"(?<!\w){re.escape(span)}(?!\w)", normalize_text(message)):
            return False
    return has_details(nlu.slots)


def consistent_details(slots: NormalizedSlots, row: Transaction) -> bool:
    return bool(
        (slots.amount_value is None or abs(float(slots.amount_value) - row.amount) <= 0.011)
        and (slots.currency is None or slots.currency == row.currency)
        and (slots.date_start is None or row.process_date >= slots.date_start)
        and (slots.date_end is None or row.process_date <= slots.date_end)
        and (
            not slots.merchant_expr
            or normalize_text(slots.merchant_expr) in normalize_text(row.merchant_name)
        )
    )


def uncertain_selection(message: str) -> bool:
    # Missing one date can still allow choices; uncertainty about identity cannot.
    value = re.sub(r"\b(no recuerdo la fecha|nao lembro a data)\b", "", normalize_text(message))
    return uncertain(value)
