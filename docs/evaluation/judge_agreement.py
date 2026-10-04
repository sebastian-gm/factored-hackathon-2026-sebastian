"""Offline aggregates for the 20-item human review; no provider calls or raw output.

Run from the repository root with ``python -m docs.evaluation.judge_agreement``.
The existing importer validates IDs, original wording, complete ratings and N/A.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from evals.studies.llm.human_review import (
    DIMENSIONS,
    import_ratings,
    private_output,
    rating,
    read_sheet,
)


def average_ranks(values: list[int]) -> list[float]:
    """One-based ranks, assigning the mean rank to ties."""
    ordered = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        for index in ordered[start:end]:
            ranks[index] = (start + 1 + end) / 2
        start = end
    return ranks


def spearman(pairs: list[tuple[int, int]]) -> float | None:
    """Pearson correlation of average ranks; constant/empty vectors are undefined."""
    if not pairs:
        return None
    left = average_ranks([a for a, _ in pairs])
    right = average_ranks([b for _, b in pairs])
    left_mean, right_mean = sum(left) / len(left), sum(right) / len(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True))
    denominator = math.sqrt(
        sum((a - left_mean) ** 2 for a in left) * sum((b - right_mean) ** 2 for b in right)
    )
    return numerator / denominator if denominator else None


def aggregate(scored: Path, source: Path, inputs: Path, checkpoints: Path) -> dict[str, Any]:
    """Supplement validated agreement with rank correlation and gap direction."""
    result = import_ratings(scored, source, inputs, checkpoints)
    humans = {row["sample_id"]: row for row in read_sheet(scored)}
    judges = {}
    for path in checkpoints.glob("*/result.json"):
        saved = json.loads(path.read_text())
        if "sonnet_scores" in saved:
            judges[saved["sample_id"]] = saved
    for comparison, left, right in (
        ("human_vs_sonnet", "human", "sonnet"),
        ("human_vs_jev", "human", "jev"),
        ("sonnet_vs_jev", "sonnet", "jev"),
    ):
        for language in ("all", "es", "pt"):
            for dimension in DIMENSIONS:
                pairs = []
                for sample_id, human in humans.items():
                    if language != "all" and not human["target_locale"].startswith(language):
                        continue
                    if dimension == "handoff_usefulness" and not human["handoff_summary"].strip():
                        continue
                    saved = judges.get(sample_id, {})
                    scores = {"human": rating(human["human_" + dimension])}
                    for model in ("sonnet", "jev"):
                        model_scores = saved.get(model + "_scores")
                        scores[model] = (
                            rating(model_scores.get(dimension)) if model_scores else None
                        )
                    a, b = scores[left], scores[right]
                    if a is not None and b is not None:
                        pairs.append((a, b))
                metrics = result["comparisons"][comparison][language][dimension]
                if metrics["paired_n"] != len(pairs):
                    raise ValueError("Supplement differs from the validated pairing")
                metrics.update(
                    spearman=spearman(pairs),
                    right_higher_by_more_than_one_n=sum(b - a > 1 for a, b in pairs),
                    right_lower_by_more_than_one_n=sum(a - b > 1 for a, b in pairs),
                )
    return result


def self_check() -> None:
    """Known ordinal examples, tie handling and undefined correlations."""
    assert average_ranks([3, 1, 3, 5]) == [2.5, 1.0, 2.5, 4.0]
    assert spearman([]) is None
    assert spearman([(3, 1), (3, 5)]) is None
    assert spearman([(1, 3), (5, 3)]) is None
    assert spearman([(1, 1), (3, 3), (3, 3), (5, 5)]) == 1
    assert spearman([(1, 5), (3, 3), (5, 1)]) == -1
    assert math.isclose(spearman([(1, 1), (1, 2), (3, 3)]) or 0, math.sqrt(3) / 2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scored", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--judge-inputs", type=Path)
    parser.add_argument("--checkpoints", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/human-judge/v4-agreement.json")
    )
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return
    if not all((args.scored, args.source, args.judge_inputs, args.checkpoints)):
        parser.error("All four private input paths are required")
    result = aggregate(args.scored, args.source, args.judge_inputs, args.checkpoints)
    private_output(args.output)
    with args.output.open("w", encoding="utf-8") as stream:
        args.output.chmod(0o600)
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    # Read back before announcing success; no source rows or individual scores.
    if json.loads(args.output.read_text()) != result:
        raise ValueError("Aggregate receipt read-back failed")
    print(json.dumps(result, indent=2, allow_nan=False))  # noqa: T201 -- aggregates only


if __name__ == "__main__":
    main()
