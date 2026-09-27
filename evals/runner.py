"""Execute project-generated baseline scenarios through the FastAPI ASGI surface."""

from __future__ import annotations

import argparse
import asyncio
import logging
import secrets
from pathlib import Path
from typing import Any

import yaml
from httpx import ASGITransport, AsyncClient

from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.bank.repository import TransactionRepository
from aclara.evals.schema import ScenarioSuite
from aclara.llm.client import StructuredClient
from aclara.settings import Settings

LOGGER = logging.getLogger("aclara.evals")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "evals" / "dev_scenarios.yaml"


async def _new_authenticated_client(
    settings: Settings | None = None,
    repository: TransactionRepository | None = None,
    runtime: Runtime | None = None,
    *,
    llm_client: StructuredClient | None = None,
) -> tuple[Any, AsyncClient, str, str]:
    username = "dev.persona"
    password = secrets.token_urlsafe(32)
    app = create_app(
        settings
        or Settings(
            demo_username=username,
            demo_password=password,
            llm_provider="mock",
        ),
        repository,
        runtime,
        llm_client=llm_client,
    )
    username = app.state.settings.demo_username
    password = app.state.settings.demo_password
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
    login = await client.post("/auth/login", json={"username": username, "password": password})
    if login.status_code != 200:
        await client.aclose()
        raise RuntimeError("Demo login failed in local harness")
    challenge = login.json()
    sms = await client.get(
        f"/auth/challenges/{challenge['challenge_id']}/sms",
        headers={"X-Preauth-Token": challenge["preauth_token"]},
    )
    if sms.status_code != 200:
        await client.aclose()
        raise RuntimeError("Simulated SMS panel failed in local harness")
    verified = await client.post(
        "/auth/otp/verify",
        headers={"X-Preauth-Token": challenge["preauth_token"]},
        json={"challenge_id": challenge["challenge_id"], "code": sms.json()["code"]},
    )
    if verified.status_code != 200:
        await client.aclose()
        raise RuntimeError("OTP verification failed in local harness")
    token = verified.json()["access_token"]
    conversation = await client.post(
        "/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    if conversation.status_code != 200:
        await client.aclose()
        raise RuntimeError("Conversation creation failed in local harness")
    return app, client, token, conversation.json()["conversation_id"]


async def run_scenario(scenario: dict[str, Any]) -> tuple[bool, bool]:
    _, client, token, conversation_id = await _new_authenticated_client()
    headers = {"Authorization": f"Bearer {token}"}
    last_result: dict[str, Any] = {}
    readback_verified = False
    try:
        for turn in scenario["turns"]:
            if "confirm" in turn:
                proposal_hash = last_result.get("proposal", {}).get("proposal_hash")
                if not proposal_hash:
                    return False, False
                response = await client.post(
                    f"/chat/sessions/{conversation_id}/confirm",
                    headers=headers,
                    json={"proposal_hash": proposal_hash, "confirmed": bool(turn["confirm"])},
                )
            else:
                response = await client.post(
                    f"/chat/sessions/{conversation_id}/messages",
                    headers=headers,
                    json={"message": turn["message"]},
                )
            if response.status_code != 200:
                return False, False
            last_result = response.json()
        passed = last_result.get("outcome") == scenario["expected"]
        if passed and last_result.get("outcome") == "dispute_filed":
            case_id = last_result.get("case", {}).get("case_id")
            readback = await client.get(f"/disputes/{case_id}", headers=headers)
            readback_verified = (
                readback.status_code == 200
                and readback.json().get("status") == "received"
                and last_result.get("verified") is True
            )
            passed = passed and readback_verified
        if passed and last_result.get("outcome") == "handoff_created":
            handoff_id = last_result.get("handoff", {}).get("handoff_id")
            readback = await client.get(f"/handoffs/{handoff_id}", headers=headers)
            readback_verified = readback.status_code == 200
            passed = passed and readback_verified
        return passed, readback_verified
    finally:
        await client.aclose()


async def verify_scope_and_confirmation_guards() -> bool:
    app, client, token, conversation_id = await _new_authenticated_client()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        transactions = (await client.get("/transactions", headers=headers)).json()
        other_scope = await client.get(
            "/transactions", headers=headers, params={"customer_id": "another"}
        )
        scoped = (
            len(transactions) == 6
            and all("customer_id" not in row and "product_id" not in row for row in transactions)
            and len(other_scope.json()) == 6
        )
        proposal_response = await client.post(
            f"/chat/sessions/{conversation_id}/messages",
            headers=headers,
            json={"message": "No hice el cargo de Mercado Verde"},
        )
        if proposal_response.status_code != 200:
            return False
        proposal_hash = (proposal_response.json().get("proposal") or {}).get("proposal_hash", "")
        tampered = await client.post(
            f"/chat/sessions/{conversation_id}/confirm",
            headers=headers,
            json={"proposal_hash": "0" * 64, "confirmed": True},
        )
        return (
            scoped and bool(proposal_hash) and tampered.status_code == 409 and not app.state.cases
        )
    finally:
        await client.aclose()


async def async_main(args: argparse.Namespace) -> int:
    payload = yaml.safe_load(args.scenarios.read_text(encoding="utf-8"))
    if payload.get("version") == 2:
        import json

        import jsonschema

        from evals.metrics import aggregate
        from evals.reactive import execute, write_results

        schema = json.loads((ROOT / "contracts/interfaces/scenario-suite.schema.json").read_text())
        jsonschema.validate(payload, schema, format_checker=jsonschema.FormatChecker())
        ids = [s["id"] for s in payload["scenarios"]]
        if len(ids) != len(set(ids)):
            raise ValueError("Scenario IDs must be unique")
        cases = [
            await execute(s, args.system, repeat, payload.get("bank_clock"))
            for repeat in range(args.repeats)
            for s in payload["scenarios"]
        ]
        assert len({c["run_id"] for c in cases}) == len(cases)
        prices = yaml.safe_load((ROOT / "config/pricing.yaml").read_text())
        report = aggregate(
            cases,
            {
                "workload": payload["description"],
                "system": args.system,
                "model": args.model,
                "prompt_versions": args.prompt_versions,
                "tag": args.tag,
                "cost_assumptions": "Mock calls cost USD 0; infrastructure excluded",
                "price_table_date": str(prices.get("as_of", "2026-09-26")),
                "monthly_infrastructure_estimate_usd": 34.63,
                "policy_version": yaml.safe_load((ROOT / "config/policy.yaml").read_text())[
                    "version"
                ],
                "matcher_version": sorted(
                    {
                        e["matcher_version"]
                        for c in cases
                        for e in c["events"]
                        if e["event"] == "match"
                    }
                )
                or ["rules"],
                "dataset_version": payload.get("dataset_version", "authored-fixtures"),
            },
        )
        write_results(args.output, cases, report)
        LOGGER.info(
            "%s v2: cases=%d passed=%d; aggregates: %s",
            args.system,
            len(cases),
            report["passed"],
            args.output / "results.json",
        )
        return 0 if report["passed"] == len(cases) else 1
    suite = ScenarioSuite.model_validate(payload)
    scenarios = [scenario.model_dump(mode="python") for scenario in suite.scenarios]
    passed = 0
    readbacks = 0
    failed_ids: list[str] = []
    for scenario in scenarios:
        result, verified = await run_scenario(scenario)
        passed += int(result)
        readbacks += int(verified)
        if not result:
            failed_ids.append(str(scenario["id"]))
    safety_ok = await verify_scope_and_confirmation_guards()
    LOGGER.info(
        "%s dev harness: scenarios=%d passed=%d failed=%d readbacks=%d safety_guards=%s",
        args.system,
        len(scenarios),
        passed,
        len(scenarios) - passed,
        readbacks,
        "passed" if safety_ok else "failed",
    )
    if failed_ids:
        LOGGER.error("Failed scenario IDs: %s", ", ".join(failed_ids))
    return 0 if passed == len(scenarios) and safety_ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", choices=("B1", "P"), default="B1")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--model", default="mock")
    parser.add_argument("--prompt-versions", default="nlu@v1,phrase@v1")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--budget-usd", type=float, default=0)
    parser.add_argument("--tag", default="working-tree")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/evaluation")
    args = parser.parse_args()
    if args.model != "mock" or args.budget_usd != 0:
        parser.error(
            "This local workload runs mock only; real-model evaluation requires separate owner-approved setup"
        )
    if args.repeats < 1:
        parser.error("repeats must be positive")
    if not args.output.resolve().is_relative_to((ROOT / "artifacts").resolve()):
        parser.error("Evaluation records must stay in ignored artifacts/")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
