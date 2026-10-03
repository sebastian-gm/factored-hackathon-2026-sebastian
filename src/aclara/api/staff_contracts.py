"""Additive staff projections; no raw identities, transcripts or model thinking."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from aclara.agent.contracts import HandoffView, InterfaceModel


class IdentityView(InterfaceModel):
    username: str
    language: Literal["es", "pt"]
    role: Literal["customer", "agent", "ops"]
    locale: Literal["es-MX", "es-CO", "es-AR", "pt-BR"]
    bank_clock: datetime
    judge_profiles_enabled: bool = False
    judge_profile_id: Literal["mx-es", "co-es", "ar-es", "pt"] | None = None
    profile_selection_required: bool = False
    demo_stories: list[Literal["explain", "ambiguous", "fraud"]] | None = None


class PersonaView(InterfaceModel):
    username: str
    label: str
    role: Literal["customer", "agent", "ops"]
    locale: Literal["es-MX", "es-CO", "es-AR", "pt-BR"]
    demo_stories: list[Literal["explain", "ambiguous", "fraud"]] = Field(default_factory=list)


class Evidence(InterfaceModel):
    id: str
    record_ref: str
    tool: str
    verified_at: datetime
    dataset_version: str


class ActionEvidence(InterfaceModel):
    action: str
    status: Literal["verified", "failed"]
    evidence_ref: str


class DeskPacket(HandoffView):
    request_summary: dict[str, str | dict[str, str]]
    conversation_id: str | None
    customer_display: str
    sla_due_at: datetime
    status: Literal["waiting", "claimed", "resolved"]
    claimed_by: str | None
    version: int
    evidence: list[Evidence]
    actions: list[ActionEvidence]
    verified: bool = True
    scope: Literal["current_workspace", "current_realm"] = "current_workspace"


class StaffAction(InterfaceModel):
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(pattern=r"^[A-Za-z0-9_-]{8,80}$")
    resolution: Literal["review_completed", "transferred"] | None = None


class LlmMetadata(InterfaceModel):
    provider: str
    model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    latency_ms: float
    route: str | None = None
    status: Literal["valid", "invalid_json", "provider_error", "refusal", "skipped"] | None = None
    attempt: int | None = Field(default=None, ge=1)
    judgments: dict[str, Any] | None = None


class TraceEvent(InterfaceModel):
    id: str
    stage: Literal["Understand", "Decide", "Act", "Verify", "Escalate"]
    state: str
    tool: str | None
    rules: list[str]
    verified: bool
    llm: LlmMetadata | None = None


class TraceView(InterfaceModel):
    conversation_id: str
    events: list[TraceEvent]
    policy_version: str
    scope: Literal["current_workspace"] = "current_workspace"


class QualityCheck(InterfaceModel):
    name: str
    passed: bool
    checked: int


class WorkspaceMetrics(InterfaceModel):
    source: Literal["current_workspace_operations"] = "current_workspace_operations"
    cases: int
    handoffs: int
    conversations: int
    execution_records: int
    observed_model_cost_usd: float
    sar: None = None
    unsafe_rate: None = None
    note: str = "Operational counts are not evaluation results; no gold denominator available."


class OpsView(InterfaceModel):
    dataset_version: str
    bank_clock: datetime
    loaded_at: datetime
    source_as_of: datetime
    source_kind: Literal["authored_fixture", "organizer_serving"] = "authored_fixture"
    quality: list[QualityCheck]
    metrics: WorkspaceMetrics
    conversation_ids: list[str]
    scope: Literal["current_workspace"] = "current_workspace"


class ResetProposal(InterfaceModel):
    action: Literal["reset_current_workspace"] = "reset_current_workspace"
    proposal_hash: str
    expires_at: datetime
    scope: Literal["current_workspace_operations_except_audit_auth"] = (
        "current_workspace_operations_except_audit_auth"
    )


class ResetConfirm(InterfaceModel):
    proposal_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed: bool


class ResetReceipt(InterfaceModel):
    receipt_id: str
    reset: bool
    verified: bool
    remaining_operations: int
    audit_retained: bool = True
