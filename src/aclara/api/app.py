"""FastAPI app for the local Layer 1 demo."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg_pool import PoolTimeout
from pydantic import BaseModel, ConfigDict, Field

from aclara.agent.ai import AgentAI
from aclara.agent.contracts import ResponsePlan, TransactionView
from aclara.agent.conversation import (
    changes_target,
    classify_request,
    recognizes_charge,
    risk_reasons,
    unfamiliar_charge,
)
from aclara.agent.matching import MatchState
from aclara.agent.nlg.builder import render_dispute_offer
from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.nlu import (
    Intent,
    classify,
    is_cancellation,
    is_confirmation,
    normalize_text,
)
from aclara.agent.nlu.structured import NluResult, NormalizedSlots
from aclara.agent.nlu.structured import understand as deterministic_understand
from aclara.agent.runtime import InjectedFailure, Runtime
from aclara.agent.selection import candidates as identified_candidates
from aclara.agent.selection import explicit_choice, scoped_inquiry_language, uncertain
from aclara.api.staff import complete_packet, install_staff
from aclara.api.staff_contracts import IdentityView
from aclara.api.workflows import (
    fraud_handoff,
    install_workflows,
    make_handoff,
    policy_context,
    public_case,
    safe_merchant,
    security_event,
)
from aclara.bank.repository import Transaction, TransactionRepository
from aclara.bank.serving import (
    Persona,
    ServingRepository,
    demo_story_mappings,
    request_snapshot_cache,
)
from aclara.handoff.packet import create_packet
from aclara.handoff.routing import AgentDirectory
from aclara.llm.client import StructuredClient
from aclara.ops.budget import PostgresSpendGate
from aclara.ops.store import Scope, Store
from aclara.policy.engine import PolicyDecision, evaluate
from aclara.policy.rules import catalog, rule
from aclara.policy.rules.guards import cross_customer, escalations, injection, unsupported_language
from aclara.settings import Settings


@dataclass(frozen=True, slots=True)
class Principal:
    session_id: str
    run_id: str
    customer_id: str
    username: str
    otp_at: datetime
    expires_at: datetime
    step_up_at: datetime | None = None
    capability_digest: str = ""
    role: str = "customer"
    locale: str = "es-MX"


@dataclass(slots=True)
class OtpChallenge:
    preauth_token: str
    code: str
    expires_at: datetime
    attempts: int = 0
    step_up: bool = False
    username: str = ""


@dataclass(slots=True)
class ActionProposal:
    action_hash: str
    nonce: str
    transaction_handle: str
    transaction: Transaction
    policy: PolicyDecision
    expires_at: datetime
    language: str


class SnapshotCacheMiddleware:
    """Scope serving snapshot memoization to exactly one HTTP request."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        with request_snapshot_cache():
            await self.app(scope, receive, send)


@dataclass(slots=True)
class Conversation:
    session_id: str
    language: str = "es"
    degraded: bool = False
    model_failed: bool = False
    slots: NormalizedSlots | None = None
    candidates: list[tuple[str, Transaction]] = field(default_factory=list)
    intent: Intent | None = None
    proposal: ActionProposal | None = None
    rounds: int = 0
    unsupported_turns: int = 0
    terminal_handoff_id: str | None = None
    offer_handle: str | None = None
    unfamiliar_charge: bool = False
    recognition_rounds: int = 0
    # Legal/distress cues seen during cross-customer attempts; the security
    # handoff must retain them (ADR-0015 §3-4).
    security_cues: list[str] = field(default_factory=list)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginBody(StrictModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class OtpBody(StrictModel):
    challenge_id: str = Field(min_length=1, max_length=160)
    code: str = Field(pattern=r"^\d{6}$")


class MessageBody(StrictModel):
    message: str = Field(min_length=1, max_length=1000)


class ConfirmBody(StrictModel):
    proposal_hash: str = Field(min_length=64, max_length=64)
    confirmed: bool


def _digest_proposal(
    session_id: str, handle: str, decision: PolicyDecision, expires_at: datetime, nonce: str
) -> str:
    content = json.dumps(
        {
            "action": "create_dispute",
            "session_id": session_id,
            "transaction_handle": handle,
            "policy_rules": decision.rule_ids,
            "expires_at": expires_at.isoformat(),
            "nonce": nonce,
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
        "merchant": safe_merchant(row.merchant_name),
        "status": row.transaction_status,
    }


def _localized(language: str, spanish: str, portuguese: str) -> str:
    return spanish if language == "es" else portuguese


def _explanation(language: str, row: Transaction, reason: str) -> str:
    row = replace(row, merchant_name=safe_merchant(row.merchant_name))
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
            f"El cargo de {amount} en {row.merchant_name} aparece como reversado y el importe no fue cobrado. No hay una fecha de reverso registrada.",
            f"A cobrança de {amount} em {row.merchant_name} aparece como estornada e o valor não foi cobrado. Não há uma data de estorno registrada.",
        )
    if reason == "declined":
        return _localized(
            language,
            f"El cargo de {amount} en {row.merchant_name} figura como rechazado; no hubo movimiento de dinero.",
            f"A cobrança de {amount} em {row.merchant_name} aparece como recusada; não houve movimentação de dinheiro.",
        )
    return _localized(
        language,
        f"El registro muestra {amount} en {row.merchant_name}, con estado {row.transaction_status.lower()}.",
        f"O registro mostra {amount} em {row.merchant_name}, com status {row.transaction_status.lower()}.",
    )


def _review_reason(decision: PolicyDecision, language: str) -> str:
    reasons = {
        "pending_over_limit": (
            "La autorización lleva más de 14 días pendiente.",
            "A autorização está pendente há mais de 14 dias.",
        ),
        "outside_intake_window": (
            "El cargo tiene más de 90 días.",
            "A cobrança tem mais de 90 dias.",
        ),
        "restricted_customer_or_product": (
            "El estado del cliente o del producto requiere revisión.",
            "O estado do cliente ou do produto exige análise.",
        ),
        "fee_or_adjustment": (
            "Las tarifas y ajustes requieren revisión humana.",
            "Tarifas e ajustes exigem análise humana.",
        ),
        "unsupported_transaction_type": (
            "Este tipo de movimiento requiere otro proceso.",
            "Este tipo de transação exige outro processo.",
        ),
        "amount_over_limit": (
            "El monto convertido supera el límite de registro automático.",
            "O valor convertido supera o limite de registro automático.",
        ),
        "policy_boundary": (
            "El monto está cerca del límite o el cargo tiene entre 85 y 90 días.",
            "O valor está próximo do limite ou a cobrança tem entre 85 e 90 dias.",
        ),
        "fx_nearest_prior": (
            "La conversión usa un tipo de cambio de una fecha anterior.",
            "A conversão usa uma taxa de câmbio de uma data anterior.",
        ),
        "fraud_review": (
            "Una señal de riesgo requiere atención de Fraudes.",
            "Um sinal de risco exige atendimento de Fraudes.",
        ),
    }
    if decision.reason.startswith("missing:"):
        labels = {
            "amount": ("monto", "valor"),
            "date": ("fecha", "data"),
            "transaction_date": ("fecha", "data"),
            "status": ("estado", "status"),
            "amount_usd": ("conversión de moneda verificada", "conversão de moeda verificada"),
        }
        fields = ", ".join(
            labels.get(f, ("dato necesario", "dado necessário"))[language == "pt"]
            for f in decision.reason.split(":", 1)[1].split(",")
        )
        return ("Falta verificar: " if language == "es" else "Falta verificar: ") + fields + "."
    return reasons.get(
        decision.reason,
        ("Se requiere revisión de los datos.", "É necessária uma análise dos dados."),
    )[language == "pt"]


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
    store: Store | None = None,
) -> FastAPI:
    active_settings = settings or Settings.from_environment()
    operational = store or Store(
        os.getenv("OPS_DSN", "") if active_settings.ops_backend == "postgres" else None
    )
    ledger = repository or (
        ServingRepository(operational, active_settings.bank_clock)
        if active_settings.ledger_backend == "serving"
        else TransactionRepository()
    )
    app = FastAPI(title="Aclara demo API", version="0.1.0")
    app.add_middleware(SnapshotCacheMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("WEB_ORIGIN", "http://localhost:3000")],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Preauth-Token"],
    )
    app.state.runtime = runtime or Runtime(system=active_settings.agent_system)
    spend_gate = (
        PostgresSpendGate(operational, run_id=os.getenv("LLM_BUDGET_RUN_ID") or None)
        if active_settings.llm_provider != "mock" and llm_client is None
        else None
    )
    ai = AgentAI(active_settings, app.state.runtime, llm_client, spend_gate=spend_gate)
    app.state.ai = ai
    app.state.instance_id = str(uuid4())
    app.state.settings = active_settings
    app.state.ledger = ledger
    app.state.loaded_at = ledger.loaded_at
    app.state.dataset_version = ledger.dataset_version
    app.state.personas = {
        p.username: p
        for p in (
            ledger.personas()
            if isinstance(ledger, ServingRepository)
            else [
                Persona(
                    active_settings.demo_username,
                    active_settings.demo_customer_id,
                    active_settings.demo_locale,
                    active_settings.demo_role,
                )
            ]
        )
        if p.username
    }
    app.state.demo_stories = demo_story_mappings(
        ledger, app.state.personas, active_settings.bank_clock
    )
    realms = {
        hashlib.sha256(p.username.encode()).hexdigest()[:12]: p.customer_id
        for p in app.state.personas.values()
    }

    def auth_customer(run_id: str) -> str:
        if not isinstance(ledger, ServingRepository):
            return active_settings.demo_customer_id
        realm, separator, _ = run_id.partition("_")
        if not separator or realm not in realms:
            raise KeyError("Unknown identity realm")
        return str(realms[realm])

    app.state.store = operational
    app.state.agent_directory = (
        ledger.directory()
        if isinstance(ledger, ServingRepository)
        else AgentDirectory(store=operational)
    )
    auth_scope = Scope(active_settings.demo_customer_id, "auth", "auth")
    app.state.challenges = operational.mapping(
        "otp_challenges", OtpChallenge, auth_scope=auth_scope, auth_customer=auth_customer
    )
    app.state.sessions = operational.mapping(
        "sessions", Principal, auth_scope=auth_scope, auth_customer=auth_customer
    )
    app.state.conversations = operational.mapping("conversations", Conversation)
    app.state.cases = operational.mapping("cases", dict[str, Any])
    app.state.handoffs = operational.mapping("handoffs", dict[str, Any])
    app.state.card_states = operational.mapping("card_states", dict[str, Any])
    app.state.executions = operational.mapping("execution_records", dict[str, Any])
    app.state.turns = operational.mapping("turns", dict[str, Any])
    app.state.idempotency = operational.mapping("idempotency_keys", dict[str, Any])

    def scope(principal: Principal) -> Scope:
        return Scope(principal.customer_id, principal.run_id, principal.session_id)

    def execution(
        result: dict[str, Any], conversation_id: str, cursor: int, message: str | None = None
    ) -> None:
        record_id = str(uuid4())
        events = app.state.runtime.events[cursor:]
        app.state.executions[record_id] = {
            "conversation_id": conversation_id,
            "created_at": datetime.now(UTC).isoformat(),
            "events": events,
            "outcome": result["outcome"],
            "response": result,
            "policy_version": catalog()[0],
            "system": app.state.runtime.system,
        }
        app.state.turns[record_id] = {
            "conversation_id": conversation_id,
            "customer_text": redact_for_model(message) if message else None,
            "response": result,
        }

    learned_matcher: MatchState | None = None

    @app.exception_handler(psycopg.Error)
    @app.exception_handler(PoolTimeout)
    async def database_unavailable(_request: Request, _error: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "Operational storage unavailable; no success can be confirmed"},
        )

    def principal_from_token(token: str | None) -> Principal:
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        principal: Principal | None = app.state.sessions.get(token)
        now = datetime.now(UTC)
        if principal is None or principal.expires_at <= now:
            app.state.sessions.pop(token, None)
            raise HTTPException(status_code=401, detail="Session expired")
        return replace(principal, capability_digest=hashlib.sha256(token.encode()).hexdigest())

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
            "instance_id": app.state.instance_id,
            "storage": "postgres" if operational.pool else "memory",
        }

    @app.get("/readyz")
    async def readyz() -> dict[str, str]:
        if not _read_db_ready():
            raise HTTPException(status_code=503, detail="Database unavailable")
        if operational.pool:
            try:
                with operational.transaction(Scope("", "", "")):
                    operational.keys("cases")
            except (psycopg.Error, PoolTimeout, PermissionError):
                raise HTTPException(
                    status_code=503, detail="Operational storage unavailable"
                ) from None
        if isinstance(ledger, ServingRepository) and not ledger.ready():
            raise HTTPException(503, "Serving version changed")
        return {"status": "ready", "database": "ok"}

    @app.post("/auth/login", status_code=status.HTTP_200_OK)
    async def login(body: LoginBody) -> dict[str, str]:
        if not app.state.personas or not active_settings.demo_password:
            raise HTTPException(status_code=503, detail="Demo identity is not configured")
        persona = app.state.personas.get(body.username)
        valid = (
            hmac.compare_digest(body.password, active_settings.demo_password)
            and persona is not None
        )
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid login")
        session_id = secrets.token_urlsafe(18)
        run_id = app.state.runtime.run_id
        if isinstance(ledger, ServingRepository):
            run_id = hashlib.sha256(body.username.encode()).hexdigest()[:12] + "_" + run_id
        challenge_id = f"{run_id}.{session_id}.{secrets.token_urlsafe(18)}"
        preauth_token = secrets.token_urlsafe(24)
        app.state.challenges[challenge_id] = OtpChallenge(
            preauth_token=hashlib.sha256(preauth_token.encode()).hexdigest(),
            code=f"{secrets.randbelow(1_000_000):06d}",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            username=body.username,
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
            or not hmac.compare_digest(
                challenge.preauth_token, hashlib.sha256(x_preauth_token.encode()).hexdigest()
            )
        ):
            raise HTTPException(status_code=404, detail="Challenge not found")
        return {"code": challenge.code, "channel": "simulated_sms"}

    @app.post("/auth/otp/verify")
    async def verify_otp(
        body: OtpBody, x_preauth_token: str | None = Header(default=None)
    ) -> dict[str, str]:
        error = None
        result: dict[str, str] = {}
        try:
            challenge_scope = app.state.challenges.auth_context(body.challenge_id)
        except KeyError:
            raise HTTPException(status_code=401, detail="Challenge expired or invalid") from None
        with operational.transaction(challenge_scope):
            try:
                result = await process_otp(body, x_preauth_token)
            except HTTPException as exc:
                error = exc
        if error:
            raise error
        return result

    async def process_otp(
        body: OtpBody, x_preauth_token: str | None = Header(default=None)
    ) -> dict[str, str]:
        challenge: OtpChallenge | None = app.state.challenges.get(body.challenge_id)
        now = datetime.now(UTC)
        if (
            challenge is None
            or challenge.step_up
            or challenge.expires_at <= now
            or challenge.attempts >= 5
            or not x_preauth_token
            or not hmac.compare_digest(
                challenge.preauth_token, hashlib.sha256(x_preauth_token.encode()).hexdigest()
            )
        ):
            raise HTTPException(status_code=401, detail="Challenge expired or invalid")
        challenge.attempts += 1
        app.state.challenges[body.challenge_id] = challenge
        if not hmac.compare_digest(body.code, challenge.code):
            raise HTTPException(status_code=401, detail="Invalid code")
        run_id, session_id, _ = body.challenge_id.split(".", 2)
        persona = app.state.personas.get(challenge.username or active_settings.demo_username)
        if persona is None or persona.customer_id != auth_customer(run_id):
            raise HTTPException(401, "Identity unavailable")
        session_token = f"{run_id}.{session_id}.{secrets.token_urlsafe(32)}"
        app.state.sessions[session_token] = Principal(
            session_id=session_id,
            run_id=run_id,
            customer_id=persona.customer_id,
            username=persona.username,
            role=persona.role,
            locale=persona.locale,
            otp_at=now,
            expires_at=now + timedelta(minutes=int(rule("AUTH-01").parameters["session_minutes"])),
        )
        del app.state.challenges[body.challenge_id]
        return {"access_token": session_token, "token_type": "bearer"}

    @app.get("/me", response_model=IdentityView)
    async def me(principal: Principal = Depends(get_principal)) -> IdentityView:
        return IdentityView.model_validate(
            {
                "username": principal.username,
                "language": "pt" if principal.locale == "pt-BR" else "es",
                "role": principal.role,
                "locale": principal.locale,
                "bank_clock": active_settings.bank_clock,
            }
        )

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
        with operational.transaction(scope(principal)):
            conversation_id = str(uuid4())
            app.state.conversations[conversation_id] = Conversation(session_id=principal.session_id)
            return {"conversation_id": conversation_id}

    @app.post("/chat/sessions/{conversation_id}/messages", response_model=ResponsePlan)
    async def send_message(
        conversation_id: str,
        body: MessageBody,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        cursor = len(app.state.runtime.events)
        with operational.transaction(scope(principal)):
            try:
                app.state.runtime.checkpoint("MATCH")
                result = await process_message(conversation_id, body, principal)
            except InjectedFailure as error:
                result = safe_failure(principal, classify(body.message).language, str(error))
            app.state.runtime.record("response", response_type=result["response_type"])
            conversation = app.state.conversations.get(conversation_id)
            complete_packet(app, result, principal, conversation_id, body.message)
            if conversation and result.get("handoff"):
                conversation.proposal = None
                conversation.candidates = []
                conversation.offer_handle = None
                conversation.unfamiliar_charge = False
                conversation.terminal_handoff_id = result["handoff"]["handoff_id"]
            result = ai.reply(
                result,
                conversation.language if conversation else "es",
                # Recognition is a specific decision question. Generic phrasing
                # must not replace it with a request for transaction details.
                deterministic=bool(
                    conversation
                    and (
                        conversation.degraded
                        or (conversation.offer_handle and result["response_type"] == "clarify")
                    )
                ),
            )
            execution(result, conversation_id, cursor, body.message)
        # Commit precedes the independent read-back and any success response.
        if result.get("case"):
            with operational.transaction(scope(principal)):
                record = app.state.cases.get(result["case"]["case_id"])
                if (
                    not record
                    or record["transaction_handle"] != result["case"]["transaction_handle"]
                    or record["status"] != result["case"]["status"]
                ):
                    raise HTTPException(
                        status_code=503, detail="Durable read-back verification failed"
                    )
                operational.audit({"action": "verified_commit", "case_id": record["case_id"]})
        if result.get("handoff"):
            with operational.transaction(scope(principal)):
                if not app.state.handoffs.get(result["handoff"]["handoff_id"]):
                    raise HTTPException(status_code=503, detail="Durable handoff read-back failed")
                result["verified"] = True
                app.state.executions[str(uuid4())] = {
                    "conversation_id": conversation_id,
                    "created_at": datetime.now(UTC).isoformat(),
                    "events": [
                        {"event": "verify_readback", "handle": result["handoff"]["handoff_id"]}
                    ],
                    "outcome": "handoff_verified",
                    "policy_version": catalog()[0],
                }
        return result

    def safe_failure(
        principal: Principal, language: str, cause: str = "tool_failure"
    ) -> dict[str, Any]:
        reasons = ["COM-01", "ESC-04"]
        if cause in {"database_timeout", "connection_reset"}:
            reasons.append("DATA-01")
        packet = create_packet(language, reasons, app.state.agent_directory)
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

    def refuse_cross_customer(
        principal: Principal, conversation: Conversation, language: str, message: str
    ) -> dict[str, Any]:
        security_event(app, "cross_customer_attempt")
        cues = {reason for reason in escalations(message) if reason in {"ESC-02", "ESC-03"}}
        conversation.security_cues = sorted(set(conversation.security_cues) | cues)
        state = app.state.executions.get("security_state", {"attempts": 0})
        # The strikes and their cues share the durable authenticated-session scope.
        # Older records may have kept cues only in conversation objects; preserve
        # those too when the next strike arrives after an upgrade or restart.
        state["cues"] = sorted(
            set(state.get("cues", []))
            | cues
            | {cue for tab in app.state.conversations.values() for cue in tab.security_cues}
        )
        state["attempts"] += 1
        app.state.executions["security_state"] = state
        ended = state["attempts"] >= int(rule("SEC-01").parameters["end_session_attempts"])
        # Invalidate all pending decisions in this authenticated session, including
        # another chat tab. Scoped maps cannot enumerate another session's state.
        for pending in app.state.conversations.values():
            pending.proposal = None
            pending.offer_handle = None
            pending.candidates = []
            pending.slots = None
            pending.intent = None
            pending.unfamiliar_charge = False
        for key in list(app.state.idempotency):
            if key.startswith("freeze-proposal:"):
                del app.state.idempotency[key]
        result = {
            "response_type": "refuse",
            "outcome": "refused_security",
            "reply": _localized(
                language,
                "Solo puedo consultar los datos de tu sesión autenticada.",
                "Só posso consultar os dados da sua sessão autenticada.",
            ),
            "policy_rules": ["AUTH-03", "SEC-01"],
            "session_ended": ended,
        }
        app.state.runtime.record("refuse_request")
        if ended:
            result["handoff"] = make_handoff(app, principal, language, ("SEC-01", *state["cues"]))[
                "handoff"
            ]
            operational.delete("sessions", principal.capability_digest)
            app.state.runtime.record("end_session")
        return result

    async def process_message(
        conversation_id: str,
        body: MessageBody,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        conversation: Conversation | None = app.state.conversations.get(conversation_id)
        if conversation is None or conversation.session_id != principal.session_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if cross_customer(body.message):
            if not (
                conversation.candidates
                or conversation.offer_handle
                or conversation.proposal
                or conversation.intent
            ):
                # No established conversation language yet: route in the language used.
                conversation.language = classify(body.message).language
            return refuse_cross_customer(
                principal, conversation, conversation.language, body.message
            )
        if conversation.terminal_handoff_id:
            packet = app.state.handoffs[conversation.terminal_handoff_id]
            return {
                "response_type": "offer_human",
                "outcome": "handoff_created",
                "reply": _handoff_reply(conversation.language),
                "handoff": {
                    k: v
                    for k, v in packet.items()
                    if k not in {"customer_id", "session_id", "request_summary"}
                },
                "policy_rules": packet["reason_codes"],
            }
        if conversation.proposal is not None:
            if is_confirmation(body.message):
                raise HTTPException(status_code=409, detail="Use the action confirmation control")
            conversation.proposal = None
            if is_cancellation(body.message):
                return {
                    "response_type": "cancelled",
                    "outcome": "cancelled",
                    "reply": _localized(
                        conversation.language, "Disputa cancelada.", "Contestação cancelada."
                    ),
                }
        nonlocal learned_matcher
        frame = classify_request(body.message)
        nlu: NluResult | None = None
        language = (
            conversation.language
            if conversation.candidates or conversation.offer_handle
            else frame.language
        )
        conversation.language = language
        if injection(body.message):
            security_event(app, "direct_prompt_injection")
            clean = " ".join(
                part for part in re.split(r"[.;\n]", body.message) if not injection(part)
            )
            if not clean.strip() or classify(clean).intent == Intent.OUT_OF_SCOPE:
                app.state.runtime.record("refuse_request")
                return {
                    "response_type": "refuse",
                    "outcome": "refused_security",
                    "reply": _localized(
                        language,
                        "No puedo revelar instrucciones internas ni cambiar los controles. Puedo ayudarte con un cargo.",
                        "Não posso revelar instruções internas nem alterar os controles. Posso ajudar com uma cobrança.",
                    ),
                    "policy_rules": ["SEC-02"],
                }
            body = MessageBody(message=clean)
            frame = classify_request(clean)
        reasons = escalations(body.message)
        if frame.intent == Intent.FRAUD:
            reasons.append("FRD-01")
        if reasons:
            conversation.proposal = None
            if "FRD-01" in reasons:
                return fraud_handoff(app, principal, language, reasons=reasons)
            return make_handoff(app, principal, language, reasons)
        if unsupported_language(body.message):
            conversation.unsupported_turns += 1
            if conversation.unsupported_turns >= 2:
                return make_handoff(app, principal, language, "ESC-04")
            return {
                "response_type": "clarify",
                "outcome": "clarification",
                "reply": "Puedo atenderte en español o portugués. / Posso atender em espanhol ou português.",
                "policy_rules": ["ESC-04"],
            }
        normalized_message = normalize_text(body.message)
        requested = re.search(r"DSP-[A-Za-z0-9-]+", body.message, re.IGNORECASE)
        if requested or re.search(
            r"(estado|status|andamento).{0,30}(caso|disputa|contestacion|contestacao)|(mi caso|minha contestacao)",
            normalized_message,
        ):
            cases = list(app.state.cases.values())
            if requested:
                cases = [
                    c for c in cases if c["case_id"].casefold() == requested.group().casefold()
                ]
            if cases:
                record = cases[-1]
                app.state.runtime.record("status_lookup")
                app.state.runtime.record("report_case", handle=record["transaction_handle"])
                return {
                    "response_type": "report_status",
                    "outcome": "status_reported",
                    "reply": _localized(
                        language,
                        f"El caso {record['case_id']} tiene estado {record['status']}.",
                        f"O caso {record['case_id']} tem status {record['status']}.",
                    ),
                    "case": public_case(record),
                    "verified": True,
                    "policy_rules": ["DSP-06"],
                }
            return {
                "response_type": "clarify",
                "outcome": "clarification",
                "reply": _localized(
                    language,
                    "No encontré ese caso en tu sesión. ¿Qué cargo quieres revisar?",
                    "Não encontrei esse caso na sua sessão. Qual cobrança deseja consultar?",
                ),
                "policy_rules": ["DSP-06"],
            }
        offered_row = None
        if conversation.offer_handle:
            offered_row = dict(
                ledger.for_customer(principal.customer_id, active_settings.bank_clock)
            ).get(conversation.offer_handle)
            if offered_row is None:
                conversation.offer_handle = None
                return safe_failure(principal, language, "database_timeout")
        if (
            app.state.runtime.system == "P"
            and not conversation.candidates
            and not conversation.proposal
        ):
            nlu = ai.understand(
                body.message,
                active_settings.bank_clock,
                awaiting_recognition=offered_row is not None,
                masked_charge={
                    k: str(v)
                    for k, v in _masked_transaction(
                        conversation.offer_handle or "", offered_row
                    ).items()
                    if k in {"merchant", "amount", "currency", "transaction_date", "status"}
                }
                if offered_row
                else None,
            )
            if nlu.extracted.other_customer_reference:
                return refuse_cross_customer(principal, conversation, language, body.message)
            extracted_reasons = risk_reasons(nlu.extracted)
            if extracted_reasons:
                if "FRD-01" in extracted_reasons:
                    return fraud_handoff(app, principal, language, reasons=extracted_reasons)
                return make_handoff(app, principal, language, extracted_reasons)
            conversation.degraded = nlu.degraded
            conversation.model_failed |= nlu.degraded and (
                ai.client.models["nlu"].provider != "mock"
                or ai.client.mock_configured
                or any(
                    e.get("event") == "fault" and e.get("kind") == "llm_outage"
                    for e in app.state.runtime.events
                )
            )
            if not nlu.degraded:
                frame = nlu.frame
                previous = conversation.slots.model_dump() if conversation.slots else {}
                conversation.slots = NormalizedSlots.model_validate(
                    {
                        **previous,
                        **{k: v for k, v in nlu.slots.model_dump().items() if v is not None},
                    }
                )
                if (
                    conversation.intent
                    and conversation.rounds
                    and frame.intent == Intent.OUT_OF_SCOPE
                ):
                    frame = frame.model_copy(update={"intent": conversation.intent})
                # Conservative deterministic routing takes precedence over extracted intent.
                guard = classify_request(body.message)
                if guard.intent in {Intent.HUMAN_REQUEST, Intent.FRAUD, Intent.FEE_DISPUTE}:
                    frame = guard
                elif not offered_row and (
                    nlu.clarification
                    or frame.confidence < float(rule("ESC-04").parameters["nlu_min_confidence"])
                ):
                    if frame.confidence < float(rule("ESC-04").parameters["nlu_min_confidence"]):
                        return make_handoff(app, principal, conversation.language, "ESC-04")
                    conversation.rounds += 1
                    if conversation.intent != Intent.DISPUTE_CHARGE:
                        conversation.intent = frame.intent
                    conversation.language = (
                        "pt" if nlu.extracted.language == "pt" else conversation.language
                    )
                    if conversation.rounds >= 2:
                        return make_handoff(app, principal, conversation.language, "ESC-04")
                    return {
                        "response_type": "clarify",
                        "outcome": "clarification",
                        "reply": _localized(
                            conversation.language,
                            "¿Puedes aclarar el idioma, monto, moneda o fecha?",
                            "Pode esclarecer o idioma, valor, moeda ou data?",
                        ),
                    }
        if offered_row is not None:
            if nlu is None:
                nlu = deterministic_understand(
                    body.message,
                    country=app.state.runtime.country,
                    bank_clock=active_settings.bank_clock,
                    awaiting_recognition=True,
                )
            if normalize_text(body.message).strip(" .,!¿?¡") in {
                "cancelar",
                "cancela",
                "deixa",
                "deixa pra la",
            }:
                conversation.offer_handle = None
                conversation.unfamiliar_charge = False
                conversation.intent = None
                return {
                    "response_type": "cancelled",
                    "outcome": "cancelled",
                    "reply": _localized(language, "Disputa cancelada.", "Contestação cancelada."),
                }
            changed = changes_target(body.message, offered_row, nlu.slots)
            recognition = nlu.extracted.recognition
            if normalize_text(body.message).strip(" .,!¿?¡") in {"si", "sim", "no", "nao"}:
                recognition = "unsure"
            elif recognition is None and recognizes_charge(body.message):
                recognition = "recognized"
            elif recognition is None and (
                frame.intent == Intent.DISPUTE_CHARGE or unfamiliar_charge(body.message)
            ):
                recognition = "denied"
            if not changed and recognition in {"recognized", "denied"}:
                handle = conversation.offer_handle
                assert handle is not None
                conversation.offer_handle = None
                conversation.unfamiliar_charge = False
                conversation.recognition_rounds = 0
                conversation.rounds = 0
                conversation.intent = (
                    Intent.DISPUTE_CHARGE if recognition == "denied" else Intent.CHARGE_INQUIRY
                )
                app.state.runtime.record("recognition", value=recognition, handle=handle)
                return _decide_for_transaction(
                    app,
                    conversation,
                    principal,
                    language,
                    conversation.intent,
                    handle,
                    offered_row,
                    active_settings,
                )
            if (
                not changed
                and frame.intent != Intent.OUT_OF_SCOPE
                or (not changed and recognition == "unsure")
            ):
                conversation.recognition_rounds += 1
                if conversation.recognition_rounds >= 2:
                    return make_handoff(
                        app,
                        principal,
                        language,
                        ("COM-01", "ESC-04") if conversation.model_failed else "ESC-04",
                    )
                return {
                    "response_type": "clarify",
                    "outcome": "clarification",
                    "reply": _localized(
                        language,
                        "¿Ahora reconoces el cargo, o quieres disputarlo? Indica una de esas opciones.",
                        "Agora você reconhece a cobrança ou quer contestá-la? Diga uma dessas opções.",
                    ),
                }
            conversation.offer_handle = None
            conversation.intent = None
            conversation.unfamiliar_charge = False
            conversation.rounds = 0
            conversation.recognition_rounds = 0
            conversation.slots = nlu.slots if not nlu.degraded else None
        if frame.intent == Intent.OUT_OF_SCOPE and not conversation.candidates:
            contextual_language = scoped_inquiry_language(
                body.message, ledger.for_customer(principal.customer_id, active_settings.bank_clock)
            )
            if contextual_language:
                frame = frame.model_copy(
                    update={"intent": Intent.CHARGE_INQUIRY, "language": contextual_language}
                )
                app.state.runtime.record("scoped_status_context")
        language = conversation.language if conversation.candidates else frame.language
        conversation.language = language

        if frame.intent in {Intent.HUMAN_REQUEST, Intent.FRAUD, Intent.FEE_DISPUTE}:
            reason_code = {
                Intent.HUMAN_REQUEST: "ESC-01",
                Intent.FRAUD: "FRD-01",
                Intent.FEE_DISPUTE: "DSP-03",
            }[frame.intent]
            conversation.proposal = None
            if reason_code == "FRD-01":
                return fraud_handoff(app, principal, language)
            packet = create_packet(language, reason_code, app.state.agent_directory)
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

        if conversation.intent and conversation.rounds and frame.intent == Intent.OUT_OF_SCOPE:
            frame = frame.model_copy(update={"intent": conversation.intent})
        if conversation.intent == Intent.DISPUTE_CHARGE and (
            conversation.rounds or conversation.candidates
        ):
            frame = frame.model_copy(update={"intent": Intent.DISPUTE_CHARGE})
        if frame.intent in {Intent.DISPUTE_CHARGE, Intent.CHARGE_INQUIRY}:
            conversation.intent = frame.intent
            if frame.intent == Intent.DISPUTE_CHARGE:
                conversation.unfamiliar_charge = False
            else:
                conversation.unfamiliar_charge |= unfamiliar_charge(body.message) or bool(
                    nlu and getattr(nlu.extracted, "unfamiliar_charge", False)
                )
        if frame.intent == Intent.OUT_OF_SCOPE and not conversation.candidates:
            if conversation.model_failed:
                # The deterministic fallback could not classify the request while the
                # model route was down: a safe failure, not an out-of-scope claim
                # (ADR-0015 §3, model outage with unsuccessful fallback).
                return safe_failure(principal, language, "llm_outage")
            handoff = make_handoff(app, principal, language, "SCOPE-01")
            app.state.runtime.record("abstain")
            return {
                "handoff": handoff["handoff"],
                "policy_rules": ["SCOPE-01"],
                "response_type": "abstain",
                "outcome": "abstained_out_of_scope",
                "reply": _localized(
                    language,
                    "Puedo ayudar con cargos no reconocidos. Si necesitas otro tema, puedo derivarte a una persona.",
                    "Posso ajudar com cobranças não reconhecidas. Para outro assunto, posso encaminhar você a uma pessoa da equipe.",
                ),
            }

        if conversation.candidates:
            choice = explicit_choice(body.message, len(conversation.candidates))
            if choice is None:
                conversation.rounds += 1
                if conversation.rounds >= 2:
                    conversation.candidates = []
                    packet = create_packet(language, "ESC-04", app.state.agent_directory)
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
        if any(injection(row.merchant_name) for _, row in rows):
            security_event(app, "indirect_prompt_injection")
            rows = [
                (handle, replace(row, merchant_name=safe_merchant(row.merchant_name)))
                for handle, row in rows
            ]
        candidates, needs_choice = identified_candidates(body.message, rows)
        if uncertain(body.message):
            candidates = []

        learned_choice = False
        if app.state.runtime.system == "P" and not conversation.degraded and conversation.slots:
            if learned_matcher is None:
                learned_matcher = MatchState()
            matched = learned_matcher.match(
                conversation.slots, rows, principal.customer_id, active_settings.bank_clock
            )
            app.state.runtime.record(
                "match",
                matcher_version=learned_matcher.version,
                action=matched.action,
                top_probability=matched.top_correct_probability,
                exists_probability=matched.match_exists_probability,
            )
            by_handle = dict(rows)
            candidates = [(handle, by_handle[handle]) for handle in matched.transaction_ids]
            learned_choice = matched.action == "choose"
            if app.state.runtime.fault("missing_fx", "MATCH"):
                candidates = []

        if uncertain(body.message):
            candidates = []
        if not candidates:
            conversation.rounds += 1
            if conversation.rounds >= 2:
                failure_reasons = ("COM-01", "ESC-04") if conversation.model_failed else ("ESC-04",)
                packet = create_packet(language, failure_reasons, app.state.agent_directory)
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

        if len(candidates) > 1 or learned_choice or needs_choice:
            conversation.candidates = candidates[:3]
            conversation.intent = frame.intent
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
        cursor = len(app.state.runtime.events)
        with operational.transaction(scope(principal)):
            try:
                result = await process_confirmation(conversation_id, body, principal)
            except InjectedFailure:
                conversation = app.state.conversations.get(conversation_id)
                language = (
                    conversation.proposal.language
                    if conversation and conversation.proposal
                    else "es"
                )
                if conversation:
                    conversation.proposal = None
                result = safe_failure(principal, language)
            app.state.runtime.record("response", response_type=result["response_type"])
            conversation = app.state.conversations.get(conversation_id)
            complete_packet(app, result, principal, conversation_id)
            if conversation and result.get("handoff"):
                conversation.proposal = None
                conversation.candidates = []
                conversation.offer_handle = None
                conversation.unfamiliar_charge = False
                conversation.terminal_handoff_id = result["handoff"]["handoff_id"]
            result = ai.reply(
                result,
                conversation.language if conversation else "es",
                deterministic=bool(conversation and conversation.degraded),
            )
            execution(result, conversation_id, cursor, None)
        # Commit precedes the independent read-back and any success response.
        if result.get("case"):
            with operational.transaction(scope(principal)):
                record = app.state.cases.get(result["case"]["case_id"])
                if (
                    not record
                    or record["transaction_handle"] != result["case"]["transaction_handle"]
                    or record["status"] != result["case"]["status"]
                ):
                    raise HTTPException(
                        status_code=503, detail="Durable read-back verification failed"
                    )
                operational.audit({"action": "verified_commit", "case_id": record["case_id"]})
        if result.get("handoff"):
            with operational.transaction(scope(principal)):
                if not app.state.handoffs.get(result["handoff"]["handoff_id"]):
                    raise HTTPException(status_code=503, detail="Durable handoff read-back failed")
                result["verified"] = True
                app.state.executions[str(uuid4())] = {
                    "conversation_id": conversation_id,
                    "created_at": datetime.now(UTC).isoformat(),
                    "events": [
                        {"event": "verify_readback", "handle": result["handoff"]["handoff_id"]}
                    ],
                    "outcome": "handoff_verified",
                    "policy_version": catalog()[0],
                }
        return result

    async def process_confirmation(
        conversation_id: str,
        body: ConfirmBody,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        conversation: Conversation | None = app.state.conversations.get(conversation_id)
        if conversation is None or conversation.session_id != principal.session_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.terminal_handoff_id:
            raise HTTPException(status_code=409, detail="Conversation already handed off")
        proposal = conversation.proposal
        if proposal is None:
            raise HTTPException(status_code=409, detail="No pending action")
        if not body.confirmed:
            conversation.proposal = None
            return {
                "response_type": "cancelled",
                "outcome": "cancelled",
                "reply": _localized(
                    proposal.language, "Disputa cancelada.", "Contestação cancelada."
                ),
            }
        expected_hash = _digest_proposal(
            principal.session_id,
            proposal.transaction_handle,
            proposal.policy,
            proposal.expires_at,
            proposal.nonce,
        )
        now = datetime.now(UTC)
        if (
            not hmac.compare_digest(expected_hash, proposal.action_hash)
            or not hmac.compare_digest(body.proposal_hash, proposal.action_hash)
            or proposal.expires_at <= now
        ):
            conversation.proposal = None
            raise HTTPException(status_code=409, detail="Action proposal expired or changed")
        if now - principal.otp_at > timedelta(
            minutes=int(rule("AUTH-02").parameters["otp_minutes"])
        ):
            raise HTTPException(status_code=401, detail="Step-up verification required")
        current_rows = dict(ledger.for_customer(principal.customer_id, active_settings.bank_clock))
        current = current_rows.get(proposal.transaction_handle)
        if (
            current is None
            or replace(current, merchant_name=safe_merchant(current.merchant_name))
            != proposal.transaction
        ):
            raise HTTPException(409, "Transaction changed; request a new proposal")
        context = policy_context(app, principal, current)
        decision = evaluate(current, active_settings.bank_clock, is_dispute=True, context=context)
        if decision.decision == "status":
            record = app.state.cases[context.existing_case_id]
            conversation.proposal = None
            return {
                "response_type": "report_status",
                "outcome": "status_reported",
                "reply": _localized(
                    proposal.language, "El caso ya está registrado.", "O caso já está registrado."
                ),
                "case": public_case(record),
                "verified": True,
                "policy_rules": ["DSP-06"],
            }
        if decision.decision != "eligible":
            conversation.proposal = None
            raise HTTPException(status_code=409, detail="Policy no longer permits this action")

        previous = app.state.idempotency.get(proposal.action_hash)
        if previous:
            record = app.state.cases.get(previous["case_id"])
            if record:
                conversation.proposal = None
                return {
                    "response_type": "report_case",
                    "outcome": "dispute_filed",
                    "reply": _localized(
                        proposal.language,
                        "El caso ya está registrado.",
                        "O caso já está registrado.",
                    ),
                    "case": {
                        k: v
                        for k, v in record.items()
                        if k not in {"customer_id", "transaction_id"}
                    },
                    "verified": True,
                }
        case_id = f"DSP-{secrets.token_hex(4).upper()}"
        record = {
            "case_id": case_id,
            "customer_id": principal.customer_id,
            "transaction_id": proposal.transaction.record_id,
            "transaction_handle": proposal.transaction_handle,
            "status": "received",
            "policy_rules": list(decision.rule_ids),
            "created_at": now.isoformat(),
            "bank_created_at": active_settings.bank_clock.isoformat(),
            "review_flag": decision.review_flag,
        }
        app.state.runtime.record("policy", **asdict(decision))
        app.state.runtime.checkpoint("create_dispute")
        app.state.cases[case_id] = record
        app.state.idempotency[proposal.action_hash] = {"case_id": case_id}
        app.state.runtime.record(
            "create_dispute", handle=proposal.transaction_handle, confirmed=True, step_up=True
        )
        app.state.runtime.checkpoint("read_back")
        read_back = app.state.cases.get(case_id)
        conversation.proposal = None
        if read_back is None or read_back["customer_id"] != principal.customer_id:
            raise HTTPException(status_code=503, detail="Read-back verification failed")
        app.state.runtime.record("verify_readback", handle=proposal.transaction_handle)
        if decision.review_flag:
            app.state.runtime.record("set_review_flag", handle=proposal.transaction_handle)
        return {
            "response_type": "report_case",
            "outcome": "dispute_filed",
            "reply": _localized(
                proposal.language,
                f"Tu disputa {case_id} fue registrada y verificada. El siguiente paso es la revisión; respuesta en hasta 15 días (SLA simulado).",
                f"Sua contestação {case_id} foi registrada e verificada. A próxima etapa é a análise; resposta em até 15 dias (SLA simulado).",
            ),
            "case": public_case(read_back),
            "verified": True,
        }

    @app.get("/disputes/{case_id}")
    async def read_dispute(
        case_id: str,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        with operational.transaction(scope(principal)):
            record: dict[str, Any] | None = app.state.cases.get(case_id)
            if record is None or record["customer_id"] != principal.customer_id:
                raise HTTPException(status_code=404, detail="Dispute not found")
            return public_case(record)

    @app.get("/handoffs/{handoff_id}")
    async def read_handoff(
        handoff_id: str,
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        with operational.transaction(scope(principal)):
            packet: dict[str, Any] | None = app.state.handoffs.get(handoff_id)
            if (
                packet is None
                or packet["customer_id"] != principal.customer_id
                or packet["session_id"] != principal.session_id
            ):
                raise HTTPException(status_code=404, detail="Handoff not found")
            return {
                key: value
                for key, value in packet.items()
                if key not in {"customer_id", "session_id"}
            }

    install_workflows(app, get_principal)
    install_staff(app, get_principal)
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
    current = dict(app.state.ledger.for_customer(principal.customer_id, settings.bank_clock)).get(
        handle
    )
    if current is None:
        return make_handoff(app, principal, language, ("DATA-01", "COM-01", "ESC-04"))
    row = current
    is_dispute = intent == Intent.DISPUTE_CHARGE
    context = policy_context(app, principal, row)
    decision = evaluate(
        row,
        settings.bank_clock,
        is_dispute=is_dispute or bool(context.existing_case_id),
        context=context,
    )
    app.state.runtime.record("policy", **asdict(decision))
    row = replace(row, merchant_name=safe_merchant(row.merchant_name))
    if decision.decision == "freeze_offer":
        return fraud_handoff(app, principal, language, row, reasons=decision.rule_ids)
    if decision.decision == "status":
        record = app.state.cases[context.existing_case_id]
        app.state.runtime.record("status_lookup")
        app.state.runtime.record("report_case", handle=handle)
        return {
            "response_type": "report_status",
            "outcome": "status_reported",
            "reply": _localized(
                language,
                "Ya existe un caso para este cargo.",
                "Já existe um caso para esta cobrança.",
            ),
            "case": public_case(record),
            "verified": True,
            "policy_rules": ["DSP-06"],
        }
    if decision.decision == "handoff":
        packet = create_packet(language, decision.rule_ids, app.state.agent_directory)
        if not decision.reason.startswith("missing:"):
            packet["verified_facts"] = [_masked_transaction(handle, row)]
        app.state.handoffs[packet["handoff_id"]] = {
            **packet,
            "customer_id": principal.customer_id,
            "session_id": principal.session_id,
        }
        return {
            "response_type": "offer_human",
            "outcome": "handoff_created",
            "reply": _handoff_reply(language)
            + " "
            + _localized(language, "Motivo de revisión: ", "Motivo da análise: ")
            + _review_reason(decision, language),
            "handoff": {key: value for key, value in packet.items() if key != "request_summary"},
            "policy_rules": list(decision.rule_ids),
        }
    if decision.decision == "eligible":
        expires_at = datetime.now(UTC) + timedelta(minutes=5)
        nonce = secrets.token_urlsafe(24)
        action_hash = _digest_proposal(principal.session_id, handle, decision, expires_at, nonce)
        conversation.proposal = ActionProposal(
            action_hash=action_hash,
            nonce=nonce,
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
            f"Você confirma o registro de uma contestação de {amount} em {row.merchant_name}? Isso abrirá um caso; não garante reembolso.",
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
    app.state.runtime.record("explain_status", handle=handle)
    if conversation.unfamiliar_charge and not is_dispute:
        transaction = _masked_transaction(handle, row)
        conversation.offer_handle = handle
        conversation.recognition_rounds = 0
        app.state.runtime.record("offer_dispute", handle=handle)
        return {
            "response_type": "offer_dispute",
            "outcome": "awaiting_dispute_decision",
            "reply": render_dispute_offer(
                TransactionView.model_validate(transaction),
                language=language,
                country=app.state.runtime.country,
            ),
            "transaction": transaction,
            "policy_rules": list(decision.rule_ids),
        }
    return {
        "response_type": "explain_status",
        "outcome": "explained",
        "reply": _explanation(language, row, decision.reason),
        "transaction": _masked_transaction(handle, row),
        "policy_rules": list(decision.rule_ids),
    }


app = create_app()
