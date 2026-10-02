"""Optional Key Vault account alias; never accepts new ownership or role claims."""

from __future__ import annotations

import hmac
import json
import os
import re
from dataclasses import dataclass, replace

from aclara.bank.serving import Persona
from aclara.settings import Settings

PROFILE_LOCALES = {"mx-es": "es-MX", "co-es": "es-CO", "ar-es": "es-AR", "pt": "pt-BR"}
PROFILE_LABELS = {
    "mx-es": "México · Español",
    "co-es": "Colombia · Español",
    "ar-es": "Argentina · Español",
    "pt": "Conversa em português",
}


@dataclass(frozen=True)
class JudgeConfiguration:
    alias: Persona
    source_username: str
    profiles: dict[str, Persona]
    fingerprint: str


def judge_configuration(
    settings: Settings, personas: dict[str, Persona]
) -> JudgeConfiguration | None:
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
        if not isinstance(definition, dict) or set(definition) not in (
            {"username", "source_username"},
            {"username", "profiles"},
        ):
            raise ValueError
        username = definition["username"]
        if (
            not isinstance(username, str)
            or not re.fullmatch(r"judge\.[a-z0-9._-]{1,64}", username)
            or username in personas
        ):
            raise ValueError
        profiles: dict[str, Persona] = {}
        if "profiles" in definition:
            configured = definition["profiles"]
            if not isinstance(configured, dict) or set(configured) != set(PROFILE_LOCALES):
                raise ValueError
            for profile_id, locale in PROFILE_LOCALES.items():
                source_name = configured[profile_id]
                if not isinstance(source_name, str) or source_name not in personas:
                    raise ValueError
                candidate = personas[source_name]
                if candidate.locale != locale or candidate.role not in {"customer", "agent", "ops"}:
                    raise ValueError
                profiles[profile_id] = candidate
            if len({p.customer_id for p in profiles.values()}) != 4:
                raise ValueError
            source_username = profiles["mx-es"].username
        else:
            source_username = definition["source_username"]
            if not isinstance(source_username, str) or source_username not in personas:
                raise ValueError
        source = personas[source_username]
    except (ValueError, TypeError, KeyError):
        # Do not echo the Key Vault JSON or anything from its source identity.
        raise ValueError("Invalid or unavailable Key Vault judge persona") from None
    identity = [
        username,
        source_username,
        [(key, p.username, p.customer_id, p.locale, p.role) for key, p in profiles.items()],
    ]
    fingerprint = hmac.new(
        settings.judge_password.encode(), json.dumps(identity).encode(), "sha256"
    ).hexdigest()
    return JudgeConfiguration(
        replace(source, username=username, role="customer" if profiles else source.role),
        source_username,
        profiles,
        fingerprint,
    )


def judge_alias(settings: Settings, personas: dict[str, Persona]) -> Persona | None:
    configuration = judge_configuration(settings, personas)
    return configuration.alias if configuration else None
