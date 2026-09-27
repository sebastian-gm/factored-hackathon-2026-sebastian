"""Scoped policy workflows shared by chat, action endpoints and readbacks."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections.abc import Iterable
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from aclara.agent.contracts import InterfaceModel, ProductView, ResponsePlan
from aclara.api.staff import complete_packet
from aclara.bank.repository import Transaction
from aclara.handoff.packet import create_packet
from aclara.ops.store import Scope
from aclara.policy.engine import PolicyContext
from aclara.policy.rules import rule
from aclara.policy.rules.guards import injection


def public_case(record: dict[str, Any]) -> dict[str, Any]:
    return {
        k: record[k]
        for k in (
            "case_id",
            "transaction_handle",
            "status",
            "policy_rules",
            "created_at",
            "review_flag",
        )
        if k in record
    }


def policy_context(app: FastAPI, principal: Any, row: Transaction) -> PolicyContext:
    clock = app.state.settings.bank_clock
    cases = list(app.state.cases.values())
    recent = sum(
        clock - timedelta(days=7)
        <= datetime.fromisoformat(c.get("bank_created_at", c["created_at"]))
        <= clock
        for c in cases
    )
    existing = next((c["case_id"] for c in cases if c.get("transaction_id") == row.record_id), None)
    return cast(
        PolicyContext, app.state.ledger.context(row, cases_7_days=recent, existing_case_id=existing)
    )


def security_event(app: FastAPI, category: str) -> None:
    app.state.runtime.record("log_security_event", category=category)
    app.state.store.audit({"action": "security_event", "category": category})


def safe_merchant(value: str) -> str:
    return "—" if not value or injection(value) else value


def make_handoff(
    app: FastAPI,
    principal: Any,
    language: str,
    reason: str | Iterable[str],
    *,
    freeze_outcome: str | None = None,
    facts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    packet = create_packet(language, reason, app.state.agent_directory)
    packet["verified_facts"] = facts or []
    if freeze_outcome:
        packet["freeze_outcome"] = freeze_outcome
        packet["actions_taken"] = [f"freeze_card:{freeze_outcome}"]
    app.state.handoffs[packet["handoff_id"]] = {
        **packet,
        "customer_id": principal.customer_id,
        "session_id": principal.session_id,
    }
    app.state.runtime.record(
        "create_handoff",
        reason=packet["primary_reason"],
        reasons=packet["reason_codes"],
        queue=packet["route"]["queue"],
    )
    response = {
        "response_type": "offer_human",
        "outcome": "handoff_created",
        "reply": (
            "Voy a derivar tu solicitud para revisión humana."
            if language == "es"
            else "Vou encaminhar sua solicitação para análise humana."
        ),
        "handoff": {k: v for k, v in packet.items() if k != "request_summary"},
        "policy_rules": packet["reason_codes"],
    }
    complete_packet(app, response, principal)
    return response


def fraud_handoff(
    app: FastAPI,
    principal: Any,
    language: str,
    row: Transaction | None = None,
    *,
    reasons: Iterable[str] = ("FRD-01",),
) -> dict[str, Any]:
    products = app.state.ledger.products_for_customer(principal.customer_id)
    offers = [
        {"handle": handle, "product_type": p.product_type, "status": p.status}
        for handle, p in products
        if p.product_type in {"Credit Card", "Debit Card"}
        and p.status not in {"Closed", "Blocked"}
        and (row is None or p.product_id == row.product_id)
    ]
    response = make_handoff(
        app, principal, language, reasons, freeze_outcome="offered" if offers else "not_applicable"
    )
    if offers:
        response["freeze_offer"] = offers
        response["reply"] += (
            " Puedes bloquear tu tarjeta con un nuevo OTP y confirmación."
            if language == "es"
            else " Você pode bloquear seu cartão após informar um novo código de verificação e confirmar a ação."
        )
    return response


class StepUpBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    challenge_id: str = Field(max_length=160)
    code: str = Field(pattern=r"^\d{6}$")


class FreezeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed: bool


class FreezeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str = Field(pattern=r"^(es|pt)$", default="es")


class CardStateView(InterfaceModel):
    handle: str
    status: str
    verified: bool


class FreezeProposalView(InterfaceModel):
    response_type: Literal["confirm_action"] = "confirm_action"
    action: Literal["freeze_card"] = "freeze_card"
    handle: str
    proposal_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expires_at: datetime
    reply: str


class FreezeResultView(ResponsePlan):
    card: CardStateView | None = None


def freeze_hash(proposal: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {k: v for k, v in proposal.items() if k != "proposal_hash"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def install_workflows(app: FastAPI, principal_dependency: Any) -> None:
    from aclara.api.app import OtpChallenge

    principal_default = Depends(principal_dependency)
    store = app.state.store

    def scope(principal: Any) -> Scope:
        return Scope(principal.customer_id, principal.run_id, principal.session_id)

    def product_for(handle: str, principal: Any) -> Any:
        product = dict(app.state.ledger.products_for_customer(principal.customer_id)).get(handle)
        if product is None:
            raise HTTPException(404, "Product not found")
        return product

    @app.get("/accounts", response_model=list[ProductView])
    async def accounts(principal: Any = principal_default) -> list[dict[str, Any]]:
        return [
            {"handle": handle, "product_type": p.product_type, "status": p.status}
            for handle, p in app.state.ledger.products_for_customer(principal.customer_id)
        ]

    @app.post("/auth/step-up")
    async def step_up(principal: Any = principal_default) -> dict[str, str]:
        challenge_id = f"{principal.run_id}.{principal.session_id}.{secrets.token_urlsafe(18)}"
        preauth = secrets.token_urlsafe(24)
        app.state.challenges[challenge_id] = OtpChallenge(
            preauth_token=hashlib.sha256(preauth.encode()).hexdigest(),
            code=f"{secrets.randbelow(1000000):06d}",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            step_up=True,
        )
        return {"challenge_id": challenge_id, "preauth_token": preauth}

    @app.post("/auth/step-up/verify")
    async def verify_step_up(
        body: StepUpBody,
        principal: Any = principal_default,
        x_preauth_token: str | None = Header(default=None),
    ) -> dict[str, str]:
        error = None
        with store.transaction(scope(principal)):
            # Reject a different session before asking the authentication map to change scope.
            if body.challenge_id.split(".")[:2] != [principal.run_id, principal.session_id]:
                raise HTTPException(404, "Challenge not found")
            challenge = app.state.challenges.get(body.challenge_id)
            now = datetime.now(UTC)
            if (
                not challenge
                or not challenge.step_up
                or challenge.expires_at <= now
                or challenge.attempts >= 5
                or not x_preauth_token
                or not hmac.compare_digest(
                    challenge.preauth_token, hashlib.sha256(x_preauth_token.encode()).hexdigest()
                )
            ):
                raise HTTPException(401, "Challenge expired or invalid")
            challenge.attempts += 1
            app.state.challenges[body.challenge_id] = challenge
            if not hmac.compare_digest(challenge.code, body.code):
                error = HTTPException(401, "Invalid code")
            else:
                renewed = replace(principal, otp_at=now, step_up_at=now)
                payload = asdict(renewed)
                payload.pop("capability_digest", None)
                payload = {
                    k: v.isoformat() if isinstance(v, datetime) else v for k, v in payload.items()
                }
                store.put("sessions", principal.capability_digest, payload)
                del app.state.challenges[body.challenge_id]
                store.audit({"action": "step_up_verified"})
        if error:
            raise error
        return {"status": "verified"}

    @app.get("/cards/{handle}", response_model=CardStateView)
    async def card(handle: str, principal: Any = principal_default) -> dict[str, Any]:
        product = product_for(handle, principal)
        if product.product_type not in {"Credit Card", "Debit Card"}:
            raise HTTPException(404, "Card not found")
        with store.transaction(scope(principal)):
            state = app.state.card_states.get(product.product_id)
            return {
                "handle": handle,
                "status": state["status"] if state else product.status,
                "verified": True,
            }

    @app.post("/cards/{handle}/freeze/proposal", response_model=FreezeProposalView | ResponsePlan)
    async def proposal(
        handle: str, body: FreezeRequest, principal: Any = principal_default
    ) -> dict[str, Any]:
        product = product_for(handle, principal)
        now = datetime.now(UTC)
        with store.transaction(scope(principal)):
            if product.product_type not in {"Credit Card", "Debit Card"}:
                return make_handoff(
                    app, principal, body.language, "FRD-01", freeze_outcome="not_applicable"
                )
            if product.status in {"Closed", "Blocked"}:
                return make_handoff(
                    app, principal, body.language, "FRD-01", freeze_outcome="unavailable"
                )
            if principal.step_up_at is None or now - principal.step_up_at > timedelta(
                minutes=int(rule("AUTH-02").parameters["otp_minutes"])
            ):
                raise HTTPException(401, "Step-up verification required")
            value = {
                "action": "freeze_card",
                "product_id": product.product_id,
                "handle": handle,
                "sid": principal.session_id,
                "run_id": principal.run_id,
                "expires_at": (now + timedelta(minutes=5)).isoformat(),
                "nonce": secrets.token_urlsafe(24),
                "language": body.language,
                "step_up_at": principal.step_up_at.isoformat(),
            }
            value["proposal_hash"] = freeze_hash(value)
            app.state.idempotency["freeze-proposal:" + value["proposal_hash"]] = value
            return {
                "response_type": "confirm_action",
                "action": "freeze_card",
                "handle": handle,
                "proposal_hash": value["proposal_hash"],
                "expires_at": value["expires_at"],
                "reply": "¿Confirmas el bloqueo de esta tarjeta?"
                if body.language == "es"
                else "Confirma o bloqueio deste cartão?",
            }

    @app.post("/cards/{handle}/freeze", response_model=FreezeResultView)
    async def freeze(
        handle: str, body: FreezeBody, principal: Any = principal_default
    ) -> dict[str, Any]:
        from aclara.agent.runtime import InjectedFailure

        product = product_for(handle, principal)
        with store.transaction(scope(principal)):
            key = "freeze-proposal:" + body.proposal_hash
            proposal = app.state.idempotency.get(key)
            if (
                not proposal
                or product.product_type not in {"Credit Card", "Debit Card"}
                or product.status in {"Closed", "Blocked"}
                or proposal["product_id"] != product.product_id
                or proposal["sid"] != principal.session_id
                or proposal["run_id"] != principal.run_id
                or datetime.fromisoformat(proposal["expires_at"]) <= datetime.now(UTC)
                or not hmac.compare_digest(freeze_hash(proposal), body.proposal_hash)
            ):
                raise HTTPException(409, "Action proposal expired or changed")
            if (
                principal.step_up_at is None
                or datetime.now(UTC) - principal.step_up_at
                > timedelta(minutes=int(rule("AUTH-02").parameters["otp_minutes"]))
                or principal.step_up_at.isoformat() != proposal["step_up_at"]
            ):
                raise HTTPException(401, "Step-up verification required")
            previous = app.state.idempotency.get("freeze-result:" + body.proposal_hash)
            if previous:
                result = previous
            else:
                outcome = "declined"
                if body.confirmed:
                    try:
                        app.state.runtime.checkpoint("freeze_card")
                        app.state.card_states[product.product_id] = {
                            "status": "Frozen",
                            "updated_at": datetime.now(UTC).isoformat(),
                        }
                        app.state.runtime.record(
                            "freeze_card", handle=handle, confirmed=True, step_up=True
                        )
                        app.state.runtime.checkpoint("read_back")
                        assert app.state.card_states[product.product_id]["status"] == "Frozen"
                        app.state.runtime.record("verify_readback", handle=handle)
                        outcome = "verified"
                    except InjectedFailure:
                        outcome = "unverified"
                        app.state.runtime.record("safe_failure")
                result = make_handoff(
                    app, principal, proposal["language"], "FRD-01", freeze_outcome=outcome
                )
                if outcome == "verified":
                    result["card"] = {"handle": handle, "status": "Frozen", "verified": True}
                    result["reply"] = (
                        "El bloqueo de la tarjeta fue verificado. Derivé el caso a Fraudes."
                        if proposal["language"] == "es"
                        else "O bloqueio do cartão foi verificado. Encaminhei o caso a Fraudes."
                    )
                result["verified"] = True
                app.state.executions["freeze:" + body.proposal_hash] = {
                    "conversation_id": result["handoff"].get("conversation_id"),
                    "created_at": datetime.now(UTC).isoformat(),
                    "events": [
                        {
                            "event": "freeze_card",
                            "handle": handle,
                            "confirmed": body.confirmed,
                            "step_up": True,
                        },
                        {"event": "verify_readback", "handle": handle},
                    ]
                    if outcome == "verified"
                    else [
                        {"event": "safe_failure" if outcome == "unverified" else "freeze_declined"}
                    ],
                    "outcome": outcome,
                }
                app.state.idempotency["freeze-result:" + body.proposal_hash] = result
                store.audit({"action": "freeze_result", "outcome": outcome})
        # A separate transaction verifies committed state before success leaves the API.
        with store.transaction(scope(principal)):
            if (
                result.get("card")
                and (app.state.card_states.get(product.product_id) or {}).get("status") != "Frozen"
            ):
                raise HTTPException(503, "Durable freeze readback failed")
            if not app.state.handoffs.get(result["handoff"]["handoff_id"]):
                raise HTTPException(503, "Durable handoff readback failed")
        return cast(dict[str, Any], result)
