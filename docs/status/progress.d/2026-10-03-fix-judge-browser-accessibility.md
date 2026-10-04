# Judge browser accessibility — 2026-10-03

## Completed (verified)

- Read handoffs 17–19, repository rules, recent progress and origin/main. Zero
  model/cloud spend; repository remains private. User's release merge hold is active.
- Fixed sidebar focus contrast (2.03:1 → 13.87:1), cropped phone locale labels,
  visible/accessibility link-name mismatches, small v4 source touch target, lineage
  zoom discoverability and narrow-phone cost-axis wrapping. All numbers unchanged.
- Verified 20 keyboard checks, 16 locale/header checks at 320–1440px, eight explicit
  axe checks, 65 initial and 17 affected fixture browser checks. Web typecheck,
  lint and production build passed. Rebuilt make demo; desktop/mobile Lighthouse
  accessibility both 100, performance 69/70 on the development server.
- Fixed the UI Desk shortcut for Ops-backed judge profiles: judges use the
  invitation panel for a separately signed-in staff session. Two authored MX/PT
  UI regressions passed; BFF selection validation is untouched and lead-owned.
- Private evidence: artifacts/ux-audit/go-live/. Generated screenshots/data are ignored.
  Changes were measured after the final evaluation and do not change v4.

## Done but not verified

- Exact-head remote CI and deployed visual/keyboard evidence pending.
- Lead's Ops-backed BFF profile correction must deploy before live judge checks.

## Next / blocked

- Keep the PR open during the release merge hold; no merge/auto-merge.
- Complete the separate tour/gallery PRs. Live owner/runner checks wait for the
  user's judge-access-open signal and the lead's dedicated $0.20 browser scope.
