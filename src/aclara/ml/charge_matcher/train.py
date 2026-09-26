"""Local-only Optuna/MLflow comparison with a single held-out test touch."""
# ruff: noqa: E402 -- disable telemetry before importing the optional tracking SDK.

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "true"
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"

import mlflow
import numpy as np
import optuna
from dotenv import dotenv_values
from lightgbm import LGBMClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from aclara.data.pipeline import _pipeline_version
from aclara.data.snapshot import ROOT, write_json
from aclara.ml.charge_matcher.dataset import SEED, build_dataset, validation_partition
from aclara.ml.charge_matcher.evaluate import COSTS, choose_thresholds, report, summarize_queries
from aclara.ml.charge_matcher.features import FEATURES, FxBook, candidate_features, rules_score
from aclara.ml.charge_matcher.model import Array, Matcher, interpolate, logistic, query_features
from aclara.ml.charge_matcher.types import Query

LOGGER = logging.getLogger(__name__)


@dataclass
class Batch:
    queries: list[Query]
    x: Array
    y: Array
    groups: list[tuple[int, int]]


def batch(queries: list[Query], fx: FxBook) -> Batch:
    x: list[list[float]] = []
    y: list[float] = []
    groups = []
    for query in queries:
        start = len(x)
        x.extend(candidate_features(query.slots, query.candidates, fx))
        y.extend(float(row.transaction_id == query.target_id) for row in query.candidates)
        groups.append((start, len(x)))
    return Batch(
        queries,
        np.asarray(x, dtype=np.float64).reshape(-1, len(FEATURES)),
        np.asarray(y, dtype=np.float64),
        groups,
    )


def fit_logistic(x: Array, y: Array, weights: Array | None = None) -> dict[str, Any]:
    if len(set(y.tolist())) < 2:
        raise ValueError("calibration or training partition needs both label classes")
    scaler = StandardScaler().fit(x)
    model = LogisticRegression(max_iter=1000, random_state=SEED, C=1.0).fit(
        scaler.transform(x), y, sample_weight=weights
    )
    return {
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coefficients": model.coef_[0].tolist(),
        "intercept": float(model.intercept_[0]),
    }


def fit_isotonic(x: Array, y: Array) -> dict[str, Any]:
    model = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip").fit(x, y)
    return {"x": model.X_thresholds_.tolist(), "y": model.y_thresholds_.tolist()}


@dataclass
class Pointwise:
    name: str
    parameters: dict[str, Any]
    fitted: Any = None

    def score(self, x: Array) -> Array:
        if self.name == "rules":
            return np.asarray([rules_score(row.tolist()) for row in x], dtype=np.float64)
        if self.name == "logistic":
            return logistic(x, self.parameters)
        return np.asarray(self.fitted.predict_proba(x)[:, 1], dtype=np.float64)


def top_labels(data: Batch, scores: Array) -> Array:
    return np.asarray(
        [
            data.y[start + int(np.argmax(scores[start:end]))] if end > start else 0
            for start, end in data.groups
        ],
        dtype=np.float64,
    )


def exists_labels(data: Batch) -> Array:
    return np.asarray([query.target_id is not None for query in data.queries], dtype=np.float64)


def calibrated(
    pointwise: Pointwise, tune: Batch, calibration: Batch, policy: Batch
) -> tuple[dict[str, Any], float]:
    tune_scores = pointwise.score(tune.x)
    tune_meta = query_features(tune_scores, tune.x, tune.groups)
    top_model = fit_logistic(tune_meta, top_labels(tune, tune_scores))
    exists_model = fit_logistic(tune_meta, exists_labels(tune))
    cal_scores = pointwise.score(calibration.x)
    cal_meta = query_features(cal_scores, calibration.x, calibration.groups)
    top_cal = fit_isotonic(logistic(cal_meta, top_model), top_labels(calibration, cal_scores))
    exists_cal = fit_isotonic(logistic(cal_meta, exists_model), exists_labels(calibration))
    policy_scores = pointwise.score(policy.x)
    policy_meta = query_features(policy_scores, policy.x, policy.groups)
    p_top = interpolate(logistic(policy_meta, top_model), top_cal)
    p_exists = interpolate(logistic(policy_meta, exists_model), exists_cal)
    thresholds, cost = choose_thresholds(
        policy.queries, policy_scores, policy.groups, p_top, p_exists
    )
    return {
        "format_version": "1.0.0",
        "model": pointwise.name,
        "features": list(FEATURES),
        "pointwise": pointwise.parameters,
        "query_features": ["top_score", "margin", "log1p_set_size", "slot_coverage"],
        "top_model": top_model,
        "exists_model": exists_model,
        "top_calibration": top_cal,
        "exists_calibration": exists_cal,
        "thresholds": thresholds,
        "cost_table": COSTS,
    }, cost


def _lightgbm(parameters: dict[str, Any]) -> LGBMClassifier:
    return LGBMClassifier(
        **parameters,
        objective="binary",
        random_state=SEED,
        n_jobs=2,
        verbosity=-1,
        deterministic=True,
        force_col_wise=True,
    )


def _card(
    version: str,
    metadata: dict[str, Any],
    results: dict[str, Any],
    selected: str,
    recommendation: str,
) -> None:
    lines = [
        "# Charge matcher model card",
        "",
        f"Version: `{version}`. Dataset: `{metadata['dataset_version']}`. Seed: {SEED}.",
        "",
        f"Validation-selected model: **{selected}**. Deployment recommendation after the one-time comparison: **{recommendation}**.",
        "",
        "## Intended use",
        "",
        "Rank a verified customer’s already-authorized transaction candidates from normalized recollection slots. A proposal always requires customer confirmation. The matcher has no identity, policy or write authority. Currency conversion uses the candidate transaction’s business date. Missing FX is neutral evidence, never an invented conversion.",
        "",
        "## Data and leakage controls",
        "",
        "Organizer synthetic ledger; team-generated normalized recollections, with 15% no-match queries. No raw source rows are committed. No real customer language or NLU quality is measured. Customer groups use SHA-256 buckets and are disjoint. Train targets are before 2026-01-01, validation targets in January–February 2026, and test targets from 2026-03-01. Each query has its own as-of clock and a half-open 120-day retrieval window. Overlay fixtures, fraud fields, generator parameters, target identity and complaint/transcript text are excluded from features.",
        "",
        f"Query counts: `{json.dumps(metadata['counts'], sort_keys=True)}`. Unique customer counts: `{json.dumps(metadata['customers'], sort_keys=True)}`.",
        "",
        "Validation customers are split again into tuning, calibration and policy groups. Hyperparameters and the two query-level logistic heads use tuning only; isotonic calibrators use calibration only; decision thresholds use policy only. Test-only stress noise families are frozen in the dataset metadata. Test touches are append-only local records by version.",
        "",
        "## Models and operating point",
        "",
        "Fixed rules scorer, scaled pointwise logistic regression, and pointwise LightGBM use the same features and queries. Each has query-level match-exists and top-correct heads followed by isotonic calibration. Thresholds minimize validation cost: wrong proposal 10, extra turn 1, false no-match 3, choice missing the target 4. The simplest model within 0.02 expected cost of the best validation cost is selected before opening test.",
        "",
        "| Model | Top-1 | MRR | Recall@3 | NONE precision | NONE recall | ECE | Cost/query | Wrong proposals / proposals |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def value(v: Any) -> str:
        return f"{v:.4f}" if isinstance(v, float) else "undefined" if v is None else str(v)

    for name, result in results.items():
        m = result["overall"]
        lines.append(
            "| "
            + name
            + " | "
            + " | ".join(
                value(m[k])
                for k in (
                    "top1_accuracy",
                    "mrr",
                    "recall_at_3",
                    "no_match_precision",
                    "no_match_recall",
                    "ece",
                    "mean_cost",
                )
            )
            + f" | {m['wrong_proposals']} / {m['proposal_count']} |"
        )
    lines += [
        "",
        "Top-1, MRR and Recall@3 use queries with a true match; NONE metrics use all queries. ECE uses ten equal-width bins for P(top-1 correct), including no-match negatives. Risk–coverage curves and customer-clustered 95% bootstrap intervals (300 resamples) are in `metrics.json`. No observed low error rate establishes production safety.",
        "",
        "## Candidate-set sizes",
        "",
        "| Model | Candidates | n | Top-1 | NONE recall | Cost/query |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        for size, m in result["by_candidate_set_size"].items():
            lines.append(
                f"| {name} | {size} | {m['n']} | {value(m['top1_accuracy'])} | {value(m['no_match_recall'])} | {value(m['mean_cost'])} |"
            )
    lines += [
        "",
        "## Limits and review",
        "",
        "- This is an offline synthetic comparison, not measured production improvement. Donor and fabricated no-match generation may introduce artifacts; deployment requires naturally written recollections.",
        "- Human gold recollections (60–100), independent NLU double-labeling, agreement statistics and fluent Portuguese review remain pending. Normalized slots cannot establish language fairness. Country and segment results are in metrics; cells below 30 are marked insufficient.",
        "- Complete feature definitions include status and weak channel match. Demographics, protected attributes, fraud labels and fraud scores are excluded. Country/segment are used for evaluation only; an explicitly mentioned transaction country is a matching feature.",
        "- There are no empty candidate sets in target-sampled benchmark queries; empty-set behavior is separately unit tested. Sparse large-candidate slices limit conclusions.",
        "- Twenty failures per model are categorized by a deterministic audit. Private per-query records permit later human review; no human failure review is claimed.",
        "- Synthetic FX and source records have documented anomalies. Policy and authorization must recheck the transaction before any action.",
        "",
        "## Reproduction and tracking",
        "",
        f"`uv run --extra data-ml python -m aclara.ml.charge_matcher.train --version {version} --trials 30` (use a new version for a new test touch). MLflow uses the local ignored file store in `lake/mlruns`; Optuna uses a seeded TPE sampler. Export contains numeric model parameters, calibrators, thresholds, feature order, metadata, metrics and checksums only. No pickled code or row records.",
        "",
        "Sources consulted: [dbt contracts](https://docs.getdbt.com/docs/mesh/govern/model-contracts), [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html), [LightGBM classifier](https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.LGBMClassifier.html), [Optuna study API](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.create_study.html).",
        "",
    ]
    path = ROOT / "docs/ml/model-card-charge-matcher.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def train(
    lake: Path,
    version: str,
    trials: int = 30,
    train_n: int = 6000,
    validation_n: int = 3000,
    test_n: int = 3000,
) -> dict[str, Any]:
    if not version or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        for char in version
    ):
        raise ValueError("version must be a simple artifact name")
    private = ROOT / "artifacts/charge_matcher" / version
    export = ROOT / "models/charge_matcher" / version
    if (private / "test_touch.json").exists() or (export / "metadata.json").exists():
        raise ValueError("version has already touched test; choose a new version and record why")
    private.mkdir(parents=True, exist_ok=True)
    marker = json.loads((lake / "_meta/current.json").read_text())
    datasets, fx, metadata = build_dataset(
        Path(marker["database"]),
        private / "dataset",
        train_n=train_n,
        validation_n=validation_n,
        test_n=test_n,
    )
    training = batch(datasets["train"], fx)
    partitions = {
        key: batch(
            [
                query
                for query in datasets["validation"]
                if validation_partition(query.customer_id) == key
            ],
            fx,
        )
        for key in ("tune", "calibration", "policy")
    }
    weights = np.asarray(
        [1 / max(1, end - start) for start, end in training.groups for _ in range(end - start)],
        dtype=np.float64,
    )
    os.environ["MLFLOW_ENABLE_ASYNC_LOGGING"] = "false"
    # MLflow 3.16 rejects a file-store run if an ancestor is literally named artifacts.
    # Both this store and row-level experiment files stay in ignored local directories.
    mlflow.set_tracking_uri((ROOT / "lake/mlruns").as_uri())
    mlflow.set_experiment("charge-matcher-local")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    metadata.update(
        version=version,
        git_sha=_pipeline_version(),
        features=list(FEATURES),
        trials=trials,
        validation_partition_counts={key: len(value.queries) for key, value in partitions.items()},
        training_code_sha256=hashlib.sha256(
            b"".join(path.read_bytes() for path in sorted(Path(__file__).parent.glob("*.py")))
        ).hexdigest(),
    )
    with mlflow.start_run(run_name=version) as run:
        mlflow.log_params(
            {
                "dataset_version": metadata["dataset_version"],
                "git_sha": metadata["git_sha"],
                "seed": SEED,
                "trials": trials,
                "noise_version": metadata["noise_version"],
                "feature_count": len(FEATURES),
            }
        )
        mlflow.log_dict({"features": list(FEATURES), "costs": COSTS}, "contracts.json")
        tune = partitions["tune"]

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
            match = exists_labels(tune).astype(bool)
            loss = float(1 - np.mean(labels[match]) + 0.1 * np.mean((scores - tune.y) ** 2))
            with mlflow.start_run(run_name=f"trial-{trial.number:02}", nested=True):
                mlflow.log_params(params)
                mlflow.log_metric("validation_ranking_objective", loss)
            return loss

        study = optuna.create_study(
            direction="minimize", sampler=optuna.samplers.TPESampler(seed=SEED)
        )
        study.optimize(objective, n_trials=trials)
        write_json(
            private / "optuna.json",
            {
                "best_params": study.best_params,
                "best_value": study.best_value,
                "trials": [
                    {"number": trial.number, "params": trial.params, "value": trial.value}
                    for trial in study.trials
                ],
            },
        )
        points = [
            Pointwise("rules", {}),
            Pointwise("logistic", fit_logistic(training.x, training.y, weights)),
            Pointwise(
                "lightgbm",
                study.best_params,
                _lightgbm(study.best_params).fit(training.x, training.y, sample_weight=weights),
            ),
        ]
        calibrated_models = {}
        policy_costs = {}
        for point in points:
            parameters, cost = calibrated(
                point, partitions["tune"], partitions["calibration"], partitions["policy"]
            )
            calibrated_models[point.name] = parameters
            policy_costs[point.name] = cost
        best = min(policy_costs.values())
        selected = next(
            name for name in ("rules", "logistic", "lightgbm") if policy_costs[name] <= best + 0.02
        )
        metadata.update(
            validation_policy_costs=policy_costs,
            selected_on_validation=selected,
            mlflow_run_id=run.info.run_id,
        )
        write_json(private / "selection.json", metadata)
        # Reserve the touch BEFORE computing any test predictions. A failed run is still a touch.
        touch = {
            "version": version,
            "dataset_version": metadata["dataset_version"],
            "at": datetime.now(UTC).isoformat(),
            "systems": [point.name for point in points],
            "selected": selected,
        }
        with (private / "test_touch.json").open("x") as stream:
            json.dump(touch, stream, indent=2)
        test = batch(datasets["test"], fx)
        results = {}
        export.mkdir(parents=True, exist_ok=True)
        for point in points:
            params = calibrated_models[point.name]
            scores = point.score(test.x)
            meta = query_features(scores, test.x, test.groups)
            p_top = interpolate(logistic(meta, params["top_model"]), params["top_calibration"])
            p_exists = interpolate(
                logistic(meta, params["exists_model"]), params["exists_calibration"]
            )
            rows = summarize_queries(
                test.queries, scores, test.groups, p_top, p_exists, params["thresholds"]
            )
            results[point.name] = report(rows)
            results[point.name]["thresholds"] = params["thresholds"]
            with (private / f"{point.name}-predictions.jsonl").open("w") as stream:
                for row in rows:
                    stream.write(json.dumps(row) + "\n")
            for metric, value in results[point.name]["overall"].items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(f"{point.name}_{metric}", float(value))
            if point.name == selected:
                write_json(export / "model.json", params)
                if point.name == "lightgbm":
                    point.fitted.booster_.save_model(str(export / "lightgbm.txt"))
                loaded = Matcher(export)
                if not np.allclose(loaded.scores(test.x), scores, rtol=1e-10, atol=1e-10):
                    raise RuntimeError("export score parity failed")
                for index, query in enumerate(test.queries[:100]):
                    start, end = test.groups[index]
                    decision = loaded.decide(
                        tuple(row.transaction_id for row in query.candidates), test.x[start:end]
                    )
                    if decision.action != rows[index]["action"] or not np.isclose(
                        decision.top_correct_probability, p_top[index]
                    ):
                        raise RuntimeError("export decision parity failed")
        recommendation = selected
        if results["lightgbm"]["overall"]["mean_cost"] >= results["rules"]["overall"]["mean_cost"]:
            recommendation = "rules" if selected == "lightgbm" else selected
        metadata.update(
            recommendation=recommendation,
            test_touch=touch,
            artifact_policy="numeric parameters and aggregates only; no row data",
            export_parity_verified=True,
        )
        write_json(export / "metrics.json", results)
        write_json(export / "metadata.json", metadata)
        write_json(
            export / "checksums.json",
            {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(export.iterdir())
                if path.is_file() and path.name != "checksums.json"
            },
        )
        mlflow.log_dict(metadata, "metadata.json")
        mlflow.log_dict(results, "metrics.json")
        _card(version, metadata, results, selected, recommendation)
        LOGGER.info(
            "Matcher complete; selected=%s; recommendation=%s; test=%s",
            selected,
            recommendation,
            json.dumps(
                {name: result["overall"] for name, result in results.items()}, sort_keys=True
            ),
        )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--train-n", type=int, default=6000)
    parser.add_argument("--validation-n", type=int, default=3000)
    parser.add_argument("--test-n", type=int, default=3000)
    args = parser.parse_args()
    values = dotenv_values(ROOT / ".env")
    lake = Path(os.environ.get("LAKE_DIR") or values.get("LAKE_DIR") or ROOT / "lake")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    train(lake, args.version, args.trials, args.train_n, args.validation_n, args.test_n)


if __name__ == "__main__":
    main()
