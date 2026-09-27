"""Pure synthetic policy decisions; identity and writes remain API responsibilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import isfinite
from typing import Any

from aclara.bank.repository import Transaction
from aclara.policy.reasons import handoff_reasons
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
    if age_days < 0 or age_days > int(rule("DATA-01").parameters["window_days"]):
        return result("handoff", ("DATA-01",), "outside_search_window")
    restricted = facts.customer_status in {"Suspended", "Closed"} or facts.product_status in {
        "Closed",
        "Blocked",
    }
    fraud = fraud_required(facts)
    if restricted:
        reasons = ["DSP-05", *(["FRD-01"] if fraud else [])]
        return result("handoff", handoff_reasons(reasons), "restricted_customer_or_product")
    if fraud:
        return result(
            "freeze_offer" if facts.card else "handoff", handoff_reasons("FRD-01"), "fraud_review"
        )
    if is_dispute and facts.existing_case_id:
        return result("status", ("DSP-06",), "existing_case")

    missing = list(facts.missing_fields)
    if not isfinite(transaction.amount):
        missing.append("amount")
    if transaction.transaction_status not in {"Approved", "Pending", "Reversed", "Declined"}:
        missing.append("status")
    if not transaction.transaction_type:
        missing.append("transaction_type")
    snapshot["missing_fields"] = sorted(set(missing))
    type_rule = (
        "DSP-03"
        if transaction.transaction_type == "Adjustment"
        else "DSP-04"
        if transaction.transaction_type in {"Transfer", "Deposit"}
        else "DSP-02"
        if transaction.transaction_type not in {"Purchase", "Withdrawal", "Payment", ""}
        else None
    )
    # Display defects cannot be explained away. On dispute review, retain every
    # other cause whose input is still trustworthy instead of returning early.
    if missing and not is_dispute:
        return result("handoff", ("BRD-01",), "missing:" + ",".join(sorted(set(missing))))
    if not missing and transaction.transaction_status == "Pending":
        if age_days > int(rule("TXN-02").parameters["pending_days"]):
            return result("handoff", ("TXN-02",), "pending_over_limit")
        return result("explain", ("TXN-01",), "pending_authorization")
    if not missing and transaction.transaction_status == "Reversed":
        return result("explain", ("TXN-03",), "reversed")
    if not missing and transaction.transaction_status == "Declined":
        return result("explain", ("TXN-04",), "declined")
    if not is_dispute:
        return result("explain", ("DATA-01",), "approved_charge")

    # Establish every applicable review cause before selecting routing precedence.
    reasons = ["BRD-01"] if missing else []
    reason = "missing:" + ",".join(sorted(set(missing))) if missing else "eligible"
    if type_rule:
        reasons.append(type_rule)
        if not missing:
            reason = (
                "fee_or_adjustment" if type_rule == "DSP-03" else "unsupported_transaction_type"
            )
    invalid_fx = usd is None or not isfinite(usd) or facts.fx_nearest_prior
    if invalid_fx:
        reasons.append("BRD-01")
        if not type_rule and not missing:
            reason = "fx_nearest_prior" if facts.fx_nearest_prior else "missing:amount_usd"
    age_known = not {"date", "process_date", "transaction_date"}.intersection(missing)
    if age_known and age_days > int(rule("DSP-01").parameters["intake_days"]):
        reasons.append("DSP-01")
        if not type_rule and not invalid_fx and not missing:
            reason = "outside_intake_window"
    elif age_known and (
        int(rule("BRD-01").parameters["age_min_days"])
        <= age_days
        <= int(rule("BRD-01").parameters["age_max_days"])
    ):
        reasons.extend(("BRD-01", "DSP-01"))
        if not type_rule and not invalid_fx and not missing:
            reason = "policy_boundary"
    limit = float(rule("DSP-07").parameters["limit_usd"])
    margin = float(rule("BRD-01").parameters["amount_margin"])
    if usd is not None and isfinite(usd) and not facts.fx_nearest_prior and "amount" not in missing:
        if limit * (1 - margin) <= usd <= limit * (1 + margin):
            reasons.extend(("BRD-01", "DSP-07"))
            if reason == "eligible":
                reason = "policy_boundary"
        elif usd > limit:
            reasons.append("DSP-07")
            if reason == "eligible":
                reason = "amount_over_limit"
    if reasons:
        return result("handoff", handoff_reasons(reasons), reason)
    flagged = facts.complaints_90_days >= int(rule("ESC-05").parameters["complaints_90_days_gte"])
    ids = ("DSP-01", "DSP-02", "DSP-07") + (("ESC-05",) if flagged else ())
    return result("eligible", ids, "eligible", flagged)


def fraud_required(facts: PolicyContext) -> bool:
    return (
        facts.fraud_score > float(rule("FRD-01").parameters["fraud_score_gt"])
        or facts.lost_or_stolen
        or facts.cases_7_days >= int(rule("FRD-01").parameters["cases_7_days_gte"])
    )
