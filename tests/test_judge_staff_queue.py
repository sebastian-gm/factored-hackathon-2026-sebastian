"""Authored ES/PT: own-visit judge delegation never widens bank or staff scope."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from test_judge_profiles import AuthoredLedger, application, authenticate, headers, select
from test_staff_realm_queue import invitation, join
from test_staff_realm_revocation import restarted

from aclara.api import staff_queue
from aclara.handoff import queue
from aclara.ops.store import Store


class CustomerProfiles(AuthoredLedger):
    def personas(self):
        return [replace(persona, role="customer") for persona in super().personas()]


@pytest.fixture
def persisted_store():
    dsn = os.getenv("TEST_OPS_DSN")
    store = Store(dsn) if dsn else None
    try:
        yield store
    finally:
        if store is not None:
            store.close()


def handoff(client, token, profile="mx-es"):
    cid = client.post("/chat/sessions", headers=headers(token)).json()["conversation_id"]
    message = (
        "Quero falar com um atendente; meu CPF é 123.456.789-01"
        if profile == "pt"
        else "Quiero hablar con un agente; mi correo es fixture@example.invalid"
    )
    result = client.post(
        f"/chat/sessions/{cid}/messages", headers=headers(token), json={"message": message}
    )
    assert result.status_code == 200 and result.json()["verified"]
    return result.json()["handoff"]["handoff_id"], cid


def root_scope(app, token):
    return app.state.judge_sessions.controller_scope(app.state.sessions[token].judge_reference)


def grant_state(app, token, invited):
    with app.state.store.transaction(root_scope(app, token)):
        key = "realm-invite:" + hashlib.sha256(invited.encode()).hexdigest()
        return app.state.idempotency.get(key), app.state.idempotency.get("judge-staff-realm")


@pytest.mark.parametrize("profile", ["mx-es", "pt"])
def test_own_visit_self_redemption_masked_claim_and_unchanged_authority(
    monkeypatch, profile, persisted_store
):
    app, settings, client = application(
        monkeypatch, store=persisted_store, ledger=CustomerProfiles()
    )
    root = authenticate(client, settings)
    assert join(client, root, "not-an-invitation-token").status_code == 403
    token = select(client, root, profile)
    before = client.get("/me", headers=headers(token)).json()
    bank_before = client.get("/transactions", headers=headers(token)).json()
    key, cid = handoff(client, token, profile)
    path = f"/agent/handoffs/{key}"
    body = dict(expected_version=1, idempotency_key="judge_self_claim_001")
    assert client.get("/agent/handoffs", headers=headers(token)).status_code == 403
    assert client.post(path + "/claim", headers=headers(token), json=body).status_code == 403
    invited = invitation(client, token)
    assert join(client, token, invited).json() == dict(joined=True, verified=True)
    assert join(client, token, invited).json()["verified"]  # Same controller, idempotent.
    packets = client.get("/agent/handoffs", headers=headers(token)).json()
    assert len(packets) == 1 and packets[0]["handoff_id"] == key
    assert packets[0]["scope"] == "current_realm"
    assert packets[0]["transcript_ref"] is None and packets[0]["trace_ref"] is None
    encoded = json.dumps(packets)
    for private in ["123.456.789-01", "fixture@example.invalid", "judge-customer", token, invited]:
        assert private not in encoded
    claimed = client.post(path + "/claim", headers=headers(token), json=body)
    assert claimed.status_code == 200 and claimed.json()["status"] == "claimed"
    assert claimed.json()["version"] == 2 and claimed.json()["verified"]
    assert client.get(path, headers=headers(token)).json() == claimed.json()
    assert client.post(path + "/claim", headers=headers(token), json=body).json() == claimed.json()
    assert client.post(path + "/resolve", headers=headers(token), json=body).status_code == 409
    assert client.get("/me", headers=headers(token)).json() == before
    assert client.get("/transactions", headers=headers(token)).json() == bank_before
    for endpoint in ["/ops/snapshot", f"/agent/conversations/{cid}"]:
        assert client.get(endpoint, headers=headers(token)).status_code == 403


def test_other_visits_owner_invitations_and_replays_cannot_grant_membership(
    monkeypatch, persisted_store
):
    app, settings, client = application(monkeypatch, store=persisted_store)
    first = select(client, authenticate(client, settings), "mx-es")
    key, _ = handoff(client, first)
    invited = invitation(client, first)
    other = select(client, authenticate(client, settings), "pt")
    assert join(client, other, invited).status_code == 403
    grant, member = grant_state(app, first, invited)
    assert grant["used_by"] is None and member is None
    assert join(client, first, invited).status_code == 200
    assert join(client, other, invited).status_code == 403
    assert join(client, other, invitation(client, other)).status_code == 200
    assert client.get("/agent/handoffs", headers=headers(other)).json() == []
    assert client.get(f"/agent/handoffs/{key}", headers=headers(other)).status_code == 404
    assert (
        client.post(
            f"/agent/handoffs/{key}/claim",
            headers=headers(other),
            json=dict(expected_version=1, idempotency_key="cross_visit_claim_001"),
        ).status_code
        == 404
    )
    owner = authenticate(
        client, settings, username="authored.mx-es", password=settings.demo_password
    )
    assert join(client, first, invitation(client, owner)).status_code == 403
    assert join(client, owner, invited).status_code == 403


def test_same_controller_grant_survives_restart_and_valid_profile_switch(
    monkeypatch, persisted_store
):
    app, settings, client = application(monkeypatch, store=persisted_store)
    token = select(client, authenticate(client, settings), "mx-es")
    first, _ = handoff(client, token)
    assert join(client, token, invitation(client, token)).status_code == 200
    _, _, current = restarted(monkeypatch, app, settings, "unchanged")
    assert current.get("/agent/handoffs", headers=headers(token)).status_code == 200
    active = select(current, token, "pt")
    second, _ = handoff(current, active, "pt")
    assert current.get("/agent/handoffs", headers=headers(token)).status_code == 401
    assert {
        p["handoff_id"] for p in current.get("/agent/handoffs", headers=headers(active)).json()
    } == {first, second}
    assert (
        current.post(
            f"/agent/handoffs/{first}/claim",
            headers=headers(active),
            json=dict(expected_version=1, idempotency_key="switch_claim_001"),
        ).status_code
        == 200
    )
    assert (
        current.get("/transactions", headers=headers(active)).json()[0]["merchant"] == "Fixture pt"
    )
    assert current.get(f"/handoffs/{first}", headers=headers(active)).status_code == 404


@pytest.mark.parametrize(
    "change", ["off", "password", "configuration", "dataset", "logout", "expiry"]
)
@pytest.mark.parametrize("claimed", [False, True])
def test_revocation_denies_queue_and_cached_claim_without_mutation(
    monkeypatch, change, claimed, persisted_store
):
    app, settings, client = application(monkeypatch, store=persisted_store)
    token = select(client, authenticate(client, settings), "mx-es")
    key, _ = handoff(client, token)
    assert join(client, token, invitation(client, token)).status_code == 200
    path = f"/agent/handoffs/{key}"
    body = dict(expected_version=1, idempotency_key="revoked_claim_001")
    if claimed:
        assert client.post(path + "/claim", headers=headers(token), json=body).status_code == 200
    principal = app.state.sessions[token]
    realm = staff_queue.customer_realm(principal)

    def snapshot():
        with (
            app.state.store.transaction(staff_queue.scope(principal)),
            queue.context(app.state.store, realm, staff=True),
        ):
            return dict(queue.read(app.state.store, realm, key)[0])

    before = snapshot()
    if change == "logout":
        assert client.post("/auth/logout", headers=headers(token)).json()["verified"]
        current = client
    elif change == "expiry":
        with app.state.store.transaction(root_scope(app, token)):
            digest = principal.judge_reference.digest
            root = app.state.store.get("sessions", digest)
            root["expires_at"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
            app.state.store.put("sessions", digest, root)
        current = client
    else:
        _, _, current = restarted(monkeypatch, app, settings, change)
    assert current.get("/agent/handoffs", headers=headers(token)).status_code in {401, 403}
    assert current.get(path, headers=headers(token)).status_code in {401, 403}
    assert current.post(path + "/claim", headers=headers(token), json=body).status_code in {
        401,
        403,
    }
    assert snapshot() == before


def test_profile_switch_before_redemption_lock_consumes_nothing(monkeypatch, persisted_store):
    app, settings, client = application(monkeypatch, store=persisted_store)
    token = select(client, authenticate(client, settings), "mx-es")
    invited = invitation(client, token)
    principal = replace(
        app.state.sessions[token], capability_digest=hashlib.sha256(token.encode()).hexdigest()
    )
    original = app.state.sessions.auth_context

    def switch_before_lock(value):
        origin = original(value)
        if value == invited:
            select(client, token, "pt")
        return origin

    monkeypatch.setattr(app.state.sessions, "auth_context", switch_before_lock)
    with pytest.raises(HTTPException) as error:
        staff_queue.join(app, principal, staff_queue.RealmJoin(invitation=invited))
    assert error.value.status_code in {401, 403}
    grant, member = grant_state(app, token, invited)
    assert grant["used_by"] is None and member is None


@pytest.mark.parametrize("expired", [False, True])
def test_forged_or_expired_own_invitation_cannot_attach_judge(
    monkeypatch, expired, persisted_store
):
    app, settings, client = application(monkeypatch, store=persisted_store)
    token = select(client, authenticate(client, settings), "pt")
    invited = invitation(client, token)
    if expired:
        with app.state.store.transaction(root_scope(app, token)):
            key = "realm-invite:" + hashlib.sha256(invited.encode()).hexdigest()
            grant = app.state.idempotency[key]
            grant["expires_at"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
            app.state.idempotency[key] = grant
        rejected = invited
    else:
        rejected = invited[:-1] + ("A" if invited[-1] != "A" else "B")
    assert join(client, token, rejected).status_code == 403
    assert grant_state(app, token, invited)[1] is None
