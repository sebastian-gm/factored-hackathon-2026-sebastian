# Model budget approval ledger

Historical evaluation results and their approval receipts stay unchanged. This
ledger records owner authorization; it does not settle unknown charges or raise
a provider key limit. Reserve-before-call Postgres accounting remains authoritative
for spend and includes outstanding/unknown-cost reservations.

| Approval date | Owner decision | Allowed purpose | Ceiling |
|---|---|---|---|
| Before October 2, 2026 | Previous cumulative approval | Development, final evaluations and approved release smokes | $12.00 |
| October 2, 2026 | Sebastian approved **+$3.00** in this session | Final release smoke and judging window | **$15.00 cumulative**, including reserves |
| October 5, 2026 | Sebastian approved **+$3.00** in handoff 20 | Post-v4 final-build regression replay, live exploration and remaining judging window | **$18.00 cumulative**, including reserves |

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
submission-day approval. See the [runbook](../../submission/submission-day-runbook.md).

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

## Final-day approval — October 5

The current conservative ceiling is **$18.00**, superseding $15 for new operator
readbacks. Historical evaluation caps and official results remain unchanged.
Production remains **$1 per UTC day**, with its existing $1.60 judging lifetime
run; the provider key's independent limit remains the hard stop. No key limit,
Azure setting, reservation or unknown charge changes with this approval.

New, separate lifetime scopes (never reset or re-enabled by preparation):

- `regression/final-build/v4`, run `final-build`: **$0.30**, for one P replay of
  all 100 v4 cases, with the eight previously flagged cases first and reported
  as a subset. B1 is zero cost. This is regression on already seen data,
  **not a new held-out evaluation**.
- `live-exploration/final-day`, run `final-build`: **$0.40**, for the AI lane's
  one live judge exploration after deployment. API production accounting also
  applies; counting the lane reserve and API charge is conservative.

The last verified operator maximum was $14.91264898. Adding both full new
allowances gives **$15.61264898 <= $18** before any new calls.
`scripts.final_day_budget --prepare` refreshes every retained reserve and unused
authorized cap before creating either purse; it excludes unused amounts only
for independently verified disabled runs. The live receipt supersedes this
illustrative arithmetic. No email or account top-up is authorized.


## Executed v0.9.8 and authorized v0.9.9 rerun — October 5

The final-build replay charged **$0.23744950/$0.30**; the single live exploration
charged **$0.05621900/$0.40**, with no new unknown reserves. Their combined
recorded cost is **$0.29366850**. The v0.9.8 conservative funded maximum remained
**$15.61264898/$18**, with all 75 historical unknown reservations retained.

The owner subsequently approved one v0.9.9 improvement and a single live rerun
capped at **$0.15**. A fresh durable scope `live-exploration/v0.9.9`, run
`v0.9.9`, has a **$0.15 lifetime and daily cap**, initially zero charge. It does
not reset or reuse the completed journal, raise any prior cap, change the
production $1/UTC-day limit or raise the provider key limit.

Funding includes the prior unused allowances: **$15.61264898 + $0.15 =
$15.76264898 <= $18**. Readback checks each scope/run policy and adds only the
new scope's unused capacity to the refreshed all-scope exposure; spent amounts
are already included there. The trusted operator must reserve before every
request and settle from verified per-turn metadata. Unknown costs retain their
reserve and stop the run. The one paid rerun waits for the new deployment signal.

## 2026-10-05 — final submission live rerun settled

The single authorized `live-exploration/v0.9.9` / `v0.9.9` run completed with **$0.07865600 charged**, all known, against its **$0.15** lifetime cap. No new unknown reserves, retries or budget denials. Its remaining $0.071344 stays included conservatively; authorization for another run is not implied. The lead independently read back the scope and private provider balance/key gates. Production remains $1/UTC-day and the provider-key hard stop is unchanged.

Conservative funded maximum remains **$15.76264898 <= $18**, retaining **75 historical unknown reserves** and unused prior allowances. Final-day own-scope charges total **$0.3723245** (regression $0.2374495 + v0.9.8 live $0.056219 + v0.9.9 live $0.078656). This is not an invoice reconciliation or the global sum, which conservatively duplicates production/lane costs. v1.0.0 tagging and deterministic public verification used no further model calls.

## October 5 — independent v5 preparation (handoff 21)

Sebastian approved one **≤ $1.50** durable scope inside the existing **$18**
ceiling, with execution waiting for the explicit “v5 suite merged” GO. Created
and independently read back `final-evaluation-v5` / `final-program-v5`:
**$1.50 lifetime**, **0 attempts**, **$0 known/charged**, **0 v5 unknown costs**.
Conservative maximum is **$15.76264898 + $1.50 = $17.26264898 ≤ $18**; all 75
historical unknown reservations and unused funded allowances remain included.
No cap/reset/closure of prior runs, provider-limit or production-breaker change.
No v5 material was opened and no model call occurred. Refresh budget and provider
balance/key metadata before and after the future one-pass P/B1 run.


## October 5 — independent v5 settled

The one-pass `final-evaluation-v5` / `final-program-v5` run completed: **$0.320539 known/charged**, 157 valid Gemini calls, 0 new unknown reserves, no fallback/case replays. B1 model cost $0. Free before/after account/key readbacks decreased by the same $0.320539. Lifetime cap stays $1.50; unused $1.179461 remains funded. Conservative maximum stays **$17.26264898 ≤ $18**, retaining all 75 historical unknown reservations; prior plus v5 charges is $16.08318798. These are conservative funding figures, not an invoice total. Zero-case shell/preflight startup receipts retained at $0; no old budget history reset. Production/key limits unchanged; no further paid run authorized by completion. See `docs/evaluation/final-v5-results.md` for scores and failed safety gates. Official v4 stays unchanged.

### 2026-10-05 — approved post-v5 safety replay

Handoff 22 authorizes one P replay of seen v5 and v4 (100 each), NOT held-out, under
`regression/post-v5` / `post-v5-final-build`, lifetime **$0.80**. Retired unused
`final-evaluation-v5` capacity **$1.179461**; its $0.320539 charge and all historical
reservations remain intact. `scripts.post_v5_budget --prepare` verified conservative
funding **$16.88318798/$18**, with 75 historical unknown reserves retained. Before
replay, free provider account/key readbacks cover the full purse. No calls yet.
