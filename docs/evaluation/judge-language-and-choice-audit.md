# Reply language and remaining choices: mock audit

The combined held stack remains **27/30**, with **103/109** passing turns and
**773/789** passing checks (previously 772/789). JE-28's status language check now
passes: a Portuguese case question switches the conversation back to Portuguese
while transaction choices are still pending. The earlier matching failure still
prevents a proposal, so confirmation correctly returns 409 and no case exists.

P confirmation, cancellation and verified receipt replay use current conversation
language. Reliable ES/PT text can change it; uncertain text retains it. Owned
merchant names carry no language vote. Replay verifies the stored scoped case and
changes only text, with no model call, new execution or financial write. Proposal
hash/expiry, authorization, policy checks and machine-readable step-up details
remain intact. B1 behavior is unchanged.

JE-08 and JE-16 retain selection requests under the existing confidence policy:

| Turn | Requested fixture | Previously positively identified? | Decision |
|---|---|---|---|
| JE-08 / 3 | second | No; earlier recognition/explanation identified approved | Choose between two candidates |
| JE-16 / 1 | approved | No | Choose between two candidates |
| JE-16 / 2 | pending | Identified by this turn's positive scoped correction | Explain |
| JE-16 / 3 | approved | Earlier named and listed, never selected | Choose between two candidates |

Fresh merchant-only MATCH confidence is **0.625**, with existence confidence
**0.846939**, below the unchanged **0.9 / 0.9** automatic-selection gates. The
customer naming a charge and seeing it listed did not establish its identity.
The requested targets were not lost from a prior positive identification.
Explicit different-merchant retargets now clear old amount/date slots; fresh
inputs still require a choice. The suite continues to expect direct explanations,
so these workflows remain failed in the raw score. No expectations were weakened.

All **100 no-write**, **109 mock/zero-spend**, **14 case readback** and **7 handoff
readback** checks pass. B1 v2 remains **32/32**; model spend is **$0**. Spanish
passes 15/15; Portuguese 12/15. All remaining failures (JE-08/16/28) are workflow
checks; no UX/control check fails. Thirty new ES/PT/B1 regressions pass.
Full local integration tests: **1,740 passed, 43 skipped**. Ruff and strict mypy
pass; skipped infrastructure tests remain unverified. Earlier remote CI did not
execute, as verified in Actions budget annotations; refreshed CI awaits readback.

The frozen suite/runner and source receipts were independently hash-verified.
This extends held [#166](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/166),
[#169](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/169) and
[#170](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/170).
Metrics describe authored mock development fixtures; official v4 results remain
unchanged. Sebastian authorized cross-lane API edits; lead reviews the new held
feature and shared merge seams. PR #174 was opened before the publication audit
hold. Sebastian has since lifted that hold, and GitHub readback confirms the repo
is public. The lead retains the v0.9.1 merge order; merges remain held. Refreshed
remote CI awaits readback, and live judge runs await explicit access. No deployment,
budget or repository-visibility changes were made by the AI lane.
