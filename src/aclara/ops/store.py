"""Typed operational maps with explicit transactions and bounded Postgres pooling."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterator, MutableMapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from psycopg import Connection, sql
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool
from pydantic import TypeAdapter

TABLES = frozenset(
    {
        "cases",
        "card_states",
        "handoffs",
        "conversations",
        "turns",
        "execution_records",
        "idempotency_keys",
        "otp_challenges",
        "sessions",
        "demo_identities",
    }
)
CUSTOMER_TABLES = frozenset({"customer_cases", "customer_card_states"})
CLOSED_CASE_STATUSES = frozenset({"closed", "resolved", "cancelled", "rejected"})


def open_case(payload: dict[str, Any]) -> bool:
    return (
        payload.get("_canonical", True)
        and payload.get("status", "received") not in CLOSED_CASE_STATUSES
    )


@dataclass(frozen=True)
class Scope:
    customer_id: str
    run_id: str
    sid: str


@dataclass
class Unit:
    scope: Scope
    connection: Connection[Any] | None = None
    cache: dict[tuple[str, str], tuple[Any, Any, Any]] = field(default_factory=dict)
    customer_realm: str | None = None


class Store:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn
        self.pool: ConnectionPool[Connection[Any]] | None = None
        if dsn is not None:
            self.pool = ConnectionPool(
                dsn, min_size=0, max_size=4, open=True, kwargs={"autocommit": True}, timeout=5
            )
        self.memory: dict[tuple[Scope, str, str], Any] = {}
        self.lock = RLock()
        self.current: ContextVar[Unit | None] = ContextVar("ops_unit", default=None)

    @contextmanager
    def transaction(self, scope: Scope) -> Iterator[None]:
        existing = self.current.get()
        if existing:
            if existing.scope != scope:
                raise RuntimeError("Cannot change authorization context inside a transaction")
            yield
            return
        with self.lock:
            if self.pool is None:
                before = dict(self.memory)
                token = self.current.set(Unit(scope))
                try:
                    yield
                    self._flush()
                except BaseException:
                    self.memory = before
                    raise
                finally:
                    self.current.reset(token)
            else:
                with self.pool.connection() as connection, connection.transaction():
                    privileged = connection.execute(
                        "SELECT rolsuper OR rolbypassrls OR pg_has_role(current_user,'aclara_owner','MEMBER') FROM pg_roles WHERE rolname=current_user"
                    ).fetchone()
                    if not privileged or privileged[0]:
                        raise PermissionError("Operational runtime must use the non-owner API role")
                    for name, value in (
                        ("app.customer_id", scope.customer_id),
                        ("app.run_id", scope.run_id),
                        ("app.sid", scope.sid),
                    ):
                        connection.execute("SELECT set_config(%s,%s,true)", (name, value))
                    # Serialize one session's read/modify/write cycle across replicas.
                    connection.execute(
                        "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                        (json.dumps([scope.customer_id, scope.run_id, scope.sid]),),
                    )
                    token = self.current.set(Unit(scope, connection))
                    try:
                        yield
                        self._flush()
                    finally:
                        self.current.reset(token)

    def _unit(self) -> Unit:
        unit = self.current.get()
        if unit is None:
            raise RuntimeError("Operational access requires an explicit scoped transaction")
        return unit

    def _flush(self) -> None:
        unit = self._unit()
        for (table, key), (value, original, adapter) in list(unit.cache.items()):
            payload = adapter.dump_python(value, mode="json")
            if payload != original:
                self.put(table, key, payload)

    def customer_context(self, realm: str) -> None:
        unit = self._unit()
        if not realm or (unit.customer_realm is not None and unit.customer_realm != realm):
            raise PermissionError("Invalid customer realm")
        if unit.customer_realm is None:
            unit.customer_realm = realm
            if unit.connection is not None:
                unit.connection.execute("SELECT set_config('app.customer_realm',%s,true)", (realm,))
                unit.connection.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                    (json.dumps(["customer", unit.scope.customer_id, realm]),),
                )

    def _storage_scope(self, table: str) -> Scope:
        unit = self._unit()
        if table in CUSTOMER_TABLES:
            if unit.customer_realm is None:
                raise PermissionError("Customer business access requires a trusted realm")
            return Scope(unit.scope.customer_id, unit.customer_realm, "customer")
        return unit.scope

    def get(self, table: str, key: str) -> Any:
        unit = self._unit()
        if unit.connection is None:
            value = self.memory.get((self._storage_scope(table), table, key))
            return json.loads(json.dumps(value)) if value is not None else None
        row = unit.connection.execute(
            sql.SQL("SELECT payload FROM ops.{} WHERE id=%s").format(sql.Identifier(table)), (key,)
        ).fetchone()
        return row[0] if row else None

    def put(self, table: str, key: str, payload: Any) -> None:
        unit = self._unit()
        if unit.connection is None:
            storage_scope = self._storage_scope(table)
            if table == "customer_cases" and open_case(payload):
                for (stored_scope, stored_table, stored_key), stored in self.memory.items():
                    if (
                        stored_scope == storage_scope
                        and stored_table == table
                        and stored_key != key
                        and stored.get("transaction_id") == payload.get("transaction_id", key)
                        and open_case(stored)
                    ):
                        raise ValueError(
                            "An open case already exists for this customer transaction"
                        )
            self.memory[(storage_scope, table, key)] = json.loads(json.dumps(payload))
        else:
            scope = unit.scope
            if table in CUSTOMER_TABLES:
                self._storage_scope(table)
                unit.connection.execute(
                    sql.SQL(
                        "INSERT INTO ops.{} (customer_id,realm,id,payload) VALUES (%s,%s,%s,%s) ON CONFLICT(customer_id,realm,id) DO UPDATE SET payload=excluded.payload,updated_at=clock_timestamp()"
                    ).format(sql.Identifier(table)),
                    (scope.customer_id, unit.customer_realm, key, Jsonb(payload)),
                )
            else:
                unit.connection.execute(
                    sql.SQL(
                        "INSERT INTO ops.{} (customer_id,run_id,sid,id,payload) VALUES (%s,%s,%s,%s,%s) ON CONFLICT(customer_id,run_id,sid,id) DO UPDATE SET payload=excluded.payload,updated_at=clock_timestamp()"
                    ).format(sql.Identifier(table)),
                    (scope.customer_id, scope.run_id, scope.sid, key, Jsonb(payload)),
                )
            if table not in {"otp_challenges", "sessions", "demo_identities"}:
                self.audit({"action": "write", "table": table, "record_id": key})

    def delete(self, table: str, key: str) -> None:
        unit = self._unit()
        unit.cache.pop((table, key), None)
        if unit.connection is None:
            self.memory.pop((self._storage_scope(table), table, key), None)
        else:
            unit.connection.execute(
                sql.SQL("DELETE FROM ops.{} WHERE id=%s").format(sql.Identifier(table)), (key,)
            )

    def keys(self, table: str) -> list[str]:
        unit = self._unit()
        if unit.connection is None:
            storage_scope = self._storage_scope(table)
            return [key for scope, t, key in self.memory if scope == storage_scope and t == table]
        return [
            row[0]
            for row in unit.connection.execute(
                sql.SQL("SELECT id FROM ops.{} ORDER BY id").format(sql.Identifier(table))
            ).fetchall()
        ]

    def audit(self, event: dict[str, Any]) -> None:
        unit = self._unit()
        if unit.connection:
            unit.connection.execute("SELECT ops.append_audit(%s)", (Jsonb(event),))

    def close(self) -> None:
        if self.pool:
            self.pool.close()

    def mapping(
        self,
        table: str,
        kind: Any,
        *,
        auth_scope: Scope | None = None,
        auth_customer: Callable[[str], str] | None = None,
    ) -> RecordMap[Any]:
        if table not in TABLES:
            raise ValueError("Unknown operational table")
        return RecordMap(self, table, kind, auth_scope, auth_customer)

    def customer_mapping(
        self, table: str, kind: Any, realm: Callable[[Scope], str], *, legacy: str
    ) -> CustomerRecordMap[Any]:
        if table not in CUSTOMER_TABLES or legacy not in {"cases", "card_states"}:
            raise ValueError("Unknown customer business table")
        return CustomerRecordMap(self, table, kind, realm, legacy)


class RecordMap[T](MutableMapping[str, T]):
    def __init__(
        self,
        store: Store,
        table: str,
        kind: Any,
        auth_scope: Scope | None,
        auth_customer: Callable[[str], str] | None = None,
    ):
        self.store, self.table, self.auth_scope = store, table, auth_scope
        self.auth_customer = auth_customer
        self.adapter: TypeAdapter[T] = TypeAdapter(kind)

    def _key(self, key: str) -> str:
        # Authentication capabilities never appear as recoverable database keys.
        return hashlib.sha256(key.encode()).hexdigest() if self.auth_scope else key

    def auth_context(self, key: str) -> Scope:
        if self.auth_scope is None:
            raise RuntimeError("Not an authentication map")
        parts = key.split(".", 2)
        if len(parts) != 3 or any(not part for part in parts) or len(key) > 160:
            raise KeyError("Invalid capability")
        customer = (
            self.auth_customer(parts[0]) if self.auth_customer else self.auth_scope.customer_id
        )
        return Scope(customer, parts[0], parts[1])

    @contextmanager
    def _context(self, key: str = "") -> Iterator[None]:
        if self.auth_scope:
            with self.store.transaction(self.auth_context(key)):
                yield
        else:
            self.store._unit()
            yield

    def __getitem__(self, key: str) -> T:
        with self._context(key):
            key = self._key(key)
            unit = self.store._unit()
            cached = unit.cache.get((self.table, key))
            if cached:
                return cached[0]  # type: ignore[no-any-return]
            payload = self.store.get(self.table, key)
            if payload is None:
                raise KeyError(key)
            value = self.adapter.validate_python(payload)
            unit.cache[(self.table, key)] = (value, payload, self.adapter)
            return value

    def __setitem__(self, key: str, value: T) -> None:
        with self._context(key):
            key = self._key(key)
            payload = self.adapter.dump_python(value, mode="json")
            self.store.put(self.table, key, payload)
            self.store._unit().cache[(self.table, key)] = (value, payload, self.adapter)

    def __delitem__(self, key: str) -> None:
        with self._context(key):
            self.store.delete(self.table, self._key(key))

    def __iter__(self) -> Iterator[str]:
        with self._context():
            return iter(self.store.keys(self.table))

    def __len__(self) -> int:
        if self.store.current.get() is None and not self.auth_scope and self.store.pool is None:
            return sum(table == self.table for _, table, _ in self.store.memory)
        return len(list(iter(self)))


class CustomerRecordMap[T](RecordMap[T]):
    """Bank state persists across logins; workspace state remains session-scoped.

    The realm resolver uses server-trusted identity metadata. Legacy reads are
    restricted to the current session and copied lazily for safe upgrades.
    """

    def __init__(
        self, store: Store, table: str, kind: Any, realm: Callable[[Scope], str], legacy: str
    ):
        super().__init__(store, table, kind, None)
        self.realm = realm
        self.legacy = legacy

    @contextmanager
    def _context(self, key: str = "") -> Iterator[None]:
        self.store.customer_context(self.realm(self.store._unit().scope))
        yield

    def __getitem__(self, key: str) -> T:
        try:
            return super().__getitem__(key)
        except KeyError:
            with self._context():
                legacy = self.store.get(self.legacy, key)
                if legacy is None:
                    raise
                value = self.adapter.validate_python(legacy)
                self[key] = value
                return value

    def __iter__(self) -> Iterator[str]:
        with self._context():
            return iter(
                sorted(set(self.store.keys(self.table)) | set(self.store.keys(self.legacy)))
            )
