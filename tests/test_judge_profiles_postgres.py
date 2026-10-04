"""Judge profile isolation using authored gold and disposable non-owner Postgres."""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import psycopg
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.types.json import Jsonb
from scripts.verify_audit_chain import verify
from test_judge_profiles import authenticate, authored_settings, headers, select

from aclara.api.app import create_app
from aclara.api.judge_access import PROFILE_LOCALES
from aclara.bank.serving import temporal_column_available
from aclara.data.serving_load import CUSTOMER_SCOPED, load_serving
from aclara.data.snapshot import build_snapshot
from aclara.llm.types import BudgetFailure
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import Scope, Store


@pytest.fixture
def judge_database(tmp_path: Path, monkeypatch):
    owner, runtime = os.getenv("TEST_DATA_LOAD_DSN"), os.getenv("TEST_OPS_DSN")
    if not owner or not runtime:
        pytest.skip("Disposable local Postgres required")
    pytest.importorskip("dbt.cli.main")
    monkeypatch.delenv("LLM_BUDGET_RUN_ID", raising=False)
    lake = tmp_path / "lake"
    build_snapshot(Path("tests/fixtures/incremental/day1"), lake, reports=False)
    result = load_serving(lake, owner)
    # Copy only project-authored fixture templates. Never load organizer data here.
    with psycopg.connect(owner) as pg:
        had_temporal_column = temporal_column_available(pg)
        # Authored profile templates intentionally represent passed checks;
        # never treat a real older serving load this way.
        pg.execute(
            "ALTER TABLE bank.transactions ADD COLUMN IF NOT EXISTS temporal_quality_reason TEXT"
        )
        pg.execute("GRANT USAGE ON SCHEMA meta,reference TO aclara_api")
        pg.execute("GRANT SELECT ON meta.serving_state TO aclara_api")
        pg.execute(
            "CREATE TABLE IF NOT EXISTS reference.demo_personas "
            "(username text, customer_id text, locale text, role text, dataset_version text)"
        )
        pg.execute("GRANT SELECT ON reference.demo_personas TO aclara_api")
        pg.execute("DELETE FROM reference.demo_personas WHERE username LIKE 'authored.%'")
        for key, locale in PROFILE_LOCALES.items():
            customer, product = "judge-customer-" + key, "judge-product-" + key
            overrides = {
                "customers": {"customer_id": customer, "customer_status": "Active"},
                "products": {
                    "customer_id": customer,
                    "product_id": product,
                    "product_type": "Debit_Card",
                    "product_status": "Active",
                },
                "transactions": {
                    "temporal_quality_reason": None,
                    "transaction_id": "judge-transaction-" + key,
                    "customer_id": customer,
                    "product_id": product,
                    "transaction_type": "Purchase",
                    "transaction_status": "Approved",
                    "merchant_name": "Fixture " + key,
                    "currency": "USD",
                    "amount": 20,
                    "amount_usd_recomputed": 20,
                    "fraud_score": 0,
                    "fx_nearest_prior": False,
                    "transaction_date": "2026-06-15T12:00:00Z",
                    "process_date": "2026-06-15",
                },
            }
            for table, changes in overrides.items():
                pg.execute(
                    sql.SQL(
                        "INSERT INTO bank.{table} SELECT "
                        "(jsonb_populate_record(NULL::bank.{table},to_jsonb(t)||%s)).* "
                        "FROM bank.{table} t LIMIT 1"
                    ).format(table=sql.Identifier(table)),
                    (Jsonb(changes),),
                )
            pg.execute(
                "INSERT INTO reference.demo_personas VALUES(%s,%s,%s,'ops',%s)",
                ("authored." + key, customer, locale, result["dataset_version"]),
            )
    settings = replace(authored_settings(), ledger_backend="serving")
    stores = [Store(runtime), Store(runtime)]
    try:
        yield owner, runtime, settings, stores
    finally:
        for store in stores:
            store.close()
        if not had_temporal_column:
            with psycopg.connect(owner) as pg:
                pg.execute("ALTER TABLE bank.transactions DROP COLUMN temporal_quality_reason")


def test_judge_rls_restart_audit_and_global_budget(judge_database):
    owner, runtime, settings, stores = judge_database
    app = create_app(settings, store=stores[0])
    client = TestClient(app)
    root = authenticate(client, settings)
    controller = app.state.sessions[root]
    mx = select(client, root, "mx-es")
    cid = client.post("/chat/sessions", headers=headers(mx)).json()["conversation_id"]
    proposed = client.post(
        f"/chat/sessions/{cid}/messages",
        headers=headers(mx),
        json={"message": "No hice el cargo de Fixture mx-es por 20 USD"},
    ).json()
    assert proposed["outcome"] == "dispute_proposed"
    case = client.post(
        f"/chat/sessions/{cid}/confirm",
        headers=headers(mx),
        json={"proposal_hash": proposed["proposal"]["proposal_hash"], "confirmed": True},
    ).json()
    assert case["verified"]
    path = "/disputes/" + case["case"]["case_id"]
    app2 = create_app(settings, store=stores[1])
    restored = TestClient(app2)
    assert restored.get(path, headers=headers(mx)).status_code == 200
    assert restored.get("/me", headers=headers(root)).status_code == 401
    # Authenticated profile switching never changes the global model scope/run.
    # Use a private fixture purse to avoid modifying any other test's reservations.
    budget_scope = "fixture-judge-budget-" + uuid4().hex
    with psycopg.connect(owner) as pg:
        pg.execute("SET LOCAL ROLE aclara_owner")
        pg.execute("INSERT INTO llm.limits VALUES(%s,3.00,false)", (budget_scope,))
    gate = PostgresSpendGate(stores[0], scope=budget_scope)
    reservation = gate.reserve(2.90)  # No provider call; conservative fixture exposure.
    current = mx
    capabilities = [root, mx]
    for key in ["co-es", "ar-es", "pt", "mx-es"]:
        previous = current
        current = select(restored, current, key)
        capabilities.append(current)
        assert client.get("/me", headers=headers(previous)).status_code == 401
        transactions = restored.get("/transactions", headers=headers(current))
        assert [r["merchant"] for r in transactions.json()] == ["Fixture " + key]
        # Bank state survives returning to the same judge profile; other
        # profiles and every old capability remain isolated/revoked.
        assert restored.get(path, headers=headers(current)).status_code == (
            200 if key == "mx-es" else 404
        )
        # Selecting a profile alone does not grant masked staff queue access.
        assert restored.get("/agent/handoffs", headers=headers(current)).status_code == 403
        with pytest.raises(BudgetFailure):
            PostgresSpendGate(stores[1], scope=budget_scope).reserve(0.20)
        principal = app2.state.sessions[current]
        with stores[1].transaction(
            Scope(principal.customer_id, principal.run_id, principal.session_id)
        ):
            pg = stores[1]._unit().connection
            assert pg.execute("SELECT DISTINCT customer_id FROM bank.transactions").fetchall() == [
                (principal.customer_id,)
            ]
            assert pg.execute("SELECT count(*) FROM ops.cases").fetchone() == (0,)
    gate.settle(reservation, 0)  # Fixture reservation only; actual spend stays zero.
    assert restored.post("/auth/logout", headers=headers(current)).json()["verified"]
    assert all(client.get("/me", headers=headers(t)).status_code == 401 for t in capabilities)
    with psycopg.connect(runtime) as pg:
        for table in CUSTOMER_SCOPED:
            assert pg.execute(
                sql.SQL("SELECT count(*) FROM bank.{}").format(sql.Identifier(table))
            ).fetchone() == (0,)
        scope = (controller.customer_id, controller.run_id, controller.session_id)
        for key, value in zip(("app.customer_id", "app.run_id", "app.sid"), scope, strict=True):
            pg.execute("SELECT set_config(%s,%s,true)", (key, value))
        rows = pg.execute(
            "SELECT sequence,canonical,prev_hash,row_hash FROM ops.audit_log ORDER BY sequence"
        ).fetchall()
    assert verify(rows, scope) == 12  # login + five switches with readback + logout
    actions = [json.loads(row[1])["event"]["action"] for row in rows]
    assert actions.count("judge_profile_selected") == actions.count("judge_profile_verified") == 5
    encoded = json.dumps(rows)
    assert all(t not in encoded for t in capabilities)
    assert settings.judge_password not in encoded and settings.demo_password not in encoded
    assert "Fixture" not in encoded  # No bank row facts in controller audit.


def test_cross_replica_activation_has_one_winner(judge_database, monkeypatch):
    _, _, settings, stores = judge_database
    apps = [create_app(settings, store=store) for store in stores]
    client = TestClient(apps[0])
    root = authenticate(client, settings)
    principal = replace(
        apps[0].state.sessions[root], capability_digest=hashlib.sha256(root.encode()).hexdigest()
    )
    barrier = Barrier(2)
    managers = [app.state.judge_sessions for app in apps]
    for manager in managers:
        validate = manager.validate

        def synchronized(p, original=validate):
            result = original(p)
            if p.judge_profile is None:
                barrier.wait(timeout=15)
            return result

        monkeypatch.setattr(manager, "validate", synchronized)

    def switch(pair):
        manager, profile = pair
        try:
            return manager.select(principal, profile)[0]
        except HTTPException as error:
            assert error.status_code == 401
            return None

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(switch, zip(managers, ["co-es", "pt"], strict=True)))
    winners = [r for r in results if r]
    assert len(winners) == 1
    assert client.get("/transactions", headers=headers(winners[0])).status_code == 200
    assert client.get("/me", headers=headers(root)).status_code == 401
