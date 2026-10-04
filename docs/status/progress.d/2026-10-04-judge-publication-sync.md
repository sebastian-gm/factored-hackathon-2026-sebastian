# Held frontend PR publication sync — 2026-10-04

## Completed (verified)

- Owner lifted the publication hold. GitHub read-back confirms the repository
  is public. Fetch used only origin; main remains edd3070.
- All five frontend PR branches include current origin/main and match their
  remote heads. No source rebase or force-push is necessary; local integration
  merges remain local rather than becoming a large aggregate PR.
- PRs #163, #164, #167 and #168 have successful CI and safety runs on their exact
  heads. Those unchanged, valid results remain in place.
- #173 contains the locally verified ES/PT desktop/phone gallery fixes, healthy
  reply regression and first-time receipt tour. Screenshots remain ignored.
- First remote run passed safety, Python, Postgres and 171 mock UI checks. Its
  local bank-API suite caught an old assertion expecting the removed product
  placeholder. The corrected assertion requires the merchant and no empty field.
- Local bank-API 12/12, staff 13/13 and trusted-role 2/2 browser checks passed with
  mock providers. The correction changes only the regression test.

## Done but not verified

- #173 remote CI is pending. CI runs only for PRs targeting main, so the held
  draft is temporarily targeted at main for validation of its new session head.
  Restore its base to #167 after validation to retain a small review.
- Live owner/GitHub judge tours still require the explicit access-open signal
  and the lead's durable budget adapter. No live or paid model calls were made.

## Next / blocked

- Keep every merge held. The lead owns review and merge order for v0.9.1.
- Verify exact heads and green checks before reporting readiness. Retain draft
  state and disabled auto-merge on #173 while the release batch is held.
- This is post-evaluation development evidence; official v4 results are unchanged.
