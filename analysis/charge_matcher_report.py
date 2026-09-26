"""Review frozen predictions; no refitting, retuning or additional test inference."""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    export = root / "models/charge_matcher" / args.version
    metrics = json.loads((export / "metrics.json").read_text())
    prediction_dir = root / "artifacts/charge_matcher" / args.version
    predictions = {
        name: [
            json.loads(line)
            for line in (prediction_dir / f"{name}-predictions.jsonl").read_text().splitlines()
        ]
        for name in metrics
    }
    assert len({tuple(row["query_id"] for row in rows) for rows in predictions.values()}) == 1
    groups: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(predictions["rules"]):
        groups[row["customer_id"]].append(index)
    indices = list(groups.values())
    rng = np.random.default_rng(20260926)
    comparisons = {}
    for name in ("logistic", "lightgbm"):
        delta = np.asarray(
            [
                p["cost"] - b["cost"]
                for p, b in zip(predictions[name], predictions["rules"], strict=True)
            ]
        )
        samples = []
        for _ in range(1000):
            sample = [
                index
                for cluster in rng.integers(0, len(indices), len(indices))
                for index in indices[int(cluster)]
            ]
            samples.append(float(np.mean(delta[sample])))
        comparisons[name] = {
            "cost_difference_vs_rules": float(np.mean(delta)),
            "customer_clustered_95_ci": np.quantile(samples, [0.025, 0.975]).tolist(),
            "resamples": 1000,
        }
    docs = root / "docs/ml"
    (docs / "paired-comparison.json").write_text(
        json.dumps(comparisons, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# Frozen matcher result review",
        "",
        "This review reuses the one-time v1 predictions; there is no refitting or additional test inference.",
        "",
        "## Selection and uncertainty",
        "",
        "LightGBM was selected on validation before opening test. Test logistic regression has lower mean cost and better calibration, while LightGBM makes fewer wrong proposals. The held-out result does not change thresholds or the selected artifact. A future independent workload should revisit this trade-off.",
        "",
        "| Model | Cost difference vs rules | Customer-clustered 95% interval |",
        "|---|---:|---|",
    ]
    for name, value in comparisons.items():
        lines.append(
            f"| {name} | {value['cost_difference_vs_rules']:.4f} | {value['customer_clustered_95_ci']} |"
        )
    lines += [
        "",
        "The lower-is-better cost combines explicitly chosen synthetic error costs; this interval is not a guarantee of production safety.",
        "",
        "## Slice review",
        "",
        "| Model | Slice | Group | n | Top-1 | Cost |",
        "|---|---|---|---:|---:|---:|",
    ]
    for name, result in metrics.items():
        for field in ("by_country", "by_segment"):
            for group, m in result[field].items():
                lines.append(
                    f"| {name} | {field} | {group} | {m['n']} | {m['top1_accuracy']:.4f} | {m['mean_cost']:.4f} |"
                )
    lines += [
        "",
        "These groups describe source customer attributes, not language performance. Candidate-set size, query family and source composition can differ by group; gaps are observational. Protected attributes never enter the feature vector.",
        "",
        "## Known synthetic artifacts",
        "",
        "As-of clocks are zero to ten days after the target business date. This makes recency predictive by construction and can overstate improvement on a real workload. Customers without a target transaction are not sampled, so the target-sampled candidate distribution is larger than the all-customer serving distribution. No-match donor/fabrication and held-out stress profiles can shift confidence; LightGBM’s NONE precision and ECE warrant particular caution.",
        "",
        "## Human validation plan",
        "",
        "Sebastian has 40 private Spanish cards from customers excluded from every synthetic benchmark split. Recollections are blank and human validation is pending. Portuguese recollections will be labeled model-generated and cross-checked by a second model vendor, after the relevant model access/cost approval. No Portuguese performance or human labeling agreement is claimed.",
        "",
    ]
    (docs / "result-review.md").write_text("\n".join(lines))
    os.environ.setdefault("MPLCONFIGDIR", str(root / "artifacts/matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout="constrained")
    colors = {"rules": "#59646d", "logistic": "#277c8e", "lightgbm": "#b35322"}
    for name, result in metrics.items():
        curve = [row for row in result["risk_coverage"] if row["risk"] is not None]
        axes[0].plot(
            [r["coverage"] for r in curve],
            [r["risk"] for r in curve],
            marker="o",
            label=name,
            color=colors[name],
        )
        bins = ["1", "2-3", "4-8", "9+"]
        axes[1].plot(
            bins,
            [result["by_candidate_set_size"][size]["top1_accuracy"] for size in bins],
            marker="o",
            label=name,
            color=colors[name],
        )
    axes[0].set(
        xlabel="Coverage by top-correct confidence",
        ylabel="Wrong top-1 share",
        title="Risk–coverage (confidence only)",
    )
    axes[1].set(
        xlabel="Candidate count",
        ylabel="Top-1 accuracy on match queries",
        ylim=(0.7, 1.01),
        title="Ranking by candidate-set size",
    )
    for ax in axes:
        ax.legend()
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Offline synthetic benchmark — 3,000 held-out queries")
    out = docs / "charge-matcher-comparison.svg"
    fig.savefig(out)
    out.write_text("\n".join(line.rstrip() for line in out.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    main()
