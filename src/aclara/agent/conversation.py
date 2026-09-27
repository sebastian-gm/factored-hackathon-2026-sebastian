"""Deterministic conversation guards around model observations (ADR-0015)."""

from __future__ import annotations

import re

from aclara.agent.contracts import Intent, NluFrame
from aclara.agent.nlu.rules import classify_nlu, normalize_text
from aclara.agent.nlu.structured import ExtractedNlu, NormalizedSlots
from aclara.bank.repository import Transaction


def unfamiliar_charge(message: str) -> bool:
    return bool(
        re.search(
            r"\b(no reconozco|no me suena|no ubico|no cacho de donde|nao reconheco|nao sei de onde|sigo sin reconocer|ainda nao reconheco)\b",
            normalize_text(message),
        )
    )


def risk_reasons(extracted: ExtractedNlu) -> list[str]:
    reasons = []
    if extracted.lost_stolen or extracted.intent == "card_lost_or_fraud":
        reasons.append("FRD-01")
    if extracted.legal or extracted.regulator:
        reasons.append("ESC-02")
    if extracted.distress:
        reasons.append("ESC-03")
    if extracted.human_requested or extracted.intent == "human_request":
        reasons.append("ESC-01")
    return reasons


def changes_target(message: str, row: Transaction, slots: NormalizedSlots) -> bool:
    value = normalize_text(message)
    if re.search(
        r"\b(otro cargo|otra compra|otro cobro|outra cobranca|outra compra|outro lancamento|cambiar de cargo|trocar de compra)\b",
        value,
    ):
        return True
    if slots.amount_value is not None and abs(float(slots.amount_value) - row.amount) > 0.011:
        return True
    if slots.currency and slots.currency != row.currency:
        return True
    if slots.merchant_expr:
        merchant = normalize_text(slots.merchant_expr)
        if merchant not in normalize_text(row.merchant_name):
            return True
    return bool(
        slots.date_start
        and slots.date_end
        and not slots.date_start <= row.process_date <= slots.date_end
    )


def classify_request(message: str) -> NluFrame:
    # "Someone else made it" describes a denial, not an access or human request.
    sanitized = re.sub(
        r"\b(?:lo hizo|la hizo|fue) otra persona\b", "no hice", normalize_text(message)
    )
    sanitized = re.sub(r"\b(?:foi|quem fez foi) outra pessoa\b", "nao fiz", sanitized)
    frame = classify_nlu(sanitized)
    if sanitized != normalize_text(message) and frame.intent == Intent.OUT_OF_SCOPE:
        frame = frame.model_copy(update={"intent": Intent.DISPUTE_CHARGE})
    return frame
