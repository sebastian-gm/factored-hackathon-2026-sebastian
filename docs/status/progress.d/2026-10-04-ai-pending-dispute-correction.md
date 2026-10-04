# AI pending-dispute target correction

## Completed (verified)

- Reproduced live JE-13's lost dispute intent with synthetic ES/PT mock NLU:
  a corrected charge was explained rather than offered for separate confirmation.
- Preserve a pending P proposal's dispute intent only for an explicit, grounded
  target correction. Re-run normal matching and policy, issue a fresh proposal,
  and reject the previous hash and textual assent. Questions, ordinary inquiries,
  recognition, cancellation, uncertain details and safety guards retain precedence.
- **30 new ES/PT regressions and 329 existing regressions passed**. Ruff lint and
  format and strict mypy on all 80 source files passed; no model spend.
- The unchanged frozen exploration remains **27/30**, 103/109 turns,
  773/789 assertions. Failures remain JE-08, JE-16 and JE-28. No-write 100/100,
  zero-spend 109/109, case readbacks 14/14 and handoff readbacks 7/7 passed.
- Final B1 v2 (`evals/dev_scenarios_v2.yaml`) remains **32/32**; zero model spend.
- API cross-lane changes are explicitly authorized by the owner and require
  lead review. Frozen interfaces, matching thresholds and expectations are unchanged.

## Done but not verified

- No paid live rerun of this correction. Remote CI is pending.

## Next / blocked

- The lead reviews and owns the merge order; this feature remains held.
- Preserve the live operator's unresolved reservation and partial evidence.
