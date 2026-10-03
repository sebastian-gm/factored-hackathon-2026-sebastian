"""Structured NLU plus deterministic slot normalization; authority remains in code."""

from __future__ import annotations

import json
import logging
import os
import re
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from typesafe_sdk import RetryPolicy, TypeSafeClient

from aclara.agent.contracts import Intent, NluFrame
from aclara.agent.nlg.grounding import money_expressions, redact_for_model, scan_dlp
from aclara.agent.nlu.rules import classify_nlu, normalize_text
from aclara.agent.nlu.transaction_types import normalize_transaction_type
from aclara.agent.nlu.word_amounts import parse_spoken_money, parse_word_amount
from aclara.llm.client import StructuredClient
from aclara.llm.prompts import data_block, load_prompt
from aclara.llm.types import BudgetFailure, CallRecord, ModelFailure
from aclara.llm.typesafe import MODEL_ID as JEV_MODEL_ID
from aclara.llm.typesafe import TypedJudgments, TypeSafeAdapter
from aclara.llm.typesafe_questions import (
    QUESTION_SOURCE_HASH,
    QUESTION_VERSION,
    RISK_CUES,
    risk_questions,
)

LOGGER = logging.getLogger(__name__)
JEV_RESERVE_USD = 0.01
JEV_WAIT_SECONDS = 3.0


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
    recognition: Literal["recognized", "denied", "unsure"] | None = None
    unfamiliar_charge: bool = False
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
    if re.search(r"\bcentavos?\b", plain):
        # A fractional expression must parse completely, including its units;
        # falling through would silently take just its first integer.
        return parse_spoken_money(plain)
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
        words = parse_word_amount(plain)
        if words is None:
            return None
        raw = str(words)
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None
    country_upper = (country or "").upper()
    numeric_scale = (
        re.match(r"\s*(mil millones|millon(?:es)?|milhao|milhoes|mil)\b", plain[match.end() :])
        if match
        else None
    )
    if numeric_scale:
        scale = numeric_scale[1]
        value *= (
            1_000_000_000 if scale == "mil millones" else 1_000 if scale == "mil" else 1_000_000
        )
    elif "palo" in plain and country_upper in {"CO", "CL"}:
        value *= 1_000_000
    elif ("luca" in plain and country_upper in {"AR", "CL", "CO"}) or (
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
    if "pasad" in plain or "passad" in plain:
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
    # A stated day/month is exact within the current bank year when already
    # past; a future date without a year remains ambiguous instead of inventing
    # a previous year. Impossible dates also remain clarification candidates.
    months = {
        "enero": 1,
        "janeiro": 1,
        "febrero": 2,
        "fevereiro": 2,
        "marzo": 3,
        "marco": 3,
        "abril": 4,
        "mayo": 5,
        "maio": 5,
        "junio": 6,
        "junho": 6,
        "julio": 7,
        "julho": 7,
        "agosto": 8,
        "septiembre": 9,
        "setiembre": 9,
        "setembro": 9,
        "octubre": 10,
        "outubro": 10,
        "noviembre": 11,
        "novembro": 11,
        "diciembre": 12,
        "dezembro": 12,
    }
    stated = re.fullmatch(
        r"(?:(?:el|del|dia|do dia) )?(\d{1,2}|[a-z]+(?: [a-z]+)*) de "
        r"([a-z]+)(?: (?:de )?(20\d{2}))?",
        plain.strip(" .,!¿?¡"),
    )
    if stated and stated[2] in months:
        if _SPOKEN_UNIT.search(stated[1]):
            return None  # Amount units cannot turn an ill-formed phrase into a date.
        day_value = int(stated[1]) if stated[1].isdigit() else parse_word_amount(stated[1])
        if day_value is None or not 1 <= day_value <= 31:
            return None
        try:
            day = date(int(stated[3] or business_day.year), months[stated[2]], int(day_value))
        except ValueError:
            return None
        if stated[3] is None and day > business_day:
            return None
        return day, day
    return None


def _fallback_recognition(message: str) -> Literal["recognized", "denied", "unsure"] | None:
    """Conservative recognition cue for a degraded reply in the waiting state."""
    plain = normalize_text(message).strip(" .,!¿?¡")
    if plain in {"si", "no", "sim", "nao"}:
        return "unsure"
    denied = bool(
        re.search(
            r"\b(?:no fui yo|no (?:la )?hice|no pague|no compre|ni pise|"
            r"sigo sin reconocer|quiero (?:disput|desconoc|reclam)|"
            r"(?:abr|pid).*disputa|nao fui eu|nao passei|nao autorizei|"
            r"nao comprei|ainda nao reconheco|quero contestar)\b",
            _DECLINED_OFFER.sub("", plain),
        )
    )
    recognized = bool(
        re.search(
            r"\b(?:ya (?:caigo|me acorde|recorde|lo ubique)|"
            r"ahora (?:cache|me acorde|entendi)|si la hice yo|"
            r"la compra era mia|compra mia|fui yo quien pago|"
            r"(?:agora|ja) (?:lembrei|caiu a ficha|entendi)|"
            r"fui eu que comprei|essa compra foi minha|eu fiz essa compra|"
            r"fui eu mesmo|eu tinha feito essa compra)\b",
            plain,
        )
    )
    if denied and recognized:
        return "unsure"
    if denied:
        return "denied"
    if recognized:
        return "recognized"
    if any(term in plain for term in ("no se", "no recuerdo", "nao sei", "nao lembro")):
        return "unsure"
    return None


_CHARGE_REFERENT = re.compile(
    r"\b(?:cargo|cobro|compra|movimiento|consumo|pago|cobranca|lancamento|debito|transacao)\b"
)
_UNFAMILIAR_CUE = re.compile(
    r"\b(?:no (?:reconozco|reconoci|ubico|recuerdo|me suena|cacho|se que|se de donde|"
    r"tengo idea|me cuadra)|desconozco|"
    r"nao (?:reconheco|reconheci|lembro|sei que|sei de onde|faco ideia|conheco)|"
    r"nem lembro|nao me recordo)\b"
)
_STRONG_UNFAMILIAR_CUE = re.compile(
    r"\b(?:no (?:reconozco|me suena|ubico|recuerdo|cacho)|"
    r"nao (?:reconheco|conheco|lembro|faco ideia))\b"
)
_EXPLICIT_DENIAL_CUE = re.compile(
    r"\b(?:no fui yo|no fui[, ]+po|no (?:la hice|lo hice|hice|compre|pague|autorice|pase)|"
    r"ni (?:pise|pase)|no he (?:comprado|estado|pasado)|"
    r"nao fui eu|nao (?:fiz|comprei|paguei|autorizei|passei))\b"
)
_FILING_REQUEST_CUE = re.compile(
    r"\b(?:quiero (?:disputar|contestar|reclamar|abrir (?:una )?disputa)|"
    r"quero (?:contestar|reclamar|abrir (?:uma )?contestacao))\b"
)
_DECLINED_OFFER = re.compile(
    r"\b(?:prefiero no|no quiero|prefiro nao|nao quero) "
    r"(?:abrir|iniciar|presentar|registrar|seguir con|continuar con) "
    r"(?:(?:una|la|uma|a) )?(?:disputa|reclamo|reclamacion|contestacao)\b"
)
_SPOKEN_UNIT = re.compile(
    r"\b(?:lucas?|palos?|contos?|pila|varos?|lana|pesos?|reais|dolares?|centavos?|usd|brl|cop|ars|mxn)\b"
)
_CHARGE_TERM = r"(?:cargo|cobro|cobranza|cobranca|consumo|compra|lancamento|debito|transacao)"
_CHARGE_ARTICLE = r"(?:(?:este|esta|ese|esa|el|la|los|las|un|una|o|a|os|as|um|uma|esse|essa) )?"
_CHARGE_MERCHANT = (
    r"(?: (?:de la|de los|de las|del|de|do|da|dos|das|na|no|em) "
    r"[a-z0-9][a-z0-9 .&'/-]*)?"
)
_NAMED_CHARGE = _CHARGE_ARTICLE + _CHARGE_TERM + _CHARGE_MERCHANT
_NEUTRAL_CHARGE_QUESTION = re.compile(
    r"^\s*[¿¡]?\s*(?:"
    rf"que es {_NAMED_CHARGE}|"
    rf"o que e {_NAMED_CHARGE}|"
    rf"por que aparece {_NAMED_CHARGE}|"
    rf"por que (?:(?:{_NAMED_CHARGE} )?"
    r"(?:esta|sigue|continua) (?:como )?(?:pendiente|pendente|aprobado|aprovado|"
    r"rechazado|recusado|revertido|revertida|estornado)|"
    rf"{_NAMED_CHARGE} (?:esta|sigue|continua) (?:como )?"
    r"(?:pendiente|pendente|aprobado|aprovado|rechazado|recusado|revertido|"
    r"revertida|estornado)))\s*[?!.]*\s*$"
)


def _bare_unfamiliarity(message: str) -> bool:
    """Recognize explicit non-recognition while ignoring ordinary charge questions."""
    plain = normalize_text(message)
    if _STRONG_UNFAMILIAR_CUE.search(plain):
        return True
    has_charge = bool(_CHARGE_REFERENT.search(plain))
    return bool(
        _UNFAMILIAR_CUE.search(plain)
        and (
            has_charge
            or re.search(r"\b(?:esta|este|ese|essa|isso|de donde salio|de onde veio)\b", plain)
        )
    )


def _fallback_extract(message: str, *, awaiting_recognition: bool = False) -> ExtractedNlu:
    frame = classify_nlu(message)
    if frame.intent not in {Intent.HUMAN_REQUEST, Intent.FRAUD, Intent.FEE_DISPUTE}:
        plain = normalize_text(message)
        if _EXPLICIT_DENIAL_CUE.search(plain):
            frame = frame.model_copy(update={"intent": Intent.DISPUTE_CHARGE, "confidence": 0.93})
        elif frame.intent == Intent.OUT_OF_SCOPE and _bare_unfamiliarity(message):
            frame = frame.model_copy(update={"intent": Intent.CHARGE_INQUIRY, "confidence": 0.82})
    amount = re.search(
        r"\b\d+(?:[.,]\d+)*\s*(?:pesos?|dolares?|reais|lucas?|palos?|contos?|varos?|pila)?",
        normalize_text(redact_for_model(message)),
    )
    if len(money_expressions(message)) > 1:
        amount = None

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
        recognition=_fallback_recognition(message) if awaiting_recognition else None,
        unfamiliar_charge=_bare_unfamiliarity(message) if not awaiting_recognition else False,
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


_UNAVAILABLE_AMOUNT = re.compile(
    r"\b(?:no (?:se|recuerdo|conozco)|nao (?:sei|lembro|recordo)) "
    r"(?:(?:el|o|qual e o) )?(?:monto|importe|valor)(?: exacto| exato)?\b"
)
_STATUS_DURATION = re.compile(
    r"\b(?:ya llevan?|ja faz|(?:esta|continua) ha) "
    r"(?P<duration>[^.;?!]+?\b(?:dias?|semanas?)\b)"
)


def _is_status_duration(expression: str | None, message: str | None, intent: str) -> bool:
    if not expression or not message or intent != "charge_inquiry":
        return False
    plain = normalize_text(message)
    if not re.search(r"\b(?:pendiente|pendente)\b", plain):
        return False
    value = normalize_text(expression).strip(" .,!¿?¡")
    return any(
        value in {match.group(0), match.group("duration")}
        for match in _STATUS_DURATION.finditer(plain)
    )


def postprocess(
    extracted: ExtractedNlu,
    *,
    country: str | None,
    bank_clock: datetime,
    awaiting_recognition: bool = False,
    message: str | None = None,
) -> NluResult:
    if message is not None:
        raw_money = money_expressions(message)
        # Parse original local evidence, independently of provider redaction or
        # extraction. Multiple amounts still require disambiguation by the model.
        if (
            len(raw_money) == 1
            and normalize_text(raw_money[0]) not in normalize_text(extracted.merchant_expr or "")
            and parse_amount(raw_money[0], country) is not None
        ):
            extracted = extracted.model_copy(update={"amount_expr": raw_money[0]})
    # Declining an offer is not a claim that the customer made the purchase.
    # Cancellation itself remains the state machine's responsibility. Preserve
    # actual recollection when the same message also declines filing.
    if (
        awaiting_recognition
        and message is not None
        and extracted.recognition == "recognized"
        and _DECLINED_OFFER.search(normalize_text(message))
        and _fallback_recognition(message) != "recognized"
    ):
        extracted = extracted.model_copy(
            update={"recognition": "unsure", "customer_confirms": None}
        )
    language = extracted.language
    intent = _INTENT_MAP[extracted.intent]
    confidence = extracted.intent_confidence
    if not awaiting_recognition and extracted.recognition is not None:
        extracted = extracted.model_copy(update={"recognition": None})
    elif awaiting_recognition and intent not in {
        Intent.HUMAN_REQUEST,
        Intent.FRAUD,
        Intent.FEE_DISPUTE,
    }:
        if extracted.recognition == "denied":
            intent = Intent.DISPUTE_CHARGE
        elif extracted.recognition in {"recognized", "unsure"}:
            intent = Intent.CHARGE_INQUIRY
    if extracted.human_requested:
        intent, confidence = Intent.HUMAN_REQUEST, 1.0
    if language == "pt" and extracted.intent == "charge_inquiry":
        merchant = normalize_text(extracted.merchant_expr or "")
        if merchant == "cargo" or extracted.out_of_scope_topic == "job":
            intent, confidence = Intent.OUT_OF_SCOPE, min(confidence, 0.5)
    unfamiliar_charge = extracted.unfamiliar_charge
    if message is not None:
        bare_cue = _bare_unfamiliarity(message)
        if intent not in {Intent.HUMAN_REQUEST, Intent.FRAUD, Intent.FEE_DISPUTE}:
            if _EXPLICIT_DENIAL_CUE.search(normalize_text(message)):
                intent = Intent.DISPUTE_CHARGE
            elif intent == Intent.OUT_OF_SCOPE and bare_cue:
                intent = Intent.CHARGE_INQUIRY
        # Preserve a valid model flag for paraphrases. Only neutral questions and
        # explicit denials are deterministic overrides of that judgment.
        if _NEUTRAL_CHARGE_QUESTION.search(normalize_text(message)) or _EXPLICIT_DENIAL_CUE.search(
            normalize_text(message)
        ):
            unfamiliar_charge = False
    if (
        awaiting_recognition
        or intent != Intent.CHARGE_INQUIRY
        or extracted.intent in {"refund_or_reversal_status", "dispute_status"}
        or (message is not None and _FILING_REQUEST_CUE.search(normalize_text(message)))
    ):
        unfamiliar_charge = False
    if extracted.unfamiliar_charge != unfamiliar_charge:
        extracted = extracted.model_copy(update={"unfamiliar_charge": unfamiliar_charge})
    public_language: Literal["es", "pt"] = "pt" if language == "pt" else "es"
    currency, ambiguous = resolve_currency(extracted.currency_expr, country)
    if not extracted.currency_expr and _SPOKEN_UNIT.search(
        normalize_text(extracted.amount_expr or "")
    ):
        # Reuse only units present in the extracted spoken amount. Do not infer
        # a currency from the country, merchant, or an unqualified number.
        currency, ambiguous = resolve_currency(extracted.amount_expr, country)
    date_expr = (
        None
        if _is_status_duration(extracted.date_expr, message, extracted.intent)
        else extracted.date_expr
    )
    dates = parse_relative_date(date_expr, bank_clock)
    # MATCH compares exact ledger enums. Preserve the raw expression for audit,
    # but only pass a canonical kind or missing evidence into its unchanged model.
    transaction_type = normalize_transaction_type(extracted.type_expr)
    slots = NormalizedSlots(
        amount_value=parse_amount(extracted.amount_expr, country),
        currency=currency,
        date_start=dates[0] if dates else None,
        date_end=dates[1] if dates else None,
        merchant_expr=extracted.merchant_expr,
        type_expr=transaction_type,
        product_hint=extracted.product_hint,
        country_expr=extracted.country_expr,
        count_expr=extracted.count_expr,
    )
    clarification: Literal["currency", "amount", "date", "language"] | None = None
    if language in {"mixed", "other"}:
        clarification = "language"
    elif ambiguous:
        clarification = "currency"
    elif (
        extracted.amount_expr
        and slots.amount_value is None
        or (
            slots.amount_value is None
            and message is not None
            and intent in {Intent.CHARGE_INQUIRY, Intent.DISPUTE_CHARGE}
            and _UNAVAILABLE_AMOUNT.search(normalize_text(message))
        )
    ):
        clarification = "amount"
    elif date_expr and dates is None:
        clarification = "date"
    return NluResult(
        frame=NluFrame(language=public_language, intent=intent, confidence=confidence),
        extracted=extracted,
        slots=slots,
        clarification=clarification,
    )


def _ask_jev_risks(message: str, key: str) -> TypedJudgments:
    with TypeSafeClient(
        api_key=key,
        model=JEV_MODEL_ID,
        retry=RetryPolicy(max_retries=0),
        timeout=2.5,
    ) as raw:
        return TypeSafeAdapter(raw).ask(
            {"customer_message": redact_for_model(message)}, risk_questions()
        )


def _risk_flags(extracted: ExtractedNlu) -> dict[str, bool]:
    return {cue: bool(getattr(extracted, cue)) for cue in RISK_CUES}


def _record_risk_opinion(
    client: StructuredClient,
    extracted: ExtractedNlu,
    result: TypedJudgments | None,
    *,
    degradation: str | None,
    reserve_usd: float,
    reservation: str | None,
    latency_ms: float,
    primary_failed: bool,
) -> ExtractedNlu:
    gemini_flags = _risk_flags(extracted)
    raw_jev_probabilities = result.nouls if result is not None else None
    jev_probabilities = raw_jev_probabilities
    if jev_probabilities is not None and set(jev_probabilities) != set(RISK_CUES):
        degradation, jev_probabilities = "incomplete_risk_answers", None
    jev_flags = (
        {cue: probability >= 0.5 for cue, probability in jev_probabilities.items()}
        if jev_probabilities is not None
        else None
    )
    union = {
        cue: gemini_flags[cue] or (jev_flags[cue] if jev_flags and not primary_failed else False)
        for cue in RISK_CUES
    }
    record = CallRecord(
        route="nlu_risk_second_opinion",
        provider="typesafe",
        model_id=JEV_MODEL_ID,
        prompt_id=QUESTION_VERSION,
        prompt_hash=QUESTION_SOURCE_HASH,
        input_tokens=(result.input_tokens or 0) if result else 0,
        output_tokens=(result.output_tokens or 0) if result else 0,
        cache_read_tokens=0,
        cache_write_tokens=0,
        latency_ms=result.latency_ms if result else latency_ms,
        cost_usd=result.cost_usd if result else (None if reserve_usd else 0.0),
        stop_reason=None,
        status="valid"
        if jev_probabilities is not None
        else "provider_error"
        if reserve_usd
        else "skipped",
        attempt=1,
        judgments={
            "primary_model_id": client.models["nlu"].model_id,
            "primary_raw_flags": gemini_flags,
            # Keep the historical key for record readers. The additive primary
            # identity/flags above identify a development challenger correctly.
            "gemini_raw_flags": gemini_flags,
            # Prompt v4 requests booleans; it exposes no per-cue Gemini probabilities.
            "gemini_raw_probabilities": {cue: None for cue in RISK_CUES},
            "gemini_intent_confidence": extracted.intent_confidence,
            "jev_raw_probabilities": raw_jev_probabilities,
            "jev_threshold_flags": jev_flags,
            "union_flags": union,
            "threshold": 0.5,
            "degradation": degradation,
            "primary_failed": primary_failed,
        },
    )
    client.finish_external_judgment(record, reserve_usd=reserve_usd, reservation=reservation)
    if degradation:
        LOGGER.warning("Jev NLU risk second opinion degraded: %s", degradation)
    return extracted.model_copy(update=union)


def _rules_result(
    message: str,
    *,
    country: str | None,
    bank_clock: datetime,
    awaiting_recognition: bool,
) -> NluResult:
    return postprocess(
        _fallback_extract(message, awaiting_recognition=awaiting_recognition),
        country=country,
        bank_clock=bank_clock,
        awaiting_recognition=awaiting_recognition,
        message=message,
    ).model_copy(update={"degraded": True})


def understand(
    message: str,
    *,
    country: str | None,
    bank_clock: datetime,
    client: StructuredClient | None = None,
    prompt_path: Path | None = None,
    awaiting_recognition: bool = False,
    masked_charge: dict[str, str] | None = None,
) -> NluResult:
    if client is None or (client.models["nlu"].provider == "mock" and not client.mock_configured):
        return _rules_result(
            message,
            country=country,
            bank_clock=bank_clock,
            awaiting_recognition=awaiting_recognition,
        )
    prompt = load_prompt(prompt_path or Path("prompts/nlu/v5.md"))
    allowed_charge: dict[str, str] = {}
    if awaiting_recognition:
        for fact_key, value in (masked_charge or {}).items():
            if fact_key not in {"merchant", "transaction_date", "amount", "currency", "status"}:
                continue
            redacted = redact_for_model(str(value))[:160]
            allowed_charge[fact_key] = "[REDACTED]" if scan_dlp(redacted) else redacted
    context = "\n".join(
        (
            data_block(
                "record",
                json.dumps(
                    {
                        "awaiting_recognition": awaiting_recognition,
                        "selected_charge": allowed_charge,
                    },
                    ensure_ascii=False,
                ),
            ),
            data_block("customer_message", redact_for_model(message)),
        )
    )
    real_route = (
        client.models["nlu"].provider not in {"mock", "recorded"}
        and client.risk_second_opinion_enabled
    )
    future: Future[TypedJudgments] | None = None
    executor: ThreadPoolExecutor | None = None
    reserve_usd = 0.0
    reservation: str | None = None
    degradation: str | None = None
    primary_error: Exception | None = None
    started = perf_counter()
    if real_route:
        key = os.getenv("TYPESAFE_API_KEY")
        if not key:
            degradation = "missing_typesafe_key"
        else:
            try:
                reservation = client.reserve_external_judgment(JEV_RESERVE_USD)
                reserve_usd = JEV_RESERVE_USD
                executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="jev-risk")
                future = executor.submit(_ask_jev_risks, message, key)
            except BudgetFailure:
                # Denied/disabled shared budgets forbid both the second opinion
                # and the primary request. No retry or vendor fallback follows.
                LOGGER.warning("NLU degraded: shared model budget unavailable or disabled")
                return _rules_result(
                    message,
                    country=country,
                    bank_clock=bank_clock,
                    awaiting_recognition=awaiting_recognition,
                )
            except ModelFailure:
                if client.spend_gate is not None:
                    raise
                degradation = "typesafe_budget_or_approval"
            except Exception as exc:
                if client.spend_gate is not None:
                    raise
                degradation = f"typesafe_setup_{type(exc).__name__}"
    try:
        extracted = client.generate(
            "nlu",
            prompt.text,
            context,
            ExtractedNlu,
            prompt_id=f"{prompt.id}@{prompt.version}",
            prompt_hash=prompt.content_hash,
        )
        primary_failed = False
    except BudgetFailure:
        extracted = _fallback_extract(message, awaiting_recognition=awaiting_recognition)
        primary_failed = True
        LOGGER.warning("NLU degraded: primary model budget unavailable or disabled")
    except ModelFailure:
        extracted = _fallback_extract(message, awaiting_recognition=awaiting_recognition)
        primary_failed = True
    except Exception as exc:
        extracted = _fallback_extract(message, awaiting_recognition=awaiting_recognition)
        primary_failed = True
        primary_error = exc
    if real_route:
        result: TypedJudgments | None = None
        if future is not None:
            try:
                result = future.result(timeout=JEV_WAIT_SECONDS)
            except FutureTimeout:
                degradation = "typesafe_timeout"
            except Exception as exc:
                degradation = f"typesafe_{type(exc).__name__}"
            finally:
                assert executor is not None
                executor.shutdown(wait=False, cancel_futures=True)
        try:
            extracted = _record_risk_opinion(
                client,
                extracted,
                result,
                degradation=degradation,
                reserve_usd=reserve_usd,
                reservation=reservation,
                latency_ms=(perf_counter() - started) * 1000 if future is not None else 0.0,
                primary_failed=primary_failed,
            )
        except BudgetFailure:
            # The durable reservation stays retained. Never try another model
            # or turn a settlement failure into customer-facing authority.
            extracted = _fallback_extract(message, awaiting_recognition=awaiting_recognition)
            primary_failed = True
            LOGGER.warning("NLU degraded: typed judgment cost settlement unavailable")
    if primary_error is not None:
        raise primary_error
    if _explicit_human_request(message):
        extracted = extracted.model_copy(
            update={"intent": "human_request", "human_requested": True}
        )
    return postprocess(
        extracted,
        country=country,
        bank_clock=bank_clock,
        awaiting_recognition=awaiting_recognition,
        message=message,
    ).model_copy(update={"degraded": primary_failed})
