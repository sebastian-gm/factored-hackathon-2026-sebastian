"""Forced realm RLS and audited claim races in a disposable non-owner database."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest

from aclara.handoff import queue
from aclara.ops.store import Scope, Store


def test_realm_rls_immutable_payload_restart_claim_race_and_audit():
    dsn = os.getenv("TEST_OPS_DSN")
    if not dsn:
        pytest.skip("Disposable local Postgres required")
    realm, other = uuid4().hex, uuid4().hex
    customer = Scope("authored-queue-customer", realm, "customer-session")
    agents = [
        Scope("authored-staff-a", realm, "staff-a"),
        Scope("authored-staff-b", realm, "staff-b"),
    ]
    store = Store(dsn)
    payload = dict(
        handoff_id="HO-AUTHORED",
        status="waiting",
        claimed_by=None,
        version=1,
        summary="Masked synthetic request",
    )
    try:
        with store.transaction(customer), queue.context(store, realm, staff=False):
            queue.publish(store, realm, payload)
        with psycopg.connect(dsn) as pg:
            assert pg.execute("SELECT count(*) FROM ops.realm_handoffs").fetchone() == (0,)
            assert pg.execute(
                "SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='ops.realm_handoffs'::regclass"
            ).fetchone() == (True, True)
        with store.transaction(agents[0]), queue.context(store, other, staff=True):
            assert queue.read(store, other) == []
        with store.transaction(agents[0]), queue.context(store, realm, staff=False):
            assert queue.read(store, realm) == []
            with pytest.raises(PermissionError):
                queue.claim(store, realm, "HO-AUTHORED", "staff", 1)
        with store.transaction(agents[0]), queue.context(store, realm, staff=True):
            assert queue.read(store, realm) == [payload]
            pg = store._unit().connection
            with pytest.raises(psycopg.errors.InsufficientPrivilege), pg.transaction():
                pg.execute("UPDATE ops.realm_handoffs SET payload='{}'")
            with pytest.raises(psycopg.errors.InsufficientPrivilege), pg.transaction():
                pg.execute("UPDATE ops.realm_handoffs SET realm=%s", (other,))
            with pytest.raises(psycopg.errors.InsufficientPrivilege), pg.transaction():
                pg.execute("DELETE FROM ops.realm_handoffs")

        def compete(agent):
            replica = Store(dsn)
            try:
                with replica.transaction(agent), queue.context(replica, realm, staff=True):
                    try:
                        queue.claim(replica, realm, "HO-AUTHORED", agent.sid, 1)
                        return True
                    except ValueError:
                        return False
            finally:
                replica.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sum(pool.map(compete, agents)) == 1
        with store.transaction(agents[0]), queue.context(store, realm, staff=True):
            saved = queue.read(store, realm)[0]
            assert saved["version"] == 2 and saved["status"] == "claimed"
            assert saved["summary"] == payload["summary"]
        audit_count = 0
        for agent in agents:
            with store.transaction(agent):
                rows = (
                    store._unit()
                    .connection.execute("SELECT canonical FROM ops.audit_log")
                    .fetchall()
                )
                audit_count += sum('"claim_handoff_queue"' in row[0] for row in rows)
        assert audit_count == 1
        # Transaction-local realm settings do not survive pool reuse.
        with store.transaction(agents[0]):
            assert store._unit().connection.execute(
                "SELECT count(*) FROM ops.realm_handoffs"
            ).fetchone() == (0,)
    finally:
        store.close()
