"""Resolve operator targets lazily; keep concrete cloud hosts out of Git."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

from scripts.azure_dev import GROUP, az


def _https(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("Azure app target must be an uncredentialed HTTPS origin")
    return value.rstrip("/")


def app_url(name: str) -> str:
    if name not in {"web", "api"}:
        raise ValueError("Unknown approved app target")
    configured = os.getenv(f"AZURE_{name.upper()}_URL")
    if configured:
        return _https(configured)
    app = az(
        "containerapp",
        "show",
        "--resource-group",
        GROUP,
        "--name",
        f"ca-{name}-aclara-dev-eastus2",
    )
    return _https("https://" + app["properties"]["configuration"]["ingress"]["fqdn"])


def database_host() -> str:
    configured = os.getenv("AZURE_POSTGRES_HOST")
    if configured:
        host = configured
    else:
        host = az(
            "postgres",
            "flexible-server",
            "show",
            "--resource-group",
            GROUP,
            "--name",
            "psql-aclara-dev-eastus2",
        )["fullyQualifiedDomainName"]
    if not host or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789.-" for c in host):
        raise ValueError("Azure database target must be a hostname")
    return host
