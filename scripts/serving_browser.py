"""Pass a local/Key Vault demo credential to the browser on stdin, never argv."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("local", "azure"), required=True)
    args = parser.parse_args()
    if args.target == "azure":
        from scripts.azure_dev import VAULT, az

        url = "https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io"
        password = az(
            "keyvault", "secret", "show", "--vault-name", VAULT, "--name", "demo-password"
        )["value"]
    else:
        values = dotenv_values(ROOT / ".env")
        url = "http://localhost:" + (values.get("WEB_HOST_PORT") or "3000")
        password = values.get("DEMO_PASSWORD") or ""
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node is required")
    result = subprocess.run(  # noqa: S603 -- fixed repository browser entry point.
        [node, "scripts/serving-browser.mjs"],
        cwd=ROOT / "apps/web",
        env={**os.environ, "PLAYWRIGHT_BROWSERS_PATH": str(ROOT / "artifacts/frontend/browsers")},
        input=json.dumps({"url": url, "password": password}),
        text=True,
        capture_output=True,
        check=False,
    )
    # Only our aggregate JSON goes to stdout. Never relay browser error stacks.
    if result.stdout:
        output = json.loads(result.stdout)
        print(json.dumps(output))  # noqa: T201
    if result.returncode:
        raise SystemExit("Browser verification failed; details suppressed to protect source data")


if __name__ == "__main__":
    main()
