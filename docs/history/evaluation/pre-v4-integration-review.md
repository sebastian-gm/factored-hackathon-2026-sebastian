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

## Corrected AI head and video-readiness integration

Reviewed #93 correction `7c7a96a` at zero cost: the reported digit/status prose,
actual `awaiting_dispute_decision` literal and status-only merchant exemption
all fail closed in authored replays. Authored localized-integrity, replay-permission
and kind-normalization tests: **153 passed**. Existing named merchant citations
and 0600 snapshot creation are covered. The NLU merge preserves #85's currency,
spoken-date and quota-stop fixes. Only the progress history conflicted.

Reviewed #94 `93e65a0`: no BFF, confirmation, OTP, proposal or banking-write
behavior changes. Trusted story hints select a login/draft, never authority.
Fixture-only usernames remain gated; missing live hints remain disabled. Numbered
choices send ordinary ordinal text. Recording access only focuses existing opt-in
controls. Retained lead's clock update on configuration changes, frontend's day
format and explicit empty sections, plus live verified-action assertions. Preserved
both progress histories. Local combined gates and Azure verification remain next.

Owner then authorized the lead-owned PT API proposal: choice eligibility requires
two valid movements from the owned, product-joined 120-day projection, without
requiring merchant names. Currency/amount/status and handle remain valid; named
explanation still requires a merchant. No merchant is invented, policy/RLS and
confirmation remain unchanged, and hints do not promise a dispute receipt.

## Combined local acceptance — 2026-10-01 UTC

Product source at `76dd05b` is identical to the integrated `1b51eb4` (only docs
followed). Verified with the same command capture receipts under ignored
`artifacts/integration/checks/`:

- Full `pytest`: **769 passed / 22 optional database skips**.
- `python -m scripts.test_postgres`: **30 passed** on disposable local non-owner
  storage, including RLS, serving, restart, budget and handoff readback tests.
- Full hooks, Ruff, strict mypy, compile, frozen interfaces, policy catalog and
  staged-file policy passed. Web typecheck, lint and build passed.
- B1 safety **32/32**, reactive v2 dev **32/32**. Generated dev report restored;
  official v2/v3 artifacts and figures remain unchanged.
- Browser **124 passed**: 111 authored fixture, 12 local live customer and 1 staff
  check. Initial fixture invocation failed to launch Chromium at a mistakenly
  relative cache path (82 could not launch / 29 non-browser checks passed).
  Absolute repository-local cache rerun passed all 111; no assertion removed.
- Free credit GETs: account **$9.659101954**, key remaining **$5.802867**, both ≥$4.
  Live East US 2 list-price estimate **$34.63/month**, approved assumptions and
  replicas zero unchanged. Current durable exposure **$6.99994254**, maximum
  **$11.82845477** with retained unknowns, full allowances, v4 $3 and both smokes.

These are local/mock and metadata gates. Remote CI, deployed product behavior and
the frontend's fresh live Azure rehearsal are separate acceptance steps. V4
remains unopened/unprepared/unstarted; feature freeze and run GO are pending.

## Accepted Azure release — 2026-10-01 UTC

Release **`92994d933e7e4d4cddbbf988fb4cc748d3cd5db1`**, integrated via #97.
PR CI/safety passed first run (`36806164942` / `36806164802`); automatic exact-main
CI/safety also passed (`36806917133` / `36806917242`). No workflow rerun. Obsolete
#85 was closed after exact-head ancestor verification; its commits are integrated
through #97. Other reviewed PRs were automatically marked merged.

- Private API/web images built/pushed and registry digests verified. API digest
  `sha256:939f9221dc9444474db1e76fd23da0d5934fe1010b1e6024ffbf0775aa9c725f`;
  web `sha256:1118658884edec5879ef73ee2b69d95bf2d1ba1b06d2b231bd5d80d7fa66c85c`.
- Reviewed/apply: **0 added / 2 changed / 0 destroyed**, images/release identity
  plus approved temporary `LLM_BUDGET_RUN_ID` only. CPU/memory, min=0/max=1,
  ingress, identities, secrets, storage and database unchanged. Explicit
  subscription `Seb Azure Sandbox` throughout; no public/judge/warm mode enabled.
- `python -m scripts.azure_verify` passed exact-image and all access/TLS controls.
- `AZURE_RELEASE_SMOKE_RUN_ID=pre-v4-release-<SHA> python -m
  scripts.azure_llm_smoke` passed ES explain→offer→deny→proposal→filing/readback,
  PT ambiguity/handoff and deterministic fraud. **9 valid calls, $0.00813975,
  zero unknowns or fallbacks**. Browser shares that hard $0.10 lifetime purse.
- `python -m scripts.serving_browser --target azure` passed three surfaces,
  verified handoff and resolution. Four conservative attempted conversations;
  no counter reset or extra attempt. Generic mock-only `azure_smoke` is not
  applicable on the real deployment and was not reported as passed.
- Outside-network workflow `36807587445` passed at the release SHA.
- GET-only BFF configuration confirms both ES story hints and the PT choice hint.
  This proves availability; the frontend's full fresh live-story rehearsal remains
  the next gate, including the four formerly observed bugs and actual prose.
- Fresh `artifacts/azure/jev-release.json`: all three acceptance flags true.
  Current exposure **$7.00808229** including retained reserves; conservative max
  **$11.83659452 ≤ $12**, counting full dev/comparison allowances, v4 $3 and both
  smokes. No old reservation or cap reset; no further comparison spend.

Main was clean/equal to origin and released at that exact SHA. This documentation
is published separately on `integration/pre-v4-freeze` so the tested release SHA
stays stable and no redundant main CI is triggered. V4 remains unopened,
unprepared and unstarted. Feature freeze/final GO follow the owner's rehearsal.
