"""Authored credentials/accounts only. No Azure or provider requests."""

import json
import secrets
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from aclara.api.app import create_app
from aclara.api.judge_access import judge_alias
from aclara.bank.serving import Persona
from aclara.settings import Settings


def configured():
    return Settings(
        demo_username="authored.owner",
        demo_password=secrets.token_urlsafe(32),
        judge_access_enabled=True,
        judge_password=secrets.token_urlsafe(32),
        judge_persona=json.dumps(
            {"username": "judge.authored", "source_username": "authored.owner"}
        ),
    )


def test_off_switch_ignores_all_judge_material():
    password = secrets.token_urlsafe(32)
    assert judge_alias(Settings(judge_persona="invalid", judge_password=password), {}) is None
    client = TestClient(create_app(Settings(demo_username="owner", demo_password=password)))
    assert (
        client.post(
            "/auth/login", json={"username": "judge.authored", "password": password}
        ).status_code
        == 401
    )


@pytest.mark.parametrize("role", ["customer", "agent", "ops"])
def test_alias_inherits_only_existing_trusted_scope_and_role(role):
    settings = configured()
    original = Persona("authored.owner", "authored-customer", "pt-BR", role)
    alias = judge_alias(settings, {original.username: original})
    assert alias == replace(original, username="judge.authored")


@pytest.mark.parametrize(
    "definition",
    [
        None,
        [],
        {"username": "judge.new", "source_username": "absent"},
        {"username": "authored.owner", "source_username": "authored.owner"},
        {"username": "judge.new", "source_username": "authored.owner", "role": "ops"},
        {"username": "judge.new", "source_username": "authored.owner", "customer_id": "other"},
    ],
)
def test_definition_cannot_claim_role_customer_or_unknown_source(definition):
    settings = replace(configured(), judge_persona=json.dumps(definition))
    with pytest.raises(ValueError, match="Invalid or unavailable"):
        judge_alias(
            settings, {"authored.owner": Persona("authored.owner", "fixture", "es-MX", "customer")}
        )


def test_separate_password_otp_and_authenticated_routes(monkeypatch):
    monkeypatch.delenv("LLM_BUDGET_RUN_ID", raising=False)
    settings = configured()
    monkeypatch.setattr(
        "aclara.api.app.demo_story_mappings", lambda *_: {"authored.owner": ["explain"]}
    )
    app = create_app(settings)
    assert app.state.demo_stories["judge.authored"] == ["explain"]
    client = TestClient(app)
    for username, password in [
        ("judge.authored", settings.demo_password),
        ("authored.owner", settings.judge_password),
    ]:
        assert (
            client.post(
                "/auth/login", json={"username": username, "password": password}
            ).status_code
            == 401
        )
    assert client.get("/transactions").status_code == 401
    challenge = client.post(
        "/auth/login", json={"username": "judge.authored", "password": settings.judge_password}
    ).json()
    headers = {"X-Preauth-Token": challenge["preauth_token"]}
    code = client.get(f"/auth/challenges/{challenge['challenge_id']}/sms", headers=headers).json()[
        "code"
    ]
    wrong = "000000" if code != "000000" else "111111"
    assert (
        client.post(
            "/auth/otp/verify",
            headers=headers,
            json={"challenge_id": challenge["challenge_id"], "code": wrong},
        ).status_code
        == 401
    )
    session = client.post(
        "/auth/otp/verify",
        headers=headers,
        json={"challenge_id": challenge["challenge_id"], "code": code},
    )
    assert session.status_code == 200
    token = session.json()["access_token"]
    auth = {"Authorization": "Bearer " + token}
    identity = client.get("/me", headers=auth).json()
    assert identity["username"] == "judge.authored" and identity["role"] == "customer"
    assert client.get("/agent/handoffs", headers=auth).status_code == 403
    assert settings.judge_password not in client.get("/personas").text
    assert settings.judge_password not in repr(settings)


def test_judge_mode_rejects_shared_password_smoke_budget_or_larger_daily_cap(monkeypatch):
    settings = configured()
    personas = {"authored.owner": Persona("authored.owner", "fixture", "es-MX", "customer")}
    with pytest.raises(ValueError):
        judge_alias(replace(settings, judge_password=settings.demo_password), personas)
    monkeypatch.setenv("LLM_BUDGET_RUN_ID", "after-v2-release-smoke")
    with pytest.raises(ValueError):
        judge_alias(settings, personas)
    monkeypatch.delenv("LLM_BUDGET_RUN_ID")
    monkeypatch.setenv("LLM_DAILY_BUDGET_USD", "4")
    with pytest.raises(ValueError):
        judge_alias(replace(settings, llm_provider="openai_compat"), personas)
