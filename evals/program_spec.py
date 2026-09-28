"""Approved v3 workload metadata. Importing this module reads no frozen inputs."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "evals/suites/test-v3"
BINDINGS = ROOT / "artifacts/evaluation-v3/customer-bindings.json"
MANIFEST_SHA256 = "ecf3f6313f33359fed892de1b3537edc4ae8e854dd5bfa8da1fc8845daa41177"
WORKLOAD = (("B1", 0, None), ("P", 0, "default"), ("P", 1, "default"), ("P", 2, "default"))
CATEGORIES = {
    "normal": 35,
    "ambiguous_unsupported": 20,
    "human_required": 20,
    "security_robustness": 25,
}
LANGUAGES = {"es": 48, "pt": 48, "mixed": 4}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_envelope() -> dict:
    """Preparation reads only manifest/provenance and opaque binding bytes."""
    if digest(RELEASE / "MANIFEST.sha256") != MANIFEST_SHA256:
        raise ValueError("Frozen manifest differs from the approved PR pin")
    provenance = json.loads((RELEASE / "provenance.json").read_text())
    entries = dict(
        line.split("  ", 1)[::-1] for line in (RELEASE / "MANIFEST.sha256").read_text().splitlines()
    )
    if digest(RELEASE / "provenance.json") != entries["provenance.json"]:
        raise ValueError("Frozen provenance checksum mismatch")
    binding_sha = digest(BINDINGS)
    if binding_sha != provenance["bindings_audit"]["private_bindings_sha256"]:
        raise ValueError("Private binding differs from its frozen provenance pin")
    if BINDINGS.stat().st_mode & 0o777 != 0o600:
        raise ValueError("Private bindings require mode 0600")
    return {"manifest_sha256": MANIFEST_SHA256, "binding_sha256": binding_sha}


def load_payloads(directory: Path) -> dict:
    """Generic schema/integrity validation, invoked only inside the start gate."""
    entries = {}
    for line in (directory / "MANIFEST.sha256").read_text().splitlines():
        checksum, name = line.split("  ", 1)
        if Path(name).name != name or name in {".", "..", "MANIFEST.sha256"} or name in entries:
            raise ValueError("Invalid manifest entry")
        entries[name] = checksum
        if digest(directory / name) != checksum:
            raise ValueError("Frozen file checksum mismatch")
    if set(entries) != {
        p.name for p in directory.iterdir() if p.is_file() and p.name != "MANIFEST.sha256"
    }:
        raise ValueError("Frozen file inventory changed")
    schema = json.loads((ROOT / "contracts/interfaces/scenario-suite.schema.json").read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    parts = []
    for path in sorted(directory.glob("scenarios-*.yaml")):
        part = yaml.safe_load(path.read_text())
        validator.validate(part)
        parts.append(part)
    if not parts or len({(p["version"], p["suite_id"], p["dataset_version"]) for p in parts}) != 1:
        raise ValueError("Inconsistent suite envelopes")
    suite = {**parts[0], "scenarios": [s for part in parts for s in part["scenarios"]]}
    rows = suite["scenarios"]
    if len({s["id"] for s in rows}) != len(rows):
        raise ValueError("Duplicate scenario identities")
    return suite


def selections(suite: dict, directory: Path) -> tuple[set[str], set[str]]:
    rows = suite["scenarios"]
    if (
        len(rows) != 100
        or Counter(s["category"] for s in rows) != CATEGORIES
        or Counter(s["language"] for s in rows) != LANGUAGES
    ):
        raise ValueError("Suite counts differ from approved metadata")
    ids = {s["id"] for s in rows}
    chosen = []
    for name in ("repeat-selection.json", "judge-selection.json"):
        values = json.loads((directory / name).read_text())["scenario_ids"]
        if len(values) != 30 or len(set(values)) != 30 or not set(values) <= ids:
            raise ValueError("Invalid preselected workload")
        chosen.append(set(values))
    return chosen[0], chosen[1]
