"""Versioned prompt loader with safe untrusted-data blocks."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import yaml  # type: ignore[import-untyped]


@dataclass(frozen=True, slots=True)
class Prompt:
    id: str
    version: str
    route: str
    text: str
    content_hash: str


def load_prompt(path: Path) -> Prompt:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError("Prompt front matter is required")
    header, body = raw[4:].split("\n---\n", 1)
    meta = yaml.safe_load(header)
    return Prompt(
        id=str(meta["id"]),
        version=str(meta["version"]),
        route=str(meta["route"]),
        text=body.strip(),
        content_hash=sha256(raw.encode("utf-8")).hexdigest(),
    )


def data_block(tag: str, value: str, *, max_chars: int = 2000) -> str:
    if tag not in {"customer_message", "record", "response_plan"}:
        raise ValueError("Unrecognized untrusted-data tag")
    escaped = value[:max_chars].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<{tag}>\n{escaped}\n</{tag}>"
