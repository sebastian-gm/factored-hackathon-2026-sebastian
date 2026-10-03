"""Authored replay: delegated authority cannot outlive current judge validity."""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import replace

import pytest
from test_judge_profiles import AuthoredLedger, application, authenticate, headers, select
from test_staff_realm_queue import handoff, invitation, join, staff

from aclara.api import staff_queue
from aclara.handoff import queue
from aclara.ops.store import Store


@pytest.fixture
def persisted_store():
    # Same API replay runs in memory locally and against disposable PG in its gate.
    dsn = os.getenv("TEST_OPS_DSN")
    store = Store(dsn) if dsn else None
    try:
        yield store
    finally:
        if store is not None:
            store.close()


def restarted(monkeypatch, app, settings, change):
    ledger = AuthoredLedger()
    if change == "off":
        settings = replace(settings, judge_access_enabled=False)
    elif change == "password":
        settings = replace(settings, judge_password=secrets.token_urlsafe(32))
    elif change == "configuration":
        definition = json.loads(settings.judge_persona)
        definition["username"] = "judge.rotated"
        settings = replace(settings, judge_persona=json.dumps(definition))
    elif change == "dataset":
        ledger.dataset_version += ":rotated"
    return application(monkeypatch, store=app.state.store, settings=settings, ledger=ledger)


def snapshot(app, agent, realm, key):
    with (
        app.state.store.transaction(staff_queue.scope(app.state.sessions[agent])),
        queue.context(app.state.store, realm, staff=True),
    ):
        return dict(queue.read(app.state.store, realm, key)[0])


@pytest.mark.parametrize("change", ["off", "password", "configuration", "dataset"])
@pytest.mark.parametrize("previously_claimed", [False, True])
def test_revoked_customer_cannot_leave_live_delegated_queue_or_claim_replay(
    monkeypatch, change, previously_claimed, persisted_store
):
    app, settings, client = application(monkeypatch, store=persisted_store)
    customer = select(client, authenticate(client, settings), "mx-es")
    key = handoff(client, customer)
    agent = staff(client, settings)
    assert join(client, agent, invitation(client, customer)).status_code == 200
    path = f"/agent/handoffs/{key}"
    body = dict(expected_version=1, idempotency_key="rotation_claim_001")
    if previously_claimed:
        assert client.post(path + "/claim", headers=headers(agent), json=body).status_code == 200
    realm = staff_queue.authorized_realm(app, app.state.sessions[agent])
    original = snapshot(app, agent, realm, key)
    _, _, current = restarted(monkeypatch, app, settings, change)
    assert current.get("/me", headers=headers(customer)).status_code == 401
    assert current.get("/me", headers=headers(agent)).status_code == 200  # Staff itself is live.
    listed = current.get("/agent/handoffs", headers=headers(agent))
    detail = current.get(path, headers=headers(agent))
    claimed = current.post(path + "/claim", headers=headers(agent), json=body)
    assert {listed.status_code, detail.status_code, claimed.status_code} <= {401, 403}
    assert snapshot(app, agent, realm, key) == original  # No claim/version mutation.


@pytest.mark.parametrize("change", ["off", "password", "configuration", "dataset"])
def test_stale_invitation_cannot_create_delegation_after_rotation(
    monkeypatch, change, persisted_store
):
    app, settings, client = application(monkeypatch, store=persisted_store)
    customer = select(client, authenticate(client, settings), "mx-es")
    grant = invitation(client, customer)
    agent = staff(client, settings)
    current_app, _, current = restarted(monkeypatch, app, settings, change)
    assert current.get("/me", headers=headers(customer)).status_code == 401
    assert join(current, agent, grant).status_code in {401, 403}
    with current_app.state.store.transaction(staff_queue.scope(current_app.state.sessions[agent])):
        assert current_app.state.idempotency.get("staff-realm") is None


def test_same_config_restart_and_profile_switch_keep_the_live_visit_delegation(
    monkeypatch, persisted_store
):
    app, settings, client = application(monkeypatch, store=persisted_store)
    customer = select(client, authenticate(client, settings), "mx-es")
    first = handoff(client, customer)
    agent = staff(client, settings)
    assert join(client, agent, invitation(client, customer)).status_code == 200
    _, _, current = restarted(monkeypatch, app, settings, "unchanged")
    assert current.get("/me", headers=headers(customer)).status_code == 200
    assert current.get("/agent/handoffs", headers=headers(agent)).status_code == 200
    active = select(current, customer, "pt")
    assert current.get("/me", headers=headers(customer)).status_code == 401  # Superseded child.
    assert current.get("/me", headers=headers(active)).status_code == 200
    second = handoff(current, active)
    packets = current.get("/agent/handoffs", headers=headers(agent))
    assert packets.status_code == 200
    assert {p["handoff_id"] for p in packets.json()} == {first, second}
    assert (
        current.post(
            f"/agent/handoffs/{first}/claim",
            headers=headers(agent),
            json=dict(expected_version=1, idempotency_key="valid_restart_claim_001"),
        ).status_code
        == 200
    )
