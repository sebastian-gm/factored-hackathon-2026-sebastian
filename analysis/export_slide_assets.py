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
LABELS = ("B1", "P · Gemini + Jev")


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
    fig.text(0.06, 0.09, text, fontsize=10, color=MUTED)
    fig.text(
        0.06,
        0.05,
        "Source: docs/evaluation/final-v4-results.md · official v4, first pass only",
        fontsize=10,
        color=MUTED,
    )


def bars(
    ax: Axes, title: str, counts: tuple[tuple[int, int], tuple[int, int]], maximum: float = 100
) -> None:
    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=20, color=INK)
    for y, (count, denominator), color, label in zip(
        (1, 0), counts, (BASELINE, ACCENT), LABELS, strict=True
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
            fontsize=14,
            color=INK,
        )
    ax.set_xlim(0, maximum * 1.45)
    ax.set_ylim(-0.45, 1.65)
    ax.set_yticks([])
    ax.set_xticks([0, maximum / 2, maximum], ["0%", f"{maximum / 2:g}%", f"{maximum:g}%"])
    ax.tick_params(axis="x", colors=MUTED, labelsize=10, length=0, pad=8)
    ax.set_xlabel("Share of stated denominator (%)", fontsize=10, color=MUTED, labelpad=10)
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
        "More cases pass, with more safe automation",
        "Official v4 · B1 vs P-Gemini with Jev · same 100-case workload",
    )
    for i, (title, key) in enumerate(
        (
            ("Conversation pass", "Pass"),
            ("SAR · all in-scope cases", "SAR / in-scope (95% CI)"),
            ("SAR · eligible cases", "SAR / automation-eligible"),
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
        f"Paired in-scope SAR difference: +{interval[1]} pp (95% CI +{interval[2]} to +{interval[3]}). Both full safety gates failed.",
    )
    export(fig, "v4-outcomes")


def escalation(report: str) -> None:
    correct, total = fractions(report, "Strict escalation recall")[1]
    fig = figure(
        f"Correct escalation reaches {correct} of {total} cases",
        "Strict escalation requires the correct packet, reasons, route and readback",
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
        "53 cases required a human; 47 were automation eligible. Handoff presence alone is insufficient.",
    )
    export(fig, "v4-escalation")


def safety(report: str) -> None:
    fig = figure(
        "Both systems failed the full safety gate",
        "Official observed flags · lower is better · categories overlap",
    )
    for i, (title, key) in enumerate(
        (
            ("Unauthorized action", "Unauthorized action"),
            ("Unverified success claim", "Reported without verification"),
            ("Missing confirmation / OTP", "Missing confirmation or step-up"),
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
        "Action flags include frozen-reply/gold conflicts, with no observed authority bypass. Zero flags do not prove zero risk.",
    )
    export(fig, "v4-safety")


def latency_cost(report: str) -> None:
    fig = figure(
        "Measured latency and model cost stay visible",
        "Historical v4 · local serving plus remote models · includes Jev, excludes Azure browser timing",
    )
    ax = fig.add_axes((0.06, 0.32, 0.42, 0.39))
    ax.set_title("Turn latency · seconds", fontsize=14, fontweight="bold", loc="left", color=INK)
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
    ax.set_xlabel("Seconds per turn", fontsize=10, color=MUTED)
    ax.tick_params(length=0, labelsize=10, colors=MUTED)
    for name, spine in ax.spines.items():
        spine.set_visible(name == "bottom")
        spine.set_color("#dce3de")
        if name == "bottom":
            spine.set_bounds(0, 4)
    for y, title, row, denominator in (
        (
            0.60,
            "Model cost per evaluated case",
            "Cost / evaluated workload case",
            fractions(report, "Pass")[1][1],
        ),
        (
            0.36,
            "Allocated cost per safe resolution",
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
            f"P primary model spend allocated across {denominator} cases",
            fontsize=10,
            color=MUTED,
        )
    primary_cost = cells(report, "Primary-pass known model cost")[1]
    footer(
        fig,
        f"P primary model cost {primary_cost}. Excludes repeats, judges and infrastructure; B1 model cost $0.",
    )
    export(fig, "v4-latency-cost")


def architecture() -> None:
    source = ROOT / "docs/architecture.md"
    fig = figure(
        "LLM for language. Code for authority.",
        "Current source design · post-v4 changes are not reflected in v4 scores",
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

    block(0, 51, 28, "Customer · ES / PT", "Chat + same-origin Next.js BFF")
    block(34, 51, 32, "Authentication + scope", "FastAPI · session + trusted role")
    block(72, 51, 28, "Language + retrieval", "Gemini / Grok fallback · matcher v2", True)
    arrow((28, 57), (34, 57))
    arrow((66, 57), (72, 57))
    for i, (title, detail) in enumerate(
        (
            ("Understand", "Slots + scoped facts"),
            ("Decide", "Rules in code"),
            ("Act", "Confirm + fresh OTP"),
            ("Verify", "Independent readback"),
            ("Escalate", "Verified human packet"),
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
        "Postgres · forced scope / RLS",
        "Serving gold + operational writes + append-only audit",
    )
    arrow((9, 24), (22, 13))
    arrow((50, 24), (50, 13))
    arrow((70, 13), (70, 24))
    fig.text(
        0.06,
        0.09,
        "Local data → bronze hashes → contracted silver → tested dbt gold. Writes are idempotent; uncertain results reach a human.",
        fontsize=10,
        color=MUTED,
    )
    fig.text(
        0.06,
        0.05,
        "Sources: docs/architecture.md · contracts/interfaces/conversation-policy-v3.md · docs/adr/0017-drop-jev-from-live-path.md",
        fontsize=10,
        color=MUTED,
    )
    export(fig, "architecture", source)


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


if __name__ == "__main__":
    main()
