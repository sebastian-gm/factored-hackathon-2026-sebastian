"""Calibrated MATCH state over code-authorized candidates and normalized slots."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from aclara.agent.nlu.structured import NormalizedSlots
from aclara.bank.repository import Transaction
from aclara.ml.charge_matcher.features import FxBook, candidate_features
from aclara.ml.charge_matcher.model import Matcher
from aclara.ml.charge_matcher.types import Candidate, Decision, Slots

ROOT = Path(__file__).resolve().parents[3]


class MatchState:
    def __init__(self, artifact: Path | None = None, fx: FxBook | None = None):
        path = artifact or ROOT / "models/charge_matcher/v2"
        checksums = json.loads((path / "checksums.json").read_text())
        for name in ("model.json", "lightgbm.txt", "metadata.json"):
            if hashlib.sha256((path / name).read_bytes()).hexdigest() != checksums[name]:
                raise ValueError("Matcher artifact checksum mismatch")
        self.matcher = Matcher(path)
        self.version = json.loads((path / "metadata.json").read_text())["version"]
        self.fx = fx or FxBook([])

    def match(
        self,
        slots: NormalizedSlots,
        rows: list[tuple[str, Transaction]],
        customer: str,
        clock: datetime,
    ) -> Decision:
        if any(
            row.customer_id != customer
            or not clock - timedelta(days=120) <= row.transaction_date < clock
            for _, row in rows
        ):
            raise ValueError("MATCH received an unauthorized or out-of-window candidate")
        candidates = tuple(
            Candidate(
                handle,
                row.customer_id,
                row.transaction_date,
                row.process_date,
                row.amount,
                row.currency,
                row.merchant_name,
                row.transaction_type,
                None,
                "",
                "",
                row.transaction_status,
            )
            for handle, row in rows
        )
        query = Slots(
            amount=float(slots.amount_value) if slots.amount_value is not None else None,
            currency=slots.currency,
            date_start=slots.date_start,
            date_end=slots.date_end,
            merchant=slots.merchant_expr,
            transaction_type=slots.type_expr,
            country=slots.country_expr,
        )
        matrix = np.asarray(candidate_features(query, candidates, self.fx), dtype=np.float64)
        return self.matcher.decide(tuple(handle for handle, _ in rows), matrix)
