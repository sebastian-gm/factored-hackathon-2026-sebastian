"""Verify the restricted serving deployment through the owner-only web BFF."""

# ruff: noqa: T201 -- aggregate checks and exception frame locations only.

from __future__ import annotations

import json
import time
from datetime import UTC, datetime

import httpx
from scripts.azure_dev import GROUP, ROOT, VAULT, az, private_write, read_variables
from scripts.azure_migrate_ops import connection_string
from scripts.serving_smoke import check, smoke, wait_config

from aclara.agent.contracts import DisputeCaseView
from aclara.bank.serving import ServingRepository
from aclara.ops.store import Store
from aclara.settings import Settings


def main() -> None:
    web = "https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io"
    password = az("keyvault", "secret", "show", "--vault-name", VAULT, "--name", "demo-password")[
        "value"
    ]
    store = Store(connection_string("aclara_app"))
    try:
        ledger = ServingRepository(store, Settings().bank_clock)
        evidence = smoke(web, password, ledger)
    finally:
        store.close()
    name = "ca-api-aclara-dev-eastus2"
    app = az("containerapp", "show", "--name", name, "--resource-group", GROUP)
    revision = app["properties"]["latestReadyRevisionName"]

    def replicas() -> set[str]:
        return {
            r["name"]
            for r in az(
                "containerapp",
                "replica",
                "list",
                "--name",
                name,
                "--revision",
                revision,
                "--resource-group",
                GROUP,
            )
        }

    before = replicas()
    assert before
    az(
        "containerapp",
        "revision",
        "restart",
        "--name",
        name,
        "--revision",
        revision,
        "--resource-group",
        GROUP,
    )
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        after = replicas()
        if after and not before.intersection(after):
            break
        time.sleep(3)
    else:
        raise RuntimeError("No replacement API replica verified")
    with httpx.Client(
        base_url=web + "/api/bff/", cookies=evidence["cookies"], headers={"Origin": web}, timeout=30
    ) as client:
        wait_config(client)
        actual = check(client.get(evidence["case_path"]))
        assert DisputeCaseView.model_validate(actual) == DisputeCaseView.model_validate(
            evidence["case"]
        )
        check(client.post("auth/logout", json={}))
        assert client.get("me").status_code == 401
    private_write(
        ROOT / "artifacts/azure/serving-smoke.json",
        json.dumps(
            {
                "verified_at": datetime.now(UTC).isoformat(),
                "release": read_variables()["image_tag"],
                "source": "organizer_serving",
                "bff_three_surfaces": "passed",
                "new_replica_case_recovery": "passed",
                "model_cost_usd": 0,
            }
        )
        + "\n",
    )
    print("Azure serving BFF, replacement API replica recovery and logout verified.")  # noqa: T201


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback

        print(
            type(exc).__name__,
            [(f.name, f.lineno) for f in traceback.extract_tb(exc.__traceback__)],
        )  # noqa: T201
        raise SystemExit(1) from None
