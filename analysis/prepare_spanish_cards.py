"""Prepare private human-writing cards, excluding all benchmark customers."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Any

import duckdb
from dotenv import dotenv_values

TYPES = {
    "Purchase": "Compra",
    "Withdrawal": "Retiro",
    "Payment": "Pago",
    "Transfer": "Transferencia",
    "Deposit": "Depósito",
    "Adjustment": "Ajuste",
}
STATUSES = {
    "Approved": "Aprobado",
    "Pending": "Pendiente",
    "Declined": "Rechazado",
    "Reversed": "Revertido",
}
COUNTRIES = {
    "MX": "México",
    "CO": "Colombia",
    "AR": "Argentina",
    "BR": "Brasil",
    "US": "Estados Unidos",
    "ES": "España",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-version", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    values = dotenv_values(root / ".env")
    lake = Path(os.environ.get("LAKE_DIR") or values.get("LAKE_DIR") or root / "lake")
    marker = json.loads((lake / "_meta/current.json").read_text())
    excluded = set()
    dataset = root / "artifacts/charge_matcher" / args.benchmark_version / "dataset"
    for split in ("train", "validation", "test"):
        with (dataset / f"{split}.jsonl").open() as stream:
            for line in stream:
                excluded.add(json.loads(line)["customer_id"])
    output = root / "artifacts/human-validation/spanish-40"
    output.mkdir(parents=True, exist_ok=True)
    # Never overwrite the owner's recollections on a repeated run.
    if (output / "recollections.csv").exists():
        raise ValueError("human-writing sheet already exists; preserve filled-in responses")
    cards: list[dict[str, Any]] = []
    references = []
    with duckdb.connect(marker["database"], read_only=True) as db:
        db.execute(
            "CREATE TEMP TABLE excluded AS SELECT unnest(?::VARCHAR[]) AS customer_id",
            [sorted(excluded)],
        )
        for country, count in (("MX", 14), ("CO", 13), ("AR", 13)):
            rows = db.execute(
                "SELECT t.transaction_id,t.customer_id,t.transaction_date,t.process_date,t.transaction_type,t.amount,t.currency,t.merchant_name,t.transaction_country,t.transaction_status FROM gold.matcher_ledger t JOIN gold.customers c USING(customer_id) WHERE c.country=? AND t.process_date>=DATE '2026-03-01' AND substr(sha256(t.customer_id),1,2)>='b3' AND substr(sha256(t.customer_id),1,2)<'da' AND t.customer_id NOT IN (SELECT customer_id FROM excluded) QUALIFY row_number() OVER (PARTITION BY t.customer_id ORDER BY sha256(t.transaction_id))=1 ORDER BY sha256(t.transaction_id || 'human-es-v1') LIMIT ?",
                [country, count],
            ).fetchall()
            for (
                transaction_id,
                customer_id,
                timestamp,
                business_day,
                kind,
                amount,
                currency,
                merchant,
                txn_country,
                status,
            ) in rows:
                card_id = f"ES-{len(cards) + 1:02}"
                as_of = min(
                    datetime.combine(business_day + timedelta(days=4), time(6), tzinfo=UTC),
                    datetime.fromisoformat(marker["bank_clock"]),
                )
                cards.append(
                    {
                        "tarjeta": card_id,
                        "fecha_simulada_utc": as_of.isoformat(),
                        "fecha_movimiento_utc": timestamp.isoformat(),
                        "fecha_negocio": business_day.isoformat(),
                        "tipo": TYPES[kind],
                        "importe": f"{amount:.2f}",
                        "moneda": currency,
                        "comercio": merchant or "(no registrado)",
                        "pais_movimiento": COUNTRIES.get(txn_country, txn_country),
                        "estado": STATUSES[status],
                        "variante_sugerida": f"es-{country}",
                        "recuerdo_cliente": "",
                        "variante_escrita": "",
                        "notas_del_autor": "",
                    }
                )
                references.append(
                    {
                        "card_id": card_id,
                        "dataset_version": marker["dataset_version"],
                        "transaction_id": transaction_id,
                        "customer_id": customer_id,
                        "as_of": as_of.isoformat(),
                        "origin": "organizer synthetic card; human utterance pending",
                    }
                )
    if len(cards) != 40:
        raise ValueError("expected exactly 40 cards")
    with (output / "recollections.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cards[0]))
        writer.writeheader()
        writer.writerows(cards)
    text = [
        "# 40 tarjetas para recuerdos en español",
        "",
        "Datos sintéticos. Escribe en `recuerdo_cliente` cómo recordarías este movimiento. Puedes omitir detalles o expresar duda. No copies números de identificación. La fecha simulada sirve para expresiones como «ayer». Puedes usar tu propio dialecto e indicarlo en `variante_escrita`.",
        "",
    ]
    for card in cards:
        text += [f"## {card['tarjeta']}", "", "| Campo | Valor |", "|---|---|"]
        for key in (
            "fecha_simulada_utc",
            "fecha_movimiento_utc",
            "fecha_negocio",
            "tipo",
            "importe",
            "moneda",
            "comercio",
            "pais_movimiento",
            "estado",
            "variante_sugerida",
        ):
            text.append(f"| {key} | {str(card[key]).replace('|', ' / ')} |")
        text += [
            "",
            "Recuerdo del cliente: ____________________________________________",
            "",
            "Variante escrita / notas: ____________________________________________",
            "",
        ]
    (output / "cards.md").write_text("\n".join(text))
    (output / "references.json").write_text(json.dumps(references, indent=2) + "\n")
    # Read-back verifies counts without displaying any source field values.
    with (output / "recollections.csv").open(encoding="utf-8-sig") as stream:
        assert len(list(csv.DictReader(stream))) == 40
    assert len(json.loads((output / "references.json").read_text())) == 40


if __name__ == "__main__":
    main()
