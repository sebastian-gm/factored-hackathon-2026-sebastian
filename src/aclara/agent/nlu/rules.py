"""Small deterministic Spanish/Portuguese NLU for the Layer 1 baseline."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from aclara.agent.contracts import Intent, NluFrame


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def detect_language_evidence(
    text: str, *, ignored_terms: tuple[str, ...] = ()
) -> Literal["es", "pt", "uncertain"]:
    """Conservative ES/PT evidence; names and domains carry no language vote."""
    normalized = normalize_text(text)
    normalized = re.sub(r"\b(?:https?://|www\.)?[^\s/]+\.[a-z]{2,}(?:/[^\s]*)?", " ", normalized)
    for name in sorted(ignored_terms, key=len, reverse=True):
        if name.strip():
            normalized = re.sub(rf"(?<!\w){re.escape(normalize_text(name))}(?!\w)", " ", normalized)
    words = set(re.findall(r"[a-z]+", normalized))
    # Shared/ambiguous tokens (including com and sim) cannot decide language.
    # Distinctive lexical evidence counts twice; weak function words require
    # context. Conflicting or insufficient evidence stays explicitly uncertain.
    pt_strong = {
        "nao",
        "cobranca",
        "cobrancas",
        "cartao",
        "fatura",
        "atendente",
        "voce",
        "pessoa",
        "preciso",
        "quero",
        "estou",
        "tenho",
        "sessao",
        "extrato",
        "obrigado",
        "obrigada",
        "tambem",
        "irmao",
        "pode",
        "poderia",
        "sinto",
        "ajudar",
        "agora",
        "fornecer",
        "detalhes",
        "moeda",
        "transacao",
        "transacoes",
        "pendente",
        "recusada",
        "recusado",
        "estornada",
        "estornado",
        "aprovada",
        "aprovado",
        "esclarecer",
        "lancamento",
        "estabelecimento",
        "contestacao",
        "falar",
        "foi",
    }
    es_strong = {
        "quiero",
        "necesito",
        "hablar",
        "persona",
        "tarjeta",
        "cobro",
        "monto",
        "moneda",
        "transaccion",
        "transacciones",
        "pendiente",
        "rechazada",
        "rechazado",
        "reversada",
        "reversado",
        "aprobada",
        "aprobado",
        "puedes",
        "puedo",
        "podrias",
        "datos",
        "aclarar",
        "operacion",
        "movimientos",
        "muestrame",
        "recuerdas",
        "reconozco",
        "deseas",
        "yo",
        "ayudar",
    }
    pt_weak = {
        "o",
        "a",
        "os",
        "as",
        "uma",
        "meu",
        "minha",
        "esse",
        "essa",
        "seu",
        "sua",
        "isso",
        "muito",
        "mais",
        "dele",
        "dela",
        "e",
    }
    es_weak = {"el", "la", "los", "las", "mi", "mis", "una", "un", "con", "no", "es", "y"}
    pt = 2 * len(words & pt_strong) + len(words & pt_weak)
    es = 2 * len(words & es_strong) + len(words & es_weak)
    if "¿" in normalized or "¡" in normalized:
        es += 2
    if es >= 2 and pt < 2:
        return "es"
    if pt >= 2 and es < 2:
        return "pt"
    return "uncertain"


def detect_language(text: str) -> Literal["es", "pt"]:
    """Preserve the frozen two-language interface; uncertainty uses its ES default."""
    evidence = detect_language_evidence(text)
    return "pt" if evidence == "pt" else "es"


def classify(text: str) -> NluFrame:
    normalized = normalize_text(text)
    language = detect_language(text)
    if any(
        term in normalized
        for term in (
            "perdi meu cartao",
            "perdi o meu cartao",
            "perdi o cartao",
            "roubaram",
            "robaron",
            "cartao roubado",
            "cartao perdido",
            "perdi mi tarjeta",
            "perdi la tarjeta",
            "se me perdio la tarjeta",
            "extravie mi tarjeta",
            "tarjeta robada",
            "tarjeta perdida",
            "me robaron la tarjeta",
            "fraude",
        )
    ):
        return NluFrame(language=language, intent=Intent.FRAUD, confidence=0.99)
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
        return NluFrame(language=language, intent=Intent.HUMAN_REQUEST, confidence=0.99)
    if any(term in normalized for term in ("tarifa", "fee", "cobro indebido", "cobro de tarifa")):
        return NluFrame(language=language, intent=Intent.FEE_DISPUTE, confidence=0.96)
    if any(term in normalized for term in ("no reconozco", "no hice", "nao reconheco", "nao fiz")):
        return NluFrame(language=language, intent=Intent.DISPUTE_CHARGE, confidence=0.93)
    if any(term in normalized for term in ("cargo", "cobranza", "cobranca", "compra", "cobro")):
        return NluFrame(language=language, intent=Intent.CHARGE_INQUIRY, confidence=0.82)
    return NluFrame(language=language, intent=Intent.OUT_OF_SCOPE, confidence=0.70)


def classify_nlu(text: str) -> NluFrame:
    """New NLU label rule; B1's frozen outcome classifier remains a separate baseline."""
    frame = classify(text)
    if frame.intent in {Intent.HUMAN_REQUEST, Intent.FRAUD, Intent.FEE_DISPUTE}:
        return frame
    normalized = normalize_text(text)
    denial_or_filing = (
        "no hice",
        "no fui yo",
        "no autorice",
        "nao fiz",
        "nao fui eu",
        "nao autorizei",
        "quiero disputar",
        "abrir una disputa",
        "presentar un reclamo",
        "quero contestar",
        "abrir uma contestacao",
        "registrar uma contestacao",
    )
    if any(term in normalized for term in denial_or_filing):
        return NluFrame(language=frame.language, intent=Intent.DISPUTE_CHARGE, confidence=0.93)
    if any(term in normalized for term in ("no reconozco", "nao reconheco")):
        return NluFrame(language=frame.language, intent=Intent.CHARGE_INQUIRY, confidence=0.82)
    return frame


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
