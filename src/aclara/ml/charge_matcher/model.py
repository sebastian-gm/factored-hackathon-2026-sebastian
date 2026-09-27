"""Portable matcher artifacts: numeric parameters only, no pickle or source records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from aclara.ml.charge_matcher.features import FEATURES, rules_score
from aclara.ml.charge_matcher.types import Decision

Array = NDArray[np.float64]


def logistic(matrix: Array, parameters: dict[str, Any]) -> Array:
    standardized = (matrix - np.asarray(parameters["mean"])) / np.asarray(parameters["scale"])
    logits = np.clip(
        standardized @ np.asarray(parameters["coefficients"]) + float(parameters["intercept"]),
        -40,
        40,
    )
    return np.asarray(1 / (1 + np.exp(-logits)), dtype=np.float64)


def interpolate(values: Array, calibration: dict[str, Any]) -> Array:
    return np.asarray(np.interp(values, calibration["x"], calibration["y"]), dtype=np.float64)


def query_features(scores: Array, matrix: Array, groups: list[tuple[int, int]]) -> Array:
    result: list[list[float]] = []
    for start, end in groups:
        if start == end:
            result.append([0, 0, 0, 0])
            continue
        values = np.sort(scores[start:end])[::-1]
        result.append(
            [
                float(values[0]),
                float(values[0] - values[1]) if len(values) > 1 else float(values[0]),
                float(np.log1p(end - start)),
                float(matrix[start, -1]),
            ]
        )
    return np.asarray(result, dtype=np.float64)


def decisions(
    top_probability: Array, exists_probability: Array, thresholds: dict[str, float]
) -> list[str]:
    return [
        "none"
        if exists < thresholds["none"]
        else "propose"
        if top >= thresholds["auto"]
        else "choose"
        if top >= thresholds["choice"]
        else "none"
        for top, exists in zip(top_probability, exists_probability, strict=True)
    ]


class Matcher:
    def __init__(self, artifact: Path) -> None:
        self.parameters: dict[str, Any] = json.loads((artifact / "model.json").read_text())
        if self.parameters["features"] != list(FEATURES):
            raise ValueError("matcher feature contract changed")
        self.booster: Any = None
        if self.parameters["model"] == "lightgbm":
            from lightgbm import Booster

            self.booster = Booster(model_file=str(artifact / "lightgbm.txt"))

    def scores(self, matrix: Array) -> Array:
        kind = self.parameters["model"]
        if kind == "rules":
            return np.asarray([rules_score(row.tolist()) for row in matrix], dtype=np.float64)
        if kind == "logistic":
            return logistic(matrix, self.parameters["pointwise"])
        if kind == "lightgbm":
            return np.asarray(self.booster.predict(matrix, num_threads=1), dtype=np.float64)
        raise ValueError("unknown pointwise model")

    def decide(self, transaction_ids: tuple[str, ...], matrix: Array) -> Decision:
        if len(transaction_ids) != len(matrix):
            raise ValueError("candidate matrix size mismatch")
        if not transaction_ids:
            return Decision("none", (), 0.0, 0.0)
        scores = self.scores(matrix)
        meta = query_features(scores, matrix, [(0, len(matrix))])
        top = float(
            interpolate(
                logistic(meta, self.parameters["top_model"]), self.parameters["top_calibration"]
            )[0]
        )
        exists = float(
            interpolate(
                logistic(meta, self.parameters["exists_model"]),
                self.parameters["exists_calibration"],
            )[0]
        )
        action = decisions(np.asarray([top]), np.asarray([exists]), self.parameters["thresholds"])[
            0
        ]
        order = np.argsort(-scores, kind="stable")
        chosen = (
            tuple(transaction_ids[int(index)] for index in order[: 1 if action == "propose" else 3])
            if action != "none"
            else ()
        )
        return Decision(action, chosen, top, exists)
