# Conversation improvements: mock exploration

The unchanged 30-conversation study improved from **15/30 to 27/30**, exceeding
Sebastian's >=26/30 target. Spanish passes 15/15; Portuguese passes 12/15.
These post-v4 development results do not revise official v4 results or establish
live-model fluency, large-ledger matching quality or browser behavior.

| Measurement | Before | Combined fixes |
|---|---:|---:|
| Coherent conversations | 15/30 | 27/30 |
| Passing turns | 75/109 | 103/109 |
| Passing checks | 727/798 | 772/789 |
| No-write checks | 100/100 | 100/100 |
| Mock / zero-spend checks | 109/109 | 109/109 |
| Independent case reads | 12/12 | 14/14 |
| Independent handoff reads | 21/21 | 7/7 |
| B1 v2 acceptance | 32/32 | 32/32 |
| Model spend | $0 | $0 |

Conditional readback counts change with responses: keeping chats open removes
unnecessary scope transfers, while successful case flows add receipt reads.
All original safety and no-write expectations remain active. No matcher
thresholds, calibration artifacts, fixture aliases or expectations were weakened.

The fixes answer short ES/PT follow-ups from freshly read charge/policy/case
context, route everyday case questions to status, keep courtesy and unrelated
requests open, and re-filter candidate corrections using owned bank facts.
Informational turns preserve proposal hashes but cannot confirm them. Real human,
fraud/legal/security and bounded-ambiguity handoffs retain their existing controls.
Rejected model-only or competing correction facts cannot select a charge or leak
into later turns; currency alone cannot identify an otherwise unidentified charge.

Remaining failures are unchanged expectations, not safety failures:

- **JE-08:** after recognizing the first charge, another merchant inquiry asks for a choice instead of explaining the named charge.
- **JE-16:** initial and returning approved-charge inquiries ask for choices; the intervening corrected second-charge inquiry now succeeds.
- **JE-28:** the second charge asks for selection rather than proposing a dispute. Confirmation correctly returns 409 without a proposal; later status has no filed case, asks for clarification and misses the requested Portuguese language.

The remaining choices reflect the retained confidence-based matcher; this study
does not justify lowering its selection threshold.

Validation uses the frozen [#162](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/162)
runner/suite and local integration of held [#166](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/166),
[#169](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/169) and
[#170](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/170).
Suite SHA-256: `e35afd88a589bfb07a820f014f78d2b65ab098a4cd50fcac9690c8027fbcc3ee`.
The unmerged runner was loaded from a hash-verified ignored copy; only its receipt
path label changed. Private synthetic receipts were saved with mode 0600 and read
back; extra source hashes cover the correction helper. New regressions cover ES/PT
context, courtesy, corrections, persistence, scoping and confirmation authority.
Full combined local tests: **1,710 passed, 43 skipped**. The 75 new ES/PT
regressions pass. Ruff and strict mypy pass; skipped infrastructure tests and
latest remote gates remain unverified while CI is unavailable.

Sebastian authorized cross-lane API edits; lead reviews the three small PRs and
their shared conversation seams. All remain unmerged under the release hold.
Latest CI is blocked before setup by the exhausted GitHub Actions budget; the
courtesy PR's earlier green run remains verified. No budget or visibility changes.
Live exploration awaits the lead's explicit access signal and approved spend scope.
