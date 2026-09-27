from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pytest

from aclara.ml.charge_matcher.evaluate import COSTS, V2_COSTS, summarize_queries
from aclara.ml.charge_matcher.features import FEATURES, FxBook, candidate_features
from aclara.ml.charge_matcher.human_noise import (
    HUMAN_FAMILIES,
    augment,
    expression_noise,
    read_queries,
    serving_query,
)
from aclara.ml.charge_matcher.model import Matcher, choice_first_decisions, decisions
from aclara.ml.charge_matcher.types import Candidate, Query, Slots


def query() -> Query:
    candidate = Candidate(
        "fixture-target",
        "fixture-customer",
        datetime(2025, 12, 5, 12, tzinfo=UTC),
        date(2025, 12, 5),
        1100,
        "USD",
        "Fixture Hardware",
        "Purchase",
        "Hardware",
        "POS",
        "MX",
        "Approved",
    )
    return Query(
        "fixture-query",
        "fixture-customer",
        datetime(2025, 12, 9, 6, tzinfo=UTC),
        Slots(amount=1100, currency="USD", date_start=candidate.process_date),
        (candidate,),
        candidate.transaction_id,
        "train",
        "complete",
        "MX",
        "Basic",
    )


def test_choice_fallback_ignores_low_existence_and_respects_raw_floor() -> None:
    top = np.asarray([0.01, 0.97, 0.97, 0.01, 0.01])
    exists = np.asarray([0.0, 0.95, 0.01, 0.0, 0.0])
    maximum = np.asarray([0.2, 0.8, 0.8, 0.0009, 0.001])
    thresholds = {"auto": 0.95, "propose_exists": 0.9, "raw_score_floor": 0.001}
    assert choice_first_decisions(top, exists, maximum, thresholds) == [
        "choose",
        "propose",
        "choose",
        "none",
        "choose",
    ]
    assert decisions(top[:1], exists[:1], {"auto": 0.9, "choice": 0, "none": 0.15}) == ["none"]
    assert choice_first_decisions(
        top[:1], exists[:1], np.asarray([0.0]), {**thresholds, "raw_score_floor": 0.0}
    ) == ["choose"]


def test_v2_export_preserves_stable_choices_and_empty_set(tmp_path: Path) -> None:
    # Constant confidence heads make the intended policy boundary independent of training.
    zeros = {"mean": [0.0] * 4, "scale": [1.0] * 4, "coefficients": [0.0] * 4, "intercept": 0.0}
    params = {
        "model": "rules",
        "features": list(FEATURES),
        "decision_policy": "choice_first_v2",
        "top_model": zeros,
        "exists_model": zeros,
        "top_calibration": {"x": [0, 1], "y": [0, 0]},
        "exists_calibration": {"x": [0, 1], "y": [0, 0]},
        "thresholds": {"auto": 0.95, "propose_exists": 0.9, "raw_score_floor": 0.001},
    }
    (tmp_path / "model.json").write_text(json.dumps(params))
    model = Matcher(tmp_path)
    target = query().candidates[0]
    candidates = tuple(replace(target, transaction_id=f"fixture-{i}") for i in range(4))
    x = np.asarray(candidate_features(Slots(amount=1100, currency="USD"), candidates, FxBook([])))
    decision = model.decide(tuple(c.transaction_id for c in candidates), x)
    assert decision.action == "choose"
    assert decision.transaction_ids == ("fixture-0", "fixture-1", "fixture-2")
    assert model.decide((), np.empty((0, len(FEATURES)))).transaction_ids == ()
    assert model.decide((), np.empty((0, len(FEATURES)))).action == "none"
    with pytest.raises(ValueError, match="size mismatch"):
        model.decide(("fixture",), x)


def test_noise_keeps_labels_scopes_and_models_literal_formats(tmp_path: Path) -> None:
    original = query()
    for family in HUMAN_FAMILIES:
        first, evidence = expression_noise(original, family, 42)
        assert (first, evidence) == expression_noise(original, family, 42)
        assert first.target_id == original.target_id
        assert first.customer_id == original.customer_id and first.split == "train"
        assert first.as_of == original.as_of
        assert first.slots.date_start is first.slots.date_end is None
        assert first.candidates[0].category is None
        assert first.candidates[0].channel == first.candidates[0].country == ""
        negative, _ = expression_noise(replace(original, target_id=None), family, 42)
        assert negative.target_id is None
    thousands, evidence = expression_noise(original, "thousands", 42)
    assert evidence["synthetic_extraction"]["amount_expr"] == "1,100"
    assert thousands.slots.amount == 1100
    suffixed, evidence = expression_noise(
        replace(original, candidates=(replace(original.candidates[0], amount=8600),)),
        "k_suffix",
        42,
    )
    assert evidence["synthetic_extraction"]["amount_expr"] == "8.6k"
    # Preserve the current serving parser defect in synthetic calibration, rather than
    # secretly giving the matcher an idealized slot it cannot receive in the app.
    assert suffixed.slots.amount != 8600
    _, evidence = expression_noise(original, "merchant_type", 42)
    assert evidence["synthetic_extraction"]["merchant_expr"] == "una ferretería"
    variants = augment([original], tmp_path / "expressions.jsonl", 7)
    assert len(variants) == 3 and variants[0] == serving_query(original)
    path = tmp_path / "queries.jsonl"
    path.write_text("\n".join(json.dumps(asdict(q), default=str) for q in variants))
    assert read_queries(path) == variants


def test_evaluation_uses_choice_policy_and_explicit_cost_version() -> None:
    q = query()
    scores = np.asarray([0.2])
    top = exists = np.asarray([0.0])
    thresholds = {"auto": 0.95, "propose_exists": 0.9, "raw_score_floor": 0.001}
    choice = summarize_queries(
        [q],
        scores,
        [(0, 1)],
        top,
        exists,
        thresholds,
        decision_policy="choice_first_v2",
        costs=V2_COSTS,
    )[0]
    assert choice["action"] == "choose" and choice["cost"] == 1
    legacy = summarize_queries(
        [q],
        scores,
        [(0, 1)],
        top,
        exists,
        {"auto": 0.9, "none": 0.15, "choice": 0},
    )[0]
    assert legacy["action"] == "none" and legacy["cost"] == COSTS["false_none"] == 3
    low = summarize_queries(
        [q],
        np.asarray([0.0001]),
        [(0, 1)],
        top,
        exists,
        thresholds,
        decision_policy="choice_first_v2",
        costs=V2_COSTS,
    )[0]
    assert low["action"] == "none" and low["cost"] == V2_COSTS["false_none"] == 6
