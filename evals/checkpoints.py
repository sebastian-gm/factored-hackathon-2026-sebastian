"""Private atomic checkpoints and one writer; independent of any frozen inputs."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + ".pending")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def save(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


@contextmanager
def exclusive(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    with os.fdopen(fd, "w") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


class Checkpoints:
    def __init__(self, root: Path, pins: dict):
        self.root = root
        manifest = root / "release.json"
        if manifest.exists():
            if json.loads(manifest.read_text()) != pins:
                raise ValueError("Resume pins differ; restore the original release and inputs")
        else:
            save(manifest, pins)

    def directory(self, key: str) -> Path:
        return self.root / "checkpoints" / hashlib.sha256(key.encode()).hexdigest()

    def read(self, key: str) -> dict | None:
        path = self.directory(key) / "result.json"
        return json.loads(path.read_text()) if path.exists() else None

    def begin(self, key: str) -> Path:
        directory = self.directory(key)
        attempts = len(list(directory.glob("attempt-*.json")))
        if attempts >= 3:
            raise RuntimeError(
                "Three interrupted attempts for one unit; manual investigation required"
            )
        number = attempts + 1
        save(directory / f"attempt-{number}.json", {"number": number, "state": "started"})
        return directory / f"calls-{number}.jsonl"

    def finish(self, key: str, value: dict) -> dict:
        save(self.directory(key) / "result.json", value)
        return value

    def calls(self, key: str) -> list[dict]:
        rows = []
        for path in sorted(self.directory(key).glob("calls-*.jsonl")):
            for line in path.read_text().splitlines():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    # A killed append can leave a partial final line; DB retains its reserve.
                    continue
        return rows
