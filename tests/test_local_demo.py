"""Local demo isolation and verification, using authored values only."""

from __future__ import annotations

import io
import json
import subprocess
import urllib.error
from pathlib import Path

import pytest
from scripts import local_demo


def test_configuration_is_private_isolated_and_idempotent(tmp_path: Path) -> None:
    existing = tmp_path / ".env"
    existing.write_text("untouched-worktree-settings\n")
    path, values = local_demo.configuration(tmp_path, "es")
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert local_demo.configuration(tmp_path, "es") == (path, values)
    assert existing.read_text() == "untouched-worktree-settings\n"
    assert values["LLM_PROVIDER"] == "mock" and values["LEDGER_BACKEND"] == "fixture"
    assert values["LLM_REAL_CALLS_APPROVED"] == "0"
    _, pt = local_demo.configuration(tmp_path, "pt")
    assert pt["COMPOSE_PROJECT_NAME"] != values["COMPOSE_PROJECT_NAME"]
    assert pt["DEMO_USERNAME"] == "demo.pt.br" and pt["DEMO_LOCALE"] == "pt-BR"
    assert not any("API_KEY" in key for key in values)


def test_demo_rejects_paid_mode_or_another_checkout(tmp_path: Path) -> None:
    path, _ = local_demo.configuration(tmp_path, "es")
    path.write_text(path.read_text().replace("LLM_PROVIDER=mock", "LLM_PROVIDER=openrouter"))
    with pytest.raises(ValueError, match="mock"):
        local_demo.configuration(tmp_path, "es")
    path.write_text(
        path.read_text().replace("COMPOSE_PROJECT_NAME=", "COMPOSE_PROJECT_NAME=other-")
    )
    with pytest.raises(ValueError, match="another checkout"):
        local_demo.configuration(tmp_path, "es")


def test_only_local_docker_and_scoped_compose_are_allowed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DOCKER_HOST", "tcp://remote.invalid:2376")
    with pytest.raises(ValueError, match="local Docker"):
        local_demo.local_docker()
    monkeypatch.setenv("DOCKER_HOST", "unix:///authored-local.sock")
    local_demo.local_docker()
    path, values = local_demo.configuration(tmp_path, "es")
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(local_demo.subprocess, "run", run)
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    local_demo.compose(tmp_path, path, values, ["down"])
    command, options = calls[0]
    assert command[-1] == "down" and "--volumes" not in command
    assert command[command.index("--project-name") + 1] == values["COMPOSE_PROJECT_NAME"]
    assert str(path) in command and "docker-compose.demo.yml" in command[-2]
    assert values["DEMO_PASSWORD"] not in command
    assert options["env"]["LLM_PROVIDER"] == "mock"


def test_readback_requires_live_bff_fixture_rows_and_revoked_session(
    tmp_path: Path, monkeypatch
) -> None:
    _, values = local_demo.configuration(tmp_path, "es")
    authenticated = False
    paths = []

    class Client:
        def open(self, req, timeout):
            nonlocal authenticated
            path = req.full_url.split("/api/bff/")[1]
            paths.append(path)
            responses = {
                "config": {"fixtures": False},
                "auth/login": {"challenge_id": "authored-challenge"},
                "auth/challenges/authored-challenge/sms": {"code": "000000"},
                "auth/otp/verify": {},
                "me": {"role": "ops", "locale": "es-MX"},
                "transactions": [{"handle": "authored-handle"}],
                "ops/snapshot": {"source_kind": "authored_fixture", "quality": [{"passed": True}]},
                "auth/logout": {},
            }
            if path == "auth/otp/verify":
                authenticated = True
            if path == "auth/logout":
                authenticated = False
            if path == "me" and not authenticated:
                raise urllib.error.HTTPError(req.full_url, 401, "revoked", {}, None)
            return io.BytesIO(json.dumps(responses[path]).encode())

    monkeypatch.setattr(local_demo.urllib.request, "build_opener", lambda *args: Client())
    receipt = local_demo.verify(values)
    assert receipt["fixture_rows"] == 1 and receipt["login_otp_logout_verified"]
    assert receipt["model_cost_usd"] == 0
    assert not any("chat" in path or "confirm" in path for path in paths)
