"""Exact literal merchant identity over current, code-authorized ledger rows."""

from __future__ import annotations

import re
from collections.abc import Sequence

from aclara.agent.nlu.rules import normalize_text
from aclara.bank.repository import Transaction
from aclara.ml.charge_matcher.features import ALIASES, normalize


def _name(value: str) -> str:
    return normalize(" ".join(normalize_text(value).split()))


def exact_merchant_rows(
    message: str, rows: Sequence[tuple[str, Transaction]]
) -> list[tuple[str, Transaction]]:
    """Return all rows for one positively named merchant, never a fuzzy match.

    Count the whole authorized window, not the displayed three. Aliases are the
    existing fixed MATCH aliases. Require a clause boundary or banking verb after
    the name, so a prefix such
    as "Uber" cannot identify an unknown "Uber Eats". The caller retains intent,
    confidence, uncertainty, detail, policy and security gates.
    """
    text = " ".join(normalize_text(message).split())
    canonical = {_name(row.merchant_name) for _, row in rows if _name(row.merchant_name)}
    terms = {" ".join(normalize_text(row.merchant_name).split()) for _, row in rows}
    terms.update(alias for alias, target in ALIASES.items() if _name(target) in canonical)
    hits: set[str] = set()
    mentions: set[str] = set()
    occupied: list[tuple[int, int]] = []
    negated = False
    alternative = False
    for term in sorted(terms, key=len, reverse=True):
        if term in {"", "—"}:
            continue
        for match in re.finditer(rf"(?<!\w){re.escape(term)}(?!\w)", text):
            if any(start <= match.start() and match.end() <= end for start, end in occupied):
                continue
            occupied.append(match.span())
            mentions.add(_name(term))
            denied = bool(
                re.search(
                    r"\b(?:no|nao)\s+(?:era|es|e|fue|foi)\s+(?:(?:el|o|la|a)\s+)?$",
                    text[: match.start()],
                )
            )
            negated |= denied
            alternative |= bool(re.match(r"[, ]+(?:o|ou|or)\b", text[match.end() :]))
            if (
                re.match(
                    r"\s*(?:$|[.,!?¿¡;:\"'»”)])|"
                    r"\s+(?:por favor|esta|aparece|figura|me|parece|es|foi|fue|tiene|tem)\b",
                    text[match.end() :],
                )
                and not denied
            ):
                hits.add(_name(term))
    if len(hits) != 1 or mentions != hits or negated or alternative:
        return []
    merchant = hits.pop()
    return [(handle, row) for handle, row in rows if _name(row.merchant_name) == merchant]
