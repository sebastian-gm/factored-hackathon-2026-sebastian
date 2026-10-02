"""Bounded ES/PT whole-number grammar, with no partial-token guessing."""

from __future__ import annotations

import re
from decimal import Decimal

# Expressions are preserved by NLU. Currency/slang interpretation stays in the
# existing country-aware normalizer; this parser supplies only the whole number.
_UNITS = r"(?:dolares?|dollars?|usd|reais|real|brl|pesos?|mxn|cop|ars|lucas?|palos?|contos?|varos?|pilas?)"
ES_SMALL = {
    "cero": 0,
    "un": 1,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20,
    "veintiun": 21,
    "veintiuno": 21,
    "veintiuna": 21,
    "veintidos": 22,
    "veintitres": 23,
    "veinticuatro": 24,
    "veinticinco": 25,
    "veintiseis": 26,
    "veintisiete": 27,
    "veintiocho": 28,
    "veintinueve": 29,
}
PT_SMALL = {
    "zero": 0,
    "um": 1,
    "uma": 1,
    "dois": 2,
    "duas": 2,
    "tres": 3,
    "quatro": 4,
    "cinco": 5,
    "seis": 6,
    "sete": 7,
    "oito": 8,
    "nove": 9,
    "dez": 10,
    "onze": 11,
    "doze": 12,
    "treze": 13,
    "catorze": 14,
    "quatorze": 14,
    "quinze": 15,
    "dezesseis": 16,
    "dezessete": 17,
    "dezoito": 18,
    "dezenove": 19,
}
ES_TENS = {
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "sesenta": 60,
    "setenta": 70,
    "ochenta": 80,
    "noventa": 90,
}
PT_TENS = {
    "vinte": 20,
    "trinta": 30,
    "quarenta": 40,
    "cinquenta": 50,
    "sessenta": 60,
    "setenta": 70,
    "oitenta": 80,
    "noventa": 90,
}
ES_HUNDREDS = {
    "ciento": 100,
    "doscientos": 200,
    "trescientos": 300,
    "cuatrocientos": 400,
    "quinientos": 500,
    "seiscientos": 600,
    "setecientos": 700,
    "ochocientos": 800,
    "novecientos": 900,
}
PT_HUNDREDS = {
    "cento": 100,
    "duzentos": 200,
    "trezentos": 300,
    "quatrocentos": 400,
    "quinhentos": 500,
    "seiscentos": 600,
    "setecentos": 700,
    "oitocentos": 800,
    "novecentos": 900,
}


def _under_hundred(words: list[str], *, pt: bool) -> int | None:
    small, tens, join = (PT_SMALL, PT_TENS, "e") if pt else (ES_SMALL, ES_TENS, "y")
    if len(words) == 1:
        return small.get(words[0], tens.get(words[0]))
    if len(words) == 3 and words[0] in tens and words[1] == join:
        unit = small.get(words[2], 0)
        if 1 <= unit <= 9:
            return tens[words[0]] + unit
    return None


def _under_thousand(words: list[str], *, pt: bool) -> int | None:
    if not words:
        return None
    if words == ["cem" if pt else "cien"]:
        return 100
    hundreds = PT_HUNDREDS if pt else ES_HUNDREDS
    if words[0] not in hundreds:
        return _under_hundred(words, pt=pt)
    base, rest = hundreds[words[0]], words[1:]
    if not rest:
        return None if base == 100 else base
    if pt:
        if rest[0] != "e":
            return None
        rest = rest[1:]
    remainder = _under_hundred(rest, pt=pt)
    return base + remainder if remainder is not None and remainder > 0 else None


def _whole(words: list[str], *, pt: bool) -> int | None:
    if "mil" not in words:
        return _under_thousand(words, pt=pt)
    if words.count("mil") != 1:
        return None
    at = words.index("mil")
    prefix = _under_thousand(words[:at], pt=pt) if at else 1
    if prefix is None or prefix <= 0:
        return None
    rest = words[at + 1 :]
    if not rest:
        return prefix * 1000
    if pt and rest[0] == "e":
        rest = rest[1:]
    remainder = _under_thousand(rest, pt=pt)
    return prefix * 1000 + remainder if remainder is not None and remainder > 0 else None


def parse_word_amount(plain: str) -> int | None:
    """Accept one complete number (0–999999) and an optional known unit suffix."""
    value = re.sub(rf"\s+(?:de )?{_UNITS}$", "", plain.strip(" .,!¿?¡"))
    words = value.split()
    for pt in (False, True):
        parsed = _whole(words, pt=pt)
        if parsed is not None:
            return parsed
    return None


def parse_spoken_money(plain: str) -> Decimal | None:
    """Accept complete ES/PT currency-and-centavos grammar, never partial numbers."""
    match = re.fullmatch(
        r"(?:(.+?) (dolares?|dollars?|usd|reais|real|brl|pesos?|mxn|cop|ars) ([ey]) )?"
        r"(.+?) centavos?",
        plain.strip(" .,!¿?¡"),
    )
    if match is None:
        return None
    whole_text, unit, join, cents_text = match.groups()
    for pt in (False, True):
        if join and join != ("e" if pt else "y"):
            continue
        if unit in {"reais", "real"} and not pt:
            continue
        cents = _whole(cents_text.split(), pt=pt)
        whole = _whole(whole_text.split(), pt=pt) if whole_text else 0
        if whole is not None and cents is not None and 0 <= cents < 100:
            return Decimal(whole) + Decimal(cents) / 100
    return None
