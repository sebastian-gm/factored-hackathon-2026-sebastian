"""Configured/offline target resolution and credential/query rejection."""

from importlib import import_module

import pytest
from scripts import azure_targets


def test_configured_targets_need_no_cloud_call(monkeypatch):
    def forbidden(*_args):
        raise AssertionError("Configured/offline imports must not contact Azure")

    monkeypatch.setattr(azure_targets, "az", forbidden)
    monkeypatch.setenv("AZURE_WEB_URL", "https://demo.example.org/")
    monkeypatch.setenv("AZURE_POSTGRES_HOST", "db.example.org")
    assert azure_targets.app_url("web") == "https://demo.example.org"
    assert azure_targets.database_host() == "db.example.org"
    for module in (
        "scripts.azure_llm_smoke",
        "scripts.azure_latency_probe",
        "scripts.azure_migrate_ops",
        "scripts.serving_browser",
    ):
        import_module(module)


@pytest.mark.parametrize(
    "value",
    [
        "http://demo.example.org",
        "https://user:pass@demo.example.org",
        "https://demo.example.org/?token=fake",
        "https://demo.example.org/#token",
        "https://demo.example.org/private",
    ],
)
def test_reject_credentialed_or_non_origin_target(monkeypatch, value):
    monkeypatch.setenv("AZURE_WEB_URL", value)
    with pytest.raises(ValueError, match="uncredentialed HTTPS origin"):
        azure_targets.app_url("web")


def test_default_uses_approved_inventory_lazily(monkeypatch):
    monkeypatch.delenv("AZURE_API_URL", raising=False)
    monkeypatch.delenv("AZURE_POSTGRES_HOST", raising=False)
    calls = []

    def inventory(*args):
        calls.append(args)
        if args[0] == "containerapp":
            return {"properties": {"configuration": {"ingress": {"fqdn": "api.example.org"}}}}
        return {"fullyQualifiedDomainName": "db.example.org"}

    monkeypatch.setattr(azure_targets, "az", inventory)
    assert calls == []
    assert azure_targets.app_url("api") == "https://api.example.org"
    assert azure_targets.database_host() == "db.example.org"
    assert len(calls) == 2
    assert all(azure_targets.GROUP in call for call in calls)
