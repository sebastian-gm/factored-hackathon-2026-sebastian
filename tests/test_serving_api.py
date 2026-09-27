"""Serving-bound API acceptance on authored gold, with real non-owner Postgres."""

from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql

from aclara.agent.contracts import DisputeCaseView
from aclara.api.app import create_app
from aclara.bank.serving import ServingRepository
from aclara.data.serving_load import CUSTOMER_SCOPED, load_serving
from aclara.data.snapshot import build_snapshot
from aclara.ops.store import Scope, Store
from aclara.settings import Settings


def test_serving_personas_rls_three_surfaces_and_restart(tmp_path: Path) -> None:
    owner, runtime = os.getenv("TEST_DATA_LOAD_DSN"), os.getenv("TEST_OPS_DSN")
    if not owner or not runtime:
        pytest.skip("Disposable Postgres credentials required")
    pytest.importorskip("dbt.cli.main")
    lake = tmp_path / "lake"
    build_snapshot(Path("tests/fixtures/incremental/day1"), lake, reports=False)
    result = load_serving(lake, owner)
    with psycopg.connect(owner) as pg:
        pg.execute("GRANT USAGE ON SCHEMA meta,reference TO aclara_api")
        pg.execute("GRANT SELECT ON meta.serving_state TO aclara_api")
        pg.execute(
            "CREATE TABLE reference.demo_personas (username text, customer_id text, locale text, role text, dataset_version text)"
        )
        pg.execute("GRANT SELECT ON reference.demo_personas TO aclara_api")
        for username, cid, locale, role in (
            ("serving.es", "fixture-customer-a", "es-MX", "ops"),
            ("serving.pt", "fixture-customer-b", "pt-BR", "customer"),
        ):
            pg.execute(
                "INSERT INTO reference.demo_personas VALUES (%s,%s,%s,%s,%s)",
                (username, cid, locale, role, result["dataset_version"]),
            )
        # Exercise the exact half-open UTC boundary and ownership join.
        pg.execute(
            "UPDATE bank.transactions SET transaction_status='Approved', transaction_type='Purchase', amount=20,amount_usd_recomputed=20,fraud_score=0,fx_nearest_prior=false,process_date=DATE '2026-06-15',merchant_name='Taller Horizonte'"
        )
        pg.execute(
            "UPDATE bank.transactions SET transaction_date=TIMESTAMPTZ '2026-06-18 06:00:00Z' WHERE transaction_id=(SELECT max(transaction_id) FROM bank.transactions)"
        )
        pg.execute(
            "UPDATE bank.transactions SET transaction_date=TIMESTAMPTZ '2026-02-18 05:59:59Z' WHERE transaction_id=(SELECT min(transaction_id) FROM bank.transactions)"
        )
        pg.execute(
            "UPDATE bank.transactions SET transaction_date=TIMESTAMPTZ '2026-06-15 12:00:00Z' WHERE transaction_date NOT IN (TIMESTAMPTZ '2026-06-18 06:00:00Z',TIMESTAMPTZ '2026-02-18 05:59:59Z')"
        )
    clock = datetime(2026, 6, 18, 6, tzinfo=UTC)
    store = Store(runtime)
    settings = Settings(
        demo_password=secrets.token_urlsafe(32), ledger_backend="serving", bank_clock=clock
    )
    app = create_app(settings, store=store)
    client = TestClient(app)

    def login(username: str) -> dict[str, str]:
        c = client.post(
            "/auth/login", json={"username": username, "password": settings.demo_password}
        ).json()
        pre = {"X-Preauth-Token": c["preauth_token"]}
        code = client.get(f"/auth/challenges/{c['challenge_id']}/sms", headers=pre).json()["code"]
        response = client.post(
            "/auth/otp/verify", headers=pre, json={"challenge_id": c["challenge_id"], "code": code}
        )
        assert response.status_code == 200
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    try:
        assert "fixture-customer" not in client.get("/personas").text
        first, other = login("serving.es"), login("serving.pt")
        assert client.get("/me", headers=other).json()["locale"] == "pt-BR"
        assert client.get("/me", headers=first).json()["role"] == "ops"
        rows = client.get("/transactions", headers=first)
        assert rows.status_code == 200 and len(rows.json()) == 1
        assert all(
            x not in rows.text for x in ("customer_id", "product_id", "fraud_score", "_source")
        )
        assert client.get("/transactions", headers=other).json() == []
        assert client.get("/ops/snapshot", headers=other).status_code == 403
        assert client.get("/agent/handoffs", headers=other).status_code == 403
        token = first["Authorization"].removeprefix("Bearer ")
        forged = other["Authorization"].split(".")[0] + "." + token.split(".", 1)[1]
        assert client.get("/transactions", headers={"Authorization": forged}).status_code == 401
        cid = client.post("/chat/sessions", headers=first).json()["conversation_id"]
        endpoint = f"/chat/sessions/{cid}"
        proposal = client.post(
            endpoint + "/messages",
            headers=first,
            json={"message": "No reconozco el cargo de Taller Horizonte por 20 USD"},
        ).json()
        assert proposal["outcome"] == "dispute_proposed"
        case = client.post(
            endpoint + "/confirm",
            headers=first,
            json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True},
        ).json()
        assert case["outcome"] == "dispute_filed" and case["verified"]
        case_path = "/disputes/" + case["case"]["case_id"]
        assert client.get(case_path, headers=first).status_code == 200
        assert client.get(case_path, headers=other).status_code == 404
        handoff = client.post(
            endpoint + "/messages", headers=first, json={"message": "Quiero hablar con una persona"}
        ).json()
        assert handoff["verified"]
        packet_path = "/agent/handoffs/" + handoff["handoff"]["handoff_id"]
        claim = client.post(
            packet_path + "/claim",
            headers=first,
            json={"expected_version": 1, "idempotency_key": "serving-claim"},
        ).json()
        assert claim["status"] == "claimed"
        assert client.get(packet_path, headers=first).json() == claim
        snapshot = client.get("/ops/snapshot", headers=first).json()
        assert snapshot["source_kind"] == "organizer_serving"
        assert snapshot["dataset_version"] == result["dataset_version"]
        assert snapshot["metrics"]["cases"] == snapshot["metrics"]["handoffs"] == 1
        with (
            store.transaction(Scope("fixture-customer-a", "probe", "probe")),
            pytest.raises(PermissionError),
        ):
            app.state.ledger.for_customer("fixture-customer-b", clock)
        with psycopg.connect(runtime) as pg:
            for table in CUSTOMER_SCOPED:
                assert pg.execute(
                    sql.SQL("SELECT count(*) FROM bank.{}").format(sql.Identifier(table))
                ).fetchone() == (0,)
        import asyncio

        from evals.bindings import bind
        from evals.bound_execution import execute_bound
        from tests.test_bound_evaluation import authored

        scenario = authored()
        bound = bind(
            scenario,
            {
                "customer_id": "fixture-customer-a",
                "product_id": "fixture-product-a",
                "selector": {"country": "MX", "segment": "Basic"},
            },
            serving=app.state.ledger,
        )
        merged = bound.ledger.for_customer("fixture-customer-a", clock)
        assert len(merged) == 2 and bound.refs.get("target") == "txn_1"
        assert merged[1][1].merchant_name == "Taller Horizonte"
        observed = asyncio.run(execute_bound(scenario, bound, "B1"))
        assert observed["passed"]
        with pytest.raises(PermissionError):
            bound.ledger.for_customer("fixture-customer-b", clock)
        store.close()
        store = Store(runtime)
        with TestClient(create_app(settings, store=store)) as restored:
            assert DisputeCaseView.model_validate(
                restored.get(case_path, headers=first).json()
            ) == DisputeCaseView.model_validate(case["case"])
            assert restored.get(packet_path, headers=first).json() == claim
            assert restored.post("/auth/logout", headers=first).json()["verified"]
            assert restored.get("/transactions", headers=first).status_code == 401
        with pytest.raises(ValueError):
            ServingRepository(store, datetime(2026, 6, 19, 6, tzinfo=UTC))
        pinned = ServingRepository(store, clock)
        with psycopg.connect(owner) as pg:
            pg.execute(
                "UPDATE meta.serving_state SET identity=jsonb_set(identity,'{build_fingerprint}','\"changed-dev-build\"')"
            )
        with pytest.raises(ValueError):
            pinned.for_customer("fixture-customer-a", clock)
    finally:
        client.close()
        store.close()
