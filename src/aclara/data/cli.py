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
    from aclara.data.pipeline import build

    parser = argparse.ArgumentParser(prog="aclara data")
    parser.add_argument("command", choices=("build",))
    parser.add_argument("--source", type=Path, default=source_default)
    parser.add_argument("--lake", type=Path, default=lake_default)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.source is None:
        parser.error("set LOCAL_RAW_DIR or pass --source")
    build(args.source, args.lake)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
