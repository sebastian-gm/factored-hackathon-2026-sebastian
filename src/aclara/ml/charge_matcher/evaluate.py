"""Identical query metrics, decision costs and customer-clustered intervals."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

import numpy as np

from aclara.ml.charge_matcher.model import Array, choice_first_decisions, decisions
from aclara.ml.charge_matcher.types import Query

COSTS = {
    "wrong_proposal": 10.0,
    "extra_turn": 1.0,
    "false_none": 3.0,
    "choice_missing_target": 4.0,
    "correct": 0.0,
}

# Relative interaction costs, chosen before v2 fitting; not measured currency.
V2_COSTS = {**COSTS, "false_none": 6.0}


def summarize_queries(
    queries: list[Query],
    scores: Array,
    groups: list[tuple[int, int]],
    top: Array,
    exists: Array,
    thresholds: dict[str, float],
    *,
    decision_policy: str = "legacy_v1",
    costs: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    costs = COSTS if costs is None else costs
    if decision_policy == "choice_first_v2":
        maximum = np.asarray(
            [float(np.max(scores[start:end])) if end > start else 0 for start, end in groups]
        )
        actions = choice_first_decisions(top, exists, maximum, thresholds)
    elif decision_policy == "legacy_v1":
        actions = decisions(top, exists, thresholds)
    else:
        raise ValueError("unknown matcher decision policy")
    result = []
    for query, (start, end), p_top, p_exists, action in zip(
        queries, groups, top, exists, actions, strict=True
    ):
        order = np.argsort(-scores[start:end], kind="stable")
        ids = [query.candidates[int(index)].transaction_id for index in order]
        rank = ids.index(query.target_id) + 1 if query.target_id in ids else 0
        if not ids:
            action = "none"
            p_top = p_exists = 0.0
        correct = rank == 1
        none = query.target_id is None
        cost = (
            0.0
            if action == "propose" and correct
            else costs["wrong_proposal"]
            if action == "propose"
            else (0.0 if none else costs["false_none"])
            if action == "none"
            else costs["extra_turn"]
            if none or 0 < rank <= 3
            else costs["choice_missing_target"]
        )
        result.append(
            {
                "query_id": query.query_id,
                "customer_id": query.customer_id,
                "n": len(ids),
                "rank": rank,
                "correct": correct,
                "true_none": none,
                "action": action,
                "top_probability": float(p_top),
                "exists_probability": float(p_exists),
                "cost": cost,
                "noise_family": query.noise_family,
                "country": query.customer_country,
                "segment": query.segment,
            }
        )
    return result


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    matched = [row for row in rows if not row["true_none"]]
    predicted_none = [row for row in rows if row["action"] == "none"]
    true_none = sum(row["true_none"] for row in rows)
    proposed = [row for row in rows if row["action"] == "propose"]
    ece = 0.0
    for low in np.arange(0, 1, 0.1):
        bucket = [
            row
            for row in rows
            if low <= row["top_probability"] < low + 0.1
            or low > 0.89
            and row["top_probability"] == 1
        ]
        if bucket:
            ece += (
                len(bucket)
                / max(1, n)
                * abs(
                    float(np.mean([row["top_probability"] for row in bucket]))
                    - float(np.mean([row["correct"] for row in bucket]))
                )
            )
    return {
        "n": n,
        "match_queries": len(matched),
        "no_match_queries": true_none,
        "top1_accuracy": sum(row["correct"] for row in matched) / len(matched) if matched else None,
        "mrr": sum(1 / row["rank"] if row["rank"] else 0 for row in matched) / len(matched)
        if matched
        else None,
        "recall_at_3": sum(0 < row["rank"] <= 3 for row in matched) / len(matched)
        if matched
        else None,
        "no_match_precision": sum(row["true_none"] for row in predicted_none) / len(predicted_none)
        if predicted_none
        else None,
        "no_match_recall": sum(row["true_none"] for row in predicted_none) / true_none
        if true_none
        else None,
        "ece": ece,
        "mean_cost": float(np.mean([row["cost"] for row in rows])) if rows else None,
        "proposal_coverage": len(proposed) / n if n else 0,
        "wrong_proposals": sum(not row["correct"] for row in proposed),
        "proposal_count": len(proposed),
        "proposal_risk": sum(not row["correct"] for row in proposed) / len(proposed)
        if proposed
        else None,
        "actions": dict(Counter(row["action"] for row in rows)),
        "insufficient_sample": n < 30,
    }


def choose_thresholds(
    queries: list[Query], scores: Array, groups: list[tuple[int, int]], top: Array, exists: Array
) -> tuple[dict[str, float], float]:
    best = (float("inf"), float("inf"))
    chosen: dict[str, float] = {}
    for auto in (0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 1.01):
        for choice in (0.0, 0.15, 0.3, 0.45):
            for none in (0.0, 0.15, 0.3, 0.45, 0.6):
                thresholds = {"auto": auto, "choice": choice, "none": none}
                rows = summarize_queries(queries, scores, groups, top, exists, thresholds)
                key = (
                    sum(row["cost"] for row in rows) / len(rows),
                    sum(row["action"] == "propose" and not row["correct"] for row in rows),
                )
                if key < best:
                    best = key
                    chosen = thresholds
    return chosen, best[0]


def clustered_intervals(
    rows: list[dict[str, Any]], seed: int = 20260926, repeats: int = 300
) -> dict[str, list[float]]:
    customers: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        customers.setdefault(row["customer_id"], []).append(row)
    groups = list(customers.values())
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {
        key: []
        for key in (
            "top1_accuracy",
            "mean_cost",
            "proposal_coverage",
            "no_match_precision",
            "no_match_recall",
        )
    }
    for _ in range(repeats):
        sample = [
            row for index in rng.integers(0, len(groups), len(groups)) for row in groups[int(index)]
        ]
        result = metrics(sample)
        for key in values:
            if result[key] is not None:
                values[key].append(result[key])
    return {
        key: np.quantile(samples, [0.025, 0.975]).tolist()
        for key, samples in values.items()
        if samples
    }


def report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bins: dict[str, Callable[[int], bool]] = {
        "0": lambda n: n == 0,
        "1": lambda n: n == 1,
        "2-3": lambda n: 2 <= n <= 3,
        "4-8": lambda n: 4 <= n <= 8,
        "9+": lambda n: n >= 9,
    }
    slices = {
        key: metrics([row for row in rows if predicate(row["n"])])
        for key, predicate in bins.items()
    }
    risk = []
    for threshold in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 1.0):
        accepted = [row for row in rows if row["top_probability"] >= threshold]
        risk.append(
            {
                "threshold": threshold,
                "coverage": len(accepted) / len(rows),
                "risk": sum(not row["correct"] for row in accepted) / len(accepted)
                if accepted
                else None,
                "n": len(accepted),
            }
        )
    failures = [
        row for row in rows if row["cost"] >= 3 or not row["correct"] and not row["true_none"]
    ][:20]
    categories = Counter(
        "no_match_proposed"
        if row["true_none"] and row["action"] == "propose"
        else "false_none"
        if row["action"] == "none"
        else "underspecified"
        if row["noise_family"] in {"type_only", "country_only", "partial"}
        else "noisy_recollection"
        for row in failures
    )
    return {
        "overall": metrics(rows),
        "by_candidate_set_size": slices,
        "by_noise_family": {
            family: metrics([row for row in rows if row["noise_family"] == family])
            for family in sorted({row["noise_family"] for row in rows})
        },
        "by_country": {
            country: metrics([row for row in rows if row["country"] == country])
            for country in sorted({row["country"] for row in rows})
        },
        "by_segment": {
            segment: metrics([row for row in rows if row["segment"] == segment])
            for segment in sorted({row["segment"] for row in rows})
        },
        "risk_coverage": risk,
        "bootstrap_95": clustered_intervals(rows),
        "failure_audit": {
            "n": len(failures),
            "categories": dict(categories),
            "method": "deterministic review of first 20 errors; no human review claimed",
        },
    }
