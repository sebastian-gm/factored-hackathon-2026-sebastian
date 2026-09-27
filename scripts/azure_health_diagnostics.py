"""Read-only ACA startup evidence and bounded health probes; no console contents."""

# ruff: noqa: T201 -- aggregate diagnostic output only.
from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from time import perf_counter

from scripts.azure_dev import ROOT, SUBSCRIPTION, az, private_write, run

APP = "ca-api-aclara-dev-eastus2"
GROUP = "rg-aclara-dev-eastus2"


def main() -> None:
    before = az("containerapp", "show", "--name", APP, "--resource-group", GROUP)
    revision = before["properties"]["latestReadyRevisionName"]
    replicas = az(
        "containerapp",
        "replica",
        "list",
        "--name",
        APP,
        "--resource-group",
        GROUP,
        "--revision",
        revision,
    )
    domain = before["properties"]["configuration"]["ingress"]["fqdn"]
    probes = []
    for path in ("/healthz", "/healthz", "/readyz"):
        start = perf_counter()
        status, error = None, None
        try:
            with urllib.request.urlopen("https://" + domain + path, timeout=20) as response:  # noqa: S310 -- trusted scoped ACA control plane FQDN.
                status = response.status
                response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            error = type(exc).__name__
        probes.append(
            {
                "path": path,
                "status": status,
                "error": error,
                "seconds": round(perf_counter() - start, 3),
            }
        )
    raw = run(
        [
            "az",
            "containerapp",
            "logs",
            "show",
            "--name",
            APP,
            "--resource-group",
            GROUP,
            "--type",
            "system",
            "--tail",
            "100",
            "--format",
            "json",
            "--follow",
            "false",
            "--subscription",
            SUBSCRIPTION,
            "--only-show-errors",
        ]
    )
    events = []
    reasons: Counter[str] = Counter()
    for line in raw.splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        reasons[str(value.get("Reason", "unknown"))] += 1
        message = str(value.get("Msg", value.get("Log", value.get("Log_s", "")))).lower()
        if value.get("Reason") == "ProbeFailed":
            events.append({"category": "probe_failure", "at": value.get("TimeStamp")})
            continue
        categories = {
            "image_pull": ("pulling image", "pulled image"),
            "container_start": ("started container", "created container"),
            "probe_failure": ("probe failed", "probe failure", "unhealthy"),
            "scale": ("scal", "replica"),
            "ready": ("running", "ready"),
        }
        for category, phrases in categories.items():
            if any(phrase in message for phrase in phrases):
                events.append(
                    {"category": category, "at": value.get("TimeStamp", value.get("TimeGenerated"))}
                )
                break
    after = az(
        "containerapp",
        "replica",
        "list",
        "--name",
        APP,
        "--resource-group",
        GROUP,
        "--revision",
        revision,
    )
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "subscription_name": SUBSCRIPTION,
        "min_replicas": before["properties"]["template"]["scale"].get("minReplicas") or 0,
        "replicas_before": len(replicas),
        "replicas_after": len(after),
        "probes": probes,
        "system_event_reasons": dict(reasons),
        "system_event_categories": dict(Counter(e["category"] for e in events)),
        "system_event_timeline": events,
        "historical_first_timeout_cause": "not established from current evidence",
        "read_only": True,
    }
    private_write(
        ROOT / "artifacts/azure/health-diagnostics.json", json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    main()
