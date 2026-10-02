# Model budget approval ledger

Historical evaluation results and their approval receipts stay unchanged. This
ledger records owner authorization; it does not settle unknown charges or raise
a provider key limit. Reserve-before-call Postgres accounting remains authoritative
for spend and includes outstanding/unknown-cost reservations.

| Approval date | Owner decision | Allowed purpose | Ceiling |
|---|---|---|---|
| Before October 2, 2026 | Previous cumulative approval | Development, final evaluations and approved release smokes | $12.00 |
| October 2, 2026 | Sebastian approved **+$3.00** in this session | Final release smoke and judging window | **$15.00 cumulative**, including reserves |

## October 2 allocation proposal

The last verified v0.6.0 conservative exposure was **$11.97937448**, comprising
$11.87612498 in conservative allowances/accounting plus $0.10324950 otherwise
omitted closed-scope exposure. No paid call followed in this session. This is the
last verified readback, not a new live balance.

- Remaining against the new ceiling: **$3.02062552**.
- Fresh final-release smoke: retain the existing **$0.10 lifetime** purse and
  its conversation guard. Never reset earlier smoke counters or reservations.
- Proposed judging lifetime allowance: **at most $2.92**, reduced if the fresh
  conservative readback or provider key remaining limit requires it.
- Proposed shared production breaker during judging: **$1 per UTC day** across
  all profiles, workers, retries and providers. This is awaiting approval and
  activation, not a new $1 allowance every day beyond the cumulative ceiling.
- Conservative allocation: **$11.97937448 + $0.10 + $2.92 = $14.99937448**.
  Service availability through October 16 does not authorize $14 in model spend.

The production inference key's own remaining limit is an independent hard stop.
Read its metadata before/after the final smoke; never print keys, raise the key
limit, add credits, bypass a denial, or reroute on account exhaustion. The binding
must enforce both the judging lifetime allowance and the UTC-day cap before
public judge activation. Current testing remains $3/day with the existing capped
smoke binding; no Azure setting or Postgres limit changed to record this approval.

## Execution gates

Refresh all-scope conservative accounting (including retained reserves and
unused approved allowances) before creating a fresh SHA-bound smoke purse.
`scripts.release_smoke_budget` uses the new $15 ceiling; historical v4/dev
preflight ceilings remain $12 so old result provenance is not rewritten.
The release receipt must also include scopes omitted by the legacy helper,
as the submission runbook already requires. Stop above $15 or on a key/budget
denial; use deterministic degradation instead of another paid provider.

Warm replicas, public/judge ingress and publication still need separate
submission-day approval. See the [runbook](../submission/submission-day-runbook.md).
