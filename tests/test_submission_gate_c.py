"""Authored publication guards; no Azure, GitHub or frozen-suite access."""

import copy
import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from scripts import submission_gate_c as gate

SHA = "a" * 40
DEPLOYED = "b" * 40
DIGEST = "sha256:" + "c" * 64


def evidence(now):
    release = {
        "implementation_sha": SHA,
        "deployed_sha": DEPLOYED,
        "verified_at": now.isoformat(),
        "controls_verified": True,
        "real_smoke_verified": True,
        "ci_verified": True,
        "judge_access_enabled": True,
        "min_replicas": 1,
        "application_images": {
            name: {"tag": f"fixture.example/aclara-{name}:{DEPLOYED}", "digest": DIGEST}
            for name in ("api", "web")
        },
    }
    audit = {
        "sha": SHA,
        "verified_at": now.isoformat(),
        "git_refs_sha256": "refs",
        "github_inventory_sha256": "github",
        "gitleaks_findings": 0,
        **dict.fromkeys(gate.AUDIT_CHECKS, True),
    }
    return release, audit


def validate(release, audit, now):
    gate.verify_evidence(
        release, audit, sha=SHA, deployed_sha=DEPLOYED, refs="refs", github="github", now=now
    )


@pytest.mark.parametrize(
    "where,key,value",
    [
        ("release", "implementation_sha", DEPLOYED),
        ("release", "deployed_sha", SHA),
        ("release", "real_smoke_verified", False),
        ("release", "judge_access_enabled", False),
        ("release", "min_replicas", 0),
        ("release", "application_images", {"api": {}, "web": {}}),
        ("audit", "sha", DEPLOYED),
        ("audit", "git_refs_sha256", "drift"),
        ("audit", "github_inventory_sha256", "drift"),
        ("audit", "gitleaks_findings", 1),
        *[("audit", key, False) for key in gate.AUDIT_CHECKS],
    ],
)
def test_missing_or_stale_acceptance_fails_closed(where, key, value):
    now = datetime.now(UTC)
    release, audit = evidence(now)
    validate(release, audit, now)
    (release if where == "release" else audit)[key] = value
    with pytest.raises(gate.GateError):
        validate(release, audit, now)


@pytest.mark.parametrize("stamp", ["invalid", "2026-10-03T00:00:00", "old", "future"])
def test_receipt_age_and_timezone_required(stamp):
    now = datetime.now(UTC)
    value = {
        "old": (now - timedelta(hours=25)).isoformat(),
        "future": (now + timedelta(minutes=1)).isoformat(),
    }.get(stamp, stamp)
    assert not gate.fresh(value, now)


def test_approval_is_owner_day_gate_and_both_sha_specific():
    now = datetime.now(UTC)
    approval = {
        "approved_by": "Sebastian",
        "gate": "C",
        "sha": SHA,
        "deployed_sha": DEPLOYED,
        "approved_on": now.date().isoformat(),
        "publish_repo": True,
        "tag_and_release": True,
    }
    gate.verify_approval(approval, SHA, DEPLOYED, now)
    for key, value in (
        ("gate", "B"),
        ("approved_by", "operator"),
        ("deployed_sha", SHA),
        ("approved_on", "2020-01-01"),
        ("publish_repo", False),
        ("tag_and_release", False),
    ):
        bad = {**approval, key: value}
        with pytest.raises(gate.GateError):
            gate.verify_approval(bad, SHA, DEPLOYED, now)


def test_ruleset_requires_every_check_no_bypass_and_no_rewrite():
    actual = copy.deepcopy(gate.ruleset())
    for row in actual["rules"][-1]["parameters"]["required_status_checks"]:
        row["integration_id"] = None  # GitHub expands this default on readback.
    gate.verify_ruleset(actual)
    for mutate in (
        lambda r: r.update(enforcement="evaluate"),
        lambda r: r.update(bypass_actors=[{"actor_type": "RepositoryRole", "actor_id": 5}]),
        lambda r: r["rules"].pop(0),
        lambda r: r["rules"][-1]["parameters"].update(strict_required_status_checks_policy=False),
        lambda r: r["rules"][-1]["parameters"]["required_status_checks"].pop(),
    ):
        bad = copy.deepcopy(actual)
        mutate(bad)
        with pytest.raises(gate.GateError):
            gate.verify_ruleset(bad)


def test_latest_workflow_failure_cannot_hide_behind_earlier_success(monkeypatch):
    runs = [
        {
            "name": name,
            "head_branch": "main",
            "run_number": 1,
            "run_attempt": 1,
            "status": "completed",
            "conclusion": "success",
        }
        for name in ("ci", "safety", "azure-access")
    ]
    runs.append({**runs[0], "run_attempt": 2, "conclusion": "failure"})
    monkeypatch.setattr(gate, "pages", lambda *args: runs)
    with pytest.raises(gate.GateError, match="not green"):
        gate.verify_workflows(SHA)


@pytest.mark.parametrize(
    "urls",
    [
        "https://example.invalid/wrong.git",
        "",
        "git@github.com:other/repo.git",
        "\n".join([f"https://github.com/{gate.REPOSITORY}.git"] * 2),
    ],
)
def test_origin_rejects_wrong_missing_or_multiple_destinations(monkeypatch, urls):
    monkeypatch.setattr(gate, "git", lambda *args: urls)
    with pytest.raises(gate.GateError, match="Origin differs"):
        gate.verify_origin()


def test_origin_checks_fetch_and_push_independently(monkeypatch):
    calls = []

    def origin(*args):
        calls.append(args)
        return "git@github.com:" + (
            "wrong/repository.git" if "--push" in args else gate.REPOSITORY + ".git"
        )

    monkeypatch.setattr(gate, "git", origin)
    with pytest.raises(gate.GateError, match="Origin differs"):
        gate.verify_origin()
    assert len(calls) == 2 and "--push" in calls[1]


def test_api_pins_github_host_even_with_another_cli_default(monkeypatch):
    calls = []
    monkeypatch.setenv("GH_HOST", "fixture.invalid")
    monkeypatch.setattr(gate, "command", lambda argv, **kwargs: calls.append(argv) or "{}")
    assert gate.api("rulesets", method="POST", value={}) == {}
    assert calls[0][calls[0].index("--hostname") + 1] == "github.com"


def test_notes_scan_uses_audited_config_and_disables_inline_ignore(monkeypatch, tmp_path):
    calls = []
    (tmp_path / "empty-ignore").write_text("")

    def scanner(argv, **kwargs):
        calls.append(argv)
        Path(argv[argv.index("--report-path") + 1]).write_text("[]")
        return ""

    monkeypatch.setattr(gate, "command", scanner)
    gate.scan_notes(Path("authored-gitleaks"), b"Authored aggregate notes", tmp_path)
    assert calls[0][calls[0].index("--config") + 1] == str(gate.ROOT / ".gitleaks.toml")
    assert "--ignore-gitleaks-allow" in calls[0]
    assert calls[0][calls[0].index("--gitleaks-ignore-path") + 1] == str(tmp_path / "empty-ignore")


@pytest.mark.parametrize(
    "changed_path,allowed",
    [
        ("docs/evidence.md", True),
        ("README.md", True),
        ("scripts/submission_gate_c.py", False),
        ("src/aclara/api/app.py", False),
    ],
)
def test_plan_never_changes_visibility_tags_releases_or_rules(
    monkeypatch, capsys, changed_path, allowed
):
    now = datetime.now(UTC)
    release, audit = evidence(now)
    audit["git_refs_sha256"] = gate.digest(["refs/heads/main " + SHA])
    calls = []

    def fake_git(*args):
        values = {
            ("status", "--porcelain"): "",
            ("branch", "--show-current"): "main",
            ("rev-parse", "HEAD"): SHA,
            ("rev-parse", "origin/main"): SHA,
            ("merge-base", "--is-ancestor", DEPLOYED, SHA): "",
            ("diff", "--name-only", DEPLOYED, SHA): changed_path,
            ("tag", "--list", gate.TAG): "",
            ("ls-remote", "origin", "refs/tags/v1.0.0"): "",
            ("for-each-ref", "--format=%(refname) %(objectname)"): "refs/heads/main " + SHA,
        }
        return values[args]

    def fake_api(path, **kwargs):
        calls.append((path, kwargs))
        return {"sha": SHA} if path == "commits/main" else {"private": True}

    monkeypatch.setattr(
        sys, "argv", ["gate-c", "--deployed-sha", DEPLOYED, "--audit-receipt", "audit.json"]
    )
    monkeypatch.setattr(gate, "git", fake_git)
    monkeypatch.setattr(gate, "verify_origin", lambda: None)
    monkeypatch.setattr(gate, "api", fake_api)
    monkeypatch.setattr(gate, "inventory", lambda: "github")
    monkeypatch.setattr(gate, "verify_workflows", lambda sha: None)
    monkeypatch.setattr(
        gate,
        "private_file",
        lambda p: json.dumps(audit if p.name == "audit.json" else release).encode(),
    )
    monkeypatch.setattr(gate, "publish", lambda *args: pytest.fail("Plan published"))
    assert gate.main() == (0 if allowed else 1)
    output = capsys.readouterr()
    if allowed:
        assert "No changes made" in output.out
    else:
        assert "Undeployed code differs" in output.err
    assert all(not kwargs for _, kwargs in calls)


def test_execution_uses_approved_notes_snapshot_even_if_original_changes(monkeypatch, tmp_path):
    now = datetime.now(UTC)
    release, audit = evidence(now)
    audit["git_refs_sha256"] = gate.digest(["refs/heads/main " + SHA])
    notes = tmp_path / "original-notes.md"
    approved_notes = b"Reviewed authored aggregate release notes.\n"
    notes.write_bytes(approved_notes)
    approval = {
        "gate": "C",
        "approved_by": "Sebastian",
        "sha": SHA,
        "deployed_sha": DEPLOYED,
        "approved_on": now.date().isoformat(),
        "publish_repo": True,
        "tag_and_release": True,
        "release_notes_sha256": hashlib.sha256(approved_notes).hexdigest(),
    }
    values = {
        "audit.json": json.dumps(audit).encode(),
        "approval.json": json.dumps(approval).encode(),
        "jev-release.json": json.dumps(release).encode(),
        "original-notes.md": approved_notes,
    }

    def fake_git(*args):
        if args[0] == "rev-parse":
            return SHA
        if args[0] == "branch":
            return "main"
        if args[0] == "for-each-ref":
            return "refs/heads/main " + SHA
        return ""

    published = []
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "gate-c",
            "--execute",
            "--deployed-sha",
            DEPLOYED,
            "--audit-receipt",
            "audit.json",
            "--approval",
            "approval.json",
            "--notes",
            str(notes),
            "--gitleaks",
            "authored-gitleaks",
        ],
    )
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    monkeypatch.setattr(gate, "git", fake_git)
    monkeypatch.setattr(gate, "verify_origin", lambda: None)
    monkeypatch.setattr(
        gate, "api", lambda path: {"sha": SHA} if path == "commits/main" else {"private": True}
    )
    monkeypatch.setattr(gate, "inventory", lambda: "github")
    monkeypatch.setattr(gate, "verify_workflows", lambda sha: None)
    monkeypatch.setattr(gate, "private_file", lambda p: values[p.name])
    monkeypatch.setattr(gate, "scan", lambda *args: None)
    monkeypatch.setattr(
        gate, "scan_notes", lambda *args: notes.write_bytes(b"Unapproved later contents")
    )
    monkeypatch.setattr(gate, "publish", lambda sha, deployed, p: published.append(p))
    assert gate.main() == 0
    assert len(published) == 1 and published[0] != notes
    assert published[0].read_bytes() == approved_notes
    assert published[0].stat().st_mode & 0o777 == 0o600


def test_failed_protection_restores_private_without_creating_tag(monkeypatch):
    changes = []

    def fake_api(path, *, method="GET", value=None):
        if path == "rulesets":
            raise gate.GateError("authored protection failure")
        changes.append(value["private"])

    monkeypatch.setattr(gate, "api", fake_api)
    monkeypatch.setattr(gate, "git", lambda *args: pytest.fail("Unsafe tag creation"))
    with pytest.raises(gate.GateError, match="restored private"):
        gate.publish(SHA, DEPLOYED, Path("notes.md"))
    assert changes == [False, True]


def test_publication_uses_deployed_sha_and_verifies_remote_tag(monkeypatch):
    commands = []

    def fake_api(path, **kwargs):
        if path == "rulesets":
            return {"id": 1}
        if path == "rulesets/1":
            return gate.ruleset()
        return {"private": False}

    def fake_git(*args):
        commands.append(args)
        return DEPLOYED + "\trefs/tags/v1.0.0^{}" if args[0] == "ls-remote" else ""

    monkeypatch.setattr(gate, "api", fake_api)
    monkeypatch.setattr(gate, "git", fake_git)
    monkeypatch.setattr(gate, "command", lambda argv: commands.append(argv))
    monkeypatch.setattr(
        gate, "verify_logged_out", lambda sha, deployed: commands.append((sha, deployed))
    )
    gate.publish(SHA, DEPLOYED, Path("notes.md"))
    assert commands[0][:4] == ("tag", "-a", "v1.0.0", DEPLOYED)
    release = next(c for c in commands if c[0] == "gh")
    assert release[release.index("--repo") + 1] == "github.com/" + gate.REPOSITORY
    assert release[release.index("--target") + 1] == DEPLOYED
    assert commands[-1] == (SHA, DEPLOYED)


def test_logged_out_check_rejects_lightweight_or_wrong_target_tag(monkeypatch):
    values = {
        "": {"private": False},
        "commits/main": {"sha": SHA},
        "readme": {"type": "file"},
        "git/ref/tags/v1.0.0": {"object": {"type": "tag", "sha": "c" * 40}},
        "git/tags/" + "c" * 40: {"object": {"type": "commit", "sha": SHA}},
    }
    monkeypatch.setattr(gate, "anonymous", lambda path: values[path])
    with pytest.raises(gate.GateError, match="wrong SHA"):
        gate.verify_logged_out(SHA, DEPLOYED)
    values["git/ref/tags/v1.0.0"]["object"]["type"] = "commit"
    with pytest.raises(gate.GateError, match="not annotated"):
        gate.verify_logged_out(SHA, DEPLOYED)
