"""Reproducible recollections with customer, time and noise-family holdouts."""

# ruff: noqa: S608 -- fixed split predicates and integer limits; source values are bound.
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

import duckdb

from aclara.ml.charge_matcher.features import FxBook
from aclara.ml.charge_matcher.types import Candidate, Query, Slots

SEED = 20260926
CUTOFF = date(2026, 3, 1)
FAMILIES = (
    "complete",
    "partial",
    "amount_approx",
    "date_fuzzy",
    "currency_confusion",
    "merchant_typo",
    "type_only",
    "country_only",
)
STRESS_FAMILIES = ("stress_rounded_partial", "stress_amount_date")


def customer_split(customer_id: str) -> str:
    value = int(hashlib.sha256(customer_id.encode()).hexdigest()[:2], 16)
    return "train" if value < 179 else "validation" if value < 218 else "test"


def validation_partition(customer_id: str) -> str:
    value = int(hashlib.sha256(("validation:" + customer_id).encode()).hexdigest()[:8], 16) % 3
    return ("tune", "calibration", "policy")[value]


def retrieve(ledger: list[Candidate], customer_id: str, as_of: datetime) -> tuple[Candidate, ...]:
    if as_of.tzinfo is None:
        raise ValueError("query as-of must be timezone-aware")
    start = as_of - timedelta(days=120)
    return tuple(
        sorted(
            (
                row
                for row in ledger
                if row.customer_id == customer_id and start <= row.transaction_date < as_of
            ),
            key=lambda r: r.transaction_id,
        )
    )


def noise(target: Candidate, family: str, rng: random.Random, fx: FxBook) -> Slots:
    amount, currency = target.amount, target.currency
    start = end = target.process_date
    merchant = target.merchant if target.transaction_type == "Purchase" else None
    kind: str | None = target.transaction_type
    country: str | None = None
    if family == "partial":
        if rng.random() < 0.5:
            merchant, kind = None, None
        else:
            amount, currency = None, None  # type: ignore[assignment]
    elif family in {"amount_approx", "stress_amount_date"}:
        amount *= 1 + rng.choice([-1, 1]) * rng.uniform(0.05, 0.30)
        if family.startswith("stress"):
            start += timedelta(days=rng.choice([-7, 7]))
            end = start
            merchant = None
    elif family == "date_fuzzy":
        center = target.process_date + timedelta(days=rng.choice([-7, -3, -1, 1, 3, 7]))
        start, end = center - timedelta(days=1), center + timedelta(days=1)
    elif family == "currency_confusion":
        # Query currency is sometimes explicit (convert), sometimes unresolved (neutral amount).
        currency = "MXN" if target.currency == "USD" else "USD"
        value = fx.convert(target.amount, target.currency, currency, target.process_date)
        amount = value if value is not None else target.amount
        if rng.random() < 0.5:
            currency = None  # type: ignore[assignment]
    elif family == "merchant_typo" and merchant:
        index = rng.randrange(len(merchant))
        merchant = merchant[:index] + merchant[index + 1 :]
    elif family == "type_only":
        return Slots(transaction_type=kind)
    elif family == "country_only":
        return Slots(country=target.country)
    elif family == "stress_rounded_partial":
        magnitude = 10 ** max(0, len(str(int(target.amount))) - 2)
        amount = round(target.amount / magnitude) * magnitude
        kind, merchant = None, None
        start, end = (
            target.process_date - timedelta(days=7),
            target.process_date + timedelta(days=7),
        )
    return Slots(
        amount=amount,
        currency=currency,
        date_start=start,
        date_end=end,
        merchant=merchant,
        transaction_type=kind,
        country=country,
    )


def _candidate(row: tuple[Any, ...]) -> Candidate:
    return Candidate(
        str(row[0]),
        str(row[1]),
        row[2],
        row[3],
        float(row[4]),
        str(row[5]),
        row[6],
        str(row[7]),
        row[8],
        str(row[9]),
        str(row[10]),
        str(row[11]),
    )


def build_dataset(
    database: Path,
    output: Path,
    *,
    train_n: int = 6000,
    validation_n: int = 3000,
    test_n: int = 3000,
    seed: int = SEED,
) -> tuple[dict[str, list[Query]], FxBook, dict[str, Any]]:
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)  # noqa: S311 -- reproducible synthetic noise, not security.
    db = duckdb.connect(str(database), read_only=True)
    columns = "transaction_id,customer_id,transaction_date,process_date,amount,currency,merchant_name,transaction_type,transaction_category,channel,transaction_country,transaction_status"
    try:
        fx = FxBook(
            db.execute(
                "SELECT date,source_currency,target_currency,exchange_rate FROM gold.fx_rates"
            ).fetchall()
        )
        versions = db.execute(
            "SELECT DISTINCT _dataset_version FROM gold.matcher_ledger"
        ).fetchall()
        if len(versions) != 1:
            raise ValueError("training requires one pinned dataset version")
        version = str(versions[0][0])
        # Serving clock is part of the aggregate mart, not the machine's wall clock.
        clock_row = db.execute(
            "SELECT value FROM gold.problem_analysis WHERE metric='bank_clock'"
        ).fetchone()
        if clock_row is None:
            raise ValueError("gold bank clock is missing")
        bank_clock = datetime.fromisoformat(json.loads(clock_row[0]))
        datasets = {}
        predicates = {
            "train": "substr(sha256(customer_id),1,2)<'b3' AND process_date<DATE '2026-01-01'",
            "validation": "substr(sha256(customer_id),1,2)>='b3' AND substr(sha256(customer_id),1,2)<'da' AND process_date>=DATE '2026-01-01' AND process_date<DATE '2026-03-01'",
            "test": "substr(sha256(customer_id),1,2)>='da' AND process_date>=DATE '2026-03-01'",
        }
        for split, n in (("train", train_n), ("validation", validation_n), ("test", test_n)):
            selected = db.execute(
                f"SELECT {columns} FROM gold.matcher_ledger WHERE {predicates[split]} AND transaction_date<? ORDER BY sha256(transaction_id || ?) LIMIT {int(n)}",
                [bank_clock, str(seed)],
            ).fetchall()
            targets = [_candidate(row) for row in selected]
            if len(targets) != n:
                raise ValueError("not enough targets for requested split sizes")
            customer_ids = sorted({row.customer_id for row in targets})
            db.execute(
                "CREATE TEMP TABLE selected_customers AS SELECT unnest(?::VARCHAR[]) AS customer_id",
                [customer_ids],
            )
            ledger_rows = db.execute(
                f"SELECT {columns} FROM gold.matcher_ledger JOIN selected_customers USING(customer_id)"
            ).fetchall()
            attrs = dict(
                (str(c), (str(country), str(segment)))
                for c, country, segment in db.execute(
                    "SELECT customer_id,country,segment FROM gold.customers JOIN selected_customers USING(customer_id)"
                ).fetchall()
            )
            db.execute("DROP TABLE selected_customers")
            ledger: dict[str, list[Candidate]] = {}
            for row in ledger_rows:
                candidate = _candidate(row)
                ledger.setdefault(candidate.customer_id, []).append(candidate)
            queries = []
            for index, target in enumerate(targets):
                as_of = min(
                    datetime.combine(
                        target.process_date + timedelta(days=rng.randrange(11) + 1),
                        time(6),
                        tzinfo=UTC,
                    ),
                    bank_clock,
                )
                candidates = retrieve(ledger[target.customer_id], target.customer_id, as_of)
                family = (
                    STRESS_FAMILIES[index % 2]
                    if split == "test" and index % 5 == 0
                    else rng.choice(FAMILIES)
                )
                no_match = index % 20 < 3
                donor = target
                # Use another customer only within this customer/time split, before this query clock.
                if no_match and index % 2 == 0:
                    eligible = [
                        other
                        for other in targets
                        if other.customer_id != target.customer_id
                        and as_of - timedelta(days=120) <= other.transaction_date < as_of
                    ]
                    if eligible:
                        donor = rng.choice(eligible)
                slots = noise(donor, family, rng, fx)
                if no_match and donor is target:
                    # Fabricated recollection in a plausible range, not an impossible sentinel feature.
                    slots = Slots(
                        amount=target.amount * rng.uniform(0.4, 2.5),
                        currency=target.currency,
                        date_start=target.process_date - timedelta(days=rng.randrange(1, 30)),
                        transaction_type=rng.choice(["Purchase", "Withdrawal", "Payment"]),
                        country=target.country,
                    )
                if target not in candidates:
                    raise ValueError("target not visible at its as-of clock")
                country, segment = attrs[target.customer_id]
                query_id = hashlib.sha256(f"{version}:{seed}:{split}:{index}".encode()).hexdigest()
                queries.append(
                    Query(
                        query_id,
                        target.customer_id,
                        as_of,
                        slots,
                        candidates,
                        None if no_match else target.transaction_id,
                        split,
                        family,
                        country,
                        segment,
                    )
                )
            datasets[split] = queries
            with (output / f"{split}.jsonl").open("w") as stream:
                for query in queries:
                    stream.write(json.dumps(asdict(query), default=str, ensure_ascii=False) + "\n")
        groups = [
            {query.customer_id for query in datasets[split]}
            for split in ("train", "validation", "test")
        ]
        if groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]:
            raise ValueError("customer split leakage")
        metadata = {
            "dataset_version": version,
            "seed": seed,
            "bank_clock": bank_clock.isoformat(),
            "noise_version": "1.0.0",
            "train_target_end_exclusive": "2026-01-01",
            "validation_target_range": ["2026-01-01", "2026-03-01"],
            "test_target_start": "2026-03-01",
            "candidate_window": "[query_as_of - 120 days, query_as_of)",
            "counts": {split: len(queries) for split, queries in datasets.items()},
            "customers": {
                split: len({query.customer_id for query in queries})
                for split, queries in datasets.items()
            },
            "no_match_share": {
                split: sum(query.target_id is None for query in queries) / len(queries)
                for split, queries in datasets.items()
            },
            "test_only_noise_families": list(STRESS_FAMILIES),
            "source_class": "organizer synthetic ledger + team-generated normalized recollections",
            "excluded_inputs": [
                "overlays",
                "fraud_score",
                "is_fraud",
                "generator parameters",
                "complaint text",
                "transcripts",
            ],
            "files": {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(output.glob("*.jsonl"))
            },
        }
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        return datasets, fx, metadata
    finally:
        db.close()
