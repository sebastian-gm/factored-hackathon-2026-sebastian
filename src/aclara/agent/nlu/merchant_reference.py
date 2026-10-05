"""Literal customer choices from an existing, owned candidate list."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from aclara.agent.nlu.rules import normalize_text

_MARKER = "__merchant__"
_READ = re.compile(
    r"(?:(?:vale|bien|ok|certo|entao)[, ]+)?"
    r"(?:(?:solo|so|apenas) )?(?:(?:quiero|quero) )?"
    r"(?:(?:saber|consultar|revisar|entender) )?"
    r"(?:(?:el|o) )?(?:estado|status) "
    r"(?:del cargo|del cobro|de la compra|da cobranca|da compra|do lancamento) (?:de|da|do) "
    r"__merchant__|"
    r"(?:explicame|explique|explica|que es|o que e) "
    r"(?:el cargo|el cobro|la compra|a cobranca|a compra) (?:de|da|do) __merchant__"
)
_PICK = re.compile(
    r"(?:(?:elijo|escojo|selecciono|escolho|seleciono) )?"
    r"(?:(?:el|la|o|a) )?(?:(?:cargo|compra|cobranca) )?"
    r"(?:de|da|do) __merchant__|__merchant__"
)


@dataclass(frozen=True)
class MerchantReference:
    handle: str
    read_only: bool


def pending_merchant_reference(
    message: str,
    shown: Sequence[tuple[str, str]],
    owned: Sequence[tuple[str, str]],
) -> MerchantReference | None:
    """Resolve positive literal wording, never a fresh MATCH or fuzzy name.

    The caller supplies current authorized rows and enforces unchanged retained
    identity, policy and security. Duplicate names anywhere in that scope cannot
    become unique merely because only three choices were displayed.
    """
    text = normalize_text(message).strip(" .,!¿?¡")
    hits = [
        (handle, normalize_text(name).strip())
        for handle, name in owned
        if name.strip() not in {"", "—"}
        and re.search(rf"(?<!\w){re.escape(normalize_text(name).strip())}(?!\w)", text)
    ]
    if len(hits) != 1:
        return None
    handle, name = hits[0]
    if (handle, name) not in [(h, normalize_text(n).strip()) for h, n in shown]:
        return None
    masked = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", _MARKER, text)
    # Full clauses reject unknown alternatives, negated/uncertain identity,
    # additional amount/date/currency details and unrelated uses of a name.
    if _READ.fullmatch(masked):
        return MerchantReference(handle, read_only=True)
    if _PICK.fullmatch(masked):
        return MerchantReference(handle, read_only=False)
    return None
