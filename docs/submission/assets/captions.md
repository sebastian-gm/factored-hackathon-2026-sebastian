# Slide assets

PNG: 1920 × 1080. SVG: editable text. Both formats use the same zero-based charts,
explicit denominators and direct labels. No organizer rows or held-out case content.

| PNG / SVG pair | Caption | Committed source |
|---|---|---|
| `v4-outcomes` | Aclara passes 88/100 versus the rules-only baseline 62/100. Resolved safely without a human: 32/100 versus 22/100 overall, and 32/47 versus 22/47 among eligible cases; paired overall difference +10 pp, 95% CI +5 to +16. Both systems failed the full safety checks; later analysis traces 6 of Aclara's 8 distinct flagged cases to harness/fixture artifacts, without changing official counts. | [Official primary results](../../evaluation/final-v4-results.md#primary-b1-versus-p-gemini), [post-hoc analysis](../../evaluation/final-v4-safety-analysis.md) |
| `v4-escalation` | Complete, correct and verified human transfers: Aclara 49/53 versus the rules-only baseline 38/53. Missed transfers: 4/53 versus 15/53; unnecessary transfers: 2/47 versus 11/47. | [Official primary results](../../evaluation/final-v4-results.md#primary-b1-versus-p-gemini) |
| `v4-safety` | Both systems failed the full safety checks. Unauthorized-action flags: rules-only baseline 2/98, Aclara 2/100; unverified-success flags: 2/98, 4/100. Missing confirmation/OTP: 0/98, 0/100. Categories overlap; zero observed flags do not establish zero risk. | [Official safety gates](../../evaluation/final-v4-results.md#safety-gates), [saved-flag interpretation](../../evaluation/final-v4-safety-analysis.md) |
| `v4-latency-cost` | Aclara response time p50/p95: 2.125/3.776 s. Primary model spend $0.229766056: about $0.0023 per evaluated case, $0.0072 allocated per case resolved safely without a human. Local serving plus remote models; excludes repeats, judges and infrastructure. | [Official latency and cost](../../evaluation/final-v4-results.md#cost-and-latency) |
| `controls-ablation` | Development study measured after the final evaluation, 20 synthetic cases per system, the same Gemini model in both: Aclara 0/20 versus a plain AI agent (no controls) 2/20 unverified write-success claims. Other observed failure counts were zero; correct escalation was 6/6 in both arms. This tests a bundle of controls, not each control separately, and does not establish safety. | [Committed dev study](../../history/evaluation/controls-ablation.md) |
| `controls-stress` | Adversarial development study measured after the final evaluation, 20 authored cases per system: the plain AI agent (no controls) filed 2/20 disputes without genuine separate confirmation and made 2/20 success claims without read-back; Aclara had 0/20 on both counters and stayed at proposals in both forged-confirmation cases. The plain AI agent also attempted one foreign-customer lookup against an instrumented fake; Aclara attempted none. Counts overlap and are not additive. Selected attacks, added after the first ablation; architecture-bundle comparison, not held-out evidence or a general safety rate. | [Committed adversarial study](../../history/evaluation/controls-ablation-stress.md#paired-results) |
| `architecture` | Language and retrieval feed code-controlled policy, confirmation/OTP, scoped writes and independent readback; uncertainty reaches a verified human packet. Current design was updated after the final evaluation; changes are not reflected in v4 numbers. | [Architecture](../../architecture.md), [conversation contract](../../../contracts/interfaces/conversation-policy-v3.md), [Decision record](../../adr/0017-drop-jev-from-live-path.md) |

Each chart has one short footer; the linked sources and these captions carry the methods and caveats.
A safe resolution is an explanation or verified case intake, not a refund. Human transfers count only when the packet, reasons, route and verification are all correct; presence alone is insufficient.

The cost chart allocates the same $0.229766056 model spend across 100 cases or 32 safe resolutions. The rules-only baseline's $0 is model cost, not zero operating cost. No Azure browser timing is claimed.

The architecture shows the current language/search → code policy → confirmation plus fresh simulated SMS code → independent verification → human handoff flow. Data preparation uses bronze/silver/gold contracts and tests; operational writes are idempotent and the audit is append-only. Details and the live Gemini/Grok path are in the linked architecture and decision record.

V4 charts describe the historical **Gemini + Jev** system. They do not measure
the current Gemini/Grok source path, Azure browser latency or production readiness.
The two unauthorized-action flags per system include frozen reactive-reply/gold
conflicts; the saved-flag analysis found no observed authority bypass and does
**not** change the official counts. The safety chart shows selected categories;
use the full gate table before making an overall safety claim.

Both controls studies were measured after the final evaluation on authored development data, not on unseen evaluation cases; missing
verification is not proof that a write failed. The stress asset's foreign lookup
is an instrumented attempt, not exposure of real records. Its three counters
omit other outcomes; use the complete report for the refund-screen false positive,
additional limitations and the unchanged preregistered counts. No new paid study
was run.

The stress chart's first panel isolates the **two forged-confirmation cases**:
the plain AI agent filed **2 of 2**, Aclara **0 of 2** (both stayed at proposals). Its count axis
runs from 0 to 2. The other panels use the **full 0–20 case scale**: the plain AI agent made
2 of 20 unverified success claims and 1 of 20 foreign-customer attempts; Aclara had
0 of 20 on both. These subset/arm denominators are distinct, and the caption's
overall 2/20 unconfirmed-write count remains unchanged.

Regenerate the original six pairs without model calls:
`uv run --no-sync --extra data-ml python analysis/export_slide_assets.py`.
SVG metadata records its primary source file's SHA-256. No deck is included.

Regenerate only the supplementary stress pair from its committed aggregate table
(no scenario, checkpoint, model or organizer reads):

```sh
uv run --no-sync --extra data-ml python - <<'PY'
import re
from analysis.export_slide_assets import ROOT, INK, MUTED, ACCENT, BASELINE, cells, export, figure, plt

source = ROOT / "docs/history/evaluation/controls-ablation-stress.md"
report = source.read_text()
match = re.search(r"Fixed counter, (\d+) cases per arm", report)
if match is None:
    raise ValueError("Missing stress denominator")
denominator = int(match[1])
subset_match = re.search(r"forged chat confirmation\s+(\d+)", report)
if subset_match is None:
    raise ValueError("Missing forged-confirmation subset denominator")
subset = int(subset_match[1])
plt.rcParams.update({
    "font.family": "DejaVu Sans", "text.parse_math": False,
    "svg.fonttype": "none", "svg.hashsalt": "aclara-slide-assets",
})
fig = figure(
    "Plain AI filed both; Aclara stayed at proposals",
    f"Development study after the final evaluation · {denominator} cases per system · ES / PT",
)
for i, (title, key, total) in enumerate((
    ("Forged-confirmation subset", "Writes without genuine separate confirmation", subset),
    ("Unverified success claims", "Write-success claims without read-back", denominator),
    ("Foreign-customer attempts", "Cross-customer tool access attempts", denominator),
)):
    counts = tuple(int(value) for value in reversed(cells(report, key)))
    if total <= 0 or any(not 0 <= count <= total for count in counts):
        raise ValueError("Invalid stress count")
    if i == 0 and (subset != 2 or counts != (2, 0)):
        raise ValueError("Forged subset facts changed; recheck the written report")
    ax = fig.add_axes((0.06 + i * 0.305, 0.32, 0.25, 0.39))
    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=20, color=INK)
    for y, count, color, label in zip(
        (1, 0), counts, (BASELINE, ACCENT), ("Plain AI agent", "Aclara"), strict=True
    ):
        ax.barh(y, count, height=0.28, color=color)
        if count == 0:
            ax.plot(0, y, "o", color=color, markersize=5, clip_on=False)
        ax.text(0, y + 0.25, label, fontsize=10, color=MUTED)
        ax.text(total, y + 0.25, f"{count} of {total}", ha="right", fontsize=12, color=INK)
    ax.set_xlim(0, total)
    ax.set_ylim(-0.45, 1.65)
    ax.set_yticks([])
    ticks = [0, 1, 2] if i == 0 else [0, 5, 10, 15, 20]
    ax.set_xticks(ticks, [str(value) for value in ticks])
    ax.tick_params(axis="x", colors=MUTED, labelsize=10, length=0, pad=8)
    ax.set_xlabel("Filed cases · 2-case subset" if i == 0 else "Cases · 20-case arm",
                  fontsize=10, color=MUTED, labelpad=10)
    for name, spine in ax.spines.items():
        spine.set_visible(name == "bottom")
        spine.set_color("#dce3de")
        if name == "bottom":
            spine.set_bounds(0, total)
fig.text(0.06, 0.07,
         "Selected synthetic attacks; the foreign lookup hit a fake. Zeros do not establish safety.",
         fontsize=10, color=MUTED)
export(fig, "controls-stress", source)
PY
```
