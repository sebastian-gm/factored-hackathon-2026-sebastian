# ruff: noqa: E402 -- skip optional ML dependencies before importing their consumers.
from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb
import pytest

pytest.importorskip("rapidfuzz")
np = pytest.importorskip("numpy")

from aclara.ml.charge_matcher.dataset import (
    build_dataset,
    customer_split,
    retrieve,
    validation_partition,
)
from aclara.ml.charge_matcher.features import FEATURES, FxBook, candidate_features, rules_score
from aclara.ml.charge_matcher.model import Matcher
from aclara.ml.charge_matcher.types import Candidate, Slots


def row() -> Candidate:
    return Candidate(
        "fixture-txn",
        "fixture-a",
        datetime(2026, 6, 17, 12, tzinfo=UTC),
        date(2026, 6, 17),
        100,
        "USD",
        "Fixture Cafe",
        "Purchase",
        None,
        "POS",
        "MX",
        "Approved",
    )


def test_retrieval_is_scoped_and_as_of() -> None:
    clock = datetime(2026, 6, 18, 6, tzinfo=UTC)
    original = row()
    first = replace(original, transaction_id="first", transaction_date=clock - timedelta(days=120))
    old = replace(
        original, transaction_id="old", transaction_date=clock - timedelta(days=120, seconds=1)
    )
    future = replace(original, transaction_id="future", transaction_date=clock)
    other = replace(original, transaction_id="other", customer_id="fixture-b")
    assert {
        r.transaction_id
        for r in retrieve([original, first, old, future, other], "fixture-a", clock)
    } == {"first", "fixture-txn"}
    with pytest.raises(ValueError, match="timezone"):
        retrieve([], "fixture-a", datetime(2026, 6, 18))  # noqa: DTZ001 -- rejected input


def test_fx_uses_candidate_business_date_and_unknown_currency_is_neutral() -> None:
    fx = FxBook(
        [(date(2026, 6, 16), "COP", "USD", 0.00025), (date(2026, 6, 18), "COP", "USD", 0.0005)]
    )
    features = candidate_features(Slots(amount=400000, currency="COP"), (row(),), fx)[0]
    assert features[0] == 0
    ambiguous = candidate_features(Slots(amount=400000, currency=None), (row(),), fx)[0]
    assert ambiguous[3] == 1
    assert ambiguous[0] == 0
    assert not {"fraud_score", "is_fraud", "target_id", "noise_family"} & set(FEATURES)
    assert fx.convert(1, "COP", "USD", date(2026, 6, 15)) is None


def test_artifact_roundtrip_and_empty_set(tmp_path: Path) -> None:
    zeros = {"mean": [0.0] * 4, "scale": [1.0] * 4, "coefficients": [0.0] * 4, "intercept": 0.0}
    artifact = {
        "model": "rules",
        "features": list(FEATURES),
        "top_model": zeros,
        "exists_model": zeros,
        "top_calibration": {"x": [0, 1], "y": [0, 1]},
        "exists_calibration": {"x": [0, 1], "y": [0, 1]},
        "thresholds": {"none": 0.2, "choice": 0.1, "auto": 0.9},
    }
    (tmp_path / "model.json").write_text(json.dumps(artifact))
    matcher = Matcher(tmp_path)
    candidates = (row(), replace(row(), transaction_id="second", amount=1000))
    x = np.asarray(candidate_features(Slots(amount=100, currency="USD"), candidates, FxBook([])))
    assert rules_score(x[0].tolist()) > rules_score(x[1].tolist())
    assert matcher.decide(("fixture-txn", "second"), x).transaction_ids[0] == "fixture-txn"
    assert matcher.decide((), np.empty((0, len(FEATURES)))).action == "none"


def test_generated_dataset_leakage_and_noise_holdout(tmp_path: Path) -> None:
    database = tmp_path / "fixture.duckdb"
    with duckdb.connect(str(database)) as db:
        db.execute("CREATE SCHEMA gold")
        db.execute(
            "CREATE TABLE gold.customers AS SELECT 'fixture-'||i AS customer_id, 'MX' AS country,'Basic' AS segment FROM range(200) r(i)"
        )
        db.execute(
            "CREATE TABLE gold.matcher_ledger AS SELECT customer_id||'-'||j AS transaction_id,customer_id, CAST(day AS TIMESTAMPTZ)+INTERVAL 12 HOUR AS transaction_date,day::DATE AS process_date, (50+j*7)::DOUBLE AS amount,'USD' AS currency,'Fixture Cafe' AS merchant_name,'Purchase' AS transaction_type,NULL::VARCHAR AS transaction_category,'POS' AS channel,'MX' AS transaction_country,'Approved' AS transaction_status,'fixture-version' AS _dataset_version FROM gold.customers CROSS JOIN (VALUES (1,DATE '2025-12-15'),(2,DATE '2026-01-10'),(3,DATE '2026-02-20'),(4,DATE '2026-03-15'),(5,DATE '2026-04-15'),(6,DATE '2026-05-15')) d(j,day)"
        )
        db.execute(
            "CREATE TABLE gold.fx_rates AS SELECT DATE '2025-01-01' AS date,'USD' AS source_currency,'MXN' AS target_currency,20.0::DOUBLE AS exchange_rate"
        )
        db.execute(
            "CREATE TABLE gold.problem_analysis AS SELECT 'bank_clock' AS metric, '\"2026-06-18T06:00:00+00:00\"' AS value"
        )
    datasets, _, meta = build_dataset(
        database, tmp_path / "private", train_n=60, validation_n=60, test_n=60
    )
    groups = []
    for split, queries in datasets.items():
        groups.append({q.customer_id for q in queries})
        assert all(customer_split(q.customer_id) == split for q in queries)
        assert sum(q.target_id is None for q in queries) == 9
        for q in queries:
            assert all(
                c.customer_id == q.customer_id
                and q.as_of - timedelta(days=120) <= c.transaction_date < q.as_of
                for c in q.candidates
            )
            target = next((c for c in q.candidates if c.transaction_id == q.target_id), None)
            if target is not None:
                assert (target.process_date >= date(2026, 3, 1)) == (split == "test")
    assert not groups[0] & groups[1] and not groups[0] & groups[2] and not groups[1] & groups[2]
    assert not {q.noise_family for q in datasets["train"]} & set(meta["test_only_noise_families"])
    assert any(q.noise_family.startswith("stress") for q in datasets["test"])
    partitions = [
        {
            q.customer_id
            for q in datasets["validation"]
            if validation_partition(q.customer_id) == name
        }
        for name in ("tune", "calibration", "policy")
    ]
    assert not partitions[0] & partitions[1] and not partitions[0] & partitions[2]
