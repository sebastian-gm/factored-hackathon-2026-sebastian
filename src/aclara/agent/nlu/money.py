"""Local monetary evidence; raw text never becomes a provider input here."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aclara.agent.nlg.grounding import redact_for_model

_CURRENCY = r"(?:USD|COP|CLP|ARS|MXN|BRL|EUR|GBP|pesos?|d[oó]lares?|reais|real|euros?)"
_SCALE = r"(?:mil(?:\s+millones)?|mill[oó]n(?:es)?|milh[aã]o|milh[oõ]es)"
_UNIT = rf"(?:{_CURRENCY}|{_SCALE}|palos?|lucas?|contos?|varos?|pilas?|lana|centavos?)"
_PREFIX = re.compile(
    rf"(?:\b{_CURRENCY}\s*|(?:R|US)?[$€£]\s*|"
    r"\b(?:(?:cargos?|cobros?|consumos?|compras?|cobranças?|transaç(?:ão|ões)|"
    r"transacci[oó]n(?:es)?|pagamentos?|pagos?|valor|monto|importe|total|quantia)"
    r"(?:\s+(?:es|e|é|fue|foi|de|do|da|por|en|no|na))*|por)\s*)$",
    re.I,
)
_SUFFIX = re.compile(rf"\s*(?:de\s+)?{_UNIT}\b(?:\s+(?:de\s+)?{_CURRENCY}\b)?", re.I)
_NUMBER = re.compile(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)")
_VALUE = re.compile(
    r"(?:\d{1,3}(?:\.\d{3})+(?:,\d{2})?|\d{1,3}(?:,\d{3})+(?:\.\d{2})?|"
    r"\d+(?:[.,]\d{1,2})?)"
)
_IDENTIFIER_CUE = re.compile(
    r"\b(?:tel[eé]fono|telefone|celular|m[oó]vil|fono|fone|whatsapp|phone|tel|"
    r"contact[ao]|contactar|contat[ao]|contatar|contacte|contate|"
    r"ll[aá]ma(?:me|nos)?|llame|llamar|liga|ligue|ligar|"
    r"DNI|CPF|c[eé]dula|RUT|documento|RG|RFC|CNPJ|pasaporte|passaporte|"
    r"cuenta|conta|n[uú]mero|num|nro|termina(?:n)?|"
    r"tarjeta|cart[aã]o|card|PAN|IBAN|CBU|CLABE)\b",
    re.I,
)
# Dots inside decimal/grouped numbers and punctuated IDs are not clause breaks.
_CLAUSE_BREAK = re.compile(r"[;!?\n]+|(?<!\d)\.|\.(?!\d)")
_SHARED_UNIT = re.compile(r"\s*(?:[,/&]|y|e|o|ou)\s*(?:de\s+)?", re.I)
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_ISO_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


@dataclass(frozen=True, slots=True)
class MoneyEvidence:
    expression: str | None = None
    needs_clarification: bool = False


def inspect_money(text: str) -> MoneyEvidence:
    """Recover one qualified amount, refusing identifiers and multiple amounts.

    Identifier cues apply throughout their clause, before or after a number.
    Redaction is unconditional; this local inspection grants no model exemption.
    """
    candidates: list[tuple[str, bool]] = []
    unsafe_input = False
    for clause in _CLAUSE_BREAK.split(text):
        identifier = bool(_IDENTIFIER_CUE.search(clause))
        numbers = tuple(_NUMBER.finditer(clause))
        unsafe_input |= identifier or (bool(numbers) and redact_for_model(clause) != clause)
        spans: dict[int, tuple[int, int]] = {}
        blocked: set[int] = set()
        protected = [
            match.span() for pattern in (_CARD, _ISO_DATE) for match in pattern.finditer(clause)
        ]
        for index, number in enumerate(numbers):
            if (
                not _VALUE.fullmatch(number[0])
                or clause[number.start() - 1 : number.start()] in {"+", "-"}
                or clause[number.end() : number.end() + 1] == "-"
                or any(start < number.end() and number.start() < end for start, end in protected)
            ):
                blocked.add(index)
                continue
            prefix = _PREFIX.search(clause[: number.start()])
            suffix = _SUFFIX.match(clause, number.end())
            if prefix or suffix:
                spans[index] = (
                    prefix.start() if prefix else number.start(),
                    suffix.end() if suffix else number.end(),
                )
        # A shared currency qualifies each value; it never selects the last one.
        for index in reversed(range(len(numbers) - 1)):
            if index in spans or index in blocked or index + 1 not in spans:
                continue
            if _SHARED_UNIT.fullmatch(clause[numbers[index].end() : numbers[index + 1].start()]):
                spans[index] = numbers[index].span()
        candidates.extend((clause[start:end], identifier) for start, end in spans.values())
    if len(candidates) == 1 and not candidates[0][1]:
        return MoneyEvidence(expression=candidates[0][0])
    return MoneyEvidence(needs_clarification=bool(candidates) or unsafe_input)
