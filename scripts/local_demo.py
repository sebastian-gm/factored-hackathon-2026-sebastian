"""Isolated, localhost-only Compose demo; no provider key or existing .env read."""

# ruff: noqa: S603, S607, S310, T201 -- fixed Docker commands and localhost HTTP URLs; no secrets printed.
from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLOCK = "2026-06-18T06:00:00Z"


def configuration(root: Path, language: str) -> tuple[Path, dict[str, str]]:
    """Reuse only this checkout/language's private generated configuration."""
    if language not in {"es", "pt"}:
        raise ValueError("Demo language must be es or pt")
    directory = root / "artifacts/demo" / language
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not directory.resolve().is_relative_to(root.resolve()) or directory.is_symlink():
        raise ValueError("Demo storage must stay inside this checkout")
    directory.chmod(0o700)
    path = directory / ".env"
    project = (
        "aclara-demo-"
        + hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:10]
        + "-"
        + language
    )
    if path.is_symlink():
        raise ValueError("Demo configuration must not be a symlink")
    if path.exists():
        values = dict(line.split("=", 1) for line in path.read_text().splitlines())
        if values.get("COMPOSE_PROJECT_NAME") != project:
            raise ValueError("Demo configuration belongs to another checkout")
    else:
        with socket.socket() as pg, socket.socket() as api, socket.socket() as web:
            for listener in (pg, api, web):
                listener.bind(("127.0.0.1", 0))
            values = {
                "COMPOSE_PROJECT_NAME": project,
                "POSTGRES_HOST_PORT": str(pg.getsockname()[1]),
                "API_HOST_PORT": str(api.getsockname()[1]),
                "WEB_HOST_PORT": str(web.getsockname()[1]),
                "POSTGRES_USER": "aclara_demo",
                "POSTGRES_DB": "aclara_demo",
                "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
                "OPS_APP_PASSWORD": secrets.token_urlsafe(32),
                "DEMO_PASSWORD": secrets.token_urlsafe(32),
                "DEMO_USERNAME": "demo.pt.br" if language == "pt" else "demo.es.mx",
                "DEMO_LOCALE": "pt-BR" if language == "pt" else "es-MX",
                "DEMO_ROLE": "ops",
                "LEDGER_BACKEND": "fixture",
                "LLM_PROVIDER": "mock",
                "LLM_REAL_CALLS_APPROVED": "0",
                "ALLOW_DEMO_RESET": "false",
                "BANK_CLOCK": CLOCK,
            }
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
    path.chmod(0o600)
    for key, expected in {
        "LEDGER_BACKEND": "fixture",
        "LLM_PROVIDER": "mock",
        "LLM_REAL_CALLS_APPROVED": "0",
        "DEMO_ROLE": "ops",
        "BANK_CLOCK": CLOCK,
    }.items():
        if values.get(key) != expected:
            raise ValueError("Demo configuration must use authored fixtures and mock models")
    ports = [int(values[key]) for key in ("POSTGRES_HOST_PORT", "API_HOST_PORT", "WEB_HOST_PORT")]
    if len(set(ports)) != 3 or any(not 1024 <= port <= 65535 for port in ports):
        raise ValueError("Invalid isolated demo ports")
    return path, values


def local_docker() -> None:
    """Do not accidentally create resources on a remote Docker context."""
    context = os.environ.get("DOCKER_CONTEXT")
    host = None if context else os.environ.get("DOCKER_HOST")
    if not host:
        host = subprocess.run(
            [
                "docker",
                "context",
                "inspect",
                *([context] if context else []),
                "--format",
                "{{.Endpoints.docker.Host}}",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    if not host.startswith(("unix://", "npipe://")):
        raise ValueError("make demo requires a local Docker Engine context")


def compose(root: Path, env_file: Path, values: dict[str, str], arguments: list[str]) -> None:
    environment = {**os.environ, **values}
    environment.pop("COMPOSE_PROFILES", None)
    log = env_file.parent / "setup.log"
    descriptor = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "a") as stream:
        subprocess.run(
            [
                "docker",
                "compose",
                "--env-file",
                str(env_file),
                "--project-name",
                values["COMPOSE_PROJECT_NAME"],
                "-f",
                str(root / "docker-compose.yml"),
                "-f",
                str(root / "docker-compose.demo.yml"),
                *arguments,
            ],
            cwd=root,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=True,
        )
    log.chmod(0o600)


def verify(values: dict[str, str]) -> dict[str, Any]:
    """Read back fixture scope and durable-store health; no dispute or handoff write."""
    origin = "http://localhost:" + values["WEB_HOST_PORT"]
    client = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
    )

    def request(path: str, body: dict[str, Any] | None = None) -> Any:
        req = urllib.request.Request(
            origin + "/api/bff/" + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Origin": origin, "Content-Type": "application/json"},
        )
        with client.open(req, timeout=180) as response:
            return json.load(response)

    config = request("config")
    if config.get("fixtures"):
        raise RuntimeError("The demo must use the live BFF and local bank API")
    challenge = request(
        "auth/login", {"username": values["DEMO_USERNAME"], "password": values["DEMO_PASSWORD"]}
    )
    sms = request("auth/challenges/" + challenge["challenge_id"] + "/sms")
    request("auth/otp/verify", {"challenge_id": challenge["challenge_id"], "code": sms["code"]})
    try:
        me, transactions, snapshot = request("me"), request("transactions"), request("ops/snapshot")
        if me["role"] != "ops" or me["locale"] != values["DEMO_LOCALE"] or not transactions:
            raise RuntimeError("Fixture persona/ledger readback failed")
        if snapshot["source_kind"] != "authored_fixture" or not all(
            item["passed"] for item in snapshot["quality"]
        ):
            raise RuntimeError("Authored ledger or operational-store readback failed")
    finally:
        request("auth/logout", {})
    try:
        request("me")
    except urllib.error.HTTPError as error:
        if error.code != 401:
            raise
    else:
        raise RuntimeError("Logout readback failed")
    return {
        "fixture_rows": len(transactions),
        "live_bff": True,
        "login_otp_logout_verified": True,
        "model_cost_usd": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--language", choices=("es", "pt"), default=os.getenv("DEMO_LANGUAGE", "es")
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop only this demo; preserve its volume"
    )
    parser.add_argument("--check", action="store_true", help="Read back an already running demo")
    args = parser.parse_args()
    started = time.monotonic()
    local_docker()
    env_file, values = configuration(ROOT, args.language)
    if args.stop:
        compose(ROOT, env_file, values, ["down"])
        print("Stopped this checkout's local demo; its database volume is preserved.")
        return
    if not args.check:
        print("Starting isolated localhost Postgres, mock bank API and web app…", flush=True)
        compose(
            ROOT, env_file, values, ["up", "--build", "--detach", "--wait", "--wait-timeout", "240"]
        )
    receipt = {**verify(values), "seconds": round(time.monotonic() - started, 2)}
    receipt_file = env_file.parent / "verification.json"
    receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
    receipt_file.chmod(0o600)
    if json.loads(receipt_file.read_text()) != receipt:
        raise RuntimeError("Verification receipt readback failed")
    print("Verified local demo: http://localhost:" + values["WEB_HOST_PORT"])
    print(
        "Persona: "
        + values["DEMO_USERNAME"]
        + " · "
        + values["DEMO_LOCALE"]
        + " · local Chat / Agent Desk / Ops"
    )
    print(
        "Password: open DEMO_PASSWORD in "
        + str(env_file.relative_to(ROOT))
        + " (private; not printed)"
    )
    print(
        "Use the simulated SMS OTP on the login screen. Authored fixtures; mock models; model spend $0."
    )
    print("Stop: make demo-stop" + (" DEMO_LANGUAGE=pt" if args.language == "pt" else ""))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(
            "Local demo failed ("
            + type(error).__name__
            + "). Inspect the private artifacts/demo/<language>/setup.log; no verified success claimed.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
