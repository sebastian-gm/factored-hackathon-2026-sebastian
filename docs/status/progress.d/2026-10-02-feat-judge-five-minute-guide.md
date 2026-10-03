# 2026-10-02 — Five-minute judge guide

## Completed (verified)

- Added a collapsed, keyboard-accessible **Prueba esto / Experimente** panel
  only for authenticated, selected judge profiles. Six ES/PT authored examples
  fill and focus the composer, then collapse; clicks never send requests or
  confirm writes. Pending actions/read uncertainty disable the examples.
- Added collapsed judge-only rule IDs in the Why drawer and a matching README
  guide covering explanation/offer, explicit denial, approximate amounts,
  lost-card help, human handoff and injection refusal. The guide distinguishes
  action confirmation/OTP/read-back from drafting, and customer from staff access.
- `pnpm --dir apps/web build`, `typecheck`, `lint`, changed-web-file Prettier
  checks and `git diff --check` passed. Production-build Playwright with
  `FRONTEND_E2E_PRODUCTION=1`, lane ports `3268/8268`, `LLM_PROVIDER=mock` and
  `LLM_REAL_CALLS_APPROVED=0`: **171 fixture + 12 mock live + 1 staff = 184 passed**.
  Eight new judge-guide tests cover draft-only clicks, keyboard/focus, profile
  changes, pending locks, Why IDs and separate confirmation/OTP/receipt steps.
- Audited eight collapsed/expanded ES/PT captures at desktop 1440 and phone 390
  under ignored `artifacts/ux-audit/judge-five-minute-guide/` (0600 files).
  WCAG A/AA scans of those states found **zero Axe violations**, with no
  horizontal overflow. Screenshots contain authored fixture UI only.
- Model spend **$0**. No real-model, organizer, Azure or held-out-suite runs.
  Post-v4 UI/documentation only; not reflected in official v4 measurements.

## Done but not verified

- Remote CI and Azure deployment pending at authoring time. No real-model
  rehearsal performed. The staff realm queue remains on the separate #138
  stack, and the README labels its release dependency explicitly.

## Next / blocked

- Open the PR into main and wait for required remote CI. **Leave it unmerged**
  during the v0.8.0 release hold (main pinned at `a8d9993`). Judge-access activation
  remains owner-controlled. No shared progress-log edits.
