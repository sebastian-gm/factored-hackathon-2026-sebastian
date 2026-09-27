"""Pass a local/Key Vault demo credential to the browser on stdin, never argv."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from contextlib import nullcontext
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("local", "azure"), required=True)
    args = parser.parse_args()
    allowance = nullcontext()
    if args.target == "azure":
        from scripts.azure_dev import VAULT, az, read_variables

        url = "https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io"
        password = az(
            "keyvault", "secret", "show", "--vault-name", VAULT, "--name", "demo-password"
        )["value"]
        if read_variables().get("enable_real_llm"):
            from scripts.azure_llm_smoke import budget_receipt, conversation_allowance

            if read_variables().get("llm_budget_run_id") != "handoff09-smoke":
                raise RuntimeError("A real browser smoke requires the approved cumulative cap")
            budget_receipt()
            allowance = conversation_allowance(1, "browser-three-surfaces")
    else:
        values = dotenv_values(ROOT / ".env")
        url = "http://localhost:" + (values.get("WEB_HOST_PORT") or "3000")
        password = values.get("DEMO_PASSWORD") or ""
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node is required")
    with allowance:
        result = subprocess.run(  # noqa: S603 -- fixed repository browser entry point.
            [node, "scripts/serving-browser.mjs"],
            cwd=ROOT / "apps/web",
            env={
                **os.environ,
                "PLAYWRIGHT_BROWSERS_PATH": str(ROOT / "artifacts/frontend/browsers"),
            },
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
