# Go-live budget controls — October 3

## Completed (verified)

- Free readback: OpenRouter account $8.830448454, prod key $4.9742135. Existing known $6.15450334; retained exposure $7.88382184; 64 unknown reservations preserved.
- Fresh East US 2 rates: idle CPU $0.000003/vCPU-second, active CPU $0.000024, memory $0.000003/GiB-second. Prior prepared burst upper estimate about $62.93/month; Gate A window and burst approved in handoff 19.

- Local commands: `make checks` — 1,630 passed / 43 skipped, B1 32/32; `scripts.test_postgres` — 105 passed; Terraform validate + 14 mocked plan tests; `pnpm test:e2e --judge-roles` — 2 actual-BFF Ops/Agent tests, typecheck/lint passed.
- Corrected BFF rejection of trusted profile Ops/Agent roles; retained identity equality, profile and expiry verification. Separate action/OTP flows unchanged.

## Done but not verified

- Gate B correction: real judge requires $1/UTC-day and `judging-2026-10` lifetime binding. Defaults remain OFF; public web only, internal API, one worker, unchanged CPU/memory.
- Separate operator scopes `go-live/2026-10-03/lead` ($0.10), `/ai` ($0.30), `/frontend` ($0.20); each run ID `2026-10-03`. Reserve conservative request maximum before BFF; settle only independently read per-turn call metadata. Unknown cost retains reserve and stops that lane. No client budget override.
- Lifetime judging production run $1.60; fresh owner release purse $0.10. Lane reservations are counted in addition to production, deliberately conservative. $12.40571698 + $0.257548 historical unused + $0.10 release + $0.60 lanes + $1.60 judging = $14.96326498 <= $15. No history reset.

## Next / blocked

- Require green CI, then release v0.9.0, apply approved Gate A/B, backed-up owner reset and live judge gates. Gate C remains prepare-only.
