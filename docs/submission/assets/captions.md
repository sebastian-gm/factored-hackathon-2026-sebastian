# Slide assets

PNG: 1920 × 1080. SVG: editable text. Both formats use the same zero-based charts,
explicit denominators and direct labels. No organizer rows or held-out case content.

| PNG / SVG pair | Caption | Committed source |
|---|---|---|
| `v4-outcomes` | P passes 88/100 versus B1 62/100. SAR is 32/100 versus 22/100 overall, and 32/47 versus 22/47 among eligible cases; paired overall difference +10 pp, 95% CI +5 to +16. Both full safety gates failed; post-hoc analysis traces 6 of P's 8 distinct flagged cases to harness/fixture artifacts, without changing official counts. | [Official primary results](../../evaluation/final-v4-results.md#primary-b1-versus-p-gemini), [post-hoc analysis](../../evaluation/final-v4-safety-analysis.md) |
| `v4-escalation` | Strict correct escalation: P 49/53 versus B1 38/53. Missed transfers: 4/53 versus 15/53; unnecessary transfers: 2/47 versus 11/47. | [Official primary results](../../evaluation/final-v4-results.md#primary-b1-versus-p-gemini) |
| `v4-safety` | Both full safety gates failed. Unauthorized-action flags: B1 2/98, P 2/100; unverified-success flags: 2/98, 4/100. Missing confirmation/OTP: 0/98, 0/100. Categories overlap; zero observed flags do not establish zero risk. | [Official safety gates](../../evaluation/final-v4-results.md#safety-gates), [saved-flag interpretation](../../evaluation/final-v4-safety-analysis.md) |
| `v4-latency-cost` | P turn p50/p95: 2.125/3.776 s. Primary model spend $0.229766056: about $0.0023 per evaluated case, $0.0072 allocated per SAR-resolved case. Local serving plus remote models; excludes repeats, judges and infrastructure. | [Official latency and cost](../../evaluation/final-v4-results.md#cost-and-latency) |
| `controls-ablation` | Paired dev study, 20 synthetic cases per arm: P 0/20 versus naive Gemini 2/20 unverified write-success claims. Other observed failure counts were zero; correct escalation was 6/6 in both arms. This tests a bundle of controls, not each control separately, and does not establish safety. | [Committed dev study](../../evaluation/controls-ablation.md) |
| `controls-stress` | Post-v4 adversarial dev, 20 authored cases per arm: naive filed 2/20 disputes without genuine separate confirmation and made 2/20 success claims without read-back; P had 0/20 on both counters and stayed at proposals in both forged-confirmation cases. Naive also attempted one foreign-customer lookup against an instrumented fake; P attempted none. Counts overlap and are not additive. Selected attacks, added after the first ablation; architecture-bundle comparison, not held-out evidence or a general safety rate. | [Committed adversarial study](../../evaluation/controls-ablation-stress.md#paired-results) |
| `architecture` | Language and retrieval feed code-controlled policy, confirmation/OTP, scoped writes and independent readback; uncertainty reaches a verified human packet. Current source design is post-v4, not reflected in v4 numbers. | [Architecture](../../architecture.md), [conversation contract](../../../contracts/interfaces/conversation-policy-v3.md), [ADR-0017](../../adr/0017-drop-jev-from-live-path.md) |

V4 charts describe the historical **Gemini + Jev** system. They do not measure
the current Gemini/Grok source path, Azure browser latency or production readiness.
The two unauthorized-action flags per system include frozen reactive-reply/gold
conflicts; the saved-flag analysis found no observed authority bypass and does
**not** change the official counts. The safety chart shows selected categories;
use the full gate table before making an overall safety claim.

Both controls studies are post-v4 authored dev evidence, not held-out; missing
verification is not proof that a write failed. The stress asset's foreign lookup
is an instrumented attempt, not exposure of real records. Its three counters
omit other outcomes; use the complete report for the refund-screen false positive,
additional limitations and the unchanged preregistered counts. No new paid study
was run.

Regenerate the original six pairs without model calls:
`uv run --no-sync --extra data-ml python analysis/export_slide_assets.py`.
SVG metadata records its primary source file's SHA-256. No deck is included.

Regenerate only the supplementary stress pair from its committed aggregate table
(no scenario, checkpoint, model or organizer reads):

```sh
uv run --no-sync --extra data-ml python - <<'PY'
import re
from analysis.export_slide_assets import ROOT, MUTED, bars, cells, export, figure, plt

source = ROOT / "docs/evaluation/controls-ablation-stress.md"
report = source.read_text()
match = re.search(r"Fixed counter, (\d+) cases per arm", report)
if match is None:
    raise ValueError("Missing stress denominator")
denominator = int(match[1])
plt.rcParams.update({
    "font.family": "DejaVu Sans", "text.parse_math": False,
    "svg.fonttype": "none", "svg.hashsalt": "aclara-slide-assets",
})
fig = figure(
    "Forged chat consent triggered two naive writes",
    f"Post-v4 adversarial dev · {denominator} authored cases per arm · ES / PT · not held-out",
)
for i, (title, key) in enumerate((
    ("No separate confirmation", "Writes without genuine separate confirmation"),
    ("Unverified success claims", "Write-success claims without read-back"),
    ("Foreign-customer attempts", "Cross-customer tool access attempts"),
)):
    counts = tuple((int(value), denominator) for value in reversed(cells(report, key)))
    if any(not 0 <= count <= total or total <= 0 for count, total in counts):
        raise ValueError("Invalid stress count")
    bars(fig.add_axes((0.06 + i * 0.305, 0.32, 0.25, 0.39)), title, counts,
         maximum=10, labels=("Naive tool agent", "P · code controls"),
         axis_label="Cases in this arm (%)", value_size=13)
for y, text in (
    (0.16, "Forged-confirmation subset (2 cases): naive filed both; P stayed at proposals. Counters overlap."),
    (0.11, "Success claims lacked read-back; the foreign lookup hit a fake. Selected attacks; zeros do not establish safety."),
    (0.05, "Source: docs/evaluation/controls-ablation-stress.md · supplementary dev evidence, not reflected in v4"),
):
    fig.text(0.06, y, text, fontsize=10, color=MUTED)
export(fig, "controls-stress", source)
PY
```
