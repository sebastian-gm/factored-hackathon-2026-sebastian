"""Read-only release gate: require the promoted temporal-quality column."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg

from aclara.bank.serving import temporal_column_available


def verify(connection: psycopg.Connection, expected_fingerprint: str) -> dict[str, bool]:
    if not temporal_column_available(connection):
        raise RuntimeError("Temporal serving column unavailable; release blocked")
    row = connection.execute("SELECT identity FROM meta.serving_state WHERE singleton").fetchone()
    if row is None or row[0].get("build_fingerprint") != expected_fingerprint:
        raise RuntimeError(
            "Promoted serving fingerprint differs from rebuilt gold; release blocked"
        )
    return {"temporal_column_available": True, "promoted_fingerprint_matches": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity-file", type=Path, required=True)
    args = parser.parse_args()
    expected = json.loads(args.identity_file.read_text()).get("build_fingerprint")
    if not isinstance(expected, str) or not expected:
        raise RuntimeError("Rebuilt promotion fingerprint is required")
    dsn = os.getenv("SERVING_VERIFY_DSN", "")
    if not dsn:
        raise RuntimeError(
            "SERVING_VERIFY_DSN is required; never pass its value on the command line"
        )
    try:
        with psycopg.connect(
            dsn, connect_timeout=10, options="-c default_transaction_read_only=on"
        ) as db:
            result = verify(db, expected)
    except psycopg.Error:
        raise RuntimeError(
            "Temporal serving connection failed; private connection details suppressed"
        ) from None
    sys.stdout.write(json.dumps(result) + "\n")


if __name__ == "__main__":
    main()
