"""Rotated judge capabilities, gated by a durable, separately scoped controller."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import replace
from datetime import UTC, datetime
from typing import Literal

from fastapi import HTTPException
from pydantic import TypeAdapter

from aclara.agent.contracts import InterfaceModel
from aclara.api.auth_models import JudgeReference, Principal
from aclara.api.judge_access import PROFILE_LABELS, JudgeConfiguration
from aclara.api.staff_contracts import IdentityView
from aclara.ops.store import RecordMap, Scope, Store

ProfileId = Literal["mx-es", "co-es", "ar-es", "pt"]


class JudgeProfileView(InterfaceModel):
    profile_id: ProfileId
    label: str
    locale: Literal["es-MX", "es-CO", "es-AR", "pt-BR"]
    language: Literal["es", "pt"]
    demo_stories: list[Literal["explain", "ambiguous", "fraud"]]


class JudgeProfilesView(InterfaceModel):
    profiles: list[JudgeProfileView]
    active_profile_id: ProfileId | None
    expires_at: datetime


class JudgeSelectionView(InterfaceModel):
    access_token: str
    token_type: Literal["bearer"]
    verified: Literal[True]
    identity: IdentityView
    expires_at: datetime


def realm(username: str) -> str:
    return hashlib.sha256(username.encode()).hexdigest()[:12]


def visit_id(reference: JudgeReference) -> str:
    """Stable within one authenticated visit; independent shared-account logins differ."""
    return hashlib.sha256(reference.digest.encode()).hexdigest()[:24]


class JudgeSessions:
    def __init__(
        self,
        store: Store,
        sessions: RecordMap[Principal],
        configuration: JudgeConfiguration,
        dataset_version: str,
    ):
        self.store, self.sessions, self.configuration = store, sessions, configuration
        self.binding_hash = hashlib.sha256(
            (configuration.fingerprint + ":" + dataset_version).encode()
        ).hexdigest()
        self.adapter = TypeAdapter(Principal)

    def profile_realm(self, profile_id: str) -> str:
        return realm(self.configuration.alias.username + ":" + profile_id)

    def controller_scope(self, reference: JudgeReference) -> Scope:
        return Scope(self.configuration.alias.customer_id, reference.run_id, reference.session_id)

    def initialize(self, principal: Principal, token: str) -> Principal:
        digest = hashlib.sha256(token.encode()).hexdigest()
        reference = JudgeReference(
            principal.run_id, principal.session_id, digest, self.binding_hash
        )
        initialized = replace(
            principal, judge_reference=reference, judge_active_digest=digest, role="customer"
        )
        self.store.audit({"action": "judge_login", "profile_selection_required": True})
        return initialized

    def _reference(self, principal: Principal) -> JudgeReference:
        reference = principal.judge_reference
        if (
            reference is None
            or principal.username != self.configuration.alias.username
            or not hmac.compare_digest(reference.binding_hash, self.binding_hash)
            or reference.run_id.partition("_")[0] != realm(self.configuration.alias.username)
        ):
            raise HTTPException(401, "Judge session unavailable")
        return reference

    def _controller(self, principal: Principal) -> Principal:
        # Caller must have entered this reference's explicit auth scope.
        reference = self._reference(principal)
        payload = self.store.get("sessions", reference.digest)
        controller = self.adapter.validate_python(payload) if payload is not None else None
        if (
            controller is None
            or controller.judge_reference != reference
            or controller.run_id != reference.run_id
            or controller.session_id != reference.session_id
            or controller.customer_id != self.configuration.alias.customer_id
            or controller.username != self.configuration.alias.username
            or controller.role != "customer"
            or controller.judge_profile is not None
            or controller.expires_at <= datetime.now(UTC)
            or principal.expires_at != controller.expires_at
            or controller.judge_revision != principal.judge_revision
            or not hmac.compare_digest(controller.judge_active_digest, principal.capability_digest)
        ):
            raise HTTPException(401, "Judge session superseded or expired")
        return controller

    def validate(self, principal: Principal) -> Principal:
        reference = self._reference(principal)
        with self.store.transaction(self.controller_scope(reference)):
            controller = self._controller(principal)
        if principal.judge_profile is None:
            valid = (
                principal.run_id == reference.run_id
                and principal.session_id == reference.session_id
                and principal.customer_id == self.configuration.alias.customer_id
                and principal.role == "customer"
            )
        else:
            persona = self.configuration.profiles.get(principal.judge_profile)
            valid = (
                persona is not None
                and principal.customer_id == persona.customer_id
                and principal.role == persona.role
                and principal.locale == persona.locale
                and principal.run_id.partition("_")[0]
                == self.profile_realm(principal.judge_profile)
                and hmac.compare_digest(
                    principal.run_id.partition("_")[2].partition("_")[0], visit_id(reference)
                )
            )
        if not valid:
            raise HTTPException(401, "Judge scope unavailable")
        return controller

    def select(self, principal: Principal, profile_id: ProfileId) -> tuple[str, Principal]:
        controller = self.validate(principal)
        reference = self._reference(principal)
        persona = self.configuration.profiles[profile_id]
        run_id = (
            self.profile_realm(profile_id)
            + "_"
            + visit_id(reference)
            + "_"
            + secrets.token_urlsafe(18)
        )
        sid = secrets.token_urlsafe(18)
        token = f"{run_id}.{sid}.{secrets.token_urlsafe(32)}"
        digest = hashlib.sha256(token.encode()).hexdigest()
        child = replace(
            principal,
            run_id=run_id,
            session_id=sid,
            customer_id=persona.customer_id,
            role=persona.role,
            locale=persona.locale,
            otp_at=controller.otp_at,
            step_up_at=None,
            capability_digest="",
            judge_profile=profile_id,
            judge_active_digest="",
            judge_revision=controller.judge_revision + 1,
        )
        # No cross-customer transaction or elevated query. A child cannot
        # authenticate until its digest is independently published by the root.
        self.sessions[token] = child
        activated = False
        try:
            with self.store.transaction(self.controller_scope(reference)):
                current = self._controller(principal)
                updated = replace(
                    current,
                    judge_active_digest=digest,
                    judge_revision=child.judge_revision,
                )
                self.store.put(
                    "sessions", reference.digest, self.adapter.dump_python(updated, mode="json")
                )
                self.store.audit(
                    {
                        "action": "judge_profile_selected",
                        "from_profile": principal.judge_profile,
                        "profile_id": profile_id,
                        "generation": child.judge_revision,
                    }
                )
            activated = True
        finally:
            if not activated:
                # Best-effort caller cleanup remains fail-closed even if storage
                # becomes unavailable: the unpublished digest has no authority.
                self.sessions.pop(token, None)
        with self.store.transaction(self.sessions.auth_context(token)):
            saved = self.sessions.get(token)
            if saved != child:
                raise HTTPException(503, "Judge activation readback failed")
        self.validate(replace(child, capability_digest=digest))
        with self.store.transaction(self.controller_scope(reference)):
            self._controller(replace(child, capability_digest=digest))
            self.store.audit(
                {
                    "action": "judge_profile_verified",
                    "profile_id": profile_id,
                    "generation": child.judge_revision,
                }
            )
        return token, child

    def revoke(self, principal: Principal) -> dict[str, bool]:
        reference = self._reference(principal)
        with self.store.transaction(self.controller_scope(reference)):
            self._controller(principal)
            self.store.delete("sessions", reference.digest)
            self.store.audit({"action": "judge_logout", "profile_id": principal.judge_profile})
        # Never reconstruct a plaintext capability to delete a child.
        # Delete by digest under its explicit selected scope instead.
        child_scope = Scope(principal.customer_id, principal.run_id, principal.session_id)
        with self.store.transaction(child_scope):
            self.store.delete("sessions", principal.capability_digest)
        with self.store.transaction(self.controller_scope(reference)):
            if self.store.get("sessions", reference.digest) is not None:
                raise HTTPException(503, "Judge revocation readback failed")
        return {"signed_out": True, "verified": True}

    def views(self, stories: dict[str, list[str]]) -> list[dict[str, object]]:
        return [
            {
                "profile_id": key,
                "label": PROFILE_LABELS[key],
                "locale": persona.locale,
                "language": "pt" if persona.locale == "pt-BR" else "es",
                "demo_stories": list(stories.get(persona.username, [])),
            }
            for key, persona in self.configuration.profiles.items()
        ]
