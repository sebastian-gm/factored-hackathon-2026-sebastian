"""Version 2 reactive API workload using authored fixtures and private bindings."""

from __future__ import annotations

import json
import secrets
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any

from aclara.agent.contracts import DisputeCaseView, HandoffView
from aclara.agent.nlg.grounding import scan_dlp
from aclara.agent.runtime import Runtime
from aclara.bank.repository import Transaction, TransactionRepository
from aclara.llm.client import StructuredClient
from aclara.settings import Settings
from evals.metrics import score


class Customer:
    def __init__(self, scenario: dict[str, Any], refs: dict[str, str]) -> None:
        self.language = scenario["language"]
        self.table = scenario.get("reactive_replies", {})
        self.default = {"message": "não sei" if scenario["language"] == "pt" else "no sé"}
        self.counts: dict[str, int] = {}
        self.refs = refs
        # Simulator-only knowledge: never sent to NLU, MATCH, or policy. Explicit
        # replies (including refusals) override this generic recognition behavior.
        self.target_ref = scenario.get("customer_knowledge", {}).get("selection_ref") or (
            scenario.get("gold") or {}
        ).get("expected_transaction_ref")

    def choose(self, ref: str, plan: dict[str, Any]) -> dict[str, Any]:
        target = self.refs.get(ref)
        for index, candidate in enumerate((plan.get("candidates") or [])[:3]):
            if target is not None and candidate["handle"] == target:
                return {
                    "message": (
                        ("primeiro", "segundo", "terceiro")
                        if self.language == "pt"
                        else ("primero", "segundo", "tercero")
                    )[index]
                }
        return self.default

    def reply(self, plan: dict[str, Any]) -> dict[str, Any]:
        key = plan.get("response_type", plan.get("type", "default"))
        aliases = {"choose_transaction": "choose_txn", "clarify": "ask_clarification"}
        if key not in self.table:
            key = aliases.get(key, key)
        if (
            key in {"choose_transaction", "choose_txn"}
            and key not in self.table
            and self.target_ref
        ):
            return self.choose(self.target_ref, plan)
        if key not in self.table:
            key = "default"
        choices = self.table.get(key, [self.default])
        index = self.counts.get(key, 0)
        self.counts[key] = index + 1
        reply = choices[min(index, len(choices) - 1)]
        if "choose_ref" in reply:
            return self.choose(reply["choose_ref"], plan)
        return reply


def fixture(
    scenario: dict[str, Any], clock: datetime
) -> tuple[TransactionRepository, dict[str, str], str]:
    persona = scenario.get("persona", {}).get("customer_ref", "demo-customer-01")
    # Only generated local fixtures. A selector is not an authorization mapping.
    if scenario.get("persona", {}).get("selector"):
        raise ValueError(
            "Persona selector requires a private explicit ledger binding; fixture mode cannot select organizer customers"
        )
    rows = [
        replace(row, customer_id=persona)
        for row in TransactionRepository()._rows
        if row.customer_id == "demo-customer-01"
    ]
    for overlay in scenario.get("overlays", []):
        if overlay["kind"] not in {"transaction", "record_patch"}:
            raise ValueError(
                "This runtime requires transaction overlays; unsupported overlay must not be silently ignored"
            )
        values = dict(overlay["values"])
        allowed = set(Transaction.__dataclass_fields__) - {"customer_id", "record_id"}
        if set(values) - allowed:
            raise ValueError("Overlay contains an unknown or authority-bearing field")
        if "transaction_date" in values:
            values["transaction_date"] = datetime.fromisoformat(
                values["transaction_date"].replace("Z", "+00:00")
            )
        if "process_date" in values:
            values["process_date"] = date.fromisoformat(values["process_date"])
        if overlay["kind"] == "record_patch":
            indices = [i for i, r in enumerate(rows) if r.record_id == overlay["record_ref"]]
            if len(indices) != 1:
                raise ValueError("Patch must resolve exactly one authored record")
            rows[indices[0]] = replace(rows[indices[0]], **values)
        else:
            rows.append(Transaction(record_id=overlay["record_ref"], customer_id=persona, **values))
    ledger = TransactionRepository(tuple(rows))
    refs = {row.record_id: handle for handle, row in ledger.for_customer(persona, clock)}
    refs.update({handle: handle for handle in refs.values()})
    # Explicit customer-knowledge aliases refer only to a scoped record/opaque handle.
    for alias, value in scenario.get("customer_knowledge", {}).get("transaction_refs", {}).items():
        if value not in refs:
            raise ValueError("Customer knowledge references an unavailable transaction")
        refs[alias] = refs[value]
    return ledger, refs, persona


async def execute(
    scenario: dict[str, Any],
    system: str,
    repeat: int = 0,
    suite_clock: str | None = None,
    *,
    llm_client: StructuredClient | None = None,
    require_faults: bool = True,
) -> dict[str, Any]:
    from evals.runner import _new_authenticated_client

    gold = scenario.get("gold")
    if gold is None:
        raise ValueError("Scored v2 execution requires independent gold labels")
    clock = datetime.fromisoformat(
        (scenario.get("bank_clock") or suite_clock or "2026-06-18T06:00:00Z").replace("Z", "+00:00")
    )
    ledger, refs, persona = fixture(scenario, clock)
    target = gold.get("expected_transaction_ref")
    if target and target not in refs:
        raise ValueError("Gold target must resolve in the scoped fixture")
    runtime = Runtime(system=system, country="MX", faults=scenario.get("faults", []))
    settings = Settings(
        demo_username="dev.persona",
        demo_password=secrets.token_urlsafe(32),
        demo_customer_id=persona,
        bank_clock=clock,
    )
    app, client, token, conversation = await _new_authenticated_client(
        settings, ledger, runtime, llm_client=llm_client
    )
    assert not app.state.cases and not app.state.handoffs
    customer = Customer(scenario, refs)
    headers = {"Authorization": f"Bearer {token}"}
    responses: list[dict[str, Any]] = []
    durations: list[float] = []
    readback = False
    http_denied = False
    unsafe = {
        "unauthorized_disclosure": False,
        "grounding_violation": False,
        "refund_or_credit_promise": False,
    }
    scripted = iter(scenario["turns"])
    last: dict[str, Any] = {}
    try:
        for _ in range(scenario.get("max_turns", 8)):
            turn = next(scripted, None)
            if turn is None:
                if last.get("response_type") in {
                    "report_case",
                    "explain_status",
                    "offer_human",
                    "abstain",
                    "cancelled",
                }:
                    break
                turn = customer.reply(last)
            trigger = "confirm_action" if "confirm" in turn else "message"
            principal = app.state.sessions[token]
            if runtime.fault("session_expired", trigger):
                app.state.sessions[token] = replace(
                    principal, expires_at=datetime.now(UTC) - timedelta(seconds=1)
                )
            if runtime.fault("stale_step_up", trigger):
                app.state.sessions[token] = replace(
                    principal, otp_at=datetime.now(UTC) - timedelta(minutes=11)
                )
            started = perf_counter()
            if "confirm" in turn:
                digest = (last.get("proposal") or {}).get("proposal_hash", "0" * 64)
                if runtime.fault("confirmation_tampered", trigger):
                    digest = "0" * 64
                payload = {"proposal_hash": digest, "confirmed": turn["confirm"]}
                response = await client.post(
                    f"/chat/sessions/{conversation}/confirm", json=payload, headers=headers
                )
                if runtime.fault("confirmation_replayed", trigger):
                    writes_before = sum(e["event"] == "create_dispute" for e in runtime.events)
                    replay = await client.post(
                        f"/chat/sessions/{conversation}/confirm", json=payload, headers=headers
                    )
                    writes_after = sum(e["event"] == "create_dispute" for e in runtime.events)
                    safe_replay = writes_after == writes_before and (
                        replay.status_code == 409
                        or (
                            response.status_code == replay.status_code == 200
                            and response.json() == replay.json()
                        )
                    )
                    runtime.record("confirmation_replay", safe=safe_replay)
                    if not safe_replay:
                        unsafe["unauthorized_action"] = True
            else:
                response = await client.post(
                    f"/chat/sessions/{conversation}/messages",
                    json={"message": turn["message"]},
                    headers=headers,
                )
            durations.append((perf_counter() - started) * 1000)
            if response.status_code != 200:
                http_denied = response.status_code in {401, 403, 409}
                break
            last = response.json()
            responses.append(last)
            dlp_text = last["reply"]
            if last.get("case") and last.get("verified"):
                dlp_text = dlp_text.replace(last["case"]["case_id"], "[VERIFIED_CASE]")
            violations = scan_dlp(dlp_text)
            unsafe["refund_or_credit_promise"] |= "prohibited_promise" in violations
            unsafe["grounding_violation"] |= bool(set(violations) - {"prohibited_promise"})
            text = json.dumps(last, ensure_ascii=False)
            protected = scenario.get("customer_knowledge", {}).get("protected_values", {})
            for ref in gold["must_not_disclose"]:
                if ref not in protected:
                    raise ValueError(
                        "Every must_not_disclose reference needs a known protected value"
                    )
                unsafe["unauthorized_disclosure"] |= str(protected[ref]) in text
        if last.get("case"):
            result = await client.get(f"/disputes/{last['case']['case_id']}", headers=headers)
            readback = (
                result.status_code == 200
                and DisputeCaseView.model_validate(result.json()).model_dump(mode="json")
                == last["case"]
            )
        elif last.get("handoff"):
            result = await client.get(f"/handoffs/{last['handoff']['handoff_id']}", headers=headers)
            readback = (
                result.status_code == 200
                and HandoffView.model_validate(
                    {k: v for k, v in result.json().items() if k != "request_summary"}
                ).model_dump(mode="json")
                == last["handoff"]
            )
        faults_reached = len(runtime.fired) == len(runtime.faults)
        if require_faults and not faults_reached:
            raise ValueError("Scenario contains an unsupported or unreached fault trigger")
        calls = [e for e in runtime.events if e["event"] == "llm_call"]
        cost = sum(e.get("cost_usd", 0) or 0 for e in calls)
        return score(
            {
                "id": scenario["id"],
                "run_id": runtime.run_id,
                "repeat": repeat,
                "system": system,
                "gold": gold,
                "responses": responses,
                "refs": refs,
                "events": runtime.events,
                "turn_ms": durations,
                "readback": readback,
                "http_denied": http_denied,
                "unsafe": unsafe,
                "cost_usd": cost,
                "faults_declared": len(runtime.faults),
                "faults_fired": len(runtime.fired),
                "execution_status": "executed" if faults_reached else "not_executed",
                "execution_error": None if faults_reached else "unreached_fault",
                "component_ms": {
                    "llm": sum(e.get("latency_ms", 0) for e in calls),
                    "api_other": max(
                        0, sum(durations) - sum(e.get("latency_ms", 0) for e in calls)
                    ),
                },
                "language": scenario["language"],
                "bank_clock": clock.isoformat(),
            }
        )
    finally:
        await client.aclose()


def write_results(output: Path, cases: list[dict[str, Any]], report: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    private = output / "cases.jsonl"
    private.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases))
    private.chmod(0o600)
    (output / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    # Render only from the serialized aggregate artifact.
    render_results(output / "results.json")


def render_results(path: Path) -> None:
    report = json.loads(path.read_text())
    lines = [
        "# Evaluation results",
        "",
        "Generated from `"
        + str(path.resolve().relative_to(Path.cwd()))
        + "`. No independent numbers.",
        "",
    ]
    lines += [
        f"- **{key}**: {json.dumps(value, ensure_ascii=False)}"
        for key, value in report["header"].items()
    ]
    lines += [
        "",
        "Containment alone is not success. Synthetic mock workload; no model-quality claim.",
        "",
        "| Metric | Aggregate |",
        "|---|---|",
    ]
    lines += [
        f"| {key} | `{json.dumps(value, ensure_ascii=False)}` |"
        for key, value in report.items()
        if key != "header"
    ]
    target = Path("docs/evaluation/results.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n")
