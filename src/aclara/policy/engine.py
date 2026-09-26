"""Policy for explanation, dispute intake, and handoff."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aclara.bank.repository import Transaction


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: str
    rule_ids: tuple[str, ...]
    reason: str


def evaluate(transaction: Transaction, bank_clock: datetime, is_dispute: bool) -> PolicyDecision:
    if transaction.transaction_status == "Pending":
        return PolicyDecision("explain", ("TXN-01",), "pending_authorization")
    if transaction.transaction_status == "Reversed":
        return PolicyDecision("explain", ("TXN-03",), "reversed")
    if transaction.transaction_status == "Declined":
        return PolicyDecision("explain", ("TXN-04",), "declined")
    if not is_dispute:
        return PolicyDecision("explain", ("TXN-00",), "approved_charge")
    age_days = (bank_clock.date() - transaction.process_date).days
    if age_days < 0 or age_days > 120:
        return PolicyDecision("handoff", ("DATA-01",), "outside_search_window")
    if age_days > 90:
        return PolicyDecision("handoff", ("DSP-01",), "outside_intake_window")
    if transaction.transaction_type == "Adjustment":
        return PolicyDecision("handoff", ("DSP-03",), "fee_or_adjustment")
    if transaction.transaction_type in {"Transfer", "Deposit"}:
        return PolicyDecision("handoff", ("DSP-04",), "unsupported_transaction_type")
    if transaction.transaction_type not in {"Purchase", "Withdrawal", "Payment"}:
        return PolicyDecision("handoff", ("DSP-02",), "unsupported_transaction_type")
    if transaction.amount > 1000:
        return PolicyDecision("handoff", ("DSP-07",), "amount_over_limit")
    return PolicyDecision("eligible", ("DSP-01", "DSP-02", "DSP-07"), "eligible")
