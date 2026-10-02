"""Aggregate-only round-two report from metadata-only local checkpoints."""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from random import Random
from statistics import median
from time import perf_counter
from typing import Any

from aclara.agent.nlu.rules import classify
from aclara.agent.nlu.structured import understand
from evals.studies.llm.comparison import _percentile, _slot_pairs
from evals.studies.llm.round_two import (
    ARTIFACTS,
    MODEL_IDS,
    SCORED_SLOTS,
    cumulative_cost,
    load_cases,
)

INTENTS = (
    "charge_inquiry",
    "dispute_charge",
    "duplicate_charge",
    "refund_or_reversal_status",
    "dispute_status",
    "fee_dispute",
    "card_lost_or_fraud",
    "human_request",
    "out_of_scope",
)


def wilson(successes: int, count: int) -> tuple[float, float]:
    if count == 0:
        return 0.0, 1.0
    z = 1.959963984540054
    proportion = successes / count
    denominator = 1 + z * z / count
    center = (proportion + z * z / (2 * count)) / denominator
    radius = (
        z
        * math.sqrt(proportion * (1 - proportion) / count + z * z / (4 * count * count))
        / denominator
    )
    lower = 0.0 if successes == 0 else max(0.0, center - radius)
    upper = 1.0 if successes == count else min(1.0, center + radius)
    return lower, upper


def slot_f1(rows: list[dict[str, Any]]) -> float:
    tp = sum(int(row["slot_tp"]) for row in rows)
    fp = sum(int(row["slot_fp"]) for row in rows)
    fn = sum(int(row["slot_fn"]) for row in rows)
    denominator = 2 * tp + fp + fn
    return 2 * tp / denominator if denominator else 1.0


def macro_f1(rows: list[dict[str, Any]]) -> float:
    labels = {row["gold_intent"] for row in rows}
    scores: list[float] = []
    for label in labels:
        tp = sum(row["gold_intent"] == label and row["predicted_intent"] == label for row in rows)
        fp = sum(row["gold_intent"] != label and row["predicted_intent"] == label for row in rows)
        fn = sum(row["gold_intent"] == label and row["predicted_intent"] != label for row in rows)
        scores.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def case_cost(row: dict[str, Any]) -> float:
    return sum(float(a["cost_usd"]) for a in row["attempts"])


def case_latency(row: dict[str, Any]) -> float:
    return sum(float(a["latency_ms"]) for a in row["attempts"]) / 1000


def interval(rows: list[dict[str, Any]], statistic: str, draws: int = 2000) -> tuple[float, float]:
    rng = Random(20260927)  # noqa: S311 - fixed seed for reproducible statistical resampling
    n = len(rows)
    values: list[float] = []
    for _ in range(draws):
        sample = [rows[rng.randrange(n)] for _ in range(n)]
        if statistic == "slot":
            value = slot_f1(sample)
        elif statistic == "macro":
            value = macro_f1(sample)
        elif statistic == "p50":
            value = median(case_latency(row) for row in sample)
        elif statistic == "p95":
            value = _percentile([case_latency(row) for row in sample], 0.95)
        elif statistic == "cost":
            value = sum(case_cost(row) for row in sample) / n
        else:
            raise ValueError(statistic)
        values.append(value)
    return _percentile(values, 0.025), _percentile(values, 0.975)


def pct(successes: int, count: int) -> str:
    lo, hi = wilson(successes, count)
    return f"{100 * successes / count:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]"


def measured(
    value: float, limits: tuple[float, float], *, percent: bool = False, precision: int = 2
) -> str:
    scale = 100 if percent else 1
    return f"{value * scale:.{precision}f} [{limits[0] * scale:.{precision}f}, {limits[1] * scale:.{precision}f}]"


def report() -> str:
    suite_cases, _, suite_hash = load_cases()
    path = ARTIFACTS / "full.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["suite_sha256"] != suite_hash:
        raise RuntimeError("Suite hash differs from round-two checkpoint")
    observations = data["observations"]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in observations:
        grouped[row["model_id"]].append(row)
    if any(len(grouped[model]) != (30 if model.endswith("opus-5") else 150) for model in MODEL_IDS):
        raise RuntimeError("Round-two model-case count is incomplete")
    lines = [
        "| Model (exact OpenRouter ID) | n | Intent accuracy, 95% CI | Macro-F1, 95% CI | Slot F1, 95% CI | Valid JSON / all attempts, 95% CI | Valid final, 95% CI | Language ID, 95% CI | ES / PT quality | p50 / p95 latency s, 95% CI | Cost / case USD, 95% CI |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    for model in MODEL_IDS:
        rows = grouped[model]
        n = len(rows)
        correct = sum(row["predicted_intent"] == row["gold_intent"] for row in rows)
        finals = sum(row["predicted_intent"] is not None for row in rows)
        language = sum(row["predicted_language"] == row["gold_language"] for row in rows)
        attempts = [a for row in rows for a in row["attempts"]]
        valid = sum(a["status"] == "valid" for a in attempts)
        latencies = [case_latency(row) for row in rows]
        cost = sum(case_cost(row) for row in rows) / n
        lines.append(
            f"| `{model}` | {n} | {pct(correct, n)} | "
            f"{measured(macro_f1(rows), interval(rows, 'macro'), percent=True, precision=1)} | "
            f"{measured(slot_f1(rows), interval(rows, 'slot'), percent=True, precision=1)} | "
            f"{valid}/{len(attempts)} ({pct(valid, len(attempts))}) | "
            f"{finals}/{n} ({pct(finals, n)}) | {pct(language, n)} | Pending / pending | "
            f"{measured(median(latencies), interval(rows, 'p50'))} / "
            f"{measured(_percentile(latencies, 0.95), interval(rows, 'p95'))} | "
            f"${measured(cost, interval(rows, 'cost'), precision=7)} |"
        )
    lines.append("")
    fallback_rows: list[dict[str, Any]] = []
    legacy_correct = 0
    for case in suite_cases:
        started = perf_counter()
        result = understand(case.message, country=case.country, bank_clock=case.bank_clock)
        latency_ms = (perf_counter() - started) * 1000
        legacy_correct += classify(case.message).intent.value == case.gold_intent
        predicted_slots = result.slots.model_dump()
        predicted_slots["date_expr"] = result.extracted.date_expr
        predicted = _slot_pairs(predicted_slots, SCORED_SLOTS)
        gold_pairs = _slot_pairs(case.gold_slots, SCORED_SLOTS)
        fallback_rows.append(
            {
                "gold_intent": case.gold_intent,
                "predicted_intent": result.extracted.intent,
                "gold_language": case.language,
                "predicted_language": result.extracted.language,
                "slot_tp": len(predicted & gold_pairs),
                "slot_fp": len(predicted - gold_pairs),
                "slot_fn": len(gold_pairs - predicted),
                "attempts": [{"latency_ms": latency_ms, "cost_usd": 0.0}],
            }
        )
    fallback_correct = sum(row["predicted_intent"] == row["gold_intent"] for row in fallback_rows)
    fallback_language = sum(
        row["predicted_language"] == row["gold_language"] for row in fallback_rows
    )
    lines.append(
        "Deterministic P fallback on the same 150 cases: intent "
        f"{pct(fallback_correct, 150)}, macro-F1 "
        f"{measured(macro_f1(fallback_rows), interval(fallback_rows, 'macro'), percent=True, precision=1)}, "
        f"slot F1 {measured(slot_f1(fallback_rows), interval(fallback_rows, 'slot'), percent=True, precision=1)}, "
        f"language ID {pct(fallback_language, 150)}. "
        f"The frozen B1 legacy intent rule scores {pct(legacy_correct, 150)}; "
        "it retains the old recognition routing for its end-to-end workflow."
    )
    lines.append("")
    lines.append(
        f"Round-two response spend: **${sum(case_cost(row) for row in observations):.6f}**; cumulative per-call spend including pilot and round one: **${cumulative_cost():.6f}**."
    )
    lines.append("")
    lines.append(
        "| Model | ES-MX correct / 30 | ES-CO correct / 30 | ES-AR correct / 30 | pt-BR correct / 30 | Mixed correct / 30 | Slang correct | False-friend correct | Injection intent correct | Out-of-scope precision / recall |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for model in MODEL_IDS:
        rows = grouped[model]
        slices: list[str] = []
        for prefix in ("mx.", "co.", "ar.", "br.", "mix."):
            subset = [row for row in rows if row["case_id"].startswith(prefix)]
            slices.append(
                f"{sum(row['predicted_intent'] == row['gold_intent'] for row in subset)}/{len(subset)}"
            )
        for tag in ("slang", "false_friend", "injection"):
            subset = [row for row in rows if tag in row["tags"]]
            slices.append(
                f"{sum(row['predicted_intent'] == row['gold_intent'] for row in subset)}/{len(subset)}"
            )
        tp = sum(
            row["gold_intent"] == "out_of_scope" and row["predicted_intent"] == "out_of_scope"
            for row in rows
        )
        fp = sum(
            row["gold_intent"] != "out_of_scope" and row["predicted_intent"] == "out_of_scope"
            for row in rows
        )
        fn = sum(
            row["gold_intent"] == "out_of_scope" and row["predicted_intent"] != "out_of_scope"
            for row in rows
        )
        abstention = f"{tp}/{tp + fp} / {tp}/{tp + fn}"
        lines.append(f"| `{model}` | {' | '.join(slices)} | {abstention} |")
    lines.append("")
    lines.append("Intent macro-F1 by dialect/language, with 95% case-bootstrap intervals:")
    lines.append("")
    lines.append("| Model | ES-MX | ES-CO | ES-AR | pt-BR | Mixed |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for model in MODEL_IDS:
        cells: list[str] = []
        for prefix in ("mx.", "co.", "ar.", "br.", "mix."):
            subset = [row for row in grouped[model] if row["case_id"].startswith(prefix)]
            cells.append(
                measured(
                    macro_f1(subset),
                    interval(subset, "macro", draws=1000),
                    percent=True,
                    precision=1,
                )
            )
        lines.append(f"| `{model}` | {' | '.join(cells)} |")
    lines.append("")
    lines.append(
        "Injection-suspected flag on the ten injection utterances (recall), followed by false flags on the other cases:"
    )
    lines.append("")
    lines.append("| Model | Flagged injection cases | False flags on non-injection cases |")
    lines.append("|---|---:|---:|")
    for model in MODEL_IDS:
        rows = grouped[model]
        injected = [row for row in rows if "injection" in row["tags"]]
        ordinary = [row for row in rows if "injection" not in row["tags"]]
        flagged = sum(row["injection_suspected"] is True for row in injected)
        false_flags = sum(row["injection_suspected"] is True for row in ordinary)
        lines.append(f"| `{model}` | {flagged}/{len(injected)} | {false_flags}/{len(ordinary)} |")
    lines.append("")
    full_rows = [row for model in MODEL_IDS[:-1] for row in grouped[model]]
    columns = (*INTENTS, "no_final")
    matrix = Counter(
        (row["gold_intent"], row["predicted_intent"] or "no_final") for row in full_rows
    )
    lines.append(
        "Pooled confusion matrix, six full-suite models (900 model-case outcomes; Opus sample excluded):"
    )
    lines.append("")
    lines.append("| Gold / predicted | " + " | ".join(columns) + " |")
    lines.append("|---|" + "---:|" * len(columns))
    for gold in INTENTS:
        lines.append(
            "| " + gold + " | " + " | ".join(str(matrix[gold, pred]) for pred in columns) + " |"
        )
    lines.append("")
    errors = [row for row in full_rows if row["predicted_intent"] not in {row["gold_intent"], None}]
    confusions = Counter((row["gold_intent"], row["predicted_intent"]) for row in errors)
    lines.append(
        "Most common completed intent confusions: "
        + "; ".join(
            f"{gold} → {pred}: {count}" for (gold, pred), count in confusions.most_common(8)
        )
        + "."
    )
    lines.append("")
    failed = Counter(
        (row["model_id"], a["status"], a["stop_reason"])
        for row in observations
        for a in row["attempts"]
        if a["status"] != "valid"
    )
    lines.append(
        "Non-valid attempts in the scored 930-case checkpoint: "
        + (
            "; ".join(
                f"{model} {status}/{reason}: {count}"
                for (model, status, reason), count in failed.items()
            )
            if failed
            else "none"
        )
        + "."
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(report())
