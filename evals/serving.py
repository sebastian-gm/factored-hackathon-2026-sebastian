"""Non-owner serving access for evaluation, with explicit isolated overlays."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from dotenv import dotenv_values
from psycopg.conninfo import make_conninfo

from aclara.bank.repository import Product, Transaction, TransactionRepository
from aclara.bank.serving import ServingRepository
from aclara.ops.store import Store
from aclara.settings import Settings


def open_serving() -> ServingRepository:
    values = dotenv_values(".env")
    dsn = os.getenv("EVAL_SERVING_DSN") or make_conninfo(
        host="127.0.0.1",
        port=values.get("POSTGRES_HOST_PORT") or "15432",
        dbname=values.get("POSTGRES_DB") or "aclara",
        user="aclara_app",
        password=values.get("OPS_APP_PASSWORD") or "",
    )
    return ServingRepository(Store(dsn), Settings().bank_clock)


class OverlayRepository(TransactionRepository):
    """Overlay records are authored counterfactuals, never written to bank tables.

    Every source read still passes through RLS. Declared overlay handles remain
    stable; additional organizer rows follow them in deterministic source order.
    """

    def __init__(self, source: ServingRepository, overlay: TransactionRepository, customer: str):
        if customer not in overlay.customers:
            raise ValueError("Overlay must include its bound customer's trusted attributes")
        self.source, self.overlay, self.customer = source, overlay, customer
        # Current API country guards read repository.customers. Expose only the
        # already bound customer; source reads still use the scoped merged view.
        self.customers = {customer: overlay.customers[customer]}
        self.dataset_version, self.loaded_at = source.dataset_version, source.loaded_at
        self.source_kind = "organizer_serving"

    def merged(self, customer: str, clock: datetime) -> TransactionRepository:
        if customer != self.customer:
            raise PermissionError("Overlay cannot change the bound customer")
        base = self.source.snapshot(customer, clock)
        products = {p.product_id: p for p in self.overlay.products}
        products.update({p.product_id: p for p in base.products if p.product_id not in products})
        return TransactionRepository(
            (*self.overlay._rows, *base._rows),
            products=tuple(products.values()),
            customers=tuple({**base.customers, **self.overlay.customers}.values()),
            policy_fields={**base.policy_fields, **self.overlay.policy_fields},
        )

    def for_customer(self, customer_id: str, as_of: datetime) -> list[tuple[str, Transaction]]:
        return self.merged(customer_id, as_of).for_customer(customer_id, as_of)

    def products_for_customer(self, customer_id: str) -> list[tuple[str, Product]]:
        return self.merged(customer_id, self.source.bank_clock).products_for_customer(customer_id)

    def context(self, row: Transaction, **kwargs: Any) -> Any:
        return self.merged(row.customer_id, self.source.bank_clock).context(row, **kwargs)
