"""Write or verify the checked-in machine-readable interface snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aclara.api.app import app
from aclara.evals.schema import ScenarioSuite

ROOT = Path(__file__).resolve().parents[1]
INTERFACES = ROOT / "contracts" / "interfaces"


def scenario_schema() -> dict[str, Any]:
    """Compose the authored v2 schema with the unchanged runtime v1 definitions."""
    legacy = ScenarioSuite.model_json_schema()
    definitions = json.loads((ROOT / "contracts/scenario-v2-definitions.json").read_text())
    definitions.update(legacy["$defs"])
    definitions["ScenarioSuiteV1"] = {k: v for k, v in legacy.items() if k != "$defs"}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": definitions,
        "oneOf": [{"$ref": "#/$defs/ScenarioSuiteV1"}, {"$ref": "#/$defs/ScenarioSuiteV2"}],
    }


SNAPSHOTS: dict[Path, dict[str, Any]] = {
    INTERFACES / "openapi.json": app.openapi(),
    INTERFACES / "scenario-suite.schema.json": scenario_schema(),
}


def _render(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if a snapshot is stale")
    args = parser.parse_args()
    stale: list[str] = []
    for path, value in SNAPSHOTS.items():
        expected = _render(value)
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    if stale:
        for path in stale:
            sys.stderr.write(f"STALE INTERFACE: {path}; run `make interfaces`\n")
        return 1
    sys.stdout.write(
        "interface snapshots are current\n" if args.check else "interface snapshots written\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
