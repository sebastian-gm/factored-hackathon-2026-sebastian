"""Offline attempt/request latency accounting; hedges are counterfactual only."""

from __future__ import annotations

from collections import Counter, defaultdict
from importlib import import_module
from typing import Any


def requests(calls: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group serial attempts, retaining retries and fallback; ignore parallel Jev."""
    result: list[list[dict[str, Any]]] = []
    for call in calls:
        if call["provider"] == "typesafe" or call["status"] == "skipped":
            continue
        if (
            not result
            or call["id"] != result[-1][0]["id"]
            or call.get("candidate") != result[-1][0].get("candidate")
            or call["prompt_id"] != result[-1][0]["prompt_id"]
            or (call["attempt"] == 1 and call["route"] in {"nlu", "phrase"})
        ):
            result.append([])
        result[-1].append(call)
    return result


def retry_analysis(calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Replay only observed retries earlier; never invent secondary successes/cost."""
    metrics = import_module("evals.metrics")

    groups = requests(calls)
    serial = defaultdict(list)
    for group in groups:
        serial[group[0]["id"]].append(sum(c["latency_ms"] for c in group))
    hedges = {}
    for seconds in (3, 4):
        threshold = seconds * 1000
        replay = defaultdict(list)
        triggers = rescued = already_retried = unknown = 0
        duplicate_cost_proxy = 0.0
        for group in groups:
            first = group[0]
            total = sum(c["latency_ms"] for c in group)
            if first["latency_ms"] > threshold:
                triggers += 1
                unknown += first["cost_usd"] is None
                if first["status"] == "valid":
                    duplicate_cost_proxy += first["cost_usd"] or 0
                if len(group) > 1 and first["status"] != "valid":
                    already_retried += 1
                    # Optimistic timing-only replay: same observed second and
                    # fallback latencies, first unsuccessful and censored.
                    total -= first["latency_ms"] - threshold
                    rescued += any(c["status"] == "valid" for c in group[1:])
            replay[first["id"]].append(total)
        hedges[str(seconds)] = {
            "triggered_first_attempts": triggers,
            "already_retried": already_retried,
            "new_duplicate_requests": triggers - already_retried,
            "observed_successful_retries_shifted": rescued,
            "unknown_cost_first_attempts": unknown,
            "optimistic_request_latency": metrics.latency(list(replay.values())),
            "measured_hedge_cost_usd": None,
            "duplicate_cost_if_same_usage_as_slow_success_usd": duplicate_cost_proxy,
        }
    totals = [sum(c["latency_ms"] for c in group) for group in groups]
    attempted = [c for group in groups for c in group]
    # Preserve censored timeout durations in all latency distributions. A
    # generic provider error is not evidence that either timeout was reached.
    timeout_codes = {"timeout", "http_408", "http_504", "provider_408", "provider_504"}
    timeouts = [c for c in attempted if c.get("stop_reason") in timeout_codes]
    return {
        "serial_requests": len(groups),
        "requests_with_retry_or_fallback": sum(len(g) > 1 for g in groups),
        "first_attempt_status": dict(Counter(g[0]["status"] for g in groups)),
        "serial_request_latency": metrics.latency(list(serial.values())),
        "serial_request_p99_ms": metrics.percentile(totals, 0.99),
        "serial_request_max_ms": max(totals) if totals else None,
        "retry_first_latency_ms": [g[0]["latency_ms"] for g in groups if len(g) > 1],
        "latency_failures": {
            "timeout_attempts": len(timeouts),
            "timeout_cases": len({c["id"] for c in timeouts}),
            "timeout_latency_ms": [c["latency_ms"] for c in timeouts],
            "provider_error_codes": dict(
                Counter(
                    c.get("stop_reason") or "unknown"
                    for c in attempted
                    if c["status"] == "provider_error"
                )
            ),
            "first_attempts_over_serving_6s": sum(g[0]["latency_ms"] > 6000 for g in groups),
        },
        "hedge_counterfactual": hedges,
        "counterfactual_assumptions": (
            "Only shift observed unsuccessful slow-first retries; keep successful firsts and "
            "fast failures unchanged. Secondary latency/outcome is assumed unchanged by "
            "overlap. Not a measured hedge, turn/case p95, independent-tail claim or cost. "
            "Timeout is right-censoring, not proof the provider stopped billing."
        ),
    }
