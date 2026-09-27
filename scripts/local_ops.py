"""Generate only the local application credential, without printing it."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import dotenv_values


def main() -> None:
    path = Path(".env")
    if not path.is_file():
        raise ValueError("Create the ignored .env using .env.example first")
    if not dotenv_values(path).get("OPS_APP_PASSWORD"):
        lines = [
            line
            for line in path.read_text().splitlines()
            if not line.startswith("OPS_APP_PASSWORD=")
        ]
        lines.append("OPS_APP_PASSWORD=" + secrets.token_urlsafe(32))
        descriptor = os.open(path, os.O_WRONLY | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write("\n".join(lines) + "\n")
        path.chmod(0o600)


if __name__ == "__main__":
    main()
