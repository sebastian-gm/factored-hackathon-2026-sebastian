# Phone candidate choices — 2026-10-04

## Completed (verified)

- Reviewed and applied the AI lane's supplied `phone-choice-viewport-proposed.patch`
  on a new branch from `origin/main` (`edd3070`). Credit: AI lane proposal and
  initial tests; frontend lane review and independent validation.
- Customer chat scrolls the candidate grid into view, retaining decision/receipt
  fallbacks and the pending-confirmation guard.
- The regression waits for exactly three choices and checks every button's full
  phone viewport bounds in ES and PT. Selecting a choice still opens a separate
  confirmation dialog without issuing a confirm request. Accessibility and
  horizontal overflow assertions remain in place.
- `cd apps/web && pnpm test:e2e tests/judge-ux.spec.ts --grep 'phone choices' --repeat-each=3`:
  six passes at 390 × 844. `pnpm test:e2e tests/judge-ux.spec.ts`: 19 passes,
  including desktop/phone, offer actions, retry and authority boundaries.
- `pnpm typecheck`, `pnpm lint` and `git diff --check` passed. All browser runs
  used local project-authored fixtures; zero paid calls or cloud changes.

## Done but not verified

- Remote CI for this new branch is pending publication of its small held PR.
- Deployed judge access remains unopened; owner-network and GitHub-runner live
  tours still await the lead's access signal and approved cost adapter.

## Next / blocked

- Keep the PR held for the lead's v0.9.1 review and merge order; auto-merge stays
  off. Repository publication is approved. Official v4 evidence is unchanged.
