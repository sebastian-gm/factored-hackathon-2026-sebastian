"""Free, read-only launch gate for account credits and the inference key limit."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

MINIMUM_USD = Decimal("4.00")
BASE_URL = "https://openrouter.ai/api/v1"


class CreditPreflightError(RuntimeError):
    """Only sanitized metadata is carried; never include response bodies or keys."""


def _money(value: Any) -> Decimal:
    if value is None or isinstance(value, bool):
        raise CreditPreflightError("Invalid credit metadata")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise CreditPreflightError("Invalid credit metadata") from None
    if not parsed.is_finite() or parsed < 0:
        raise CreditPreflightError("Invalid credit metadata")
    return parsed


def inspect(client: httpx.Client, key: str) -> dict[str, Any]:
    if not key.strip():
        raise CreditPreflightError("Inference key unavailable")
    values: dict[str, dict[str, Any]] = {}
    for endpoint in ("credits", "key"):
        try:
            response = client.get(
                BASE_URL + "/" + endpoint, headers={"Authorization": "Bearer " + key}
            )
        except httpx.HTTPError as error:
            raise CreditPreflightError("OpenRouter " + type(error).__name__) from None
        if response.status_code != 200:
            raise CreditPreflightError(f"OpenRouter {endpoint} HTTP {response.status_code}")
        try:
            body = response.json()
            data = body["data"]
        except (ValueError, KeyError, TypeError):
            raise CreditPreflightError("Invalid credit response shape") from None
        if not isinstance(data, dict):
            raise CreditPreflightError("Invalid credit response shape")
        values[endpoint] = data
    balance = _money(values["credits"].get("total_credits")) - _money(
        values["credits"].get("total_usage")
    )
    remaining = _money(values["key"].get("limit_remaining"))
    receipt = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "account_remaining_usd": float(balance),
        "key_limit_remaining_usd": float(remaining),
        "minimum_each_usd": float(MINIMUM_USD),
        "gate_passed": balance >= MINIMUM_USD and remaining >= MINIMUM_USD,
        "model_calls": 0,
        "cost_usd": 0,
    }
    if not receipt["gate_passed"]:
        raise CreditPreflightError(
            "Account balance and key remaining limit must each be at least USD 4"
        )
    return receipt


def main() -> None:
    from scripts.azure_dev import ROOT, VAULT, az, private_write

    key = (
        os.getenv("OPENROUTER_API_KEY")
        or az("keyvault", "secret", "show", "--vault-name", VAULT, "--name", "openrouter-api-key")[
            "value"
        ]
    )
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        receipt = inspect(client, key)
    private_write(
        ROOT / "artifacts/evaluation-v4/openrouter-preflight.json", json.dumps(receipt) + "\n"
    )
    print(json.dumps(receipt))  # noqa: T201 -- numeric aggregate only, no labels or keys.


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Azure/httpx errors may contain credentials, URLs or response input.
        message = str(error) if isinstance(error, CreditPreflightError) else type(error).__name__
        raise SystemExit("OpenRouter preflight stopped: " + message) from None
