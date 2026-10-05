"""Bounded intent-only replies while a customer still needs to choose a charge."""

from __future__ import annotations

import re

from aclara.agent.nlu.rules import normalize_text


def pending_dispute_request(message: str) -> bool:
    """Recognize a positive denial/request without asserting any target identity.

    Full clauses exclude new target details, uncertainty and unrelated requests.
    The caller still requires a later explicit choice and separate confirmation.
    """
    text = normalize_text(message).strip(" .,!¿?¡")
    return bool(
        re.fullmatch(
            r"(?:(?:volvamos al cargo|voltemos a cobranca)[.! ]+)?"
            r"(?:no fui yo y quiero disputarlo|nao fui eu e quero contestar)",
            text,
        )
    )
