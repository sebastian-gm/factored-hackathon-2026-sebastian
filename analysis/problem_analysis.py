"""Read the promoted gold aggregate mart; regenerate shareable reports and figures."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import duckdb
from dotenv import dotenv_values

from aclara.data.reporting import generate_reports


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    settings = dotenv_values(root / ".env")
    lake = Path(
        os.getenv("LAKE_DIR")
        or str(settings.get("LAKE_DIR") or Path(tempfile.gettempdir()) / "aclara-shared-lake")
    )
    current = json.loads((lake / "_meta/current.json").read_text())
    with duckdb.connect(current["database"], read_only=True) as db:
        profile = {
            name: json.loads(value)
            for name, value in db.execute(
                "SELECT metric,value FROM gold.problem_analysis"
            ).fetchall()
        }
    generate_reports(profile, root / "docs")
    findings = ["", "## Interpretation of the measured results", ""]
    for reason in profile["contact_reasons"]:
        if reason["contact_reason"] == "Queja":
            findings.append(
                f"Complaints account for {reason['volume_share']:.1%} of contacts and {reason['handle_time_share']:.1%} of handle time, with FCR {reason['fcr']:.1%}. This supports prioritizing grounded charge explanations and dispute intake."
            )
    for threshold in profile["fraud_thresholds"]:
        findings += [
            "",
            f"At fraud-score > {threshold['threshold']}, the flag rate is {threshold['flagged'] / threshold['total']:.4%} over all transactions and {threshold['window_flagged'] / threshold['window_n']:.4%} in the serving window. The denominator includes null-score rows; this differs from a percentile over scored rows.",
        ]
    app = {row["is_error"]: row for row in profile["app_error_contact"]}
    if True in app and False in app:
        gap = 100 * (app[True]["contact_rate"] - app[False]["contact_rate"])
        findings += [
            "",
            f"App-error events were followed by contact at {app[True]['contact_rate']:.3%}, compared with {app[False]['contact_rate']:.3%} for other selected events: a {gap:.4f} percentage-point difference. This small descriptive gap does not support building error-triggered contact automation from this dataset.",
        ]
    for source, rows in profile["accent_test"].items():
        by_match = {row["accent_match"]: row for row in rows}
        if True in by_match and False in by_match:
            gap = 100 * (by_match[True]["fcr"] - by_match[False]["fcr"])
            findings += [
                "",
                f"The {source}-accent FCR difference (matched minus mismatched) is {gap:.3f} percentage points; this descriptive result provides no useful basis for accent routing.",
            ]
    with (root / "docs/problem-analysis.md").open("a") as stream:
        stream.write("\n".join(findings) + "\n")
    os.environ.setdefault("MPLCONFIGDIR", str(root / "artifacts/matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    rows = profile["contact_reasons"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout="constrained")
    for ax, key, label in zip(
        axes,
        ("volume_share", "fcr"),
        ("Contact volume share", "First-contact resolution"),
        strict=True,
    ):
        ax.barh([r["contact_reason"] for r in rows], [r[key] for r in rows], color="#276b91")
        ax.set_xlabel(label)
        ax.set_xlim(0, 1)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Synthetic historical operations — context only")
    out = root / "docs/data/contact-demand.svg"
    fig.savefig(out)
    out.write_text("\n".join(line.rstrip() for line in out.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    main()
