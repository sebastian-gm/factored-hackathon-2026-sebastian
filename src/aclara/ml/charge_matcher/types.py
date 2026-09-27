"""The matcher receives already authorized candidates, never grants access."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Candidate:
    transaction_id: str
    customer_id: str
    transaction_date: datetime
    process_date: date
    amount: float
    currency: str
    merchant: str | None
    transaction_type: str
    category: str | None
    channel: str
    country: str
    status: str


@dataclass(frozen=True)
class Slots:
    amount: float | None = None
    currency: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    merchant: str | None = None
    transaction_type: str | None = None
    category: str | None = None
    channel: str | None = None
    country: str | None = None


@dataclass(frozen=True)
class Query:
    query_id: str
    customer_id: str
    as_of: datetime
    slots: Slots
    candidates: tuple[Candidate, ...]
    target_id: str | None
    split: str
    noise_family: str
    customer_country: str
    segment: str


@dataclass(frozen=True)
class Decision:
    action: str
    transaction_ids: tuple[str, ...]
    top_correct_probability: float
    match_exists_probability: float
