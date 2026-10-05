# Development record moved

Submission materials: [six-page slides and demo video](../submission/README.md);
[verification record](progress.d/2026-10-04-submission-deliverables.md).

Read the [complete archived record](../history/status/progress-log.md).
The [final evaluation (v4)](../evaluation/final-v4-results.md) remains unchanged.
Current release: [v0.9.4 verified ES/PT quick-start](../submission/v0.9.4-release-evidence.md).

Latest AI human review: [October 3 post-hoc agreement](../evaluation/judge-human-validation.md).

Latest live AI evidence: [partial v0.9.1 judge exploration](../evaluation/judge-live-exploration-v0.9.1.md).

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
[v0.9.1 progress entry](../history/status/progress-log.md#2026-10-04-v091-release-verified-and-live-lane-signal).
Historical AI baseline: [October 3 mock judge exploration](../evaluation/judge-multi-turn-exploration.md).

Latest AI controls: [live exploration verification](progress.d/2026-10-04-ai-live-controls.md).
Latest AI choice follow-ups: [mock context regressions](progress.d/2026-10-04-ai-pending-candidate-followups.md).

Earlier candidate: [v0.9.3 reviewed judge-story integration](progress.d/2026-10-04-v093-review.md).
Historical v0.9.3 stop remains disclosed; v0.9.4 is verified in the
[release progress record](progress.d/2026-10-04-v094-release.md).

Latest AI starter replays: [missing-merchant normalization](progress.d/2026-10-04-ai-merchant-placeholder.md).
Latest AI live diagnosis: [partial exploration and zero-cost root causes](progress.d/2026-10-04-ai-live-exploration-partial.md).

## 2026-10-04 — English reviewer interface candidate

### Completed (verified)

- EN desktop/phone chrome, ES/PT conversation separation and staff guidance;
  [lane record](progress.d/2026-10-04-english-interface-activation.md).
- Final admission/resilience checks: 26 passed; TypeScript and lint passed.
- Catalog #194 merged; main merged into activation #195 without rewriting history.

### Done but not verified

- Activation remote final gates and deployed v0.9.5 behavior remain pending.

### Next / blocked

- Lead owns merge/release; clean 2x authored-fixture video assets follow both merges.

## 2026-10-04 — v0.9.5

## Completed — verified

- Catalog #194 and corrected activation #195 merged on four green remote gates.
- Deployed/tagged/released `7ca5905015a42f1e79db10e1bb995005a7b17747` as v0.9.5.
- Local/mock browser review 129/129; corrected PR browser groups 255 passed;
  production build and exact-SHA CI/safety passed.
- Image-only plan/apply; Azure readback and independent authenticated access passed.
- Live fresh-judge EN default, English Desk/Insights, ES/PT draft language,
  desktop/390px bounds, four-profile RLS, stale-cookie and logout checks passed.
- Temporal and masked queue security readbacks passed. Zero new model calls/spend;
  conservative maximum $14.91264898/$15; existing $1/UTC-day prod cap retained.
- [Release evidence](../submission/v0.9.5-release-evidence.md) documents commands,
  workflow IDs, image digests, initial CI failures and revision convergence.

## Done but not verified

- No new real-model or financial-action run: v0.9.4 evidence is explicitly inherited
  only for the identical API digest and unchanged runtime inputs.
- Populated live English packets were not created; source and authored tests cover
  English guidance. Original API summaries remain labeled ES/PT service text.

## Next / blocked

- Video/submission may use v0.9.5. Final v1.0.0/email await Sebastian's go.
- Official v4 results remain unchanged; no held-out replay or new score.

## 2026-10-04 — English launch gallery and phone icon

### Completed (verified)

- Both English-interface PRs merged; #195 head was
  `4407436036389d25dbc0faf347ba95d46c6dff0e`, merged at `7ca5905`.
- Local authored bank gallery: 90 PNGs at 2x scale, desktop and phone,
  ES/PT replies, English staff guidance, verified case and four claim readbacks.
  Published aggregate Insights charts included with explicit owner approval.
- Phone icon regression reproduced at 320/390px; CSS correction passed all
  13 English Playwright checks including axe. TypeScript and focused lint passed.
- Model spend and external browser requests: zero. Gallery stays ignored at
  `artifacts/ux-audit/video-assets-en/`; no organizer row inputs used.

### Done but not verified

- Phone icon correction awaits remote CI and lead review; refreshed captures
  will identify their exact source SHA in the local manifest.

### Next / blocked

- Lead retains all main merge and release authority. No live model runs needed.

## 2026-10-04 — v0.9.6 phone release

## Completed — verified

- Reviewed #197; history-preserving main merge kept both progress entries.
  Fresh four-gate CI passed before merge; no action/session/policy changes.
- Deployed/tagged/released `22f8833c33599e0b49d00ce60e533641ce4be9e8` as v0.9.6.
- Local/mock English checks 13/13; refreshed PR browser groups 257 passed;
  exact-SHA CI/safety, production build and Azure readback passed.
- Live Chromium ES/PT at 320/390px: square avatar, minimum width 32px;
  page/header bounds, English UI, ES/PT drafts and logout passed.
- Four-profile RLS/role/stale-cookie checks, temporal/queue security and independent
  authenticated azure-access passed. Zero chat submissions/financial writes/models.
- New LLM spend $0; budget/provider readbacks unchanged; conservative maximum
  $14.91264898/$15; production $1/UTC-day retained. Image/metadata-only release.
- [Release evidence](../submission/v0.9.6-release-evidence.md) records commands,
  exact workflows, image digests and verification limits.

## Done but not verified

- No new real-model or financial-action check; unchanged API explicitly inherits
  v0.9.4 evidence. No populated live packet or physical-device/Safari test.

## Next / blocked

- Stand by for submission instructions. v1.0.0/email await Sebastian's go.
- Official v4 unchanged; no held-out rerun or new score.
