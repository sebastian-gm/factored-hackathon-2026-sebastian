# Model budget approval ledger

Historical evaluation results and their approval receipts stay unchanged. This
ledger records owner authorization; it does not settle unknown charges or raise
a provider key limit. Reserve-before-call Postgres accounting remains authoritative
for spend and includes outstanding/unknown-cost reservations.

| Approval date | Owner decision | Allowed purpose | Ceiling |
|---|---|---|---|
| Before October 2, 2026 | Previous cumulative approval | Development, final evaluations and approved release smokes | $12.00 |
| October 2, 2026 | Sebastian approved **+$3.00** in this session | Final release smoke and judging window | **$15.00 cumulative**, including reserves |

## Historical pre-v0.7 allocation proposal — superseded

The last verified v0.6.0 conservative exposure was **$11.97937448**, comprising
$11.87612498 in conservative allowances/accounting plus $0.10324950 otherwise
omitted closed-scope exposure. This was the pre-v0.7 readback; it is not a
current live balance. See the executed smoke below.

- Remaining against the new ceiling: **$3.02062552**.
- Fresh final-release smoke: retain the existing **$0.10 lifetime** purse and
  its conversation guard. Never reset earlier smoke counters or reservations.
- Historical proposed judging lifetime allowance: **at most $2.92**, reduced if the fresh
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


## Executed v0.8.0 smoke and revised judging proposal

- Deployed `2573e1d8367de20574935fce8f7624eb7dae33a9`; the corrected image retains the original
  `pre-v4-release-a8d9993eecf9895a6ca220e03cdce3df4f34b593` **$0.10 lifetime** purse. Two rejected pre-NLU chats
  cost $0; all eight conversation attempts (including the explicitly approved
  deterministic browser retry), counters and reservations are retained.
- **6 calls / $0.011353**, zero unknown
  smoke costs. Production key remaining **$4.9819735**; key
  decrease **$0.011353**, independently recorded versus the
  durable charge. No key-limit increase or account top-up.
- All-scope known cost **$6.14674334**; actual exposure with
  retained reservations **$7.87606184**.
- Conservative cumulative maximum **$12.39795698**, including unused dev/round
  allowances and the closed-scope exposure omitted by the legacy helper.
- Current smoke remaining **$0.088647** and prior v0.7 remaining **$0.076661**
  stay included; unused capacity is not permission for further model calls.
- Revised judging lifetime proposal **$2.40**, superseding $2.92:
  **$12.39795698 + $0.088647 + $0.076661 + $2.40 = $14.96326498 <= $15**.
  Shared **$1/UTC-day** breaker and judge activation remain OFF, pending Gate B.
  Refresh the math before another release or activation; reduce the lifetime
  proposal as needed without releasing unknown reserves.
- [Release evidence](../evaluation/v0.8-release-notes.md).

## Prepared v0.8.1 allocation — no new calls yet

Read-only check at October 3 01:25 UTC: account remaining **$8.838208454**,
production key remaining **$4.9819735**, known cost **$6.14674334**, retained
exposure **$7.87606184**, conservative maximum **$12.39795698**. All 64 legacy
unknown reservations remain intact; they are not counted as free capacity.

Propose a new **$0.10** SHA-bound release purse, and reduce the OFF judging
lifetime proposal from $2.40 to **$2.30**. Retain both older unused smoke
capacities and all other conservative allowances:

**$12.39795698 + $0.088647 + $0.076661 + $0.10 + $2.30 = $14.96326498 <= $15**.

No new scope, live cap, key limit or Azure setting was changed by this readback.
The real-smoke estimate and owner go remain prerequisites. Refresh again on
the final candidate; the shared **$1/UTC-day** judging breaker remains OFF.

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

## Executed v0.8.1 smoke

Owner-approved fresh `pre-v4-release-3bc06d0db1c9b38233c04558f8093ce956258ab2` $0.10 lifetime purse: **$0.00776**,
**4 provider calls**, **6 attempted conversations**, zero unknown
smoke costs. Key remaining **$4.9742135**; independently
measured decrease **$0.00776**, minus smoke charge
**$0.0**. No key increase, reserve release or history reset.

All-scope known **$6.15450334**, retained exposure
**$7.88382184**, conservative
**$12.40571698**. Include unused capacities from both prior purses and this new
purse, plus OFF judging $2.30: **$14.96326498 <= $15**. All
64 legacy unknown reservations retained.
Judging $1/UTC-day/activation remain OFF pending explicit Gate B go.
See [verified release evidence](../evaluation/v0.8.1-release-notes.md).
