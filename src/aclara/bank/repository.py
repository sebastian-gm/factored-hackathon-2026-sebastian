"""Fixture ledger access scoped by the authenticated session's customer."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aclara.policy.engine import PolicyContext


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


@dataclass(frozen=True, slots=True)
class Product:
    product_id: str
    customer_id: str
    product_type: str = "Debit Card"
    status: str = "Active"


@dataclass(frozen=True, slots=True)
class Customer:
    customer_id: str
    status: str = "Active"
    country: str = "MX"
    segment: str = "Basic"
    complaints_90_days: int = 0


class TransactionRepository:
    def __init__(
        self,
        rows: tuple[Transaction, ...] | None = None,
        *,
        products: tuple[Product, ...] | None = None,
        customers: tuple[Customer, ...] | None = None,
        policy_fields: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._rows = rows if rows is not None else self._read_fixture()
        self.products = (
            products
            if products is not None
            else tuple(
                Product(product_id, customer_id)
                for customer_id, product_id in dict.fromkeys(
                    (r.customer_id, r.product_id) for r in self._rows
                )
            )
        )
        self.customers = {
            c.customer_id: c
            for c in (
                customers
                or tuple(
                    Customer(customer_id)
                    for customer_id in dict.fromkeys(r.customer_id for r in self._rows)
                )
            )
        }
        self.policy_fields = policy_fields or {}

    def products_for_customer(self, customer_id: str) -> list[tuple[str, Product]]:
        return [
            (f"prod_{i}", product)
            for i, product in enumerate(
                (p for p in self.products if p.customer_id == customer_id), start=1
            )
        ]

    def context(
        self, row: Transaction, *, cases_7_days: int = 0, existing_case_id: str | None = None
    ) -> PolicyContext:
        from aclara.policy.engine import PolicyContext

        product = next(
            (
                p
                for p in self.products
                if p.product_id == row.product_id and p.customer_id == row.customer_id
            ),
            None,
        )
        customer = self.customers.get(row.customer_id)
        return PolicyContext(
            **{
                **self.policy_fields.get(row.record_id, {}),
                "customer_status": customer.status if customer else "Closed",
                "product_status": product.status if product else "Closed",
                "product_type": product.product_type if product else "Unknown",
                "product_owned": product is not None,
                "complaints_90_days": customer.complaints_90_days if customer else 0,
                "cases_7_days": cases_7_days,
                "existing_case_id": existing_case_id,
            }
        )

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
            and any(
                p.product_id == row.product_id and p.customer_id == customer_id
                for p in self.products
            )
            and as_of - timedelta(days=120) <= row.transaction_date < as_of
        ]
        return [(f"txn_{index}", row) for index, row in enumerate(candidates, start=1)]
