"""One separately budgeted, owner-approved rerun of the frozen 36-case dev inventory."""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal

from evals.studies.llm import dev_post_v4 as study

SCOPE, RUN, CAP = "dev-gate/post-v4-rerun", "post-v4-rerun", Decimal("0.08")


def configure() -> None:
    # Only the offline runner changes: original fixtures, inventory and scorer stay identical.
    study.SCOPE, study.RUN_ID, study.CAP = SCOPE, RUN, CAP
    study.OUTPUT = study.ROOT / "artifacts/post-v4-rerun"
    study.OUTPUT.mkdir(parents=True, exist_ok=True, mode=0o700)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true")
    args = parser.parse_args()
    configure()
    sys.argv = [sys.argv[0], "after-real" if args.real else "triage-mock"]
    study.main()


if __name__ == "__main__":
    main()
