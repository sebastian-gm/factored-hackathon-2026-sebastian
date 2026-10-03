"""Slide PNG/SVG assets from committed aggregates only; no scenario/model reads."""

# ruff: noqa: T201 -- generated asset filenames only.
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "artifacts/slide-assets/mpl-cache"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

REPORT = ROOT / "docs/evaluation/final-v4-results.md"
OUT = ROOT / "docs/submission/assets"
INK, MUTED, ACCENT, BASELINE = "#20352f", "#52645d", "#176b56", "#73837b"
LABELS = ("Rules-only baseline", "Aclara")


def cells(report: str, label: str) -> tuple[str, str]:
    match = re.search(
        r"^\| " + re.escape(label) + r" \| ([^|]+)\| ([^|]+)\|$", report, re.MULTILINE
    )
    if match is None:
        raise ValueError("Missing committed result row: " + label)
    return match[1].strip(), match[2].strip()


def fractions(report: str, label: str) -> tuple[tuple[int, int], tuple[int, int]]:
    result = []
    for cell in cells(report, label):
        match = re.search(r"(\d+)/(\d+)", cell)
        if match is None:
            raise ValueError("Result needs an explicit denominator: " + label)
        result.append((int(match[1]), int(match[2])))
    return result[0], result[1]


def figure(title: str, subtitle: str) -> Figure:
    fig = plt.figure(figsize=(12, 6.75), facecolor="white")
    fig.text(0.06, 0.925, title, fontsize=24, fontweight="bold", color=INK)
    fig.text(0.06, 0.865, subtitle, fontsize=14, color=MUTED)
    return fig


def footer(fig: Figure, text: str) -> None:
    fig.text(0.06, 0.07, text, fontsize=10, color=MUTED)


def bars(
    ax: Axes,
    title: str,
    counts: tuple[tuple[int, int], tuple[int, int]],
    maximum: float = 100,
    labels: tuple[str, str] = LABELS,
    axis_label: str = "Share of stated denominator (%)",
    value_size: float = 14,
) -> None:
    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=20, color=INK)
    for y, (count, denominator), color, label in zip(
        (1, 0), counts, (BASELINE, ACCENT), labels, strict=True
    ):
        value = 100 * count / denominator
        ax.barh(y, value, height=0.28, color=color)
        if count == 0:
            ax.plot(0, y, "o", color=color, markersize=5, clip_on=False)
        ax.text(0, y + 0.25, label, fontsize=10, color=MUTED)
        ax.text(
            value + maximum * 0.025,
            y,
            f"{count}/{denominator} · {value:.1f}%",
            va="center",
            fontsize=value_size,
            color=INK,
        )
    ax.set_xlim(0, maximum * 1.45)
    ax.set_ylim(-0.45, 1.65)
    ax.set_yticks([])
    ax.set_xticks([0, maximum / 2, maximum], ["0%", f"{maximum / 2:g}%", f"{maximum:g}%"])
    ax.tick_params(axis="x", colors=MUTED, labelsize=10, length=0, pad=8)
    ax.set_xlabel(axis_label, fontsize=10, color=MUTED, labelpad=10)
    for name, spine in ax.spines.items():
        spine.set_visible(name == "bottom")
        spine.set_color("#dce3de")
        if name == "bottom":
            spine.set_bounds(0, maximum)


def export(fig: Figure, name: str, source: Path = REPORT) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUT / (name + ".png"),
        dpi=160,
        facecolor="white",
        metadata={"Software": "Aclara aggregate asset exporter"},
    )
    path = OUT / (name + ".svg")
    fig.savefig(
        path,
        metadata={
            "Date": None,
            "Creator": "Aclara",
            "Description": str(source.relative_to(ROOT))
            + " sha256:"
            + hashlib.sha256(source.read_bytes()).hexdigest(),
        },
    )
    # Retain editable SVG text and accessible title, without thousands of diff lines.
    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
    tree = ElementTree.fromstring(path.read_text())  # noqa: S314 -- locally generated SVG only.
    title = ElementTree.Element("{http://www.w3.org/2000/svg}title")
    title.text = name.replace("-", " ")
    tree.insert(0, title)
    path.write_text(ElementTree.tostring(tree, encoding="unicode") + "\n")
    plt.close(fig)
    print(name + ": PNG + SVG")


def outcomes(report: str) -> None:
    fig = figure(
        "More cases pass; more resolved safely without a human",
        "Final evaluation (v4) · same 100 cases for both systems",
    )
    for i, (title, key) in enumerate(
        (
            ("All requirements met", "Pass"),
            ("Resolved safely\nall cases", "SAR / in-scope (95% CI)"),
            ("Resolved safely\neligible cases", "SAR / automation-eligible"),
        )
    ):
        bars(fig.add_axes((0.06 + i * 0.305, 0.30, 0.25, 0.39)), title, fractions(report, key))
    interval = re.search(
        r"SAR difference is \+(\d+) percentage points,\s+95% interval \+(\d+) to \+(\d+)",
        report.replace("**", ""),
    )
    if interval is None:
        raise ValueError("Missing official paired SAR interval")
    footer(
        fig,
        f"Difference across all cases: +{interval[1]} pp (95% CI +{interval[2]} to +{interval[3]}). Both systems failed the safety checks.",
    )
    export(fig, "v4-outcomes")


def escalation(report: str) -> None:
    correct, total = fractions(report, "Strict escalation recall")[1]
    fig = figure(
        f"Correct human transfers: {correct} of {total} cases",
        "Final evaluation (v4) · complete, correct and verified transfers",
    )
    for i, (title, key) in enumerate(
        (
            ("Correct · higher is better", "Strict escalation recall"),
            ("Missed · lower is better", "Missed transfers"),
            ("Unnecessary · lower is better", "Unnecessary transfers"),
        )
    ):
        bars(fig.add_axes((0.06 + i * 0.305, 0.30, 0.25, 0.39)), title, fractions(report, key))
    footer(
        fig,
        "53 cases required a human; 47 allowed automation. Details and limits are in the captions.",
    )
    export(fig, "v4-escalation")


def safety(report: str) -> None:
    fig = figure(
        "Both systems failed the safety checks",
        "Final evaluation (v4) · recorded flags · lower is better",
    )
    for i, (title, key) in enumerate(
        (
            ("Unauthorized action flags", "Unauthorized action"),
            ("Unverified success", "Reported without verification"),
            ("Missing consent or code", "Missing confirmation or step-up"),
        )
    ):
        bars(
            fig.add_axes((0.06 + i * 0.305, 0.32, 0.25, 0.37)),
            title,
            fractions(report, key),
            maximum=5,
        )
    footer(
        fig,
        "Flags overlap. Zero flags do not prove zero risk; see the captions for their interpretation.",
    )
    export(fig, "v4-safety")


def latency_cost(report: str) -> None:
    fig = figure(
        "Response times and model costs",
        "Final evaluation (v4) · local server, remote models",
    )
    ax = fig.add_axes((0.06, 0.32, 0.42, 0.39))
    ax.set_title("Response time · seconds", fontsize=14, fontweight="bold", loc="left", color=INK)
    for i, cell in enumerate(cells(report, "Turn p50 / p95")):
        numbers = re.findall(r"\d+\.\d+", cell)
        for j, value in enumerate(map(float, numbers)):
            y = 3 - 2 * i - j
            ax.barh(y, value, height=0.38, color=(BASELINE, ACCENT)[i])
            ax.text(
                value + 0.1,
                y,
                f"{LABELS[i]} · p{(50, 95)[j]} · {value:.3f} s",
                va="center",
                fontsize=10,
                color=INK,
            )
    ax.set_xlim(0, 7.1)
    ax.set_yticks([])
    ax.set_xticks([0, 2, 4], ["0", "2", "4"])
    ax.set_xlabel("Seconds per reply", fontsize=10, color=MUTED)
    ax.tick_params(length=0, labelsize=10, colors=MUTED)
    for name, spine in ax.spines.items():
        spine.set_visible(name == "bottom")
        spine.set_color("#dce3de")
        if name == "bottom":
            spine.set_bounds(0, 4)
    for y, title, row, denominator in (
        (
            0.60,
            "Model cost per case",
            "Cost / evaluated workload case",
            fractions(report, "Pass")[1][1],
        ),
        (
            0.36,
            "Cost per safe resolution",
            "Allocated primary cost / SAR-resolved case",
            fractions(report, "SAR / in-scope (95% CI)")[1][0],
        ),
    ):
        cell = cells(report, row)[1]
        value = float(re.search(r"\$([\d.]+)", cell)[1])
        fig.text(0.58, y + 0.08, title, fontsize=14, color=MUTED)
        fig.text(0.58, y, f"${value:.4f}", fontsize=24, fontweight="bold", color=ACCENT)
        fig.text(
            0.58,
            y - 0.06,
            f"Aclara model spend divided by {denominator} cases",
            fontsize=10,
            color=MUTED,
        )
    footer(
        fig,
        "Model cost excludes infrastructure, repeats and judges. Rules-only baseline model cost: $0.",
    )
    export(fig, "v4-latency-cost")


def architecture() -> None:
    source = ROOT / "docs/architecture.md"
    fig = figure(
        "AI understands. Code controls actions.",
        "Current design · updated after the final evaluation; v4 scores unchanged",
    )
    ax = fig.add_axes((0.055, 0.21, 0.89, 0.60))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis("off")

    def block(
        x: float, y: float, width: float, title: str, detail: str, accent: bool = False
    ) -> None:
        ax.add_patch(Rectangle((x, y), width, 13, facecolor="#f3f6f4", edgecolor="none"))
        ax.text(
            x + width / 2,
            y + 8,
            title,
            ha="center",
            fontsize=14,
            fontweight="bold",
            color=ACCENT if accent else INK,
        )
        ax.text(x + width / 2, y + 3, detail, ha="center", fontsize=10, color=MUTED)

    def arrow(start: tuple[float, float], end: tuple[float, float]) -> None:
        ax.add_patch(
            FancyArrowPatch(
                start, end, arrowstyle="-|>", mutation_scale=12, color="#778a81", linewidth=1
            )
        )

    block(0, 51, 28, "Customer · ES / PT", "Chat in your language")
    block(34, 51, 32, "Verified access", "Signed-in customer workspace")
    block(72, 51, 28, "Language + charge search", "Find your own transactions", True)
    arrow((28, 57), (34, 57))
    arrow((66, 57), (72, 57))
    for i, (title, detail) in enumerate(
        (
            ("Understand", "Customer facts"),
            ("Decide", "Rules in code"),
            ("Act", "Confirm + new SMS code"),
            ("Verify", "Verified receipt"),
            ("Escalate", "Human with context"),
        )
    ):
        block(i * 20.5, 24, 18, title, detail)
        if i < 3:
            arrow((i * 20.5 + 18, 30), ((i + 1) * 20.5, 30))
    ax.plot([85, 85, 9], [51, 43, 43], color="#778a81", linewidth=1)
    arrow((9, 43), (9, 37))
    # Escalation is an alternative/recovery path, not mandatory after every write.
    ax.plot([29, 29, 90], [24, 19, 19], color="#778a81", linewidth=1)
    ax.plot([72, 72], [24, 19], color="#778a81", linewidth=1)
    arrow((90, 19), (90, 24))
    block(
        12,
        0,
        76,
        "Checked bank records",
        "Own transactions · saved actions · recorded checks",
    )
    arrow((9, 24), (22, 13))
    arrow((50, 24), (50, 13))
    arrow((70, 13), (70, 24))
    footer(fig, "Actions are verified before success is reported. Uncertainty reaches a human.")
    export(fig, "architecture", source)


def controls_ablation() -> None:
    source = ROOT / "docs/evaluation/controls-ablation.md"
    report = source.read_text()
    fig = figure(
        "Plain AI claimed two filings without verification",
        "Development study after the final evaluation · 20 synthetic cases per system",
    )
    for i, (title, key) in enumerate(
        (
            ("Actions outside the rules", "Unauthorized/ineligible writes"),
            ("Without confirmation", "Writes without explicit confirmation"),
            ("Unverified success", "Write-success claims without read-back"),
            ("Refund promises", "Promised refunds"),
            ("Other-customer attempts", "Cross-customer tool access attempts"),
            ("Correct human transfers", "Correct escalations, six eligible cases"),
        )
    ):
        counts = []
        # This committed table orders P then naive; the chart orders naive then P.
        for cell in reversed(cells(report, key)):
            match = re.fullmatch(r"(\d+)(?:/(\d+))?", cell)
            if match is None:
                raise ValueError("Missing explicit ablation count: " + key)
            count, denominator = int(match[1]), int(match[2] or 20)
            if not 0 <= count <= denominator or denominator <= 0:
                raise ValueError("Invalid ablation denominator: " + key)
            counts.append((count, denominator))
        bars(
            fig.add_axes((0.06 + (i % 3) * 0.305, 0.56 - (i // 3) * 0.33, 0.25, 0.17)),
            title,
            (counts[0], counts[1]),
            labels=("Plain AI agent", "Aclara"),
            axis_label="Cases (%)",
            value_size=12,
        )
    footer(
        fig,
        "Unverified does not mean failed. Small synthetic study; zeros do not establish safety.",
    )
    export(fig, "controls-ablation", source)


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "text.parse_math": False,
            "svg.fonttype": "none",
            "svg.hashsalt": "aclara-slide-assets",
        }
    )
    report = REPORT.read_text()
    for render in (outcomes, escalation, safety, latency_cost):
        render(report)
    architecture()
    controls_ablation()


if __name__ == "__main__":
    main()
