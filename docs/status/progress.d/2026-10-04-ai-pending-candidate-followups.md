# AI pending-choice follow-ups

## Completed (verified)

- Audited verified live JE-03/05/17 execution metadata without new model calls.
  Their opening normalized intent/flags match the mock observations; MATCH safely
  chose candidates. Raw model JSON, confidence and per-turn slots are unavailable.
- Reproduced JE-03/05's subsequent questions/recognition being treated as out of
  scope without invoking NLU. Keep owned choices visible on contextual follow-ups;
  explicit recognition clears unfamiliarity without selecting a charge.
- Added 24 synthetic ES/PT regressions with the observed normalized intent/flags.
  Confidence and slots are reconstructed, explicitly labeled. Re-read owned handles;
  never auto-select, consume another clarification round, or bypass safety guards.
- The combined corrected tree passed 183 targeted conversation/security/language
  regressions. The unchanged exploration remains **27/30**, 103/109 turns and
  773/789 checks; JE-08/16/28 remain. All 100 no-write, 109 zero-spend, 14 case and
  7 handoff readbacks pass. Final B1 v2 remains 32/32; no model spend.
- Cross-lane API changes are explicitly authorized and require lead review.
  This PR depends on #180; matching thresholds and frozen expectations are unchanged.

## Done but not verified

- No paid rerun or deployed verification. Remote CI is pending.

## Next / blocked

- Keep this feature held; the lead owns release merge order and merges #180 first.
- Preserve the partial live evidence and unresolved reservation. No paid retry.
