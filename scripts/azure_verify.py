"""Read back approved Azure controls; never emit private inputs or secret values."""

from __future__ import annotations

import json
import sys

from scripts.azure_dev import GROUP, ROOT, STORAGE, VAULT, az, read_variables


def main() -> None:
    values = read_variables()
    real_llm = values.get("enable_real_llm", False)
    judge = values.get("enable_judge_access", False)
    minimum = values.get("min_replicas", 0)
    burst = values.get("enable_submission_scale", False)
    assert minimum in (0, 1)
    assert minimum == 0 or values.get("enable_submission_warm", False)
    assert not burst or minimum == 1
    assert not judge or values.get("llm_budget_run_id") == "judging-2026-10"
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
    vault = az("keyvault", "show", "--resource-group", GROUP, "--name", VAULT)
    assert vault["properties"]["enableRbacAuthorization"]
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
        rules = ingress.get("ipSecurityRestrictions") or []
        if name == "web":
            if judge:
                assert not rules
            else:
                assert len(rules) == 1 and rules[0]["action"] == "Allow"
                assert rules[0]["ipAddressRange"] == values["owner_ipv4"] + "/32"
            assert ingress["external"]
        else:
            assert not ingress["external"] and not rules
            assert ".internal." in ingress["fqdn"]
        assert not ingress.get("allowInsecure", False)
        assert properties["configuration"]["activeRevisionsMode"] == "Single"
        # ARM can return null for the documented default minimum of zero.
        scale = properties["template"]["scale"]
        maximum = 3 if name == "api" and burst else 1
        assert (scale.get("minReplicas") or 0) == minimum
        assert scale["maxReplicas"] == maximum
        scale_rules = scale.get("rules") or []
        if name == "api" and burst:
            assert len(scale_rules) == 1 and scale_rules[0]["name"] == "submission-http"
            assert scale_rules[0]["http"]["metadata"] == {"concurrentRequests": "5"}
            assert not scale_rules[0].get("custom") and not scale_rules[0].get("azureQueue")
        else:
            assert not scale_rules
        container = properties["template"]["containers"][0]
        assert container["image"].endswith(":" + values["image_tag"])
        assert container["resources"]["cpu"] == 0.25 and container["resources"]["memory"] == "0.5Gi"
        assert properties["provisioningState"] == "Succeeded"
        if name == "api":
            env = {item["name"]: item for item in container["env"]}
            assert not container.get("command") and not container.get("args")
            assert not ({"WEB_CONCURRENCY", "UVICORN_WORKERS"} & env.keys())
            assert env["LLM_PROVIDER"]["value"] == ("openai_compat" if real_llm else "mock")
            assert env["LLM_REAL_CALLS_APPROVED"]["value"] == ("1" if real_llm else "0")
            assert env["LLM_DAILY_BUDGET_USD"]["value"] == ("1" if judge else "3")
            assert env["LLM_MODEL_ROUTE"]["value"] == "default"
            assert env["LLM_BUDGET_RUN_ID"].get("value", "") == values.get("llm_budget_run_id", "")
            assert env["AGENT_SYSTEM"]["value"] == "P"
            assert env["OPS_BACKEND"]["value"] == "postgres"
            assert env["LEDGER_BACKEND"]["value"] == "serving"
            assert env["PGSSLMODE"]["value"] == "verify-full"
            assert env["PGUSER"]["value"] == "aclara_app"
            assert env["PGPASSWORD"]["secretRef"] == "postgres-app"
            assert env["DEMO_PASSWORD"]["secretRef"] == "demo-password"
            secrets = properties["configuration"]["secrets"]
            expected_secrets = {"postgres-app", "demo-password"}
            if judge:
                expected_secrets.update({"judge-persona", "judge-password"})
                assert env["JUDGE_ACCESS_ENABLED"]["value"] == "true"
                for field, secret in (
                    ("JUDGE_PERSONA", "judge-persona"),
                    ("JUDGE_PASSWORD", "judge-password"),
                ):
                    assert env[field]["secretRef"] == secret and "value" not in env[field]
            else:
                assert env.get("JUDGE_ACCESS_ENABLED", {}).get("value", "false") == "false"
            if real_llm:
                expected_secrets.update({"openrouter-api-key", "typesafe-api-key"})
                assert env["TYPESAFE_API_KEY"]["secretRef"] == "typesafe-api-key"
                assert env["OPENROUTER_API_KEY"]["secretRef"] == "openrouter-api-key"
                assert not env["OPENROUTER_API_KEY"].get("value")
            else:
                assert "OPENROUTER_API_KEY" not in env
            assert {item["name"] for item in secrets} == expected_secrets
            assert all(
                item.get("keyVaultUrl", "").startswith(f"https://{VAULT}.vault.azure.net/")
                for item in secrets
            )
            assert all(
                item["identity"].lower() in {identity.lower() for identity in identities}
                for item in secrets
            )
            assert all(not item.get("value") for item in secrets)
            if judge:
                for secret in ("judge-persona", "judge-password"):
                    reference = next(item for item in secrets if item["name"] == secret)
                    assert (
                        reference["keyVaultUrl"]
                        == f"https://{VAULT}.vault.azure.net/secrets/{secret}"
                    )
                    entry = next(
                        value
                        for key, value in identities.items()
                        if key.lower() == reference["identity"].lower()
                    )
                    scope = vault["id"] + "/secrets/" + secret
                    grants = az(
                        "role",
                        "assignment",
                        "list",
                        "--assignee-object-id",
                        entry["principalId"],
                        "--scope",
                        scope,
                        "--include-inherited",
                        "--fill-principal-name",
                        "false",
                    )
                    assert grants and all(
                        grant["scope"].lower() == scope.lower()
                        and grant["roleDefinitionName"] == "Key Vault Secrets User"
                        for grant in grants
                    )
        sys.stdout.write(
            f"Verified {name}: approved HTTPS boundary, single revision, replicas {minimum}..{maximum}, SHA image, managed registry identity.\n"
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
