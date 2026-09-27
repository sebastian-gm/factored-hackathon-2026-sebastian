"""Local append-only access ledger for frozen inputs and saved observations."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "artifacts/heldout/access-ledger.jsonl"


def append(event: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "a") as stream:
        stream.write(json.dumps({"at": datetime.now(UTC).isoformat(), **event}) + "\n")


@contextmanager
def access(action: str, paths: Sequence[Path], purpose: str) -> Iterator[None]:
    resolved = [p.resolve() for p in paths]
    if any(not p.is_relative_to(ROOT) for p in resolved):
        raise ValueError("Evaluation access must remain inside this checkout")
    event = {"access_id": str(uuid4()), "action": action, "purpose": purpose}
    append({**event, "status": "started", "paths": [str(p.relative_to(ROOT)) for p in resolved]})
    try:
        hashes = {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in resolved
        }
        yield
    except BaseException:
        append({**event, "status": "failed"})
        raise
    else:
        append({**event, "status": "completed", "sha256": hashes})
