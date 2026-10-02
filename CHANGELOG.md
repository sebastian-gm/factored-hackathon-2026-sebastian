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
