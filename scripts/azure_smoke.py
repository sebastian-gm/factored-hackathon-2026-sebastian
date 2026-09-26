"""Authenticated HTTPS smoke of deployed mock main; report aggregates only."""

from __future__ import annotations

import json
import sys

import httpx
import yaml
from scripts.azure_dev import ROOT, VAULT, az, run

from aclara.evals.schema import ScenarioSuite


def main() -> None:
    outputs = json.loads(run(["terraform", "-chdir=infra", "output", "-json"]))
    api = outputs["api_url"]["value"]
    web = outputs["web_url"]["value"]
    password = az("keyvault", "secret", "show", "--vault-name", VAULT, "--name", "demo-password")[
        "value"
    ]
    suite = ScenarioSuite.model_validate(
        yaml.safe_load((ROOT / "evals/dev_scenarios.yaml").read_text())
    )
    readbacks = 0
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
                "/auth/login", json={"username": "demo.es.mx", "password": password}
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
                readbacks += 1
            if result["outcome"] == "handoff_created":
                readback = client.get(
                    f"/handoffs/{result['handoff']['handoff_id']}", headers=headers
                )
                assert readback.status_code == 200
                readbacks += 1
    sys.stdout.write(
        f"Azure HTTPS smoke passed: {len(suite.scenarios)}/{len(suite.scenarios)} ES/PT scenarios; {readbacks} readbacks; login/OTP, scope, auth denial, CORS, web, mock, database readiness.\n"
    )


if __name__ == "__main__":
    main()
