"""Mock-only, separately authenticated staff and customer realm authorization."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from test_judge_profiles import application, authenticate, headers, select

from aclara.api import staff_queue
from aclara.ops.store import Scope


def handoff(client, token):
    cid = client.post("/chat/sessions", headers=headers(token)).json()["conversation_id"]
    result = client.post(
        f"/chat/sessions/{cid}/messages",
        headers=headers(token),
        json={
            "message": "Quiero un agente; mi CPF es 123.456.789-01 y mi correo es prueba@example.invalid"
        },
    )
    assert result.status_code == 200 and result.json()["verified"]
    return result.json()["handoff"]["handoff_id"]


def invitation(client, token):
    result = client.post("/handoffs/realm-invitations", headers=headers(token))
    assert result.status_code == 200
    return result.json()["invitation"]


def staff(client, settings, username="authored.mx-es"):
    return authenticate(client, settings, username=username, password=settings.demo_password)


def join(client, token, invite):
    return client.post("/agent/handoff-realm", headers=headers(token), json={"invitation": invite})


def test_same_visit_queue_masking_and_claim_readback_idempotence(monkeypatch):
    app, settings, client = application(monkeypatch)
    customer = select(client, authenticate(client, settings), "mx-es")
    key = handoff(client, customer)
    invited = invitation(client, customer)
    agent = staff(client, settings)
    assert client.get("/agent/handoffs", headers=headers(agent)).json() == []
    assert join(client, agent, invited).json() == dict(joined=True, verified=True)
    assert join(client, agent, invited).json()["verified"]
    packets = client.get("/agent/handoffs", headers=headers(agent)).json()
    assert len(packets) == 1 and packets[0]["handoff_id"] == key
    assert packets[0]["scope"] == "current_realm"
    encoded = json.dumps(packets)
    for private in [
        "123.456.789-01",
        "prueba@example.invalid",
        "judge-customer-mx-es",
        customer,
        invited,
    ]:
        assert private not in encoded
    body = dict(expected_version=1, idempotency_key="authored_claim_001")
    path = f"/agent/handoffs/{key}"
    claimed = client.post(path + "/claim", headers=headers(agent), json=body)
    assert claimed.status_code == 200 and claimed.json()["status"] == "claimed"
    assert claimed.json()["claimed_by"].startswith("agent_")
    assert client.get(path, headers=headers(agent)).json() == claimed.json()
    assert client.post(path + "/claim", headers=headers(agent), json=body).json() == claimed.json()
    assert (
        client.post(
            path + "/claim", headers=headers(agent), json=body | dict(expected_version=2)
        ).status_code
        == 409
    )
    # Verified source updates preserve the claim and idempotent replay reads current facts.
    source = app.state.sessions[customer]
    with app.state.store.transaction(staff_queue.scope(source)):
        packet = dict(app.state.handoffs[key])
    packet["freeze_outcome"] = "verified"
    packet["actions_taken"] = [*packet["actions_taken"], "freeze_card"]
    staff_queue.publish(app, source, packet)
    refreshed = client.get(path, headers=headers(agent)).json()
    assert refreshed["status"] == "claimed" and refreshed["version"] == 3
    assert refreshed["claimed_by"] == claimed.json()["claimed_by"]
    assert refreshed["freeze_outcome"] == "verified"
    assert client.post(path + "/claim", headers=headers(agent), json=body).json() == refreshed
    staff_queue.publish(app, source, packet)
    assert client.get(path, headers=headers(agent)).json()["version"] == 3
    # A second customer profile in the same visit publishes to the same realm.
    pt = select(client, customer, "pt")
    second = handoff(client, pt)
    assert {
        p["handoff_id"] for p in client.get("/agent/handoffs", headers=headers(agent)).json()
    } == {key, second}
    assert client.get("/transactions", headers=headers(agent)).status_code == 200
    assert client.get(f"/handoffs/{key}", headers=headers(agent)).status_code == 404


def test_other_visit_customer_role_invitation_replay_and_logout_denied(monkeypatch):
    app, settings, client = application(monkeypatch)
    first = select(client, authenticate(client, settings), "mx-es")
    key = handoff(client, first)
    agent = staff(client, settings)
    grant = invitation(client, first)
    assert join(client, agent, grant).status_code == 200
    second = select(client, authenticate(client, settings), "pt")
    other = staff(client, settings, "authored.pt")
    assert join(client, other, grant).status_code == 403  # One-use, staff-session bound.
    assert join(client, other, invitation(client, second)).status_code == 200
    assert client.get("/agent/handoffs", headers=headers(other)).json() == []
    assert client.get(f"/agent/handoffs/{key}", headers=headers(other)).status_code == 404
    assert (
        client.post(
            f"/agent/handoffs/{key}/claim",
            headers=headers(other),
            json=dict(expected_version=1, idempotency_key="other_claim_001"),
        ).status_code
        == 404
    )
    app.state.sessions[other] = replace(app.state.sessions[other], role="customer")
    assert client.get("/agent/handoffs", headers=headers(other)).status_code == 403
    assert join(client, other, invitation(client, second)).status_code == 403
    assert client.post("/auth/logout", headers=headers(first)).json()["verified"]
    assert client.get("/agent/handoffs", headers=headers(agent)).status_code == 403


def test_expired_and_forged_invites_never_attach_staff(monkeypatch):
    app, settings, client = application(monkeypatch)
    customer = select(client, authenticate(client, settings), "mx-es")
    token = invitation(client, customer)
    agent = staff(client, settings)
    assert join(client, agent, token[:-1] + ("A" if token[-1] != "A" else "B")).status_code == 403
    import hashlib

    reference = app.state.sessions[customer].judge_reference
    with app.state.store.transaction(app.state.judge_sessions.controller_scope(reference)):
        key = "realm-invite:" + hashlib.sha256(token.encode()).hexdigest()
        grant = app.state.idempotency[key]
        grant["expires_at"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
        app.state.idempotency[key] = grant
    assert join(client, agent, token).status_code == 403
    principal = app.state.sessions[agent]
    with app.state.store.transaction(
        Scope(principal.customer_id, principal.run_id, principal.session_id)
    ):
        assert app.state.idempotency.get("staff-realm") is None


def test_digit_only_masked_case_reference_survives_structural_redaction():
    packet = dict(handoff_id="HO-12345678", customer_statements=[dict(quote="CPF 123.456.789-01")])
    redacted = staff_queue.masked(packet)
    assert redacted["handoff_id"] == packet["handoff_id"]
    assert "123.456.789-01" not in redacted["customer_statements"][0]["quote"]
