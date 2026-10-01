"""Zero-spend authored-ledger smoke through local Compose's live BFF."""

# ruff: noqa: T201 -- aggregates and exception frame locations only.

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx
from dotenv import dotenv_values
from scripts.serving_smoke import check, wait_config

from aclara.agent.contracts import DisputeCaseView


def main() -> None:
    values = dotenv_values(".env")
    if values.get("LEDGER_BACKEND") != "fixture" or values.get("LLM_PROVIDER") != "mock":
        raise RuntimeError("This smoke requires the authored fixture ledger and mock provider")
    if values.get("LLM_REAL_CALLS_APPROVED", "0") not in {"0", ""}:
        raise RuntimeError("Paid calls must remain disabled")
    if values.get("DEMO_ROLE") != "ops":
        raise RuntimeError("Set DEMO_ROLE=ops to verify all three local surfaces")
    port = int(values.get("WEB_HOST_PORT") or "3000")
    if not 1 <= port <= 65535:
        raise ValueError("Invalid local web port")
    web = f"http://localhost:{port}"
    with httpx.Client(base_url=web + "/api/bff/", headers={"Origin": web}, timeout=190) as client:
        config = wait_config(client)
        if config["fixtures"]:
            raise RuntimeError("Use the live BFF against the local API, not presentation fixtures")
        assert client.get("transactions").status_code == 401
        challenge = check(
            client.post(
                "auth/login",
                json={"username": values["DEMO_USERNAME"], "password": values["DEMO_PASSWORD"]},
            )
        )
        sms = check(client.get(f"auth/challenges/{challenge['challenge_id']}/sms"))
        check(
            client.post(
                "auth/otp/verify",
                json={"challenge_id": challenge["challenge_id"], "code": sms["code"]},
            )
        )
        me = check(client.get("me"))
        assert me["role"] == "ops"
        clock = datetime.fromisoformat(me["bank_clock"].replace("Z", "+00:00"))
        rows = check(client.get("transactions"))
        target = next(
            row
            for row in rows
            if row["status"] == "Approved"
            and row["currency"] == "USD"
            and row["merchant"]
            and Decimal(str(row["amount"])) < 450
            and 0
            <= (clock.date() - datetime.fromisoformat(row["transaction_date"]).date()).days
            < 30
        )
        pt = me["locale"] == "pt-BR"
        description = f"{target['amount']} {target['currency']} {target['merchant']} {target['transaction_date'][:10]}"
        cid = check(client.post("chat/sessions", json={}))["conversation_id"]
        path = "chat/sessions/" + cid

        def message(text: str) -> dict[str, Any]:
            result = check(client.post(path + "/messages", json={"message": text}))
            if result["outcome"] == "choose_transaction":
                position = next(
                    i
                    for i, row in enumerate(result["candidates"])
                    if row["handle"] == target["handle"]
                )
                result = check(
                    client.post(
                        path + "/messages",
                        json={
                            "message": ("primeiro", "segundo", "terceiro")[position]
                            if pt
                            else ("primero", "segundo", "tercero")[position]
                        },
                    )
                )
            return result

        explained = message(
            ("Quero consultar uma cobrança de " if pt else "Quiero consultar un cargo de ")
            + description
            + "?"
        )
        assert explained["outcome"] == "explained"
        cid = check(client.post("chat/sessions", json={}))["conversation_id"]
        path = "chat/sessions/" + cid
        offered = message(
            ("Não reconheço a cobrança de " if pt else "No reconozco el cargo de ") + description
        )
        assert offered["response_type"] == "offer_dispute"
        proposal = message("Não fui eu, quero contestar" if pt else "No fui yo, quiero disputarlo")
        assert proposal["outcome"] == "dispute_proposed"
        receipt = check(
            client.post(
                path + "/confirm",
                json={"proposal_hash": proposal["proposal"]["proposal_hash"], "confirmed": True},
            )
        )
        assert receipt["outcome"] == "dispute_filed" and receipt["verified"]
        assert DisputeCaseView.model_validate(receipt["case"]) == DisputeCaseView.model_validate(
            check(client.get("disputes/" + receipt["case"]["case_id"]))
        )
        assert receipt["case"]["transaction_handle"] == target["handle"]
        cid = check(client.post("chat/sessions", json={}))["conversation_id"]
        handoff = check(
            client.post(
                "chat/sessions/" + cid + "/messages",
                json={
                    "message": "Quero falar com uma pessoa"
                    if pt
                    else "Quiero hablar con una persona"
                },
            )
        )
        assert handoff["outcome"] == "handoff_created" and handoff["verified"]
        packet = check(client.get("agent/handoffs/" + handoff["handoff"]["handoff_id"]))
        assert packet["handoff_id"] == handoff["handoff"]["handoff_id"]
        assert "ESC-01" in packet["reason_codes"]
        snapshot = check(client.get("ops/snapshot"))
        assert snapshot["source_kind"] == "authored_fixture"
        assert snapshot["metrics"]["cases"] == 1 and snapshot["metrics"]["handoffs"] == 1
        assert all(item["passed"] for item in snapshot["quality"])
        check(client.post("auth/logout", json={}))
        assert client.get("me").status_code == 401
    print(
        json.dumps(
            {
                "fixture_bff_smoke": "passed",
                "auth_otp": True,
                "cases_verified": 1,
                "handoffs_verified": 1,
                "staff_reads": True,
                "logout_verified": True,
                "model_cost_usd": 0,
            }
        )
    )  # noqa: T201


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        frames = []
        tb = error.__traceback__
        while tb is not None:
            frames.append(f"{tb.tb_frame.f_code.co_name}:{tb.tb_lineno}")
            tb = tb.tb_next
        raise SystemExit(
            "Fixture smoke failed: " + type(error).__name__ + " at " + ",".join(frames)
        ) from None
