"""TypeSafe Jev adapter for typed judgments; never used for prose or slot extraction."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from typesafe_sdk import Choice, Noul, Score, SystemOneResponse, TypeSafeClient

MODEL_ID = "jev-1.13.0"
INPUT_USD_PER_MILLION = 0.042
Question = Choice | Noul | Score


@dataclass(frozen=True, slots=True)
class ChoiceJudgment:
    choice: str
    probabilities: dict[str, float]
    confidence: float


@dataclass(frozen=True, slots=True)
class ScoreJudgment:
    score: float  # Zero-based probability-weighted position, not an integer rubric level.
    probabilities: dict[int, float]
    confidence: float


@dataclass(frozen=True, slots=True)
class TypedJudgments:
    model_id: str
    choices: dict[str, ChoiceJudgment]
    nouls: dict[str, float]
    scores: dict[str, ScoreJudgment]
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: float
    cost_usd: float | None


def _probability(value: float) -> float:
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("TypeSafe returned an invalid probability")
    return value


def _normalize(response: SystemOneResponse, latency_ms: float) -> TypedJudgments:
    if response.model != MODEL_ID:
        raise ValueError("TypeSafe served a different model than the pinned Jev version")
    choices: dict[str, ChoiceJudgment] = {}
    for name, choice_answer in response.choices.items():
        choice_probs = {
            key: _probability(float(value)) for key, value in choice_answer.probabilities.items()
        }
        if choice_answer.choice not in choice_probs or abs(sum(choice_probs.values()) - 1) > 0.02:
            raise ValueError("TypeSafe Choice distribution is invalid")
        choices[name] = ChoiceJudgment(
            choice=choice_answer.choice,
            probabilities=choice_probs,
            confidence=_probability(float(choice_answer.confidence)),
        )
    nouls = {name: _probability(float(answer.noul)) for name, answer in response.nouls.items()}
    scores: dict[str, ScoreJudgment] = {}
    for name, score_answer in response.scores.items():
        score_probs = {
            int(key): _probability(float(value))
            for key, value in score_answer.probabilities.items()
        }
        if not score_probs or abs(sum(score_probs.values()) - 1) > 0.02:
            raise ValueError("TypeSafe Score distribution is invalid")
        score = float(score_answer.score)
        if not math.isfinite(score) or not min(score_probs) <= score <= max(score_probs):
            raise ValueError("TypeSafe Score is outside its levels")
        scores[name] = ScoreJudgment(
            score=score,
            probabilities=score_probs,
            confidence=_probability(float(score_answer.confidence)),
        )
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    if input_tokens is not None and input_tokens < 0:
        raise ValueError("TypeSafe input-token usage is invalid")
    if output_tokens is not None and output_tokens < 0:
        raise ValueError("TypeSafe output-token usage is invalid")
    return TypedJudgments(
        model_id=response.model,
        choices=choices,
        nouls=nouls,
        scores=scores,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        cost_usd=input_tokens * INPUT_USD_PER_MILLION / 1_000_000
        if input_tokens is not None
        else None,
    )


class TypeSafeAdapter:
    """One System One call can answer independent Choice/Noul/Score questions."""

    def __init__(self, client: TypeSafeClient) -> None:
        self.client = client

    def ask(self, state: dict[str, Any], questions: Mapping[str, Question]) -> TypedJudgments:
        if not questions or any(
            not isinstance(q, (Choice, Noul, Score)) for q in questions.values()
        ):
            raise ValueError("TypeSafe adapter accepts typed judgment questions only")
        started = perf_counter()
        response = self.client.system_one(state=state, questions=questions, model=MODEL_ID)
        return _normalize(response, (perf_counter() - started) * 1000)
