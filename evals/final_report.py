"""Aggregate final artifacts: objective protocol metrics, variability and dual judges."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from evals.checkpoints import atomic_write, save
from evals.heldout_report import DRAWS, SEED, comparison, report
from evals.metrics import aggregate, proportion
from evals.studies.llm.dual_judge import agreement_report
from evals.studies.llm.judge_validation import quadratic_weighted_kappa


def mean_interval(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mean": None, "case_bootstrap_95": None}
    rng = np.random.default_rng(SEED)
    data = np.asarray(values)
    samples = data[rng.integers(0, len(data), (DRAWS, len(data)))].mean(axis=1)
    return {
        "n": len(values),
        "mean": float(data.mean()),
        "case_bootstrap_95": np.quantile(samples, [0.025, 0.975]).tolist(),
    }


def enrich(metrics: dict, cases: list[dict]) -> dict:
    metrics["flagged_intakes_rate"] = proportion(metrics["flagged_intakes"], len(cases))
    for key in ("handoff_completeness", "handoff_rubric"):
        values = (
            [c["completeness"] for c in cases if c["completeness"] is not None]
            if key == "handoff_completeness"
            else [
                sum(c["handoff_rubric"].values()) / len(c["handoff_rubric"])
                for c in cases
                if c["handoff_rubric"]
            ]
        )
        metrics[key].update(mean_interval(values))
    metrics["cost"]["per_case_interval"] = mean_interval([c["cost_usd"] for c in cases])
    # Jointly resample numerator and SAR denominator; undefined draws stay visible.
    rng = np.random.default_rng(SEED)
    draws = (
        rng.integers(0, len(cases), (DRAWS, len(cases))) if cases else np.empty((0, 0), dtype=int)
    )
    costs = np.asarray([c["cost_usd"] for c in cases])
    successes = np.asarray([int(c["sar"]) for c in cases])
    denominators = successes[draws].sum(axis=1)
    valid = denominators > 0
    ratios = costs[draws].sum(axis=1)[valid] / denominators[valid]
    metrics["cost"]["per_sar_bootstrap_95"] = (
        np.quantile(ratios, [0.025, 0.975]).tolist() if len(ratios) else None
    )
    metrics["cost"]["undefined_sar_draws"] = int((~valid).sum())
    metrics["cost"]["unknown_cost_attempts"] = sum(c.get("unknown_cost_attempts", 0) for c in cases)
    metrics["cost"]["recovered_case_attempts"] = sum(c.get("recovered_attempts", 0) for c in cases)
    metrics["cost"]["note"] = (
        "Known billed/modelled call costs; unknown reserves and interrupted exposure are in durable_budget. Not defined when SAR is zero."
    )
    metrics["components_note"] = (
        "Trace component times sum calls, including parallel Jev work; they are not additive wall-clock latency."
    )
    return metrics


def judge_report(ratings: list[dict], planned: dict | None = None) -> dict:
    planned = planned if planned is not None else {"calibration": 50, "frozen": 100}
    out = {}
    for cohort in ("calibration", "frozen"):
        rows = [r for r in ratings if r["cohort"] == cohort]
        pairs = [r for r in rows if r.get("sonnet_scores") and r.get("jev_scores")]
        left = {r["sample_id"]: r["sonnet_scores"] for r in pairs}
        right = {r["sample_id"]: r["jev_scores"] for r in pairs}
        values = agreement_report(left, right)["jev_vs_sonnet"]
        for dimension, item in values.items():
            scores = [
                (r["sonnet_scores"][dimension], r["jev_scores"][dimension])
                for r in pairs
                if r["sonnet_scores"][dimension] is not None
                and r["jev_scores"][dimension] is not None
            ]
            item["exact_interval"] = proportion(sum(a == b for a, b in scores), len(scores))
            item["within_one_interval"] = proportion(
                sum(abs(a - b) <= 1 for a, b in scores), len(scores)
            )
            for vendor in ("sonnet", "jev"):
                item[vendor + "_mean"] = mean_interval(
                    [
                        r[vendor + "_scores"][dimension]
                        for r in pairs
                        if r[vendor + "_scores"][dimension] is not None
                    ]
                )
            rng = np.random.default_rng(SEED)
            kappas = []
            if scores:
                for indices in rng.integers(0, len(scores), (DRAWS, len(scores))):
                    kappa = quadratic_weighted_kappa([scores[i] for i in indices])
                    if kappa is not None:
                        kappas.append(kappa)
            item["kappa_bootstrap_95"] = (
                np.quantile(kappas, [0.025, 0.975]).tolist() if kappas else None
            )
        out[cohort] = {
            "planned": planned[cohort],
            "attempted": len(rows),
            "paired": len(pairs),
            "unpaired": len(rows) - len(pairs),
            "failed": sum(r.get("status") == "judge_failed" for r in rows),
            "dimensions": values,
        }
    out["human_validation"] = {
        "status": "pending",
        "sheet": "human-judge-20.csv",
        "note": "20-item owner review is separate from the uncompleted 50-item calibration. No human agreement claim.",
    }
    return out


def flatten(value: object, prefix: str = "") -> list[tuple[str, str]]:
    if isinstance(value, dict):
        return [
            item
            for key, child in value.items()
            for item in flatten(child, f"{prefix}.{key}" if prefix else key)
        ]
    return [(prefix, json.dumps(value, ensure_ascii=False).replace("|", "\\|"))]


def write_report(
    output: Path,
    cases: list[dict],
    ratings: list[dict],
    repeat_ids: set[str],
    header: dict,
    budget: dict,
) -> dict:
    b1 = [c for c in cases if c["system"] == "B1"]
    p = [c for c in cases if c["system"] == "P" and c["repeat"] == 0]
    repeats = [c for c in cases if c["system"] == "P" and c["repeat"] > 0]
    systems = {}
    for name, rows in [
        ("B1", b1),
        (header.get("p_system_label", "P-Gemini"), p),
        ("P-Sonnet", [c for c in cases if c["system"] == "P-Sonnet"]),
    ]:
        if name == "P-Sonnet" and not rows:
            continue
        metrics = enrich(report(rows, {**header, "system": name}), rows)
        for field in ("language", "dialect", "country", "segment"):
            for label, subset in metrics["slices"][field].items():
                selected = [c for c in rows if c[field] == label]
                all_metrics = enrich(
                    aggregate(selected, {"bootstrap_draws": DRAWS, "bootstrap_seed": SEED}),
                    selected,
                )
                all_metrics.pop("header")
                metrics["slices"][field][label] = {**all_metrics, **subset}
        systems[name] = metrics
    paired = comparison(b1, p, repeats, repeat_ids)
    paired["interpretation"] = (
        "Fixed paired workload; P majority success/outcome on preselected repeats. Safety gates and uncertainty must be read alongside differences."
    )
    result = {
        "header": {**header, "sample_size": len(b1), "case_runs": len(cases)},
        "systems": systems,
        "paired_comparison": paired,
        "judges": judge_report(ratings, header.get("judge_planned")),
        "durable_budget": budget,
        "limitations": [
            "No fluent-human Portuguese review; model-generated dialect wording.",
            "Human judge calibration is pending; the 20-item sheet is not completed review.",
            "Frozen suite has outcome/action gold, not independently labelled NLU slots or matcher rankings; those metrics remain in the separate dev/matcher reports.",
            "Interrupted attempts are retained and billed within the same cap; final latency describes completed executions.",
            "Organizer serving ledger with explicit counterfactual overlays; operational state is isolated per case.",
        ],
    }
    save(output / "results.json", result)
    sections = [
        "# Final evaluation results",
        "",
        f"**Workload:** {header['workload']}. **Sample size:** {len(b1)} independent scenarios; {len(cases)} case-runs.",
        "",
        f"**Model:** {header['model']}. **Release SHA:** `{header['implementation_sha']}`.",
        "",
        "**Prompt hashes:** " + json.dumps(header["prompt_versions"]) + ".",
        "",
        "**Cost assumptions:** " + header["cost_assumptions"] + ".",
        "",
        "**Price-table dates:** " + json.dumps(header["price_table_dates"]) + ".",
        "",
        "Proportions use Wilson 95% intervals; latency, means and paired differences use case-clustered bootstrap (10,000 draws). Small cells (n < 30) are insufficient samples. Containment alone is not success.",
        "",
        "0 observed in n cases does not establish zero risk; the 95% upper bound is 3/n.",
        "",
        "Monthly infrastructure estimate is separate: $"
        + str(header["monthly_infrastructure_estimate_usd"])
        + " before tax.",
        "",
    ]
    if header.get("preflight_disclosure"):
        sections.extend(["**Preflight recovery:** " + header["preflight_disclosure"], ""])
    for name, value in result.items():
        if name == "header":
            continue
        sections.extend(
            ["## " + name.replace("_", " ").title(), "", "| Metric | Value |", "| --- | --- |"]
        )
        sections.extend(
            f"| {key} | {val} |" for key, val in flatten(value) if ".header." not in key
        )
        sections.append("")
    atomic_write(output / "results.md", "\n".join(sections))
    return result
