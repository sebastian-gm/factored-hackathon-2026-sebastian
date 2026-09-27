"""Pure synthetic policy decisions; identity and writes remain API responsibilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import isfinite
from typing import Any

from aclara.bank.repository import Transaction
from aclara.policy.rules import catalog, rule


@dataclass(frozen=True, slots=True)
class PolicyContext:
    customer_status: str = "Active"
    product_status: str = "Active"
    product_type: str = "Debit Card"
    product_owned: bool = True
    fraud_score: float = 0
    lost_or_stolen: bool = False
    cases_7_days: int = 0
    complaints_90_days: int = 0
    amount_usd: float | None = None
    fx_nearest_prior: bool = False
    missing_fields: tuple[str, ...] = ()
    existing_case_id: str | None = None

    @property
    def card(self) -> bool:
        return self.product_type in {"Credit Card", "Debit Card"}


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: str
    rule_ids: tuple[str, ...]
    reason: str
    version: str = catalog()[0]
    inputs_snapshot: dict[str, Any] = field(default_factory=dict)
    review_flag: bool = False


def evaluate(
    transaction: Transaction,
    bank_clock: datetime,
    is_dispute: bool,
    context: PolicyContext | None = None,
) -> PolicyDecision:
    facts = context or PolicyContext()
    age_days = (
        (bank_clock - timedelta(hours=6, microseconds=1)).date() - transaction.process_date
    ).days
    usd = transaction.amount if transaction.currency == "USD" else facts.amount_usd
    snapshot = {
        "age_days": age_days,
        "status": transaction.transaction_status,
        "transaction_type": transaction.transaction_type,
        "amount_usd": usd if usd is not None and isfinite(usd) else None,
        "customer_status": facts.customer_status,
        "product_status": facts.product_status,
        "product_type": facts.product_type,
        "owned": facts.product_owned,
        "fraud_flag": fraud_required(facts),
        "complaints_90_days": facts.complaints_90_days,
        "missing_fields": list(facts.missing_fields),
        "fx_nearest_prior": facts.fx_nearest_prior,
    }

    def result(
        decision: str, ids: tuple[str, ...], reason: str, review: bool = False
    ) -> PolicyDecision:
        return PolicyDecision(decision, ids, reason, inputs_snapshot=snapshot, review_flag=review)

    if not facts.product_owned:
        return result("handoff", ("DATA-01",), "product_ownership_unverified")
    missing = list(facts.missing_fields)
    if not isfinite(transaction.amount):
        missing.append("amount")
    if transaction.transaction_status not in {"Approved", "Pending", "Reversed", "Declined"}:
        missing.append("status")
    if missing:
        return result("handoff", ("BRD-01",), "missing:" + ",".join(sorted(set(missing))))
    if age_days < 0 or age_days > int(rule("DATA-01").parameters["window_days"]):
        return result("handoff", ("DATA-01",), "outside_search_window")
    if facts.customer_status in {"Suspended", "Closed"} or facts.product_status in {
        "Closed",
        "Blocked",
    }:
        return result("handoff", ("DSP-05",), "restricted_customer_or_product")
    if fraud_required(facts):
        return result("freeze_offer" if facts.card else "handoff", ("FRD-01",), "fraud_review")
    if is_dispute and facts.existing_case_id:
        return result("status", ("DSP-06",), "existing_case")
    if transaction.transaction_status == "Pending":
        if age_days > int(rule("TXN-02").parameters["pending_days"]):
            return result("handoff", ("TXN-02",), "pending_over_limit")
        return result("explain", ("TXN-01",), "pending_authorization")
    if transaction.transaction_status == "Reversed":
        return result("explain", ("TXN-03",), "reversed")
    if transaction.transaction_status == "Declined":
        return result("explain", ("TXN-04",), "declined")
    if not is_dispute:
        return result("explain", ("DATA-01",), "approved_charge")
    if age_days > int(rule("DSP-01").parameters["intake_days"]):
        return result("handoff", ("DSP-01",), "outside_intake_window")
    if transaction.transaction_type == "Adjustment":
        return result("handoff", ("DSP-03",), "fee_or_adjustment")
    if transaction.transaction_type in {"Transfer", "Deposit"}:
        return result("handoff", ("DSP-04",), "unsupported_transaction_type")
    if transaction.transaction_type not in {"Purchase", "Withdrawal", "Payment"}:
        return result("handoff", ("DSP-02",), "unsupported_transaction_type")
    if usd is None or not isfinite(usd) or facts.fx_nearest_prior:
        return result(
            "handoff",
            ("BRD-01",),
            "fx_nearest_prior" if facts.fx_nearest_prior else "missing:amount_usd",
        )
    limit = float(rule("DSP-07").parameters["limit_usd"])
    margin = float(rule("BRD-01").parameters["amount_margin"])
    if limit * (1 - margin) <= usd <= limit * (1 + margin) or int(
        rule("BRD-01").parameters["age_min_days"]
    ) <= age_days <= int(rule("BRD-01").parameters["age_max_days"]):
        return result("handoff", ("BRD-01",), "policy_boundary")
    if usd > limit:
        return result("handoff", ("DSP-07",), "amount_over_limit")
    flagged = facts.complaints_90_days >= int(rule("ESC-05").parameters["complaints_90_days_gte"])
    ids = ("DSP-01", "DSP-02", "DSP-07") + (("ESC-05",) if flagged else ())
    return result("eligible", ids, "eligible", flagged)


def fraud_required(facts: PolicyContext) -> bool:
    return (
        facts.fraud_score > float(rule("FRD-01").parameters["fraud_score_gt"])
        or facts.lost_or_stolen
        or facts.cases_7_days >= int(rule("FRD-01").parameters["cases_7_days_gte"])
    )
