"""Full v2 adapter. All mutations happen in a fresh in-memory application per case."""

from __future__ import annotations

import secrets
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Any

from httpx import Response

from aclara.agent.contracts import DisputeCaseView, HandoffView
from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.runtime import Runtime
from aclara.llm.client import StructuredClient
from aclara.settings import Settings
from evals.bindings import BoundFixture
from evals.metrics import score
from evals.observations import disclosures, validate_gold
from evals.reactive import Customer
from evals.runner import _new_authenticated_client


def step_up_required(response: Response) -> bool:
    """Only the API's exact stale-step-up error permits the renewal transition."""
    if response.status_code != 401:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    return isinstance(payload, dict) and payload.get("detail") == "Step-up verification required"


async def execute_bound(
    scenario: dict[str, Any],
    fixture: BoundFixture,
    system: str,
    repeat: int = 0,
    *,
    llm_client: StructuredClient | None = None,
) -> dict[str, Any]:
    validate_gold(scenario["gold"], fixture.refs, fixture.protected)
    runtime = Runtime(system=system, country=fixture.country, faults=scenario.get("faults", []))
    settings = Settings(
        demo_username="eval.persona",
        demo_password=secrets.token_urlsafe(32),
        demo_customer_id=fixture.customer_id,
        bank_clock=fixture.clock,
        llm_provider="openai_compat" if llm_client is not None else "mock",
    )
    app, client, token, conversation = await _new_authenticated_client(
        settings, fixture.ledger, runtime, llm_client=llm_client
    )
    scope = fixture.seed(app, token)
    app.state.sessions[token] = replace(
        app.state.sessions[token], otp_at=datetime.now(UTC) - fixture.step_up_age
    )
    headers = {"Authorization": f"Bearer {token}"}
    visible = await client.get("/transactions", headers=headers)
    if visible.status_code != 200:
        raise ValueError("Cannot verify scoped fixture projection")
    trusted_facts = {r["handle"]: r for r in visible.json()}
    customer = Customer(scenario, fixture.refs.values)
    responses: list[dict[str, Any]] = []
    durations: list[float] = []
    readbacks: set[str] = set()
    action_targets: dict[str, set[str]] = {}
    observed_handoff = None
    last: dict[str, Any] = {}
    last_message = ""
    denial, freeze_handle = False, None
    freeze_handoff_id = None
    renewed_step_up = False
    not_executed = None
    error = None
    terminal = {
        "report_case",
        "report_status",
        "explain_status",
        "offer_human",
        "abstain",
        "cancelled",
        "refuse",
    }
    prefix = iter(scenario["turns"])
    started_case = perf_counter()

    async def step_up() -> bool:
        challenge = await client.post("/auth/step-up", headers=headers)
        if challenge.status_code != 200:
            return False
        c = challenge.json()
        preauth = {"X-Preauth-Token": c["preauth_token"]}
        sms = await client.get(f"/auth/challenges/{c['challenge_id']}/sms", headers=preauth)
        if sms.status_code != 200:
            return False
        result = await client.post(
            "/auth/step-up/verify",
            headers={**headers, **preauth},
            json={"challenge_id": c["challenge_id"], "code": sms.json()["code"]},
        )
        return result.status_code == 200

    def auth_faults() -> None:
        principal = app.state.sessions.get(token)
        if principal is None:
            return
        if runtime.fault("session_expired", "confirm_action"):
            app.state.sessions[token] = replace(
                principal, expires_at=datetime.now(UTC) - timedelta(seconds=1)
            )
        if runtime.fault("stale_step_up", "confirm_action"):
            app.state.sessions[token] = replace(
                principal,
                otp_at=datetime.now(UTC) - timedelta(minutes=11),
                step_up_at=datetime.now(UTC) - timedelta(minutes=11),
            )

    try:
        for _ in range(scenario.get("max_turns", 12)):
            if last.get("session_ended"):
                break
            turn = next(prefix, None)
            if turn is None:
                if last.get("freeze_offer") and scenario["customer_knowledge"].get(
                    "provides_new_step_up", True
                ):
                    start = perf_counter()
                    if not await step_up():
                        error = "step_up_failed"
                        break
                    # Select the visible owned card; no gold or hidden fraud facts used.
                    freeze_handle = last["freeze_offer"][0]["handle"]
                    freeze_handoff_id = last["handoff"]["handoff_id"]
                    response = await client.post(
                        f"/cards/{freeze_handle}/freeze/proposal",
                        headers=headers,
                        json={
                            "language": scenario["customer_knowledge"]["preferred_language"],
                            "handoff_id": freeze_handoff_id,
                        },
                    )
                    durations.append((perf_counter() - start) * 1000)
                    if response.status_code != 200:
                        denial = response.status_code in {401, 403, 409}
                        error = "freeze_proposal_http_" + str(response.status_code)
                        break
                    last = response.json()
                    responses.append(last)
                elif last.get("response_type") in terminal:
                    break
                turn = customer.reply(last)
            start = perf_counter()
            if "confirm" in turn:
                proposal = last.get("proposal") or (
                    last if last.get("action") == "freeze_card" else {}
                )
                if not proposal.get("proposal_hash"):
                    error = "customer_confirmation_without_live_proposal"
                    break
                auth_faults()
                digest = proposal["proposal_hash"]
                if runtime.fault("confirmation_tampered", "confirm_action"):
                    digest = "0" * 64
                endpoint = (
                    f"/cards/{freeze_handle}/freeze"
                    if freeze_handle
                    else f"/chat/sessions/{conversation}/confirm"
                )
                payload = {"proposal_hash": digest, "confirmed": turn["confirm"]}
                response = await client.post(endpoint, headers=headers, json=payload)
                if (
                    step_up_required(response)
                    and not renewed_step_up
                    and scenario["customer_knowledge"].get("provides_new_step_up") is True
                ):
                    # Disputes may keep the still-valid proposal. Card proposals
                    # bind the OTP timestamp: renewing it requires a NEW proposal
                    # and another customer decision, never an automatic freeze.
                    renewed_step_up = True
                    if await step_up():
                        runtime.record("step_up_renewed")
                        if freeze_handle:
                            response = await client.post(
                                f"/cards/{freeze_handle}/freeze/proposal",
                                headers=headers,
                                json={
                                    "language": scenario["customer_knowledge"][
                                        "preferred_language"
                                    ],
                                    "handoff_id": freeze_handoff_id,
                                },
                            )
                            # Normal response processing below exposes this new
                            # proposal to Customer.reply on the next turn. It can
                            # confirm or change its mind using its authored replies.
                        else:
                            response = await client.post(endpoint, headers=headers, json=payload)
                if (
                    response.status_code == 200
                    and response.json().get("case")
                    and response.json().get("verified")
                ) and runtime.fault("confirmation_replayed", "verified_intake"):
                    replay = await client.post(endpoint, headers=headers, json=payload)
                    runtime.record("replay_checked", rejected=replay.status_code == 409)
            else:
                last_message = fixture.render(turn["message"])
                response = await client.post(
                    f"/chat/sessions/{conversation}/messages",
                    headers=headers,
                    json={"message": fixture.render(turn["message"])},
                )
            durations.append((perf_counter() - start) * 1000)
            if response.status_code != 200:
                denial = response.status_code in {401, 403, 409}
                runtime.record("http_error", status=response.status_code)
                break
            last = response.json()
            responses.append(last)
        # Independent committed reads, after action processing. Expired/revoked sessions do
        # not regain API access: trusted test scope verifies the already-persisted packet.
        start = perf_counter()
        for response in responses:
            if response.get("case"):
                record = response["case"]
                result = await client.get(f"/disputes/{record['case_id']}", headers=headers)
                if (
                    result.status_code == 200
                    and DisputeCaseView.model_validate(result.json()).model_dump(mode="json")
                    == record
                ):
                    ref = next(
                        (
                            r
                            for r, value in fixture.refs.values.items()
                            if value == record["case_id"]
                        ),
                        "created-case",
                    )
                    fixture.refs.add(ref, "case", record["case_id"])
                    readbacks.add(ref)
                    action_targets.setdefault("report_case", set()).add(ref)
            if response.get("card"):
                result = await client.get(f"/cards/{response['card']['handle']}", headers=headers)
                if result.status_code == 200 and result.json() == response["card"]:
                    fixture.refs.add("created-state", "card_state", response["card"]["handle"])
                    readbacks.update({"created-state", "product"})
            if response.get("handoff"):
                handoff_id = response["handoff"]["handoff_id"]
                result = await client.get(f"/handoffs/{handoff_id}", headers=headers)
                packet = result.json() if result.status_code == 200 else None
                if packet is None and response.get("session_ended"):
                    with app.state.store.transaction(scope):
                        stored = app.state.handoffs.get(handoff_id)
                        packet = (
                            {
                                k: v
                                for k, v in stored.items()
                                if k not in {"customer_id", "session_id"}
                            }
                            if stored
                            else None
                        )
                if packet and HandoffView.model_validate(
                    {k: v for k, v in packet.items() if k != "request_summary"}
                ).model_dump(mode="json") == HandoffView.model_validate(
                    response["handoff"]
                ).model_dump(mode="json"):
                    readbacks.add("handoff")
                    fixture.refs.add("handoff", "handoff", handoff_id)
                    observed_handoff = packet
        durations.append((perf_counter() - start) * 1000)
        with app.state.store.transaction(scope):
            stored_cases = list(app.state.cases.values())
            duplicate = any(
                n > 1 for n in Counter(c["transaction_id"] for c in stored_cases).values()
            )
            cross_scope = any(c.get("customer_id") != fixture.customer_id for c in stored_cases)
        if len(runtime.fired) != len(runtime.faults):
            not_executed = "unreached_fault_boundary"
        for event in runtime.events:
            if event.get("handle"):
                for ref, value in fixture.refs.values.items():
                    if value == event["handle"]:
                        action_targets.setdefault(event["event"], set()).add(ref)
        action_targets.setdefault("verify_readback", set()).update(readbacks)
        if observed_handoff:
            action_targets.setdefault("create_handoff", set()).add("handoff")
        for event in ("refuse_request", "end_session", "log_security_event"):
            if any(e["event"] == event for e in runtime.events):
                action_targets.setdefault(event, set()).add("persona")
        expected_reads = set()
        for r in responses:
            if r.get("case"):
                expected_reads.add(
                    "existing-case"
                    if any(c["case_id"] == r["case"]["case_id"] for c in fixture.cases)
                    else "created-case"
                )
            if r.get("card"):
                expected_reads.add("created-state")
            if r.get("handoff"):
                expected_reads.add("handoff")
        calls = [e for e in runtime.events if e["event"] == "llm_call"]
        result = score(
            {
                "id": scenario["id"],
                "run_id": runtime.run_id,
                "system": system,
                "repeat": repeat,
                "gold": scenario["gold"],
                "responses": responses,
                "trusted_facts": trusted_facts,
                "refs": fixture.refs.values,
                "events": runtime.events,
                "turn_ms": durations[:-1],
                "verification_ms": durations[-1],
                "case_ms": (perf_counter() - started_case) * 1000,
                "readback": bool(expected_reads) and expected_reads.issubset(readbacks),
                "verified_refs": sorted(readbacks),
                "action_targets": {k: sorted(v) for k, v in action_targets.items()},
                "observed_handoff": observed_handoff,
                "judge_input": {
                    "target_locale": scenario.get("dialect", scenario["language"]),
                    "customer_message": redact_for_model(last_message),
                    "customer_reply": redact_for_model(last.get("reply", "")),
                    "handoff_summary": redact_for_model(
                        (observed_handoff or {}).get("request_summary", {}).get("text", "")
                    ),
                },
                "http_denied": denial,
                "duplicate_case": duplicate,
                "cross_customer_action": cross_scope,
                "unsafe": {
                    "unauthorized_disclosure": disclosures(
                        responses + ([observed_handoff] if observed_handoff else []),
                        fixture.protected,
                        scenario["gold"]["must_not_disclose"],
                    )
                },
                "cost_usd": sum(e.get("cost_usd", 0) or 0 for e in calls),
                "component_ms": {
                    "model_calls_summed_including_parallel": sum(
                        e.get("latency_ms", 0) for e in calls
                    ),
                    "independent_readback": durations[-1],
                    "api_turns_total": sum(durations[:-1]),
                },
                "language": scenario["language"],
                "dialect": scenario.get("dialect", "unspecified"),
                "country": fixture.country,
                "segment": fixture.segment,
                "category": scenario["category"],
                "bank_clock": fixture.clock.isoformat(),
                "input_warnings": fixture.input_warnings,
                "execution_error": error,
                "execution_status": "not_executed" if not_executed else "executed",
                "not_executed_reason": not_executed,
            }
        )
        return result
    finally:
        await client.aclose()
        app.state.store.close()
