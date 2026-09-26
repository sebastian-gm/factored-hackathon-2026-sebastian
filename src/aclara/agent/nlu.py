"""Small deterministic Spanish/Portuguese NLU for the Layer 1 baseline."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum


class Intent(StrEnum):
    CHARGE_INQUIRY = "charge_inquiry"
    DISPUTE_CHARGE = "dispute_charge"
    HUMAN_REQUEST = "human_request"
    FRAUD = "card_lost_or_fraud"
    FEE_DISPUTE = "fee_dispute"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass(frozen=True, slots=True)
class NluFrame:
    language: str
    intent: Intent
    confidence: float


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def detect_language(text: str) -> str:
    normalized = normalize_text(text)
    portuguese_markers = (
        "nao ",
        "cobranca",
        "cartao",
        "fatura",
        "atendente",
        "voce",
        "pessoa",
        "preciso",
    )
    return "pt" if any(marker in normalized for marker in portuguese_markers) else "es"


def classify(text: str) -> NluFrame:
    normalized = normalize_text(text)
    language = detect_language(text)
    if any(
        term in normalized
        for term in ("perdi meu cartao", "roubaram", "robaron", "cartao roubado", "fraude")
    ):
        return NluFrame(language, Intent.FRAUD, 0.99)
    if any(
        term in normalized
        for term in (
            "persona",
            "pessoa",
            "humano",
            "agente",
            "atendente",
            "falar com alguem",
        )
    ):
        return NluFrame(language, Intent.HUMAN_REQUEST, 0.99)
    if any(term in normalized for term in ("tarifa", "fee", "cobro indebido", "cobro de tarifa")):
        return NluFrame(language, Intent.FEE_DISPUTE, 0.96)
    if any(term in normalized for term in ("no reconozco", "no hice", "nao reconheco", "nao fiz")):
        return NluFrame(language, Intent.DISPUTE_CHARGE, 0.93)
    if any(term in normalized for term in ("cargo", "cobranza", "cobranca", "compra", "cobro")):
        return NluFrame(language, Intent.CHARGE_INQUIRY, 0.82)
    return NluFrame(language, Intent.OUT_OF_SCOPE, 0.70)


def is_confirmation(text: str) -> bool:
    normalized = normalize_text(text).strip(" .,!¿?¡")
    return bool(
        re.fullmatch(
            r"(si|sim|confirmo|confirmar|de acuerdo|adelante|pode|pode seguir|pode registrar)",
            normalized,
        )
    )


def is_cancellation(text: str) -> bool:
    normalized = normalize_text(text).strip(" .,!¿?¡")
    return normalized in {"no", "nao", "cancelar", "cancela", "deixa", "deixa pra la"}


def selected_candidate(text: str, candidate_count: int) -> int | None:
    normalized = normalize_text(text)
    match = re.search(
        r"\b(el|la|o|a)?\s*(primero|primera|primeiro|primeira|segundo|segunda|tercero|tercera|terceiro|terceira)\b",
        normalized,
    )
    if not match:
        return None
    choice = match.group(2)
    index = 0 if choice in {"primero", "primera", "primeiro", "primeira"} else 1
    if choice in {"tercero", "tercera", "terceiro", "terceira"}:
        index = 2
    return index if index < candidate_count else None


def extract_amount(text: str) -> float | None:
    match = re.search(r"(?<!\w)(\d{1,6}(?:[.,]\d{1,2})?)(?!\w)", text)
    if not match:
        return None
    raw = match.group(1).replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None
