"""Structured NLU plus deterministic slot normalization; authority remains in code."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from aclara.agent.contracts import Intent, NluFrame
from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.nlu.rules import classify, normalize_text
from aclara.llm.client import StructuredClient
from aclara.llm.prompts import data_block, load_prompt
from aclara.llm.types import ModelFailure


class ExtractedNlu(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Literal["es", "pt", "mixed", "other"]
    dialect_hint: Literal["MX", "CO", "AR", "BR", "unknown"] = "unknown"
    intent: Literal[
        "charge_inquiry",
        "dispute_charge",
        "duplicate_charge",
        "refund_or_reversal_status",
        "card_lost_or_fraud",
        "dispute_status",
        "human_request",
        "fee_dispute",
        "out_of_scope",
    ]
    intent_confidence: float = Field(ge=0.0, le=1.0)
    amount_expr: str | None = None
    currency_expr: str | None = None
    date_expr: str | None = None
    merchant_expr: str | None = None
    type_expr: str | None = None
    product_hint: str | None = None
    country_expr: str | None = None
    count_expr: str | None = None
    customer_confirms: Literal["yes", "no", "unclear"] | None = None
    human_requested: bool = False
    lost_stolen: bool = False
    regulator: bool = False
    legal: bool = False
    distress: bool = False
    injection_suspected: bool = False
    other_customer_reference: bool = False
    out_of_scope_topic: str | None = None


class NormalizedSlots(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    amount_value: Decimal | None = None
    currency: Literal["USD", "COP", "ARS", "MXN", "BRL"] | None = None
    date_start: date | None = None
    date_end: date | None = None
    merchant_expr: str | None = None
    type_expr: str | None = None
    product_hint: str | None = None
    country_expr: str | None = None
    count_expr: str | None = None


class NluResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    frame: NluFrame
    extracted: ExtractedNlu
    slots: NormalizedSlots
    clarification: Literal["currency", "amount", "date", "language"] | None = None
    degraded: bool = False


_INTENT_MAP: dict[str, Intent] = {
    "charge_inquiry": Intent.CHARGE_INQUIRY,
    "dispute_charge": Intent.DISPUTE_CHARGE,
    "duplicate_charge": Intent.DISPUTE_CHARGE,
    "refund_or_reversal_status": Intent.CHARGE_INQUIRY,
    "card_lost_or_fraud": Intent.FRAUD,
    "dispute_status": Intent.CHARGE_INQUIRY,
    "human_request": Intent.HUMAN_REQUEST,
    "fee_dispute": Intent.FEE_DISPUTE,
    "out_of_scope": Intent.OUT_OF_SCOPE,
}


def parse_amount(expression: str | None, country: str | None = None) -> Decimal | None:
    if not expression:
        return None
    plain = normalize_text(expression)
    match = re.search(r"(?<!\w)(\d[\d.,]*\d|\d)(?!\w)", plain)
    if match:
        raw = match.group(1)
        if "," in raw and "." in raw:
            decimal_separator = "," if raw.rfind(",") > raw.rfind(".") else "."
            grouping_separator = "." if decimal_separator == "," else ","
            raw = raw.replace(grouping_separator, "").replace(decimal_separator, ".")
        elif re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", raw):
            raw = raw.replace(",", "").replace(".", "")
        else:
            raw = raw.replace(",", ".")
    else:
        word_values = {
            "un": "1",
            "una": "1",
            "um": "1",
            "uma": "1",
            "dos": "2",
            "dois": "2",
            "duas": "2",
            "tres": "3",
            "quatro": "4",
            "cuatro": "4",
            "cinco": "5",
            "seis": "6",
            "siete": "7",
            "sete": "7",
        }
        raw = next(
            (value for word, value in word_values.items() if re.search(rf"\b{word}\b", plain)), ""
        )
        if not raw:
            return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None
    country_upper = (country or "").upper()
    if "palo" in plain and country_upper == "CO":
        value *= 1_000_000
    elif ("luca" in plain and country_upper == "AR") or (
        "conto" in plain and country_upper == "BR"
    ):
        value *= 1_000
    # MX lana/varos and BR pila refer to money, without a numeric multiplier.
    return value


def resolve_currency(
    expression: str | None, country: str | None
) -> tuple[Literal["USD", "COP", "ARS", "MXN", "BRL"] | None, bool]:
    if not expression:
        return None, False
    plain = normalize_text(expression)
    if any(word in plain for word in ("usd", "dolar", "dollar")):
        return "USD", False
    if any(word in plain for word in ("brl", "real", "reai")):
        return "BRL", False
    if "mxn" in plain:
        return "MXN", False
    if "cop" in plain:
        return "COP", False
    if "ars" in plain:
        return "ARS", False
    if "peso" in plain or "varos" in plain or "lana" in plain:
        if country == "CO":
            return "COP", False
        if country == "AR":
            return "ARS", False
        # MX ledger accounts are USD; ask which currency/FX meaning was intended.
        return None, True
    if country == "BR" and any(word in plain for word in ("conto", "pila")):
        return "BRL", False
    return None, True


def parse_relative_date(expression: str | None, bank_clock: datetime) -> tuple[date, date] | None:
    if not expression:
        return None
    if bank_clock.tzinfo is None:
        raise ValueError("BANK_CLOCK must be timezone-aware")
    business_day = (
        bank_clock.astimezone(timezone(timedelta(hours=-6))) - timedelta(microseconds=1)
    ).date()
    plain = normalize_text(expression)
    offsets = {
        "hoy": 0,
        "hoje": 0,
        "ayer": 1,
        "ontem": 1,
        "anteayer": 2,
        "anteontem": 2,
    }
    for word, days in offsets.items():
        if re.search(rf"\b{word}\b", plain):
            day = business_day - timedelta(days=days)
            return day, day
    if "semana pasada" in plain or "semana passada" in plain:
        return business_day - timedelta(days=7), business_day - timedelta(days=1)
    if "hace" in plain or "faz" in plain:
        match = re.search(r"(?:hace|faz)(?: como)? (\d+) (dia|semana)", plain)
        if match:
            n = int(match.group(1)) * (7 if match.group(2) == "semana" else 1)
            day = business_day - timedelta(days=n)
            return day, day
        if "una semana" in plain or "uma semana" in plain:
            day = business_day - timedelta(days=7)
            return day, day
    weekdays = {
        "lunes": 0,
        "segunda": 0,
        "martes": 1,
        "terca": 1,
        "miercoles": 2,
        "quarta": 2,
        "jueves": 3,
        "quinta": 3,
        "viernes": 4,
        "sexta": 4,
        "sabado": 5,
        "domingo": 6,
    }
    if "pasad" in plain:
        for word, weekday in weekdays.items():
            if re.search(rf"\b{word}\b", plain):
                delta = (business_day.weekday() - weekday) % 7 or 7
                day = business_day - timedelta(days=delta)
                return day, day
    iso = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", plain)
    if iso:
        try:
            day = date.fromisoformat(iso.group(1))
        except ValueError:
            return None
        return day, day
    return None


def _fallback_extract(message: str) -> ExtractedNlu:
    frame = classify(message)
    amount = re.search(
        r"\b\d+(?:[.,]\d+)?\s*(?:pesos?|dolares?|reais|lucas?|palos?|contos?|varos?|pila)?",
        normalize_text(message),
    )

    currency = re.search(
        r"\b(?:pesos?|dolares?|reais|usd|cop|ars|mxn|brl|varos?|lana)\b", normalize_text(message)
    )
    date_expr = next(
        (
            term
            for term in (
                "anteayer",
                "anteontem",
                "ayer",
                "ontem",
                "hoy",
                "hoje",
                "semana pasada",
                "semana passada",
                "hace una semana",
                "faz uma semana",
            )
            if term in normalize_text(message)
        ),
        None,
    )
    return ExtractedNlu(
        language=frame.language,
        intent=frame.intent.value,
        intent_confidence=frame.confidence,
        amount_expr=amount.group(0) if amount else None,
        currency_expr=currency.group(0) if currency else None,
        date_expr=date_expr,
        human_requested=frame.intent == Intent.HUMAN_REQUEST,
    )


def _explicit_human_request(message: str) -> bool:
    plain = normalize_text(message)
    return bool(
        re.search(
            r"\b(?:hablar|falar|contactar|conectar|quiero|preciso|necesito)\b"
            r".{0,50}\b(?:persona|pessoa|humano|agente|atendente)\b",
            plain,
        )
    )


def postprocess(extracted: ExtractedNlu, *, country: str | None, bank_clock: datetime) -> NluResult:
    language = extracted.language
    intent = _INTENT_MAP[extracted.intent]
    confidence = extracted.intent_confidence
    if extracted.human_requested:
        intent, confidence = Intent.HUMAN_REQUEST, 1.0
    if language == "pt" and extracted.intent == "charge_inquiry":
        merchant = normalize_text(extracted.merchant_expr or "")
        if merchant == "cargo" or extracted.out_of_scope_topic == "job":
            intent, confidence = Intent.OUT_OF_SCOPE, min(confidence, 0.5)
    public_language: Literal["es", "pt"] = "pt" if language == "pt" else "es"
    currency, ambiguous = resolve_currency(extracted.currency_expr, country)
    dates = parse_relative_date(extracted.date_expr, bank_clock)
    slots = NormalizedSlots(
        amount_value=parse_amount(extracted.amount_expr, country),
        currency=currency,
        date_start=dates[0] if dates else None,
        date_end=dates[1] if dates else None,
        merchant_expr=extracted.merchant_expr,
        type_expr=extracted.type_expr,
        product_hint=extracted.product_hint,
        country_expr=extracted.country_expr,
        count_expr=extracted.count_expr,
    )
    clarification: Literal["currency", "amount", "date", "language"] | None = None
    if language in {"mixed", "other"}:
        clarification = "language"
    elif ambiguous:
        clarification = "currency"
    elif extracted.amount_expr and slots.amount_value is None:
        clarification = "amount"
    elif extracted.date_expr and dates is None:
        clarification = "date"
    return NluResult(
        frame=NluFrame(language=public_language, intent=intent, confidence=confidence),
        extracted=extracted,
        slots=slots,
        clarification=clarification,
    )


def understand(
    message: str,
    *,
    country: str | None,
    bank_clock: datetime,
    client: StructuredClient | None = None,
    prompt_path: Path | None = None,
) -> NluResult:
    if client is None or (client.models["nlu"].provider == "mock" and not client.mock_configured):
        return postprocess(
            _fallback_extract(message), country=country, bank_clock=bank_clock
        ).model_copy(update={"degraded": True})
    prompt = load_prompt(prompt_path or Path("prompts/nlu/v1.md"))
    try:
        extracted = client.generate(
            "nlu",
            prompt.text,
            data_block("customer_message", redact_for_model(message)),
            ExtractedNlu,
            prompt_id=f"{prompt.id}@{prompt.version}",
            prompt_hash=prompt.content_hash,
        )
        if _explicit_human_request(message):
            extracted = extracted.model_copy(
                update={"intent": "human_request", "human_requested": True}
            )
        return postprocess(extracted, country=country, bank_clock=bank_clock)
    except ModelFailure:
        return postprocess(
            _fallback_extract(message), country=country, bank_clock=bank_clock
        ).model_copy(update={"degraded": True})
