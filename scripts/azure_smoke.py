"""Authenticated HTTPS smoke of deployed mock main; report aggregates only."""

from __future__ import annotations

import json
import sys
import time

import httpx
import psycopg
import yaml
from scripts.azure_dev import ROOT, VAULT, az, run, terraform_environment
from scripts.azure_migrate_ops import connection_string
from scripts.verify_audit_chain import verify

from aclara.evals.schema import ScenarioSuite


def main() -> None:
    outputs = json.loads(
        run(["terraform", "-chdir=infra", "output", "-json"], env=terraform_environment())
    )
    api = outputs["api_url"]["value"]
    web = outputs["web_url"]["value"]
    password = az("keyvault", "secret", "show", "--vault-name", VAULT, "--name", "demo-password")[
        "value"
    ]
    evidence = smoke(api, web, password)
    audit_entries = 0
    with psycopg.connect(connection_string("aclara_app")) as connection:
        for run_id, sid in evidence["scopes"]:
            with connection.transaction():
                for key, value in (
                    ("app.customer_id", "demo-customer-01"),
                    ("app.run_id", run_id),
                    ("app.sid", sid),
                ):
                    connection.execute("SELECT set_config(%s,%s,true)", (key, value))
                rows = connection.execute(
                    "SELECT sequence,canonical,prev_hash,row_hash FROM ops.audit_log ORDER BY sequence"
                ).fetchall()
                audit_entries += verify(rows, ("demo-customer-01", run_id, sid))
    with httpx.Client(base_url=api, timeout=30) as client:
        previous_instance = client.get("/healthz").json()["instance_id"]
    sys.stdout.write(
        f"Azure audit chains verified: {audit_entries} entries; requesting API restart.\n"
    )
    sys.stdout.flush()
    app = az(
        "containerapp",
        "show",
        "--name",
        "ca-api-aclara-dev-eastus2",
        "--resource-group",
        "rg-aclara-dev-eastus2",
    )
    az(
        "containerapp",
        "revision",
        "restart",
        "--revision",
        app["properties"]["latestReadyRevisionName"],
        "--resource-group",
        "rg-aclara-dev-eastus2",
        "--name",
        "ca-api-aclara-dev-eastus2",
    )
    deadline = time.monotonic() + 240
    observations = {"old_instance": 0, "not_ready": 0, "transport_error": 0, "case_status": 0}
    with httpx.Client(base_url=api, timeout=10) as client:
        while time.monotonic() < deadline:
            try:
                response = client.get("/readyz")
                health = client.get("/healthz")
                if (
                    response.status_code == 200
                    and health.status_code == 200
                    and health.json()["instance_id"] != previous_instance
                ):
                    restored = client.get(evidence["case_path"], headers=evidence["case_headers"])
                    observations["case_status"] = restored.status_code
                    if restored.status_code == 200 and restored.json()["status"] == "received":
                        break
                elif response.status_code != 200 or health.status_code != 200:
                    observations["not_ready"] += 1
                else:
                    observations["old_instance"] += 1
            except httpx.HTTPError:
                observations["transport_error"] += 1
            time.sleep(2)
        else:
            raise RuntimeError(f"Post-restart readback did not recover: {observations}")
    sys.stdout.write(
        f"Azure audit chains verified: {audit_entries} entries; existing authenticated case survived revision restart.\n"
    )


def smoke(api: str, web: str, password: str, username: str = "demo.es.mx") -> dict:
    suite = ScenarioSuite.model_validate(
        yaml.safe_load((ROOT / "evals/dev_scenarios.yaml").read_text())
    )
    readbacks = 0
    evidence: dict = {"scopes": []}
    with httpx.Client(base_url=api, timeout=120) as client:
        health = client.get("/healthz")
        health.raise_for_status()
        assert health.json()["llm_provider"] == "mock"
        assert client.get("/readyz").json()["database"] == "ok"
        assert client.get("/transactions").status_code == 401
        assert (
            client.post(
                "/auth/login", json={"username": "invalid", "password": "invalid"}
            ).status_code
            == 401
        )
        cors = client.options(
            "/auth/login",
            headers={
                "Origin": web,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert cors.headers.get("access-control-allow-origin") == web
        html = client.get(web)
        html.raise_for_status()
        assert "Aclara" in html.text and api in html.text
        for scenario in suite.scenarios:
            challenge = client.post(
                "/auth/login", json={"username": username, "password": password}
            ).json()
            preauth = {"X-Preauth-Token": challenge["preauth_token"]}
            sms = client.get(
                f"/auth/challenges/{challenge['challenge_id']}/sms", headers=preauth
            ).json()
            session = client.post(
                "/auth/otp/verify",
                headers=preauth,
                json={"challenge_id": challenge["challenge_id"], "code": sms["code"]},
            ).json()
            headers = {"Authorization": f"Bearer {session['access_token']}"}
            parts = session["access_token"].split(".", 2)
            if len(parts) == 3:
                evidence["scopes"].append(parts[:2])
            transactions = client.get("/transactions", headers=headers).json()
            assert len(transactions) == 6
            assert all("customer_id" not in row and "product_id" not in row for row in transactions)
            conversation = client.post("/chat/sessions", headers=headers).json()["conversation_id"]
            result: dict = {}
            for turn in scenario.model_dump()["turns"]:
                if "confirm" in turn:
                    response = client.post(
                        f"/chat/sessions/{conversation}/confirm",
                        headers=headers,
                        json={
                            "proposal_hash": result["proposal"]["proposal_hash"],
                            "confirmed": turn["confirm"],
                        },
                    )
                else:
                    response = client.post(
                        f"/chat/sessions/{conversation}/messages",
                        headers=headers,
                        json={"message": turn["message"]},
                    )
                response.raise_for_status()
                result = response.json()
            assert result["outcome"] == scenario.expected, f"Scenario failed: {scenario.id}"
            if result["outcome"] == "dispute_filed":
                readback = client.get(f"/disputes/{result['case']['case_id']}", headers=headers)
                assert readback.status_code == 200 and readback.json()["status"] == "received"
                assert result["verified"] is True
                evidence["case_path"] = f"/disputes/{result['case']['case_id']}"
                evidence["case_headers"] = headers
                readbacks += 1
            if result["outcome"] == "handoff_created":
                readback = client.get(
                    f"/handoffs/{result['handoff']['handoff_id']}", headers=headers
                )
                assert readback.status_code == 200
                readbacks += 1
    sys.stdout.write(
        f"HTTP smoke passed: {len(suite.scenarios)}/{len(suite.scenarios)} ES/PT scenarios; {readbacks} readbacks; login/OTP, scope, auth denial, CORS, web, mock, database readiness.\n"
    )
    sys.stdout.flush()

    return evidence


if __name__ == "__main__":
    main()
