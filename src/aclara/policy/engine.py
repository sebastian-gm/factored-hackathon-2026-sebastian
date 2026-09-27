"""Policy for explanation, dispute intake, and handoff."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite

from aclara.bank.repository import Transaction
from aclara.policy.rules import catalog, rule


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: str
    rule_ids: tuple[str, ...]
    reason: str
    version: str = catalog()[0]


def evaluate(transaction: Transaction, bank_clock: datetime, is_dispute: bool) -> PolicyDecision:
    age_days = (
        (bank_clock - timedelta(hours=6, microseconds=1)).date() - transaction.process_date
    ).days
    if age_days < 0 or age_days > int(rule("DATA-01").parameters["window_days"]):
        return PolicyDecision("handoff", ("DATA-01",), "outside_search_window")
    if transaction.transaction_status == "Pending":
        if age_days > int(rule("TXN-02").parameters["pending_days"]):
            return PolicyDecision("handoff", ("TXN-02",), "pending_over_limit")
        return PolicyDecision("explain", ("TXN-01",), "pending_authorization")
    if transaction.transaction_status == "Reversed":
        return PolicyDecision("explain", ("TXN-03",), "reversed")
    if transaction.transaction_status == "Declined":
        return PolicyDecision("explain", ("TXN-04",), "declined")
    if transaction.transaction_status != "Approved" or not isfinite(transaction.amount):
        return PolicyDecision("handoff", ("BRD-01",), "key_data_missing")
    if not is_dispute:
        return PolicyDecision("explain", ("DATA-01",), "approved_charge")
    if age_days > int(rule("DSP-01").parameters["intake_days"]):
        return PolicyDecision("handoff", ("DSP-01",), "outside_intake_window")
    if transaction.transaction_type == "Adjustment":
        return PolicyDecision("handoff", ("DSP-03",), "fee_or_adjustment")
    if transaction.transaction_type in {"Transfer", "Deposit"}:
        return PolicyDecision("handoff", ("DSP-04",), "unsupported_transaction_type")
    if transaction.transaction_type not in {"Purchase", "Withdrawal", "Payment"}:
        return PolicyDecision("handoff", ("DSP-02",), "unsupported_transaction_type")
    if transaction.currency != "USD":
        return PolicyDecision("handoff", ("BRD-01",), "verified_fx_required")
    limit = float(rule("DSP-07").parameters["limit_usd"])
    margin = float(rule("BRD-01").parameters["amount_margin"])
    if limit * (1 - margin) <= transaction.amount <= limit * (1 + margin) or int(
        rule("BRD-01").parameters["age_min_days"]
    ) <= age_days <= int(rule("BRD-01").parameters["age_max_days"]):
        return PolicyDecision("handoff", ("BRD-01",), "policy_boundary")
    if transaction.amount > limit:
        return PolicyDecision("handoff", ("DSP-07",), "amount_over_limit")
    return PolicyDecision("eligible", ("DSP-01", "DSP-02", "DSP-07"), "eligible")
