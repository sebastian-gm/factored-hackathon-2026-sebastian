"""Read the promoted organizer ledger through the non-owner, forced-RLS pool.

No source file or fixture fallback exists here. Only the authenticated customer's
120-day projection is materialized; policy-only fields never enter public views.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite
from typing import TYPE_CHECKING, Any

from aclara.bank.repository import Customer, Product, Transaction, TransactionRepository
from aclara.handoff.routing import AgentDirectory, ServiceAgent
from aclara.ops.store import Scope, Store

if TYPE_CHECKING:
    from aclara.policy.engine import PolicyContext


@dataclass(frozen=True)
class Persona:
    username: str
    customer_id: str
    locale: str
    role: str


class ServingRepository(TransactionRepository):
    def __init__(self, store: Store, bank_clock: datetime):
        if store.pool is None:
            raise ValueError("Serving requires non-owner Postgres storage")
        self.store, self.bank_clock = store, bank_clock
        self.source_kind = "organizer_serving"
        with store.transaction(Scope("", "", "")):
            connection = store._unit().connection
            assert connection is not None
            connection.execute("SELECT pg_advisory_xact_lock_shared(61928471)")
            row = connection.execute(
                "SELECT identity,loaded_at FROM meta.serving_state WHERE singleton"
            ).fetchone()
            if row is None:
                raise ValueError("Promoted serving state is absent")
            if datetime.fromisoformat(row[0]["bank_clock"].replace("Z", "+00:00")) != bank_clock:
                raise ValueError("Serving bank clock differs from runtime")
            self.dataset_version, self.loaded_at = row[0]["dataset_version"], row[1]
            self.identity: dict[str, str] = row[0]

    def personas(self) -> list[Persona]:
        with self.store.transaction(Scope("", "", "")):
            connection = self.store._unit().connection
            assert connection is not None
            rows = connection.execute(
                "SELECT username,customer_id,locale,role FROM reference.demo_personas "
                "WHERE dataset_version=%s ORDER BY username",
                (self.dataset_version,),
            ).fetchall()
        if not rows:
            raise ValueError("Organizer demo personas have not been bound")
        return [Persona(*row) for row in rows]

    def directory(self) -> AgentDirectory:
        with self.store.transaction(Scope("", "", "")):
            pg = self.store._unit().connection
            assert pg is not None
            rows = pg.execute(
                "SELECT agent_id,agent_status,agent_type,languages,specialty,total_monthly_interactions "
                "FROM bank.service_agents ORDER BY agent_id"
            ).fetchall()
        return AgentDirectory(
            tuple(
                ServiceAgent(
                    "agent_" + hashlib.sha256(r[0].encode()).hexdigest()[:24],
                    r[1],
                    r[2],
                    r[3],
                    r[4],
                    r[5],
                )
                for r in rows
            )
        )

    def snapshot(self, customer_id: str, as_of: datetime) -> TransactionRepository:
        if as_of != self.bank_clock:
            raise ValueError("Runtime clock differs from promoted serving window")
        current = self.store.current.get()
        if current and current.scope.customer_id != customer_id:
            raise PermissionError("Ledger customer differs from operational scope")
        scope = current.scope if current else Scope(customer_id, "ledger", "ledger")
        with self.store.transaction(scope):
            pg = self.store._unit().connection
            assert pg is not None
            pg.execute("SELECT pg_advisory_xact_lock_shared(61928471)")
            state = pg.execute("SELECT identity FROM meta.serving_state WHERE singleton").fetchone()
            if state is None or state[0] != self.identity:
                raise ValueError("Serving version changed; restart the runtime")
            customers = pg.execute(
                "SELECT c.customer_id,c.customer_status,c.country,c.segment,"
                "COALESCE(h.complaint_count_90d,0) FROM bank.customers c "
                "LEFT JOIN bank.complaint_history_agg h USING(customer_id) "
                "WHERE c.customer_id=%s",
                (customer_id,),
            ).fetchall()
            products = pg.execute(
                "SELECT product_id,customer_id,product_type,product_status FROM bank.products "
                'WHERE customer_id=%s ORDER BY product_id COLLATE "C"',
                (customer_id,),
            ).fetchall()
            records = pg.execute(
                "SELECT t.transaction_id,t.customer_id,t.product_id,t.transaction_date,"
                "t.process_date,t.transaction_type,t.amount,t.currency,t.merchant_name,"
                "t.transaction_status,t.amount_usd_recomputed,t.fraud_score,t.fx_nearest_prior "
                "FROM bank.transactions t JOIN bank.products p "
                "ON p.product_id=t.product_id AND p.customer_id=t.customer_id "
                "WHERE t.customer_id=%s AND t.transaction_date >= %s AND t.transaction_date < %s "
                'ORDER BY t.transaction_id COLLATE "C"',
                (customer_id, as_of - timedelta(days=120), as_of),
            ).fetchall()
        rows, fields = [], {}
        for r in records:
            rows.append(
                Transaction(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8] or "", r[9])
            )
            fields[r[0]] = {
                "amount_usd": r[10],
                "fraud_score": r[11] or 0,
                "fx_nearest_prior": r[12],
                "missing_fields": ("merchant_name",) if not r[8] else (),
            }
        return TransactionRepository(
            tuple(rows),
            customers=tuple(Customer(*c) for c in customers),
            products=tuple(
                Product(p[0], p[1], p[2].replace("_", " ").title(), p[3]) for p in products
            ),
            policy_fields=fields,
        )

    def for_customer(self, customer_id: str, as_of: datetime) -> list[tuple[str, Transaction]]:
        return self.snapshot(customer_id, as_of).for_customer(customer_id, as_of)

    def products_for_customer(self, customer_id: str) -> list[tuple[str, Product]]:
        return self.snapshot(customer_id, self.bank_clock).products_for_customer(customer_id)

    def context(
        self, row: Transaction, *, cases_7_days: int = 0, existing_case_id: str | None = None
    ) -> PolicyContext:
        return self.snapshot(row.customer_id, self.bank_clock).context(
            row, cases_7_days=cases_7_days, existing_case_id=existing_case_id
        )

    def ready(self) -> bool:
        # Startup and readiness fail closed if the promoted clock/version has changed.
        current = ServingRepository(self.store, self.bank_clock)
        return current.identity == self.identity


def demo_story_mappings(
    ledger: TransactionRepository, personas: dict[str, Persona], clock: datetime
) -> dict[str, list[str]]:
    """Owner-approved routing hints, enabled only from trusted scoped ledger facts."""
    stories: dict[str, list[str]] = {}
    for username, expected_locale in (("demo.es.mx", "es-MX"), ("demo.pt.br", "pt-BR")):
        persona = personas.get(username)
        if persona is None or persona.locale != expected_locale or persona.role != "ops":
            continue
        rows = ledger.for_customer(persona.customer_id, clock)
        displayable = [
            row
            for _, row in rows
            if isfinite(row.amount)
            and row.amount >= 0
            and row.merchant_name
            and row.transaction_status in {"Approved", "Pending", "Reversed", "Declined"}
        ]
        available = []
        if username == "demo.es.mx":
            if displayable:
                available.append("explain")
            if any(
                p.product_type in {"Credit Card", "Debit Card"} and p.status == "Active"
                for _, p in ledger.products_for_customer(persona.customer_id)
            ):
                available.append("fraud")
        elif len(displayable) >= 2:
            available.append("ambiguous")
        stories[username] = available
    return stories


def persona_views(
    personas: dict[str, Persona], stories: dict[str, list[str]] | None = None
) -> list[dict[str, Any]]:
    return [
        {
            "username": p.username,
            "label": p.username,
            "locale": p.locale,
            "role": p.role,
            "demo_stories": (stories or {}).get(p.username, []),
        }
        for p in personas.values()
    ]
