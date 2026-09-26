"""CLI entry point for the local data pipeline."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from aclara.data.pipeline import build


def main() -> int:
    parser = argparse.ArgumentParser(prog="aclara data")
    parser.add_argument("command", choices=("build",))
    parser.add_argument("--source", type=Path, default=os.getenv("LOCAL_RAW_DIR"))
    parser.add_argument("--lake", type=Path, default=os.getenv("LAKE_DIR", "lake"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.source is None:
        parser.error("set LOCAL_RAW_DIR or pass --source")
    build(args.source, args.lake)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
