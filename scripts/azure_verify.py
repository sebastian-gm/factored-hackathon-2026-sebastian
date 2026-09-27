"""Read back approved Azure controls; never emit private inputs or secret values."""

from __future__ import annotations

import json
import sys

from scripts.azure_dev import GROUP, ROOT, STORAGE, VAULT, az, read_variables


def main() -> None:
    values = read_variables()
    prefix = f"/subscriptions/{values['subscription_id']}/resourceGroups/{GROUP}"

    def resource(path: str, version: str) -> dict:
        return az(
            "rest",
            "--method",
            "get",
            "--url",
            f"https://management.azure.com{prefix}/providers/{path}?api-version={version}",
        )

    account = az("account", "show")
    assert account["id"] == values["subscription_id"] and account["name"] == "Seb Azure Sandbox"
    for name in ["api", "web"]:
        app = resource(f"Microsoft.App/containerApps/ca-{name}-aclara-dev-eastus2", "2025-01-01")
        properties = app["properties"]
        identities = app["identity"]["userAssignedIdentities"]
        assert app["identity"]["type"] == "UserAssigned"
        registries = properties["configuration"]["registries"]
        assert len(registries) == 1
        # ARM resource IDs are case-insensitive; these two fields use different casing.
        assert registries[0]["identity"].lower() in {identity.lower() for identity in identities}
        ingress = properties["configuration"]["ingress"]
        rules = ingress["ipSecurityRestrictions"]
        assert len(rules) == 1 and rules[0]["action"] == "Allow"
        assert rules[0]["ipAddressRange"] == values["owner_ipv4"] + "/32"
        assert ingress["external"] and not ingress.get("allowInsecure", False)
        assert properties["configuration"]["activeRevisionsMode"] == "Single"
        # ARM can return null for the documented default minimum of zero.
        assert properties["template"]["scale"]["minReplicas"] in (None, 0)
        assert properties["template"]["scale"]["maxReplicas"] == 1
        container = properties["template"]["containers"][0]
        assert container["image"].endswith(":" + values["image_tag"])
        assert container["resources"]["cpu"] == 0.25 and container["resources"]["memory"] == "0.5Gi"
        assert properties["provisioningState"] == "Succeeded"
        if name == "api":
            env = {item["name"]: item for item in container["env"]}
            assert env["LLM_PROVIDER"]["value"] == "mock"
            assert env["PGSSLMODE"]["value"] == "verify-full"
            assert env["PGUSER"]["value"] == "aclara_app"
            assert env["PGPASSWORD"]["secretRef"] == "postgres-app"
            assert env["DEMO_PASSWORD"]["secretRef"] == "demo-password"
            secrets = properties["configuration"]["secrets"]
            assert {item["name"] for item in secrets} == {"postgres-app", "demo-password"}
            assert all(
                item.get("keyVaultUrl", "").startswith(f"https://{VAULT}.vault.azure.net/")
                for item in secrets
            )
        sys.stdout.write(
            f"Verified {name}: owner-only HTTPS ingress, single revision, replicas 0..1, SHA image, managed registry identity.\n"
        )
    server = az(
        "postgres",
        "flexible-server",
        "show",
        "--resource-group",
        GROUP,
        "--name",
        "psql-aclara-dev-eastus2",
    )
    assert server["sku"]["name"] == "Standard_B1ms"
    assert server["storage"]["storageSizeGb"] == 32
    rules = az(
        "postgres",
        "flexible-server",
        "firewall-rule",
        "list",
        "--resource-group",
        GROUP,
        "--name",
        "psql-aclara-dev-eastus2",
    )
    assert {(r["startIpAddress"], r["endIpAddress"]) for r in rules} == {
        (values["owner_ipv4"], values["owner_ipv4"]),
        ("0.0.0.0", "0.0.0.0"),  # noqa: S104 -- owner-approved Azure firewall sentinel
    }
    tls = az(
        "postgres",
        "flexible-server",
        "parameter",
        "show",
        "--resource-group",
        GROUP,
        "--server-name",
        "psql-aclara-dev-eastus2",
        "--name",
        "require_secure_transport",
    )
    assert tls["value"].lower() == "on"
    budget = resource("Microsoft.Consumption/budgets/budget-aclara-dev-eastus2", "2024-08-01")[
        "properties"
    ]
    assert budget["amount"] == round(50 * values.get("budget_usd_to_billing_rate", 1), 2)
    notifications = list(budget["notifications"].values())
    assert {n["threshold"] for n in notifications} == {60, 100}
    assert all(
        n["enabled"]
        and n["contactEmails"] == [values["budget_email"]]
        and n["thresholdType"] == "Actual"
        for n in notifications
    )
    assert budget["currentSpend"]["unit"] == values.get("budget_currency", "USD")
    storage = az("storage", "account", "show", "--resource-group", GROUP, "--name", STORAGE)
    assert not storage["allowBlobPublicAccess"] and not storage["allowSharedKeyAccess"]
    assert storage["networkRuleSet"]["defaultAction"] == "Deny"
    assert {r["ipAddressOrRange"] for r in storage["networkRuleSet"]["ipRules"]} <= {
        values["owner_ipv4"],
        values["owner_ipv4"] + "/32",
    }
    assert len(storage["networkRuleSet"]["ipRules"]) == 1
    vault = az("keyvault", "show", "--resource-group", GROUP, "--name", VAULT)
    assert vault["properties"]["enableRbacAuthorization"]
    registry = az("acr", "show", "--resource-group", GROUP, "--name", "acraclaradeveastus2")
    assert registry["sku"]["name"] == "Basic" and not registry["adminUserEnabled"]
    assert not registry.get("anonymousPullEnabled", False)
    sys.stdout.write(
        "Verified PostgreSQL B1ms/32GB, approved two firewall rules, TLS required; Key Vault RBAC; private ACR; state firewall; converted USD 30/50 alert thresholds and confirmed email.\n"
    )
    # Retain only an aggregate success record and public release identity locally.
    (ROOT / "artifacts/azure/verified.json").write_text(
        json.dumps({"controls": "passed", "release": values["image_tag"]}) + "\n"
    )


if __name__ == "__main__":
    main()
