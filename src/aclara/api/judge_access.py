"""Optional Key Vault account alias; never accepts new ownership or role claims."""

from __future__ import annotations

import hmac
import json
import os
import re
from dataclasses import replace

from aclara.bank.serving import Persona
from aclara.settings import Settings


def judge_alias(settings: Settings, personas: dict[str, Persona]) -> Persona | None:
    if not settings.judge_access_enabled:
        return None
    if (
        len(settings.judge_password) < 32
        or hmac.compare_digest(settings.judge_password, settings.demo_password)
        or os.getenv("LLM_BUDGET_RUN_ID")
        or (settings.llm_provider != "mock" and os.getenv("LLM_DAILY_BUDGET_USD") != "3")
    ):
        raise ValueError(
            "Judge access requires separate credentials and normal USD 3/day accounting"
        )
    try:
        definition = json.loads(settings.judge_persona)
        if not isinstance(definition, dict) or set(definition) != {"username", "source_username"}:
            raise ValueError
        username, source_username = definition["username"], definition["source_username"]
        if (
            not isinstance(username, str)
            or not re.fullmatch(r"judge\.[a-z0-9._-]{1,64}", username)
            or username in personas
            or not isinstance(source_username, str)
            or source_username not in personas
        ):
            raise ValueError
        source = personas[source_username]
    except (ValueError, TypeError, KeyError):
        # Do not echo the Key Vault JSON or anything from its source identity.
        raise ValueError("Invalid or unavailable Key Vault judge persona") from None
    return replace(source, username=username)
