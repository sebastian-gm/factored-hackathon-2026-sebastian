"""Staff APIs confined to the authenticated demo workspace; no RLS widening."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException

from aclara.agent.contracts import HandoffView
from aclara.api import staff_queue
from aclara.api.staff_contracts import (
    DeskPacket,
    OpsView,
    PersonaView,
    ResetConfirm,
    ResetProposal,
    ResetReceipt,
    StaffAction,
    TraceEvent,
    TraceView,
    WorkspaceMetrics,
)
from aclara.api.trace_metadata import judgments_projection
from aclara.bank.serving import persona_views
from aclara.handoff.context import customer_context, refresh_summary
from aclara.ops.store import Scope
from aclara.policy.rules import catalog
from aclara.policy.temporal import quality_issue

OPERATIONS = ("cases", "card_states", "handoffs", "conversations", "turns", "execution_records")


def complete_packet(
    app: FastAPI,
    result: dict[str, Any],
    principal: Any,
    conversation_id: str | None = None,
    message: str | None = None,
) -> None:
    if not result.get("handoff"):
        return
    key = result["handoff"]["handoff_id"]
    packet = app.state.handoffs[key]
    language = packet["route"]["language"]
    conversation = app.state.conversations.get(conversation_id) if conversation_id else None
    # Never borrow facts from the first/latest conversation in a multi-tab session.
    if conversation and conversation.selected_handle and not packet["verified_facts"]:
        from aclara.api.app import _masked_transaction

        row = dict(
            app.state.ledger.for_customer(principal.customer_id, app.state.settings.bank_clock)
        ).get(conversation.selected_handle)
        if row is not None:
            packet["verified_facts"] = [_masked_transaction(conversation.selected_handle, row)]
    # A proposal is not an action. Include a previous dispute only after reading
    # its persisted record, and only from this conversation's execution history.
    for record in app.state.executions.values() if conversation_id else ():
        response = record.get("response", {})
        case = response.get("case")
        if (
            record.get("conversation_id") == conversation_id
            and response.get("outcome") == "dispute_filed"
            and response.get("verified") is True
            and case
        ):
            persisted = app.state.cases.get(case["case_id"])
            if (
                persisted
                and persisted.get("customer_id") == principal.customer_id
                and persisted.get("transaction_handle") == case["transaction_handle"]
                and "create_dispute" not in packet["actions_taken"]
            ):
                packet["actions_taken"].append("create_dispute")
    preferred = conversation.language if conversation else language
    statements = packet.get("customer_statements", [])
    policy_details = {
        item["rule_id"]: item for item in packet.get("policy_evaluations", []) if "rule_id" in item
    }
    if "DQ-01" in packet["reason_codes"] and "DQ-01" not in policy_details:
        detail = "not_checked"
        if conversation and conversation.selected_handle:
            current = dict(
                app.state.ledger.for_customer(principal.customer_id, app.state.settings.bank_clock)
            ).get(conversation.selected_handle)
            if current is not None:
                detail = quality_issue(app.state.ledger.context(current)) or "not_checked"
        policy_details["DQ-01"] = {"detail": detail}
    if conversation_id and not statements:
        # Read only this conversation within the caller's store/RLS scope. The
        # current message has not been written to turns yet; append it explicitly.
        turns = [
            (app.state.executions.get(key, {}).get("created_at", ""), turn)
            for key, turn in app.state.turns.items()
            if turn.get("conversation_id") == conversation_id
        ]
        history = [turn for _, turn in sorted(turns, key=lambda item: item[0])]
        if message:
            history.append({"customer_text": message, "response": result})
        statements = customer_context(history)
    packet.update(
        {
            "conversation_id": conversation_id,
            "customer": {
                "handle": "customer_current",
                "display_name_masked": "Cliente demo",
                "preferred_language": preferred,
                "auth": {"amr": ["pwd", "otp"], "otp_at": principal.otp_at.isoformat()},
            },
            "customer_statements": statements,
            "policy_evaluations": [
                {
                    **policy_details.get(reason, {}),
                    "rule_id": reason,
                    "policy_version": catalog()[0],
                    "outcome": "escalate",
                }
                for reason in packet["reason_codes"]
            ],
            "risk_flags": ["fraud_review"] if "FRD-01" in packet["reason_codes"] else [],
            "sla_due_at": (
                datetime.fromisoformat(packet["created_at"]) + timedelta(days=15)
            ).isoformat(),
            "transcript_ref": f"/agent/conversations/{conversation_id}"
            if conversation_id
            else None,
            "trace_ref": f"/chat/sessions/{conversation_id}/trace" if conversation_id else None,
        }
    )
    refresh_summary(packet, conversation.intent if conversation else None)
    app.state.handoffs[key] = packet
    result["handoff"] = HandoffView.model_validate(
        {
            k: v
            for k, v in packet.items()
            if k not in {"customer_id", "session_id", "request_summary"}
        }
    ).model_dump(mode="json")


def verify_handoff_commit(
    app: FastAPI, result: dict[str, Any], principal: Any, conversation_id: str | None
) -> None:
    """Read the committed packet before recording or showing a completed handoff."""
    store = app.state.store
    scope = Scope(principal.customer_id, principal.run_id, principal.session_id)
    key = result["handoff"]["handoff_id"]
    with store.transaction(scope):
        packet = app.state.handoffs.get(key)
        if (
            not packet
            or packet.get("customer_id") != principal.customer_id
            or packet.get("session_id") != principal.session_id
        ):
            raise HTTPException(503, "Durable handoff read-back failed")
        view = HandoffView.model_validate(
            {
                k: v
                for k, v in packet.items()
                if k not in {"customer_id", "session_id", "request_summary"}
            }
        )
        expected = HandoffView.model_validate(result["handoff"])
        if view.model_copy(
            update={"actions_taken": [a for a in view.actions_taken if a != "create_handoff"]}
        ) != expected.model_copy(
            update={"actions_taken": [a for a in expected.actions_taken if a != "create_handoff"]}
        ):
            raise HTTPException(503, "Durable handoff read-back failed")
        if "create_handoff" not in packet["actions_taken"]:
            packet["actions_taken"].append("create_handoff")
        conversation = app.state.conversations.get(conversation_id) if conversation_id else None
        refresh_summary(packet, conversation.intent if conversation else None)
        app.state.handoffs[key] = packet
        app.state.executions[str(uuid4())] = {
            "conversation_id": conversation_id,
            "created_at": datetime.now(UTC).isoformat(),
            "events": [{"event": "verify_readback", "handle": key}],
            "outcome": "handoff_verified",
            "policy_version": catalog()[0],
        }
    with store.transaction(scope):
        committed = app.state.handoffs.get(key)
        if not committed or committed != packet:
            raise HTTPException(503, "Durable handoff read-back failed")
        result["handoff"] = HandoffView.model_validate(
            {
                k: v
                for k, v in committed.items()
                if k not in {"customer_id", "session_id", "request_summary"}
            }
        ).model_dump(mode="json")
        result["verified"] = True
    staff_queue.publish(app, principal, packet)


def install_staff(
    app: FastAPI, principal_dependency: Any, auth_principal_dependency: Any | None = None
) -> None:
    principal_default = Depends(principal_dependency)
    logout_default = Depends(auth_principal_dependency or principal_dependency)
    store = app.state.store
    settings = app.state.settings

    def scope(principal: Any) -> Scope:
        return Scope(principal.customer_id, principal.run_id, principal.session_id)

    def staff(principal: Any, ops: bool = False) -> None:
        if principal.role not in ({"ops"} if ops else {"agent", "ops"}):
            raise HTTPException(403, "Staff role required")

    def fresh(principal: Any) -> None:
        if principal.step_up_at is None or datetime.now(UTC) - principal.step_up_at > timedelta(
            minutes=10
        ):
            raise HTTPException(401, "Fresh step-up required")

    def desk(key: str) -> DeskPacket:
        packet = app.state.handoffs.get(key)
        if not packet:
            raise HTTPException(404, "Handoff not found")
        state = app.state.idempotency.get(
            "desk:" + key, {"status": "waiting", "claimed_by": None, "version": 1}
        )
        view = {k: v for k, v in packet.items() if k not in {"customer_id", "session_id"}}
        evidence = [
            {
                "id": f"{key}:fact:{i}",
                "record_ref": fact["handle"],
                "tool": "scoped_transaction_read",
                "verified_at": packet["created_at"],
                "dataset_version": app.state.dataset_version,
            }
            for i, fact in enumerate(packet["verified_facts"])
        ]
        actions = [
            {"action": action, "status": "verified", "evidence_ref": packet.get("trace_ref") or key}
            for action in packet["actions_taken"]
            if action in {"create_handoff", "create_dispute"}
        ] + (
            [
                {
                    "action": "freeze_card",
                    "status": "verified" if packet["freeze_outcome"] == "verified" else "failed",
                    "evidence_ref": packet.get("trace_ref") or key,
                }
            ]
            if packet.get("freeze_outcome") in {"verified", "unverified"}
            else []
        )
        return DeskPacket.model_validate(
            {
                **view,
                **state,
                "conversation_id": packet.get("conversation_id"),
                "customer_display": "Cliente demo",
                "sla_due_at": packet.get("sla_due_at")
                or (datetime.fromisoformat(packet["created_at"]) + timedelta(days=15)).isoformat(),
                "evidence": evidence,
                "actions": actions,
            }
        )

    @app.get("/personas", response_model=list[PersonaView])
    async def personas() -> list[dict[str, Any]]:
        public = {
            name: persona
            for name, persona in app.state.personas.items()
            if persona.role == "customer"
            and name != app.state.judge_username
            and not name.startswith("judge.")
        }
        return persona_views(public, app.state.demo_stories)

    @app.post("/auth/logout")
    async def logout(
        principal: Any = logout_default,
    ) -> dict[str, bool]:
        if principal.judge_reference is not None:
            return dict(app.state.judge_sessions.revoke(principal))
        with store.transaction(scope(principal)):
            store.delete("sessions", principal.capability_digest)
            store.audit({"action": "logout"})
        with store.transaction(scope(principal)):
            if store.get("sessions", principal.capability_digest) is not None:
                raise HTTPException(503, "Revocation readback failed")
        return {"signed_out": True, "verified": True}

    @app.get("/agent/handoffs", response_model=list[DeskPacket])
    async def queue(principal: Any = principal_default) -> list[DeskPacket]:
        staff(principal)
        realm = staff_queue.authorized_realm(app, principal)
        if realm is not None:
            return sorted(
                staff_queue.packets(app, principal, realm),
                key=lambda p: (p.priority != "high", p.sla_due_at, p.handoff_id),
            )
        with store.transaction(scope(principal)):
            packets = [desk(key) for key in app.state.handoffs]
        return sorted(packets, key=lambda p: (p.priority != "high", p.sla_due_at, p.handoff_id))

    @app.get("/agent/handoffs/{handoff_id}", response_model=DeskPacket)
    async def detail(handoff_id: str, principal: Any = principal_default) -> DeskPacket:
        staff(principal)
        realm = staff_queue.authorized_realm(app, principal)
        if realm is not None:
            packets = staff_queue.packets(app, principal, realm, handoff_id)
            if not packets:
                raise HTTPException(404, "Handoff not found")
            return packets[0]
        with store.transaction(scope(principal)):
            return desk(handoff_id)

    async def transition(key: str, body: StaffAction, principal: Any, resolve: bool) -> DeskPacket:
        staff(principal)
        realm = staff_queue.authorized_realm(app, principal)
        if realm is not None:
            if resolve:
                raise HTTPException(409, "Realm queue supports claim only")
            return staff_queue.claim(app, principal, realm, key, body)
        action = "resolve" if resolve else "claim"
        fingerprint = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
        cache_key = f"desk-action:{key}:{action}:{body.idempotency_key}"
        with store.transaction(scope(principal)):
            previous = app.state.idempotency.get(cache_key)
            if previous:
                if previous["fingerprint"] != fingerprint:
                    raise HTTPException(409, "Idempotency key changed")
                expected = DeskPacket.model_validate(previous["result"])
            else:
                current = desk(key)
                if body.expected_version != current.version or current.status == "resolved":
                    raise HTTPException(409, "Handoff version changed")
                if resolve and (
                    current.status != "claimed"
                    or current.claimed_by != "agent_current"
                    or not body.resolution
                ):
                    raise HTTPException(409, "Claim and resolution required")
                if not resolve and current.status != "waiting":
                    raise HTTPException(409, "Handoff already claimed")
                state = {
                    "status": "resolved" if resolve else "claimed",
                    "claimed_by": "agent_current",
                    "version": current.version + 1,
                }
                app.state.idempotency["desk:" + key] = state
                store.audit(
                    {
                        "action": action,
                        "handoff_id": key,
                        "resolution": body.resolution if resolve else None,
                    }
                )
                expected = desk(key)
                app.state.idempotency[cache_key] = {
                    "fingerprint": fingerprint,
                    "result": expected.model_dump(mode="json"),
                }
        with store.transaction(scope(principal)):
            actual = desk(key)
            if actual.version < expected.version:
                raise HTTPException(503, "Staff action readback failed")
        return expected

    @app.post("/agent/handoffs/{handoff_id}/claim", response_model=DeskPacket)
    async def claim(
        handoff_id: str, body: StaffAction, principal: Any = principal_default
    ) -> DeskPacket:
        return await transition(handoff_id, body, principal, False)

    @app.post("/handoffs/realm-invitations", response_model=staff_queue.RealmInvitation)
    async def invitation(principal: Any = principal_default) -> staff_queue.RealmInvitation:
        return staff_queue.invite(app, principal)

    @app.post("/agent/handoff-realm")
    async def join_realm(
        body: staff_queue.RealmJoin, principal: Any = principal_default
    ) -> dict[str, bool]:
        staff(principal)
        return staff_queue.join(app, principal, body)

    @app.post("/agent/handoffs/{handoff_id}/resolve", response_model=DeskPacket)
    async def resolve(
        handoff_id: str, body: StaffAction, principal: Any = principal_default
    ) -> DeskPacket:
        return await transition(handoff_id, body, principal, True)

    def trace(conversation_id: str) -> TraceView:
        if conversation_id not in app.state.conversations:
            raise HTTPException(404, "Conversation not found")
        events = []
        for key, record in app.state.executions.items():
            if record.get("conversation_id") != conversation_id:
                continue
            for index, event in enumerate(record.get("events", [])):
                name = event["event"]
                stages = {
                    "nlu": "Understand",
                    "recognition": "Understand",
                    "offer_dispute": "Decide",
                    "explain_status": "Act",
                    "match": "Decide",
                    "policy": "Decide",
                    "create_dispute": "Act",
                    "freeze_card": "Act",
                    "verify_readback": "Verify",
                    "create_handoff": "Escalate",
                    "safe_failure": "Escalate",
                    "llm_call": "Understand",
                }
                if name not in stages:
                    continue
                llm = (
                    {
                        "provider": event["provider"],
                        "model": event["model_id"],
                        "prompt_version": event["prompt_id"],
                        "input_tokens": event["input_tokens"],
                        "output_tokens": event["output_tokens"],
                        "cost_usd": event.get("cost_usd"),
                        "latency_ms": event["latency_ms"],
                        "route": event.get("route"),
                        "status": event.get("status"),
                        "attempt": event.get("attempt"),
                        "judgments": judgments_projection(event.get("judgments")),
                    }
                    if name == "llm_call"
                    else None
                )
                events.append(
                    TraceEvent.model_validate(
                        {
                            "id": f"{key}:{index}",
                            "stage": stages[name],
                            "state": name,
                            "tool": name
                            if name in {"create_dispute", "freeze_card", "verify_readback"}
                            else None,
                            "rules": event.get("rule_ids", []),
                            "verified": name == "verify_readback",
                            "llm": llm,
                        }
                    )
                )
        return TraceView(
            conversation_id=conversation_id, events=events, policy_version=catalog()[0]
        )

    @app.get("/chat/sessions/{conversation_id}/trace", response_model=TraceView)
    async def execution_trace(
        conversation_id: str, principal: Any = principal_default
    ) -> TraceView:
        staff(principal)
        with store.transaction(scope(principal)):
            return trace(conversation_id)

    @app.get("/agent/conversations/{conversation_id}", response_model=TraceView)
    async def transcript_reference(
        conversation_id: str, principal: Any = principal_default
    ) -> TraceView:
        # Resolves to the redacted execution trail, never raw transcript content.
        return await execution_trace(conversation_id, principal)

    def metrics() -> WorkspaceMetrics:
        records = list(app.state.executions.values())
        return WorkspaceMetrics(
            cases=len(app.state.cases),
            handoffs=len(app.state.handoffs),
            conversations=len(app.state.conversations),
            execution_records=len(records),
            observed_model_cost_usd=sum(
                e.get("cost_usd", 0) or 0
                for r in records
                for e in r.get("events", [])
                if e["event"] == "llm_call"
            ),
        )

    @app.get("/ops/metrics", response_model=WorkspaceMetrics)
    async def operational_metrics(principal: Any = principal_default) -> WorkspaceMetrics:
        staff(principal, True)
        with store.transaction(scope(principal)):
            return metrics()

    @app.get("/ops/snapshot", response_model=OpsView)
    async def snapshot(principal: Any = principal_default) -> OpsView:
        staff(principal, True)
        with store.transaction(scope(principal)):
            rows = app.state.ledger.for_customer(principal.customer_id, settings.bank_clock)
            return OpsView.model_validate(
                {
                    "dataset_version": app.state.dataset_version,
                    "bank_clock": settings.bank_clock,
                    "loaded_at": app.state.loaded_at,
                    "source_as_of": settings.bank_clock,
                    "source_kind": app.state.ledger.source_kind,
                    "quality": [
                        {
                            "name": "scoped_owned_120_day_rows",
                            "passed": all(r.customer_id == principal.customer_id for _, r in rows),
                            "checked": len(rows),
                        }
                    ],
                    "metrics": metrics(),
                    "conversation_ids": list(app.state.conversations),
                }
            )

    @app.post("/ops/reset/proposal", response_model=ResetProposal)
    async def reset_proposal(principal: Any = principal_default) -> ResetProposal:
        staff(principal, True)
        if principal.judge_reference is not None:
            raise HTTPException(403, "Judge reset disabled")
        fresh(principal)
        if not settings.allow_demo_reset:
            raise HTTPException(403, "Demo reset disabled")
        payload = {
            "nonce": secrets.token_hex(24),
            "sid": principal.session_id,
            "run_id": principal.run_id,
            "step_up_at": principal.step_up_at.isoformat(),
            "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
            "action": "reset_current_workspace",
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        with store.transaction(scope(principal)):
            app.state.idempotency["reset-proposal:" + digest] = payload
        return ResetProposal(
            proposal_hash=digest, expires_at=datetime.fromisoformat(payload["expires_at"])
        )

    @app.post("/ops/reset", response_model=ResetReceipt)
    async def reset(body: ResetConfirm, principal: Any = principal_default) -> ResetReceipt:
        staff(principal, True)
        if principal.judge_reference is not None:
            raise HTTPException(403, "Judge reset disabled")
        fresh(principal)
        if not settings.allow_demo_reset:
            raise HTTPException(403, "Demo reset disabled")
        with store.transaction(scope(principal)):
            previous = app.state.idempotency.get("reset-result:" + body.proposal_hash)
            if previous:
                return ResetReceipt.model_validate(previous)
            payload = app.state.idempotency.get("reset-proposal:" + body.proposal_hash)
            if (
                not payload
                or not hmac.compare_digest(
                    hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
                    body.proposal_hash,
                )
                or payload["sid"] != principal.session_id
                or payload["run_id"] != principal.run_id
                or payload["step_up_at"] != principal.step_up_at.isoformat()
                or datetime.fromisoformat(payload["expires_at"]) <= datetime.now(UTC)
            ):
                raise HTTPException(409, "Reset proposal expired or changed")
            if body.confirmed:
                # Bank maps are customer/realm-scoped since #111. Clearing only
                # legacy session tables leaves disputes/cards visible after login.
                for records in (app.state.cases, app.state.card_states):
                    for key in list(records):
                        del records[key]
                for table in (*OPERATIONS, "idempotency_keys"):
                    for key in store.keys(table):
                        store.delete(table, key)
                store.audit({"action": "workspace_reset", "audit_retained": True})
            remaining = (
                len(app.state.cases)
                + len(app.state.card_states)
                + sum(
                    len(store.keys(table))
                    for table in OPERATIONS
                    if table not in {"cases", "card_states"}
                )
            )
            result = ResetReceipt(
                receipt_id=body.proposal_hash,
                reset=body.confirmed,
                verified=True,
                remaining_operations=remaining,
            )
            app.state.idempotency["reset-result:" + body.proposal_hash] = result.model_dump(
                mode="json"
            )
        with store.transaction(scope(principal)):
            if body.confirmed and (
                app.state.cases
                or app.state.card_states
                or any(store.keys(table) for table in OPERATIONS)
            ):
                raise HTTPException(503, "Reset readback failed")
        return result

    @app.get("/ops/reset/{receipt_id}", response_model=ResetReceipt)
    async def reset_receipt(receipt_id: str, principal: Any = principal_default) -> ResetReceipt:
        staff(principal, True)
        with store.transaction(scope(principal)):
            receipt = app.state.idempotency.get("reset-result:" + receipt_id)
            if not receipt:
                raise HTTPException(404, "Reset receipt not found")
            return ResetReceipt.model_validate(receipt)
