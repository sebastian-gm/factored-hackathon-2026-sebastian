"""CLI entry point for the local data pipeline."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from dotenv import dotenv_values


def main() -> int:
    dotenv = dotenv_values(Path(".env")) if Path(".env").is_file() else {}
    source_default = os.getenv("LOCAL_RAW_DIR") or dotenv.get("LOCAL_RAW_DIR")
    lake_default = (
        os.getenv("LAKE_DIR") or dotenv.get("LAKE_DIR") or str(Path.home() / "aclara-lake")
    )
    if not os.getenv("BANK_CLOCK") and dotenv.get("BANK_CLOCK"):
        os.environ["BANK_CLOCK"] = str(dotenv["BANK_CLOCK"])
    from aclara.data.snapshot import PromotionBlocked, build_snapshot

    parser = argparse.ArgumentParser(prog="aclara data")
    parser.add_argument("command", choices=("build", "serve-load"))
    parser.add_argument("--source", type=Path, default=source_default)
    parser.add_argument("--lake", type=Path, default=lake_default)
    parser.add_argument("--no-reports", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    lake = Path(args.lake).expanduser()
    if args.command == "serve-load":
        from aclara.data.serving_load import load_serving

        dsn = os.getenv("DATA_LOAD_DSN")
        if not dsn:
            parser.error("set DATA_LOAD_DSN to the local owner connection (never log it)")
        try:
            load_serving(lake, dsn)
        except Exception as exc:
            # Driver errors may include credentials or source values.
            logging.error("Serving load failed (%s); success not verified", type(exc).__name__)
            return 1
        return 0
    if args.source is None:
        parser.error("set LOCAL_RAW_DIR or pass --source")
    try:
        build_snapshot(Path(args.source), lake, reports=not args.no_reports)
    except PromotionBlocked as exc:
        logging.error("%s", exc)
        return 1
    except Exception as exc:
        # CSV, database and schema exceptions can include source values.
        logging.error("Pipeline failed (%s); no promotion reported", type(exc).__name__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
