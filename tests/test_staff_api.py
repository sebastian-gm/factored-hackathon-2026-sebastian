from __future__ import annotations

import asyncio
import secrets
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from evals.runner import _new_authenticated_client

from aclara.settings import Settings


async def otp(client, headers):
    c = (await client.post("/auth/step-up", headers=headers)).json()
    preauth = {"X-Preauth-Token": c["preauth_token"]}
    sms = (await client.get(f"/auth/challenges/{c['challenge_id']}/sms", headers=preauth)).json()
    response = await client.post(
        "/auth/step-up/verify",
        headers={**headers, **preauth},
        json={"challenge_id": c["challenge_id"], "code": sms["code"]},
    )
    assert response.status_code == 200


def test_customer_cannot_infer_roles_or_read_staff_data_and_logout_revokes() -> None:
    async def check():
        app, client, token, cid = await _new_authenticated_client(
            Settings(demo_username="ops.admin", demo_password=secrets.token_urlsafe(24))
        )
        headers = {"Authorization": f"Bearer {token}"}
        try:
            assert (await client.get("/me", headers=headers)).json()["role"] == "customer"
            for endpoint in [
                "/agent/handoffs",
                "/ops/snapshot",
                "/ops/metrics",
                f"/chat/sessions/{cid}/trace",
            ]:
                assert (await client.get(endpoint, headers=headers)).status_code == 403
            assert (await client.post("/ops/reset/proposal", headers=headers)).status_code == 403
            assert (await client.post("/auth/logout", headers=headers)).json()["verified"]
            assert (await client.get("/me", headers=headers)).status_code == 401
            assert token not in app.state.sessions
        finally:
            await client.aclose()

    asyncio.run(check())


def test_staff_claim_resolve_trace_and_current_workspace_isolation() -> None:
    async def check():
        app, client, token, cid = await _new_authenticated_client(
            Settings(
                demo_username="staff-fixture",
                demo_password=secrets.token_urlsafe(24),
                demo_role="agent",
            )
        )
        headers = {"Authorization": f"Bearer {token}"}
        try:
            result = await client.post(
                f"/chat/sessions/{cid}/messages",
                headers=headers,
                json={"message": "Quiero hablar con una persona"},
            )
            assert result.status_code == 200 and result.json()["verified"]
            handoff = result.json()["handoff"]
            queue = (await client.get("/agent/handoffs", headers=headers)).json()
            assert len(queue) == 1 and queue[0]["handoff_id"] == handoff["handoff_id"]
            assert queue[0]["conversation_id"] == cid and queue[0]["scope"] == "current_workspace"
            assert queue[0]["customer"]["auth"]["amr"] == ["pwd", "otp"]
            endpoint = f"/agent/handoffs/{handoff['handoff_id']}"
            body = {"expected_version": 1, "idempotency_key": "claim_fixture_01"}
            claim = await client.post(endpoint + "/claim", headers=headers, json=body)
            assert claim.status_code == 200 and claim.json()["status"] == "claimed"
            assert (
                await client.post(endpoint + "/claim", headers=headers, json=body)
            ).json() == claim.json()
            assert (await client.get(endpoint, headers=headers)).json() == claim.json()
            conflict = {**body, "idempotency_key": "claim_fixture_other"}
            assert (
                await client.post(endpoint + "/claim", headers=headers, json=conflict)
            ).status_code == 409
            resolved = await client.post(
                endpoint + "/resolve",
                headers=headers,
                json={
                    "expected_version": 2,
                    "idempotency_key": "resolve_fixture_01",
                    "resolution": "review_completed",
                },
            )
            assert resolved.status_code == 200 and resolved.json()["status"] == "resolved"
            assert (await client.get(endpoint, headers=headers)).json() == resolved.json()
            trace = await client.get(f"/chat/sessions/{cid}/trace", headers=headers)
            assert trace.status_code == 200 and any(
                e["stage"] == "Verify" for e in trace.json()["events"]
            )
            assert (
                "customer_id" not in trace.text
                and "customer_text" not in trace.text
                and "inputs_snapshot" not in trace.text
            )
            assert (await client.get("/ops/snapshot", headers=headers)).status_code == 403
            principal = app.state.sessions[token]
            other = f"{principal.run_id}.other-sid.{secrets.token_urlsafe(32)}"
            app.state.sessions[other] = replace(principal, session_id="other-sid")
            other_headers = {"Authorization": f"Bearer {other}"}
            assert (await client.get("/agent/handoffs", headers=other_headers)).json() == []
            assert (await client.get(endpoint, headers=other_headers)).status_code == 404
            assert (
                await client.get(f"/chat/sessions/{cid}/trace", headers=other_headers)
            ).status_code == 404
        finally:
            await client.aclose()

    asyncio.run(check())


def test_ops_reset_requires_fresh_bound_confirmation_and_preserves_auth() -> None:
    async def check():
        app, client, token, cid = await _new_authenticated_client(
            Settings(
                demo_username="ops-fixture",
                demo_password=secrets.token_urlsafe(24),
                demo_role="ops",
                allow_demo_reset=True,
            )
        )
        headers = {"Authorization": f"Bearer {token}"}
        try:
            await client.post(
                f"/chat/sessions/{cid}/messages",
                headers=headers,
                json={"message": "Quiero un agente"},
            )
            snapshot = (await client.get("/ops/snapshot", headers=headers)).json()
            assert snapshot["metrics"]["handoffs"] == 1 and snapshot["metrics"]["sar"] is None
            assert (await client.post("/ops/reset/proposal", headers=headers)).status_code == 401
            await otp(client, headers)
            proposal = (await client.post("/ops/reset/proposal", headers=headers)).json()
            assert (
                await client.post(
                    "/ops/reset",
                    headers=headers,
                    json={"proposal_hash": "0" * 64, "confirmed": True},
                )
            ).status_code == 409
            principal = app.state.sessions[token]
            app.state.sessions[token] = replace(
                principal, step_up_at=datetime.now(UTC) - timedelta(minutes=11)
            )
            assert (
                await client.post(
                    "/ops/reset",
                    headers=headers,
                    json={"proposal_hash": proposal["proposal_hash"], "confirmed": True},
                )
            ).status_code == 401
            app.state.sessions[token] = principal
            body = {"proposal_hash": proposal["proposal_hash"], "confirmed": True}
            result = await client.post("/ops/reset", headers=headers, json=body)
            assert result.status_code == 200 and result.json()["remaining_operations"] == 0
            assert result.json()["verified"] and result.json()["audit_retained"]
            assert (
                await client.get("/ops/reset/" + result.json()["receipt_id"], headers=headers)
            ).json() == result.json()
            assert (
                await client.post("/ops/reset", headers=headers, json=body)
            ).json() == result.json()
            assert (await client.get("/me", headers=headers)).status_code == 200
            assert (await client.get("/ops/metrics", headers=headers)).json()["handoffs"] == 0
        finally:
            await client.aclose()

    asyncio.run(check())
