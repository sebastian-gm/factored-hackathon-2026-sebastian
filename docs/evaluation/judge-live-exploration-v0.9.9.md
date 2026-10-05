# Post-v4 final build: v0.9.9 judge exploration

The single approved rerun met **19/19 bound story goals**, up from **12/19**
on v0.9.8. All **69/69 turns**, **430/430 assertions** and **79/79 safety
checks passed. All 30 frozen stories remain accounted for: 19 completed and
11 unbound because their fixture prerequisites remain absent.

| Measure | v0.9.8 | v0.9.9 |
| --- | ---: | ---: |
| Same bound story goals | 12/19 | 19/19 |
| Passing turns | 52/69 | 69/69 |
| No-write checks | 62/62 | 62/62 |
| Independent case readbacks | 13/13 | 13/13 |
| Independent handoff readbacks | 6/6 | 4/4 |
| Own durable cost | $0.05621900 | $0.07865600 |
| New unknown reserves | 0 | 0 |

The two fewer handoff readbacks reflect the avoided failure handoffs in JE-11
and JE-27. Every actual handoff still received an independent readback. The
frozen suite and its assertions are unchanged; the merchant rule and collection
context preserve the existing NLU/MATCH gates, authorization and separate
confirmation. Previously failing JE-03/05/11/17/19/21/27 all passed. The ES/PT
merchant-only openings and JE-11 correction now reach their expected flows.

The deployed API/web SHA was
`67d449ceb9029b09d3da9e49bb5c5b723c19b83a`, containing reviewed #210.
Execution used fresh authenticated judge visits, the existing profile bindings,
real production NLU and 39 model calls. Scope `live-exploration/v0.9.9`, run
`v0.9.9`, remained within its **$0.15** lifetime cap. Each HTTP request reserved
before dispatch; settlement used only its independently scoped execution costs.
There were zero retries, budget denials or unknown reserves. Production balance
and key remaining were privately verified before and after.

The unbound stories remain JE-01/02/04/08/09/10/14/16/24/28/30. They require
absent Pending/Reversed purchases, same-merchant pairs or a second suitable
charge. A judge still cannot reproduce those stories with the current profiles.
The full frozen mock suite remains **29/30**, with all safety controls passing;
JE-28's amount-bearing PT-to-ES retarget is its remaining failed story and is
unbound on live. The same bound mock cohort is 19/19. B1 v2 remains 32/32 from
the reviewed fix's mock verification. Official v4 results are unchanged.

Zero-model operator checks verified 92 preparation paths, 66 conservative
ceilings, 104 receipt projections and all 30 fixture bindings against the
source-pinned release before paid dispatch. The frozen suite SHA-256 remains
`e35afd88a589bfb07a820f014f78d2b65ab098a4cd50fcac9690c8027fbcc3ee`.

The read-back aggregate receipt is ignored and mode 0600 at
`artifacts/judge-exploration/v0.9.9/aggregate.private.json`. It contains the
deployment, attempted/bound/unbound counts, goals and safety, durable charge
including unknown reserves, and private provider balance/key checks. This
report contains aggregates only.
