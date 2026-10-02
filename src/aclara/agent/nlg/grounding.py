"""Fact citation and DLP checks for every customer-facing draft."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class AllowedFact:
    id: str
    value: str
    source: str


@dataclass(frozen=True, slots=True)
class Verdict:
    safe: bool
    violations: tuple[str, ...]


_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE = re.compile(r"(?<!\w)(?:\+\d{1,3}[ .-]?)?(?:\d[ .-]?){9,14}(?!\w)")
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_DOCUMENT = re.compile(r"(?<!\w)\d{8,12}(?!\w)")
_HANDLE = re.compile(r"\b(?:txn|card|prod|cust)_\d+\b", re.I)
# UTF-8 decoded as Latin-1/Windows-1252, replacement characters, and a narrow
# word-internal ASCII corruption signature. Ordinary ES/PT accents remain valid.
_CORRUPTION = re.compile(
    r"\ufffd|(?:Ã|Â)[\u0080-\u00bf]|â(?:€|[\u0080-\u009f])|(?<=\w)['’]#(?=[A-Za-z])"
)
_CASE = re.compile(r"\b(?:DSP|HO)-[A-Z0-9-]+\b", re.I)
_MASKED_CARD = re.compile(r"(?:[Xx]{2,}|[*•]{2,})[ -]?\d{2,4}(?:[Xx*•]{2,})?")
_WORD_DIGIT = re.compile(r"[^\W\d_]\d+[^\W\d_]", re.UNICODE)
# Machine identifiers stay internal, including future/private snake_case names.
_MACHINE_IDENTIFIER = re.compile(r"(?<!\w)_*[A-Za-z][A-Za-z0-9]*(?:_+[A-Za-z0-9]+)+_*(?!\w)")
_RAW_ENUM = re.compile(
    r"\b(?:approved|pending|declined|reversed|authorized|posted|settled|processing|"
    r"completed|failed|rejected|cancelled|canceled|purchase|withdrawal|deposit|"
    r"payment|transfer|refund|adjustment|active|inactive|blocked|frozen|closed|"
    r"abstain|clarify|clarification|explained|refuse|"
    r"dispute_filed|dispute_proposed|offer_dispute|explain_status|awaiting_recognition|"
    r"charge_inquiry|dispute_charge|out_of_scope|human_request)\b",
    re.I,
)
_NUMBER = re.compile(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)")
_ISO_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}(?=T|\b)")
_INJECTION = re.compile(
    r"ignore (?:all |your )?(?:previous |system )?instructions|ignora (?:tus |las )?instrucciones|mostra (?:todas|todos) as contas",
    re.I,
)
_PROMISE = re.compile(
    r"\b(?:garantizo|garantimos|garanto|reembolsaremos|devolveremos|refund|cr[eé]dito provisional)\b",
    re.I,
)
_NEGATED_STATUS = re.compile(
    r"\b(?:no|nao|não|not)\s+(?:est[aá]\s+|foi\s+|fue\s+)?"
    r"(?:pendiente|pendente|reversad[ao]|estornad[ao]|rechazad[ao]|recusad[ao]|"
    r"aprobad[ao]|aprovad[ao])\b",
    re.I,
)
# Generated clarifications cannot establish actions or explain their cause.
# Actual status explanations, offers and write receipts are rendered by code.
_ACTION_CLAIM = re.compile(
    r"\b(?:bloquee|bloqueei|bloqueamos|bloquead[oa]|congele|congelei|congelamos|"
    r"congelad[oa]|reembolse|reembolsei|reembolsamos|reembolsad[oa]|"
    r"devolvi|devolvimos|devolvemos|devolveremos|estornei|estornamos|"
    r"reverti|reverse|revertimos|cancele|cancelei|cancelamos|cancelad[oa]|anule|anulei|"
    r"registrei|registre|registramos|registrad[oa]|presente|apresentei|protocolei|abri|abrimos)\b|"
    r"\b(?:ya|ja)\s+(?:esta|foi|fue)\s+(?:bloquead[oa]|congelad[oa]|cancelad[oa])\b|"
    r"\b(?:voy a|vamos a|vou|vamos)\s+(?:bloquear|congelar|reembolsar|devolver|"
    r"estornar|cancelar|registrar)\b"
)
_CAUSAL_CLAIM = re.compile(
    r"\b(?:autorizad[oa]s?\s+(?:por|pela|pelo)|corresponde(?:m)?\s+a|"
    r"se debe a|deve-se a|se trata de|trata-se de|debido a|devido a|causad[oa] por)\b|"
    r"\b(?:cargo|cobro|cobranca|compra|transaccion|transacao)\b.{0,60}"
    r"\b(?:porque|por causa|a causa)\b"
)


def _fold(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(char)
    )


def _numeric_tokens(text: str) -> set[Decimal]:
    values: set[Decimal] = set()
    # A transaction timestamp such as 2026-06-09T00:00:00Z is a legitimate
    # source for a localized "9 jun 2026" date. The generic number regex does
    # not capture 09 when it is directly followed by the ISO time separator T.
    for iso_date in _ISO_DATE.findall(text):
        values.update(Decimal(part) for part in iso_date.split("-"))
    for token in _NUMBER.findall(text):
        try:
            if "," in token and "." in token:
                decimal_mark = "," if token.rfind(",") > token.rfind(".") else "."
                grouping_mark = "." if decimal_mark == "," else ","
                token = token.replace(grouping_mark, "").replace(decimal_mark, ".")
            elif "," in token or "." in token:
                separator = "," if "," in token else "."
                parts = token.split(separator)
                token = (
                    "".join(parts)
                    if len(parts) > 2 or (len(parts[-1]) == 3 and len(parts[0]) <= 3)
                    else token.replace(",", ".")
                )
            values.add(Decimal(token))
        except InvalidOperation:
            continue
    return values


def scan_dlp(text: str, *, other_customer_names: tuple[str, ...] = ()) -> tuple[str, ...]:
    violations: list[str] = []
    for label, pattern in (
        ("email", _EMAIL),
        ("phone", _PHONE),
        ("card_number", _CARD),
        ("document_number", _DOCUMENT),
        # A citation establishes provenance, not permission to show internal
        # selection handles in customer prose. Verified DSP/HO IDs stay separate.
        ("internal_handle", _HANDLE),
        ("instruction_echo", _INJECTION),
        ("prohibited_promise", _PROMISE),
        ("negated_status", _NEGATED_STATUS),
    ):
        if pattern.search(text):
            violations.append(label)
    if _CORRUPTION.search(text) or any(
        unicodedata.category(char) == "Cc" and char not in "\t\n\r" for char in text
    ):
        violations.append("text_corruption")
    folded = _fold(text)
    if any(_fold(name) in folded for name in other_customer_names if name.strip()):
        violations.append("other_customer_name")
    return tuple(violations)


def redact_for_model(text: str) -> str:
    """Strip direct identifiers before any customer text or fact reaches a provider."""
    redacted = text
    for pattern in (_EMAIL, _CARD, _PHONE, _DOCUMENT):
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _customer_prose(text: str, cited_facts: tuple[AllowedFact, ...]) -> str:
    """Remove exact grounded names/references only for prose-quality checks.

    DLP, citation, numeric and authority checks still inspect the original text.
    Arbitrary fact values never exempt ordinary words or untranslated enums.
    """
    merchants = {fact.value for fact in cited_facts if fact.id == "merchant" and fact.value}
    literals = set(merchants)
    for fact in cited_facts:
        literals.update(match.group(0) for match in _CASE.finditer(fact.value))
        literals.update(match.group(0) for match in _MASKED_CARD.finditer(fact.value))
    prose = text
    for literal in sorted(literals, key=len, reverse=True):
        pattern = r"(?<!\w)" + re.escape(literal) + r"(?!\w)"
        if literal in merchants and (
            _RAW_ENUM.fullmatch(literal) or _MACHINE_IDENTIFIER.fullmatch(literal)
        ):
            # A merchant named Pending is not a blanket exemption for a model
            # that also copies pending as the status elsewhere in the sentence.
            prefix = (
                r"(?P<merchant_context>\b(?:cargo|cobro|compra|cobrança|transação|"
                r"transacción|comercio|comércio|establecimiento|estabelecimento|loja)"
                r"(?:\s+(?:en|em|de|do|da|no|na))?\s*(?::\s*)?['\"“]?)"
            )
            prose = re.sub(prefix + pattern, r"\g<merchant_context> ", prose, flags=re.I)
        else:
            prose = re.sub(pattern, " ", prose, flags=re.I)
    return prose


def verify_draft(
    text: str,
    cited_fact_ids: list[str],
    facts: tuple[AllowedFact, ...],
    *,
    known_merchants: tuple[str, ...] = (),
    other_customer_names: tuple[str, ...] = (),
) -> Verdict:
    violations = list(scan_dlp(text, other_customer_names=other_customer_names))
    allowed_by_id = {fact.id: fact for fact in facts}
    if len(cited_fact_ids) != len(set(cited_fact_ids)):
        violations.append("duplicate_citation")
    if any(fact_id not in allowed_by_id for fact_id in cited_fact_ids):
        violations.append("unknown_citation")
    if any(
        not allowed_by_id[fact_id].source for fact_id in cited_fact_ids if fact_id in allowed_by_id
    ):
        violations.append("missing_source")
    cited_values = " ".join(
        allowed_by_id[fact_id].value for fact_id in cited_fact_ids if fact_id in allowed_by_id
    )
    cited_fold = _fold(cited_values)
    cited_facts = tuple(
        allowed_by_id[fact_id]
        for fact_id in cited_fact_ids
        if fact_id in allowed_by_id and allowed_by_id[fact_id].source
    )
    prose = _customer_prose(text, cited_facts)
    if _ACTION_CLAIM.search(_fold(prose)):
        violations.append("unsupported_action_claim")
    if _CAUSAL_CLAIM.search(_fold(prose)):
        violations.append("unsupported_causal_claim")
    if _WORD_DIGIT.search(prose):
        violations.append("text_corruption")
    if _RAW_ENUM.search(prose) or _MACHINE_IDENTIFIER.search(prose):
        violations.append("unlocalized_enum")
    if not _numeric_tokens(text).issubset(_numeric_tokens(cited_values)):
        violations.append("uncited_number")
    for label, pattern in (("date", _ISO_DATE), ("handle", _HANDLE), ("case_id", _CASE)):
        cited_tokens = {_fold(value) for value in pattern.findall(cited_values)}
        for match in pattern.finditer(text):
            if _fold(match.group(0)) not in cited_tokens:
                violations.append(f"uncited_{label}")
                break
    status_claims = {
        "pending": (r"\b(?:pendiente|pendente|retenid[ao])\b",),
        "reversed": (r"\b(?:reversad[ao]|estornad[ao])\b",),
        "declined": (r"\b(?:rechazad[ao]|recusad[ao])\b",),
        "approved": (r"\b(?:aprobad[ao]|aprovad[ao])\b",),
    }
    for status, patterns in status_claims.items():
        if (
            any(re.search(pattern, _fold(prose)) for pattern in patterns)
            and status not in cited_fold
        ):
            violations.append("uncited_status")
    text_fold = _fold(text)
    cited_merchants = {_fold(fact.value) for fact in cited_facts if fact.id == "merchant"}
    merchants = {*known_merchants, *(fact.value for fact in facts if fact.id == "merchant")}
    for merchant in merchants:
        if merchant and _fold(merchant) in text_fold and _fold(merchant) not in cited_merchants:
            violations.append("uncited_merchant")
            break
    return Verdict(not violations, tuple(dict.fromkeys(violations)))
