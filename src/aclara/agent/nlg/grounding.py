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
_CASE = re.compile(r"\b(?:DSP|HO)-[A-Z0-9-]+\b", re.I)
_NUMBER = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)")
_ISO_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
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


def _fold(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(char)
    )


def _numeric_tokens(text: str) -> set[Decimal]:
    values: set[Decimal] = set()
    for token in _NUMBER.findall(text):
        try:
            values.add(Decimal(token.replace(",", ".")))
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
        ("instruction_echo", _INJECTION),
        ("prohibited_promise", _PROMISE),
        ("negated_status", _NEGATED_STATUS),
    ):
        if pattern.search(text):
            violations.append(label)
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
            any(re.search(pattern, _fold(text)) for pattern in patterns)
            and status not in cited_fold
        ):
            violations.append("uncited_status")
    text_fold = _fold(text)
    for merchant in known_merchants:
        if merchant and _fold(merchant) in text_fold and _fold(merchant) not in cited_fold:
            violations.append("uncited_merchant")
            break
    return Verdict(not violations, tuple(dict.fromkeys(violations)))
