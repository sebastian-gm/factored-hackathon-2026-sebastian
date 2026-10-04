"""Prepare Gate C; publication requires a fresh, SHA-specific Sebastian approval."""

# ruff: noqa: S603, S607 -- fixed subprocess commands, no shell, Git always -C ROOT.
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "sebastian-gm/factored-hackathon-2026-sebastian"
TAG = "v1.0.0"
CHECKS = ("checks", "invariants", "postgres", "web")
AUDIT_CHECKS = (
    "current_tree_scrubbed",
    "full_history_scanned",
    "github_text_and_logs_scanned",
    "actions_artifacts_reviewed",
    "password_rotation_verified",
    "clean_clone_verified",
    "organizer_files_absent",
    "historical_metadata_disclosure_approved",
)


class GateError(RuntimeError):
    """A failed publication gate, without subprocess or private evidence output."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def fresh(value: Any, now: datetime) -> bool:
    try:
        timestamp = datetime.fromisoformat(value)
        return timestamp.tzinfo is not None and timedelta(0) <= now - timestamp <= timedelta(
            hours=24
        )
    except (TypeError, ValueError):
        return False


def private_file(path: Path) -> bytes:
    path = path.resolve()
    require(path.is_relative_to(ROOT / "artifacts"), "Evidence must be inside ignored artifacts")
    require(path.is_file() and path.stat().st_mode & 0o777 == 0o600, "Evidence requires mode 0600")
    command(["git", "-C", str(ROOT), "check-ignore", "--quiet", str(path)])
    return path.read_bytes()


def command(argv: list[str], *, data: str | None = None, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(argv, cwd=ROOT, input=data, text=True, capture_output=True, env=env)
    require(result.returncode == 0, "External command failed; details suppressed")
    return result.stdout.strip()


def git(*args: str) -> str:
    return command(["git", "-C", str(ROOT), *args])


def verify_origin() -> None:
    approved = {
        f"https://github.com/{REPOSITORY}",
        f"https://github.com/{REPOSITORY}.git",
        f"git@github.com:{REPOSITORY}.git",
    }
    for flags in ((), ("--push",)):
        urls = git("remote", "get-url", "--all", *flags, "origin").splitlines()
        require(
            len(urls) == 1 and urls[0] in approved, "Origin differs from the approved repository"
        )


def api(path: str, *, method: str = "GET", value: object | None = None) -> Any:
    args = [
        "gh",
        "api",
        f"repos/{REPOSITORY}/{path}",
        "--hostname",
        "github.com",
        "--method",
        method,
    ]
    if value is not None:
        args += ["--input", "-"]
    return json.loads(command(args, data=json.dumps(value) if value is not None else None))


def pages(path: str, field: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in range(1, 1001):
        result = api(f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
        batch = result[field] if field else result
        rows.extend(batch)
        if len(batch) < 100:
            return rows
    raise GateError("GitHub inventory pagination limit reached")


def inventory() -> str:
    """Hash metadata only; never open suite rows, bindings, workflow logs or prose."""
    records: dict[str, Any] = {}
    pulls = pages("pulls?state=all")
    records["pulls"] = [
        (p["number"], p["updated_at"], p["head"]["sha"], p["base"]["ref"]) for p in pulls
    ]
    records["reviews"] = [
        (p["number"], r["id"], r.get("submitted_at"), r["state"], digest(r.get("body")))
        for p in pulls
        for r in pages(f"pulls/{p['number']}/reviews")
    ]
    for name in ("issues/comments", "pulls/comments"):
        records[name] = [(r["id"], r["updated_at"]) for r in pages(name)]
    records["runs"] = [
        (r["id"], r["run_attempt"], r["updated_at"], r["status"], r["conclusion"])
        for r in pages("actions/runs", "workflow_runs")
    ]
    records["artifacts"] = [
        (a["id"], a["updated_at"], a["expired"], a["size_in_bytes"])
        for a in pages("actions/artifacts", "artifacts")
    ]
    records["releases"] = [(r["id"], r["updated_at"], r["tag_name"]) for r in pages("releases")]
    return digest(records)


def ruleset() -> dict[str, Any]:
    return {
        "name": "submission-main",
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 0,
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_review_thread_resolution": True,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [{"context": name} for name in CHECKS],
                    "strict_required_status_checks_policy": True,
                },
            },
        ],
    }


def verify_ruleset(value: dict[str, Any]) -> None:
    expected = ruleset()
    require(
        all(value.get(k) == expected[k] for k in expected if k != "rules"),
        "Main ruleset readback differs",
    )
    actual_rules = {r["type"]: r for r in value.get("rules", [])}
    for rule in expected["rules"]:
        actual = actual_rules.get(rule["type"], {})
        for key, wanted in rule.get("parameters", {}).items():
            actual_value = actual.get("parameters", {}).get(key)
            if key == "required_status_checks" and isinstance(actual_value, list):
                actual_value = [{"context": item.get("context")} for item in actual_value]
            require(actual_value == wanted, "Main ruleset parameter readback differs")
        require(bool(actual), "Main ruleset is missing a required rule")


def verify_workflows(sha: str) -> None:
    runs = pages(f"actions/runs?head_sha={sha}", "workflow_runs")
    for name in ("ci", "safety", "azure-access"):
        matching = [r for r in runs if r["name"] == name and r["head_branch"] == "main"]
        require(bool(matching), "Missing exact-SHA main workflow")
        latest = max(matching, key=lambda r: (r["run_number"], r["run_attempt"]))
        require(
            latest["status"] == "completed" and latest["conclusion"] == "success",
            "Latest exact-SHA main workflow is not green",
        )


def verify_evidence(
    release: dict[str, Any],
    audit: dict[str, Any],
    *,
    sha: str,
    deployed_sha: str,
    refs: str,
    github: str,
    now: datetime,
) -> None:
    require(bool(re.fullmatch(r"[0-9a-f]{40}", deployed_sha)), "Invalid deployed SHA")
    require(release.get("deployed_sha") == deployed_sha, "Deployed release SHA differs")
    require(release.get("implementation_sha") == sha, "Release readback is not pinned to main")
    require(fresh(release.get("verified_at"), now), "Fresh release readback required")
    require(
        all(
            release.get(k) is True
            for k in ("controls_verified", "real_smoke_verified", "ci_verified")
        ),
        "Release acceptance flags are incomplete",
    )
    require(
        release.get("judge_access_enabled") is True and release.get("min_replicas") == 1,
        "Gate A/B release evidence required",
    )
    images = release.get("application_images", {})
    for name in ("api", "web"):
        image = images.get(name, {})
        require(
            image.get("tag", "").endswith(":" + deployed_sha), "Image tag differs from deployed SHA"
        )
        require(
            bool(re.fullmatch(r"sha256:[0-9a-f]{64}", image.get("digest", ""))),
            "Invalid image digest",
        )
    require(
        audit.get("sha") == sha and fresh(audit.get("verified_at"), now),
        "Fresh main privacy audit required",
    )
    require(audit.get("git_refs_sha256") == refs, "Git refs changed since privacy audit")
    require(
        audit.get("github_inventory_sha256") == github,
        "GitHub inventory changed since privacy audit",
    )
    require(audit.get("gitleaks_findings") == 0, "Privacy audit has findings")
    require(
        all(audit.get(k) is True for k in AUDIT_CHECKS), "Privacy/reproduction audit is incomplete"
    )


def verify_approval(value: dict[str, Any], sha: str, deployed_sha: str, now: datetime) -> None:
    require(
        value.get("gate") == "C"
        and value.get("approved_by") == "Sebastian"
        and value.get("sha") == sha
        and value.get("deployed_sha") == deployed_sha
        and value.get("approved_on") == now.date().isoformat()
        and value.get("publish_repo") is True
        and value.get("tag_and_release") is True,
        "Current-day Sebastian Gate C approval for both SHAs required",
    )


def write_private(path: Path, value: object) -> None:
    write_bytes(path, (json.dumps(value, indent=2) + "\n").encode())


def write_bytes(path: Path, value: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as file:
        file.write(value)


def scan(binary: Path, audit: dict[str, Any], output: Path) -> None:
    require(binary.is_file(), "Gitleaks binary missing")
    require(
        hashlib.sha256(binary.read_bytes()).hexdigest() == audit.get("gitleaks_binary_sha256"),
        "Gitleaks binary differs from audited pin",
    )
    require(
        hashlib.sha256((ROOT / ".gitleaks.toml").read_bytes()).hexdigest()
        == audit.get("gitleaks_config_sha256"),
        "Gitleaks configuration changed",
    )
    # Native Gitleaks starts Git itself; enforce the repository boundary there too.
    wrapper = output / "git"
    wrapper.write_text(
        f"#!{sys.executable}\nimport os,sys\nos.execv(os.environ['GATE_C_GIT'],"
        f"[os.environ['GATE_C_GIT'],'-C',{str(ROOT)!r},*sys.argv[1:]])\n"
    )
    wrapper.chmod(0o700)
    original = shutil.which("git")
    require(original is not None, "Git executable missing")
    report = output / "full-history-secrets.json"
    empty_ignore = output / "empty-ignore"
    empty_ignore.write_text("")
    command(
        [
            str(binary),
            "git",
            str(ROOT),
            "--log-opts=--all --full-history --root --diff-merges=first-parent",
            "--redact",
            "--ignore-gitleaks-allow",
            "--gitleaks-ignore-path",
            str(empty_ignore),
            "--config",
            str(ROOT / ".gitleaks.toml"),
            "--report-format",
            "json",
            "--report-path",
            str(report),
        ],
        env={
            **os.environ,
            "PATH": str(output) + os.pathsep + os.environ["PATH"],
            "GATE_C_GIT": original,
        },
    )
    require(report.is_file(), "Gitleaks report missing")
    report.chmod(0o600)
    require(json.loads(report.read_text()) == [], "Full-history scan has findings")


def scan_notes(binary: Path, notes: bytes, output: Path) -> None:
    report = output / "release-notes-secrets.json"
    command(
        [
            str(binary),
            "stdin",
            "--redact",
            "--ignore-gitleaks-allow",
            "--gitleaks-ignore-path",
            str(output / "empty-ignore"),
            "--config",
            str(ROOT / ".gitleaks.toml"),
            "--report-format",
            "json",
            "--report-path",
            str(report),
        ],
        data=notes.decode(),
    )
    require(
        report.is_file() and json.loads(report.read_text()) == [],
        "Release notes secret scan failed",
    )
    report.chmod(0o600)


def anonymous(path: str) -> Any:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/{path}",
        headers={"User-Agent": "Aclara-Gate-C", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 -- fixed HTTPS origin
        return json.load(response)


def verify_logged_out(sha: str, deployed_sha: str) -> None:
    require(anonymous("").get("private") is False, "Logged-out repo is not public")
    require(anonymous("commits/main").get("sha") == sha, "Logged-out main SHA differs")
    require(anonymous("readme").get("type") == "file", "Logged-out README unavailable")
    ref = anonymous(f"git/ref/tags/{TAG}")["object"]
    require(ref["type"] == "tag", "Submission tag is not annotated")
    tag = anonymous(f"git/tags/{ref['sha']}")["object"]
    require(tag["type"] == "commit" and tag["sha"] == deployed_sha, "Public tag targets wrong SHA")
    release = anonymous(f"releases/tags/{TAG}")
    require(
        not release["draft"] and not release["prerelease"], "Public submission release unavailable"
    )


def publish(sha: str, deployed_sha: str, notes: Path) -> None:
    api("", method="PATCH", value={"private": False})
    try:
        value = api("rulesets", method="POST", value=ruleset())
        verify_ruleset(api(f"rulesets/{value['id']}"))
    except Exception:
        # Approval includes restoring privacy if protection cannot be established.
        api("", method="PATCH", value={"private": True})
        raise GateError("Main protection failed; restored private visibility") from None
    require(api("")["private"] is False, "Publication readback failed")
    git("tag", "-a", TAG, deployed_sha, "-m", "Aclara final submission release")
    git("push", "origin", f"refs/tags/{TAG}")
    require(
        git("ls-remote", "origin", f"refs/tags/{TAG}^{{}}").split()[0] == deployed_sha,
        "Tag readback differs",
    )
    args = [
        "gh",
        "release",
        "create",
        TAG,
        "--repo",
        "github.com/" + REPOSITORY,
        "--target",
        deployed_sha,
    ]
    args += ["--title", "Aclara v1.0.0", "--notes-file", str(notes)]
    command(args)
    verify_logged_out(sha, deployed_sha)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute", action="store_true", help="Requires explicit Gate C approval; default is plan"
    )
    parser.add_argument("--deployed-sha", required=True)
    parser.add_argument(
        "--release-receipt", type=Path, default=ROOT / "artifacts/azure/jev-release.json"
    )
    parser.add_argument("--audit-receipt", type=Path, required=True)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--notes", type=Path)
    parser.add_argument("--gitleaks", type=Path)
    args = parser.parse_args()
    try:
        os.umask(0o077)
        now = datetime.now(UTC)
        require(
            not git("status", "--porcelain") and git("branch", "--show-current") == "main",
            "Clean main required",
        )
        verify_origin()
        sha = git("rev-parse", "HEAD")
        require(sha == git("rev-parse", "origin/main"), "Main differs from origin/main")
        require(api("commits/main")["sha"] == sha, "Remote main differs")
        require(
            api("")["private"] is True,
            "Repository must still be private; partial publication requires owner review",
        )
        git("merge-base", "--is-ancestor", args.deployed_sha, sha)
        changed = git("diff", "--name-only", args.deployed_sha, sha).splitlines()
        require(
            all(p.startswith("docs/") or p in {"README.md", "CHANGELOG.md"} for p in changed),
            "Undeployed code differs from main",
        )
        require(not git("tag", "--list", TAG), "Submission tag already exists; never overwrite it")
        require(
            not git("ls-remote", "origin", f"refs/tags/{TAG}"),
            "Remote submission tag already exists",
        )
        release = json.loads(private_file(args.release_receipt))
        audit = json.loads(private_file(args.audit_receipt))
        refs = digest(git("for-each-ref", "--format=%(refname) %(objectname)").splitlines())
        verify_evidence(
            release,
            audit,
            sha=sha,
            deployed_sha=args.deployed_sha,
            refs=refs,
            github=inventory(),
            now=now,
        )
        verify_workflows(sha)
        if args.deployed_sha != sha:
            verify_workflows(args.deployed_sha)
        if not args.execute:
            sys.stdout.write(
                "PLAN verified: publish repository, protect main, annotate v1.0.0 at deployed SHA, create release, verify signed out. No changes made.\n"
            )
            return 0
        require(
            args.approval is not None and args.notes is not None and args.gitleaks is not None,
            "Execution requires approval, reviewed notes and pinned Gitleaks",
        )
        approval = json.loads(private_file(args.approval))
        verify_approval(approval, sha, args.deployed_sha, now)
        notes = private_file(args.notes)
        require(
            approval.get("release_notes_sha256") == hashlib.sha256(notes).hexdigest(),
            "Approval is not pinned to reviewed release notes",
        )
        output = ROOT / "artifacts/submission-day" / ("gate-c-" + now.strftime("%Y%m%dT%H%M%S"))
        output.mkdir(mode=0o700, parents=True, exist_ok=False)
        scan(args.gitleaks.resolve(), audit, output)
        scan_notes(args.gitleaks.resolve(), notes, output)
        require(api("commits/main")["sha"] == sha, "Remote main changed before publication")
        require(
            audit["github_inventory_sha256"] == inventory(),
            "GitHub inventory changed before publication",
        )
        write_private(
            output / "intent.json",
            {"sha": sha, "deployed_sha": args.deployed_sha, "approved_at": now.isoformat()},
        )
        frozen_notes = output / "release-notes.md"
        write_bytes(frozen_notes, notes)
        publish(sha, args.deployed_sha, frozen_notes)
        write_private(
            output / "complete.json",
            {
                "sha": sha,
                "deployed_sha": args.deployed_sha,
                "tag": TAG,
                "logged_out_verified": True,
            },
        )
        sys.stdout.write(
            "Gate C publication and signed-out verification complete. Email remains an owner action.\n"
        )
        return 0
    except (GateError, OSError, ValueError, KeyError, IndexError, TypeError) as error:
        message = str(error) if isinstance(error, GateError) else type(error).__name__
        sys.stderr.write("Gate C stopped: " + message + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
