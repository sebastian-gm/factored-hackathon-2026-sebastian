"""Stable typed contracts shared by the agent, API, and evaluation lanes."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Intent(StrEnum):
    CHARGE_INQUIRY = "charge_inquiry"
    DISPUTE_CHARGE = "dispute_charge"
    HUMAN_REQUEST = "human_request"
    FRAUD = "card_lost_or_fraud"
    FEE_DISPUTE = "fee_dispute"
    OUT_OF_SCOPE = "out_of_scope"


class InterfaceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NluFrame(InterfaceModel):
    language: Literal["es", "pt"]
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)


class TransactionView(InterfaceModel):
    handle: str
    transaction_date: datetime
    transaction_type: str
    amount: float = Field(ge=0.0)
    currency: str
    merchant: str | None
    status: str


class ProposalView(InterfaceModel):
    action: Literal["create_dispute"]
    proposal_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expires_at: datetime
    policy_rules: list[str]


class HandoffRoute(InterfaceModel):
    queue: str
    language: Literal["es", "pt"]
    fallback_used: bool
    requested_queue: str | None = None
    specialty_fallback: bool = False
    language_fallback: bool = False
    assigned_agent_ref: str | None = None
    routing_explanation: str | None = None
    assignment_pending: bool = False


class HandoffView(InterfaceModel):
    schema_version: Literal["1.0"]
    handoff_id: str
    created_at: datetime
    reason_codes: list[str]
    primary_reason: str | None = None
    priority: Literal["normal", "high"]
    route: HandoffRoute
    verified_facts: list[TransactionView]
    actions_taken: list[str]
    open_questions: list[str]
    freeze_outcome: str | None = None
    conversation_id: str | None = None
    customer: dict[str, Any] | None = None
    customer_statements: list[dict[str, Any]] | None = None
    policy_evaluations: list[dict[str, str]] | None = None
    risk_flags: list[str] | None = None
    suggested_next_steps: list[str] | None = None
    sla_due_at: datetime | None = None
    transcript_ref: str | None = None
    trace_ref: str | None = None

    @model_validator(mode="after")
    def validate_primary_reason(self) -> HandoffView:
        if self.primary_reason is not None and self.primary_reason not in self.reason_codes:
            raise ValueError("primary_reason must occur in reason_codes")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason_codes must be deduplicated")
        return self


class DisputeCaseView(InterfaceModel):
    case_id: str
    transaction_handle: str
    status: str
    policy_rules: list[str]
    created_at: datetime
    review_flag: bool = False


class ProductView(InterfaceModel):
    handle: str
    product_type: str
    status: str


class ResponsePlan(InterfaceModel):
    """Validated API action plan; required detail depends on response_type."""

    response_type: Literal[
        "cancelled",
        "offer_human",
        "abstain",
        "choose_transaction",
        "clarify",
        "report_case",
        "confirm_action",
        "explain_status",
        "offer_dispute",
        "report_status",
        "refuse",
    ]
    outcome: Literal[
        "cancelled",
        "handoff_created",
        "abstained_out_of_scope",
        "choose_transaction",
        "clarification",
        "dispute_filed",
        "dispute_proposed",
        "explained",
        "awaiting_dispute_decision",
        "status_reported",
        "refused_security",
    ]
    reply: str
    transaction: TransactionView | None = None
    candidates: list[TransactionView] | None = None
    proposal: ProposalView | None = None
    handoff: HandoffView | None = None
    case: DisputeCaseView | None = None
    verified: bool | None = None
    policy_rules: list[str] | None = None
    freeze_offer: list[ProductView] | None = None
    session_ended: bool = False

    @model_validator(mode="after")
    def validate_response_shape(self) -> ResponsePlan:
        expected_outcomes = {
            "cancelled": "cancelled",
            "offer_human": "handoff_created",
            "abstain": "abstained_out_of_scope",
            "choose_transaction": "choose_transaction",
            "clarify": "clarification",
            "report_case": "dispute_filed",
            "confirm_action": "dispute_proposed",
            "explain_status": "explained",
            "offer_dispute": "awaiting_dispute_decision",
            "report_status": "status_reported",
            "refuse": "refused_security",
        }
        if self.outcome != expected_outcomes[self.response_type]:
            raise ValueError(
                f"{self.response_type} requires outcome {expected_outcomes[self.response_type]}"
            )
        required: dict[str, tuple[str, ...]] = {
            "choose_transaction": ("candidates",),
            "report_case": ("case", "verified"),
            "report_status": ("case", "verified"),
            "confirm_action": ("transaction", "proposal"),
            "explain_status": ("transaction",),
            "offer_dispute": ("transaction",),
            "offer_human": ("handoff",),
        }
        missing = [
            name for name in required.get(self.response_type, ()) if getattr(self, name) is None
        ]
        if missing:
            raise ValueError(f"{self.response_type} requires {', '.join(missing)}")
        if self.response_type in {"report_case", "report_status"} and self.verified is not True:
            raise ValueError("report_case requires a successful read-back")
        return self
