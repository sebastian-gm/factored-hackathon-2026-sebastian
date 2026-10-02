# Changelog

All notable changes to Aclara are documented here, following Keep a Changelog
and semantic versioning. Versions describe released behavior, not safety
certification. The v0.1.0–v0.5.0 annotated tags and GitHub Releases were created
**retroactively on 2026-10-01**; their commits retain their original dates.

## [Unreleased]

- Renamed the original development repository to the submission name, retaining
  its branches, PRs, CI and evaluation chronology. Archived the former snapshot
  privately without deleting it.
- Post-v4 fixes are disclosed separately and do not change official v4 scores.
- Every change now uses a feature branch and PR; every Azure release gets a tag.
- `v1.0.0` is reserved for the exact submission-day Azure release SHA.
- Follow-up, not deployed in v0.7.0: independent shared-account judge visits get
  separate case/card realms; approved owner reset clears the durable bank maps
  as well as its session workspace. Both modes remain OFF on Azure.

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
