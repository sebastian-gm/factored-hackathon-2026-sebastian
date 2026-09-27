"""Fixture ledger access scoped by the authenticated session's customer."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Transaction:
    record_id: str
    customer_id: str
    product_id: str
    transaction_date: datetime
    process_date: date
    transaction_type: str
    amount: float
    currency: str
    merchant_name: str
    transaction_status: str


class TransactionRepository:
    def __init__(self, rows: tuple[Transaction, ...] | None = None) -> None:
        self._rows = rows if rows is not None else self._read_fixture()

    @staticmethod
    def _read_fixture() -> tuple[Transaction, ...]:
        repository_root = Path(__file__).resolve().parents[3]
        fixture = repository_root / "tests" / "fixtures" / "ledger" / "demo_transactions.csv"
        with fixture.open("r", encoding="utf-8", newline="") as stream:
            rows: list[Transaction] = []
            for row in csv.DictReader(stream):
                rows.append(
                    Transaction(
                        record_id=row["transaction_id"],
                        customer_id=row["customer_id"],
                        product_id=row["product_id"],
                        transaction_date=datetime.fromisoformat(row["transaction_date"]),
                        process_date=date.fromisoformat(row["process_date"]),
                        transaction_type=row["transaction_type"],
                        amount=float(row["amount"]),
                        currency=row["currency"],
                        merchant_name=row["merchant_name"],
                        transaction_status=row["transaction_status"],
                    )
                )
        return tuple(rows)

    def for_customer(self, customer_id: str, as_of: datetime) -> list[tuple[str, Transaction]]:
        candidates = [
            row
            for row in self._rows
            if row.customer_id == customer_id
            and as_of - timedelta(days=120) <= row.transaction_date < as_of
        ]
        return [(f"txn_{index}", row) for index, row in enumerate(candidates, start=1)]
