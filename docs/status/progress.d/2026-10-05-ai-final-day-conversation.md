# 2026-10-05 — AI final-day conversation fixes

## Completed (verified)

- Classified every saved live failure in
  [the final-day audit](../../evaluation/final-day-conversation-failures.md).
  #180/#185 are already on main; no new live calls were needed.
- Fixed JE-03's repeated merchant read while choices are pending. Resolve only
  one literal current owned retained candidate with unchanged record identity;
  explicit read wording explains without inheriting a pending dispute.
  API edits are within Sebastian's explicit cross-lane authorization; lead reviews.
- Four recorded-boundary regressions fail when the resolver is disabled.
  `LLM_PROVIDER=mock uv run pytest -q -o addopts= tests/test_pending_merchant_reference.py tests/test_pending_candidate_followups.py tests/test_dispute_target_correction_context.py tests/test_candidate_corrections.py tests/test_api_security.py tests/test_workflow_api.py tests/test_live_charge_starter_replays.py tests/test_conversation_reply_language.py`: **215 passed**, including 40 new ES/PT and safety cases.
- Ruff passes; `uv run mypy --strict src/aclara`: 81 source files pass.
- Frozen mock exploration: **27/30**, unchanged expectations and thresholds;
  100 no-write, 109 zero-spend, 14 case and 7 handoff readbacks pass.
  B1 original and v2 each **32/32**. New model spend **$0**.

## Done but not verified

- Remote CI, lead review and deployed behavior await the feature PR/release.
- No new live score. Raw historical model JSON/confidence/slots were not stored;
  replays explicitly distinguish retained metadata from authored reconstructions.

## Next / blocked

- Open the small PR, report its number immediately, and leave merging to the lead.
- Item 1 comes before operator preparation. After the lead deploys the fixes,
  use the supplied SHA/new durable scope for the newly approved single <=$0.40
  fresh-judge rerun. The cumulative ceiling is $18; old reservations stay intact.
- Post-v4, final build only; official v4 numbers remain unchanged.
