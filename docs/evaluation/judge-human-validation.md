# Human wording review of the final v4 system

**Status: v4 page ready; human ratings pending.** Sebastian will rate the final
system's saved v4 responses. No human–judge agreement is claimed before his
export is received. This 20-item review is descriptive; it does not satisfy the
[rubric's 50-item calibration requirement](judge-rubric.md).

## Offline scoring

Open `artifacts/human-judge/v4-score.html` in the AI worktree:

```bash
xdg-open /home/megagdev/.herdr/worktrees/bank-agent-lab/feat-ai/artifacts/human-judge/v4-score.html
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

## Import the human export

Once the exported path is confirmed, run the
[importer](../../src/aclara/llm/human_review.py) from the AI worktree:

```bash
.venv/bin/python -m aclara.llm.human_review import \
  --scored /home/megagdev/Downloads/human-judge-20-scored.csv \
  --source /home/megagdev/megagdev/factored-hackathon-2026/bank-agent-lab/artifacts/final-program-v4/human-judge-20.csv \
  --judge-inputs /home/megagdev/megagdev/factored-hackathon-2026/bank-agent-lab/artifacts/final-program-v4/judge-inputs.json \
  --checkpoints /home/megagdev/megagdev/factored-hackathon-2026/bank-agent-lab/artifacts/final-program-v4/checkpoints \
  --output artifacts/human-judge/v4-agreement.json
```

The Downloads path is provisional. Import requires all applicable ratings,
twenty unique original IDs, exact columns and unchanged locale/text, and checks
the wording against saved judge inputs before joining checkpoint scores by ID.
A v3 export cannot be substituted. It makes no new model calls.

Report human–Sonnet, human–Jev and Sonnet–Jev agreement per dimension: paired n,
exact agreement, within-one agreement and quadratic-weighted Cohen's κ on the
fixed 1–5 scale, overall and for ES/PT. Missing ratings and absent handoffs are
excluded; they never become zero. Empty pairs and zero expected disagreement
produce undefined κ. Keep item-level ratings and notes private; inspect
disagreements exceeding one point after the human scores arrive.

## Saved v4 judge pairs

All **60/60** planned v4 judge items have saved Sonnet/Jev scores. All **20/20**
human-sheet items can be paired: eleven ES, three pt-BR, three mixed and three
other-language items. Ten have handoff summaries. On these shared sheet items,
before any human ratings:

| Sonnet vs Jev dimension | Paired n | Exact | Within one | Quadratic κ |
|---|---:|---:|---:|---:|
| Language/register | 20 | 50% | 100% | 0.174 |
| Clarity | 20 | 60% | 90% | 0.364 |
| Empathy | 20 | 30% | 100% | 0.200 |
| Handoff usefulness | 10 | 90% | 100% | 0.000 |

These are judge–judge agreements, not correctness or human validation. Two
clarity pairs differ by more than one point. The private aggregate receipt is
`artifacts/human-judge/v4-agreement-pending.json`; human pair counts are currently
zero. **TODO(human export):** add each judge's agreement with Sebastian, ES/PT
slice denominators and the review of larger disagreements.

One reviewer, a small sample, correlated response types and only three pt-BR
items limit interpretation. Fluent PT human review remains unconfirmed. Mixed
and other-language items are included overall but excluded from ES/PT slices.
Objective outcomes, authorization and safety remain code-scored. Neither judge
is validated by agreement with the other.

V4 is the primary human-review sample. Analyze the earlier v3 sheet separately
only if Sebastian also scores it; it will not substitute for final-system ratings.
