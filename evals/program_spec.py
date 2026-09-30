"""Approved program envelopes. Configuration/imports read no frozen inputs."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from psycopg.conninfo import conninfo_to_dict

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


@dataclass(frozen=True)
class ProgramSpec:
    suite: str
    bindings: Path
    manifest_pin: str

    @property
    def release(self) -> Path:
        return ROOT / "evals/suites" / self.suite

    @property
    def scope(self) -> str:
        return "final-evaluation-" + self.suite.removeprefix("test-")

    @property
    def run_id(self) -> str:
        return "final-program-" + self.suite.removeprefix("test-")

    @property
    def output(self) -> Path:
        return ROOT / "artifacts" / self.run_id

    def identity(self) -> dict[str, str]:
        return {
            "suite": self.suite,
            "bindings": str(self.bindings.relative_to(ROOT)),
            "manifest_pin": self.manifest_pin,
            "scope": self.scope,
            "run_id": self.run_id,
        }


MANIFEST_PINS = {
    "test-v3": MANIFEST_SHA256,
    "test-v4": "309c3aa22c2eab51b3289075b733c52bb7934a879299762c3fb9ba16a3d9bec8",
}


def specification(
    suite: str, bindings: str | Path | None = None, manifest_pin: str | None = None
) -> ProgramSpec:
    """Resolve only approved metadata, without inspecting suite or binding files."""
    if suite not in MANIFEST_PINS:
        raise ValueError("Suite is outside the approved program metadata")
    pin = MANIFEST_PINS[suite]
    if manifest_pin is not None and manifest_pin != pin:
        raise ValueError("Manifest pin differs from the approved release")
    path = (
        Path(bindings)
        if bindings
        else Path(f"artifacts/evaluation-{suite[5:]}/customer-bindings.json")
    )
    path = (ROOT / path).resolve()
    if not path.is_relative_to(ROOT / "artifacts"):
        raise ValueError("Private bindings must remain in ignored repository artifacts")
    return ProgramSpec(suite, path, pin)


def add_arguments(parser) -> None:
    parser.add_argument("--suite", choices=tuple(MANIFEST_PINS), default="test-v4")
    parser.add_argument("--bindings", help="Ignored private binding path; never its contents")
    parser.add_argument("--manifest-pin", help="Must equal the approved suite manifest SHA256")


def serving_pin(spec: ProgramSpec) -> dict[str, str]:
    """Reject remote/owner serving connections before any secret/provider access."""
    if spec.suite != "test-v4":
        return {"location": "legacy"}
    dsn = os.getenv("EVAL_SERVING_DSN")
    if not dsn:
        raise ValueError("V4 requires an explicit local EVAL_SERVING_DSN")
    try:
        values = conninfo_to_dict(dsn)
    except Exception:
        raise ValueError("Invalid local serving connection configuration") from None
    if (
        values.get("host") not in {"localhost", "127.0.0.1", "::1"}
        or values.get("hostaddr", "127.0.0.1") not in {"127.0.0.1", "::1"}
        or values.get("user") != "aclara_app"
        or not values.get("dbname")
        or values.get("service")
    ):
        raise ValueError("V4 serving requires a local non-owner aclara_app connection")
    # Never include passwords/DSNs. Pin endpoint and role across prepare/resume.
    return {
        "location": "local",
        **{
            name: values.get(name, "5432" if name == "port" else "")
            for name in ("host", "hostaddr", "port", "dbname", "user")
        },
    }


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_envelope(spec: ProgramSpec | None = None) -> dict:
    """Preparation reads only manifest/provenance and opaque binding bytes."""
    directory = spec.release if spec else RELEASE
    bindings = spec.bindings if spec else BINDINGS
    pin = spec.manifest_pin if spec else MANIFEST_SHA256
    if digest(directory / "MANIFEST.sha256") != pin:
        raise ValueError("Frozen manifest differs from the approved PR pin")
    provenance = json.loads((directory / "provenance.json").read_text())
    entries = dict(
        line.split("  ", 1)[::-1]
        for line in (directory / "MANIFEST.sha256").read_text().splitlines()
    )
    if digest(directory / "provenance.json") != entries["provenance.json"]:
        raise ValueError("Frozen provenance checksum mismatch")
    binding_sha = digest(bindings)
    if binding_sha != provenance["bindings_audit"]["private_bindings_sha256"]:
        raise ValueError("Private binding differs from its frozen provenance pin")
    if bindings.stat().st_mode & 0o777 != 0o600:
        raise ValueError("Private bindings require mode 0600")
    return {"manifest_sha256": pin, "binding_sha256": binding_sha}


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
