# Human wording review of the saved v3 sample

**Status: human ratings pending.** This is a descriptive review of existing v3
responses, not a new model run or the rubric's required 50-item calibration.
No human–judge agreement is claimed yet. The original outputs and official v3
results remain unchanged; v3 is now development evidence.

## Offline scoring and import

The private page is
`artifacts/human-judge/v3-score.html` in the AI worktree. It embeds the lead's
unchanged `artifacts/final-program-v3/human-judge-20.csv` and the
[rubric](judge-rubric.md), with Spanish instructions and translated score anchors.
It shows locale, customer message, delivered reply and handoff summary, without
system identities, objective gold or model scores. Four independent 1–5 ratings
and optional notes autosave to localStorage. Handoff usefulness is N/A when no
summary exists and exports as a blank cell. «Exportar CSV» preserves the exact
ten source columns and original wording, including any visible defects.

Open the HTML directly in a browser. It has no dependencies, external assets,
hosting or network calls; CSP prohibits connections. Ratings stay in that
browser/device until exported. The original source, generated HTML, notes and
exported CSV stay out of Git. Offline Chromium checks verified 20 items, six
N/A summaries, autosave/reload and CSV export with quoted multiline notes:
zero network requests and zero browser errors. Source SHA-256:
`898c2702856dc4475e5e8f7f4d22865081cd74369330e6759f4385db78a75418`.

After Sebastian confirms his export path, run the
[importer](../../src/aclara/llm/human_review.py) from the AI worktree:

```bash
.venv/bin/python -m aclara.llm.human_review import \
  --scored /home/megagdev/Downloads/human-judge-20-scored.csv \
  --source /home/megagdev/megagdev/factored-hackathon-2026/bank-agent-lab/artifacts/final-program-v3/human-judge-20.csv \
  --judge-inputs /home/megagdev/megagdev/factored-hackathon-2026/bank-agent-lab/artifacts/final-program-v3/judge-inputs.json \
  --checkpoints /home/megagdev/megagdev/factored-hackathon-2026/bank-agent-lab/artifacts/final-program-v3/checkpoints
```

The Downloads path is provisional. Import requires all applicable human ratings,
the original twenty unique IDs, identical locale/text and exact CSV columns. It
also matches saved judge inputs before joining score checkpoints by blinded ID.
No additional judge calls are made. Its ignored `v3-agreement.json` reports human
vs Sonnet, human vs Jev and Sonnet vs Jev, by dimension and ES/PT slice: paired n,
exact agreement, within-one agreement and quadratic-weighted Cohen's κ on the
fixed 1–5 scale. Missing scores and N/A are excluded, never imputed as zero.
Empty pairs and zero expected disagreement produce undefined κ.

## Available pairs and limitations

[V3 judging](final-v3-results.md) stopped at **28/60** items. Only **10/20** sheet
items have saved scores: six ES, two PT and two mixed. Eight of those ten have
handoff summaries. Thus completing all twenty human ratings cannot create
twenty model pairs. On these existing shared sheet items only:

| Sonnet vs Jev dimension | Paired n | Exact | Within one | Quadratic κ |
|---|---:|---:|---:|---:|
| Language/register | 10 | 60% | 100% | 0.429 |
| Clarity | 10 | 30% | 100% | 0.286 |
| Empathy | 10 | 20% | 90% | 0.000 |
| Handoff usefulness | 8 | 100% | 100% | Undefined: no variance |

Human vs Sonnet and human vs Jev results will be added after the confirmed export.
These small, partially observed pairs cannot validate either judge. One reviewer,
partial judging and correlated response types limit interpretation; mixed items
are included in the overall denominator but excluded from ES/PT slices. Fluent
PT human review remains unconfirmed. Inspect differences exceeding one point;
keep item-level notes and ratings private. Objective outcomes remain code-scored.

## Item 1 integrity check and repair

The reported defect is present in both the CSV and its saved reply; it was not
introduced by export. The pinned v3 implementation is `e12efc7`, with phrase
**v1**. This historical sample does not demonstrate a phrase-v2 failure.

Current [phrase v2](../../prompts/phrase/v2.md) preserves the approved reply and
requested language. Its [language guard](../../src/aclara/agent/nlg/builder.py)
identifies the saved reply as PT and rejects confidently opposite-language drafts
when the caller requests ES. This is a conservative heuristic: ambiguous text or
an incorrectly supplied target language cannot be guaranteed correct.

Before this repair, [grounding/DLP](../../src/aclara/agent/nlg/grounding.py) rejected
uncited handles but accepted cited internal handles and corrupted characters.
It now rejects customer-text `txn_`, `prod_`, `card_` and `cust_` numeric handles
regardless of citation; verified customer case references remain allowed. It also
rejects replacement characters, common UTF-8 mojibake, a narrow word-internal
apostrophe/hash corruption signature and non-whitespace control characters.
Valid ES/PT accents are preserved. Unknown corruption patterns can still escape
this detector; it is not a universal text-quality proof.

The [authored regressions](../../tests/test_nlg_output_integrity.py) reproduced
14 failures before the repair. A zero-cost replay of the saved reply through the
current builder rejects both integrity defects and returns a clean Spanish
approved template after two mock attempts. Opposite-language tests pass separately
in both directions. Private aggregate receipt:
`artifacts/human-judge/item1-replay.json`. No deployment, paid calls or v4 access.

Local verification: 459 Python tests passed, 17 database-dependent skips; the
v4-specific test module was excluded and a file-access barrier protected actual
v4 inputs. Strict mypy, Ruff, interface/catalog checks and B1 dev 32/32 passed.
