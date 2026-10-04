"""Authored ARM metadata; readback performs no Azure or model requests."""

from __future__ import annotations

import pytest
from scripts import azure_verify
from scripts.azure_dev import STORAGE, VAULT


def authored(monkeypatch, tmp_path, *, judge=False, warm=False, burst=False):
    values = dict(
        subscription_id="authored-subscription",
        owner_ipv4="192.0.2.10",
        image_tag="a" * 40,
        enable_real_llm=True,
        enable_judge_access=judge,
        enable_submission_warm=warm,
        enable_submission_scale=burst,
        min_replicas=int(warm),
        llm_budget_run_id="judging-2026-10" if judge else "",
        budget_email="authored@example.invalid",
    )
    vault = dict(id="/authored/vault", properties=dict(enableRbacAuthorization=True))
    apps = {}
    for name in ["api", "web"]:
        names = ["postgres-app", "demo-password", "openrouter-api-key", "typesafe-api-key"]
        if judge:
            names.extend(["judge-persona", "judge-password"])
        env = {
            "LLM_PROVIDER": "openai_compat",
            "LLM_REAL_CALLS_APPROVED": "1",
            "LLM_DAILY_BUDGET_USD": "1" if judge else "3",
            "LLM_MODEL_ROUTE": "default",
            "LLM_BUDGET_RUN_ID": values["llm_budget_run_id"],
            "AGENT_SYSTEM": "P",
            "OPS_BACKEND": "postgres",
            "LEDGER_BACKEND": "serving",
            "PGSSLMODE": "verify-full",
            "PGUSER": "aclara_app",
        }
        if judge:
            env["JUDGE_ACCESS_ENABLED"] = "true"
        bindings = {
            "PGPASSWORD": "postgres-app",
            "DEMO_PASSWORD": "demo-password",
            "OPENROUTER_API_KEY": "openrouter-api-key",
            "TYPESAFE_API_KEY": "typesafe-api-key",
        }
        if judge:
            bindings.update({"JUDGE_PERSONA": "judge-persona", "JUDGE_PASSWORD": "judge-password"})
        apps[name] = dict(
            identity=dict(
                type="UserAssigned",
                userAssignedIdentities={
                    "/authored/identity": {"principalId": "authored-principal"}
                },
            ),
            properties=dict(
                provisioningState="Succeeded",
                configuration=dict(
                    activeRevisionsMode="Single",
                    registries=[dict(identity="/authored/identity")],
                    ingress=dict(
                        external=name == "web",
                        allowInsecure=False,
                        fqdn="authored.internal.invalid" if name == "api" else "authored.invalid",
                        ipSecurityRestrictions=[
                            dict(action="Allow", ipAddressRange="192.0.2.10/32")
                        ]
                        if name == "web" and not judge
                        else [],
                    ),
                    secrets=[
                        dict(
                            name=s,
                            keyVaultUrl=f"https://{VAULT}.vault.azure.net/secrets/{s}",
                            identity="/authored/identity",
                        )
                        for s in names
                    ],
                ),
                template=dict(
                    scale=dict(
                        minReplicas=int(warm),
                        maxReplicas=3 if name == "api" and burst else 1,
                        rules=[
                            dict(
                                name="submission-http",
                                http=dict(metadata=dict(concurrentRequests="5")),
                            )
                        ]
                        if name == "api" and burst
                        else [],
                    ),
                    containers=[
                        dict(
                            image="authored:" + values["image_tag"],
                            resources=dict(cpu=0.25, memory="0.5Gi"),
                            env=[dict(name=k, value=v) for k, v in env.items()]
                            + [dict(name=k, secretRef=v) for k, v in bindings.items()],
                        )
                    ],
                ),
            ),
        )
    calls = []

    def fake_az(*args):
        calls.append(args)
        if args == ("account", "show"):
            return dict(id=values["subscription_id"], name="Seb Azure Sandbox")
        if args[0] == "keyvault":
            return vault
        if args[0] == "role":
            scope = args[args.index("--scope") + 1]
            return [dict(scope=scope, roleDefinitionName="Key Vault Secrets User")]
        if args[0] == "rest":
            url = args[args.index("--url") + 1]
            for name in apps:
                if "/ca-" + name + "-" in url:
                    return apps[name]
            return dict(
                properties=dict(
                    amount=50,
                    currentSpend=dict(unit="USD"),
                    notifications={
                        str(n): dict(
                            threshold=n,
                            enabled=True,
                            contactEmails=[values["budget_email"]],
                            thresholdType="Actual",
                        )
                        for n in [60, 100]
                    },
                )
            )
        if args[0] == "postgres":
            if args[2] == "show":
                return dict(sku=dict(name="Standard_B1ms"), storage=dict(storageSizeGb=32))
            if args[2] == "firewall-rule":
                sentinel = "0.0.0.0"  # noqa: S104 -- authored Azure firewall metadata
                return [
                    dict(startIpAddress=s, endIpAddress=s) for s in [values["owner_ipv4"], sentinel]
                ]
            return dict(value="on")
        if args[0] == "storage":
            assert args[-1] == STORAGE
            return dict(
                allowBlobPublicAccess=False,
                allowSharedKeyAccess=False,
                networkRuleSet=dict(
                    defaultAction="Deny", ipRules=[dict(ipAddressOrRange=values["owner_ipv4"])]
                ),
            )
        if args[0] == "acr":
            return dict(sku=dict(name="Basic"), adminUserEnabled=False)
        raise AssertionError("Unexpected authored readback request")

    monkeypatch.setattr(azure_verify, "az", fake_az)
    monkeypatch.setattr(azure_verify, "read_variables", lambda: values)
    monkeypatch.setattr(azure_verify, "ROOT", tmp_path)
    (tmp_path / "artifacts/azure").mkdir(parents=True)
    return apps, values, calls


@pytest.mark.parametrize(
    "judge,warm,burst", [(False, False, False), (False, True, True), (True, True, True)]
)
def test_readback_supports_approved_modes_without_cloud_calls(
    monkeypatch, tmp_path, judge, warm, burst
):
    _, _, calls = authored(monkeypatch, tmp_path, judge=judge, warm=warm, burst=burst)
    azure_verify.main()
    assert (tmp_path / "artifacts/azure/verified.json").is_file()
    assert len([c for c in calls if c[0] == "role"]) == (2 if judge else 0)


@pytest.mark.parametrize(
    "change",
    [
        "public_api",
        "anonymous_judge_cap",
        "replicas",
        "http_threshold",
        "workers",
        "literal_secret",
    ],
)
def test_readback_rejects_authority_or_scaling_drift(monkeypatch, tmp_path, change):
    apps, _, _ = authored(monkeypatch, tmp_path, judge=True, warm=True, burst=True)
    api = apps["api"]["properties"]
    container = api["template"]["containers"][0]
    if change == "public_api":
        api["configuration"]["ingress"]["external"] = True
    elif change == "anonymous_judge_cap":
        next(e for e in container["env"] if e["name"] == "LLM_DAILY_BUDGET_USD")["value"] = "3"
    elif change == "replicas":
        api["template"]["scale"]["maxReplicas"] = 4
    elif change == "http_threshold":
        api["template"]["scale"]["rules"][0]["http"]["metadata"]["concurrentRequests"] = "10"
    elif change == "workers":
        container["env"].append(dict(name="WEB_CONCURRENCY", value="2"))
    else:
        api["configuration"]["secrets"][0]["value"] = "authored-literal-secret"
    with pytest.raises(AssertionError):
        azure_verify.main()
    assert not (tmp_path / "artifacts/azure/verified.json").exists()


def test_judge_readback_rejects_inherited_vault_wide_grant(monkeypatch, tmp_path):
    authored(monkeypatch, tmp_path, judge=True, warm=True, burst=True)
    original = azure_verify.az

    def widened(*args):
        result = original(*args)
        if args[0] == "role":
            return result + [
                dict(scope="/authored/vault", roleDefinitionName="Key Vault Secrets User")
            ]
        return result

    monkeypatch.setattr(azure_verify, "az", widened)
    with pytest.raises(AssertionError):
        azure_verify.main()
    assert not (tmp_path / "artifacts/azure/verified.json").exists()
