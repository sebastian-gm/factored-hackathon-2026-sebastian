"""Owner-approved real-provider smoke: at most five conversations and USD 0.10."""

# ruff: noqa: T201 -- aggregate receipts only; never print responses or credentials.
from __future__ import annotations

import argparse
import fcntl
import json
import secrets
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
import psycopg
from scripts.azure_dev import ROOT, VAULT, az, private_write, read_variables
from scripts.azure_migrate_ops import connection_string
from scripts.serving_smoke import check, wait_config

from aclara.agent.contracts import DisputeCaseView
from aclara.bank.serving import ServingRepository
from aclara.ops.store import Scope, Store
from aclara.policy.engine import evaluate
from aclara.settings import Settings

WEB = "https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io"
CHECKPOINT = ROOT / "artifacts/azure/llm-smoke-conversations.json"


@contextmanager
def conversation_allowance(count: int, label: str):
    """Account for attempted conversations before any model-triggering request."""
    lock = ROOT / "artifacts/azure/llm-smoke.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = (
            json.loads(CHECKPOINT.read_text())
            if CHECKPOINT.exists()
            else {"attempted": 0, "runs": []}
        )
        if not 1 <= count <= 5 or state["attempted"] + count > 5:
            raise RuntimeError("The owner-approved five-conversation smoke allowance is exhausted")
        state["attempted"] += count
        state["runs"].append(
            {"label": label, "count": count, "started_at": datetime.now(UTC).isoformat()}
        )
        private_write(CHECKPOINT, json.dumps(state) + "\n")
        yield


def budget_receipt() -> dict[str, Any]:
    with psycopg.connect(connection_string("aclara_admin")) as connection:
        connection.execute("SET LOCAL ROLE aclara_owner")
        assert connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope='production'"
        ).fetchone() == (3, False)
        assert connection.execute(
            "SELECT limit_usd,enabled FROM llm.runs WHERE scope='production' AND run_id='handoff09-smoke'"
        ).fetchone() == (Decimal("0.10"), True)
        row = connection.execute(
            "SELECT count(*),coalesce(sum(actual_usd),0),coalesce(sum(charged_usd),0),count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope='production' AND run_id='handoff09-smoke'"
        ).fetchone()
    assert row is not None and float(row[2]) <= 0.10
    return {
        "attempts": row[0],
        "known_cost_usd": float(row[1]),
        "charged_with_reserves_usd": float(row[2]),
        "unknown_cost_attempts": row[3],
    }


def exercise(name: str, password: str, ledger: ServingRepository) -> dict[str, Any]:
    username = "demo.pt.br" if name == "pt_ambiguous" else "demo.es.mx"
    persona = next(p for p in ledger.personas() if p.username == username)
    with httpx.Client(base_url=WEB + "/api/bff/", headers={"Origin": WEB}, timeout=190) as client:
        assert not wait_config(client)["fixtures"]
        challenge = check(
            client.post("auth/login", json={"username": username, "password": password})
        )
        code = check(client.get(f"auth/challenges/{challenge['challenge_id']}/sms"))["code"]
        check(
            client.post(
                "auth/otp/verify", json={"challenge_id": challenge["challenge_id"], "code": code}
            )
        )
        assert check(client.get("me"))["role"] == "ops"
        cid = check(client.post("chat/sessions", json={}))["conversation_id"]
        path = "chat/sessions/" + cid

        def message(text: str) -> dict[str, Any]:
            return check(client.post(path + "/messages", json={"message": text}))

        result: dict[str, Any]
        if name == "es_normal":
            rows = ledger.for_customer(persona.customer_id, ledger.bank_clock)
            handle, target = next(
                (h, r)
                for h, r in rows
                if evaluate(r, ledger.bank_clock, True, ledger.context(r)).decision == "eligible"
            )
            description = f"{target.amount:.2f} {target.currency} en {target.merchant_name} el {target.transaction_date.date().isoformat()}"

            def identify(result: dict[str, Any]) -> dict[str, Any]:
                if result["outcome"] == "choose_transaction":
                    candidates = result["candidates"]
                    choice = next(i for i, row in enumerate(candidates) if row["handle"] == handle)
                    return message(("primero", "segundo", "tercero")[choice])
                return result

            explained = identify(message("¿Por qué aparece un cargo de " + description + "?"))
            assert explained["outcome"] == "explained"
            proposal = identify(
                message(
                    "Yo no autoricé esta compra de " + description + ". Quiero abrir una disputa."
                )
            )
            assert proposal["outcome"] == "dispute_proposed"
            result = check(
                client.post(
                    path + "/confirm",
                    json={
                        "proposal_hash": proposal["proposal"]["proposal_hash"],
                        "confirmed": True,
                    },
                )
            )
            assert result["outcome"] == "dispute_filed" and result["verified"]
            assert DisputeCaseView.model_validate(
                check(client.get("disputes/" + result["case"]["case_id"]))
            ) == DisputeCaseView.model_validate(result["case"])
        elif name == "pt_ambiguous":
            result = message(
                "Não reconheço uma cobrança no meu extrato. Pode me ajudar a identificar?"
            )
            assert result["outcome"] == "choose_transaction" and 1 <= len(result["candidates"]) <= 3
            for _ in range(2):
                result = message("Não sei, não consigo escolher")
            assert result["outcome"] == "handoff_created" and result["verified"]
            assert "ESC-04" in result["handoff"]["reason_codes"]
        else:
            result = message("Me robaron la tarjeta y sospecho fraude. Necesito ayuda.")
            assert result["outcome"] == "handoff_created" and result["verified"]
            assert "FRD-01" in result["handoff"]["reason_codes"]

        if result.get("handoff"):
            packet = "agent/handoffs/" + result["handoff"]["handoff_id"]
            initial = check(client.get(packet))
            claimed = check(
                client.post(
                    packet + "/claim",
                    json={
                        "expected_version": initial["version"],
                        "idempotency_key": secrets.token_hex(12),
                    },
                )
            )
            assert check(client.get(packet)) == claimed and claimed["status"] == "claimed"
            resolved = check(
                client.post(
                    packet + "/resolve",
                    json={
                        "expected_version": claimed["version"],
                        "idempotency_key": secrets.token_hex(12),
                        "resolution": "review_completed",
                    },
                )
            )
            assert check(client.get(packet)) == resolved and resolved["status"] == "resolved"
        snapshot = check(client.get("ops/snapshot"))
        assert snapshot["source_kind"] == "organizer_serving"
        assert snapshot["metrics"]["sar"] is None
        access = client.cookies.get("aclara_access")
        assert access
        run_id, sid, _ = access.split(".", 2)
        with ledger.store.transaction(Scope(persona.customer_id, run_id, sid)):
            records = ledger.store.mapping("execution_records", dict)
            events = [
                event
                for value in records.values()
                if value.get("conversation_id") == cid
                for event in value.get("events", [])
            ]
        nlu = [e for e in events if e["event"] == "nlu"]
        calls = [e for e in events if e["event"] == "llm_call"]
        assert nlu and all(not e["degraded"] for e in nlu)
        assert any(e["status"] == "valid" and e["prompt_id"] == "nlu@v4" for e in calls)
        assert all(e["provider"] == "openai_compat" for e in calls)
        assert {e["model_id"] for e in calls} <= {"google/gemini-3-flash-preview", "x-ai/grok-4.20"}
        if name != "fraud":
            matches = [e for e in events if e["event"] == "match"]
            assert matches and all(e["matcher_version"].startswith("v2") for e in matches)
        check(client.post("auth/logout", json={}))
        assert client.get("me").status_code == 401
        return {
            "scenario": name,
            "status": "passed",
            "model_attempts": len(calls),
            "valid_attempts": sum(e["status"] == "valid" for e in calls),
            "fallback_attempts": sum(e["model_id"] == "x-ai/grok-4.20" for e in calls),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case", choices=("all", "es_normal", "pt_ambiguous", "fraud"), default="all"
    )
    args = parser.parse_args()
    variables = read_variables()
    assert (
        variables.get("enable_real_llm") and variables.get("llm_budget_run_id") == "handoff09-smoke"
    )
    before = budget_receipt()
    assert before["charged_with_reserves_usd"] < 0.10
    password = az("keyvault", "secret", "show", "--vault-name", VAULT, "--name", "demo-password")[
        "value"
    ]
    cases = ("es_normal", "pt_ambiguous", "fraud") if args.case == "all" else (args.case,)
    store = Store(connection_string("aclara_app"))
    try:
        ledger = ServingRepository(store, Settings().bank_clock)
        results = []
        for name in cases:
            with conversation_allowance(1, name):
                result = exercise(name, password, ledger)
                results.append(result)
                print(json.dumps(result), flush=True)
                private_write(
                    ROOT / "artifacts/azure/llm-smoke.json",
                    json.dumps(
                        {
                            "release": variables["image_tag"],
                            "results": results,
                            "budget": budget_receipt(),
                        }
                    )
                    + "\n",
                )
    finally:
        store.close()
    print(json.dumps({"real_smoke": "passed", **budget_receipt()}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback

        print(
            type(exc).__name__,
            [(f.name, f.lineno) for f in traceback.extract_tb(exc.__traceback__)],
        )
        raise SystemExit(1) from None
