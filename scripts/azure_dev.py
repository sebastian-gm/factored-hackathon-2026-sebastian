"""Local Azure bootstrap. Explicit subscription; no credentials/IDs in console output.

Only run after owner provisioning approval and a passing live-price check.
Terraform owns runtime resources; this idempotent bootstrap owns the RG and state store.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUBSCRIPTION = "Seb Azure Sandbox"
GROUP = "rg-aclara-dev-eastus2"
STORAGE = "staclaradeveastus2"
VAULT = "kv-aclara-dev-eastus2"
VARIABLES = ROOT / "infra" / "terraform.tfvars"


def run(args: list[str], *, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, env=env)  # noqa: S603
    if result.returncode:
        # Do not print command lines, environment, credentials or account identifiers.
        message = re.sub(
            r"[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}",
            "[identifier]",
            result.stderr[-3000:],
        )
        raise RuntimeError(f"{args[0]} failed ({result.returncode}): {message}")
    return result.stdout


def az(*args: str) -> Any:
    return json.loads(
        run(["az", *args, "--subscription", SUBSCRIPTION, "--only-show-errors", "-o", "json"])
        or "null"
    )


def private_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as stream:
        stream.write(value)
    path.chmod(0o600)


def read_variables() -> dict[str, Any]:
    return {
        key.strip(): json.loads(value)
        for line in VARIABLES.read_text().splitlines()
        if line.strip()
        for key, value in [line.split("=", 1)]
    }


def configure(email: str | None, owner_ip: str | None) -> None:
    account = az("account", "show")
    if account["name"] != SUBSCRIPTION or account["state"] != "Enabled":
        raise RuntimeError("The approved sandbox subscription is not enabled")
    values = read_variables() if VARIABLES.exists() else {}
    if owner_ip is None and "owner_ipv4" not in values:
        with urllib.request.urlopen("https://api.ipify.org", timeout=20) as response:  # noqa: S310
            owner_ip = response.read().decode().strip()
    if owner_ip:
        address = ipaddress.IPv4Address(owner_ip)
        if not address.is_global:
            raise ValueError("Owner IPv4 must be a public address")
        values["owner_ipv4"] = str(address)
    values.update(subscription_id=account["id"], tenant_id=account["tenantId"])
    values.setdefault("budget_start_date", datetime.now(UTC).strftime("%Y-%m-01T00:00:00Z"))
    values.setdefault("deploy_apps", False)
    values.setdefault(
        "image_tag", run(["git", "-C", str(ROOT), "rev-parse", "origin/main"]).strip()
    )
    if email:
        values["budget_email"] = email
    private_write(
        VARIABLES, "".join(f"{key} = {json.dumps(value)}\n" for key, value in values.items())
    )
    sys.stdout.write("Private Terraform inputs saved (mode 0600); no values displayed.\n")


def bootstrap() -> None:
    values = read_variables()
    account = az("account", "show")
    if account["id"] != values["subscription_id"] or account["name"] != SUBSCRIPTION:
        raise RuntimeError("Sandbox subscription mismatch")
    for provider in [
        "Microsoft.Storage",
        "Microsoft.App",
        "Microsoft.ContainerRegistry",
        "Microsoft.KeyVault",
        "Microsoft.ManagedIdentity",
        "Microsoft.DBforPostgreSQL",
        "Microsoft.Consumption",
        "Microsoft.OperationalInsights",
    ]:
        state = az("provider", "show", "--namespace", provider)["registrationState"]
        if state != "Registered":
            az("provider", "register", "--namespace", provider, "--wait")
        sys.stdout.write(f"Provider ready: {provider}\n")
        sys.stdout.flush()
    az(
        "group",
        "create",
        "--name",
        GROUP,
        "--location",
        "eastus2",
        "--tags",
        "project=aclara",
        "environment=dev",
    )
    stores = az("storage", "account", "list", "--resource-group", GROUP)
    if not any(store["name"] == STORAGE for store in stores):
        az(
            "storage",
            "account",
            "create",
            "--name",
            STORAGE,
            "--resource-group",
            GROUP,
            "--location",
            "eastus2",
            "--sku",
            "Standard_LRS",
            "--kind",
            "StorageV2",
            "--min-tls-version",
            "TLS1_2",
            "--allow-blob-public-access",
            "false",
            "--allow-shared-key-access",
            "false",
            "--default-action",
            "Deny",
            "--bypass",
            "None",
            "--https-only",
            "true",
            "--tags",
            "project=aclara",
            "environment=dev",
        )
    az(
        "storage",
        "account",
        "network-rule",
        "add",
        "--account-name",
        STORAGE,
        "--resource-group",
        GROUP,
        "--ip-address",
        values["owner_ipv4"],
    )
    storage = az("storage", "account", "show", "--name", STORAGE, "--resource-group", GROUP)
    owner = az("rest", "--method", "get", "--url", "https://graph.microsoft.com/v1.0/me")
    roles = az("role", "assignment", "list", "--scope", storage["id"])
    if not any(
        r["principalId"] == owner["id"]
        and r["roleDefinitionName"] == "Storage Blob Data Contributor"
        for r in roles
    ):
        az(
            "role",
            "assignment",
            "create",
            "--assignee-object-id",
            owner["id"],
            "--assignee-principal-type",
            "User",
            "--scope",
            storage["id"],
            "--role",
            "Storage Blob Data Contributor",
        )
    for attempt in range(12):
        try:
            az(
                "storage",
                "container",
                "create",
                "--account-name",
                STORAGE,
                "--name",
                "tfstate",
                "--auth-mode",
                "login",
                "--public-access",
                "off",
            )
            break
        except RuntimeError:
            if attempt == 11:
                raise
            time.sleep(10)
    az(
        "storage",
        "account",
        "blob-service-properties",
        "update",
        "--account-name",
        STORAGE,
        "--resource-group",
        GROUP,
        "--enable-versioning",
        "true",
        "--enable-delete-retention",
        "true",
        "--delete-retention-days",
        "7",
        "--enable-container-delete-retention",
        "true",
        "--container-delete-retention-days",
        "7",
    )
    private_write(
        ROOT / "infra" / "dev.backend.hcl",
        f'resource_group_name = "{GROUP}"\nstorage_account_name = "{STORAGE}"\ncontainer_name = "tfstate"\nkey = "dev.terraform.tfstate"\n',
    )
    sys.stdout.write("Bootstrap complete: private Blob state, owner IPv4 firewall, Entra RBAC.\n")


def terraform(action: str) -> None:
    values = read_variables()
    env = {
        **os.environ,
        "ARM_SUBSCRIPTION_ID": values["subscription_id"],
        "ARM_TENANT_ID": values["tenant_id"],
    }
    if action == "init":
        output = run(
            [
                "terraform",
                "-chdir=infra",
                "init",
                "-reconfigure",
                "-input=false",
                "-no-color",
                "-backend-config=dev.backend.hcl",
            ],
            env=env,
        )
        sys.stdout.write(
            "Terraform remote backend initialized.\n"
            if "successfully initialized" in output
            else "Terraform init finished.\n"
        )
        return
    command = ["terraform", "-chdir=infra", action, "-input=false", "-no-color"]
    if action == "plan":
        command += ["-out=dev.tfplan"]
    else:
        command += ["dev.tfplan"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=env)  # noqa: S603
    # Full outputs can include resource IDs; keep only in ignored, restricted artifacts.
    private_write(ROOT / "artifacts" / "azure" / f"{action}.log", result.stdout + result.stderr)
    for line in result.stdout.splitlines():
        if line.startswith(("Plan:", "Apply complete!", "No changes.")):
            sys.stdout.write(line + "\n")
    if result.returncode:
        raise RuntimeError(
            f"Terraform {action} failed; inspect the ignored log with identifier redaction"
        )


def seed_database() -> None:
    import psycopg
    from psycopg import sql

    admin = az("keyvault", "secret", "show", "--vault-name", VAULT, "--name", "postgres-admin")[
        "value"
    ]
    password = az("keyvault", "secret", "show", "--vault-name", VAULT, "--name", "postgres-app")[
        "value"
    ]
    with psycopg.connect(
        host="psql-aclara-dev-eastus2.postgres.database.azure.com",
        dbname="aclara",
        user="aclara_admin",
        password=admin,
        sslmode="verify-full",
        sslrootcert="/etc/ssl/certs/ca-certificates.crt",
        connect_timeout=15,
    ) as connection:
        # Parameterize the password; format identifiers with psycopg.sql only.
        if not connection.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s", ("aclara_app",)
        ).fetchone():
            connection.execute(
                "CREATE ROLE aclara_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION"
            )
        connection.execute(
            sql.SQL("ALTER ROLE aclara_app PASSWORD {}").format(sql.Literal(password))
        )
        connection.execute("REVOKE ALL ON DATABASE aclara FROM PUBLIC")
        connection.execute("GRANT CONNECT ON DATABASE aclara TO aclara_app")
        connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        tls = connection.execute(
            "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()"
        ).fetchone()
        if tls != (True,):
            raise RuntimeError("Database TLS readback failed")
    sys.stdout.write(
        "App role initialized with CONNECT only; TLS verified; passwords never displayed.\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["configure", "bootstrap", "init", "plan", "apply", "seed"]
    )
    parser.add_argument("--email")
    parser.add_argument("--owner-ip")
    args = parser.parse_args()
    if args.action == "configure":
        configure(args.email, args.owner_ip)
    elif args.action == "bootstrap":
        bootstrap()
    elif args.action == "seed":
        seed_database()
    else:
        terraform(args.action)


if __name__ == "__main__":
    main()
