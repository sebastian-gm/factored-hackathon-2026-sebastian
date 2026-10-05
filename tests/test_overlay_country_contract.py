"""Authored overlay API compatibility; no frozen cases or organizer data."""

import asyncio
from datetime import UTC, datetime

import pytest
from evals.bindings import bind
from evals.bound_execution import execute_bound
from evals.serving import OverlayRepository
from tests.test_bound_evaluation import IDENTITY, authored

from aclara.bank.repository import Customer, Product, TransactionRepository


class AuthoredServing:
    bank_clock = datetime(2026, 6, 18, 6, tzinfo=UTC)
    dataset_version = "authored-overlay-contract"
    loaded_at = bank_clock

    def __init__(self, country):
        self.base = TransactionRepository(
            (),
            customers=(Customer(IDENTITY["customer_id"], country=country),),
            products=(Product(IDENTITY["product_id"], IDENTITY["customer_id"]),),
        )

    def snapshot(self, customer, clock):
        if customer != IDENTITY["customer_id"]:
            raise PermissionError("Foreign snapshot denied")
        return self.base


@pytest.mark.parametrize("country", ["MX", "BR"])
@pytest.mark.parametrize("system", ["B1", "P"])
def test_bound_overlay_exposes_trusted_country_and_completes_mock_api(country, system):
    source = AuthoredServing(country)
    identity = {**IDENTITY, "selector": {"country": country, "segment": "Basic"}}
    scenario = authored()
    fixture = bind(scenario, identity, serving=source)
    assert fixture.ledger.customers[identity["customer_id"]].country == country
    assert set(fixture.ledger.customers) == {identity["customer_id"]}
    assert asyncio.run(execute_bound(scenario, fixture, system))["passed"]
    with pytest.raises(PermissionError):
        fixture.ledger.for_customer("authored-foreign-customer", source.bank_clock)


def test_overlay_without_bound_customer_fails_closed():
    with pytest.raises(ValueError, match="bound customer"):
        OverlayRepository(AuthoredServing("MX"), TransactionRepository(()), "absent")
