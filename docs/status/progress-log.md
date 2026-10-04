# Development record moved

Read the [complete archived record](../history/status/progress-log.md).
The [final evaluation (v4)](../evaluation/final-v4-results.md) remains unchanged.
Current release: [v0.9.1 verified release](../submission/v0.9.1-release-evidence.md).

Latest AI human review: [October 3 post-hoc agreement](../evaluation/judge-human-validation.md).

<details>
<summary>Compatibility excerpt for existing chart tools</summary>

- Approved ten-conversation latency probe stopped correctly after **5 conversations /
  10 turns** on one unknown-cost call; no retry. In-Azure BFF p50/p95 **1.300s / 8.191s**;
  excluding the entire first conversation, **1.300s / 7.441s** (8 turns). Client
  **1.384s / 8.277s** includes workstation network. No forced cold restart; handler
  timing excludes ingress/module startup. Known **$0.00964182**, charged **$0.02157732**,
  11 reservations / 1 unknown. Probe purse was closed with reservations preserved;
  prior release binding restored via plan/apply (**0 added, 1 changed, 0 destroyed**).

- Latency probe is **partial (5/10)**, not a 10-conversation measurement; p95 is a
  small-sample observation, not an SLA or cold-start bound. Unknown cost remains reserved.

- Disclosure: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed.

</details>

AI candidate-correction evidence: [mock conversation improvements](../evaluation/judge-conversation-improvements.md).
AI reply-language evidence: [mock language and choice audit](../evaluation/judge-language-and-choice-audit.md).
Public-only publication completed at v0.9.0; v1.0.0 and email remain pending.
The [folded lane records](../history/status/progress-log.md#2026-10-04-public-only-publication-and-held-batch-records)
preserve author-time checks and holds. The combined v0.9.1 release, reset and live-lane signal are verified in the
[latest progress entry](../history/status/progress-log.md#2026-10-04-v091-release-verified-and-live-lane-signal).
Historical AI baseline: [October 3 mock judge exploration](../evaluation/judge-multi-turn-exploration.md).

Latest AI choice follow-ups: [mock context regressions](progress.d/2026-10-04-ai-pending-candidate-followups.md).
