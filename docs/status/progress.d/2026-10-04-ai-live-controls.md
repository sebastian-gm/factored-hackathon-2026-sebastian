# AI live exploration controls

## Completed (verified)

- Added pure evaluation helpers for the reviewed v0.9.1 contextual NLU ceiling,
  all configured attempts, trusted judge identity and independently supplied
  execution receipts. Handoff verification permits the source-proven
  post-commit enrichment and opt-in BFF field projection; API matching stays exact.
- `.venv/bin/python -m pytest -q tests/test_live_exploration_controls.py`:
  **61 passed**, including ES/PT roles, BFF projection and invalid cost receipts.
  Ruff lint and format checks pass.
- `LLM_PROVIDER=mock .venv/bin/python -m evals.runner --system B1`:
  **32/32**, 12 readbacks, safety guards passed; zero model spend.
- The initial live operator's incorrect customer-role restriction was corrected.
  Four fresh judge profile visits verified the trusted configured roles without
  model calls. Original paid receipts and durable reservations were preserved;
  the owner explicitly authorized untouched stories only.

## Done but not verified

- Remote CI for this feature PR is pending. Product source and official v4
  evaluation results are unchanged.

## Next / blocked

- Record the live exploration outcome separately, including unbound fixtures
  and own-execution cost. The lead reviews and owns all merges.
