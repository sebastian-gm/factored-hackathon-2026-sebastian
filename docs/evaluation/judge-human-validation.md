# Human review of final evaluation (v4) wording

**What this shows:** How closely two AI judges scored the same replies as Sebastian.
**Result:** All 20 blind items were scored and matched; the judges often rated wording more generously.
**Limits:** One reviewer and 20 replies describe this sample; they do not validate either judge.

Sebastian's scored export was received on October 3, 2026. We compared it with
saved Sonnet and Jev scores for the **unchanged final evaluation (v4) replies**.
There were no new model calls and no changes to the official outcome results.
Agreement was measured after the final evaluation.

The importer confirmed all original IDs, locales and wording, and all **70/70**
applicable human ratings. Every sheet item has both saved judges. The sample
contains **11 ES, 3 PT, 3 mixed and 3 other-language replies**. Ten replies have
handoff summaries; the other ten are excluded from that dimension.

## Agreement with Sebastian

Exact means the same 1–5 score. Within one means the scores differ by at most one
point. Weighted κ adjusts agreement for chance; Spearman ρ compares score order.
Neither statistic measures whether an action was safe or correct.

| AI judge vs human | Dimension | Paired n | Exact | Within one | Weighted κ | Spearman ρ |
|---|---|---:|---:|---:|---:|---:|
| Sonnet | Language and tone | 20 | 55.0% | 90.0% | 0.062 | 0.092 |
| Sonnet | Clarity | 20 | 50.0% | 85.0% | 0.451 | 0.605 |
| Sonnet | Empathy | 20 | 35.0% | 100.0% | -0.083 | -0.124 |
| Sonnet | Handoff usefulness | 10 | 0.0% | 100.0% | 0.000 | Undefined |
| Jev | Language and tone | 20 | 35.0% | 100.0% | 0.188 | 0.309 |
| Jev | Clarity | 20 | 40.0% | 75.0% | 0.196 | 0.399 |
| Jev | Empathy | 20 | 50.0% | 95.0% | -0.083 | -0.092 |
| Jev | Handoff usefulness | 10 | 0.0% | 90.0% | 0.000 | Undefined |

The largest differences concern clarity. Sonnet scored it over one point higher
than Sebastian in **3/20** replies; Jev did so in **5/20**. Both judges agreed
with the human on **0/10** handoff scores, even though Sonnet was within one
point on all ten. A high within-one percentage alone can hide a consistent
scoring difference. Empathy κ is negative for both judges in the overall sample.

All gaps larger than one point favored the AI judge's score. Sonnet also had
**2/20** larger language-and-tone gaps; Jev had **1/20** for empathy and **1/10**
for handoff usefulness. None of these larger gaps occurred in PT.

Private review found that the larger clarity gaps concentrate on short replies
about routing or transfer. All five Jev clarity gaps were ES replies with a
handoff summary; four mentioned transfer to a person. Human notes were blank
on every larger-gap item, so these are observed contexts, not an explanation
of Sebastian's reasons. Short, orderly transfer wording may receive generous
AI scores while still leaving a human reader wanting more detail.

<details>
<summary>Language slices, method and private reproduction</summary>

## ES and PT slices

Mixed and other-language items count in the overall table but not these slices.
The PT results cover only three replies and two handoffs; even a 100% entry is
not evidence of reliable Portuguese scoring.

| Language | AI judge vs human | Dimension | Paired n | Exact | Within one | Weighted κ | Spearman ρ |
|---|---|---|---:|---:|---:|---:|---:|
| ES | Sonnet | Language and tone | 11 | 72.7% | 90.9% | 0.154 | 0.221 |
| ES | Sonnet | Clarity | 11 | 45.5% | 81.8% | 0.500 | 0.712 |
| ES | Sonnet | Empathy | 11 | 36.4% | 100.0% | -0.116 | -0.153 |
| ES | Sonnet | Handoff usefulness | 7 | 0.0% | 100.0% | 0.000 | Undefined |
| PT | Sonnet | Language and tone | 3 | 0.0% | 100.0% | 0.000 | Undefined |
| PT | Sonnet | Clarity | 3 | 66.7% | 100.0% | 0.000 | Undefined |
| PT | Sonnet | Empathy | 3 | 33.3% | 100.0% | 0.000 | Undefined |
| PT | Sonnet | Handoff usefulness | 2 | 0.0% | 100.0% | 0.000 | Undefined |
| ES | Jev | Language and tone | 11 | 45.5% | 100.0% | 0.327 | 0.516 |
| ES | Jev | Clarity | 11 | 27.3% | 54.5% | 0.158 | 0.388 |
| ES | Jev | Empathy | 11 | 45.5% | 90.9% | 0.000 | 0.000 |
| ES | Jev | Handoff usefulness | 7 | 0.0% | 85.7% | 0.000 | Undefined |
| PT | Jev | Language and tone | 3 | 0.0% | 100.0% | 0.000 | Undefined |
| PT | Jev | Clarity | 3 | 100.0% | 100.0% | 1.000 | 1.000 |
| PT | Jev | Empathy | 3 | 100.0% | 100.0% | 1.000 | 1.000 |
| PT | Jev | Handoff usefulness | 2 | 0.0% | 100.0% | 0.000 | Undefined |

## Saved judge-to-judge comparison

These unchanged figures compare the two AI judges on the same 20 sheet items.
They cannot substitute for a human comparison.

| Sonnet vs Jev dimension | Paired n | Exact | Within one | Weighted κ | Spearman ρ |
|---|---:|---:|---:|---:|---:|
| Language and tone | 20 | 50.0% | 100.0% | 0.174 | 0.181 |
| Clarity | 20 | 60.0% | 90.0% | 0.364 | 0.411 |
| Empathy | 20 | 30.0% | 100.0% | 0.200 | 0.303 |
| Handoff usefulness | 10 | 90.0% | 100.0% | 0.000 | Undefined |

## Method and interpretation

Scores use the [same four 1–5 rubric dimensions](judge-rubric.md). Pairing is by
original item ID, never file order. Missing model ratings and absent handoff
scores are excluded, never treated as zero. Weighted κ is Cohen's κ with squared
disagreement weights on the fixed 1–5 scale. Spearman is Pearson correlation of
average ranks, with ties assigned their mean rank. κ is undefined when expected
disagreement is zero; ρ is undefined if either score vector is constant.
Sebastian gave all ten handoffs the same score, so their ρ is undefined even
when there is a scoring difference.

This is **descriptive n=20 agreement**, not the rubric's 50-item calibration.
One reviewer, correlated response types, a narrow score range, and three PT
items limit interpretation. Fluent PT human review remains unconfirmed. No
population estimate, significance claim, or calibration threshold is asserted.
Authorization, safety and outcome correctness remain checked by code. Neither
judge is validated by agreement with the other. Analyze an earlier v3 sheet
separately if it is scored; it cannot substitute for this final-system sample.

## Reproduce privately, without model calls

The [offline supplement](judge_agreement.py) invokes the existing strict
[importer](../../evals/studies/llm/human_review.py), then adds Spearman and aggregate
gap directions. It stores and reads back **only aggregates** under ignored
`artifacts/`, with mode 0600. Inputs, item ratings, notes and CSV remain private.

```bash
LLM_PROVIDER=mock .venv/bin/python -m docs.evaluation.judge_agreement --self-check
LLM_PROVIDER=mock .venv/bin/python -m docs.evaluation.judge_agreement \
  --scored "$SCORED_HUMAN_SHEET" \
  --source "$FINAL_V4_ARTIFACTS/human-judge-20.csv" \
  --judge-inputs "$FINAL_V4_ARTIFACTS/judge-inputs.json" \
  --checkpoints "$FINAL_V4_ARTIFACTS/checkpoints" \
  --output artifacts/human-judge/v4-agreement.json
```

Source SHA-256: `84ed0d45458c0c6fba7dd92950b364ab5156887ca012ff75ce91a5fc0f6ae169`.
Scored export SHA-256: `d8cf1965fe996b6d202b6c9e683d401fd2d6f8d04ab9a5089151e5c5c1fce8fa`.
The private aggregate receipt is `artifacts/human-judge/v4-agreement.json`.
Both judges have **60/60** saved v4 judge items; this report analyzes only the
**20/20** matched human-sheet items.

## How the blind review was collected

Open `artifacts/human-judge/v4-score.html` in the AI worktree:

```bash
xdg-open $AI_WORKTREE/artifacts/human-judge/v4-score.html
```

The page embeds the lead's unchanged `artifacts/final-program-v4/human-judge-20.csv`
and the [rubric](judge-rubric.md), with Spanish instructions and 1–5 anchors.
Each item shows locale, customer message, delivered reply and handoff summary.
Model identities, judge scores and objective gold are hidden. Four independent
ratings and optional notes autosave locally; handoff usefulness is N/A when no
summary exists and exports as a blank cell. «Exportar CSV» downloads
`human-judge-20-scored.csv`, preserving all ten original columns and customer text.

The single HTML file works offline without external assets, hosting or network
calls; CSP prohibits connections. V4 autosave is separate from v3 and keyed to
the source hash. Local Chromium verified 20 items, ten N/A summaries, all 70
applicable ratings, autosave/reload and CSV export with quoted multiline notes:
zero network requests and zero browser errors. The original wording survived the
export unchanged. The generated page is mode 0600; source, page, notes and CSV
remain private and outside Git. Source SHA-256:
`84ed0d45458c0c6fba7dd92950b364ab5156887ca012ff75ce91a5fc0f6ae169`.


</details>
