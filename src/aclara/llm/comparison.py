"""Same-case model comparison; output is aggregate-only and never selects a winner."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from statistics import mean

from aclara.agent.nlg.grounding import redact_for_model
from aclara.agent.nlu.structured import ExtractedNlu, postprocess
from aclara.llm.client import StructuredClient
from aclara.llm.prompts import Prompt, data_block
from aclara.llm.types import ModelFailure


@dataclass(frozen=True, slots=True)
class ComparisonCase:
    message: str
    country: str
    bank_clock: datetime
    gold_intent: str
    gold_slots: dict[str, str]
    language: str
    scored_slot_keys: tuple[str, ...] | None = None
    case_id: str = ""


@dataclass(frozen=True, slots=True)
class ComparisonRow:
    model: str
    cases: int
    intent_accuracy: float
    slot_f1: float
    valid_json_rate: float | None
    es_quality: float | None
    pt_quality: float | None
    p50_latency_ms: float
    p95_latency_ms: float
    cost_per_case_usd: float | None


def _percentile(values: list[float], proportion: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * proportion
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)


def _slot_pairs(
    values: Mapping[str, object], scored_keys: tuple[str, ...] | None = None
) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for key, value in values.items():
        if value is None or (scored_keys is not None and key not in scored_keys):
            continue
        normalized = str(value).strip().casefold()
        if key == "amount_value":
            with suppress(InvalidOperation):
                normalized = str(Decimal(normalized).normalize())
        result.add((key, normalized))
    return result


def evaluate_model(
    route: str,
    cases: list[ComparisonCase],
    client: StructuredClient,
    prompt: Prompt,
    *,
    quality_scores: dict[str, list[float]] | None = None,
    after_case: Callable[[], None] | None = None,
) -> ComparisonRow:
    if not cases:
        raise ValueError("Comparison requires cases")
    correct_intent = 0
    tp = fp = fn = 0
    case_latencies: list[float] = []
    start_record = len(client.records)
    for case in cases:
        prior = len(client.records)
        try:
            extracted = client.generate(
                route,
                prompt.text,
                data_block("customer_message", redact_for_model(case.message)),
                ExtractedNlu,
                prompt_id=f"{prompt.id}@{prompt.version}",
                prompt_hash=prompt.content_hash,
            )
            result = postprocess(extracted, country=case.country, bank_clock=case.bank_clock)
            correct_intent += result.extracted.intent == case.gold_intent
            predicted = _slot_pairs(result.slots.model_dump(), case.scored_slot_keys)
            gold = _slot_pairs(case.gold_slots, case.scored_slot_keys)
            tp += len(predicted & gold)
            fp += len(predicted - gold)
            fn += len(gold - predicted)
        except ModelFailure:
            fn += len(_slot_pairs(case.gold_slots, case.scored_slot_keys))
        case_latencies.append(sum(record.latency_ms for record in client.records[prior:]))
        if after_case is not None:
            after_case()
    records = client.records[start_record:]
    valid_rate = (
        sum(record.status == "valid" for record in records) / len(records) if records else None
    )
    costs = [record.cost_usd for record in records]
    quality_scores = quality_scores or {}
    return ComparisonRow(
        model=client.models[route].model_id,
        cases=len(cases),
        intent_accuracy=correct_intent / len(cases),
        slot_f1=2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0,
        valid_json_rate=valid_rate,
        es_quality=mean(quality_scores["es"]) if quality_scores.get("es") else None,
        pt_quality=mean(quality_scores["pt"]) if quality_scores.get("pt") else None,
        p50_latency_ms=_percentile(case_latencies, 0.50),
        p95_latency_ms=_percentile(case_latencies, 0.95),
        cost_per_case_usd=(
            sum(cost for cost in costs if cost is not None) / len(cases)
            if all(cost is not None for cost in costs)
            else None
        ),
    )


def markdown_table(rows: list[ComparisonRow]) -> str:
    lines = [
        "| Model | n | Intent accuracy | Slot F1 | Valid JSON | ES quality | PT quality | p50 ms | p95 ms | USD/case |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def pct(value: float | None) -> str:
        return "pending" if value is None else f"{value:.1%}"

    def score(value: float | None) -> str:
        return "pending" if value is None else f"{value:.2f}/5"

    for row in rows:
        cost = "pending" if row.cost_per_case_usd is None else f"${row.cost_per_case_usd:.5f}"
        lines.append(
            f"| {row.model} | {row.cases} | {pct(row.intent_accuracy)} | {pct(row.slot_f1)} | "
            f"{pct(row.valid_json_rate)} | {score(row.es_quality)} | {score(row.pt_quality)} | "
            f"{row.p50_latency_ms:.0f} | {row.p95_latency_ms:.0f} | {cost} |"
        )
    return "\n".join(lines)
