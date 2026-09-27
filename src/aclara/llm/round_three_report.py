"""Aggregate-only round-three report on the frozen 150-case dev suite."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from random import Random
from statistics import median
from typing import Any

from aclara.llm.comparison import _percentile
from aclara.llm.round_three import (
    ARTIFACTS,
    MODEL_IDS,
    cumulative_cost,
    load_cases,
    unknown_attempts,
)
from aclara.llm.round_two import ARTIFACTS as ROUND_TWO_ARTIFACTS
from aclara.llm.round_two_report import (
    case_latency,
    interval,
    macro_f1,
    measured,
    pct,
    slot_f1,
    wilson,
)

BASELINE = "google/gemini-3-flash-preview"
CATALOG_RATES = {
    BASELINE: (0.25, 1.50),
    "openai/gpt-5-nano": (0.025, 0.20),
    "openai/gpt-5-mini": (0.125, 1.00),
    "x-ai/grok-4.20": (1.25, 2.50),
    "qwen/qwen3-next-80b-a3b-instruct": (0.10, 1.10),
    "deepseek/deepseek-v4-flash-0731": (0.0215, 0.30),
    "mistralai/mistral-small-2603": (0.15, 0.60),
}


def _known_cost(row: dict[str, Any]) -> float:
    return sum(float(a["cost_usd"]) for a in row["attempts"] if a["cost_usd"] is not None)


def _cost_interval(rows: list[dict[str, Any]]) -> tuple[float, float]:
    cleaned = [
        {**row, "attempts": [{**a, "cost_usd": a["cost_usd"] or 0.0} for a in row["attempts"]]}
        for row in rows
    ]
    return interval(cleaned, "cost")


def _paired_slot_delta(
    rows: list[dict[str, Any]], baseline: list[dict[str, Any]], draws: int = 2000
) -> tuple[float, tuple[float, float]]:
    baseline_by_id = {row["case_id"]: row for row in baseline}
    pairs = [(row, baseline_by_id[row["case_id"]]) for row in rows]
    observed = slot_f1(rows) - slot_f1(baseline)
    rng = Random(20260927)  # noqa: S311 - fixed statistical resampling seed
    samples = []
    for _ in range(draws):
        sampled = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        samples.append(
            slot_f1([pair[0] for pair in sampled]) - slot_f1([pair[1] for pair in sampled])
        )
    return observed, (_percentile(samples, 0.025), _percentile(samples, 0.975))


def report() -> str:
    _, _, suite_hash = load_cases()
    round_three = json.loads((ARTIFACTS / "full.json").read_text(encoding="utf-8"))
    round_two = json.loads((ROUND_TWO_ARTIFACTS / "full.json").read_text(encoding="utf-8"))
    if round_three["suite_sha256"] != suite_hash or round_two["suite_sha256"] != suite_hash:
        raise RuntimeError("The frozen suite hash changed")
    if round_three["prompt_hash"] != round_two["prompt_hash"]:
        raise RuntimeError("The round-three prompt differs from the baseline")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in round_three["observations"] + round_two["observations"]:
        if row["model_id"] in (*MODEL_IDS, BASELINE):
            grouped[row["model_id"]].append(row)
    if any(len(grouped[model]) != 150 for model in (*MODEL_IDS, BASELINE)):
        raise RuntimeError("The 150-case full comparison is incomplete")
    if any(len({row["case_id"] for row in grouped[model]}) != 150 for model in grouped):
        raise RuntimeError("Duplicate case observations")
    baseline = grouped[BASELINE]
    lines = [
        "| Exact OpenRouter model ID | Catalog input / output USD per 1M | n | Intent, 95% CI | Macro-F1, 95% CI | Slot F1, 95% CI | Valid JSON / all attempts, 95% CI | Valid final, 95% CI | Language ID, 95% CI | Injection flags / 10; false flags / 140 | ES / PT quality | p50 / p95 latency s, 95% CI | Known cost / case USD, 95% CI |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    for model in (BASELINE, *MODEL_IDS):
        rows = grouped[model]
        n = len(rows)
        attempts = [a for row in rows for a in row["attempts"]]
        valid = sum(a["status"] == "valid" for a in attempts)
        finals = sum(row["predicted_intent"] is not None for row in rows)
        correct = sum(row["predicted_intent"] == row["gold_intent"] for row in rows)
        language = sum(row["predicted_language"] == row["gold_language"] for row in rows)
        injected = [row for row in rows if "injection" in row["tags"]]
        ordinary = [row for row in rows if "injection" not in row["tags"]]
        flags = sum(row["injection_suspected"] is True for row in injected)
        false_flags = sum(row["injection_suspected"] is True for row in ordinary)
        latencies = [case_latency(row) for row in rows]
        rate = CATALOG_RATES[model]
        lines.append(
            f"| `{model}` | ${rate[0]:g} / ${rate[1]:g} | {n} | {pct(correct, n)} | "
            f"{measured(macro_f1(rows), interval(rows, 'macro'), percent=True, precision=1)} | "
            f"{measured(slot_f1(rows), interval(rows, 'slot'), percent=True, precision=1)} | "
            f"{valid}/{len(attempts)} ({pct(valid, len(attempts))}) | "
            f"{finals}/{n} ({pct(finals, n)}) | {pct(language, n)} | "
            f"{flags}/10 [{100 * wilson(flags, 10)[0]:.1f}, {100 * wilson(flags, 10)[1]:.1f}]%; "
            f"{false_flags}/140 | Pending / pending | "
            f"{measured(median(latencies), interval(rows, 'p50'))} / "
            f"{measured(_percentile(latencies, 0.95), interval(rows, 'p95'))} | "
            f"${measured(sum(_known_cost(row) for row in rows) / n, _cost_interval(rows), precision=7)} |"
        )
    lines += [
        "",
        "Paired slot-F1 differences versus the selected Gemini 3 Flash baseline on the same 150 cases "
        "(2,000 case-pair bootstrap resamples; percentage points):",
        "",
        "| Challenger | Difference, 95% CI | Injection flags and false flags match baseline? |",
        "|---|---:|---:|",
    ]
    for model in MODEL_IDS:
        delta, bounds = _paired_slot_delta(grouped[model], baseline)
        rows = grouped[model]
        flags = sum(
            row["injection_suspected"] is True for row in rows if "injection" in row["tags"]
        )
        false_flags = sum(
            row["injection_suspected"] is True for row in rows if "injection" not in row["tags"]
        )
        lines.append(
            f"| `{model}` | {100 * delta:+.1f} [{100 * bounds[0]:+.1f}, {100 * bounds[1]:+.1f}] | "
            f"{'Yes' if (flags, false_flags) == (10, 0) else 'No'} |"
        )
    lines += ["", "Dialect and challenge-slice intent accuracy:", ""]
    lines.append(
        "| Model | ES-MX / 30 | ES-CO / 30 | ES-AR / 30 | pt-BR / 30 | Mixed / 30 | Slang | False friends | Injection intent | Out-of-scope precision / recall |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for model in (BASELINE, *MODEL_IDS):
        rows = grouped[model]
        cells = []
        for prefix in ("mx.", "co.", "ar.", "br.", "mix."):
            subset = [row for row in rows if row["case_id"].startswith(prefix)]
            cells.append(
                f"{sum(row['predicted_intent'] == row['gold_intent'] for row in subset)}/{len(subset)}"
            )
        for tag in ("slang", "false_friend", "injection"):
            subset = [row for row in rows if tag in row["tags"]]
            cells.append(
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
        lines.append(f"| `{model}` | {' | '.join(cells)} | {tp}/{tp + fp} / {tp}/{tp + fn} |")
    lines += ["", "Cross-model intent confusions (challengers only):", ""]
    columns = (
        "charge_inquiry",
        "dispute_charge",
        "duplicate_charge",
        "refund_or_reversal_status",
        "dispute_status",
        "fee_dispute",
        "card_lost_or_fraud",
        "human_request",
        "out_of_scope",
        "no_final",
    )
    matrix = Counter(
        (row["gold_intent"], row["predicted_intent"] or "no_final")
        for model in MODEL_IDS
        for row in grouped[model]
    )
    lines.append("| Gold / predicted | " + " | ".join(columns) + " |")
    lines.append("|---|" + "---:|" * len(columns))
    for gold in columns[:-1]:
        lines.append(
            "| " + gold + " | " + " | ".join(str(matrix[gold, pred]) for pred in columns) + " |"
        )
    failed = Counter(
        (row["model_id"], a["status"], a["stop_reason"])
        for row in round_three["observations"]
        for a in row["attempts"]
        if a["status"] != "valid"
    )
    lines += [
        "",
        "Non-valid scored attempts: "
        + (
            "; ".join(
                f"{model} {status}/{reason}: {count}"
                for (model, status, reason), count in failed.items()
            )
            if failed
            else "none"
        )
        + ".",
        f"Known round-three pilot, provider-probe, and scored-response spend: **${cumulative_cost() - 3.520801127:.6f}**; cumulative known per-call spend: **${cumulative_cost():.6f}**. "
        f"There are {unknown_attempts()} no-response attempts without per-call cost, including six initial preflight errors. "
        "They are excluded from cost per case; a separate $0.02/attempt guard plus a $0.30 reserve protects the cumulative $10 cap.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(report())
