"""Author-created profiles only; no organizer records, credentials or paid calls."""

from __future__ import annotations

import hashlib
import json
import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from aclara.api.app import create_app
from aclara.api.judge_access import PROFILE_LOCALES, judge_configuration
from aclara.bank.repository import Customer, TransactionRepository
from aclara.bank.serving import Persona
from aclara.handoff.routing import AgentDirectory
from aclara.settings import Settings


class AuthoredLedger(TransactionRepository):
    def __init__(self):
        original = TransactionRepository()._rows[0]
        rows = tuple(
            replace(
                original,
                record_id="judge-fixture-" + key,
                customer_id="judge-customer-" + key,
                product_id="judge-product-" + key,
                transaction_type="Purchase",
                transaction_status="Approved",
                merchant_name="Fixture " + key,
                amount=20,
                currency="USD",
                transaction_date=datetime(2026, 6, 15, 12, tzinfo=UTC),
            )
            for key in PROFILE_LOCALES
        )
        super().__init__(
            rows,
            customers=tuple(Customer(row.customer_id) for row in rows),
        )

    def personas(self):
        return [
            Persona("authored." + key, "judge-customer-" + key, locale, "ops")
            for key, locale in PROFILE_LOCALES.items()
        ]

    def directory(self):
        return AgentDirectory()

    def ready(self):
        return True


def authored_settings():
    return Settings(
        demo_password=secrets.token_urlsafe(32),
        judge_access_enabled=True,
        judge_password=secrets.token_urlsafe(32),
        judge_persona=json.dumps(
            {
                "username": "judge.authored",
                "profiles": {key: "authored." + key for key in PROFILE_LOCALES},
            }
        ),
        allow_demo_reset=True,
    )


def application(monkeypatch, *, store=None, settings=None, ledger=None):
    monkeypatch.delenv("LLM_BUDGET_RUN_ID", raising=False)
    # A fake serving boundary for unit tests only. Real bank RLS is covered below.
    monkeypatch.setattr("aclara.api.app.ServingRepository", AuthoredLedger)
    settings = settings or authored_settings()
    app = create_app(settings, ledger or AuthoredLedger(), store=store)
    return app, settings, TestClient(app)


def authenticate(client, settings, username="judge.authored", password=None):
    response = client.post(
        "/auth/login", json={"username": username, "password": password or settings.judge_password}
    )
    assert response.status_code == 200
    login = response.json()
    pre = {"X-Preauth-Token": login["preauth_token"]}
    code = client.get(f"/auth/challenges/{login['challenge_id']}/sms", headers=pre).json()["code"]
    otp = client.post(
        "/auth/otp/verify", headers=pre, json={"challenge_id": login["challenge_id"], "code": code}
    )
    assert otp.status_code == 200
    # Consumed challenge cannot create a second account capability.
    assert (
        client.post(
            "/auth/otp/verify",
            headers=pre,
            json={"challenge_id": login["challenge_id"], "code": code},
        ).status_code
        == 401
    )
    return otp.json()["access_token"]


def headers(token):
    return {"Authorization": "Bearer " + token}


def select(client, token, profile):
    result = client.post(
        "/auth/judge/profile", headers=headers(token), json={"profile_id": profile}
    )
    assert result.status_code == 200
    assert result.json()["verified"] is True
    return result.json()["access_token"]


def test_picker_has_no_bank_staff_or_step_up_authority(monkeypatch):
    app, settings, client = application(monkeypatch)
    token = authenticate(client, settings)
    identity = client.get("/me", headers=headers(token)).json()
    assert identity["profile_selection_required"] and identity["role"] == "customer"
    views = client.get("/auth/judge/profiles", headers=headers(token))
    assert views.status_code == 200
    assert [p["profile_id"] for p in views.json()["profiles"]] == list(PROFILE_LOCALES)
    assert all(
        x not in views.text for x in ["customer_id", "source_username", settings.judge_password]
    )
    for path in ["/transactions", "/accounts", "/agent/handoffs", "/ops/snapshot"]:
        assert client.get(path, headers=headers(token)).status_code == 403
    for path in ["/chat/sessions", "/auth/step-up", "/ops/reset/proposal"]:
        assert client.post(path, headers=headers(token)).status_code == 403
    assert client.post("/auth/logout", headers=headers(token)).json()["verified"]
    assert client.get("/me", headers=headers(token)).status_code == 401


def test_restart_preserves_current_scope_but_never_extends_login(monkeypatch):
    app, settings, client = application(monkeypatch)
    root = authenticate(client, settings)
    token = select(client, root, "pt")
    _, _, restarted = application(monkeypatch, store=app.state.store, settings=settings)
    assert (
        restarted.get("/transactions", headers=headers(token)).json()[0]["merchant"] == "Fixture pt"
    )
    assert restarted.get("/me", headers=headers(root)).status_code == 401
    p = app.state.sessions[token]
    # A modified child cannot extend the independently stored controller deadline.
    app.state.sessions[token] = replace(p, expires_at=p.expires_at + timedelta(hours=1))
    assert restarted.get("/me", headers=headers(token)).status_code == 401
    app.state.sessions[token] = replace(p, expires_at=datetime.now(UTC) - timedelta(seconds=1))
    assert restarted.get("/me", headers=headers(token)).status_code == 401


def test_capability_cannot_be_rebased_onto_another_profile_realm(monkeypatch):
    app, settings, client = application(monkeypatch)
    token = select(client, authenticate(client, settings), "mx-es")
    p = app.state.sessions[token]
    forged = app.state.judge_sessions.profile_realm("pt") + "_" + token.split("_", 1)[1]
    assert client.get("/transactions", headers=headers(forged)).status_code == 401
    assert client.get("/transactions", headers=headers(token)).status_code == 200
    # Even a corrupt persisted customer claim cannot pass the trusted binding check.
    app.state.sessions[token] = replace(p, customer_id="judge-customer-pt")
    assert client.get("/transactions", headers=headers(token)).status_code == 401


def test_all_profiles_rotate_scope_ttl_and_no_customer_identity_is_returned(monkeypatch):
    app, settings, client = application(monkeypatch)
    token = authenticate(client, settings)
    original = app.state.sessions[token]
    scopes = set()
    for key, locale in PROFILE_LOCALES.items():
        previous = token
        token = select(client, token, key)
        principal = app.state.sessions[token]
        scopes.add((principal.customer_id, principal.run_id, principal.session_id))
        assert token != previous and principal.otp_at == original.otp_at
        assert principal.expires_at == original.expires_at and principal.step_up_at is None
        assert client.get("/me", headers=headers(previous)).status_code == 401
        identity = client.get("/me", headers=headers(token)).json()
        assert identity["judge_profile_id"] == key and identity["locale"] == locale
        assert identity.get("profile_selection_required", False) is False
        rows = client.get("/transactions", headers=headers(token))
        assert len(rows.json()) == 1 and rows.json()[0]["merchant"] == "Fixture " + key
        assert "judge-customer" not in rows.text and "customer_id" not in rows.text
    assert len(scopes) == 4


@pytest.mark.parametrize(
    "body",
    [
        {"profile_id": "unknown"},
        {"profile_id": "mx-es", "customer_id": "other"},
        {"profile_id": "mx-es", "role": "ops"},
        {"profile_id": "mx-es", "session_id": "fixed"},
        {"profile_id": "mx-es", "run_id": "fixed"},
    ],
)
def test_caller_cannot_supply_identity_role_or_session(monkeypatch, body):
    _, settings, client = application(monkeypatch)
    token = authenticate(client, settings)
    assert client.post("/auth/judge/profile", headers=headers(token), json=body).status_code == 422
    assert client.get("/me", headers=headers(token)).status_code == 200


def test_owner_and_unauthed_cannot_select_and_passwords_are_separate(monkeypatch):
    _, settings, client = application(monkeypatch)
    for username, password in [
        ("judge.authored", settings.demo_password),
        ("authored.mx-es", settings.judge_password),
    ]:
        assert (
            client.post(
                "/auth/login", json={"username": username, "password": password}
            ).status_code
            == 401
        )
    owner = authenticate(client, settings, "authored.mx-es", settings.demo_password)
    assert client.get("/auth/judge/profiles", headers=headers(owner)).status_code == 403
    assert client.get("/auth/judge/profiles").status_code == 401
    assert client.get("/transactions", headers=headers(owner)).status_code == 200


def test_old_conversation_case_handoff_proposal_and_otp_cannot_cross_profiles(monkeypatch):
    app, settings, client = application(monkeypatch)
    root = authenticate(client, settings)
    mx = select(client, root, "mx-es")
    mx_headers = headers(mx)
    cid = client.post("/chat/sessions", headers=mx_headers).json()["conversation_id"]
    proposal = client.post(
        f"/chat/sessions/{cid}/messages",
        headers=mx_headers,
        json={"message": "No hice el cargo de Fixture mx-es por 20 USD"},
    ).json()
    assert proposal["outcome"] == "dispute_proposed"
    case = client.post(
        f"/chat/sessions/{cid}/confirm",
        headers=mx_headers,
        json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True},
    ).json()
    assert case["verified"]
    handoff = client.post(
        f"/chat/sessions/{cid}/messages",
        headers=mx_headers,
        json={"message": "Quiero hablar con una persona"},
    ).json()
    challenge = client.post("/auth/step-up", headers=mx_headers).json()
    pre = {"X-Preauth-Token": challenge["preauth_token"]}
    code = client.get(f"/auth/challenges/{challenge['challenge_id']}/sms", headers=pre).json()[
        "code"
    ]
    co = select(client, mx, "co-es")
    for path in [
        f"/disputes/{case['case']['case_id']}",
        f"/agent/handoffs/{handoff['handoff']['handoff_id']}",
    ]:
        assert client.get(path, headers=headers(co)).status_code == 404
    assert (
        client.post(
            f"/chat/sessions/{cid}/confirm",
            headers=headers(co),
            json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/auth/step-up/verify",
            headers={**headers(co), **pre},
            json={"challenge_id": challenge["challenge_id"], "code": code},
        ).status_code
        == 404
    )
    returned = select(client, co, "mx-es")
    assert (
        client.get(f"/disputes/{case['case']['case_id']}", headers=headers(returned)).status_code
        == 404
    )
    assert client.get("/agent/handoffs", headers=headers(returned)).json() == []
    assert (
        client.post(
            "/auth/judge/profile", headers=mx_headers, json={"profile_id": "pt"}
        ).status_code
        == 401
    )
    assert app.state.sessions[returned].session_id != app.state.sessions[mx].session_id


def test_step_up_does_not_travel_and_reset_cannot_erase_controller(monkeypatch):
    app, settings, client = application(monkeypatch)
    token = select(client, authenticate(client, settings), "mx-es")
    p = app.state.sessions[token]
    app.state.sessions[token] = replace(p, step_up_at=datetime.now(UTC), otp_at=datetime.now(UTC))
    assert client.post("/ops/reset/proposal", headers=headers(token)).status_code == 403
    assert (
        client.post(
            "/ops/reset",
            headers=headers(token),
            json={"proposal_hash": "a" * 64, "confirmed": True},
        ).status_code
        == 403
    )
    changed = select(client, token, "pt")
    p = app.state.sessions[changed]
    assert p.step_up_at is None
    assert client.post("/auth/logout", headers=headers(changed)).json()["verified"]
    for old in [token, changed]:
        assert client.get("/me", headers=headers(old)).status_code == 401


@pytest.mark.parametrize("change", ["off", "password", "binding", "dataset"])
def test_restart_revalidates_off_switch_credential_binding_and_dataset(monkeypatch, change):
    app, settings, client = application(monkeypatch)
    token = select(client, authenticate(client, settings), "mx-es")
    ledger = AuthoredLedger()
    if change == "off":
        settings = replace(settings, judge_access_enabled=False)
    elif change == "password":
        settings = replace(settings, judge_password=secrets.token_urlsafe(32))
    elif change == "binding":
        original = ledger.personas
        ledger.personas = lambda: [replace(p, role="customer") for p in original()]
    else:
        ledger.dataset_version += ":new"
    _, _, restarted = application(
        monkeypatch, store=app.state.store, settings=settings, ledger=ledger
    )
    assert restarted.get("/me", headers=headers(token)).status_code == 401


def test_switch_storage_failure_leaves_old_session_live_and_orphan_inactive(monkeypatch):
    app, settings, client = application(monkeypatch)
    token = authenticate(client, settings)
    original_put = app.state.store.put

    def fail_root(table, key, value):
        if value.get("judge_revision") == 1 and value.get("judge_active_digest"):
            raise RuntimeError("authored controller failure")
        original_put(table, key, value)

    monkeypatch.setattr(app.state.store, "put", fail_root)
    with pytest.raises(RuntimeError, match="authored controller"):
        client.post("/auth/judge/profile", headers=headers(token), json={"profile_id": "pt"})
    assert client.get("/me", headers=headers(token)).status_code == 200
    assert len([k for _, table, k in app.state.store.memory if table == "sessions"]) == 1


def test_competing_switches_have_one_winner_and_replay_is_denied(monkeypatch):
    app, settings, client = application(monkeypatch)
    token = authenticate(client, settings)
    principal = replace(
        app.state.sessions[token], capability_digest=hashlib.sha256(token.encode()).hexdigest()
    )
    barrier = Barrier(2)
    manager = app.state.judge_sessions
    original = manager.validate

    def synchronized(p):
        result = original(p)
        if p.judge_profile is None:
            barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(manager, "validate", synchronized)

    def choose(profile):
        try:
            return manager.select(principal, profile)[0]
        except HTTPException as error:
            assert error.status_code == 401
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(choose, ["co-es", "pt"]))
    winners = [x for x in results if x]
    assert len(winners) == 1
    assert client.get("/me", headers=headers(winners[0])).status_code == 200
    assert client.get("/me", headers=headers(token)).status_code == 401


@pytest.mark.parametrize("fault", ["missing", "extra", "same_customer", "locale", "role"])
def test_config_rejects_unreviewed_or_ambiguous_profiles(fault):
    settings = authored_settings()
    personas = {p.username: p for p in AuthoredLedger().personas()}
    definition = json.loads(settings.judge_persona)
    if fault == "missing":
        del definition["profiles"]["pt"]
    elif fault == "extra":
        definition["profiles"]["other"] = "authored.mx-es"
    else:
        p = personas["authored.pt"]
        personas[p.username] = replace(
            p,
            **{
                "same_customer": {"customer_id": personas["authored.mx-es"].customer_id},
                "locale": {"locale": "es-MX"},
                "role": {"role": "admin"},
            }[fault],
        )
    with pytest.raises(ValueError, match="Invalid or unavailable"):
        judge_configuration(replace(settings, judge_persona=json.dumps(definition)), personas)
