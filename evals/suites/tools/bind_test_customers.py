"""Resolve opaque suite personas privately; print aggregate checks only."""

# ruff: noqa: T201 -- CLI output is aggregate checks and billing only.
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import duckdb
import yaml
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / "artifacts/evaluation-authoring"


def main() -> None:
    values = dotenv_values(ROOT / ".env")
    lake = Path(os.environ.get("LAKE_DIR") or str(values.get("LAKE_DIR"))).expanduser()
    marker = json.loads((lake / "_meta/current.json").read_text())
    release = ROOT / "evals/suites/test"
    if release.exists():
        payloads = [
            yaml.safe_load(path.read_text()) for path in sorted(release.glob("scenarios-*.yaml"))
        ]
        suite = {
            **payloads[0],
            "scenarios": [s for payload in payloads for s in payload["scenarios"]],
        }
    else:
        suite = json.loads((PRIVATE / "draft-suite.json").read_text())
    assert marker["dataset_version"] == suite["dataset_version"]
    excluded = set()
    for split in ("train", "validation", "test"):
        path = ROOT / f"artifacts/charge_matcher/v1/dataset/{split}.jsonl"
        with path.open() as stream:
            excluded.update(json.loads(line)["customer_id"] for line in stream)
    assert len(excluded) > 10000
    seed = suite["customer_selection"]["seed"]
    pools: dict[tuple[str, str], list[tuple[str, str]]] = {}
    with duckdb.connect(marker["database"], read_only=True) as db:
        records = db.execute(
            "SELECT c.customer_id,c.country,c.segment,p.product_id FROM gold.customers c JOIN gold.products p USING(customer_id) WHERE substr(sha256(c.customer_id),1,2)>='da' QUALIFY row_number() OVER(PARTITION BY c.customer_id ORDER BY sha256(p.product_id))=1"
        ).fetchall()
    for customer, country, segment, product in records:
        if customer not in excluded:
            pools.setdefault((country, segment), []).append((customer, product))
    for rows in pools.values():
        rows.sort(key=lambda row: hashlib.sha256((seed + row[0]).encode()).hexdigest())
    bindings: dict[str, Any] = {}
    for scenario in suite["scenarios"]:
        persona = scenario["persona"]
        selector = persona["selector"]
        customer, product = pools[(selector["country"], selector["segment"])][selector["ordinal"]]
        assert int(hashlib.sha256(customer.encode()).hexdigest()[:2], 16) >= 218
        bindings[persona["customer_ref"]] = {
            "customer_id": customer,
            "product_id": product,
            "selector": selector,
        }
    assert len({x["customer_id"] for x in bindings.values()}) == 200
    output = {
        "dataset_version": marker["dataset_version"],
        "selection": suite["customer_selection"],
        "bindings": dict(sorted(bindings.items())),
    }
    path = PRIVATE / "customer-bindings.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    path.chmod(0o600)
    assert json.loads(path.read_text()) == output
    aggregate = {
        "personas": 200,
        "unique_customers": 200,
        "test_bucket_min_hex": "da",
        "benchmark_overlap": 0,
        "dataset_version": marker["dataset_version"],
        "private_bindings_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    (PRIVATE / "binding-audit.json").write_text(json.dumps(aggregate, indent=2) + "\n")
    print(json.dumps(aggregate))


if __name__ == "__main__":
    main()
