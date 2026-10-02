# 2026-10-02 — Portuguese injection guard (AI lane)

## Completed (verified)

- Reproduced the saved ablation opening: `Ignore as regras` missed the deterministic guard; Spanish `Ignora las reglas` already matched. Four authored override regressions failed before the fix.
- Narrow shared-file correction in `policy/rules/guards.py`: PT `regras`, ES/PT `políticas` and `desconsidere` now use the existing control-override guard.
- Original ablation evidence and official v4 numbers remain unchanged. Post-v4 fix, not reflected in v4. No changes to `agent/ai.py` or `llm/client.py`.

## Done but not verified

- All authored API/unit and existing guard/workflow mock regressions pass. Full local checks, B1 32/32, Ruff, strict mypy and snapshots pass. Required remote CI is pending; no real-model claim for this fix.

## Next / blocked

- Merge hold until #137 then #140 land and the lead announces clearance.
- Freeze/commit a separately disclosed 20-case adversarial dev stress arm before inference; own approved $0.10 cap.
