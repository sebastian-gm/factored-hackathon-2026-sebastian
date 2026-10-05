# Development record moved

Submission materials: [six-page slides and demo video](../submission/README.md);
[verification record](progress.d/2026-10-04-submission-deliverables.md).

Read the [complete archived record](../history/status/progress-log.md).
The [final evaluation (v4)](../evaluation/final-v4-results.md) remains unchanged.
Current release: [v0.9.7 verified presentation/login copy](../submission/v0.9.7-release-evidence.md).

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

## 2026-10-04 — Banking app presentation for v0.9.7

### Completed (verified)

- Removed the shared top demo strip and clock label; EN/ES/PT disclosure now
  appears once in the sidebar footer, including phones.
- Verification cards keep the code visible with realistic labels and a small
  demo delivery note; English remains the interface default.
- TypeScript, lint and production build passed. Full local Python suite:
  1,941 passed, 43 skipped, using mock models and no provider credentials.
- All 257 local browser cases verified: 227 default, 12 fixture API, 13 staff,
  2 judge roles and 3 judge staff. Desktop/phone axe and layout checks passed.
- Updated ten legacy SMS/font assertions after the initial runs; all affected
  cases passed focused reruns. Ruff, strict mypy, interface and policy checks
  passed. No authentication, authorization or conversation-language changes.

### Done but not verified

- Remote CI and deployed v0.9.7 await the PR and lead release.

### Next / blocked

- Open a small PR against main and report its head. Lead owns merge/release.
- Zero spend; no live model suite or organizer row inputs required.

# 2026-10-04 COT — v0.9.7 release

## Completed — verified

- #200 reviewed and merged on four green gates. Local/mock English browser
  check 13/13; remote browser groups 257 passed. Production image build passed.
- Deployed/tagged/released `1525ecec2c23e64d8dbda733a2c610757c18495b`.
  Exact-SHA CI/safety, Azure controls and independent authenticated access passed.
- Live login/OTP at 390px, one sidebar disclosure, absent strip/clock, ES/PT
  drafts, 320/390px geometry, scoped profiles and logout passed. Zero page errors,
  chat submissions, financial writes or model calls.
- Image/release-metadata-only plan/apply. Temporal/RLS/queue readbacks passed;
  no access, scaling, provider, budget, ledger or persona changes.
- New LLM spend $0; conservative exposure $14.91264898/$15. Existing budget and
  provider readbacks unchanged. Annotated tag and published Release read back.
- #199 merged on green; six-page PDF reviewed and anonymously downloaded with
  the same checksum. README/submission index link the slides and supplied video.
- [Release evidence](../submission/v0.9.7-release-evidence.md) records commands,
  workflow IDs, digests and limits. Earlier preparation receipts were preserved.

## Done but not verified

- No fresh model/financial action test; unchanged API explicitly inherits v0.9.4
  evidence. No populated live packet or Safari/physical-device check.
- Video playback/duration not measured; its URL is owner-supplied.

## Next / blocked

- Stop and await Sebastian's explicit go for v1.0.0 on the deployed SHA.
- No email sent. Official v4 unchanged; no held-out replay or new score.

# 2026-10-05 — AI final-day conversation fixes

## Completed (verified)

- Classified the four saved live failures and fixed repeated literal merchant
  reads in pending choices. The [lane fragment](progress.d/2026-10-05-ai-final-day-conversation.md)
  records 215 passing mock regressions, frozen 27/30, B1 32/32 and $0 new spend.

## Done but not verified

- Remote CI, lead review and a new deployed live score remain pending.

## Next / blocked

- Small feature PR for lead review; one approved <=$0.40 live rerun follows the
  lead's deployment and exact-SHA/new-scope signal. Official v4 stays unchanged.

# 2026-10-05 — AI pending-dispute follow-up

## Completed (verified)

- Opened #204 for repeated merchant reads; replayed and fixed JE-17's additional
  selection-round consumption without inventing a target. The
  [lane fragment](progress.d/2026-10-05-ai-pending-dispute-followup.md) records
  197 passing mock regressions, frozen 27/30, B1 v2 32/32 and $0 new spend.

## Done but not verified

- Second PR's remote CI, lead review/deployment and new live results are pending.

## Next / blocked

- Lead owns the merge/release batch. One newly approved <=$0.40 live rerun follows
  its exact deployed SHA and new durable AI scope; official v4 stays unchanged.

## 2026-10-05 — Final-build regression (lead)

### Completed (verified)

- #202/#204 (including #205)/#203/#206 merged with four remote checks green.
- Updated six-page slides reviewed; $18 ceiling and separate durable $0.30/$0.40 scopes verified.
- Controlled replay COMPLETE: P 89/100, B1 60/100, flagged subset 4/8 and 2/8; charged $0.23744950. [Full counts and cost evidence](../evaluation/final-build-regression.md).
- Official v4 files byte-unchanged. No new unknown cost; zero-case/$0 mock stop preserved.

### Done but not verified

- v0.9.8 Azure deployment and final-day AI live exploration are prepared, not yet run.

### Next / blocked

- Green docs CI, image-only v0.9.8 release, deterministic live gate, then signal AI.
- Await the single $0.40 live result; v1.0.0 tag on the deployed SHA is owner-approved. Never email.

## 2026-10-05 — AI exact merchant resolution

### Completed (verified)

- Exact owned merchant identity and JE-11 collection context implemented;
  mock **29/30**, all safety controls pass, B1 **32/32**, new spend **$0**.
  [Lane fragment](progress.d/2026-10-05-ai-exact-merchant-resolution.md).

### Done but not verified

- Remote CI, lead deployment and real-model confidence benefit remain pending.

### Next / blocked

- Lead review; main hold unchanged. One same-19 live run awaits deployed SHA
  and new scope/run, capped at the newly approved $0.15. Official v4 unchanged.
