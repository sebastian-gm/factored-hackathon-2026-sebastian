# AI exact merchant resolution — 2026-10-05

## Completed (verified)

- Exact owned merchant/alias identity resolves one row; duplicate names remain
  choices. NLU and MATCH thresholds, no-write and confirmation gates unchanged.
- Saved JE-11 metadata shows correction and dispute intent retained; supplied
  the missing collection-intent context and added a metadata-only gate trace.
- Frozen mock 29/30, all controls pass; same bound cohort 19/19, B1 v2 32/32.
  `ruff check` and strict mypy pass. Historical v5.1 prompt and frozen suite
  hashes preserved. [Evidence and replay limits](../../evaluation/exact-merchant-resolution.md).
- Full local mock suite: 2,073 passed, 44 infrastructure skips. Final parser,
  reply-language and budget controls: 157 passed; zero provider calls.
- Lead review revision: all eight ES/PT negation/exclusion and preceding
  unknown-alternative probes stay on choice/clarify, with generic merchant
  coverage and recognition/denial controls. Focused replay suite: 276 passed.
- Merged main `1a2b4dd` with both progress entries and histories preserved;
  frozen mock remains 29/30 with all controls green; B1 stays 32/32, spend $0.

## Done but not verified

- Real-model confidence benefit, remote CI and deployment await lead review.

## Next / blocked

- Small feature PR; main hold stays in place. Lead supplies deployed SHA and
  new scope/run for one same-19 live run capped at $0.15. Preparation spent $0.
- Official v4 unchanged; no additional held-out evaluation.
