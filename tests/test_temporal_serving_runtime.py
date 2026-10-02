"""Authored old/new serving interface checks; no real connections or row inputs."""

from __future__ import annotations

import asyncio
from contextlib import nullcontext
from contextvars import ContextVar
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from httpx import ASGITransport, AsyncClient
from scripts.verify_temporal_serving import verify
from test_api_security import _settings
from test_dev_acceptance import ledger

from aclara.api.app import create_app
from aclara.bank.serving import Persona, ServingRepository, temporal_column_available
from aclara.data.serving_load import _migrate_temporal_column
from aclara.handoff.routing import AgentDirectory
from aclara.settings import Settings


@pytest.mark.parametrize("available", (True, False))
def test_column_gate_requires_correct_nullable_text_column_and_promoted_fingerprint(available):
    column = Mock()
    column.fetchone.return_value = (available,)
    identity = Mock()
    identity.fetchone.return_value = ({"build_fingerprint": "authored-build"},)
    connection = Mock()
    connection.execute.side_effect = [column, identity]
    if available:
        assert verify(connection, "authored-build") == {
            "temporal_column_available": True,
            "promoted_fingerprint_matches": True,
        }
    else:
        with pytest.raises(RuntimeError, match="column unavailable"):
            verify(connection, "authored-build")
    query = connection.execute.call_args_list[0].args[0]
    assert "data_type='text'" in query and "is_nullable='YES'" in query


@pytest.mark.parametrize("schema", ("exact_old", "wrong_names", "wrong_type", "already_current"))
def test_migration_only_adds_the_exact_known_missing_nullable_column(schema):
    connection = Mock()
    names = ["transaction_id", "temporal_quality_reason"]
    existing = [("transaction_id", "text", "NO")]
    if schema == "wrong_names":
        existing = [("unexpected_column", "text", "NO")]
    elif schema == "wrong_type":
        existing += [("temporal_quality_reason", "boolean", "YES")]
    elif schema == "already_current":
        existing += [("temporal_quality_reason", "text", "YES")]
    if schema == "wrong_type":
        with pytest.raises(ValueError, match="unsupported migration"):
            _migrate_temporal_column(connection, "transactions", names, existing)
    else:
        result = _migrate_temporal_column(connection, "transactions", names, existing)
        assert [r[0] for r in result] == (
            names if schema != "wrong_names" else ["unexpected_column"]
        )
    assert connection.execute.call_count == int(schema == "exact_old")


@pytest.mark.parametrize("identity", (None, ({"build_fingerprint": "old-build"},)))
def test_release_gate_rejects_old_or_missing_promoted_identity(identity):
    connection = Mock()
    column, state = Mock(), Mock()
    column.fetchone.return_value, state.fetchone.return_value = (True,), identity
    connection.execute.side_effect = [column, state]
    with pytest.raises(RuntimeError, match="fingerprint differs"):
        verify(connection, "authored-build")


@pytest.mark.parametrize("available", (True, False))
def test_serving_adapter_handles_missing_column_without_losing_explanations(available):
    repo, clock = ledger(), Settings().bank_clock
    row = repo._rows[0]
    identity = {"dataset_version": "authored-serving"}
    queries = []

    def execute(query, _params=None):
        queries.append(query)
        cursor = Mock()
        if "information_schema.columns" in query:
            cursor.fetchone.return_value = (available,)
        elif "meta.serving_state" in query:
            cursor.fetchone.return_value = (identity,)
        elif "FROM bank.customers" in query:
            cursor.fetchall.return_value = [(row.customer_id, "Active", "MX", "Basic", 0)]
        elif "FROM bank.products" in query:
            cursor.fetchall.return_value = [
                (row.product_id, row.customer_id, "Credit_Card", "Active")
            ]
        elif "FROM bank.transactions" in query:
            cursor.fetchall.return_value = [
                (
                    row.record_id,
                    row.customer_id,
                    row.product_id,
                    row.transaction_date,
                    row.process_date,
                    row.transaction_type,
                    row.amount,
                    row.currency,
                    row.merchant_name,
                    row.transaction_status,
                    row.amount,
                    0,
                    False,
                    "before_product_open" if available else None,
                )
            ]
        return cursor

    connection = SimpleNamespace(execute=execute)
    serving = ServingRepository.__new__(ServingRepository)
    serving.store = SimpleNamespace(
        current=ContextVar("authored-serving-scope", default=None),
        transaction=lambda _scope: nullcontext(),
        _unit=lambda: SimpleNamespace(connection=connection),
    )
    serving.bank_clock, serving.identity = clock, identity
    serving.temporal_quality_checked = temporal_column_available(connection)
    snapshot = serving.snapshot(row.customer_id, clock)
    assert len(snapshot.for_customer(row.customer_id, clock)) == len(snapshot._rows) == 1
    facts = snapshot.context(snapshot._rows[0])
    assert facts.temporal_quality_checked is available
    assert facts.temporal_quality_reason == ("before_product_open" if available else None)
    selection = next(q for q in queries if "FROM bank.transactions" in q)
    assert ("t.temporal_quality_reason " in selection) is available
    assert ("NULL::text AS temporal_quality_reason " in selection) is not available
    assert "t.customer_id=%s" in selection


@pytest.mark.parametrize("checked", (True, False))
def test_readiness_remains_available_with_an_explicit_automation_warning(monkeypatch, checked):
    settings, fixture = _settings(), ledger()

    class AuthoredServing(ServingRepository):
        def __init__(self):
            self.__dict__.update(fixture.__dict__)
            self.temporal_quality_checked = checked

        def personas(self):
            return [Persona(settings.demo_username, settings.demo_customer_id, "es-MX", "customer")]

        def directory(self):
            return AgentDirectory()

        def ready(self):
            return True

    monkeypatch.setattr("aclara.api.app._read_db_ready", lambda: True)
    app = create_app(settings, AuthoredServing())

    async def check():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
            response = await api.get("/readyz")
        assert response.status_code == 200 and response.json()["status"] == "ready"
        assert ("warning" in response.json()) is not checked
        if not checked:
            assert "automatic dispute disabled" in response.json()["warning"]

    asyncio.run(check())
