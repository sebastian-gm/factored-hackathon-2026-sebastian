## Final-build regression adapter — October 5

### Completed (verified)

- The controlled zero-cost rehearsal stopped before completing its first case:
  AttributeError at the API trusted-country repository lookup. The overlay
  adapter did not expose the bound customer's already verified attributes.
- Eval-only correction exposes that customer alone and fails closed if absent.
  Source reads retain their scoped merge/forced-RLS path; no product, prompt,
  configuration, suite, binding or official v4 output changed.
- Authored MX/BR fixtures exercise B1 and mock P API calls and foreign-customer
  denial. No model calls or spend were made in diagnosis.

### Done but not verified

- Fresh remote CI and the complete zero-cost replay await this PR's merge.

### Next / blocked

- Preserve the zero-case/$0 mock stop, then verify the current adapter end to end
  before the single owner-approved $0.30 real regression. Official v4 unchanged.
