# 2026-10-05 — AI pending-dispute follow-up

## Completed (verified)

- #204 is open at `ada7bf935395227b9673f649b2009ba51cf5fb04`; it classifies the
  saved failures and resolves repeated literal merchant reads in pending choices.
- JE-17 replay reveals a round-count bug beyond its correct demand for a choice.
  Fix P's bounded positive return-to-dispute clause to retain owned choices and
  dispute intent without consuming a clarification round or selecting a target.
  Authorized cross-lane API edits require lead review.
- Two ES/PT cases fail before the production edit (rounds 1 versus 0).
  `LLM_PROVIDER=mock uv run pytest -q -o addopts= tests/test_pending_dispute_followup.py tests/test_pending_candidate_followups.py tests/test_dispute_target_correction_context.py tests/test_candidate_corrections.py tests/test_api_security.py tests/test_workflow_api.py tests/test_live_charge_starter_replays.py tests/test_conversation_reply_language.py`: **197 passed**, including 22 new cases.
- Ruff and strict mypy pass. Frozen mock exploration remains **27/30** and all
  no-write/zero-spend/case/handoff readbacks pass. B1 v2 remains **32/32**.
  New model spend **$0**; historical partial 5/9 and official v4 stay unchanged.

## Done but not verified

- Second PR's remote CI and lead review/deployment remain pending.
- Historical raw slots/confidence are absent; replay inputs label reconstructions.
- No new paid run; operator preparation waits until item 1 fixes are submitted.

## Next / blocked

- Open/report this small PR and leave both feature PRs unmerged for the lead.
- After deployed-SHA/new-scope signal, perform the approved single fresh-judge
  exploration at <=$0.40 within the approved $18 cumulative ceiling.
