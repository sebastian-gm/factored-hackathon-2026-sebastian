"""Move the owner-supplied production key to the approved vault, without printing it."""

from __future__ import annotations

import hmac
import os
import subprocess
import tempfile
from pathlib import Path

from dotenv import dotenv_values, unset_key
from scripts.azure_dev import ROOT, SUBSCRIPTION, VAULT


def main() -> None:
    path = ROOT / ".env"
    key = dotenv_values(path).get("OPENROUTER_API_KEY")
    if not key or "\n" in key or "\r" in key:
        raise RuntimeError("Production key is absent or invalid in the local environment file")
    temporary: Path | None = None
    prefix = ["az", "keyvault", "secret"]
    suffix = [
        "--vault-name",
        VAULT,
        "--name",
        "openrouter-api-key",
        "--subscription",
        SUBSCRIPTION,
        "--only-show-errors",
    ]
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=ROOT / "artifacts/azure", delete=False
        ) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            stream.write(key)
        result = subprocess.run(  # noqa: S603 -- fixed CLI; key travels only via private file.
            [
                *prefix,
                "set",
                *suffix,
                "--file",
                str(temporary),
                "--encoding",
                "utf-8",
                "-o",
                "none",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("Key Vault upload failed; local key retained")
        result = subprocess.run(  # noqa: S603 -- never print CLI output or arguments.
            [*prefix, "show", *suffix, "--query", "value", "-o", "tsv"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode or not hmac.compare_digest(result.stdout.rstrip("\r\n"), key):
            raise RuntimeError("Key Vault readback failed; local key retained")
        if dotenv_values(path).get("OPENROUTER_API_KEY") != key:
            raise RuntimeError("Local key changed during transfer; retained for owner review")
        unset_key(path, "OPENROUTER_API_KEY")
        path.chmod(0o600)
        print("Production key moved to Key Vault and verified; local entry removed.")  # noqa: T201
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(type(exc).__name__ + ": production key transfer did not complete.")  # noqa: T201
        raise SystemExit(1) from None
