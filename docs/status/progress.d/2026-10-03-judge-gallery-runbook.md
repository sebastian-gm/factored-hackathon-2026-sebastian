# Judge gallery and operator runbook — 2026-10-03

## Completed (verified)

- Generated a private ignored gallery with 213 desktop/phone screenshots. Full
  screenshots and actual-scroll viewport captures cover ES/PT OTP, explanation,
  Why, clarification, case receipt, handoff/freeze, Desk claim, Insights and Ops.
  The gallery itself has no overflow at 320, 390 or 1440px.
- Local tour: 28/28 checks; eight affected story/Desk checks and final phone
  OTP/expiry check passed. Across 101 screen audits: zero axe violations or
  horizontal overflow. The 32 current request-metric files record zero application
  exceptions; one legacy-format metric file is excluded from that count.
- Aggregate-only Lighthouse: accessibility 100/100 desktop/mobile, performance
  69/70, best practices 96, SEO 100, CLS 0. Development-server timing only;
  signed-out /me resource errors are expected. No paid model calls.
- Added README commands, an operator runbook and a lead-owned runner workflow
  template under apps/web/ci. YAML/default/no-upload checks and script syntax
  passed. Private operator reservations are mandatory for paid dispatches.
- Combined local preparation branch passed web typecheck, lint and production
  build. Conditional Python operator dependencies are included in the runner
  template; actual shared workflows remain untouched.
- Measured after the final evaluation; v4 and all official result numbers unchanged.

## Done but not verified

- Exact-head remote CI pending. Workflow installation, private live credentials,
  operator adapter/binding and deployed owner/GitHub execution are not completed.
- Local demo lacks judge picker and separate staff identity; candidate selection
  is explicitly unverified where the serving ledger returns clarification.

## Next / blocked

- Keep PRs open under the release merge hold. Merge harness before its companion
  journey PR after the user lifts the hold and fresh required checks are green.
- Lead installs/reviews the runner template in its shared workflow lane. Run live
  only after the user opens access, with exact SHA and shared $0.20 frontend scope.
