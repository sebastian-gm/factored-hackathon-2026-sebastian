"""Verify a scoped append-only hash chain; print only aggregate counts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Any

import psycopg


def verify(rows: list[tuple[Any, ...]], expected_scope: tuple[str, str, str]) -> int:
    previous = "0" * 64
    for expected_sequence, row in enumerate(rows, start=1):
        sequence, canonical, prev_hash, row_hash = row
        payload = json.loads(canonical)
        if sequence != expected_sequence or payload["sequence"] != sequence:
            raise ValueError("Audit sequence is incomplete")
        if tuple(payload[k] for k in ("customer_id", "run_id", "sid")) != expected_scope:
            raise ValueError("Audit scope mismatch")
        if (
            prev_hash != previous
            or row_hash != hashlib.sha256((previous + canonical).encode()).hexdigest()
        ):
            raise ValueError("Audit chain integrity failure")
        previous = row_hash
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customer", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--sid", required=True)
    args = parser.parse_args()
    scope = (args.customer, args.run, args.sid)
    with psycopg.connect(os.getenv("OPS_DSN", "")) as connection:
        for key, value in zip(("app.customer_id", "app.run_id", "app.sid"), scope, strict=True):
            connection.execute("SELECT set_config(%s,%s,true)", (key, value))
        rows = connection.execute(
            "SELECT sequence,canonical,prev_hash,row_hash FROM ops.audit_log ORDER BY sequence"
        ).fetchall()
        count = verify(rows, scope)
    sys.stdout.write(f"Audit chain verified: {count} entries\n")


if __name__ == "__main__":
    main()
