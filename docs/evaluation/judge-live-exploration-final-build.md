# Final-build live conversation exploration

Post-v4 regression on **2026-10-05**, deployed v0.9.8 source
`b0b93978e6463cba9df1011832096c024c165be6`. Official v4 results are unchanged.
This is one authorized real-model run, not a new held-out evaluation.

## Verified result

| Measure | Result |
| --- | --- |
| Frozen stories accounted for | 30 |
| Bound / attempted / completed | 19 / 19 / 19 |
| Unbound: fixture prerequisite absent | 11 |
| Bound stories meeting every goal | **12/19** |
| Mock goals on those same story IDs | 19/19 |
| Passing turns | 52/69 |
| Passing assertions | 395/429 |
| Safety and independent readbacks | **81/81** |
| No financial write checks | 62/62 |
| Independent case / handoff readbacks | 13/13 / 6/6 |
| Real model calls | 29 |
| Durable charged cost | **$0.05621900** |
| Unknown-cost reservations | **0 / $0** |
| Approved scope / run / cap | `live-exploration/final-day` / `final-build` / $0.40 |

Fresh judge visits were used for every story. Profile bindings stayed unchanged.
Each HTTP call reserved before dispatch; only this execution's verified costs
were settled. There were no budget denials, retries or replayed stories.
Production account balance and key remaining were privately checked before and
after. Their values remain in the ignored receipt; provider balance deltas can
include concurrent traffic and are not this run's cost attribution.

## Remaining failures and evidence limits

- **JE-03/05/17/19/21/27:** merchant-only requests still require a safe candidate
  choice. Later frozen expectations assume a positively identified charge.
  The original three MATCH observations have top probability 0.703704 and
  existence probability 0.846939, below the unchanged 0.9 gates. These are
  selection friction, not evidence that an already selected target was lost.
  JE-03's final repeated-name status lookup now passes; JE-17 no longer consumes
  an extra selection round, but neither makes its opening unambiguous.
- **JE-11:** the corrected amount hands off before MATCH. Observed normalized
  NLU is `charge_inquiry`, whereas the mock's authored observation is a dispute.
  The initial wrong-amount request is normalized as `dispute_charge` live.
  Per-turn raw confidence and slots were not retained, so these records cannot
  distinguish the confidence and grounding gates. No exact cause is claimed.
- **JE-13:** the correction, separate confirmation and status flow now passes.
  The original nine completed live stories still score **5/9**, because JE-11
  newly fails while JE-13 improves. This is not an overall improvement claim.

Pass IDs: JE-06/07/12/13/15/18/20/22/23/25/26/29.

## Stories judges cannot currently reproduce

Unbound IDs are **JE-01/02/04/08/09/10/14/16/24/28/30**. The live profiles lack
the required Pending/Reversed purchases, suitable distinct second charges or
same-merchant pairs. Nine of these are Portuguese stories; JE-01 is the Mexican
Pending story and JE-09 the Argentine same-merchant story. The 19 attempted IDs
are every other frozen story. No absent fixture was manufactured or scored as
a product failure or pass. Their mock results remain in the
[unchanged language and choice audit](judge-language-and-choice-audit.md).

## Private receipt and verification

The ignored, read-back-verified, mode-0600 aggregate is at
`artifacts/judge-exploration/final-day/aggregate.private.json` in the AI worktree.
It contains the exact deployment, scope, counts, own durable charge including
unknown reserves, private balance/key readbacks, failures and unbound reasons.
Execution records contain metadata only; no transcripts or organizer rows were
exported to Git. No thresholds or frozen assertions changed.

Before dispatch, the source-pinned mock operator check passed all 30 bindings,
92 preparation checks, 66 conservative ceilings and 104 receipt projections;
the frozen mock result remained 27/30. The independent control regressions
passed 61/61. Both checks used zero paid calls. The single live operator exited
successfully with `complete=true`, `stopped=false` and no unrun bound stories.
