# Pre-v4 integration review (2026-10-01 UTC)

Main remains `2dfa50408547c001140764f782562e63ebfdede7`. This review concerns the
private `integration/pre-v4-freeze` candidate, not a release or a final run.
No paid calls, cloud changes, v4 row access or historical result changes.

## AI round-two PR #85

Reviewed the eleven commits through
`83be37164c4470ac04882f1debafaf943d908322`, including production diffs, study
accounting, reports and authored regressions. Frozen conversation definitions,
builders, model-comparison selection and slot annotations were not opened for
diagnosis or tuning; no v4 rows, selections or bindings were opened.

| Area | Review conclusion |
| --- | --- |
| Spoken dates/currency | Additive parsing of an explicit day and month; impossible dates, absent month and unsupported units remain unresolved. No guess from the customer's country. |
| Offer refusal | AI correctly separates a refusal from recognition. Lead orchestration still failed that path; fresh authored reproduction and PR #92 repair are documented in [live-rehearsal-triage.md](live-rehearsal-triage.md). |
| Typed provider failure | Safe numeric failure codes preserve validated billing and generation identity; no provider prose/keys. Settlement precedes a stopping audit callback, including parallel Jev accounting. |
| Comparison stop | Initial `provider_402` versus `http_402` gap was confirmed and relayed. Corrected head stops both code families for 401/402/403/429, including known-cost HTTP-200 envelopes, before retry/fallback. Authored tests passed. |
| Same-path comparison | Challenger-only opt-in retains Jev union; mock routes never call it. Actual model/fallback identity is recorded. No production model or risk default change. |
| Lean prompt | v5.2 is a prepared candidate only. Production remains v5.1; incomplete comparisons cannot satisfy the adoption gate. |
| Quality/cost claims | Partial paired study: 30/50 completed pairs, both 25/30 pass and 19/28 in-scope SAR. Unequal round-two before/after denominators are explicitly disclosed; common 47 cases remain 9/47 for both. Unknown bills retain reserves; no balance-delta cost claim. No further comparison spend. |

The study reports substantial remaining lead-owned limitations: descriptive
candidate corrections, carrying unfamiliarity across early clarification,
compound existing-case/new-charge requests and two independent charge concerns.
The source confirms that candidate state accepts an ordinal but skips another
NLU extraction; the early NLU-clarification return precedes unfamiliarity retention.
The two-round mixed-language limit and colloquial amount-unit meaning also need
contract adjudication, without changing frozen gold. The small cancellation
repair does not claim these broader problems solved. Real round-two baseline
15/60 is development evidence, not a v4 readiness or accuracy claim.

## Lead and frontend boundaries

- #90: localized fallback status, persisted selected handle, same-conversation
  scoped facts and read-backed handoff/dispute actions; live Desk wall time and
  explicit empty-facts explanation. No confirmation/OTP/policy/MATCH change.
- #91: free account/key credit gate and exact local-serving launch checklist;
  no budget preparation, suite preparation or worker launch executed.
- #92: explicit polite refusal cancels the offered dispute, actual recollection
  still explains, isolated assent still clarifies. Authored mock regressions only.
- Live AI phrase corruption/status and transaction-kind alias fixes are pending.
  Frontend story helper currently excludes Ops-role live personas; API ambiguity
  gating also correctly omits the PT hint when there is only one displayable
  merchant. Keep the data gate; do not fabricate movements or enable unsupported
  stories. Frontend/data lane owns the coordinated helper/binding review.

## Commands actually run

Command receipts and raw local logs are ignored, mode 0600 under
`artifacts/integration/checks/`. All models mocked and real-call approval off.

| Command | Verified result |
| --- | --- |
| `.venv/bin/pytest -q` on parent `0a459e9` | 579 passed / 22 skipped; counts from pytest progress marks; exit 0 |
| `.venv/bin/python -m scripts.test_postgres` | 30 passed; disposable non-owner RLS, restart and serving checks |
| `pytest tests/test_offer_refusal_state.py tests/test_nlu_round2_regressions.py tests/test_conversation_v3.py` | 50 passed after the cancellation repair |
| `pnpm --dir apps/web test:e2e` | 93 passed |
| `pnpm --dir apps/web test:e2e --live` | 12 passed, real local BFF/API |
| `pnpm --dir apps/web test:e2e --staff` | 1 passed, real local BFF/API |
| `pnpm --dir apps/web typecheck`, `lint`, `build` | All exit 0 |
| `.venv/bin/pre-commit run --all-files`, Ruff, strict mypy, compile | All exit 0; strict mypy covers 88 files |
| Interface and policy catalog `--check`; working-tree staged-file policy | All exit 0 |
| `python -m evals.runner --system B1` | Exit 0; standard safety harness |
| `python -m evals.runner --system B1 --scenarios evals/dev_scenarios_v2.yaml --output artifacts/integration/b1-pre-v4` | 32/32 passed |

These are local implementation gates, not Azure verification or a new real-model
quality measurement. Generated browser references and B1 Markdown were restored;
official result pages remain unchanged. Remote CI is held for the complete
candidate to preserve the owner's single-run requirement. Main merge/release,
new capped real smoke and feature freeze follow reviewed closure of live blockers.

## Subsequent PR review and cumulative preflight

- #88 `a3f54d3`: original live failure observations, project-authored messages and
  aggregate timing/cost receipts only; no organizer values, operational IDs or
  credentials. Integrated without claiming the failed PT draft was repaired.
- #86 `3d86622`: supporting aggregate disparity analysis, checked against official
  v3 ES/PT/strict-transfer figures and caveats. No result/gold/scorer change.
- #93 `8d3ac42`: original corruption is rejected, source status/type display facts
  localize and raw kind aliases canonicalize without threshold changes. Held for
  three zero-cost corrections sent to the AI lane: the actual
  `awaiting_dispute_decision` machine enum is not rejected; an uncited merchant
  `Approved` is exempted/counted as cited through a status citation; private
  replay snapshots/reports are created with default permissions rather than 0600.
  Authored source-only replays reproduced both guard gaps; no frozen row or paid
  run. Stacked base now `integration/pre-v4-freeze` so corrections use local checks.
- Fresh `scripts.pre_v4_budget` readback: $6.99994254 current charged/reserved;
  conservative full dev + v4 + smoke allowances $11.82845477 ≤ $12. No budgets
  changed and no unknown reserves released. Recheck after release/before launch.

The frontend video-readiness PR and corrected #93 head are still pending. Main
remote CI will run once on the complete candidate. Release has standing approval;
feature freeze and v4 GO remain separate, after the owner's live rehearsal.

## Release helper arithmetic correction

The existing release helper would count current pre-v4 dev charges and then add
its full $1 allowance again, yielding $12.69994254 and refusing a release that
passes the shared preflight. Its aggregate SQL now reads total and pre-v4 charged
exposure in one snapshot and includes that spend inside the full $1 allowance.
All historical/production/comparison charges, comparison's full $1.50 allowance,
$3 v4 and both $0.10 smokes remain counted. No record, reserve or cap is changed.

Authored budget boundaries: **19 passed / 9 Postgres-dependent skips**. Invalid,
overspent dev or above-$12 exposure fails; the exact ceiling passes. Read-only
`release_smoke_budget.verify(..., prepare=False)` on the existing deployed SHA's
purse succeeded: unchanged $0.10 cap, 19 attempts, $0.01627249 charged, zero unknown
costs; total $6.99994254 and corrected conservative maximum $11.82845477. Private
numeric receipt: `artifacts/azure/release-budget-counting-readonly.json`. No new
purse was created and no model call occurred.
