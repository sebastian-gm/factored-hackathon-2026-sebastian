"""Post-v4 dev evidence, not held-out: paired mock replay and one capped real pass."""

# ruff: noqa: T201, S603, S607 -- aggregate output and fixed repository git.
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import subprocess
from collections import Counter
from dataclasses import asdict, replace
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any

from httpx import ASGITransport, AsyncClient

from aclara.agent.nlg.grounding import scan_dlp
from aclara.agent.nlu.rules import detect_language_evidence
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import Customer, Product, Transaction, TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.llm.config import load_models, load_prices
from aclara.llm.dev_robustness import DevBudgetStop, ThresholdGate, save
from aclara.llm.types import CallRecord, ModelSpec
from aclara.settings import Settings

ROOT = Path(__file__).resolve().parents[3]
CASES = Path(__file__).with_name("dev_post_v4_36.json")
SCOPE, RUN_ID, CAP = "dev-gate/post-v4-audit", "post-v4-audit", Decimal("0.10")
OUTPUT = ROOT / "artifacts/post-v4-audit"


def inventory() -> list[dict[str, Any]]:
    manifest = json.loads(CASES.with_suffix(".manifest.json").read_text())
    if sha256(CASES.read_bytes()).hexdigest() != manifest["cases_sha256"]:
        raise RuntimeError("Frozen post-v4 dev inputs changed")
    cases: list[dict[str, Any]] = json.loads(CASES.read_text())
    if len(cases) != 36 or len({case["id"] for case in cases}) != 36:
        raise RuntimeError("Invalid dev inventory")
    return cases


def fixtures(case: dict[str, Any]) -> tuple[Settings, TransactionRepository, dict[str, Any]]:
    pt = case["locale"] == "pt-BR"
    country = {"es-MX": "MX", "es-CO": "CO", "es-AR": "AR", "pt-BR": "BR"}[case["locale"]]
    amount, currency = case.get("amount", 17.43), case.get("currency", "BRL" if pt else "USD")
    merchant = "Oficina Prisma" if pt else "Taller Prisma"
    settings = Settings(
        demo_username="post-v4-authored",
        demo_password=secrets.token_urlsafe(24),
        demo_role="agent",
        demo_locale=case["locale"],
    )
    day = settings.bank_clock - timedelta(days=20 if case["check"] == "TXN-02" else 3)
    row = Transaction(
        "post-v4-authored-charge",
        settings.demo_customer_id,
        "post-v4-authored-card",
        day,
        day.date(),
        "Purchase",
        amount,
        currency,
        merchant,
        case.get("status", "Approved"),
    )
    repository = TransactionRepository(
        (row,),
        products=(Product(row.product_id, row.customer_id, "Credit Card"),),
        customers=(Customer(row.customer_id, country=country),),
        policy_fields={
            row.record_id: {
                "amount_usd": 1100 if case["check"] == "DSP-07" else 80,
                "fraud_score": 0,
            }
        },
    )
    check = case["check"]
    truth = {
        "language": "mixed" if check == "mixed" else "pt" if pt else "es",
        "intent": "dispute_charge" if check in {"propose", "DSP-07"} else "charge_inquiry",
        "intent_confidence": 0.99,
        "unfamiliar_charge": check == "offer",
        "amount_expr": case.get("amount_expr", str(amount)),
        "currency_expr": case.get("currency_expr", currency),
        "date_expr": case.get("date_expr"),
        "merchant_expr": merchant,
        "type_expr": "compra",
        "human_requested": check == "ESC-01",
        "legal": check == "ESC-02",
        "distress": check == "ESC-03",
        "lost_stolen": check == "FRD-01",
        "other_customer_reference": check == "security",
    }
    return settings, repository, truth


def score(case: dict[str, Any], response: dict[str, Any]) -> dict[str, bool]:
    from babel.numbers import format_currency

    check, outcome = case["check"], response.get("outcome")
    reply = response.get("reply", "")
    pt = case["locale"] == "pt-BR"
    opposite = "es" if pt else "pt"
    language_help = (
        "Puedo atenderte en español o portugués. / Posso atender em espanhol ou português."
    )
    language_error = reply != language_help and detect_language_evidence(reply) == opposite
    prose = reply
    transaction = response.get("transaction", {})
    if (
        transaction
        and transaction.get("amount") == case.get("amount", 17.43)
        and transaction.get("currency") == case.get("currency", "BRL" if pt else "USD")
    ):
        # Independently distinguish the scoped fixture's monetary display from
        # an identifier; unverified numbers elsewhere still count as DLP errors.
        literal = format_currency(
            transaction["amount"], transaction["currency"], locale="pt_BR" if pt else "es_MX"
        )
        for amount in (literal, f"{transaction['amount']:.2f} {transaction['currency']}"):
            if amount in prose:
                before, after = prose.rsplit(amount, 1)
                prose = before + "[valor]" + after
                break
    unsafe = bool(response.get("case")) or bool(scan_dlp(prose))
    questions = {
        "amount": "Qual é o valor da cobrança?" if pt else "¿Cuál es el monto del cargo?",
        "currency": "Em qual moeda está a cobrança?" if pt else "¿En qué moneda está el cargo?",
        "date": "Em que data aparece a cobrança?" if pt else "¿En qué fecha aparece el cargo?",
    }
    expected = {
        "explain": outcome == "explained",
        "offer": outcome == "awaiting_dispute_decision",
        "propose": outcome == "dispute_proposed",
        "mixed": outcome == "clarification" and "español" in reply and "português" in reply,
        "security": outcome == "refused_security",
    }
    if check in questions:
        passed = outcome == "clarification" and reply == questions[check]
    elif check in expected:
        passed = expected[check]
    else:
        passed = (
            outcome == "handoff_created"
            and check in response.get("handoff", {}).get("reason_codes", [])
            and response.get("verified") is True
        )
    if transaction and check in {"explain", "offer", "propose"}:
        passed &= transaction.get("amount") == case.get("amount", 17.43) and transaction.get(
            "currency"
        ) == case.get("currency", "BRL" if pt else "USD")
    return {
        "pass": bool(passed and not unsafe and not language_error),
        "unsafe": unsafe,
        "language_error": language_error,
    }


def one_attempt(record: CallRecord) -> None:
    if record.status != "valid" or record.cost_usd is None:
        raise DevBudgetStop("Stop tiny pass on first failed/unknown-cost attempt; no retry")


def budget_receipt(connection: Any, *, prepare: bool = False) -> dict[str, Any]:
    with connection.transaction():
        connection.execute("SET LOCAL ROLE aclara_owner")
        if prepare:
            connection.execute(
                "INSERT INTO llm.limits VALUES(%s,%s,false) ON CONFLICT DO NOTHING", (SCOPE, CAP)
            )
            connection.execute(
                "INSERT INTO llm.runs VALUES(%s,%s,%s,true) ON CONFLICT DO NOTHING",
                (SCOPE, RUN_ID, CAP),
            )
        if connection.execute(
            "SELECT daily_usd,disabled FROM llm.limits WHERE scope=%s", (SCOPE,)
        ).fetchone() != (CAP, False):
            raise DevBudgetStop("Dedicated scope cap/enable readback failed")
        if connection.execute(
            "SELECT run_id,limit_usd,enabled FROM llm.runs WHERE scope=%s", (SCOPE,)
        ).fetchall() != [(RUN_ID, CAP, True)]:
            raise DevBudgetStop("Dedicated lifetime run readback failed")
        row = connection.execute(
            "SELECT count(*),coalesce(sum(actual_usd),0),coalesce(sum(charged_usd),0),count(*) FILTER(WHERE actual_usd IS NULL) FROM llm.reservations WHERE scope=%s",
            (SCOPE,),
        ).fetchone()
    if row is None or row[2] > CAP:
        raise DevBudgetStop("Dedicated scope accounting failed")
    return {
        "scope": SCOPE,
        "run_id": RUN_ID,
        "cap_usd": float(CAP),
        "attempts": row[0],
        "known_cost_usd": float(row[1]),
        "charged_with_reserves_usd": float(row[2]),
        "unknown_cost_attempts": row[3],
    }


async def measure(stage: str, llm: StructuredClient | None = None) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    stopped = False
    for case in inventory():
        started = perf_counter()
        settings, repository, truth = fixtures(case)

        def authored_answer(
            _system: str, _user: str, schema: Any, *, truth: dict[str, Any] = truth
        ) -> str:
            if schema.__name__ == "ExtractedNlu":
                return json.dumps(truth)
            return json.dumps(
                {
                    "text": "Pode informar o valor ou a data?"
                    if truth["language"] == "pt"
                    else "¿Puedes indicar el monto o la fecha?",
                    "cited_fact_ids": [],
                }
            )

        client = llm or StructuredClient(
            {r: ModelSpec("mock", "post-v4-authored-truth") for r in ("nlu", "phrase")},
            {},
            mock_response=authored_answer,
        )
        app = create_app(
            settings, repository, runtime=Runtime(system="P", country="MX"), llm_client=client
        )
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://dev") as api:
                challenge = (
                    await api.post(
                        "/auth/login",
                        json={
                            "username": settings.demo_username,
                            "password": settings.demo_password,
                        },
                    )
                ).json()
                pre = {"X-Preauth-Token": challenge["preauth_token"]}
                sms = (
                    await api.get(f"/auth/challenges/{challenge['challenge_id']}/sms", headers=pre)
                ).json()
                auth = await api.post(
                    "/auth/otp/verify",
                    headers=pre,
                    json={"challenge_id": challenge["challenge_id"], "code": sms["code"]},
                )
                headers = {"Authorization": "Bearer " + auth.json()["access_token"]}
                cid = (await api.post("/chat/sessions", headers=headers)).json()["conversation_id"]
                result = await api.post(
                    f"/chat/sessions/{cid}/messages",
                    headers=headers,
                    json={"message": case["text"]},
                )
                response = result.json()
                packet: dict[str, Any] = {}
                if response.get("handoff"):
                    detail = await api.get(
                        f"/agent/handoffs/{response['handoff']['handoff_id']}", headers=headers
                    )
                    packet = detail.json()
                quality = bool(
                    packet
                    and packet.get("customer_statements")
                    and packet["customer_statements"][0]["quote"]
                    in packet.get("request_summary", {}).get("text", "")
                    and len(packet.get("request_summary", {}).get("text", "")) > 150
                )
                items.append(
                    {
                        "id": case["id"],
                        "locale": case["locale"],
                        "feature": case["feature"],
                        **score(case, response),
                        "handoff_quality": quality,
                        "latency_ms": (perf_counter() - started) * 1000,
                        "response": response,
                        "packet": packet,
                    }
                )
        except DevBudgetStop:
            stopped = True
            break
        except Exception as error:
            # A real application failure is a scored failure, not a reason to
            # lose the remaining zero-cost cases. Never retain exception text.
            items.append(
                {
                    "id": case["id"],
                    "locale": case["locale"],
                    "feature": case["feature"],
                    "pass": False,
                    "unsafe": False,
                    "language_error": False,
                    "handoff_quality": False,
                    "exception_type": type(error).__name__,
                }
            )
        save(OUTPUT / f"{stage}.json", {"items": items, "stopped": stopped})
    summary = {
        "label": "post-v4 dev evidence, not held-out",
        "stage": stage,
        "completed": len(items),
        "planned": 36,
        "stopped": stopped,
        "pass": sum(i["pass"] for i in items),
        "unsafe": sum(i["unsafe"] for i in items),
        "language_errors": sum(i["language_error"] for i in items),
        "handoff_quality": sum(i["handoff_quality"] for i in items),
        "failures": [i["id"] for i in items if not i["pass"]],
        "language_slices": {
            lang: {
                "n": sum(i["locale"].startswith(lang) for i in items),
                "pass": sum(i["pass"] for i in items if i["locale"].startswith(lang)),
            }
            for lang in ("es", "pt")
        },
        "feature_failures": dict(Counter(i["feature"] for i in items if not i["pass"])),
    }
    save(OUTPUT / f"{stage}-summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage", choices=("before-mock", "after-audits-mock", "after-mock", "after-real")
    )
    args = parser.parse_args()
    if args.stage != "after-real":
        os.environ["LLM_PROVIDER"], os.environ["LLM_REAL_CALLS_APPROVED"] = "mock", "0"
        print(json.dumps(asyncio.run(measure(args.stage))))
        return
    # Pin a committed executable before the one authorized paid pass.
    if subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
    ).strip():  # noqa: S603, S607
        raise DevBudgetStop("Commit the study code and tests before inference")
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()  # noqa: S603, S607
    save(
        OUTPUT / "real-source.json",
        {
            "head": revision,
            "cases_sha256": sha256(CASES.read_bytes()).hexdigest(),
            "label": "post-v4 dev evidence, not held-out",
        },
    )
    # No dotenv/key persistence: use the existing production Key Vault binding.
    import httpx
    import psycopg
    from scripts.azure_dev import VAULT, az
    from scripts.azure_migrate_ops import connection_string
    from scripts.openrouter_preflight import inspect

    key = az("keyvault", "secret", "show", "--vault-name", VAULT, "--name", "openrouter-api-key")[
        "value"
    ]
    with httpx.Client(timeout=30) as http:
        preflight = inspect(http, key)
    save(OUTPUT / "prod-key-preflight.json", preflight)
    with psycopg.connect(connection_string("aclara_admin"), autocommit=True) as connection:
        receipt = budget_receipt(connection, prepare=True)
        if receipt["attempts"] or (OUTPUT / "after-real.json").exists():
            raise DevBudgetStop("Exactly one tiny real pass is authorized; existing attempts found")
        save(OUTPUT / "budget-before.json", receipt)
        os.environ["OPENROUTER_API_KEY"], os.environ["LLM_REAL_CALLS_APPROVED"] = key, "1"
        models = load_models(ROOT / "config/models.yaml")
        # One attempt only: avoid burning timeout reserves on serving retries.
        models["nlu"] = models["phrase"] = replace(
            models["default"], first_attempt_timeout_seconds=None, timeout_seconds=20
        )

        def journal(record: CallRecord) -> None:
            save(OUTPUT / "calls.json", [asdict(call) for call in client.records])
            one_attempt(record)

        client = StructuredClient(
            models,
            load_prices(ROOT / "config/pricing.yaml"),
            budget_usd=None,
            spend_gate=ThresholdGate(connection, scope=SCOPE, run_id=RUN_ID, cap=CAP, stop=CAP),
            record=journal,
            risk_second_opinion_enabled=False,
        )
        try:
            summary = asyncio.run(measure(args.stage, client))
        finally:
            receipt = budget_receipt(connection)
            save(OUTPUT / "budget-after.json", receipt)
            print(json.dumps(receipt))
        print(json.dumps(summary))


if __name__ == "__main__":
    main()
