"""Label-free pointwise features, with per-candidate business-date FX."""

from __future__ import annotations

import math
import unicodedata
from bisect import bisect_right
from datetime import date

from rapidfuzz.fuzz import WRatio, token_set_ratio

from aclara.ml.charge_matcher.types import Candidate, Slots

FEATURES = (
    "amount_relative_error",
    "amount_log_error",
    "amount_missing",
    "fx_missing",
    "date_distance_days",
    "date_in_range",
    "date_missing",
    "merchant_wratio",
    "merchant_token_set",
    "merchant_missing",
    "type_match",
    "type_missing",
    "category_match",
    "category_missing",
    "channel_match",
    "channel_missing",
    "country_match",
    "country_missing",
    "status_approved",
    "status_pending",
    "status_declined",
    "status_reversed",
    "recency_rank",
    "candidate_set_size",
    "amount_rank",
    "slot_coverage",
)
ALIASES = {"el super": "supermercado", "el supermercado": "supermercado", "taxi app": "uber"}


def normalize(value: str | None) -> str:
    plain = (
        "".join(
            char
            for char in unicodedata.normalize("NFKD", value or "")
            if not unicodedata.combining(char)
        )
        .lower()
        .strip()
    )
    return ALIASES.get(plain, plain)


class FxBook:
    def __init__(self, rows: list[tuple[date, str, str, float]]) -> None:
        self.rates: dict[tuple[str, str], list[tuple[date, float]]] = {}
        for day, source, target, rate in rows:
            self.rates.setdefault((source, target), []).append((day, rate))
        for values in self.rates.values():
            values.sort()

    def convert(self, amount: float, source: str | None, target: str, day: date) -> float | None:
        if source == target:
            return amount
        values = self.rates.get((source or "", target), [])
        index = bisect_right(values, (day, float("inf"))) - 1
        if index < 0:
            return None
        return amount * values[index][1]


def candidate_features(
    slots: Slots, candidates: tuple[Candidate, ...], fx: FxBook
) -> list[list[float]]:
    output = []
    amounts = sorted(row.amount for row in candidates)
    recency = {
        row.transaction_id: rank
        for rank, row in enumerate(
            sorted(candidates, key=lambda r: (r.transaction_date, r.transaction_id), reverse=True)
        )
    }
    for row in candidates:
        converted = (
            fx.convert(slots.amount, slots.currency, row.currency, row.process_date)
            if slots.amount is not None
            else None
        )
        relative = (
            min(abs(converted - row.amount) / max(abs(row.amount), 0.01), 10)
            if converted is not None
            else 0.0
        )
        log_error = (
            min(abs(math.log(max(converted, 0.01) / max(row.amount, 0.01))), 10)
            if converted is not None
            else 0.0
        )
        distance = (
            max(
                (slots.date_start - row.process_date).days,
                (row.process_date - (slots.date_end or slots.date_start)).days,
                0,
            )
            if slots.date_start
            else 0
        )
        merchant_available = bool(
            slots.merchant and row.merchant and row.transaction_type == "Purchase"
        )
        coverage = (
            sum(
                value is not None
                for value in (
                    slots.amount,
                    slots.date_start,
                    slots.merchant,
                    slots.transaction_type,
                    slots.category,
                    slots.channel,
                    slots.country,
                )
            )
            / 7
        )
        output.append(
            [
                relative,
                log_error,
                float(slots.amount is None),
                float(slots.amount is not None and converted is None),
                float(min(distance, 120)),
                float(distance == 0 and slots.date_start is not None),
                float(slots.date_start is None),
                WRatio(normalize(slots.merchant), normalize(row.merchant)) / 100
                if merchant_available
                else 0.0,
                token_set_ratio(normalize(slots.merchant), normalize(row.merchant)) / 100
                if merchant_available
                else 0.0,
                float(not merchant_available),
                float(slots.transaction_type == row.transaction_type),
                float(slots.transaction_type is None),
                float(slots.category == row.category and slots.category is not None),
                float(slots.category is None),
                float(slots.channel == row.channel),
                float(slots.channel is None),
                float(slots.country == row.country),
                float(slots.country is None),
                float(row.status == "Approved"),
                float(row.status == "Pending"),
                float(row.status == "Declined"),
                float(row.status == "Reversed"),
                recency[row.transaction_id] / max(1, len(candidates) - 1),
                float(len(candidates)),
                (bisect_right(amounts, row.amount) - 1) / max(1, len(candidates) - 1),
                coverage,
            ]
        )
    return output


def rules_score(features: list[float]) -> float:
    """Fixed engineer-written scorer; decision thresholds are tuned separately."""
    (
        amount,
        _,
        missing,
        fx_missing,
        days,
        _,
        date_missing,
        merchant,
        _,
        merchant_missing,
        kind,
        kind_missing,
        category,
        category_missing,
        _,
        _,
        country,
        country_missing,
        *_,
    ) = features
    weights = (0.5, 0.25, 0.15, 0.05, 0.025, 0.025)
    present = (
        not missing and not fx_missing,
        not date_missing,
        not merchant_missing,
        not kind_missing,
        not category_missing,
        not country_missing,
    )
    values = (
        1.0 if amount <= 0.01 else max(0, 1 - amount / 0.35),
        max(0, 1 - days / 10),
        merchant,
        kind,
        category,
        country,
    )
    denominator = sum(
        weight for weight, available in zip(weights, present, strict=True) if available
    )
    return (
        sum(
            weight * value
            for weight, value, available in zip(weights, values, present, strict=True)
            if available
        )
        / denominator
        if denominator
        else 0.0
    )
