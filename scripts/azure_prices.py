"""Check live East US 2 list prices before provisioning; fail above USD 40/month."""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def prices(service: str) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "$filter": f"serviceName eq '{service}' and armRegionName eq 'eastus2' and priceType eq 'Consumption'",
            "currencyCode": "USD",
        }
    )
    url = f"https://prices.azure.com/api/retail/prices?{query}"
    rows: list[dict[str, Any]] = []
    while url:
        if not url.startswith("https://prices.azure.com"):
            raise ValueError("Unexpected retail-price pagination host")
        with urllib.request.urlopen(url, timeout=45) as response:  # noqa: S310
            page = json.load(response)
        rows.extend(page["Items"])
        url = page.get("NextPageLink", "")
    return rows


def meter(rows: list[dict[str, Any]], product: str, name: str) -> float:
    found = [row for row in rows if row["productName"] == product and row["meterName"] == name]
    if len(found) != 1:
        raise ValueError(f"Expected exactly one USD East US 2 meter: {product}/{name}")
    return float(found[0]["retailPrice"])


def main() -> int:
    pg = prices("Azure Database for PostgreSQL")
    acr = prices("Container Registry")
    aca = prices("Azure Container Apps")
    rates = {
        "pg_hour": meter(
            pg, "Azure Database for PostgreSQL Flexible Server Burstable BS Series Compute", "B1MS"
        ),
        "pg_gb_month": meter(
            pg, "Azure Database for PostgreSQL Flex Server Storage", "Storage Data Stored"
        ),
        "acr_day": meter(acr, "Container Registry", "Basic Registry Unit"),
        "aca_vcpu_second": meter(aca, "Azure Container Apps", "Standard vCPU Active Usage"),
        "aca_gib_second": meter(aca, "Azure Container Apps", "Standard Memory Active Usage"),
        "aca_million_requests": meter(aca, "Azure Container Apps", "Standard Requests"),
    }
    fixed = rates["pg_hour"] * 730 + rates["pg_gb_month"] * 32 + rates["acr_day"] * 30
    # Two .25-vCPU/.5-GiB apps active together for 100h/month, <=100k requests.
    # No free grants assumed in the approval gate. State/KV/log/egress allowances are additive.
    usage = 100 * 3600 * (0.5 * rates["aca_vcpu_second"] + rates["aca_gib_second"])
    usage += 0.1 * rates["aca_million_requests"]
    estimate = fixed + usage + 1.0 + 0.10 + 7.0
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "source": "https://prices.azure.com/api/retail/prices",
        "region": "eastus2",
        "currency": "USD",
        "rates": rates,
        "assumptions": "730 DB hours;32 GB;30 ACR days;100h both apps;100k requests;no ACA free grant;no dedicated/private-endpoint/planned-maintenance fees;before tax",
        "fixed_monthly": round(fixed, 2),
        "monthly_with_free_grant_range": [round(fixed + 3.1, 2), round(fixed + 8.1, 2)],
        "monthly_without_free_grant_with_margin": round(estimate, 2),
        "stop_above": 40,
        "gate_passed": estimate <= 40,
    }
    path = Path(__file__).resolve().parents[1] / "artifacts" / "azure" / "prices.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 0 if estimate <= 40 else 1


if __name__ == "__main__":
    raise SystemExit(main())
