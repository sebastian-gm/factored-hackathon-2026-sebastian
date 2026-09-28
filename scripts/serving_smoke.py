"""Exercise real serving data through the web BFF; print aggregate checks only."""

# ruff: noqa: T201 -- aggregate checks and exception frame locations only.

from __future__ import annotations

import json
import secrets
import time
from typing import Any

import httpx
from scripts.verify_audit_chain import verify

from aclara.agent.contracts import DisputeCaseView
from aclara.api.app import _masked_transaction
from aclara.bank.serving import ServingRepository
from aclara.ops.store import Scope
from aclara.policy.engine import evaluate


def wait_config(client: httpx.Client) -> dict[str, Any]:
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        try:
            r = client.get("config")
            if r.status_code == 200:
                return r.json()
        except httpx.HTTPError:
            pass
        time.sleep(2)
    raise RuntimeError("BFF config did not become ready")


def check(response: httpx.Response, expected: int = 200) -> Any:
    if response.status_code != expected:
        raise RuntimeError(f"Smoke HTTP status {response.status_code}; expected {expected}")
    return response.json()


def smoke(web: str, password: str, ledger: ServingRepository) -> dict[str, Any]:
    counts = {
        "personas": 0,
        "scoped_transactions": 0,
        "cases": 0,
        "handoffs": 0,
        "claims": 0,
        "resolutions": 0,
        "audit_entries": 0,
    }
    recovery = None
    for persona in ledger.personas():
        with httpx.Client(
            base_url=web.rstrip("/") + "/api/bff/", headers={"Origin": web}, timeout=30
        ) as client:
            config = wait_config(client)
            assert not config["fixtures"]
            assert len(config["personas"]) == 4
            assert client.get("transactions").status_code == 401
            challenge = check(
                client.post("auth/login", json={"username": persona.username, "password": password})
            )
            sms = check(client.get(f"auth/challenges/{challenge['challenge_id']}/sms"))
            check(
                client.post(
                    "auth/otp/verify",
                    json={"challenge_id": challenge["challenge_id"], "code": sms["code"]},
                )
            )
            identity = check(client.get("me"))
            assert identity["role"] == persona.role and identity["locale"] == persona.locale
            rows = check(client.get("transactions"))
            actual = ledger.for_customer(persona.customer_id, ledger.bank_clock)
            assert rows == [_masked_transaction(h, r) for h, r in actual]
            assert all("customer_id" not in row and "fraud_score" not in row for row in rows)
            counts["personas"] += 1
            counts["scoped_transactions"] += len(rows)
            if persona.role == "customer":
                assert client.get("agent/handoffs").status_code == 403
                assert client.get("ops/snapshot").status_code == 403
                check(client.post("auth/logout", json={}))
                assert client.get("me").status_code == 401
                continue
            eligible = [
                (h, r)
                for h, r in actual
                if evaluate(r, ledger.bank_clock, True, ledger.context(r)).decision == "eligible"
            ]
            if not eligible:
                raise RuntimeError("Demo persona lacks a policy-eligible organizer transaction")
            _, target = eligible[0]
            # Amount precedes merchant so a number in a merchant name is not a slot.
            suffix = f"{target.amount:.2f} {target.currency} en {target.merchant_name}"
            pt = persona.locale == "pt-BR"

            def conversation() -> str:
                return (
                    "chat/sessions/"
                    + check(client.post("chat/sessions", json={}))["conversation_id"]
                )

            normal = check(
                client.post(
                    conversation() + "/messages",
                    json={
                        "message": (
                            "Quero consultar uma cobrança de "
                            if pt
                            else "Quiero consultar un cargo de "
                        )
                        + suffix
                    },
                )
            )
            assert normal["outcome"] == "explained"
            path = conversation()
            offered = check(
                client.post(
                    path + "/messages",
                    json={
                        "message": (
                            "Não reconheço a cobrança de " if pt else "No reconozco el cargo de "
                        )
                        + suffix
                    },
                )
            )
            assert offered["outcome"] == "awaiting_dispute_decision"
            assert offered["response_type"] == "offer_dispute"
            assert offered["transaction"]["handle"]
            proposal = check(
                client.post(
                    path + "/messages",
                    json={
                        "message": "Não fui eu, quero contestar"
                        if pt
                        else "Yo no fui, quiero disputarlo"
                    },
                )
            )
            assert proposal["outcome"] == "dispute_proposed"
            assert proposal["transaction"]["handle"] == offered["transaction"]["handle"]
            filed = check(
                client.post(
                    path + "/confirm",
                    json={
                        "proposal_hash": proposal["proposal"]["proposal_hash"],
                        "confirmed": True,
                    },
                )
            )
            assert filed["outcome"] == "dispute_filed" and filed["verified"]
            case_path = "disputes/" + filed["case"]["case_id"]
            assert DisputeCaseView.model_validate(
                check(client.get(case_path))
            ) == DisputeCaseView.model_validate(filed["case"])
            counts["cases"] += 1
            ambiguous = conversation()
            first = check(
                client.post(
                    ambiguous + "/messages",
                    json={
                        "message": "Não reconheço uma cobrança" if pt else "No reconozco un cargo"
                    },
                )
            )
            assert first["outcome"] == "choose_transaction"
            for _ in range(2):
                handoff = check(
                    client.post(
                        ambiguous + "/messages",
                        json={
                            "message": "Não sei, não consigo escolher"
                            if pt
                            else "No sé, no puedo elegir"
                        },
                    )
                )
            assert handoff["outcome"] == "handoff_created" and handoff["verified"]
            assert "ESC-04" in handoff["handoff"]["reason_codes"]
            human = check(
                client.post(
                    conversation() + "/messages",
                    json={
                        "message": "Quero falar com uma pessoa"
                        if pt
                        else "Quiero hablar con una persona"
                    },
                )
            )
            assert human["outcome"] == "handoff_created" and human["verified"]
            counts["handoffs"] += 2
            queue = check(client.get("agent/handoffs"))
            assert len(queue) == 2
            packet = "agent/handoffs/" + human["handoff"]["handoff_id"]
            claim = check(
                client.post(
                    packet + "/claim",
                    json={"expected_version": 1, "idempotency_key": secrets.token_hex(12)},
                )
            )
            assert claim["status"] == "claimed" and check(client.get(packet)) == claim
            counts["claims"] += 1
            resolved = check(
                client.post(
                    packet + "/resolve",
                    json={
                        "expected_version": 2,
                        "idempotency_key": secrets.token_hex(12),
                        "resolution": "review_completed",
                    },
                )
            )
            assert resolved["status"] == "resolved" and check(client.get(packet)) == resolved
            counts["resolutions"] += 1
            snapshot = check(client.get("ops/snapshot"))
            assert (
                snapshot["source_kind"] == "organizer_serving"
                and snapshot["dataset_version"] == ledger.dataset_version
            )
            assert snapshot["metrics"]["cases"] == 1 and snapshot["metrics"]["handoffs"] == 2
            assert snapshot["metrics"]["sar"] is None and snapshot["metrics"]["unsafe_rate"] is None
            assert all(q["passed"] for q in snapshot["quality"])
            for cid in snapshot["conversation_ids"]:
                check(client.get(f"chat/sessions/{cid}/trace"))
            token = client.cookies.get("aclara_access")
            assert token is not None
            run_id, sid, _ = token.split(".", 2)
            with ledger.store.transaction(Scope(persona.customer_id, run_id, sid)):
                pg = ledger.store._unit().connection
                assert pg is not None
                audit = pg.execute(
                    "SELECT sequence,canonical,prev_hash,row_hash FROM ops.audit_log ORDER BY sequence"
                ).fetchall()
                counts["audit_entries"] += verify(audit, (persona.customer_id, run_id, sid))
            recovery = {
                "case_path": case_path,
                "case": filed["case"],
                "cookies": dict(client.cookies),
            }
    assert recovery is not None
    print(
        json.dumps(
            {
                "serving_bff_smoke": "passed",
                "counts": counts,
                "dataset_version": ledger.dataset_version,
            }
        )
    )  # noqa: T201
    return recovery
