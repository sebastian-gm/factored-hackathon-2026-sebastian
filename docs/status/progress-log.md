# Development record moved

Read the [complete archived record](../history/status/progress-log.md).
The [final evaluation (v4)](../evaluation/final-v4-results.md) remains unchanged.

Latest AI session: [October 3 human review](progress.d/2026-10-03-ai-judge-human-agreement.md).

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
