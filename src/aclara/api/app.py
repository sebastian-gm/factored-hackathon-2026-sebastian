"""FastAPI app for the local Layer 1 demo."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from aclara.agent.ai import AgentAI
from aclara.agent.contracts import ResponsePlan
from aclara.agent.nlu import (
    Intent,
    classify,
    extract_amount,
    is_cancellation,
    is_confirmation,
    normalize_text,
    selected_candidate,
)
from aclara.agent.runtime import InjectedFailure, Runtime
from aclara.bank.repository import Transaction, TransactionRepository
from aclara.handoff.packet import create_packet
from aclara.llm.client import StructuredClient
from aclara.policy.engine import PolicyDecision, evaluate
from aclara.settings import Settings


@dataclass(frozen=True, slots=True)
class Principal:
    session_id: str
    customer_id: str
    username: str
    otp_at: datetime
    expires_at: datetime


@dataclass(slots=True)
class OtpChallenge:
    preauth_token: str
    code: str
    expires_at: datetime
    attempts: int = 0


@dataclass(slots=True)
class ActionProposal:
    action_hash: str
    transaction_handle: str
    transaction: Transaction
    policy: PolicyDecision
    expires_at: datetime
    language: str


@dataclass(slots=True)
class Conversation:
    session_id: str
    language: str = "es"
    degraded: bool = False
    candidates: list[tuple[str, Transaction]] = field(default_factory=list)
    intent: Intent | None = None
    proposal: ActionProposal | None = None
    rounds: int = 0


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginBody(StrictModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class OtpBody(StrictModel):
    challenge_id: str = Field(min_length=1, max_length=80)
    code: str = Field(pattern=r"^\d{6}$")


class MessageBody(StrictModel):
    message: str = Field(min_length=1, max_length=1000)


class ConfirmBody(StrictModel):
    proposal_hash: str = Field(min_length=64, max_length=64)
    confirmed: bool


def _digest_proposal(session_id: str, handle: str, decision: PolicyDecision) -> str:
    content = json.dumps(
        {
            "action": "create_dispute",
            "session_id": session_id,
            "transaction_handle": handle,
            "policy_rules": decision.rule_ids,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _masked_transaction(handle: str, row: Transaction) -> dict[str, Any]:
    return {
        "handle": handle,
        "transaction_date": row.transaction_date.isoformat(),
        "transaction_type": row.transaction_type,
        "amount": row.amount,
        "currency": row.currency,
        "merchant": row.merchant_name,
        "status": row.transaction_status,
    }


def _localized(language: str, spanish: str, portuguese: str) -> str:
    return spanish if language == "es" else portuguese


def _explanation(language: str, row: Transaction, reason: str) -> str:
    amount = f"{row.amount:.2f} {row.currency}"
    if reason == "pending_authorization":
        return _localized(
            language,
            f"El cargo de {amount} en {row.merchant_name} está pendiente. Es una autorización; normalmente se confirma o desaparece dentro de 7 días. No hay una fecha de liquidación registrada.",
            f"A cobrança de {amount} em {row.merchant_name} está pendente. É uma autorização; normalmente é confirmada ou desaparece em até 7 dias. Não há uma data de liquidação registrada.",
        )
    if reason == "reversed":
        return _localized(
            language,
            f"El cargo de {amount} en {row.merchant_name} aparece como reversado. No hay una fecha de reverso registrada.",
            f"A cobrança de {amount} em {row.merchant_name} aparece como estornada. Não há uma data de estorno registrada.",
        )
    if reason == "declined":
        return _localized(
            language,
            f"El cargo de {amount} en {row.merchant_name} figura como rechazado; el registro indica que no se completó.",
            f"A cobrança de {amount} em {row.merchant_name} aparece como recusada; o registro indica que não foi concluída.",
        )
    return _localized(
        language,
        f"El registro muestra {amount} en {row.merchant_name}, con estado {row.transaction_status.lower()}.",
        f"O registro mostra {amount} em {row.merchant_name}, com status {row.transaction_status.lower()}.",
    )


def _handoff_reply(language: str) -> str:
    return _localized(
        language,
        "Voy a derivar tu solicitud a un agente. El paquete de atención ya está preparado.",
        "Vou encaminhar sua solicitação para uma pessoa. O pacote de atendimento está preparado.",
    )


def _read_db_ready() -> bool:
    try:
        with psycopg.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=int(os.getenv("PGPORT", "5432")),
            user=os.getenv("PGUSER", ""),
            password=os.getenv("PGPASSWORD", ""),
            dbname=os.getenv("PGDATABASE", ""),
            connect_timeout=2,
        ) as connection:
            connection.execute("SELECT 1")
        return True
    except (psycopg.Error, ValueError):
        return False


def create_app(
    settings: Settings | None = None,
    repository: TransactionRepository | None = None,
    runtime: Runtime | None = None,
    llm_client: StructuredClient | None = None,
) -> FastAPI:
    active_settings = settings or Settings.from_environment()
    ledger = repository or TransactionRepository()
    app = FastAPI(title="Aclara demo API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("WEB_ORIGIN", "http://localhost:3000")],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Preauth-Token"],
    )
    app.state.runtime = runtime or Runtime(system=active_settings.agent_system)
    ai = AgentAI(active_settings, app.state.runtime, llm_client)
    app.state.ai = ai
    app.state.settings = active_settings
    app.state.ledger = ledger
    app.state.challenges = {}
    app.state.sessions = {}
    app.state.conversations = {}
    app.state.cases = {}
    app.state.handoffs = {}

    def principal_from_token(token: str | None) -> Principal:
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        principal: Principal | None = app.state.sessions.get(token)
        now = datetime.now(UTC)
        if principal is None or principal.expires_at <= now:
            app.state.sessions.pop(token, None)
            raise HTTPException(status_code=401, detail="Session expired")
        return principal

    async def get_principal(authorization: str | None = Header(default=None)) -> Principal:
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        return principal_from_token(token)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "aclara-api",
            "llm_provider": active_settings.llm_provider,
        }

    @app.get("/readyz")
    async def readyz() -> dict[str, str]:
        if not _read_db_ready():
            raise HTTPException(status_code=503, detail="Database unavailable")
        return {"status": "ready", "database": "ok"}

    @app.post("/auth/login", status_code=status.HTTP_200_OK)
    async def login(body: LoginBody) -> dict[str, str]:
        if not active_settings.demo_username or not active_settings.demo_password:
            raise HTTPException(status_code=503, detail="Demo identity is not configured")
        valid = hmac.compare_digest(
            body.username, active_settings.demo_username
        ) and hmac.compare_digest(body.password, active_settings.demo_password)
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid login")
        challenge_id = secrets.token_urlsafe(18)
        preauth_token = secrets.token_urlsafe(24)
        app.state.challenges[challenge_id] = OtpChallenge(
            preauth_token=preauth_token,
            code=f"{secrets.randbelow(1_000_000):06d}",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        return {"challenge_id": challenge_id, "preauth_token": preauth_token}

    @app.get("/auth/challenges/{challenge_id}/sms")
    async def simulated_sms(
        challenge_id: str,
        x_preauth_token: str | None = Header(default=None),
    ) -> dict[str, str]:
        challenge: OtpChallenge | None = app.state.challenges.get(challenge_id)
        if (
            challenge is None
            or challenge.expires_at <= datetime.now(UTC)
            or not x_preauth_token
            or not hmac.compare_digest(challenge.preauth_token, x_preauth_token)
        ):
            raise HTTPException(status_code=404, detail="Challenge not found")
        return {"code": challenge.code, "channel": "simulated_sms"}

    @app.post("/auth/otp/verify")
    async def verify_otp(
        body: OtpBody, x_preauth_token: str | None = Header(default=None)
    ) -> dict[str, str]:
        challenge: OtpChallenge | None = app.state.challenges.get(body.challenge_id)
        now = datetime.now(UTC)
        if (
            challenge is None
            or challenge.expires_at <= now
            or challenge.attempts >= 5
            or not x_preauth_token
            or not hmac.compare_digest(challenge.preauth_token, x_preauth_token)
        ):
            raise HTTPException(status_code=401, detail="Challenge expired or invalid")
        challenge.attempts += 1
        if not hmac.compare_digest(body.code, challenge.code):
            raise HTTPException(status_code=401, detail="Invalid code")
        session_token = secrets.token_urlsafe(32)
        app.state.sessions[session_token] = Principal(
            session_id=secrets.token_urlsafe(18),
            customer_id=active_settings.demo_customer_id,
            username=active_settings.demo_username,
            otp_at=now,
            expires_at=now + timedelta(minutes=15),
        )
        del app.state.challenges[body.challenge_id]
        return {"access_token": session_token, "token_type": "bearer"}

    @app.get("/me")
    async def me(principal: Principal = Depends(get_principal)) -> dict[str, str]:
        return {"username": principal.username, "language": "es"}

    @app.get("/transactions")
    async def list_transactions(
        principal: Principal = Depends(get_principal),
    ) -> list[dict[str, Any]]:
        rows = ledger.for_customer(principal.customer_id, active_settings.bank_clock)
        return [_masked_transaction(handle, row) for handle, row in rows]

    @app.post("/chat/sessions")
    async def start_conversation(
        principal: Principal = Depends(get_principal),
    ) -> dict[str, str]:
        conversation_id = str(uuid4())
        app.state.conversations[conversation_id] = Conversation(session_id=principal.session_id)
        return {"conversation_id": conversation_id}

    @app.post("/chat/sessions/{conversation_id}/messages", response_model=ResponsePlan)
    async def send_message(
        conversation_id: str,
        body: MessageBody,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        try:
            app.state.runtime.checkpoint("MATCH")
            result = await process_message(conversation_id, body, principal)
        except InjectedFailure:
            result = safe_failure(principal, classify(body.message).language)
        app.state.runtime.record("response", response_type=result["response_type"])
        conversation = app.state.conversations.get(conversation_id)
        return ai.reply(
            result,
            conversation.language if conversation else "es",
            deterministic=bool(conversation and conversation.degraded),
        )

    def safe_failure(principal: Principal, language: str) -> dict[str, Any]:
        packet = create_packet(language, "ESC-04")
        app.state.handoffs[packet["handoff_id"]] = {
            **packet,
            "customer_id": principal.customer_id,
            "session_id": principal.session_id,
        }
        app.state.runtime.record("safe_failure")
        return {
            "response_type": "offer_human",
            "outcome": "handoff_created",
            "reply": _handoff_reply(language),
            "handoff": {k: v for k, v in packet.items() if k != "request_summary"},
        }

    async def process_message(
        conversation_id: str,
        body: MessageBody,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        conversation: Conversation | None = app.state.conversations.get(conversation_id)
        if conversation is None or conversation.session_id != principal.session_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        frame = classify(body.message)
        if (
            app.state.runtime.system == "P"
            and not conversation.candidates
            and not conversation.proposal
        ):
            nlu = ai.understand(body.message, active_settings.bank_clock)
            conversation.degraded = nlu.degraded
            if not nlu.degraded:
                frame = nlu.frame
                # Conservative deterministic routing takes precedence over extracted intent.
                guard = classify(body.message)
                if guard.intent in {Intent.HUMAN_REQUEST, Intent.FRAUD, Intent.FEE_DISPUTE}:
                    frame = guard
                elif nlu.clarification or frame.confidence < 0.6:
                    conversation.rounds += 1
                    conversation.language = (
                        "pt" if nlu.extracted.language == "pt" else conversation.language
                    )
                    if conversation.rounds >= 2:
                        return safe_failure(principal, conversation.language)
                    return {
                        "response_type": "clarify",
                        "outcome": "clarification",
                        "reply": _localized(
                            conversation.language,
                            "¿Puedes aclarar el idioma, monto, moneda o fecha?",
                            "Pode esclarecer o idioma, valor, moeda ou data?",
                        ),
                    }
        language = conversation.language if conversation.candidates else frame.language
        conversation.language = language

        if conversation.proposal is not None:
            if is_cancellation(body.message):
                conversation.proposal = None
                return {
                    "response_type": "cancelled",
                    "outcome": "cancelled",
                    "reply": _localized(
                        language,
                        "De acuerdo, no registraré la disputa.",
                        "Tudo bem, não vou registrar a disputa.",
                    ),
                }
            if is_confirmation(body.message):
                raise HTTPException(status_code=409, detail="Use the action confirmation control")

        if frame.intent in {Intent.HUMAN_REQUEST, Intent.FRAUD, Intent.FEE_DISPUTE}:
            reason_code = {
                Intent.HUMAN_REQUEST: "ESC-01",
                Intent.FRAUD: "FRD-01",
                Intent.FEE_DISPUTE: "DSP-03",
            }[frame.intent]
            packet = create_packet(language, reason_code)
            app.state.handoffs[packet["handoff_id"]] = {
                **packet,
                "customer_id": principal.customer_id,
                "session_id": principal.session_id,
            }
            return {
                "response_type": "offer_human",
                "outcome": "handoff_created",
                "reply": _handoff_reply(language),
                "handoff": {
                    key: value for key, value in packet.items() if key != "request_summary"
                },
            }

        if frame.intent == Intent.OUT_OF_SCOPE and not conversation.candidates:
            return {
                "response_type": "abstain",
                "outcome": "abstained_out_of_scope",
                "reply": _localized(
                    language,
                    "Puedo ayudar con cargos no reconocidos. Si necesitas otro tema, puedo derivarte a una persona.",
                    "Posso ajudar com cobranças não reconhecidas. Para outro assunto, posso encaminhar você para uma pessoa.",
                ),
            }

        if conversation.candidates:
            choice = selected_candidate(body.message, len(conversation.candidates))
            if choice is None:
                conversation.rounds += 1
                if conversation.rounds >= 2:
                    conversation.candidates = []
                    packet = create_packet(language, "ESC-04")
                    app.state.handoffs[packet["handoff_id"]] = {
                        **packet,
                        "customer_id": principal.customer_id,
                        "session_id": principal.session_id,
                    }
                    return {
                        "response_type": "offer_human",
                        "outcome": "handoff_created",
                        "reply": _handoff_reply(language),
                        "handoff": {
                            key: value for key, value in packet.items() if key != "request_summary"
                        },
                    }
                return {
                    "response_type": "choose_transaction",
                    "outcome": "choose_transaction",
                    "reply": _localized(
                        language,
                        "Responde el primero, segundo o tercero para elegir el cargo.",
                        "Responda primeiro, segundo ou terceiro para escolher a cobrança.",
                    ),
                    "candidates": [
                        _masked_transaction(handle, row)
                        for handle, row in conversation.candidates[:3]
                    ],
                }
            handle, row = conversation.candidates[choice]
            conversation.candidates = []
            return _decide_for_transaction(
                app,
                conversation,
                principal,
                language,
                frame.intent if frame.intent == Intent.DISPUTE_CHARGE else conversation.intent,
                handle,
                row,
                active_settings,
            )

        rows = ledger.for_customer(principal.customer_id, active_settings.bank_clock)
        normalized = normalize_text(body.message)
        merchant_matches = [
            (handle, row) for handle, row in rows if normalize_text(row.merchant_name) in normalized
        ]
        amount = extract_amount(body.message)
        amount_matches = [
            (handle, row)
            for handle, row in rows
            if amount is not None and abs(row.amount - amount) < 0.011
        ]
        if merchant_matches and amount_matches:
            candidates = [item for item in merchant_matches if item in amount_matches]
        elif merchant_matches:
            candidates = merchant_matches
        elif amount_matches:
            candidates = amount_matches
        else:
            candidates = rows

        if not candidates:
            conversation.rounds += 1
            if conversation.rounds >= 2:
                packet = create_packet(language, "ESC-04")
                app.state.handoffs[packet["handoff_id"]] = {
                    **packet,
                    "customer_id": principal.customer_id,
                    "session_id": principal.session_id,
                }
                return {
                    "response_type": "offer_human",
                    "outcome": "handoff_created",
                    "reply": _handoff_reply(language),
                    "handoff": {
                        key: value for key, value in packet.items() if key != "request_summary"
                    },
                }
            return {
                "response_type": "clarify",
                "outcome": "clarification",
                "reply": _localized(
                    language,
                    "No encontré un cargo con esos datos. ¿Recuerdas el comercio o el monto?",
                    "Não encontrei uma cobrança com esses dados. Você lembra o estabelecimento ou o valor?",
                ),
            }

        if len(candidates) > 1:
            conversation.candidates = candidates[:3]
            conversation.intent = frame.intent
            conversation.rounds += 1
            return {
                "response_type": "choose_transaction",
                "outcome": "choose_transaction",
                "reply": _localized(
                    language,
                    "Encontré varios cargos posibles. Elige uno para revisar.",
                    "Encontrei algumas cobranças possíveis. Escolha uma para revisar.",
                ),
                "candidates": [_masked_transaction(handle, row) for handle, row in candidates[:3]],
            }

        handle, row = candidates[0]
        return _decide_for_transaction(
            app,
            conversation,
            principal,
            language,
            frame.intent,
            handle,
            row,
            active_settings,
        )

    @app.post("/chat/sessions/{conversation_id}/confirm", response_model=ResponsePlan)
    async def confirm_action(
        conversation_id: str,
        body: ConfirmBody,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        try:
            result = await process_confirmation(conversation_id, body, principal)
        except InjectedFailure:
            conversation = app.state.conversations.get(conversation_id)
            language = (
                conversation.proposal.language if conversation and conversation.proposal else "es"
            )
            if conversation:
                conversation.proposal = None
            result = safe_failure(principal, language)
        app.state.runtime.record("response", response_type=result["response_type"])
        conversation = app.state.conversations.get(conversation_id)
        return ai.reply(
            result,
            conversation.language if conversation else "es",
            deterministic=bool(conversation and conversation.degraded),
        )

    async def process_confirmation(
        conversation_id: str,
        body: ConfirmBody,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        conversation: Conversation | None = app.state.conversations.get(conversation_id)
        if conversation is None or conversation.session_id != principal.session_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        proposal = conversation.proposal
        if proposal is None:
            raise HTTPException(status_code=409, detail="No pending action")
        if not body.confirmed:
            conversation.proposal = None
            return {
                "response_type": "cancelled",
                "outcome": "cancelled",
                "reply": _localized(proposal.language, "Disputa cancelada.", "Disputa cancelada."),
            }
        expected_hash = _digest_proposal(
            principal.session_id, proposal.transaction_handle, proposal.policy
        )
        now = datetime.now(UTC)
        if (
            not hmac.compare_digest(expected_hash, proposal.action_hash)
            or not hmac.compare_digest(body.proposal_hash, proposal.action_hash)
            or proposal.expires_at <= now
        ):
            conversation.proposal = None
            raise HTTPException(status_code=409, detail="Action proposal expired or changed")
        if now - principal.otp_at > timedelta(minutes=10):
            conversation.proposal = None
            raise HTTPException(status_code=401, detail="Step-up verification required")
        decision = evaluate(proposal.transaction, active_settings.bank_clock, is_dispute=True)
        if decision.decision != "eligible":
            conversation.proposal = None
            raise HTTPException(status_code=409, detail="Policy no longer permits this action")

        case_id = f"DSP-{secrets.token_hex(4).upper()}"
        record = {
            "case_id": case_id,
            "customer_id": principal.customer_id,
            "transaction_id": proposal.transaction.record_id,
            "transaction_handle": proposal.transaction_handle,
            "status": "received",
            "policy_rules": list(decision.rule_ids),
            "created_at": now.isoformat(),
        }
        app.state.runtime.checkpoint("create_dispute")
        app.state.cases[case_id] = record
        app.state.runtime.record(
            "create_dispute", handle=proposal.transaction_handle, confirmed=True, step_up=True
        )
        app.state.runtime.checkpoint("read_back")
        read_back = app.state.cases.get(case_id)
        conversation.proposal = None
        if read_back is None or read_back["customer_id"] != principal.customer_id:
            raise HTTPException(status_code=503, detail="Read-back verification failed")
        app.state.runtime.record("verify_readback", handle=proposal.transaction_handle)
        return {
            "response_type": "report_case",
            "outcome": "dispute_filed",
            "reply": _localized(
                proposal.language,
                f"Tu disputa {case_id} fue registrada y verificada.",
                f"Sua disputa {case_id} foi registrada e verificada.",
            ),
            "case": {
                key: value
                for key, value in read_back.items()
                if key not in {"customer_id", "transaction_id"}
            },
            "verified": True,
        }

    @app.get("/disputes/{case_id}")
    async def read_dispute(
        case_id: str,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        record: dict[str, Any] | None = app.state.cases.get(case_id)
        if record is None or record["customer_id"] != principal.customer_id:
            raise HTTPException(status_code=404, detail="Dispute not found")
        return {
            key: value
            for key, value in record.items()
            if key not in {"customer_id", "transaction_id"}
        }

    @app.get("/handoffs/{handoff_id}")
    async def read_handoff(
        handoff_id: str,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        packet: dict[str, Any] | None = app.state.handoffs.get(handoff_id)
        if packet is None or packet["customer_id"] != principal.customer_id:
            raise HTTPException(status_code=404, detail="Handoff not found")
        return {
            key: value for key, value in packet.items() if key not in {"customer_id", "session_id"}
        }

    return app


def _decide_for_transaction(
    app: FastAPI,
    conversation: Conversation,
    principal: Principal,
    language: str,
    intent: Intent | None,
    handle: str,
    row: Transaction,
    settings: Settings,
) -> dict[str, Any]:
    is_dispute = intent == Intent.DISPUTE_CHARGE
    decision = evaluate(row, settings.bank_clock, is_dispute=is_dispute)
    if decision.decision == "handoff":
        packet = create_packet(language, decision.rule_ids[0])
        packet["verified_facts"] = [_masked_transaction(handle, row)]
        app.state.handoffs[packet["handoff_id"]] = {
            **packet,
            "customer_id": principal.customer_id,
            "session_id": principal.session_id,
        }
        return {
            "response_type": "offer_human",
            "outcome": "handoff_created",
            "reply": _handoff_reply(language),
            "handoff": {key: value for key, value in packet.items() if key != "request_summary"},
            "policy_rules": list(decision.rule_ids),
        }
    if decision.decision == "eligible":
        action_hash = _digest_proposal(principal.session_id, handle, decision)
        expires_at = datetime.now(UTC) + timedelta(minutes=5)
        conversation.proposal = ActionProposal(
            action_hash=action_hash,
            transaction_handle=handle,
            transaction=row,
            policy=decision,
            expires_at=expires_at,
            language=language,
        )
        amount = f"{row.amount:.2f} {row.currency}"
        reply = _localized(
            language,
            f"¿Confirmas que registre una disputa por {amount} en {row.merchant_name}? Esta acción abrirá un caso; no garantiza un reembolso.",
            f"Você confirma o registro de uma disputa de {amount} em {row.merchant_name}? Isso abrirá um caso; não garante reembolso.",
        )
        return {
            "response_type": "confirm_action",
            "outcome": "dispute_proposed",
            "reply": reply,
            "transaction": _masked_transaction(handle, row),
            "proposal": {
                "action": "create_dispute",
                "proposal_hash": action_hash,
                "expires_at": expires_at.isoformat(),
                "policy_rules": list(decision.rule_ids),
            },
        }
    return {
        "response_type": "explain_status",
        "outcome": "explained",
        "reply": _explanation(language, row, decision.reason),
        "transaction": _masked_transaction(handle, row),
        "policy_rules": list(decision.rule_ids),
    }


app = create_app()
