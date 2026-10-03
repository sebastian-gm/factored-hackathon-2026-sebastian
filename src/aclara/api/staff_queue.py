"""Explicit realm delegation to independently authenticated staff; masked packets only."""

from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from pydantic import Field, TypeAdapter, ValidationError

from aclara.agent.contracts import InterfaceModel
from aclara.agent.nlg.grounding import redact_for_model
from aclara.api.auth_models import Principal
from aclara.api.staff_contracts import DeskPacket, StaffAction
from aclara.handoff import queue
from aclara.ops.store import Scope


class RealmInvitation(InterfaceModel):
    invitation: str
    expires_at: datetime
    verified: bool = True


class RealmJoin(InterfaceModel):
    invitation: str = Field(min_length=20, max_length=160)


def scope(principal: Any) -> Scope:
    return Scope(principal.customer_id, principal.run_id, principal.session_id)


def customer_realm(principal: Any) -> str:
    reference = principal.judge_reference
    identity = (
        reference.digest + reference.binding_hash
        if reference
        else principal.run_id + ":" + principal.session_id
    )
    return hashlib.sha256(("handoff:" + identity).encode()).hexdigest()


STRUCTURAL_FIELDS = frozenset(
    {
        "handoff_id",
        "conversation_id",
        "id",
        "record_ref",
        "handle",
        "evidence_ref",
        "created_at",
        "sla_due_at",
        "verified_at",
        "dataset_version",
        "otp_at",
        "transaction_date",
    }
)


def masked(value: Any, field: str = "") -> Any:
    if isinstance(value, str):
        return value if field in STRUCTURAL_FIELDS else redact_for_model(value)
    if isinstance(value, list):
        return [masked(item, field) for item in value]
    if isinstance(value, dict):
        return {key: masked(item, key) for key, item in value.items()}
    return value


def packet_view(app: Any, packet: dict[str, Any]) -> dict[str, Any]:
    view = {k: v for k, v in packet.items() if k not in {"customer_id", "session_id"}}
    view.update(
        status="waiting",
        claimed_by=None,
        version=1,
        scope="current_realm",
        customer_display="Cliente demo",
        verified=True,
        sla_due_at=packet.get("sla_due_at")
        or (datetime.fromisoformat(packet["created_at"]) + timedelta(days=15)).isoformat(),
        evidence=[
            dict(
                id=f"{packet['handoff_id']}:fact:{i}",
                record_ref=fact["handle"],
                tool="scoped_transaction_read",
                verified_at=packet["created_at"],
                dataset_version=app.state.dataset_version,
            )
            for i, fact in enumerate(packet["verified_facts"])
        ],
        actions=[
            dict(action=action, status="verified", evidence_ref=packet["handoff_id"])
            for action in packet["actions_taken"]
            if action in {"create_handoff", "create_dispute"}
        ],
        # Queue permission never grants transcripts or banking APIs.
        transcript_ref=None,
        trace_ref=None,
    )
    if packet.get("freeze_outcome") in {"verified", "unverified"}:
        view["actions"].append(
            dict(
                action="freeze_card",
                status="verified" if packet["freeze_outcome"] == "verified" else "failed",
                evidence_ref=packet["handoff_id"],
            )
        )
    return DeskPacket.model_validate(masked(view)).model_dump(mode="json")


def publish(app: Any, principal: Any, packet: dict[str, Any]) -> None:
    store, realm = app.state.store, customer_realm(principal)
    expected = packet_view(app, packet)
    with store.transaction(scope(principal)), queue.context(store, realm, staff=False):
        queue.publish(store, realm, expected)
    with store.transaction(scope(principal)), queue.context(store, realm, staff=False):
        rows = queue.read(store, realm, packet["handoff_id"])
        if len(rows) != 1 or {
            k: v for k, v in rows[0].items() if k not in {"status", "claimed_by", "version"}
        } != {k: v for k, v in expected.items() if k not in {"status", "claimed_by", "version"}}:
            raise HTTPException(503, "Queue publication readback failed")


def invite(app: Any, principal: Any) -> RealmInvitation:
    source_scope = scope(principal)
    source_digest = principal.capability_digest
    if principal.judge_reference:
        reference = principal.judge_reference
        source_scope = app.state.judge_sessions.controller_scope(reference)
        source_digest = reference.digest
    token = f"{source_scope.run_id}.{source_scope.sid}.{secrets.token_urlsafe(24)}"
    key = "realm-invite:" + hashlib.sha256(token.encode()).hexdigest()
    expires = min(principal.expires_at, datetime.now(UTC) + timedelta(minutes=5))
    grant = dict(
        realm=customer_realm(principal),
        expires_at=expires.isoformat(),
        source_digest=source_digest,
        owner_expires_at=principal.expires_at.isoformat(),
        used_by=None,
    )
    with app.state.store.transaction(source_scope):
        app.state.idempotency[key] = grant
        app.state.store.audit(dict(action="handoff_realm_invitation"))
    with app.state.store.transaction(source_scope):
        if app.state.idempotency.get(key) != grant:
            raise HTTPException(503, "Invitation readback failed")
    return RealmInvitation(invitation=token, expires_at=expires)


def actor(principal: Any) -> str:
    return "agent_" + hashlib.sha256(principal.username.encode()).hexdigest()[:12]


def source_owner(app: Any, origin: Scope, digest: str) -> Principal:
    """Validate the live visit controller, without binding staff to a rotated child."""
    with app.state.store.transaction(origin):
        payload = app.state.store.get("sessions", digest)
    if payload is None:
        raise HTTPException(403, "Staff membership revoked")
    try:
        owner = TypeAdapter(Principal).validate_python(payload)
    except ValidationError:
        raise HTTPException(403, "Staff membership revoked") from None
    if scope(owner) != origin or owner.expires_at <= datetime.now(UTC):
        raise HTTPException(403, "Staff membership revoked")
    judges = app.state.judge_sessions
    if owner.judge_reference is not None:
        if (
            not app.state.settings.judge_access_enabled
            or judges is None
            or owner.judge_profile is not None
            or owner.judge_reference.digest != digest
            or re.fullmatch(r"[a-f0-9]{64}", owner.judge_active_digest) is None
        ):
            raise HTTPException(403, "Staff membership revoked")
        # The stored root tracks the current child digest/revision. Reuse the
        # same binding/configuration checks as customer authentication; never
        # reconstruct a token or grant this root any banking authority.
        try:
            judges.validate(replace(owner, capability_digest=owner.judge_active_digest))
        except HTTPException as error:
            if error.status_code not in {401, 403}:
                raise
            raise HTTPException(403, "Staff membership revoked") from None
    elif judges is not None and owner.username == judges.configuration.alias.username:
        # A legacy alias cannot survive the transition to picker controllers.
        raise HTTPException(403, "Staff membership revoked")
    return owner


def join(app: Any, principal: Any, body: RealmJoin) -> dict[str, bool]:
    if principal.role not in {"agent", "ops"} or principal.judge_reference is not None:
        raise HTTPException(403, "Separate staff sign-in required")
    store = app.state.store
    try:
        origin = app.state.sessions.auth_context(body.invitation)
    except KeyError:
        raise HTTPException(403, "Invitation unavailable") from None
    key = "realm-invite:" + hashlib.sha256(body.invitation.encode()).hexdigest()
    member = hashlib.sha256((principal.run_id + ":" + principal.session_id).encode()).hexdigest()
    with store.transaction(origin):
        grant = app.state.idempotency.get(key)
        if (
            not grant
            or datetime.fromisoformat(grant["expires_at"]) <= datetime.now(UTC)
            or grant["used_by"] not in {None, member}
        ):
            raise HTTPException(403, "Invitation unavailable")
        owner = source_owner(app, origin, grant["source_digest"])
        if grant["realm"] != customer_realm(owner):
            raise HTTPException(403, "Invitation unavailable")
        grant["used_by"] = member
        app.state.idempotency[key] = grant
    membership = dict(
        realm=grant["realm"],
        origin=asdict(origin),
        source_digest=grant["source_digest"],
        expires_at=min(principal.expires_at, owner.expires_at).isoformat(),
    )
    with store.transaction(scope(principal)):
        app.state.idempotency["staff-realm"] = membership
        store.audit(dict(action="join_handoff_realm", realm=grant["realm"]))
    if authorized_realm(app, principal) != grant["realm"]:
        raise HTTPException(503, "Membership readback failed")
    return dict(joined=True, verified=True)


def authorized_realm(app: Any, principal: Any) -> str | None:
    with app.state.store.transaction(scope(principal)):
        member = app.state.idempotency.get("staff-realm")
    if member is None:
        return None
    if (
        principal.role not in {"agent", "ops"}
        or principal.judge_reference is not None
        or datetime.fromisoformat(member["expires_at"]) <= datetime.now(UTC)
    ):
        raise HTTPException(403, "Staff membership expired")
    owner = source_owner(app, Scope(**member["origin"]), member["source_digest"])
    if member["realm"] != customer_realm(owner):
        raise HTTPException(403, "Staff membership revoked")
    return str(member["realm"])


def packets(app: Any, principal: Any, realm: str, key: str | None = None) -> list[DeskPacket]:
    with (
        app.state.store.transaction(scope(principal)),
        queue.context(app.state.store, realm, staff=True),
    ):
        return [DeskPacket.model_validate(item) for item in queue.read(app.state.store, realm, key)]


def claim(app: Any, principal: Any, realm: str, key: str, body: StaffAction) -> DeskPacket:
    store = app.state.store
    fingerprint = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
    cache_key = f"realm-claim:{realm}:{key}:{body.idempotency_key}"
    with store.transaction(scope(principal)), queue.context(store, realm, staff=True):
        previous = app.state.idempotency.get(cache_key)
        if previous:
            if previous["fingerprint"] != fingerprint:
                raise HTTPException(409, "Idempotency key changed")
            expected = DeskPacket.model_validate(previous["result"])
        else:
            rows = queue.read(store, realm, key)
            if not rows:
                raise HTTPException(404, "Handoff not found")
            try:
                queue.claim(store, realm, key, actor(principal), body.expected_version)
            except ValueError:
                raise HTTPException(409, "Handoff version changed") from None
            expected = DeskPacket.model_validate(queue.read(store, realm, key)[0])
            app.state.idempotency[cache_key] = dict(
                fingerprint=fingerprint, result=expected.model_dump(mode="json")
            )
    actual = packets(app, principal, realm, key)
    if (
        len(actual) != 1
        or actual[0].version < expected.version
        or actual[0].status != expected.status
        or actual[0].claimed_by != expected.claimed_by
    ):
        raise HTTPException(503, "Claim readback failed")
    with store.transaction(scope(principal)):
        store.audit(
            dict(action="verify_handoff_claim", handoff_id=key, claimed_by=actor(principal))
        )
    return actual[0]
