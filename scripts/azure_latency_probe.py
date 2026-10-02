"""Approved ten-conversation probe through Azure BFF; duration/cost aggregates only."""

# ruff: noqa: T201, S603, S607 -- aggregate output and fixed repo-scoped git only.
from __future__ import annotations

import fcntl
import json
import math
import os
import re
import subprocess
import time
from datetime import UTC, datetime
from typing import Any

import httpx
from scripts.azure_dev import ROOT, VAULT, az, private_write, read_variables
from scripts.azure_migrate_ops import connection_string
from scripts.azure_targets import app_url
from scripts.release_smoke_budget import run_id, verify
from scripts.serving_smoke import check

from aclara.bank.serving import ServingRepository
from aclara.ops.store import Scope, Store
from aclara.settings import Settings


def bff_ms(header: str) -> float:
    match = re.fullmatch(r"aclara_bff;dur=(\d+\.\d{2})", header)
    if not match or not math.isfinite(value := float(match[1])):
        raise RuntimeError("Missing or invalid BFF duration-only Server-Timing")
    return value


def percentiles(values: list[float]) -> dict[str, float | int | None]:
    ordered = sorted(values)

    def quantile(q: float) -> float | None:
        if not ordered:
            return None
        position = (len(ordered) - 1) * q
        lo, hi = math.floor(position), math.ceil(position)
        return round(ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo), 2)

    return {"n": len(values), "p50_ms": quantile(0.5), "p95_ms": quantile(0.95)}


def summarize(items: list[dict[str, Any]], startup: list[dict[str, Any]]) -> dict:
    return {
        "all_turns_bff": percentiles([x["bff_ms"] for x in items]),
        "all_turns_client": percentiles([x["client_ms"] for x in items]),
        "startup_excluded_bff": percentiles([x["bff_ms"] for x in items if x["conversation"] > 0]),
        "startup_excluded_client": percentiles(
            [x["client_ms"] for x in items if x["conversation"] > 0]
        ),
        "startup_read_and_auth_bff": percentiles([x["bff_ms"] for x in startup]),
        "startup_read_and_auth_client": percentiles([x["client_ms"] for x in startup]),
        "definition": (
            "BFF processing measured inside Azure, includes API/provider/budget/read-back. "
            "Client timing includes workstation network. All turns exclude config/auth/session setup; "
            "startup-excluded additionally excludes the first conversation. No forced cold restart. "
            "Header excludes ingress scheduling/module loading before the handler; client startup retains it."
        ),
    }


def main() -> None:
    if (
        os.getenv("AZURE_LATENCY_PROBE_APPROVED") != "1"
        or os.getenv("LLM_REAL_CALLS_APPROVED") != "1"
    ):
        raise RuntimeError("Released-main latency probe needs owner approval")
    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
    ).strip():
        raise RuntimeError("Clean released main required")
    if (
        subprocess.check_output(
            ["git", "-C", str(ROOT), "branch", "--show-current"], text=True
        ).strip()
        != "main"
    ):
        raise RuntimeError("Main required")
    if (
        subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "origin/main"], text=True
        ).strip()
        != sha
    ):
        raise RuntimeError("Released main must equal origin/main")
    acceptance = json.loads((ROOT / "artifacts/azure/jev-release.json").read_text())
    if acceptance.get("implementation_sha", acceptance.get("release")) != sha or not all(
        acceptance.get(k) is True
        for k in ("controls_verified", "real_smoke_verified", "ci_verified")
    ):
        raise RuntimeError("Full release acceptance at this SHA required")
    name = run_id("latency", sha)
    variables = read_variables()
    if variables.get("image_tag") != sha or variables.get("llm_budget_run_id") != name:
        raise RuntimeError("Deployed SHA-bound latency purse required")
    web = app_url("web")
    owner = connection_string("aclara_admin")
    budget = verify(owner, "latency", sha)
    if budget["charged_with_reserves_usd"] >= 0.10 or budget["unknown_cost_attempts"]:
        raise RuntimeError("Latency purse exhausted or has unknown costs")
    output = ROOT / f"artifacts/azure/{name}"
    output.mkdir(parents=True, exist_ok=True)
    with (output / "probe.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (output / "launch.json").exists():
            raise RuntimeError("Probe already attempted; do not repeat paid conversations")
        private_write(
            output / "launch.json",
            json.dumps(
                {
                    "sha": sha,
                    "run_id": name,
                    "planned": 10,
                    "started_at": datetime.now(UTC).isoformat(),
                }
            ),
        )
        password = az(
            "keyvault", "secret", "show", "--vault-name", VAULT, "--name", "demo-password"
        )["value"]
        items: list[dict[str, Any]] = []
        startup: list[dict[str, Any]] = []
        completed = 0
        store = Store(connection_string("aclara_app"))
        try:
            personas = ServingRepository(store, Settings().bank_clock).personas()
            for i in range(10):
                pt = i % 2 == 1
                with httpx.Client(
                    base_url=web + "/api/bff/", headers={"Origin": web}, timeout=190
                ) as client:

                    def call(
                        method: str,
                        path: str,
                        body: dict | None = None,
                        *,
                        turn: int | None = None,
                        conversation: int = i,
                        portuguese: bool = pt,
                    ) -> dict:
                        started = time.perf_counter()
                        response = client.request(method, path, json=body)
                        timing = {
                            "conversation": conversation,
                            "language": "pt" if portuguese else "es",
                            "status": response.status_code,
                            "client_ms": round((time.perf_counter() - started) * 1000, 2),
                            "bff_ms": bff_ms(response.headers.get("Server-Timing", "")),
                        }
                        if turn is None:
                            startup.append(timing)
                        else:
                            timing["turn"] = turn
                            items.append(timing)
                        return check(response)

                    config = call("GET", "config")
                    if config["fixtures"]:
                        raise RuntimeError("Live serving required")
                    challenge = call(
                        "POST",
                        "auth/login",
                        {
                            "username": "demo.pt.br" if pt else "demo.es.mx",
                            "password": password,
                        },
                    )
                    code = call("GET", f"auth/challenges/{challenge['challenge_id']}/sms")["code"]
                    call(
                        "POST",
                        "auth/otp/verify",
                        {"challenge_id": challenge["challenge_id"], "code": code},
                    )
                    me = call("GET", "me")
                    persona = next(p for p in personas if p.username == me["username"])
                    rows = call("GET", "transactions")
                    row = next((x for x in rows if x.get("merchant")), None)
                    if not row:
                        raise RuntimeError("Owned named transaction required")
                    cid = call("POST", "chat/sessions", {})["conversation_id"]
                    private_write(
                        output / "progress.json",
                        json.dumps({"attempted": i + 1, "completed": completed}),
                    )
                    description = f"{row['amount']} {row['currency']} {row['merchant']} {row['transaction_date'][:10]}"
                    messages = (
                        [
                            "Pode explicar esta cobrança: " + description + "?",
                            "Pode resumir o status dessa cobrança?",
                        ]
                        if pt
                        else [
                            "¿Puedes explicar este cargo: " + description + "?",
                            "¿Puedes resumir el estado de ese cargo?",
                        ]
                    )
                    for turn, message in enumerate(messages):
                        result = call(
                            "POST", f"chat/sessions/{cid}/messages", {"message": message}, turn=turn
                        )
                        items[-1]["outcome"] = result["outcome"]
                        if result["outcome"] in {"dispute_filed", "card_frozen"}:
                            raise RuntimeError("Explanation probe must not perform bank actions")
                        private_write(
                            output / "progress.json",
                            json.dumps(
                                {"attempted": i + 1, "completed": completed, "turns": len(items)}
                            ),
                        )
                    access = client.cookies.get("aclara_access")
                    if not access:
                        raise RuntimeError("Authenticated session lost")
                    run, sid, _ = access.split(".", 2)
                    with store.transaction(Scope(persona.customer_id, run, sid)):
                        calls = [
                            e
                            for v in store.mapping("execution_records", dict).values()
                            if v.get("conversation_id") == cid
                            for e in v.get("events", [])
                            if e.get("event") == "llm_call"
                        ]
                    if not calls or not any(
                        c.get("status") == "valid" and c.get("provider") == "openai_compat"
                        for c in calls
                    ):
                        raise RuntimeError("Conversation did not reach a valid real model")
                    completed += 1
                    call("POST", "auth/logout", {})
                    budget = verify(owner, "latency", sha)
                    if budget["unknown_cost_attempts"]:
                        raise RuntimeError("Unknown model cost; stop without looping")
                    private_write(
                        output / "progress.json",
                        json.dumps(
                            {"attempted": i + 1, "completed": completed, "turns": len(items)}
                        ),
                    )
                    print(
                        json.dumps(
                            {
                                "completed": completed,
                                "planned": 10,
                                "charged_usd": budget["charged_with_reserves_usd"],
                            }
                        ),
                        flush=True,
                    )
        finally:
            store.close()
            result = {
                "implementation_sha": sha,
                "run_id": name,
                "complete": completed == 10,
                "conversations": completed,
                "turns": items,
                "startup": startup,
                "metrics": summarize(items, startup),
                "budget": verify(owner, "latency", sha),
            }
            private_write(output / "latency.json", json.dumps(result, indent=2) + "\n")
            private_write(
                output / "latency.md",
                "# In-region Azure BFF latency\n\n"
                + json.dumps(
                    {
                        "sha": sha,
                        "complete": result["complete"],
                        "metrics": result["metrics"],
                        "budget": result["budget"],
                    },
                    indent=2,
                )
                + "\n",
            )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit("Latency probe stopped: " + type(error).__name__) from None
