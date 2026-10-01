"""Authored HTTP metadata checks; no model, network, frozen suite or real key."""

from __future__ import annotations

import json

import httpx
import pytest
from scripts.openrouter_preflight import CreditPreflightError, inspect


@pytest.mark.parametrize("account,key", [("4.00", "4.00"), ("10.10", "5.80")])
def test_each_remaining_amount_must_pass_and_only_get_metadata_leaves(account, key):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "data": {
                    "total_credits": account,
                    "total_usage": 0,
                    "limit_remaining": key,
                    "label": "private identity metadata",
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = inspect(client, "authored-inference-token")
    assert result["gate_passed"] and result["model_calls"] == result["cost_usd"] == 0
    assert [r.url.path for r in requests] == ["/api/v1/credits", "/api/v1/key"]
    assert all(r.method == "GET" for r in requests)
    assert "private identity metadata" not in json.dumps(result)
    assert "authored-inference-token" not in json.dumps(result)


@pytest.mark.parametrize("account,key", [("3.99", "5"), ("5", "3.99"), ("3.99", "3.99")])
def test_either_insufficient_balance_stops(account, key):
    def respond(request):
        return httpx.Response(
            200,
            json={
                "data": {
                    "total_credits": account,
                    "total_usage": 0,
                    "limit_remaining": key,
                }
            },
        )

    with (
        httpx.Client(transport=httpx.MockTransport(respond)) as client,
        pytest.raises(CreditPreflightError),
    ):
        inspect(client, "authored-inference-token")


@pytest.mark.parametrize("value", [None, True, "NaN", "Infinity", -1, "invalid"])
def test_invalid_key_metadata_fails_closed(value):
    def respond(request):
        return httpx.Response(
            200,
            json={
                "data": {
                    "total_credits": 10,
                    "total_usage": 0,
                    "limit_remaining": value,
                }
            },
        )

    with (
        httpx.Client(transport=httpx.MockTransport(respond)) as client,
        pytest.raises(CreditPreflightError),
    ):
        inspect(client, "authored-inference-token")


@pytest.mark.parametrize("status", [401, 402, 403, 429, 500])
def test_provider_failure_never_echoes_response_body(status):
    def respond(request):
        return httpx.Response(status, text="private identity metadata and authored-inference-token")

    with (
        httpx.Client(transport=httpx.MockTransport(respond)) as client,
        pytest.raises(CreditPreflightError) as error,
    ):
        inspect(client, "authored-inference-token")
    assert str(status) in str(error.value)
    assert "private identity metadata" not in str(error.value)
    assert "authored-inference-token" not in str(error.value)
