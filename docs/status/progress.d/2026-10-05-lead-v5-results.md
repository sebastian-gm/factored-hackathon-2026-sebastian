# Lead — independent v5 completed (October 5)

## Completed (verified)

- #213 and eval-only metadata fix #215 merged on four green gates. Evaluated `d53d1b9fdedec68adb3a87205b018fa48b8a68c5`; runtime diff from v1.0.0 empty. Manifest pin `f6e7b15bcef3766b4933c1eb2ef95eb3118bdf46ffef6a9de6d2c1709a3ccaef`; private binding mode/checksum/ownership verified inside the authorized loader.
- `scripts.v5_blind_evaluation start/status --suite test-v5`: COMPLETE 200/200 checkpoints, one pass per system, no case replay. P 73/100 vs B1 47/100; SAR 27/100 vs 18/100; paired +9 pp (95% CI +3 to +16); strict escalation 35/46 vs 27/46. Full safety gate failed; every predicate/ID is in `docs/evaluation/final-v5-results.md`.
- `scripts.v5_budget` plus free provider credits before/after: $0.320539 charged/known, 157 valid Gemini calls, zero new unknown reserves; $1.50 lifetime cap; conservative maximum $17.26264898/$18 retaining 75 historical unknown reserves. Zero-case shell/preflight stops preserved/disclosed; no product fix, deploy or tag.
- Authored prep tests: 4 passed; pre-commit passed. Official v4 remains unchanged; README labels this independent blind post-fixes check.

## Done but not verified

- Human gold/language validation, family-level uncertainty, natural conversations and deployed latency. Unreached fault boundaries: P one, B1 two; retained as failures.

## Next / blocked

- Merge this aggregate docs PR only on green CI, then stop. No paid follow-up, product changes or reruns for improvement.
