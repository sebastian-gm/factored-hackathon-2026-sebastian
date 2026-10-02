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
omitted closed-scope exposure. This was the pre-v0.7 readback; it is not a
current live balance. See the executed smoke below.

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

## Executed v0.7.0 smoke — October 2

- SHA-bound production run `pre-v4-release-e7c6b552dec0006c4f36e02188764dcf554942e2`:
  **12 calls, $0.023339 / $0.10**, zero unknown smoke costs. History retained.
- Key readback **$5.1618465 → $5.1385075**, exactly matching the charge; no key
  increase or account top-up. All-scope known cost **$5.99020934**; actual ledger
  exposure with retained reservations **$7.71952784**.
- Conservative unused-allowance/reserve exposure **$12.00271348 / $15**.
  With remaining smoke **$0.076661** and proposed judging lifetime **$2.92**,
  worst allocation **$14.99937448**. Proposed global $1/UTC-day judging cap is OFF.
- Scope/model/key breakers remain independent. New tests/follow-up use mock
  only. [Release evidence and limitations](../evaluation/v0.7-release-notes.md).

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
