# 2026-10-03 — Human agreement on final v4 wording

## Completed (verified)

- Read repository rules, handoffs 17–19, current/archived progress and origin/main. Created the AI feature branch from private origin/main; no public change, provider call or cloud spend.
- Strict offline import validated twenty unique unchanged blind items and all 70 applicable human ratings against saved v4 wording. All 20 have both saved judges; handoffs have n=10. CSV, individual ratings and notes remain outside Git.
- Reported each judge's exact/within-one agreement, quadratic weighted κ and Spearman ρ overall and for ES/PT. Independent in-memory recomputation matched all aggregates. Original outcomes and published v4 metrics are unchanged; agreement was measured after the final evaluation.
- `LLM_PROVIDER=mock .venv/bin/python -m docs.evaluation.judge_agreement --self-check` passed known ranks, ties, constant and empty examples. The aggregate output was read back at mode 0600. Existing importer/judge tests: 15 passed. Strict mypy: 78 source files passed.
- Reviewed every human–judge gap larger than one point privately. All favored the judge's score; notes were blank, so response-context observations are not attributed to the human's reasons. Ruff/format and documentation links passed (839 links, zero broken).

## Done but not verified

- Remote CI and merge pending on this small evidence PR.
- n=20 does not meet the rubric's 50-item calibration requirement. Fluent PT review is unconfirmed; PT n=3 and handoff n=2 cannot validate Portuguese quality.

## Next / blocked

- Merge on green remote CI, then finish handoff 19 item 7 in a separate small PR: 30 authored ES/PT multi-turn conversations, mock run and honest UX findings.
- Live exploration awaits the lead's confirmation that judge access is open, a separate durable scope capped at $0.30, and fresh before/after balance checks. No live model run started.
