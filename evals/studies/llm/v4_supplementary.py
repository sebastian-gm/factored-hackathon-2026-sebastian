"""Read-only confidence/outcome proxies and paired family bootstrap; no inference."""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from hashlib import sha256
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SEED, DRAWS = 20261001, 10000
MODEL = "google/gemini-3-flash-preview"


def reliability(observations: Sequence[tuple[float, bool]], bins: int = 10) -> dict[str, Any]:
    """Equal-width ECE; the caller must identify what the binary label measures."""
    if bins < 1:
        raise ValueError("Positive bin count required")
    groups: dict[int, list[tuple[float, bool]]] = defaultdict(list)
    for score, correct in observations:
        if not math.isfinite(score) or not 0 <= score <= 1 or type(correct) is not bool:
            raise ValueError("Finite probability and boolean correctness required")
        groups[min(int(score * bins), bins - 1)].append((score, correct))
    populated = []
    for index, values in sorted(groups.items()):
        mean_confidence = sum(score for score, _ in values) / len(values)
        accuracy = sum(correct for _, correct in values) / len(values)
        populated.append(
            {
                "lower": index / bins,
                "upper": (index + 1) / bins,
                "n": len(values),
                "correct": sum(correct for _, correct in values),
                "mean_confidence": mean_confidence,
                "accuracy": accuracy,
            }
        )
    n = len(observations)
    return {
        "n": n,
        "correct": sum(correct for _, correct in observations),
        "mean_confidence": sum(score for score, _ in observations) / n if n else None,
        "accuracy": sum(correct for _, correct in observations) / n if n else None,
        "ece": sum(g["n"] * abs(g["mean_confidence"] - g["accuracy"]) for g in populated) / n
        if n
        else None,
        "bins": bins,
        "populated_bins": populated,
    }


def paired_interval(
    differences: Sequence[int],
    families: Sequence[str] | None = None,
    *,
    draws: int = DRAWS,
    seed: int = SEED,
) -> dict[str, Any]:
    """Sample complete paired clusters; retain a case-weighted ratio estimand."""
    if not differences or draws < 1 or any(d not in {-1, 0, 1} for d in differences):
        raise ValueError("Nonempty paired binary differences and positive draws required")
    if families is not None and len(families) != len(differences):
        raise ValueError("One family per case required")
    grouped: dict[str, list[int]] = defaultdict(list)
    for i, diff in enumerate(differences):
        grouped[str(i) if families is None else families[i]].append(diff)
    keys = sorted(grouped)
    sums = np.array([sum(grouped[key]) for key in keys], dtype=float)
    sizes = np.array([len(grouped[key]) for key in keys], dtype=int)
    # Preserve original case order for an exact reproduction of official SAR.
    if families is None:
        sums = np.asarray(differences, dtype=float)
    indices = np.random.default_rng(seed).integers(0, len(keys), (draws, len(keys)))
    sampled = sums[indices].sum(axis=1) / sizes[indices].sum(axis=1)
    return {
        "n": len(differences),
        "clusters": len(keys),
        "difference": sum(differences) / len(differences),
        "paired_95": np.quantile(sampled, [0.025, 0.975]).tolist(),
        "draws": draws,
        "seed": seed,
    }


def _paired_primary(rows: Iterable[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    by_system: dict[str, dict[str, dict]] = {"B1": {}, "P": {}}
    for row in rows:
        if row.get("system") not in by_system or row.get("repeat") != 0:
            continue
        cases = by_system[row["system"]]
        if row["id"] in cases:
            raise ValueError("Duplicate primary execution; attempts and results cannot both count")
        cases[row["id"]] = row
    if not by_system["P"] or by_system["B1"].keys() != by_system["P"].keys():
        raise ValueError("Complete paired primary workload required")
    ids = sorted(by_system["P"])
    b, p = ([by_system[name][key] for key in ids] for name in ("B1", "P"))
    if not all(row["in_scope"] for row in [*b, *p]):
        raise ValueError("This analysis requires the all-in-scope v4 denominator")
    return b, p


def summarize(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    b, p = _paired_primary(rows)
    families = [row["gold"]["written_rule_basis"] for row in p]
    if any(not isinstance(key, str) or not key.strip() for key in families):
        raise ValueError("Saved predeclared contract rationale required for family proxy")
    members: dict[str, list[dict]] = defaultdict(list)
    for family, row in zip(families, p, strict=True):
        members[family].append(row)
    if any(
        len({(r["category"], r["gold"]["outcome"]) for r in group}) != 1
        for group in members.values()
    ):
        raise ValueError("Contract family proxy mixes category or expected outcome")
    comparisons = {}
    for metric in ("sar", "passed"):
        differences = [
            int(right[metric]) - int(left[metric]) for left, right in zip(b, p, strict=True)
        ]
        comparisons[metric] = {
            "b1_successes": sum(row[metric] for row in b),
            "p_successes": sum(row[metric] for row in p),
            "case_bootstrap": paired_interval(differences),
            "family_proxy_bootstrap": paired_interval(differences, families),
            "p_wins": differences.count(1),
            "b1_wins": differences.count(-1),
        }
    first: list[tuple[float, bool]] = []
    all_turns: list[tuple[float, bool]] = []
    languages: dict[str, list[tuple[float, bool]]] = defaultdict(list)
    absent = []
    for row in p:
        scores = [
            float(event["judgments"]["gemini_intent_confidence"])
            for event in row["events"]
            if event.get("event") == "llm_call"
            and event.get("route") == "nlu_risk_second_opinion"
            and "gemini_intent_confidence" in (event.get("judgments") or {})
        ]
        if not scores:
            absent.append(row["passed"])
            continue
        first.append((scores[0], row["passed"]))
        languages[row["language"]].append((scores[0], row["passed"]))
        all_turns.extend((score, row["passed"]) for score in scores)
    thresholds = []
    for threshold in (0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99, 1.0):
        rejected = [passed for score, passed in first if score < threshold]
        thresholds.append(
            {
                "threshold": threshold,
                "first_cases_flagged": len(rejected),
                "failed_cases_flagged": sum(not passed for passed in rejected),
                "passing_cases_flagged": sum(rejected),
                "all_turn_scores_below": sum(score < threshold for score, _ in all_turns),
            }
        )
    return {
        "scope": "supplementary saved primary results; no rerun or rescore",
        "correctness_label": "official terminal case passed; NOT independent intent correctness",
        "true_intent_ece": None,
        "true_intent_ece_unavailable": "No independent per-turn intent gold in saved v4 artifacts",
        "family_key": "exact gold.written_rule_basis; contract-family proxy, not exported author ID",
        "families": {
            "n": len(members),
            "sizes": dict(sorted(Counter(len(group) for group in members.values()).items())),
            "languages": dict(
                sorted(
                    Counter(
                        "/".join(sorted(r["language"] for r in group)) for group in members.values()
                    ).items()
                )
            ),
        },
        "comparisons": comparisons,
        "confidence": {
            "first_per_case_outcome_proxy": reliability(first),
            "all_turns_outcome_proxy_sensitivity": reliability(all_turns),
            "first_per_language": {
                key: reliability(values) for key, values in sorted(languages.items())
            },
            "cases_without_score": {"n": len(absent), "passed": sum(absent)},
            "all_turn_min": min((score for score, _ in all_turns), default=None),
            "exact_score_groups": [
                {"score": score, "n": len(values), "passed": sum(values)}
                for score in sorted({score for score, _ in first})
                if (values := [passed for value, passed in first if value == score])
            ],
            "thresholds": thresholds,
        },
    }


def saved_report(source: Path) -> dict[str, Any]:
    fingerprints = []
    rows = []
    validated_nlu = 0
    for path in sorted((source / "checkpoints").glob("*/result.json")):
        raw = path.read_bytes()
        row = json.loads(raw)
        if row.get("system") not in {"B1", "P"} or row.get("repeat") != 0:
            continue
        fingerprints.append((str(path.relative_to(source)), sha256(raw).hexdigest()))
        if row["system"] == "P":
            call_path = path.with_name("calls-1.jsonl")
            calls = (
                [json.loads(line) for line in call_path.read_text().splitlines()]
                if call_path.exists()
                else []
            )
            nlu = [c for c in calls if c["call"]["route"] == "nlu"]
            scores = []
            for call in nlu:
                if call["call"]["status"] != "valid" or call["call"]["model_id"] != MODEL:
                    raise ValueError("Unexpected primary NLU attempt; do not silently discard it")
                scores.append(call["validated_output"]["intent_confidence"])
            risk_scores = [
                e["judgments"]["gemini_intent_confidence"]
                for e in row["events"]
                if e.get("route") == "nlu_risk_second_opinion"
            ]
            if scores != risk_scores:
                raise ValueError("Validated NLU scores disagree with saved risk-call metadata")
            validated_nlu += len(nlu)
            if call_path.exists():
                fingerprints.append(
                    (str(call_path.relative_to(source)), sha256(call_path.read_bytes()).hexdigest())
                )
        rows.append(row)
    result = summarize(rows)
    official_path = source / "results.json"
    official_raw = official_path.read_bytes()
    official = json.loads(official_raw)
    original = official["paired_comparison"]["primary_single_run"]
    reproduced = result["comparisons"]["sar"]["case_bootstrap"]
    if (
        original["difference"] != reproduced["difference"]
        or original["paired_95"] != reproduced["paired_95"]
    ):
        raise ValueError("Primary SAR does not exactly reproduce official stored estimate/CI")
    result["official_case_sar"] = original
    result["validated_primary_nlu_outputs"] = validated_nlu
    result["source_sha256"] = sha256(json.dumps(sorted(fingerprints)).encode()).hexdigest()
    result["source_files"] = len(fingerprints)
    result["official_results_sha256"] = sha256(official_raw).hexdigest()
    return result


def compact_svg(path: Path) -> None:
    """Compact parsed XML, preserving attribute separators and visible text."""
    tree = ElementTree.fromstring(path.read_bytes())  # noqa: S314 -- our generated plot, no untrusted XML.
    for node in tree.iter():
        if node.text is not None and not node.text.strip():
            node.text = None
        if node.tail is not None and not node.tail.strip():
            node.tail = None
    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
    ElementTree.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    path.write_bytes(ElementTree.tostring(tree, encoding="utf-8", xml_declaration=True))


def chart(result: dict[str, Any], path: Path) -> None:
    """Aggregate-only vector figure; optional local plotting dependency."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matplotlib.rcParams["svg.fonttype"] = "none"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), layout="constrained")
    ax = axes[0]
    ax.plot([0, 1], [0, 1], "--", color="#9aa3af", label="Equality reference")
    proxy = result["confidence"]["first_per_case_outcome_proxy"]
    for bucket in proxy["populated_bins"]:
        ax.scatter(bucket["mean_confidence"], bucket["accuracy"], s=75, color="#174b85")
        ax.annotate(
            f"n={bucket['n']}",
            (bucket["mean_confidence"], bucket["accuracy"]),
            xytext=(-42, -20),
            textcoords="offset points",
        )
    ax.set(
        xlim=(0, 1.03),
        ylim=(0, 1.03),
        xlabel="Raw intent confidence (bin mean)",
        ylabel="Official conversation pass rate",
        title=f"Outcome proxy only: ECE {proxy['ece']:.3f}",
    )
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax = axes[1]
    labels = []
    for index, metric in enumerate(("sar", "passed")):
        for offset, (key, label, color) in enumerate(
            (
                ("case_bootstrap", "Case", "#8a98aa"),
                ("family_proxy_bootstrap", "Contract-family proxy", "#174b85"),
            )
        ):
            value = result["comparisons"][metric][key]
            point = value["difference"] * 100
            low, high = (v * 100 for v in value["paired_95"])
            y = index * 3 + offset
            ax.errorbar(
                point, y, xerr=[[point - low], [high - point]], fmt="o", capsize=4, color=color
            )
            labels.append((y, f"{'SAR' if metric == 'sar' else 'Pass'} · {label}"))
    ax.axvline(0, color="#9aa3af", linestyle="--")
    ax.set(
        yticks=[y for y, _ in labels],
        yticklabels=[label for _, label in labels],
        xlabel="P − B1 (percentage points), percentile 95% CI",
        title="Paired primary workload; 100 cases",
    )
    ax.invert_yaxis()
    fig.savefig(path, format="svg", metadata={"Date": None})
    fig.savefig(path.with_suffix(".png"), dpi=150)
    plt.close(fig)
    compact_svg(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chart", action="store_true")
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Write private outputs only under ignored artifacts/")
    if args.output.resolve().is_relative_to(args.source.resolve()):
        raise ValueError("Never write into the official source artifact tree")
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    result = saved_report(args.source)
    output = args.output / "report.json"
    fd = os.open(output, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    if args.chart:
        chart(result, args.output / "v4-confidence-family-ci.svg")


if __name__ == "__main__":
    main()
