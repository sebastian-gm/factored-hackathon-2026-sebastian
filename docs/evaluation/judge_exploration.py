"""Authored conversation exploration against the real local API, with no paid calls.

Run: .venv/bin/python docs/evaluation/judge_exploration.py
Mock NLU is supplied independently in each authored turn; the application owns
normalization, matching, policy, state, confirmation, and readback. Phrasing uses
approved templates. This does not measure a live model or a browser session.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import re
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from unittest.mock import patch

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from aclara.agent.contracts import DisputeCaseView, HandoffView
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.agent.runtime import Runtime
from aclara.bank.repository import Customer, Transaction, TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec
from aclara.ops.store import Scope, Store
from aclara.settings import Settings

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = Path(__file__).with_name("judge-exploration-cases.json")
PROFILES: dict[str, tuple[str, Literal["es-MX", "es-CO", "es-AR", "pt-BR"]]] = {
    "mx-es": ("MX", "es-MX"),
    "co-es": ("CO", "es-CO"),
    "ar-es": ("AR", "es-AR"),
    "pt": ("BR", "pt-BR"),
}
FIXTURES = (
    ("approved", "Taller Prisma", 20.0, 16, "Approved"),
    ("second", "Estudio Nube", 35.0, 15, "Approved"),
    ("candidate_a", "Café Aurora", 12.0, 14, "Approved"),
    ("candidate_b", "Café Aurora", 24.0, 13, "Approved"),
    ("pending", "Hotel Brisa", 18.75, 17, "Pending"),
    ("reversed", "Teatro Sauce", 73.20, 12, "Reversed"),
)


def synthetic_ledger(
    country: str,
    required_aliases: list[str] | None = None,
) -> tuple[TransactionRepository, dict[str, dict[str, Any]]]:
    selected = [
        fixture
        for fixture in FIXTURES
        if required_aliases is None or fixture[0] in required_aliases
    ]
    if required_aliases is not None and set(required_aliases) != {
        fixture[0] for fixture in selected
    }:
        raise ValueError("Unknown synthetic fixture alias")
    rows = tuple(
        Transaction(
            alias,
            "exploration-customer",
            "exploration-card",
            datetime(2026, 6, day, 9, tzinfo=UTC),
            datetime(2026, 6, day, tzinfo=UTC).date(),
            "Purchase",
            amount,
            "USD",
            merchant,
            status,
        )
        for alias, merchant, amount, day, status in selected
    )
    aliases = {
        alias: {
            "merchant": merchant,
            "amount": f"{amount:.2f}",
            "currency": "USD",
            "date": f"2026-06-{day:02d}",
            "status": status,
            "handle": f"txn_{index}",
        }
        for index, (alias, merchant, amount, day, status) in enumerate(selected, 1)
    }
    return TransactionRepository(
        rows, customers=(Customer("exploration-customer", country=country),)
    ), aliases


def expand(value: Any, aliases: dict[str, dict[str, Any]]) -> Any:
    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            alias, field = match.group(1).split(".", 1)
            return str(aliases[alias][field])

        return re.sub(r"\{\{([a-z_]+\.[a-z_]+)\}\}", replace, value)
    if isinstance(value, dict):
        return {key: expand(item, aliases) for key, item in value.items()}
    if isinstance(value, list):
        return [expand(item, aliases) for item in value]
    return value


async def sign_in(client: AsyncClient, settings: Settings) -> dict[str, str]:
    login = await client.post(
        "/auth/login", json={"username": settings.demo_username, "password": settings.demo_password}
    )
    if login.status_code != 200:
        raise RuntimeError(f"Synthetic login failed: HTTP {login.status_code}")
    challenge = login.json()
    preauth = {"X-Preauth-Token": challenge["preauth_token"]}
    sms = await client.get(f"/auth/challenges/{challenge['challenge_id']}/sms", headers=preauth)
    if sms.status_code != 200:
        raise RuntimeError(f"Synthetic OTP lookup failed: HTTP {sms.status_code}")
    verified = await client.post(
        "/auth/otp/verify",
        headers=preauth,
        json={"challenge_id": challenge["challenge_id"], "code": sms.json()["code"]},
    )
    if verified.status_code != 200:
        raise RuntimeError(f"Synthetic OTP verification failed: HTTP {verified.status_code}")
    return {"Authorization": "Bearer " + verified.json()["access_token"]}


def state(app: FastAPI, token: str, conversation_id: str) -> dict[str, Any]:
    principal = app.state.sessions[token]
    with app.state.store.transaction(
        Scope(principal.customer_id, principal.run_id, principal.session_id)
    ):
        conversation = app.state.conversations[conversation_id]
        return {
            "language": conversation.language,
            "selected_handle": conversation.selected_handle,
            "offer_handle": conversation.offer_handle,
            "proposal_hash": conversation.proposal.action_hash if conversation.proposal else None,
            "terminal_handoff": bool(conversation.terminal_handoff_id),
            "cases": [dict(case) for case in app.state.cases.values()],
            "card_states": dict(app.state.card_states),
        }


def public_state(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "language": value["language"],
        "selected_handle": value["selected_handle"],
        "offer_handle": value["offer_handle"],
        "proposal_pending": bool(value["proposal_hash"]),
        "terminal_handoff": value["terminal_handoff"],
        "case_count": len(value["cases"]),
    }


def transaction_handle(response: dict[str, Any]) -> str | None:
    handle = (response.get("transaction") or {}).get("handle") or (response.get("case") or {}).get(
        "transaction_handle"
    )
    return str(handle) if handle is not None else None


def checks(
    expect: dict[str, Any],
    status: int,
    response: dict[str, Any],
    before: dict[str, Any],
    after: dict[str, Any],
    previous: list[dict[str, Any]],
    aliases: dict[str, dict[str, Any]],
    kind: str,
    level: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    def add(name: str, passed: bool) -> None:
        control = name == "no_financial_write"
        workflow = name in {"http_status", "nonempty_reply", "case_count", "verified"}
        results.append(
            {
                "check": name,
                "passed": passed,
                "level": "control"
                if control
                else "workflow"
                if workflow or level == "contract"
                else level,
            }
        )

    add("http_status", status == expect.get("http_status", 200))
    if status == 200:
        add("nonempty_reply", bool(response.get("reply", "").strip()))
    changed = before["cases"] != after["cases"] or before["card_states"] != after["card_states"]
    if kind == "message" or expect.get("no_write"):
        add("no_financial_write", not changed)
    if "response_types" in expect:
        add("response_types", response.get("response_type") in expect["response_types"])
    if "language" in expect:
        add("conversation_language", after["language"] == expect["language"])
    if "transaction_alias" in expect:
        add(
            "transaction_alias",
            transaction_handle(response) == aliases[expect["transaction_alias"]]["handle"],
        )
    if "case_count" in expect:
        add("case_count", len(after["cases"]) == expect["case_count"])
    if "verified" in expect:
        add("verified", response.get("verified") is expect["verified"])
    if expect.get("no_handoff"):
        add("no_handoff", not response.get("handoff"))
    for field, obj, key in (
        ("same_case_as_turn", "case", "case_id"),
        ("same_handoff_as_turn", "handoff", "handoff_id"),
    ):
        if field in expect:
            old = (previous[expect[field] - 1]["response"].get(obj) or {}).get(key)
            add(field, bool(old) and (response.get(obj) or {}).get(key) == old)
    if "same_transaction_as_turn" in expect:
        old = transaction_handle(previous[expect["same_transaction_as_turn"] - 1]["response"])
        add("same_transaction_as_turn", bool(old) and transaction_handle(response) == old)
    return results


async def readback(
    client: AsyncClient, headers: dict[str, str], response: dict[str, Any]
) -> list[dict[str, Any]]:
    results = []
    for field, model, path, key in (
        ("case", DisputeCaseView, "disputes", "case_id"),
        ("handoff", HandoffView, "handoffs", "handoff_id"),
    ):
        if response.get(field):
            receipt = await client.get(f"/{path}/{response[field][key]}", headers=headers)
            try:
                public = {
                    key: value for key, value in receipt.json().items() if key in model.model_fields
                }
                passed = (
                    receipt.status_code == 200
                    and model.model_validate(public) == model.model_validate(response[field])
                    and (field != "case" or response.get("verified") is True)
                )
            except ValueError:
                passed = False
            results.append(
                {"check": field + "_independent_readback", "passed": passed, "level": "control"}
            )
    return results


async def run_case(case: dict[str, Any]) -> dict[str, Any]:
    # API import creates a default app too; keep it offline despite inherited shell settings.
    with patch.object(Settings, "from_environment", return_value=Settings()):
        from aclara.api.app import create_app

    country, locale = PROFILES[case["profile"]]
    repository, aliases = synthetic_ledger(country, case.get("fixture_aliases"))
    settings = Settings(
        demo_username="exploration",
        demo_password=secrets.token_urlsafe(24),
        demo_customer_id="exploration-customer",
        demo_locale=locale,
        llm_provider="mock",
        agent_system="P",
        ops_backend="memory",
    )
    active_nlu: dict[str, Any] = {}

    def mock(_system: str, _user: str, schema: type[BaseModel]) -> str:
        if schema is not ExtractedNlu:
            raise RuntimeError(
                "Unexpected model schema; exploration uses approved phrasing templates"
            )
        return json.dumps(active_nlu, ensure_ascii=False)

    llm = StructuredClient(
        {route: ModelSpec("mock", "authored-exploration-v1") for route in ("nlu", "phrase")},
        {},
        mock_response=mock,
        budget_usd=0.0,
        daily_budget_usd=0.0,
        risk_second_opinion_enabled=False,
    )
    store = Store()
    app = create_app(settings, repository, Runtime(system="P", country=country), llm, store)
    transcript: list[dict[str, Any]] = []
    proposal_hash: str | None = None
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://exploration.local",
        ) as client:
            headers = await sign_in(client, settings)
            token = headers["Authorization"].removeprefix("Bearer ")
            started = await client.post("/chat/sessions", headers=headers)
            if started.status_code != 200:
                raise RuntimeError("Synthetic conversation start failed")
            conversation_id = started.json()["conversation_id"]
            path = f"/chat/sessions/{conversation_id}"
            for index, authored in enumerate(case["turns"], 1):
                turn = expand(authored, aliases)
                active_nlu = turn.get("mock_nlu", {})
                if turn["kind"] == "message":
                    ExtractedNlu.model_validate(active_nlu)
                before = state(app, token, conversation_id)
                calls_before = len(llm.records)
                payload = (
                    {"message": turn["message"]}
                    if turn["kind"] == "message"
                    else {
                        "proposal_hash": proposal_hash or "0" * 64,
                        "confirmed": turn["confirmed"],
                    }
                )
                result = await client.post(
                    path + ("/messages" if turn["kind"] == "message" else "/confirm"),
                    headers=headers,
                    json=payload,
                )
                try:
                    response = result.json()
                except ValueError:
                    response = {"detail": "non_json_response"}
                after = state(app, token, conversation_id)
                assertions = checks(
                    turn["expect"],
                    result.status_code,
                    response,
                    before,
                    after,
                    transcript,
                    aliases,
                    turn["kind"],
                    turn.get("expectation_level", "contract"),
                )
                if result.status_code == 200:
                    assertions.extend(await readback(client, headers, response))
                    if response.get("proposal"):
                        proposal_hash = response["proposal"]["proposal_hash"]
                    for value in aliases.values():
                        value.pop("ordinal", None)
                        for ordinal, candidate in enumerate(response.get("candidates") or [], 1):
                            if candidate["handle"] == value["handle"]:
                                value["ordinal"] = ordinal
                records = llm.records[calls_before:]
                assertions.append(
                    {
                        "check": "zero_spend_mock",
                        "level": "control",
                        "passed": llm.spent_usd == 0 and all(r.provider == "mock" for r in records),
                    }
                )
                transcript.append(
                    {
                        "turn": index,
                        "kind": turn["kind"],
                        "message": turn.get("message"),
                        "http_status": result.status_code,
                        "response": response,
                        "state_before": public_state(before),
                        "state_after": public_state(after),
                        "mock_calls": len(records),
                        "checks": assertions,
                        "passed": all(item["passed"] for item in assertions),
                    }
                )
        return {
            "id": case["id"],
            "locale": case["locale"],
            "category": case["category"],
            "coherent": all(turn["passed"] for turn in transcript),
            "controls_passed": all(
                check["passed"]
                for turn in transcript
                for check in turn["checks"]
                if check["level"] == "control"
            ),
            "workflow_passed": all(
                check["passed"]
                for turn in transcript
                for check in turn["checks"]
                if check["level"] == "workflow"
            ),
            "ux_passed": all(
                check["passed"]
                for turn in transcript
                for check in turn["checks"]
                if check["level"] == "ux"
            ),
            "first_divergence_turn": next(
                (turn["turn"] for turn in transcript if not turn["passed"]), None
            ),
            "turns": transcript,
            "expectations": case["expectations"],
            "charged_usd": llm.spent_usd,
        }
    finally:
        store.close()


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)
    if json.loads(path.read_text(encoding="utf-8")) != value:
        raise RuntimeError("Exploration artifact readback failed")


async def run(cases_path: Path, output: Path) -> dict[str, Any]:
    source = cases_path.read_bytes()
    document = json.loads(source)
    if document.get("schema_version") != 1 or document.get("synthetic") is not True:
        raise ValueError("Only authored synthetic schema v1 conversations are allowed")
    cases = document["cases"]
    if len({case["id"] for case in cases}) != len(cases) or any(
        len(case["turns"]) < 2 for case in cases
    ):
        raise ValueError("Each conversation needs a unique ID and multiple turns")
    allowed = {
        "http_status",
        "response_types",
        "language",
        "transaction_alias",
        "case_count",
        "verified",
        "no_write",
        "no_handoff",
        "same_case_as_turn",
        "same_handoff_as_turn",
        "same_transaction_as_turn",
    }
    if any(set(turn["expect"]) - allowed for case in cases for turn in case["turns"]):
        raise ValueError("An authored expectation has no implemented check")
    if any(
        turn.get("expectation_level", "contract") not in {"contract", "workflow", "ux"}
        for case in cases
        for turn in case["turns"]
    ):
        raise ValueError("Unknown expectation level")
    results = [await run_case(case) for case in cases]
    turns = [turn for case in results for turn in case["turns"]]
    assertions = [check for turn in turns for check in turn["checks"]]
    aggregate = {
        "mode": "mock",
        "conversations": len(results),
        "coherent_conversations": sum(case["coherent"] for case in results),
        "turns": len(turns),
        "passing_turns": sum(turn["passed"] for turn in turns),
        "checks": len(assertions),
        "passing_checks": sum(check["passed"] for check in assertions),
        "workflow_failed_turns": sum(
            any(not check["passed"] and check["level"] == "workflow" for check in turn["checks"])
            for turn in turns
        ),
        "ux_failed_turns": sum(
            any(not check["passed"] and check["level"] == "ux" for check in turn["checks"])
            for turn in turns
        ),
        "charged_usd": sum(case["charged_usd"] for case in results),
        "controls": {
            name: {
                "checks": sum(check["check"] == name for check in assertions),
                "failures": sum(
                    check["check"] == name and not check["passed"] for check in assertions
                ),
            }
            for name in (
                "no_financial_write",
                "zero_spend_mock",
                "case_independent_readback",
                "handoff_independent_readback",
            )
        },
        "by_locale": {
            locale: {
                "conversations": sum(case["locale"] == locale for case in results),
                "coherent": sum(case["locale"] == locale and case["coherent"] for case in results),
            }
            for locale in sorted({case["locale"] for case in results})
        },
        "failed_conversations": [case["id"] for case in results if not case["coherent"]],
    }
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    save(
        output / "run.json",
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "suite_sha256": hashlib.sha256(source).hexdigest(),
            "source_sha256": {
                relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                for relative in (
                    "docs/evaluation/judge_exploration.py",
                    "src/aclara/api/app.py",
                    "src/aclara/agent/nlu/structured.py",
                    "src/aclara/ops/store.py",
                )
            },
            "limitations": "Authored typed NLU and approved templates; no live model or browser measurement.",
            "aggregate": aggregate,
            "conversations": results,
        },
    )
    save(output / "aggregate.json", aggregate)
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/judge-exploration/mock")
    parser.add_argument("--mode", choices=("mock", "live"), default="mock")
    args = parser.parse_args()
    if args.mode == "live":
        parser.error(
            "Live exploration is blocked pending lead judge-access confirmation and a server-side durable scope capped at USD 0.30; this runner makes no network/provider calls."
        )
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        parser.error("Generated outputs must stay under ignored repository artifacts/")
    if (output / "run.json").exists():
        parser.error("Preserve previous results: choose a fresh --output directory")
    logging.getLogger("aclara.turn").setLevel(logging.WARNING)
    aggregate = asyncio.run(run(args.cases.resolve(), output))
    sys.stdout.write(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n")
    return int(aggregate["coherent_conversations"] != aggregate["conversations"])


if __name__ == "__main__":
    raise SystemExit(main())
