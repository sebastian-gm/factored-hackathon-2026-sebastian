"""V2 train/validation-only selection, followed by one reused synthetic diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import optuna

from aclara.data.pipeline import _pipeline_version
from aclara.data.snapshot import ROOT, write_json
from aclara.ml.charge_matcher.dataset import SEED, validation_partition
from aclara.ml.charge_matcher.evaluate import V2_COSTS, report, summarize_queries
from aclara.ml.charge_matcher.features import FEATURES, FxBook
from aclara.ml.charge_matcher.human_noise import augment, read_queries, serving_query
from aclara.ml.charge_matcher.model import Matcher, interpolate, logistic, query_features
from aclara.ml.charge_matcher.train import (
    Batch,
    Pointwise,
    _lightgbm,
    batch,
    exists_labels,
    fit_isotonic,
    fit_logistic,
    top_labels,
)
from aclara.ml.charge_matcher.types import Query

LOGGER = logging.getLogger(__name__)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calibrate(point: Pointwise, partitions: dict[str, Batch]) -> tuple[dict[str, Any], float]:
    tune, cal, policy = (partitions[key] for key in ("tune", "calibration", "policy"))
    ts = point.score(tune.x)
    tm = query_features(ts, tune.x, tune.groups)
    top_model = fit_logistic(tm, top_labels(tune, ts))
    exists_model = fit_logistic(tm, exists_labels(tune))
    cs = point.score(cal.x)
    cm = query_features(cs, cal.x, cal.groups)
    top_cal = fit_isotonic(logistic(cm, top_model), top_labels(cal, cs))
    exists_cal = fit_isotonic(logistic(cm, exists_model), exists_labels(cal))
    ps = point.score(policy.x)
    pm = query_features(ps, policy.x, policy.groups)
    top = interpolate(logistic(pm, top_model), top_cal)
    exists = interpolate(logistic(pm, exists_model), exists_cal)
    candidates = []
    for auto in (0.90, 0.95, 0.98, 1.01):
        for floor in (0.0, 0.001, 0.005, 0.01, 0.02):
            thresholds = {"auto": auto, "raw_score_floor": floor, "propose_exists": 0.90}
            rows = summarize_queries(
                policy.queries,
                ps,
                policy.groups,
                top,
                exists,
                thresholds,
                decision_policy="choice_first_v2",
                costs=V2_COSTS,
            )
            key = (
                sum(row["cost"] for row in rows) / len(rows),
                sum(row["action"] == "propose" and not row["correct"] for row in rows),
                sum(row["action"] == "none" and not row["true_none"] for row in rows),
                floor,
                -auto,
            )
            candidates.append((key, thresholds))
    key, thresholds = min(candidates, key=lambda pair: pair[0])
    return {
        "format_version": "2.0.0",
        "decision_policy": "choice_first_v2",
        "model": "lightgbm",
        "features": list(FEATURES),
        "pointwise": point.parameters,
        "query_features": ["top_score", "margin", "log1p_set_size", "slot_coverage"],
        "top_model": top_model,
        "exists_model": exists_model,
        "top_calibration": top_cal,
        "exists_calibration": exists_cal,
        "thresholds": thresholds,
        "cost_table": V2_COSTS,
    }, key[0]


def evaluate_model(model: Matcher, data: Batch) -> list[dict[str, Any]]:
    p = model.parameters
    scores = model.scores(data.x)
    meta = query_features(scores, data.x, data.groups)
    top = interpolate(logistic(meta, p["top_model"]), p["top_calibration"])
    exists = interpolate(logistic(meta, p["exists_model"]), p["exists_calibration"])
    rows = summarize_queries(
        data.queries,
        scores,
        data.groups,
        top,
        exists,
        p["thresholds"],
        decision_policy=p.get("decision_policy", "legacy_v1"),
        costs=V2_COSTS,
    )
    # Exercise every exported decision, not just its vectorized evaluator.
    for query, (start, end), row in zip(data.queries, data.groups, rows, strict=True):
        decision = model.decide(
            tuple(candidate.transaction_id for candidate in query.candidates), data.x[start:end]
        )
        if decision.action != row["action"] or not np.isclose(
            decision.top_correct_probability, row["top_probability"]
        ):
            raise RuntimeError("export decision parity failed")
    return rows


def save_queries(path: Path, queries: list[Query]) -> None:
    with path.open("x") as stream:
        for query in queries:
            stream.write(json.dumps(asdict(query), default=str, ensure_ascii=False) + "\n")


def train_v2(trials: int = 20) -> dict[str, Any]:
    private = ROOT / "artifacts/charge_matcher/v2"
    export = ROOT / "models/charge_matcher/v2"
    if (private / "started.json").exists() or export.exists():
        raise ValueError("v2 already started; preserve its artifacts and test access record")
    source = ROOT / "artifacts/charge_matcher/v1/dataset"
    prior = ROOT / "models/charge_matcher/v1"
    prior_meta = json.loads((prior / "metadata.json").read_text())
    private.mkdir(parents=True, exist_ok=True)
    write_json(private / "started.json", {"at": datetime.now(UTC).isoformat(), "trials": trials})
    v1_hashes = {path.name: sha(path) for path in prior.iterdir() if path.is_file()}
    data = {}
    for split in ("train", "validation"):
        path = source / f"{split}.jsonl"
        if sha(path) != prior_meta["files"][path.name]:
            raise ValueError("pinned v1 source split changed")
        data[split] = augment(read_queries(path), private / f"{split}-expressions.jsonl", SEED)
        save_queries(private / f"{split}.jsonl", data[split])
    train_customers = {q.customer_id for q in data["train"]}
    validation_customers = {q.customer_id for q in data["validation"]}
    if train_customers & validation_customers:
        raise ValueError("customer split leakage")
    fx = FxBook([])
    training = batch(data["train"], fx)
    partitions = {
        key: batch(
            [q for q in data["validation"] if validation_partition(q.customer_id) == key], fx
        )
        for key in ("tune", "calibration", "policy")
    }
    weights = np.asarray(
        [1 / (end - start) for start, end in training.groups for _ in range(end - start)]
    )
    tune = partitions["tune"]
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "num_leaves": trial.suggest_categorical("num_leaves", [7, 15]),
            "n_estimators": trial.suggest_categorical("n_estimators", [40, 80, 120]),
            "learning_rate": trial.suggest_float("learning_rate", 0.025, 0.15, log=True),
            "min_child_samples": trial.suggest_int("min_child_samples", 20, 100),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.01, 10, log=True),
        }
        fitted = _lightgbm(params).fit(training.x, training.y, sample_weight=weights)
        scores = np.asarray(fitted.predict_proba(tune.x), dtype=np.float64)[:, 1]
        labels = top_labels(tune, scores)
        return float(
            1
            - np.mean(labels[exists_labels(tune).astype(bool)])
            + 0.1 * np.mean((scores - tune.y) ** 2)
        )

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=SEED))
    study.optimize(objective, n_trials=trials)
    write_json(
        private / "optuna.json",
        {"trials": [{"params": t.params, "value": t.value} for t in study.trials]},
    )
    fitted = _lightgbm(study.best_params).fit(training.x, training.y, sample_weight=weights)
    point = Pointwise("lightgbm", study.best_params, fitted)
    parameters, policy_cost = calibrate(point, partitions)
    export.mkdir(parents=True)
    write_json(export / "model.json", parameters)
    fitted.booster_.save_model(str(export / "lightgbm.txt"))
    metadata = {
        "version": "v2",
        "dataset_version": prior_meta["dataset_version"],
        "bank_clock": prior_meta["bank_clock"],
        "git_sha": _pipeline_version(),
        "seed": SEED,
        "trials": trials,
        "noise_version": "2.0.0",
        "selected_on_validation": "lightgbm",
        "validation_policy_cost": policy_cost,
        "decision_policy": "choice_first_v2",
        "serving_projection": "category=None, channel='', country=''; default empty FX",
        "nlu_measurement": "template extraction + actual postprocess, not real NLU",
        "counts": {split: len(queries) for split, queries in data.items()},
        "customers": {split: len({q.customer_id for q in qs}) for split, qs in data.items()},
        "noise_counts": {
            split: dict(Counter(q.noise_family for q in qs)) for split, qs in data.items()
        },
        "validation_partition_counts": {k: len(v.queries) for k, v in partitions.items()},
        "source_files": prior_meta["files"],
        "training_code_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))
        ).hexdigest(),
        "nlu_postprocessor_sha256": sha(ROOT / "src/aclara/agent/nlu/structured.py"),
        "protocol_sha256": sha(ROOT / "docs/ml/matcher-v2-protocol.md"),
        "frozen_at": datetime.now(UTC).isoformat(),
        "frozen_model_files": {name: sha(export / name) for name in ("model.json", "lightgbm.txt")},
        "artifact_policy": "numeric parameters and aggregates only; no row data",
    }
    write_json(private / "model-freeze.json", metadata)
    write_json(export / "metadata.json", metadata)
    LOGGER.info(
        "V2 frozen; policy validation cost %.4f; thresholds %s",
        policy_cost,
        parameters["thresholds"],
    )
    # Only now read the old matcher test. This is not the frozen scenario suite.
    touch = {
        "at": datetime.now(UTC).isoformat(),
        "purpose": "authorized reused synthetic diagnostic",
    }
    write_json(private / "test_touch.json", touch)
    test_path = source / "test.jsonl"
    if sha(test_path) != prior_meta["files"][test_path.name]:
        raise ValueError("pinned v1 test source changed")
    original = read_queries(test_path)
    test_customers = {q.customer_id for q in original}
    if test_customers & (train_customers | validation_customers):
        raise ValueError("test customer leakage")
    augmented = augment(original, private / "test-expressions.jsonl", SEED)
    save_queries(private / "test.jsonl", augmented)
    # Augmentation retains each original first; separate original from new variants.
    original_batch = batch([serving_query(q) for q in original], fx)
    human_like_batch = batch([q for q in augmented if q.noise_family.startswith("human_")], fx)
    models = {"v1": Matcher(prior), "v2": Matcher(export)}
    if not np.allclose(models["v2"].scores(tune.x), point.score(tune.x), atol=1e-10, rtol=1e-10):
        raise RuntimeError("export scoring parity failed")
    results: dict[str, Any] = {}
    for name, test_batch in (
        ("original_3000", original_batch),
        ("human_like_6000", human_like_batch),
    ):
        results[name] = {}
        for version, model in models.items():
            rows = evaluate_model(model, test_batch)
            with (private / f"{name}-{version}-predictions.jsonl").open("x") as stream:
                for row in rows:
                    stream.write(json.dumps(row) + "\n")
            results[name][version] = report(rows)
            LOGGER.info(
                "%s %s aggregate: %s", name, version, json.dumps(results[name][version]["overall"])
            )
    metadata.update(
        test_touch=touch,
        test_counts={"original": len(original), "human_like": len(human_like_batch.queries)},
        export_parity_verified=True,
    )
    if any(sha(export / name) != value for name, value in metadata["frozen_model_files"].items()):
        raise RuntimeError("model changed after freeze")
    if {p.name: sha(p) for p in prior.iterdir() if p.is_file()} != v1_hashes:
        raise RuntimeError("v1 artifact changed")
    write_json(export / "metrics.json", results)
    write_json(export / "metadata.json", metadata)
    write_json(
        export / "checksums.json",
        {p.name: sha(p) for p in export.iterdir() if p.name != "checksums.json"},
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=20)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    train_v2(args.trials)


if __name__ == "__main__":
    main()
