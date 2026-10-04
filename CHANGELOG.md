# Changelog

All notable changes to Aclara are documented here, following Keep a Changelog
and semantic versioning. Versions describe released behavior, not safety
certification. The v0.1.0–v0.5.0 annotated tags and GitHub Releases were created
**retroactively on 2026-10-01**; their commits retain their original dates.

## [v0.9.6] — 2026-10-04

- Preserve the phone chat avatar while English notice text wraps.
- Local 13/13 checks; live ES/PT 320/390px geometry, scoped access and logout verified.
- Image-only release, $0 new LLM spend, unchanged API evidence inherited; official
  v4 unchanged. [Evidence](docs/submission/v0.9.6-release-evidence.md).

## [v0.9.5] — 2026-10-04

- English reviewer UI, reason-based staff guidance and rule labels; ES/PT customer
  conversation language remains scoped to the selected bank profile.
- Verified desktop/390px English smoke, scoped profile/logout readbacks and exact
  SHA CI/safety/access. Image-only release; unchanged API digest.
- New model spend $0; v0.9.4 real-model evidence explicitly inherited. Official v4
  unchanged. [Release evidence](docs/submission/v0.9.5-release-evidence.md).

## [Unreleased]

- Renamed the original development repository to the submission name, retaining
  its branches, PRs, CI and evaluation chronology. Archived the former snapshot
  privately without deleting it.
- Post-v4 fixes are disclosed separately and do not change official v4 scores.
- Every change now uses a feature branch and PR; every Azure release gets a tag.
- `v1.0.0` is reserved for the exact submission-day Azure release SHA.

## [0.9.4] — 2026-10-04, verified judge quick-start (post-v4)

- Date-free scoped ES/PT drafts, absent merchant normalization and opaque case-ID
  language evidence. Thresholds, ownership, Send/OTP/confirmation unchanged.
- Deployed/tagged `d39140265714b4e112e259aff7fcfaf79ac60771`;
  exact-SHA CI/safety/access, ready images and security/data controls passed.
- Real FIRST reply: ES explanation, PT explanation. Bare unfamiliarity then shows
  one owned choice; one click reaches the same-target dispute offer. No writes.
- One stopped operator and one owner-approved extra attempt preserved: six known
  calls cost $0.0115005 total; no new unknown reserve, budget or counter reset.
- [Verified evidence and limits](docs/submission/v0.9.4-release-evidence.md).

## [0.9.3] — 2026-10-04, scoped judge-story drafts (post-v4)

- Scoped ledger quick-start, conservative target corrections and pending-choice
  recognition context; explicit Send and separate confirmation are preserved.
- Deployed/tagged `63e69b674a91d43be3e304c9b6e7291ea656e0ce`; exact-SHA
  CI/safety/access, ready images and scoped data/queue controls passed.
- Known live defect: the first ES quick-start clarified instead of explaining;
  displayed date can conflict with process date. Cost $0.0021315, settled;
  PT and explanation→offer were not verified. Owner accepted this release
  as-is; v0.9.4 addresses the starter separately. Official v4 unchanged.
- [Evidence and preserved operator stops](docs/submission/v0.9.3-release-evidence.md).

## [0.9.2] — 2026-10-04, judge own-visit staff queue (post-v4)

- One judge password/OTP visit can open its masked queue and claim handoffs
  directly in Agent Desk; no second staff credential is needed.
- Queue-only delegation preserves customer/role scope; other visits and owner
  invitations are denied. Profile switching/restart preserves membership;
  logout, expiry, judge OFF and credential/config/binding rotation revoke it.
- Auth revalidation under the controller lock prevents a profile-switch race
  from consuming an invitation. Normal external staff flow is preserved.
- Deployed/tagged `f9d1796ddd661883c131359c1881bea67f9a0c49`; exact-SHA
  CI/safety/access and live ES/PT queue/claim/browser checks passed.
- Smoke $0.003879; browser $0 with a $0.01 verifier-stop reserve retained.
  Image-only release; official v4 results remain unchanged.
- [Verified evidence, commands and operator disclosures](docs/submission/v0.9.2-release-evidence.md).

## [0.9.1] — 2026-10-04, judge conversation and tour (post-v4)

- Scoped latest-case status and verified readbacks; contextual follow-ups,
  courtesy and ES/PT reply-language changes preserve action confirmation.
- Corrections use grounded positive details; negated dates cannot select a charge,
  and rejected corrections reach the existing clarification/handoff limit.
- CO/AR quick-start stories keep the selected customer profile; explicit
  cross-profile recording shortcuts still use trusted server profile selection.
- Accessible judge invitation, numbered choices, phone layouts and private tour
  tooling; completed post-hoc human agreement is linked separately from v4.
- Repository publication was explicitly approved and verified on October 4,
  with PR/check protection on main. `v1.0.0` and email remain pending approval.
- Official v4 results are unchanged. This batch does not change warm/burst
  settings, judge access, CPU or budget binding. Deployed/tagged `0f0e12df13e281538d7b25800f56c55da0b8dc0b`;
  two live ES/PT stories verified; smoke $0.007624, browser $0.
- [Verified release evidence and operator disclosures](docs/submission/v0.9.1-release-evidence.md).

## [0.9.0] — 2026-10-03 COT, judge go-live (post-v4)

- Deployed/tagged `edd30702f32b21af17fc353d0ee410e67b2e932b`; CI, safety and authenticated
  independent-runner access green at that SHA. Official v4 numbers unchanged.
- Approved warm min=1, API max=3 / HTTP concurrency=5; unchanged CPU/memory/worker.
  Public HTTPS web with judge login/picker, API internal; trusted source roles
  accepted without weakening identity/cookie/expiry validation.
- Production $1/UTC day plus $1.60 lifetime judging limit; separate durable
  $0.10/$0.30/$0.20 operator scopes, conservative maximum $14.96326498 / $15.
- Backed up/reset four owner maps; two judge visits filed the same story with
  isolated receipts. Staff claim and password rotation/restoration verified.
- Six provider calls cost $0.0115855; another $0.03 attribution reserve retained.
  Browser adapter failures and follow-up checks disclosed; no paid filing replay.
- Repository private; Gate C publication/v1.0.0/email needs Sebastian's final go.
- [Evidence, costs and limits](docs/submission/go-live-2026-10-03.md).

## [0.8.1] — 2026-10-02 COT, staff queue and monetary privacy (post-v4)

- Deployed `3bc06d0db1c9b38233c04558f8093ce956258ab2`; #138/#147/#149 integrated through green #150.
- Current-controller validation revokes delegated staff access on judge OFF,
  rotation, expiry/logout and changed binding, including cached claims.
- Additive FORCE-RLS queue: independently verified one-winner claims, immutable
  packet/realm; no bank/transcript/trace authority granted.
- Guide examples draft only; monetary digit redaction has no exemptions;
  unambiguous money recovered locally. Identifier/multiple amounts clarify.
- Existing large-COP dispute/readback/retry, concurrent ES/PT attribution,
  deterministic fraud, staff invitation/claim/revocation and three surfaces passed.
- Smoke $0.00776 / $0.10; 4 provider calls; maximum allocation
  $14.96326498 / $15 including retained allowances and OFF judging proposal.
- Judge/public/scaling remain OFF; no deletion/reload/rebind. Official v4 unchanged.
- [Verified evidence and limits](docs/evaluation/v0.8.1-release-notes.md).

## [0.8.0] — 2026-10-02 COT, concurrent chat (post-v4)

- Deployed `2573e1d8367de20574935fce8f7624eb7dae33a9`: request-scoped events, AI cursor and provider records;
  removed process-wide chat serialization, preserving full-turn session advisory
  locks, scoped storage and atomic model budget reservations.
- Local warm five-session, 1-second mock NLU: 1.025696-second wall, turn
  p50/p95 1.020226/1.022139 seconds; separate cold evidence disclosed.
- Live ES/PT first turns overlap with disjoint provider records/languages;
  filing/readback/retry, ambiguity, fraud and Customer/Desk/Ops gates passed.
- Independent judge visits now get distinct bank realms; judge access remains
  OFF and live realm checks are deferred to Gate B. Authored/CI evidence passed.
- First deployment rejected two chats before NLU due to an empty environment
  DSN guard. #146 fixes one condition; all zero-call attempts and counters remain.
- Smoke $0.011353 / $0.10, 6 calls, zero unknown costs; conservative
  cumulative $12.39795698 / $15. No Azure deletion, reload, rebinding or scale/access
  change. Gate A scaling is prepared and OFF; #138 staff queue is excluded.
- [Evidence and limits](docs/evaluation/v0.8-release-notes.md). Official v4 unchanged.

## [0.7.0] — 2026-10-02, temporal-quality release (post-v4)

- Deployed `e7c6b552dec0006c4f36e02188764dcf554942e2`, then atomically reloaded
  source-verified gold: 492,414 transactions retained, 60,920 flagged. Nullable
  temporal column, promotion fingerprint, TLS and FORCE RLS asserted.
- DQ-01 allows explanations and blocks automatic disputes on temporal anomalies
  or unavailable checks. Azure flag rehearsal was **not exercised live: no demo
  persona owns a flagged transaction**; authored API/Postgres and CI cover it.
- CO filing/readback/retry, PT ambiguity, fraud handoff, six benign browser
  phrases, existing MX receipts across logins, basic-mode display and three
  surfaces verified. No Azure record deletion or persona rebinding.
- Smoke **$0.023339 / $0.10**, 12 calls, zero unknown smoke costs. Conservative
  exposure including retained allowances/reserves **$12.00271348 / $15**.
- Warm-only Gate A plan prepared and OFF; min=0/max=1 and owner-only access
  unchanged. Official v4 results unchanged. [Evidence](docs/evaluation/v0.7-release-notes.md).

## [0.6.0] — 2026-10-02, audit hardening (post-v4)

### Fixed

- Customer-scoped case/card state across logins and read-only original receipts
  after lost confirmations; separate judge profile business realms.
- Budget-denied NLU degrades safely, trusted country context and narrower ES/PT
  access/legal guards. Deterministic explanations block unverified action claims.
- Reason-specific handoff guidance, redacted request/clarification history and
  slot-specific questions. NLU runs outside scoped DB storage with revalidation.
- Private staff/judge login catalogs, 35-minute normal sessions, non-root API,
  explicit freeze readback errors and per-turn metadata logging.

### Changed

- Live Jev second opinion is off by explicit config; historical dual-judge/study
  evidence remains. BFF admission limits bound auth/chat attempts.
- Release smoke checks Jev-off routing, existing bank state and receipt retries.
- These changes are **not reflected in official v4 numbers**. Deployment evidence
  and the exact SHA/digests accompany the verified annotated tag at `f5e128d`.
  [Release evidence](docs/evaluation/v0.6-release-notes.md).

## [0.5.0] — post-v4 release (`b8c1305`)

### Fixed

- Preserved concurrent human-request reasons on fraud/legal handoffs, clarified
  recognition versus inability to identify a charge, and instrumented committed
  case-status readbacks. These fixes were **not reflected in v4 numbers**.

### Added

- Official v4 results, post-hoc safety analysis, and offline human-sheet tooling.

Evidence: [post-v4 release notes](docs/evaluation/post-v4-release-notes.md).

## [0.4.0] — v4 feature freeze (`92994d9`)

### Changed

- Corrected live ES/PT phrasing, transaction-kind normalization, Desk SLA clock,
  handoff facts/actions and guided demo story gating before the feature freeze.
- V4 evaluated this product freeze. Evaluation-interface-only repairs produced
  a later evaluated SHA; both preflight attempts are disclosed in the results.

### Measured

- Fresh 100-case v4: B1/P pass 62/88, SAR 22/32; paired +10 pp (95% CI +5 to +16).
- P strict escalation 49/53, materially incorrect 0/100, repeat flips **0/30**.
- Safety gates still failed: two unauthorized-action flags and four missing
  status verification events. Do not interpret aggregate pass as acceptance.

Evidence: [official v4 results](docs/evaluation/final-v4-results.md),
[safety analysis](docs/evaluation/final-v4-safety-analysis.md).

## [0.3.0] — v3 release (`e12efc7`)

### Changed

- Implemented explain → offer → dispute, multi-reason handoffs and generic
  evaluation contract repairs. Product freeze and post-freeze template snippet
  exposure are disclosed; no held-out improvement is claimed from later fixes.

### Measured

- V3 B1/P pass 52/77, SAR 28/39; safety gates failed. All 260 system runs were
  checkpointed; judges remained partial (28/60 items), disclosed in the results.

Evidence: [official v3 results](docs/evaluation/final-v3-results.md).

## [0.2.0] — v2 evaluation release (`fd34c7d`)

### Added

- Resumable final program, durable reserve-before-call spend budgets, matcher
  v2, Gemini production wiring, Jev risk second opinion and independent judges.

### Measured

- Completed v2: B1/Gemini/Sonnet pass 65/200, 63/200, 37/100. SAR 41/193,
  39/193, 26/98. No system passed all safety gates. V1 was abandoned, preserved
  untouched; v2 remains the official historical result without post-hoc rescoring.

Evidence: [v2 analysis](docs/evaluation/final-v2-error-analysis.md),
[chronology](docs/evaluation/final-v4-results.md).

## [0.1.0] — first working B1 vertical slice (`c2111aa`)

### Added

- Local Compose Postgres/FastAPI/Next.js, login + simulated OTP, scoped fixture
  transactions, ES/PT rules NLU, policy, confirmed dispute with readback, handoff
  packet, minimal chat, 32-case B1 harness and aggregate-only P1 pipeline.
- Scaffold, traceability, pre-commit data/secrets/size gates and CI workflows.

Evidence: the verified initial progress log at
[7680288](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/blob/7680288/docs/status/progress-log.md)
identifies the four slice commits and actual local verification. No Azure or real
model run was claimed at that milestone.
