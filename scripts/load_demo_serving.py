"""Load promoted gold and bind private demo identities; emit counts only."""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from dotenv import dotenv_values
from psycopg.conninfo import make_conninfo

from aclara.bank.serving import ServingRepository
from aclara.data.serving_load import load_serving
from aclara.ops.store import Store

ROOT = Path(__file__).resolve().parents[1]


def bind_personas(owner: str, dataset: str) -> None:
    """Select four development-partition identities from gold; no frozen reads.

    Read-only identity configuration is private reference data. The two Ops
    personas can demonstrate all surfaces within their own authenticated scope.
    PT denotes a language preference, not a Brazilian source customer.
    """
    definitions = (
        ("demo.es.mx", "MX", "es-MX", "ops"),
        ("demo.es.co", "CO", "es-CO", "customer"),
        ("demo.es.ar", "AR", "es-AR", "customer"),
        ("demo.pt.br", "MX", "pt-BR", "ops"),
    )
    with psycopg.connect(owner) as pg:
        pg.execute("CREATE SCHEMA IF NOT EXISTS reference")
        pg.execute(
            "CREATE TABLE IF NOT EXISTS reference.demo_personas ("
            "username text PRIMARY KEY,customer_id text NOT NULL UNIQUE,locale text NOT NULL,"
            "role text NOT NULL CHECK(role IN ('customer','agent','ops')),dataset_version text NOT NULL)"
        )
        pg.execute("GRANT USAGE ON SCHEMA meta,reference TO aclara_api")
        pg.execute("GRANT SELECT ON meta.serving_state,reference.demo_personas TO aclara_api")
        # Owner-only selection transaction, with FORCE restored before commit.
        # The application role never receives owner membership or reference writes.
        for table in ("customers", "products", "transactions"):
            from psycopg import sql

            pg.execute(
                sql.SQL("ALTER TABLE bank.{} NO FORCE ROW LEVEL SECURITY").format(
                    sql.Identifier(table)
                )
            )
        for username, country, locale, role in definitions:
            existing = pg.execute(
                "SELECT customer_id FROM reference.demo_personas WHERE username=%s AND dataset_version=%s",
                (username, dataset),
            ).fetchone()
            if existing:
                continue
            candidate = pg.execute(
                "SELECT c.customer_id FROM bank.customers c WHERE c.country=%s "
                "AND c.customer_status='Active' AND encode(sha256(convert_to(c.customer_id,'UTF8')),'hex')<'b3' "
                "AND NOT EXISTS(SELECT 1 FROM reference.demo_personas d WHERE d.customer_id=c.customer_id) "
                "AND EXISTS(SELECT 1 FROM bank.transactions t JOIN bank.products p USING(product_id,customer_id) "
                "WHERE t.customer_id=c.customer_id AND p.product_status='Active' "
                "AND p.product_type IN ('credit_card','debit_card') "
                "AND t.transaction_status='Approved' AND t.transaction_type IN ('Purchase','Payment','Withdrawal') "
                "AND t.process_date >= DATE '2026-05-20' AND t.process_date <= DATE '2026-06-16' "
                "AND t.amount_usd_recomputed>0 AND t.amount_usd_recomputed<450 "
                "AND COALESCE(t.fraud_score,0)<=30 AND NOT t.fx_nearest_prior AND t.merchant_name IS NOT NULL) "
                'ORDER BY c.customer_id COLLATE "C" LIMIT 1',
                (country,),
            ).fetchone()
            if candidate is None:
                raise ValueError("No eligible development persona")
            pg.execute(
                "INSERT INTO reference.demo_personas VALUES (%s,%s,%s,%s,%s) "
                "ON CONFLICT(username) DO UPDATE SET customer_id=excluded.customer_id,"
                "locale=excluded.locale,role=excluded.role,dataset_version=excluded.dataset_version",
                (username, candidate[0], locale, role, dataset),
            )
        for table in ("customers", "products", "transactions"):
            pg.execute(
                sql.SQL("ALTER TABLE bank.{} FORCE ROW LEVEL SECURITY").format(
                    sql.Identifier(table)
                )
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("local", "azure"), required=True)
    args = parser.parse_args()
    values = dotenv_values(ROOT / ".env")
    lake = Path(os.environ.get("LAKE_DIR") or values.get("LAKE_DIR") or ROOT / "lake").resolve()
    if not lake.is_relative_to(ROOT):
        raise ValueError("This session's generated data must stay inside the repository")
    if args.target == "azure":
        from scripts.azure_migrate_ops import connection_string

        prices = json.loads((ROOT / "artifacts/azure/prices.json").read_text())
        if (
            not prices["gate_passed"]
            or prices["monthly_without_free_grant_with_margin"] > 40
            or (datetime.now(UTC) - datetime.fromisoformat(prices["checked_at"])).total_seconds()
            > 21600
        ):
            raise ValueError("Fresh approved price gate required")
        owner, runtime = connection_string("aclara_admin"), connection_string("aclara_app")
    else:
        owner = make_conninfo(
            host="127.0.0.1",
            port=values.get("POSTGRES_HOST_PORT") or "15432",
            user=values.get("POSTGRES_USER") or "postgres",
            password=values.get("POSTGRES_PASSWORD") or "",
            dbname=values.get("POSTGRES_DB") or "aclara",
        )
        runtime = make_conninfo(
            owner, user="aclara_app", password=values.get("OPS_APP_PASSWORD") or ""
        )
    result = load_serving(lake, owner)
    bind_personas(owner, result["dataset_version"])
    store = Store(runtime)
    try:
        ledger = ServingRepository(
            store, datetime.fromisoformat(result["bank_clock"].replace("Z", "+00:00"))
        )
        personas = ledger.personas()
        assert len(personas) == 4
        counts = [len(ledger.for_customer(p.customer_id, ledger.bank_clock)) for p in personas]
        assert all(n > 0 for n in counts)
        logging.info(
            "Serving committed readback: %s",
            json.dumps(
                {
                    "tables": {k: v["rows"] for k, v in result["tables"].items()},
                    "personas": len(personas),
                    "scoped_rows": sum(counts),
                    "dataset_version": ledger.dataset_version,
                }
            ),
        )
    finally:
        store.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        main()
    except Exception as exc:
        logging.error("Serving setup failed (%s); no verified success claimed", type(exc).__name__)
        raise SystemExit(1) from None
