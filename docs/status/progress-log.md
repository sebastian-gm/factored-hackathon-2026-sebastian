# Progress log

## 2026-09-30 PDT — Deployed main; stale Ops smoke selector

### Completed (verified)

- #81 and exact main **6e636d3113e4a1cbaf8a3988cdcf0ba9b75e8d7a** passed CI
  and safety. Main runs **36764627466 / 36764627289** succeeded. Registry
  digests remain identical to the 21dac9e application builds.
- Reviewed app-only Terraform plan/apply: **0 added, 2 changed, 0 destroyed**;
  only image/release identity and approved capped smoke binding. `azure_verify`
  passed; outside-network workflow **36765795810** passed at this SHA.
- Real `azure_llm_smoke`: all three ES/PT/fraud paths passed, including filing
  and read-back, handoff and Gemini/Jev checks. Known spend **$0.00831825**;
  charged **$0.02025875**, including one unknown NLU provider-error reserve.
  Preserve it; no replay of that call. Cumulative charged **$4.59889495**;
  future full allowances give **$8.79889495 ≤ $12**.
- Live browser completed customer handoff and Desk, then failed at Ops:
  smoke selects the retired “Ops · glass box” navigation label. Reviewed UI
  and existing passing local staff test use “Evidencia y operaciones.” Budget
  read-back proves this failed browser attempt made no model calls.
- One-label correction passes `node --check scripts/serving-browser.mjs` and
  existing authored `pnpm test:e2e --staff` (**1/1**, live fixture API, no models).
- Corrected browser attempt stopped at login, exhausting the conservative five
  slots; do not reset them. Owner decision requested for exactly one additional
  browser attempt in the same purse. HTTP-only authentication subsequently
  passed: config/login/SMS/OTP/me/transactions/logout, no chat/model calls. First
  config took **38.4s**, above the harness's 30s default; warm config **0.33s**.
  Owner IP still matches. API console logs were unavailable with no active
  replica. Startup timeout is the supported explanation, not proof from a
  detailed browser exception (the old harness emitted only “login”).
- External harness now has the existing smoke client's **190s** navigation and
  element allowance plus stage/error-class-only failures. No POST/action retry.
  Node syntax and Prettier checks pass. The first custom read-only diagnostic
  mistakenly requested nonexistent `/clock`; corrected check verifies the clock
  from `/me`, as the actual UI contract requires.

### Done but not verified

- Correcting only the external browser harness selector. Full browser gate and
  new acceptance receipt remain pending. Shared pre-v4 scope, latency and private
  snapshot are not yet created/run. No v4 input/run or public/warm activation.

### Next / blocked

- Green harness-only correction; preserve application digests and prior real
  smoke evidence, reverify release identity/controls, finish the remaining capped
  browser allowance. Disclose reuse of identical runtime evidence explicitly.
- Only after full acceptance: **dev-gate/pre-v4 / pre-v4**, latency, private export.

## 2026-09-30 PDT — Exact-main recording fixture race

### Completed (verified)

- #78 passed PR CI **36760917373** and safety **36760917289**, merged at
  **d882deb4ea2a9015db460d7d30aedc912f6a8aea**. Main safety **36761758449**
  passed. Automatic main CI **36761758157** passed Python/Postgres but failed
  fixture browsers **79/80**; live/staff were not reached. No CI rerun.
- Failure: PT recording opt-in changes locale immediately after navigation,
  before client bootstrap. Wait for restored chat before that interaction and
  assert selected locale. Product paths/expected labels remain unchanged.
  `pnpm test:e2e --grep 'recording tools are hidden' --repeat-each=3` in CI's
  dev-server mode passed **6/6**; ignored log in `artifacts/integration/`.
- Both d882deb image tags were pushed and registry digests equal the earlier
  21dac9e builds. Live plan is exactly two existing app updates, only images,
  release identity and approved smoke binding; min=0, owner ingress, identities,
  secrets and resource shape unchanged. No apply or paid calls yet.
- Unused 21dac9e smoke purse disabled with history retained; d882deb purse
  registered at $0.10, zero attempts/spend. Cumulative maximum **$8.77863620**.

### Done but not verified

- Test-only correction needs fresh remote CI. Azure still runs prior preview;
  full release, shared pre-v4 purse, latency and private snapshot remain pending.

### Next / blocked

- Green correction PR and exact-main CI; reuse identical image digests under
  resulting main, retire unused smoke purse, replan and finish approved gates.
- Preserve all failed gate logs. Do not claim the failed main run passed or
  bypass the gate. No v4 input/run, warm replicas or public visibility change.

## 2026-09-30 PDT — Main integration verified; smoke binding validation

### Completed (verified)

- #62 merged at **21dac9e791a92fc9979cac8dfc1805a3f76b2563** after candidate
  CI **36757162866** and safety **36757162820** passed. Automatic main CI
  **36757992427** and safety **36757992412** also passed. Main equals origin/main.
- Built and pushed both exact-main images; digest receipt is ignored
  `artifacts/azure/release-21dac9e/image-digests.json`. Fresh East US 2 retail
  prices passed the $40 gate: modeled no-grant margin **$34.63/month**.
- The reviewed release plan stopped on the legacy smoke-ID validation; no
  Terraform apply or real model call occurred. Registered release purse has
  zero attempts/spend. Prepared only the approved private image/run inputs.
- Added full-SHA release/latency ID validation. `terraform -chdir=infra fmt
  -recursive`, `validate` and `test -filter=tests/submission.tftest.hcl -no-color`
  passed: **10 mocked plans**, no cloud mutation. Invalid IDs and judge/smoke
  combinations remain rejected. Application image inputs are unchanged.

### Done but not verified

- Narrow validation correction awaits remote CI/main merge. Azure still runs
  the prior preview; new live smokes, acceptance receipt, pre-v4 shared scope,
  latency probe and private submission export remain pending.

### Next / blocked

- Require remote CI/safety, promote the correction, reuse identical application
  digests under the resulting main SHA, then finish the approved release.
- After release: create **dev-gate/pre-v4 / pre-v4** ($1 lifetime), measure the
  capped Azure BFF latency, then export and scan the private submission snapshot.
  No v4 input/run, warm replica or public visibility change is authorized here.

## 2026-09-30 PDT — #76 integration, pre-v4 accounting and release preparation

### Completed (verified)

- Reviewed #76 (`4436729`), retargeted it to `fix/post-v3-analysis` and merged
  locally without conflicts. Changes are presentation/authored fixtures; BFF
  and Desk write handlers remain intact, including the earlier persona/card
  decision locks. No organizer/v4 row was opened. Recording opt-in grants no
  action authority; canonical reasons/evidence remain available.
- Added duration-only BFF `Server-Timing`, a ten-conversation ES/PT latency
  probe with duplicate-launch protection and release gates, and SHA-bound
  release/latency $0.10 lifetime purses. Authored full mock probe reaches 20
  turns without persisting facts/credentials; no real probe ran yet.
- Added `scripts.pre_v4_budget`: shared **dev-gate/pre-v4 / pre-v4**, $1 lifetime,
  prior-scope closure (post-v3 included), retained unknowns, conflict/breaker
  refusal and rollback. Final v4 preparation counts/closes this new scope and
  conservatively counts historical production charges plus both smoke caps.
- Read-only verified-TLS ledger at 18:01 UTC: prior **$4.57863620**, including
  $0.03580104 historical production; + dev $1 + v4 $3 + release $0.10 +
  latency $0.10 = **$8.77863620 ≤ $12**. Four prior unknown reserves retained.
- Combined `LLM_PROVIDER=mock make checks`: **449 passed / 20 DB skips**,
  six hooks, B1 **32/32**, compile/interfaces/catalog. Ruff and strict mypy
  (85 files) passed; disposable Postgres **23/23**; web typecheck/lint/build;
  browsers **80 fixture + 12 live API + 1 staff = 93/93**. Both bootstrap
  regressions additionally pass **6/6** in CI's development-server mode.
- Corrected a second authored bootstrap race: assert all three shortcuts render
  before removing mocked config. Expectations unchanged; original failure logs
  retained. Restored generated Next declarations. No paid model call occurred.
- Sebastian's standing OK now authorizes green #62 merge/main release and
  spending within the cumulative ceiling. Temporary smoke-run binding separately
  approved; resource shape, min=0 and owner ingress remain unchanged.

### Done but not verified

- Remote corrected-head CI/safety, merged main, pushed/deployed images, full
  Azure release gates, live pre-v4 scope and paid latency remain pending here.
  Exact milestone evidence is recorded in ignored `artifacts/integration/` and
  `artifacts/azure/jev-release.json`; read their SHA/results before claiming release.
- Live v4 scope/inputs/serving/start remain unverified and unstarted. No public
  judge/warm mode or public repository visibility is enabled.

### Next / blocked

- Publish the full corrected integration once, require remote CI/safety green,
  merge #62 and release with image tags plus the approved smoke binding only.
  Run controls/real/browser/outside-access gates and report exact SHA, then create
  and read back **dev-gate/pre-v4 / pre-v4** for the AI lane, then measure latency.
- Feature freeze **Oct 2 12:00 COT / 17:00 UTC**; independent v4 run follows
  freeze/release and a separate GO. Keep v4 blind and v1 untouched.
- After release, prepare the approved scrubbed snapshot in a new private
  `factored-hackathon-2026-sebastian`; retain honest chronology and scan it.
  Public visibility and Oct 4 warm/access activation need explicit approval.
- [Release/budget/probe commands and measurement scope](../evaluation/pre-v4-release-and-latency.md).

## 2026-09-29 PDT — Single remote #62 gate and test-only hydration correction

### Completed (verified)

- Published combined head **00246eb083121d8234c7ef45a076c7fb78801145** once;
  GitHub read-back records #63/#65–#75 merged into the feature branch. #62 and
  blind #64 remain open. Main remains **e12efc73be64f8355aa9f177f08a04337593616c**.
- Automatic CI **36672780834**, attempt 1: Python checks and Postgres passed;
  fixture browsers **63/64**, with one startup locale test failure. Safety
  **36672780958**, attempt 1: passed. No rerun. Aggregate receipt is ignored
  `artifacts/integration/pr62-remote-gates.json`.
- Diagnosed an authored-test hydration race: its first connecting label exists
  in server-rendered HTML, before the locale change handler is attached. The
  correction waits for client bootstrap, matching the existing startup test;
  adds a locale assertion. No product, confirmation, OTP, action, timeout or
  expected-label change. CI dev-server mode passes targeted **3/3**, full
  fixture **64/64**. Restored generated `next-env.d.ts`. Commands/receipt in
  [integration review](../reviews/pr-71-75-integration-review.md).
- Earlier combined local gates remain verified: Python **442**, Postgres **20**,
  B1 **32/32**, browser **64 fixture + 12 live + 1 staff**, Terraform **5** plans.
  No paid model calls or Azure changes; v4 unopened/unstarted, submission OFF.

### Done but not verified

- Remote live/staff browser runs were not reached after the fixture failure.
  The corrected local candidate has not been published or remotely checked.
  Main promotion is blocked on green remote CI; this record does not claim it.

### Next / blocked

- Obtain approval for a second automatic remote CI cycle (about **$0.06**,
  owner estimate, within the $5 hard cap), publish the test-only correction and
  inspect it without manual reruns. Then report the new exact SHA and gates.
- Main merge/release still needs Sebastian's separate confirmation. No release,
  submission activation or v4 final run is authorized by this correction.

## 2026-09-29 PDT — Complete #62 integration and local release gates

### Completed (verified)

- Opened private preparation PRs **#73** (`c328553`) and **#75** (`aaa2a97`),
  read back their feature targets and integrated them locally. Reviewed/merged
  audit **#71**, UX **#72** and AI evidence **#74** into the feature target,
  following the earlier #63/#65–#70 integrations. Two progress conflicts kept
  every entry; no product conflict or force push.
- Critical #72 review: BFF and Desk write handlers match the reviewed #68 base;
  recognition, confirmation hashes, OTP renewal, explicit expired review and
  uncertain-write drafts retain authority in code. Fixed two integration gaps
  in **8513b9d**: current eligible judge alias is retained on story selection,
  and pending card decisions lock story changes. Authored browser assertions
  observe zero message/action POSTs for draft preparation and zero freeze writes
  through the card retry/review. Corrected one stale live revocation label.
- Combined local `make checks`: **442 passed / 17 DB skips**, all six hooks,
  compile/file policy, interfaces/catalog, B1 **32/32**, reactive B1 **32/32**;
  Ruff and strict mypy **85 files**; disposable local Postgres **20/20**;
  Terraform fmt/validate and **5/5 mocked plans**. Web typecheck/lint/build;
  browser **64 fixture + 12 live API + 1 staff = 77/77**. No model spending.
- Corrected #74's stale preview claim to verified `dac3801` read-only startup;
  audit #71 explicitly covers its historical snapshot, not these later changes.
  Official figures/limits and assumption-labeled estimates are unchanged.
  [Review and commands](../reviews/pr-71-75-integration-review.md).
- V4 scope is prepared in code, not created/enabled in Azure. Cumulative snapshot
  $4.54283516 + $3 + $0.10 = **$7.64283516 ≤ $12**. V4 rows/selections/tools/
  bindings unopened; no preflight/start. V1 untouched. No Azure change; submission
  toggles OFF. Main/origin/main stay `e12efc73be64f8355aa9f177f08a04337593616c`.

### Done but not verified

- The committed record covers local gates. Remote CI/safety evidence is produced
  after the single complete-head publication and saved in ignored
  `artifacts/integration/pr62-remote-gates.json` with its exact SHA/run IDs.
  Read that receipt and current GitHub #62 checks before promotion; no extra
  documentation push is needed solely to record a CI result.
- This combined candidate is not deployed. Public judge login/warm replicas,
  new real-chat acceptance and independent v4 outcomes remain unverified.

### Next / blocked

- Inspect the one automatic #62 CI/safety run after publication. Main requires
  remote green plus Sebastian's explicit merge/release confirmation. Avoid
  needless reruns under the hard $5 Actions cap. Report SHA and gate receipt.
- A later approved release prepares the real v4 budget/bindings/local-serving
  pins; separate GO starts the final program. Submission-day activation needs
  source persona/role, dates, exact plan and infra/model cost approval.


## AI lane — 2026-09-29 (judge-facing Production Thinking and Responsible AI)

### Completed (verified)

- Read `docs/production-readiness.md` fully before refreshing it. Used the recorded restricted Azure preview, deployment/budget ADR, existing startup/warm-price evidence, current route/grounding code and published official v2/v3 aggregates only. No v4 row, authoring file or result was opened; no model/cloud call or resource change was made.
- Refreshed Production Thinking (**502 words**) with Container Apps, Postgres/non-owner forced RLS, Key Vault/managed identity, reserve-before-call daily/run caps, Grok failure fallback, committed read-back and unanchored hash-chain limits. Added clearly labeled pilot effort/monthly-cost assumptions for network, identity/MFA, telemetry/SLOs, scaling/recovery, cold starts, scheduling, human queue and bank/retention/audit work; dated baseline/warm prices are distinguished from fresh quotes and incremental allowances.
- Added Responsible AI (**509 words**) with actual masked fact/text boundaries, redaction limitations, requested OpenRouter ZDR and unverified Jev ZDR, private content-bearing persistence and unverified purge; bounded injection/DLP/grounding controls and authority in code. Published v2/v3 ES/PT SAR/strict-escalation counts, corrected regional v2 recall, failed safety gates, es-CL n=9/no fluent PT reviewer and a private issue-report proposal. Only v4 retains `TODO(results)`.
- Checked all quoted figures against existing evidence, all local links/anchors, sensitive-value exclusions and reading length: **2.79 / 2.83 minutes at 180 words/minute**. No product/interface/fixture change and no new runtime tests are needed. Working-tree data/secret/size policy and commit hooks pass, including strict mypy.
- Corrected PR #71's CI-trigger handoff and read it back: the old parser had mistaken the separate main-push filter for a PR branch filter. Target workflows still trigger all PRs. Owner policy remains local checks for stacked PRs, green remote CI before main promotion. This docs commit uses GitHub's documented `[skip ci]` marker to avoid Actions spend until the lead changes triggers; do not carry a skipped required gate into a main merge. No existing workflow was rerun or cancelled. Prior audit-only session note remains privately preserved in ignored artifacts and is excluded from this PR.

### Done but not verified

- Pilot estimates are assumptions, not implementation promises, observed bills, bank-contract quotes or a summed production forecast. No live deployment recheck, new acceptance run, human PT validation, provider deletion or operational SLO is claimed.

### Next / blocked

- Open one documentation PR against `fix/post-v3-analysis` and leave merging to the lead. Lead reviews the effort/cost assumptions and publication wording; green main-target CI remains mandatory. V4 remains pending and blind. No spend or cloud action is authorized by these pages.


## 2026-09-29 PDT — Submission-day infrastructure prepared OFF

### Completed (verified)

- Added independent OFF switches `enable_submission_warm=false`,
  `min_replicas=0`, `enable_judge_access=false`. Warm 1 requires its switch;
  judge mode cannot use a smoke budget. API stays internal HTTPS, max=1;
  public web still uses login/OTP and the existing global $3/day model breaker.
- Judge account/password are external Key Vault references only, never values
  in Terraform inputs/state. OFF has no credential requirement or effect.
  Enabled runtime aliases an existing reviewed source customer/locale/role and
  gated story hints; it cannot claim new ownership/role. Judge and owner
  passwords cannot interchange; OTP/session/action semantics are retained.
- `terraform fmt -check`, `terraform validate`, five mocked plan-only tests
  pass. Read-only sandbox plans (`-refresh=false -lock=false`, explicit sandbox
  wrapper) show **OFF: zero changes**; ON: **two app updates + two scoped RBAC
  grants**, zero deletes, API internal. Plans/JSON stay ignored and 0600.
  No Azure apply, secret upload, enablement or model call occurred.
- Live East US 2 compute rates read at 04:17 UTC: two warm replicas
  **$0.3888–$1.296/day**, 14-day compute **$5.4432–$18.144**. With explicitly
  historical fixed-service/margin assumptions, monthly infra **$34.73–$47.43**;
  upper case exceeds $40 approval gate. $3/day models can add $42 over 14 days,
  separate from v4's lifetime budget. [Plan and approval checklist](../submission/infrastructure-switches.md).
- Mock `make checks`: **429 passed / 16 DB skips**, six hooks, B1 **32/32**,
  compile/snapshots/catalog. Ruff and mypy **85 files** pass. Disposable local
  Postgres **19/19**, including judge RLS/session recovery on restart and owner
  case isolation. Authored login/security follow-up **19/19**, including only
  the source's gated story hints. Early test issues (sandbox TestClient stall,
  wrong test endpoint and inherited private smoke variable in mock tests) were
  corrected; no product regression remained.

### Done but not verified

- No real judge credential exists from this work. Public ingress, outside-IP
  login, production account/source choice and live enabled budget are not tested.
  Read-only no-refresh plans are not fresh drift audits or apply authorization.

### Next / blocked

- Open this preparation PR against `fix/post-v3-analysis`. Sebastian approves
  source persona/role, dates, exact live plan and total infra/model exposure on
  submission day before enabling anything. Keep testing min=0 and owner ingress.
- Integrate preparation/audit/UX and pending AI docs on the feature target, then
  full local browser/API gates and one remote #62 head run. No main merge,
  Azure change or v4 start until the subsequent owner gates.



## 2026-09-29 PDT — V4 runner readiness, no execution

### Completed (verified)

- Generalized suite/binding/manifest configuration, budget scope/run, output and
  detached start/resume pins for test-v4 (`309c3aa2…`) without opening any v4
  row, selection, authoring tool or binding. Local non-owner serving DSN is
  required and preserved; durable Azure budget accounting remains separate.
  Frozen selections are consumed only inside an authorized start. Judge cap
  remains 1024; B1 100 / P 160 / dual judge 60 / frontier OFF.
- Read-only aggregate ledger: prior charged/reserved $4.54283516 + v4 $3.00 +
  release-smoke allowance $0.10 = **$7.64283516 ≤ $12**. Four prior unknowns
  remain charged. Future preparation closes prior scopes and rechecks exposure;
  no Azure budget scope was created or enabled in this session.
- Authored pins/local-serving/launcher/resume/judge tests passed. Mock
  `make checks`: **430 passed / 17 DB skips**, hooks, B1 **32/32**, compile,
  interfaces/catalog; Ruff and strict mypy (84 files). Disposable local
  `python -m scripts.test_postgres`: **20/20**, including $3 v4 cap across
  restart, prior v3/dev closure and retained reserves. An initial new test used
  an unsupported Store context manager; explicit cleanup fixed it before rerun.
- [Readiness, cost math and limitations](../evaluation/v4-program-readiness.md);
  [future commands](../evaluation/final-run-plan.md). No model calls or Azure
  resource changes; main stays unchanged and v1 untouched.

### Done but not verified

- V4 release inputs/bindings, local organizer serving readiness and a new
  deployed acceptance SHA are not checked here. No v4 preflight, preparation,
  start or outcome is claimed. Latency will include provider/budget calls.

### Next / blocked

- Open the readiness PR against `fix/post-v3-analysis`; prepare separate OFF
  submission switches next. Wait for UX before the single combined main-target
  CI run. Main merge, Azure enablement and v4 execution need their release gates
  and owner authorization. Stacked PRs use documented local checks.


## 2026-09-29 PDT — AI review, feature integration and startup profiling

### Completed (verified)

- Critically reviewed PRs #65/#66 commit by commit. #63 was already merged;
  #65 merged at `b9dabfb`, #66 at `6800ffd` under the preceding feature-merge
  authorization while billing was blocked. One progress-log conflict was
  resolved by keeping both entries in a history-preserving update; no force push.
- Reproduced #65's lead-owned offer failure at zero cost in ES/PT. Commit
  `02d6bcc` narrowly exempts charge-origin memory statements from selection
  uncertainty, retaining separate inability-to-choose clauses and all matcher
  thresholds. Authored regressions: 10 failures/10 passes before, **20/20 after**.
  The reported dev case passes a bound replay using authored mock extraction,
  with its required offer, cancellation and no forbidden/unsafe action. No new
  real-model result is claimed.
- Integrated #67 then dependent #68 locally into `fix/post-v3-analysis`, followed
  by the guard correction. Full combined checks: `make checks` **417 passed /
  16 DB skips**, six hooks, file policy, compile, B1 **32/32**, **12 readbacks**,
  snapshots/catalog; Ruff and strict mypy (84 files); reactive B1 **32/32**;
  `python -m scripts.test_postgres` **19/19**; web typecheck/lint/build; browser
  **46 story + 12 live + 1 staff = 59/59**. No product merge conflict or local
  regression. Generated Next/B1 aggregate files were restored after checks.
- Reviewed and locally integrated #69/#70. Applied #69's six copy changes in
  `ea34060`, mechanically updating one stale hunk beside #68 provenance code.
  AST checks confirm six string-only changes/four replacements and identical
  non-string structure/placeholders/numbers. Corrected the review's coverage
  cutoff: later OTP retry/UX strings are outside its 134-item model inventory.
  All four model-card source pins match; no review call was rerun.
- #70's README/projection numbers match official v2/v3 reports and saved v3
  aggregate objects. Decimal recomputation confirms every low/base/high output
  and 4,440-minute sensitivity. Historical FCR, counts, handling and wait times
  match committed pipeline aggregates; workload/efficiency/infra are labeled
  assumptions, with safety failures/partial judging retained. Bootstrap order
  was checked against source, not rerun on organizer data. A second
  progress-log-only conflict preserved every entry. An early local check on
  the unresolved index failed in the staged-file scanner; after resolution the
  stable `95332e0` candidate passed `make checks` **417/417**, B1 **32/32**,
  hooks/compile/snapshots/catalog. No extra paid calls.
- Added main-only PR filters and workflow/ref cancellation to CI/safety in
  `2b41886`. YAML assertions verify PR base main, main pushes and cancellation.
  The owner initially announced billing recovery; the single authorized reruns
  on #67/#62 still started zero steps. Further reruns stopped when requested.
  The later owner confirmation supersedes that block: **$5 hard Actions cap**,
  rigorous local gates for stacked PRs, remote green required before main merge.
- Read-only startup profiling of the existing `dac3801` preview: 86.059 s is
  the prior web→API cold-read chain, with a 43.581 s web-ready/API-ready gap.
  Cached API/web images are 226.88/72.26 MiB; a separate API activation pulled
  its image in 7.54 s. Network-disabled local API initialization at 0.25 CPU /
  512 MiB took 6.399 s; TypeSafe import 0.516 s; LightGBM not loaded at readiness;
  matcher construction afterward 2.479 s. Non-owner TLS serving/identity/hint
  timings completed without printing rows. An initial workstation pool timeout
  was followed by successful TLS/read checks; firewall IP still matched.
  No Azure change, model call or banking write. [Profile and proposals](../evaluation/preview-startup-profile.md).
- [Review, commit dispositions, gate commands and limits](../reviews/pr-65-66-integration-review.md).
  Main/origin/main remain `e12efc73be64f8355aa9f177f08a04337593616c`.
  V4 files/rows/tools/bindings were neither opened nor executed; v1 untouched.

### Done but not verified

- #67–#70 and the lead guard/copy/CI changes are locally integrated, not yet
  published on the combined #62 head. GitHub stacked PRs still show open until
  publication. The frontend UX PR is being prepared on `feat/judge-ux-polish`.
- Full remote CI on the final combined head and Azure release are pending.
  Browser/Postgres checks predate only the six verified copy changes; final UX
  integration still requires its combined local browser gate.
- Startup timings are individual observations, not a complete Azure cold-start
  decomposition. No proposed dependency/import/cache/readiness optimization was
  implemented. No human PT fluency or independent v4 result is claimed.

### Next / blocked

- Wait for the orchestrator's UX PR number, review and integrate it locally.
  Re-run necessary combined local gates, then publish **one complete #62 head**
  and inspect its automatically triggered CI/safety; avoid manual reruns.
  Keep the $5 owner billing cap and main-only trigger/cancellation policy.
- Do not merge main or start v4. Report the combined SHA and remote gates after
  the single full-head run. Any release remains a separate authorized step.


## AI lane — 2026-09-29 (language model card and cross-vendor copy review)

### Completed (verified)

- Updated [the language model card](../ml/model-card.md) for NLU v5.1, phrase v2's actual approved text and deterministic clarification/recognition guard, contextual ES/PT/uncertain language evidence, the 6 s first-attempt timeout and 1024-token Sonnet judge cap. Source hashes read back exactly; only independent v4 slices retain `TODO(results)`.
- Recorded PR #65's frozen 40-conversation dev results (39/40 before/after, normalization failures 9→0, clarifications 15→6, cost/latency and limits) separately from official v3 P 77/100 versus B1 52/100, SAR +11 pp (95% CI +5 to +17). V3 is now seen dev data; its post-hoc 100/100 does not replace the official result. V4 remained unopened and unrun.
- Completed Sonnet cross-vendor review of **134/134** active source strings/variants, **67 ES + 67 pt-BR**, including all templates, offer/recognition questions, approved API replies and all eight added web translations since `e12efc7`. Ten valid calls, no retries/truncation/new unknown costs. [Before/after and decisions](../ml/pt-review.md).
- Per-call usage and readback of the ten durable reservations agree at **$0.085928**, below the approved $0.10. Existing shared `dev-gate/post-v3` / `post-v3` scope reads **$0.71924554 exposure** (known $0.68326354; three pre-existing unknowns), below the requested $0.90 stop and unchanged $1 cap. Concurrency one; every call reserved before sending under the scope lock. No key-level delta or final scope was used.
- `LLM_PROVIDER=mock make checks` passes: six hooks, Ruff, strict mypy, compilation, file policy, **308 passed / 14 database-dependent skips**, B1 **32/32**, interfaces and policy catalog. No product code changed in this PR.
- Reconciled the updated lead target `6800ffd` into this feature branch after PRs #65/#66 merged, preserving every progress entry. The conflict was documentation only; no product or fixture changes were authored. Local 381-test checks on that combined target passed in this session.
- Pushed only private origin and opened [PR #69](https://github.com/sebastian-gm/bank-agent-lab/pull/69) against `fix/post-v3-analysis`; read back the exact description, branch SHA, mergeable and open/unmerged state. All four remote CI jobs completed with failure: annotations say the jobs were not started because an Actions budget prevents use. No CI was cancelled.
- Prepared a [lead-owned strings-only patch](../ml/copy-review-post-v3-proposed.patch): five PT occurrences use `contestação` consistently, and one ES freeze offer explains OTP as a new verification code plus confirmation. No lead/front-end product folder was edited. All AI templates and changed web messages were kept. Patch applicability, Python compilation, six string-only AST changes, preserved placeholders/numbers and documentation links were verified.

### Done but not verified

- Copy is model-reviewed, not fluent-human PT validation; no additional production accuracy, fairness or latency measurement was made. The lead-owned proposed strings are not active until the lead applies the patch. PRs #65/#66 describe candidate behavior; this card is not a deployment attestation.

### Next / blocked

- PR #69 stays unmerged for the lead. Review/apply its six lead-owned copy changes and merge the prerequisite fixes before release/final v4. The authorized latest-head reruns still failed before steps; GitHub cited failed recent account payments or a spending limit needing an increase. A meaningful conflict-resolution push gets its normal CI; no further manual rerun is planned until account billing allows jobs to start. Green remote CI remains required before merge. Preserve v4 blindness and make no further paid call.
## AI lane — 2026-09-29 (Actions policy and documentation handoff)

### Completed (verified)

- Read back [PR #70](https://github.com/sebastian-gm/bank-agent-lab/pull/70) and [PR #69](https://github.com/sebastian-gm/bank-agent-lab/pull/69): both are open, unmerged and mergeable against `fix/post-v3-analysis`. Their descriptions now reflect Sebastian's latest Actions instruction: the $5 budget is unblocked; rigorous local checks are the gate for stacked PRs; green remote CI is required for PRs into `main`.
- Reconciled PR #69 with lead target `6800ffd`, preserving both progress histories; its proposed lead-owned copy patch still applies. Documentation PR #70 retains the verified **381 passed / 14 database-dependent skips**, B1 **32/32**, strict mypy and Ruff checks. No additional manual CI rerun, model spend, deployment or v4 access followed the new instruction.

### Done but not verified

- The later owner confirmation supersedes the earlier billing-block and all-merge CI notes below. This lane has not independently audited the owner billing change or future main-target CI; no green remote CI is claimed for these stacked PRs.

### Next / blocked

- Lead reviews and merges PRs #69/#70 into `fix/post-v3-analysis`; this lane leaves both unmerged. Require green remote CI before merging a PR into `main`, and avoid needless reruns. Business projection remains assumption-labeled; v4 results remain pending and blind to this lane.

## AI lane — 2026-09-29 (business projection and judge README refresh)

### Completed (verified)

- Read `docs/evaluation/business-projection.md` and root `README.md` before editing, then used only committed dataset aggregates, official v2/v3 reports, architecture/serving source and the historical Azure dev price plan. No v4 row, authoring tool or artifact was opened; no model call or cloud resource change was made.
- Refreshed [the business projection](../evaluation/business-projection.md) with official v3 P **77/100** versus B1 **52/100**, SAR **39% / 28%**, strict escalation **30/40 / 20/40**, unnecessary transfers **11/60 / 23/60**, precise **$0.00237687544** serving cost and case/turn latency. Kept safety-gate failures and partial judging visible; later seen-v3 checks do not replace the official result.
- Read back dataset **43.6% Queja contact FCR proxy**, **12,297/67,095 = 18.33% identified charge-dispute complaints**, and **434.606 s / 220.803 s** complaint/transactional handle-time means. The 10,000/month volume and use of category handle times for dispute intake are explicitly assumptions, not monthly/source facts.
- Authored a reproducible low/base/high projection against B1 with review/remediation and all nonautomated issues receiving human follow-up. Base: **3,900 automated intake outcomes**, **1,200 avoided unnecessary transfers**, **11,621 net agent minutes**, **$23.77 model + $35 assumed infra = $58.77/month**. Low adds **3,028 minutes** of work. Arithmetic uses exact source values, and avoided transfers are not counted twice as time savings. A transactional-time proxy sensitivity reduces base savings to 4,440 minutes. Only v4 retains result placeholders.
- Replaced the stale mock-diagnostic README with a short judge draft: three guided stories, one Mermaid architecture diagram, separate official v2 and after-fixes v3 evidence, v4 pending, honest language/safety/identity/production limits, and source-checked mock-only local bootstrap. Root README is the explicitly requested shared-file edit; no product code or fixtures changed.
- Decimal arithmetic, output rounding, evidence links, one-diagram constraint and v4-only `TODO(results)` entries verified. Mock `make checks` passes: six hooks, Ruff, strict mypy, compilation, file policy, **381 passed / 14 database-dependent skips**, B1 **32/32**, interface snapshots and policy catalog.
- Following Sebastian's Actions-budget instruction, reran only PR #69's latest two blocked workflows: `ci` **36662765802** and `safety` **36662765906**, both attempt 2 on `3c86e27`. All four jobs completed without steps. Their new annotations say recent account payments failed or the spending limit needs increasing; this does not establish which billing condition applies. No older head, merged PR or other lane was rerun; no repeated attempt was requested.

### Done but not verified

- Projection is conditional capacity arithmetic, not realized production savings, a labor-cost estimate or a current cloud price/capacity quote. Dispute-specific agent times, traffic weighting and operational remediation remain unmeasured. Local bootstrap commands were reviewed against code, not executed against organizer data or a new deployment in this session.
- Remote green CI is required before any merge. The authorized PR #69 reruns are still blocked before startup by GitHub account billing/spending status; the $5 budget announcement did not make those attempts runnable.

### Next / blocked

- The documentation candidate targets `fix/post-v3-analysis` and remains for lead review/merge only after green remote CI. Preserve v4 blindness and zero model spend. Once the owner confirms the GitHub billing block is resolved, rerun blocked current-head workflows once; do not rerun needlessly or merge without green CI.

## AI lane — 2026-09-29 (queued PR #62 review findings 1 and 3)

### Completed (verified)

- Read the lead's review on `fix/preview-startup-review` after opening robustness [PR #65](https://github.com/sebastian-gm/bank-agent-lab/pull/65). Added authored mock regressions before changing behavior; eleven reproduced the assigned defects. No v4 input was opened and no paid call was made.
- Preserve code-supplied clarification replies exactly, including bilingual language help; retain the existing recognition guard. Rephrased explanations now receive the actual approved `plan.reply` as `approved_text` and fallback, with DLP/grounding checks retained.
- Added explicit ES/PT/uncertain language evidence, excluding domains and trusted merchant names. Shared `com`/`sim` tokens cannot decide language; NLG rejects only confident opposite-language evidence. The frozen two-language interface retains its default. [Implementation and evidence](../ml/pr-62-ai-review-fixes.md).
- `make checks` passes: six hooks, Ruff, strict mypy, compilation, file policy, **329 passed / 14 database-dependent skips**, B1 **32/32**, interfaces and policy catalog. Targeted new and existing API/recognition/grounding regressions: **90 passed**. Merged the lead target advancement `dac3801` into this feature branch, preserving both progress-log entries and leaving PR merges to the lead.

### Done but not verified

- Real-model performance, calibrated language probabilities and human PT fluency are not measured in this follow-up. No further paid measurement is planned. Remote CI remains subject to the owner Actions budget block.

### Next / blocked

- [PR #66](https://github.com/sebastian-gm/bank-agent-lab/pull/66) is open, unmerged, targeting `fix/post-v3-analysis`. Lead reviews and merges; preserve both additive progress entries when reconciling PRs #65/#66. GitHub Actions requires the owner budget block to be resolved; read back current-head CI before merge. PR #65 retains the paid robustness study and lead-owned guard follow-up. Keep v4 blind and do not deploy.

## AI lane — 2026-09-29 (post-v3 authored robustness study)

### Completed (verified)

- Read handoff 14; authored and froze 40 synthetic ES/PT conversations at `31826c6` before any P run or language fix. All three fixture hashes read back unchanged after measurement. No v4 data was opened.
- Real P before/after: **39/40 → 39/40**, ES **19/20 → 19/20**, pt-BR **20/20 → 20/20**, zero unsafe/forbidden outcomes, all four embedded injections logged. Fixed complete ES/PT spoken-amount parsing and Portuguese previous-weekday dates in AI-owned NLU, with 45 authored parser regressions. Opening slot failures **9 → 0**, clarification responses **15 → 6**, case p50 **7.877 → 5.423 s**, p95 **12.195 → 12.273 s**. [Full report](../ml/nlu-robustness-post-v3.md).
- All **89/89 → 75/75** OpenRouter attempts and **59/59 → 50/50** Jev attempts valid. Known new per-call cost **$0.230932684**, no new unknown usage. Durable `dev-gate/post-v3` / `post-v3` readback: **$0.63331754** including retained reserves, below the $0.90 stop and $1 shared lifetime cap. No final scope was used; no further paid run planned.
- `make checks` passes: six hooks, Ruff, strict mypy, compilation, staged-file policy, **360 passed / 14 database-dependent skips**, B1 **32/32**, interfaces and policy catalog. Additional strict-mypy and B1 reactive dev **32/32** pass. No prompts, model roles, contracts or policy authority changed.

### Done but not verified

- One offer-path failure remains lead-owned: valid model/postprocess unfamiliarity is overridden by `selection.uncertain()` on a charge-origin memory statement; MATCH was confident. Zero-cost reproduction is saved privately and the report describes the lead's narrow regression/fix. No human language validation or independent accuracy claim is made; latency is one before/after observation.
- [PR #65](https://github.com/sebastian-gm/bank-agent-lab/pull/65) is open against `fix/post-v3-analysis`, unmerged. All four remote checks completed without starting jobs: their annotations report an owner Actions budget block. Local checks are green; remote CI is not green.

### Next / blocked

- Lead reviews/merges PR #65 into `fix/post-v3-analysis` and fixes the remaining deterministic uncertainty guard before release. The lead base advancement `dac3801` is merged into this feature branch with both progress entries preserved. Queued review findings 1 and 3 are complete in independent [PR #66](https://github.com/sebastian-gm/bank-agent-lab/pull/66), with mocks and zero additional spend. Keep v4 blind; this lane does not merge/deploy.

## 2026-09-29 PDT — Preview diagnosis, code-only startup fix and PR #62 review

### Completed (verified)

- Read handoff 14 fully and applied Sebastian's subsequent decisions: min
  replicas stay zero while testing; run CI locally while Actions billing is
  pending. Main and origin/main remain `e12efc73be64f8355aa9f177f08a04337593616c`.
- Read-only Azure metadata confirmed both preview images at
  `37627d4001bc02bd3ae0c25c618acd16f5b4a47e`, initially zero replicas. With
  authenticated `httpx` BFF reads, the first config GET failed 503 after 50.560 s
  and login failed after the 10.114 s deadline. Warm login/OTP, me including the
  clock, and repeated transactions passed in 0.1–0.5 s. API logs show completed
  startup, successful reads and no sampled application exceptions. This confirms
  the cold-start chain for the reported failure. No chat/provider/banking write
  was invoked; credentials/OTP/cookies and organizer rows were never printed.
  [Diagnosis and ignored evidence](../evaluation/preview-startup-diagnosis.md).
- Code commit `e043356` on `fix/preview-startup-review`, based on PR #62 head
  `32587c9`, gives startup GETs 75 s and at most one transient GET retry, preserves
  single-attempt POSTs, and shows ES/PT startup/retry states. No Azure setting,
  image or access boundary was changed.
- Pushed the separate candidate to the existing private origin and opened
  [draft PR #63](https://github.com/sebastian-gm/bank-agent-lab/pull/63), targeting
  `fix/post-v3-analysis` so its startup/doc changes can be reviewed independently
  of #62. No PR or branch was merged.
- Reviewed every PR #62 commit. Authored, zero-cost mock/ASGI reproductions
  confirmed five findings: approved language clarification lost before phrasing; legal cues
  lost across session tabs; `.com`/SIM language false positives; renewal reuses an
  invalid freeze hash; latest fraud packet may belong to another conversation.
  [Findings, owners and commit dispositions](../reviews/pr-62-review.md).
  The preliminary recognition-question finding was narrowed after checking the
  API's existing deterministic guard; the confirmed language-help case was then
  exercised through the API, not just the NLG helper.
- Local CI commands passed: `UV_CACHE_DIR=$PWD/artifacts/uv-cache make checks`
  (308 pytest passed, 14 skipped; B1 dev 32/32; interfaces/catalog current),
  `.venv/bin/ruff check .`, `.venv/bin/mypy --strict src/aclara`,
  `.venv/bin/python -m evals.runner --system B1 --scenarios evals/dev_scenarios_v2.yaml`
  (32/32), and `.venv/bin/python -m scripts.test_postgres` (17/17 in a disposable
  local database). Web: `pnpm typecheck`, `pnpm lint`, `pnpm build`,
  `pnpm test:e2e` (46/46), `pnpm test:e2e --live` (8/8),
  `pnpm test:e2e --staff` (1/1): **55 checks** including all 26 startup checks.
  Two initial startup test failures were corrected (hydration wait and translated
  retry label); the full final web run passed. Local caches use writable paths;
  the missing local pre-commit hook was reinstalled. Generated Next type paths
  and the authored-dev results page were restored after test commands.
- Added [the v3 results page](../evaluation/final-v3-results.md) from saved
  aggregates only: P 77/100 versus B1 52/100; in-scope SAR difference +11 points,
  95% CI +5 to +17; failed full safety gates and partial judging disclosed.
  Verified SHA-256 of the four original result/report/partial/sheet files remained
  unchanged. No v2 rerun or abandoned-v1 access occurred. V3's seen-data 100/100
  is explicitly a development regression check, not a replacement result.
- Read GitHub's PR #62 check annotation with `gh api`: jobs did not start because
  the account Actions budget prevents use. This is not a code-test failure and
  is not a green remote run. PR #62 remains open and unmerged.
- Added submission-day-only warm replicas and live East US 2 price assumptions
  to [the checklist](../submission/checklist.md): two 0.25-vCPU/0.5-GiB apps about
  $0.39/day idle to $1.30/day continuously active, excluding grants/other charges;
  a fully active warm month can exceed the $40 total approval gate. No replicas
  were changed. **New model spend in this session: $0.**

### Done but not verified

- Startup fix is locally verified and committed, **not deployed**; no corrected
  Azure cold-start smoke is claimed. Paid preview chat/phrasing was not tested.
- The five review findings are reported with proposed remedies; those product,
  policy/contract and evaluation fixes are not part of this startup patch.
- Local CI passes, but GitHub CI/external-access workflow cannot run until the
  owner's billing decision. V3 judging and human review remain partial/pending.

### Next / blocked

- Review the startup patch for a separately approved preview redeploy, retaining
  min replicas zero. Decide owners/timing for the five PR #62 findings before
  release. Keep #62 unmerged until CI can run or an explicit merge exception.
- Share/submission-day warm replicas require the dated plan and refreshed cost
  approval in the checklist. No cloud resource or ingress expansion is approved
  by this session.
- **V4 remains unopened and unstarted.** Complete fixes/release gates and await
  the orchestrator's explicit run go. For later sessions paste:
  “Continue from docs/status/progress-log.md. Next layer: PR #62 review fixes and
  preview startup release. Same rules.”

## 2026-09-29 UTC — Owner-approved preview deploy of `fix/post-v3-analysis`

### Completed (verified)

- Sebastian approved deploying the branch tonight for his own review. Images for
  `37627d4001bc02bd3ae0c25c618acd16f5b4a47e` were built from the committed tree,
  pushed with a temporary private Docker config (token removed), and applied as
  the only change (`image_tag`; Terraform 0 added, 2 changed, 0 destroyed).
- `scripts.azure_verify` passed: restricted HTTPS boundaries, single revisions,
  SHA images, managed identity, TLS, firewall, Key Vault RBAC and budget alerts.
  Web returns 200 from the owner IP, the BFF returns 401 without a session, and
  the API revision is healthy on the new image.
- GitHub Actions did not start PR #62 jobs: "an Actions budget is preventing
  further use" (account billing, not code). The same CI steps ran locally and
  passed: pre-commit, Ruff, strict mypy, compileall, pytest, interfaces, policy
  catalog, B1 dev and B1 v2 (32/32 each), staged-file policy, Postgres
  integration (17/17), web typecheck/lint/build, browser 29/29.

### Done but not verified

- This is a **preview of a branch, not a release of `main`**. The capped
  real-model and browser smokes were not rerun: their approved five-conversation
  allowance was already used by the v3 release smoke. The `azure-access` workflow
  cannot run until the Actions budget is restored. The deployed app keeps the
  existing production cap (run `after-v2-release-smoke`, about $0.09 left, $3 daily).

### Next / blocked

- Restore the GitHub Actions budget (owner billing decision) so CI and the
  external access check can run; then merge PR #62 and release `main` for v4.

## 2026-09-28 UTC — Post-v3 fixes (orchestrator session, branch `fix/post-v3-analysis`)

### Completed (verified)

- Post-hoc analysis of the reported v3 run found six causes for the 23 P-Gemini
  failures, plus wrong-language phrasing, judge truncation and a web logout on
  stale OTP. All fixed generically with authored regressions; details in
  [post-v3 fixes](../evaluation/post-v3-fixes.md). V3 is retired to dev data.
- Checks: pytest, Ruff, strict mypy, interfaces, policy catalog, B1 dev 32/32,
  browser 29/29 (fixtures, live, staff).
- Real P-Gemini on all 100 (seen) v3 cases: 100/100, 23/23 prior failures fixed,
  0/77 regressions. Real P dev gate (`--profile post-v3`) passed: 20/20, 18/20,
  12/12, 0 unsafe. Spend $0.40 of the new `dev-gate/post-v3` $1 allowance;
  all prior scopes closed; cumulative ≈ $4.23 of $12.

### Done but not verified

- Branch not pushed; GitHub CI not yet run. No release or Azure change.

### Next / blocked

- Lead: review, push, CI, merge; v3 results page. Data/frontend lane: author an
  independent v4 suite with new templates (handoff 14). Then release and a
  single v4 run after the orchestrator's go.

## 2026-09-28 UTC — V3 system metrics finalized with partial judging

### Completed (verified)

- The sole incomplete judge unit's metadata showed **Sonnet via OpenRouter**
  twice returning `status=refusal`, stop class `length`, exactly **256 output
  tokens** per attempt, with no validated score. Jev was not reached on that
  item. This repeats for the same item at the configured cap, so no further
  paid resume was attempted. The failure was not HTTP 5xx, timeout, rate limit
  or budget denial.
- Existing `evals.final_report.write_report` finalized aggregate system metrics
  from all **260 completed case checkpoints** and 28 completed judge pairs,
  with **zero model calls**, no tracked code change and an explicit **partial
  judging** header and receipt. `results.json` and `results.md` are ignored,
  mode 0600; `PARTIAL.json` exists and `COMPLETE.json` does not.
- Primary 100-case figures from `results.json`: B1 **52/100 pass, 28/100
  in-scope SAR**; P-Gemini **77/100 pass, 39/100 in-scope SAR**. Paired P-minus-B1
  SAR difference **+11 percentage points**, 95% bootstrap CI **+5 to +17**.
  Strict escalation recall **20/40 vs 30/40**; all 30 preselected repeats had
  zero success, SAR and outcome flips. Safety gates remain failed on both systems
  because fraud/regulator recall and required readbacks are incomplete.
- Durable v3 spend remains **$0.47321405 / $3**, zero unknown costs. Prior plus v3
  and release smoke totals **$3.83161437 / $12**. The 20-item human judge sheet
  exists for owner review; no human agreement claim is made.

### Done but not verified

- Judging is **28/60 paired items**. Sonnet/Jev agreement covers those 28 only;
  the remaining items were not scored. The partial report is not a full final
  program completion. V2 remains the official prior result; v3 is after fixes
  on an independent fresh suite.

### Next / blocked

- Stop without another paid resume. Preserve pinned clean main `e12efc7`, all
  checkpoints and the partial report. Owner can review the complete primary
  metrics and the partial judge limitation in ignored
  `artifacts/final-program-v3/results.json` and `results.md`. This progress-log
  branch remains unmerged so any later authorized run can retain its release pin.

## 2026-09-28 UTC — Single authorized v3 resume stopped during judging

### Completed (verified)

- Process metadata showed 213 completed case result files versus 212 published
  progress checkpoints after the first stop. The budget readback occurs between
  those writes, localizing the earlier `OperationalError` to the budget database
  connection path without opening a case result.
- Local Postgres container and TCP port were healthy. Azure admin and app roles
  both passed `verify-full` TLS connections. Current public IPv4 matched the
  configured Postgres allowlist; its Azure-services sentinel remained present.
- Main was clean and matched origin at the pinned release SHA `e12efc73`.
  Preserved the prior stop receipt, then ran one detached `resume` with the same
  15-minute stall and original three-hour wall-clock watchdog rules.
- Resume completed all **260/260 system runs**, then stopped at **28/60 judge
  items** with `RuntimeError`. The evaluator's sanitized wrapper message is
  “Judge execution failed; stop without advancing checkpoint.” No worker remains.
  Durable v3 spend: **484 attempts, $0.47321405 charged with reserves, zero
  unknown costs / $3**. Prior plus v3 is **$3.82358962**; including release smoke,
  **$3.83161437 / $12**. The ignored aggregate receipt is
  `artifacts/final-program-v3/stop-report-resume.json`.

### Done but not verified

- The judge phase and final report are incomplete. No v3 headline metrics have
  been reported. The underlying judge exception is not identified from the
  sanitized wrapper; case inputs and outputs were not opened.

### Next / blocked

- Stop after the single authorized resume. Preserve checkpoints, call journals,
  budget reservations and pinned main. Diagnose the judge failure without
  disclosing frozen inputs or result rows; await the owner's next instruction
  before another resume. Keep this documentation branch unmerged while the run
  requires the exact pinned main SHA.

## 2026-09-28 UTC — V3 stopped on operational error; pinned main preserved

### Completed (verified)

- Evaluation predicate PR #61 merged at `e12efc73be64f8355aa9f177f08a04337593616c`.
  All four main CI checks passed. The diff from frozen product SHA `9f0bff0`
  contains only contracts, evaluator code, tests and docs; no product paths.
- Identical private API/web image digests were retagged and applied in the approved
  Azure subscription. Azure controls and external access denial passed at the
  exact SHA; the ignored `artifacts/azure/jev-release.json` records the gates.
- The zero-cost v3 preflight passed: 100 bound cases, 30 repeat selections and
  30 judge selections. The first two stopped directories were preserved, each at
  $0 spend and zero completed checkpoints. Fresh v3 was started on the pinned SHA.
- Fresh v3 advanced to **212/260 system runs**, then stopped with
  **`OperationalError`**. Its worker exited; no `COMPLETE.json` exists. Durable
  budget readback: **291 attempts, $0.26672382 charged with reserves, zero
  unknown costs / $3**. Prior scopes plus v3 charged **$3.61709939**; including
  the earlier $0.00802475 release smoke, **$3.62512414 / $12**. Checkpoints and
  reservations remain intact. The ignored aggregate stop receipt is
  `artifacts/final-program-v3/stop-report.json`.

### Done but not verified

- V3 is incomplete. No result metrics or human judge sheet are available for
  reporting; official v2 figures remain unchanged. The cause of the
  `OperationalError` has not been diagnosed from the saved trace.

### Next / blocked

- Stop on the error gate. Review the failure safely without printing frozen
  input, case output or credentials. Keep main at the pinned release SHA; after
  owner review, use `scripts.final_program resume`, never `start`. This log entry
  is on `docs/v3-operational-stop` only and must stay unmerged while resume needs
  the exact pinned main SHA.

## 2026-09-28 UTC — V3 evaluator vocabulary repair

### Completed (verified)

- The first v3 attempt stopped at `ValidationError` (`ScenarioV2.expected`); the
  second fresh attempt stopped at `ValueError` during forbidden-predicate
  validation. Both had zero completed cases, zero provider calls and **$0 v3
  spend**. Their ignored directories are preserved separately.
- The suite author compared aggregate vocabulary without disclosing rows. The
  remaining gap is `offer_dispute` as a forbidden observation predicate. The
  evaluator now detects it from a customer response type or a trace event,
  without treating it as a write, proposal or confirmation. Authored predicate
  and bound-evaluation tests pass.
- A second broad search during startup diagnosis exposed three generic
  forbidden-action handling lines in the v3 authoring tool, after product freeze.
  No case templates, suite rows, selection, binding or result contents were
  opened. See the release notes; all subsequent source searches use explicit
  allowed paths.

### Done but not verified

- Full CI, zero-cost v3 preflight, exact-SHA release verification and fresh v3
  execution remain pending. V2 remains the official result.

### Next / blocked

- Merge the evaluation-only fix with green CI. Verify no product paths changed
  since `9f0bff0`, retag identical images, verify Azure controls/access and
  issue a new release receipt. Complete the zero-cost preflight, then launch v3
  fresh under the unchanged $3 durable scope and $12 cumulative ceiling.

## 2026-09-27 local / 2026-09-28 UTC — V3 startup contract repair in progress

### Completed (verified)

- Orchestrator authorized v3 GO on clean release
  `9f0bff04f28aae4fef6e646575d825fc175b369e`. Its first pinned launch
  stopped at startup with **`ValidationError`**, before any case checkpoint or
  provider reservation. `scripts.final_budget.verify` read back **0 attempts,
  $0.00 charged, 0 unknown costs / $3**. No results were opened.
- Access-logged, value-free error inspection found two failures of the v2
  `ScenarioV2.expected` enum in the first suite part. The v1-branch errors are
  irrelevant to a v2 suite. The ADR-0015 `cancelled` outcome already exists in
  `GoldLabels` and the reply contract, but is missing from that v2 expected enum.
- Disclosed a broad search that accidentally surfaced two authoring-tool
  case-template snippets after the product freeze; no frozen scenario rows,
  selection contents, binding values or results were printed. Sebastian approved
  continuation with disclosure and strict product-path freeze. See
  [v3 release notes](../evaluation/v3-release-notes.md).
- Added `cancelled` only to the canonical v2 expected enum and regenerated its
  interface snapshot. The authored contract test passes; no product paths change.

### Done but not verified

- Schema repair awaits full CI, exact-SHA release re-verification and a fresh v3
  launch. The first attempt remains preserved with zero measured spend. No v3
  metrics exist yet.

### Next / blocked

- Merge the schema-only correction after green CI; verify identical deployed
  image digests at the new SHA and record a new release receipt. Preserve the
  first attempt as `final-program-v3-attempt1`; start a fresh pinned v3 directory
  only after reporting class, fix and spend. Enforce the same $3 lifetime scope
  and $12 cumulative ceiling. Keep main frozen while the worker runs.

## 2026-09-27 — V3 release gates and preparation; execution on hold

### Completed (verified)

- Approved post-gate blank-merchant fix merged as #58 at runtime SHA
  **`81ce84ec6c6e1c93063bbaf84eb67dd3d98e604e`**. B1 **32/32**, mock P
  **20/20 + 12/12**, all faults triggered, zero unsafe/errors, **$0**; three
  authored regressions passed. Original paid gate and blind confirmation preserved.
- Main CI **36369151946** and safety **36369151820** passed. Built/pushed API/web
  images to private ACR. `scripts.azure_dev plan` / `apply` updated only the apps
  and restored the approved model-secret reader roles for the real-smoke stage.
  Live East US 2 infrastructure estimate remains **$34.63/month**, below $40.
- `python -m scripts.azure_smoke`: four organizer-serving personas, 15 scoped
  transactions, two cases, four handoffs, staff claim/resolve, logout and original
  session/case readback after API replica replacement passed in mock mode.
- `python -m scripts.azure_verify`: owner-IP web restriction, internal API, HTTPS,
  managed identities, Key Vault references, Postgres TLS/firewall and converted
  **$30/$50** email alerts passed. `azure-access` **36369616217** passed at runtime
  SHA: external runner denied with web 403 / API 404.
- `python -m scripts.azure_llm_smoke`: ES explain→offer→deny→file/readback and PT
  ambiguity passed with valid Gemini/Jev observations. Explicit fraud correctly
  bypasses models under ADR-0015; corrected the smoke-only stale NLU assertion,
  then `--case fraud` verified zero calls, both required reasons, readback/logout.
- `python -m scripts.serving_browser --target azure`: all three surfaces passed.
  Combined API/browser cost **$0.00802475 / $0.10**, nine settled provider attempts,
  zero unknown costs, five conversation allowances used. No further smoke calls.
- `python -m scripts.final_budget --prepare`: scope **final-evaluation-v3**, run
  **final-program-v3**, **$3 lifetime cap**, zero attempts; prior scopes closed with
  reserves preserved. Prior evaluation/dev **$3.35037557** + full v3/smoke caps =
  **$6.45037557 ≤ $12**. With actual new smoke, pre-v3 exposure is **$3.35840032**.
- Suite manifest and opaque private-binding checksums remain the approved pins;
  binding mode 0600. No v3 scenario/selection/authoring contents opened. Fixed
  workload: 100 B1, 160 P-Gemini including repeats, 60 dual-judge pairs; frontier OFF.

### Done but not verified

- V3 suite execution, metrics and human review remain unperformed. V2 remains the
  official result; no v1 access or v2 rerun occurred. PT/dialect human review remains
  a limitation. Final image identity and fresh post-merge CI/access/control evidence
  are read back into ignored `artifacts/azure/jev-release.json` before handoff;
  any retag must preserve both tested image digests.

### Next / blocked

- Finish the release-evidence merge with green CI, retag identical tested images,
  verify the exact final SHA, and run only `scripts.final_program prepare` / `status`.
  Then **STOP for the orchestrator's separate v3 GO**. Never start/resume here.
  [Exact future start/resume commands and ceiling](../evaluation/final-run-plan.md).
  The final response and ignored release/prepared receipts identify the closing SHA.

## 2026-09-27 — Approved post-gate blank-merchant fallback fix

### Completed (verified)

- The first mock Azure smoke at `6aeed0e` stopped before policy/write: deterministic
  fallback matched blank merchant names, then corrupted amount digits during
  merchant removal. Reproduced with aggregate-only smoke observations and an
  authored fixture; no frozen inputs read. Azure controls separately passed.
- Orchestrator approved the minimal product guard with explicit B1/mock-P/CI and
  disclosure conditions. Code commit **`4fee1ee3db7428a5564ecbc634bb62e0ae7049d5`**
  excludes blank merchant evidence; three authored regressions passed.
- `evals.runner --system B1`: **32/32**, 12 readbacks, safety guards passed.
  Existing mock P dev harness in a new preserved output directory: **20/20
  no-fault + 12/12 faults**, all triggers, **0/32 unsafe/forbidden**, no errors,
  **$0**. Confirmation was not loaded/repeated; prior paid results remain intact.
- [Post-gate disclosure and commands](../evaluation/after-v2-dev-gate.md) and
  [release notes](../evaluation/v3-release-notes.md). No learned threshold,
  prompt, policy or frozen-gold change.

### Done but not verified

- Fix still needs green PR/main CI and a rebuilt API release. Azure remains in
  mock mode at the earlier candidate; the full release smoke is not yet passed.
- V3 budget is prepared with **$0 / $3**, cumulative worst-case including new
  smoke **$6.45037557 / $12**. No final-program worker or v3 outcome exists.

### Next / blocked

- Merge with green CI, continue the approved release, then prepare/verify v3
  receipts and STOP for the separate go. Never access v1 or rerun held-out v2.

## 2026-09-27 — Step 4 v3 release preparation in progress

### Completed (verified)

- Accepted dev gate remains 20/20, blind 18/20, 12/12, 0/52 unsafe, B1 32/32.
  Merged suite #50 at **`a07e7fcf675f9fc2c1d9fc8a7c51abaf3de5caa1`** after
  four green checks, using description/metadata only. Manifest matches approved
  `ecf3f6313f33359fed892de1b3537edc4ae8e854dd5bfa8da1fc8845daa41177`.
- Copied only the authorized private binding into ignored
  `artifacts/evaluation-v3/customer-bindings.json`, mode 0600; checksum matches
  frozen provenance `0c31ea3301961d9ff07f28322c6d92a8eeaf0f30829c850ae474e2a86eba6fa8`.
  No binding contents printed; no scenario/selection/authoring-tool contents opened.
- Generic runtime now targets test-v3 and its separate binding/artifact paths,
  100 B1 + 160 Gemini case-runs, preselected repeats/judges, no frontier/calibration
  calls, and a separate $3 lifetime scope. Preparation reads metadata only; start
  remains gated. Checkpoint/resume and budget-denial behavior remain enforced.
- `make checks`: **274 passed / 14 database skips**, B1 **32/32**, hooks, strict
  typing, compilation and interface/policy checks passed. Disposable local
  `python -m scripts.test_postgres`: **16/16**, including persistent reservations,
  prior-scope closure and refusal to reset the v3 breaker. Terraform format passed.
- Rechecked pinned provider prices without model calls. Updated release smoke
  for prompt v5.1 and explain→offer→deny; new combined API/browser smoke cap $0.10.
  [V3 plan, workload, budget arithmetic and exact commands](../evaluation/final-run-plan.md).

### Done but not verified

- Runtime support needs PR/main CI, image build/push, deployment, full Azure
  smokes/access readback and fresh `jev-release.json`.
- V3 durable scope/preparation receipts have not yet been created. Suite execution
  and adapter behavior on frozen v3 remain unverified and are not attempted here.

### Next / blocked

- Complete the authorized release in Seb Azure Sandbox only; prepare v3 and
  report exact SHA/evidence, then STOP for the separate v3 go. No v1 access or
  held-out v2 rerun. PT/dialect human review remains a limitation.

## 2026-09-27 — Single authorized after-v2 follow-up: dev gate passed

### Completed (verified)

- Reviewed PR #54 at `c28c7479d87d922440949791bf5d6d559fbbfe22`: all four CI
  checks passed. Zero-cost replay returned `unfamiliar_charge=false` for all four
  authorized no-fault openings; the four preservation regressions also passed.
  Merged at **`75629945f36f2767bccbaddaf6fad2707ed8681f`**, including lead #55.
  Verified the merged tree is identical to the green reviewed head. The inherited
  squash-body CI-skip marker suppressed its main push workflows; this report PR
  uses an explicit merge body, with main CI required before the session closes.
- Ran the authorized full gate **once**, detached on that clean merged candidate:
  `LLM_REAL_CALLS_APPROVED=1 LLM_FINAL_RUN_STARTED=0 .venv/bin/python -m scripts.dev_gate real --profile after-v2 --attempt 2`.
  **No-fault 20/20 (ES 10/10, PT 10/10); confirmation 18/20 (ES 10/10,
  PT 8/10); faults 12/12, all triggers reached; unsafe/forbidden 0/52**.
  Zero execution errors, 52 completed checkpoints; worker exited. Confirmation
  failures remain blind. The first run and unchanged input hashes are preserved.
- `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 LLM_FINAL_RUN_STARTED=0
  .venv/bin/python -m evals.runner --system B1`: **32/32**, 12 readbacks,
  safety guards passed on the merged candidate.
- `.venv/bin/python -m scripts.after_v2_budget` final readback: this run's known
  model cost **$0.129836782**; durable increase **$0.12983704**. Shared scope
  **`dev-gate/after-v2`**, run **`after-v2`**, lifetime charge **$0.27667768 / $1**,
  304 total attempts, zero unknown costs/outstanding reservations. Cumulative
  prior plus dev charge **$3.35037557**. No budget reset or new allowance.
- [Aggregate report and verification evidence](../evaluation/after-v2-dev-gate.md).
  Ignored output: `artifacts/after-v2-dev/gate-real-followup/results.json`;
  budget receipt: `artifacts/after-v2-dev/budget-after-followup.json`.

### Done but not verified

- Step 3 dev acceptance is met; the candidate has not been deployed or tested
  through Azure/browser/LLM release smokes. No held-out improvement is claimed.
- Confirmation retains two failed PT cases, uninspected. PT/dialect wording
  still lacks fluent-human review.

### Next / blocked

- Stop for the separate release/v3 decision. No further dev repeat is authorized.
  PR #50 remains unmerged and suite-v3 rows unopened. Never access abandoned v1
  or rerun held-out v2; official v2 remains unchanged.

## 2026-09-27 — Named neutral-charge guard follow-up

### Completed (verified)

- Kept prompt v5.1 wording as the primary unfamiliarity fix. The postprocess
  backstop now covers neutral ES/PT what/why questions with charge articles and
  named-merchant suffixes; a separate non-recognition clause remains eligible
  to set `unfamiliar_charge=true`.
- Added mock regressions for the four authorized dev openings
  (`es.pending.v2`, `es.declined.v2`, `pt.pending.v2`, `pt.declined.v2`), four
  named-charge paraphrases and a neutral question followed by “no lo reconozco”.
  No frozen confirmation or suite-v3 rows were opened; no paid calls were made.
- Targeted NLU mock tests: **46 passed** (frozen-followup test excluded); after
  correcting two stale prompt-ID assertions, the affected mock selection passed
  **48 tests**. Ruff and strict mypy pass.
- Merged current main `ff570f8` into the PR #54 branch. Preserved both the prior
  AI-lane and lead progress entries.

### Done but not verified

- The first full CI run found two stale assertions for `nlu@v5`; both now expect
  the active `nlu@v5.1` ID. The corrected code head `2e346c6` passed all four
  checks: Python, invariants, Postgres and web/browser. This final log-only
  commit will also receive a full CI run before reporting its head.

### Next / blocked

- The lead reviews and merges; the lead reruns the dev gate after merge. No paid
  gate rerun was made.

## AI lane — narrow unfamiliar-charge cue for after-v2 gate, 2026-09-27 UTC

### Completed (verified)

- Bumped [NLU prompt](../../prompts/nlu/v5.md) to v5.1, SHA-256 `e40182de2f232932a12d61d722be5e6356d787217048378fbc2a84f330d241cc`. `unfamiliar_charge` stays tied to bare unfamiliarity in a charge inquiry. Postprocessing preserves semantic model flags except for neutral what/why/status questions and explicit denials; denial wording such as “no fui informado” no longer trips the denial fallback. Added focused ES/pt-BR regressions for the three lead findings.
- Targeted mock Ruff and pytest checks passed (35 selected cases). Tests used the four reported no-fault utterances and new unit examples; no paid call or dev gate run occurred. This branch does not alter fixtures or frozen data.

### Done but not verified

- The lead has not rerun the no-fault dev gate on this prompt revision.

### Next / blocked

- Follow-up PR [#54](https://github.com/sebastian-gm/bank-agent-lab/pull/54) is open for lead review. The initial automation was canceled after a mistaken interpretation of the test-scope instruction; the corrected head requires full Python, Postgres, web and invariant CI before merge. The lead reruns the no-fault gate and merges after review. No paid call or dev-gate call occurred.

## 2026-09-27 — Authorized dev-only follow-up in progress

### Completed (verified)

- Inspected saved evidence only for the four failed no-fault cases: ES/PT pending
  and declined. Each has an incorrect `unfamiliar_charge=true` NLU observation,
  followed by an unwanted offer and two uncertain replies ending in `ESC-04`.
  MATCH, recorded-status policy and final-outcome scoring behave as designed.
  No confirmation failures or suite-v3 inputs inspected; diagnosis cost **$0**.
- [Per-case diagnosis and ownership](../evaluation/after-v2-dev-gate.md): AI lane
  owns the NLU/prompt distinction; lead owns preserving the recognition-specific
  clarification through NLG. Relayed the AI causes to the orchestrator.
- Authored ES/PT regressions reproduced NLG dropping the recognition question.
  Lead fix keeps the code-authored localized question while an offer is active.
  Targeted conversation/attempt checks passed; no fixture or threshold changes.
- Added guarded `--attempt 2`: preserve the original run, require unchanged inputs
  and a completed failed first gate, refuse another attempt or overwrite, and
  retain **scope `dev-gate/after-v2`, run `after-v2`, lifetime cap $1**.

### Done but not verified

- Lead changes still need final CI/merge and integration with the AI fix PR.
- The single authorized full-gate follow-up has **not** run. Estimate $0.15–$0.30
  within the already approved shared cap; prior dev charge remains $0.14684064.

### Next / blocked

- Review/merge the AI fix and lead changes with green CI, then run all 52 cases
  once with `scripts.dev_gate real --profile after-v2 --attempt 2` on merged main.
- Keep confirmation blind. Report and stop after that gate, including if it misses.
  No release, suite-v3 access/merge or v3 run. Abandoned v1 remains untouched.

## 2026-09-27 — Step 3 merged and measured: dev gate not passed

### Completed (verified)

- Reviewed/merged frontend #52 into the lead branch, then combined #51 into main
  at **`2c8679cbe9b0dd93a55fc85f0b15d17a8e662ab3`**, each exact head with four
  green checks. Main CI `36360383303` and safety `36360383319` also passed.
- `make checks`: **234 passed / 14 database skips**, B1 **32/32**, 12 readbacks,
  safety guards, hooks, strict mypy, compilation and generated contracts passed.
  `python -m scripts.test_postgres`: **16/16**. Browser CI: **29/29**.
- Ran the authorized detached command
  `LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.dev_gate real --profile after-v2`
  once on clean merged main. All **52/52** cases checkpointed; worker exited.
  **No-fault 16/20 (ES 8/10, PT 8/10); new confirmation 17/20 (ES 10/10,
  PT 7/10); faults 12/12 (all triggers reached); zero unsafe/forbidden actions**.
  Zero execution errors. Gate **failed** the no-fault minimum of 18/20.
- Shared durable **scope `dev-gate/after-v2`, run `after-v2`, lifetime cap $1**:
  known cost **$0.146840366**, durable charge **$0.14684064**, 160 attempts,
  zero unknown-cost attempts. Cumulative prior plus dev charge **$3.22053853**.
  `python -m scripts.after_v2_budget` provides the final aggregate readback.
- [Full aggregate report and commands](../evaluation/after-v2-dev-gate.md).
  Results are in ignored `artifacts/after-v2-dev/gate-real/results.json`.

### Done but not verified

- The Step 3 fixes and frontend integration are merged, but paid dev acceptance
  is not satisfied. No claim of release readiness or held-out improvement.
- Deployment and Azure/browser/LLM release smokes were not run for this layer.
  PT/dialect wording still lacks fluent-human review.

### Next / blocked

- Stop for Sebastian/orchestrator's dev-only follow-up decision on the 16/20
  no-fault result. Do not repeat or tune on frozen confirmation cases.
- No release or v3 run. PR #50 remains unopened and unmerged pending a passed
  dev gate and separate approval. Never access abandoned v1 or rerun v2.

## 2026-09-27 — Lead Step 3 implementation and dev validation in progress

### Completed (verified)

- Reviewed/merged AI #49 at `dc0a9f94edd91b46f9df46fd4b37fc8431f7f192`, exact-head
  Python/Postgres/web/safety green. Requested and verified the missing
  `unfamiliar_charge` flag before merging. Lead consumes v5 context and masked facts.
- Implemented durable offers, context retention, full handoff reasons, cross-customer
  strikes/revocation, policy review ordering, B1 numeric-merchant handling, readback
  aliases and strict slice recall. Added dev regressions; never ran held-out v2 or
  opened suite-v3 rows. PR #50 description only was read for generic dependencies.
- `.venv/bin/python -m scripts.v2_slice_correction`: saved-v2 aggregate tables written
  separately; **853 inputs unchanged**. Official v2 result is unchanged.
- `python -m scripts.dev_gate mock --profile after-v2`: **20/20 no-fault, 12/12 faults**,
  all 12 triggers reached. B1 runner **32/32**, verified readbacks and safety checks.
- Final combined local `make checks`: **234 passed / 14 database skips**, hooks, strict mypy,
  compilation, B1, interface snapshots and policy catalog passed. Local disposable
  Postgres tests passed **16/16**, including offer and security-strike restart
  recovery. Runtime policy 1.3.0 identifies the changed control/routing semantics;
  numerical thresholds are unchanged. PR #51 is in fresh CI.
- Implemented #37 trace metadata and approved, scoped demo-story hints; seven staff,
  metadata and policy tests passed. Owner-approved model-run estimate is $0.15–$0.30
  under shared scope `dev-gate/after-v2` / run `after-v2`, hard $1 cap.
- Reviewed frontend #52 and merged its exact green head into the lead branch at
  `879c1b3e034c9c3f4eacbbd6f24c58200677de25` (four checks, including 29 browser checks).
  Added a narrow contextual fallback for typed ES/PT recognition labels after
  reproducing four B1/P failures from the frontend report. All 19 authored
  conversation regressions pass; isolated yes/no still requires clarification.

### Done but not verified

- Final candidate merge/CI and paid dev acceptance are pending. No new release,
  Azure smoke or v3 execution. Frontend offer/cancellation/reason support is integrated.

### Next / blocked

- Finish combined CI, merge lead fixes with green CI, run the authorized
  dev gate on the merged SHA and report. Do not merge #50 without the separate go.
- [Commands, changes and budget](../evaluation/after-v2-dev-gate.md). Stop after the
  Step 3 report; release/v3 still require Sebastian's later approval.

## 2026-09-27 — ADR merged; shared after-v2 dev allowance prepared

### Completed (verified)

- Behavior contract PR #48 merged after all four checks passed at
  **`ab07bfeba23824292bfd83a13e4934c6ff1ae349`**; announced the SHA for independent
  v3 authoring. Confirmation freeze #47 merged with fresh green CI at
  **`3ad29bc388e4b9d09bbd84266a87c9e8c66b419f`**. Hash-only comparison confirmed
  the two frozen files unchanged from `0692881`; no confirmation rows opened.
- `.venv/bin/python -m scripts.after_v2_budget --prepare` created and read back
  the shared durable **scope `dev-gate/after-v2`, run ID `after-v2`, lifetime cap
  $1.00**. All paid dev callers must use both identifiers with Postgres
  reserve-before-call accounting. Initial receipt: zero attempts, $0 charged,
  zero unknown costs; ignored `artifacts/after-v2-dev/budget-prepared.json`.
- Previous evaluation/Option A scopes are closed to new reservations with all
  history and outstanding charges retained. Prior exposure $3.07369789 plus
  the $1 dev and prospective $3 v3 limits totals $7.07369789, below $12.
  Budget arithmetic tests passed; this setup made no model calls.

### Done but not verified

- Lead Step 3 implementation is in progress on a feature branch. Prompt v5,
  NLG and dev integration are pending from the AI lane; no new dev gate run.

### Next / blocked

- Implement and verify the accepted contract on dev data, integrate the AI PR,
  then run the shared-budget dev gate and report. No release or v3 execution
  is authorized. Never access abandoned v1, rerun v2 or open suite-v3 rows.

## AI lane — after-v2 explain/offer dev confirmation, 2026-09-27 UTC

### Completed (verified)

- Read handoff 13 and authored the 20-case synthetic [explain/offer confirmation set](../../src/aclara/llm/dev_explain_offer_20.yaml) before any v5 prompt, NLG, or scenario implementation change. Its separate first commit `0692881` freezes the file and [SHA-256 manifest](../../src/aclara/llm/dev_explain_offer_20.sha256). Structural validation passed: 20 unique cases, 10 ES/10 pt-BR, 10 denial/10 recognition follow-ups, and no verbatim opening overlap with dev-v2.
- Read merged ADR-0015 at `ab07bfe` and aligned [NLU v5 and grounded ES/PT offer templates](../ml/dev-explain-offer-v5.md) to `offer_dispute` / `awaiting_dispute_decision` and the internal recognition signal. The scenario adapter reads the frozen hash and supplies explicit offer, choice and confirmation replies. `make checks` passed: 186 tests / 13 skips, B1 dev 32/32, Ruff and strict mypy. No paid call or suite-v3 row access occurred.
- Addressed the lead's PR #49 review: `ExtractedNlu.unfamiliar_charge` now distinguishes bare unfamiliarity from ordinary status questions in ES and pt-BR, including degraded fallback and model postprocessing. The AI execution record includes the signal. Full mock `make checks` passed after the change: 204 tests / 13 skips, B1 dev 32/32, Ruff, formatting, strict mypy, interface and policy checks. The shared `dev-gate/after-v2` scope and `after-v2` run ID are confirmed at $0 before any AI paid call.

### Done but not verified

- The new set's slang and labels are AI-authored, not fluent-human reviewed. End-to-end dev behavior and real-model prompt v5 remain unverified until the lead's executable response contract, simulator and scorer changes merge.

### Next / blocked

- Lead merged fixture PR #47; next integrate additive `offer_dispute` API/scenario/scorer behavior, then run the dev gate. Every paid dev call must reserve through the now-created `dev-gate/after-v2` scope with run ID `after-v2`, within its shared $1 lifetime cap. Do not open suite-v3 rows; lead merges AI PRs after CI.

---

## 2026-09-27 — Handoff 13 Step 1: accepted behavior specification

### Completed (verified)

- Routine merges finished: #46 analysis at `7914022`, then #45 reviewed wording
  at **`4470ba4957c7f90f54ac28e887bc3119ed99a02e`**. Each exact PR head passed
  all four CI checks before merge. Only A20/W02 wording was applied; local
  `make checks` passed (174 tests / 13 skips, B1 32/32).
- Read handoff 13 fully. Wrote [ADR-0015](../adr/0015-post-v2-conversation-and-policy-contract.md)
  and the [normative v3 behavior contract](../../contracts/interfaces/conversation-policy-v3.md)
  before behavioral code changes: nonterminal explanation/dispute offer,
  recognition/denial transitions, SAR, multi-reason handoffs, cross-customer
  actions, business-date age, and type/data rule precedence.
- Independently calculated the worked boundary: bank date 2026-06-17 minus
  84/85 days gives 2026-03-25/2026-03-24. Document links, whitespace and staged
  safety checks are checked before committing this specification.
- Orchestrator identified confirmation freeze PR #47, `0692881`, with log
  commit `857228e`, authored before fixes. Its rows have not been opened here.

### Done but not verified

- This is an accepted specification, not a claim that Step 3 is implemented.
  Runtime schemas will be regenerated with the additive interface changes.
- Prompt v5/NLG/dev integration is still being prepared by the AI lane on
  `feat/ai-explain-offer-v5`; it waits for this contract's merged SHA.

### Next / blocked

- Merge this specification with green CI and report its exact SHA immediately
  so the independent lane can author v3. Merge #47 after its remaining CI passes.
- Implement lead Step 3 on dev only, using `dev-gate/after-v2` for any approved
  real calls (new $1 cap). Never rerun v2 held-out cases or open suite-v3 rows.
  Keep official v2 outputs unchanged; saved-slice reporting corrections must be
  separate, disclosed artifacts. No release/v3 run before Sebastian's later go.

## 2026-09-27 — Routine post-v2 merges and accepted pt-BR wording

### Completed (verified)

- Opened and merged analysis PR **#46** after all four checks passed: Python,
  Postgres, web/browser and safety. Merge SHA: `791402214a2d8d5829c6c6e9e1208e80a2679945`.
- Reviewed #45's documentation and proposed patch against the actual workflow.
  Accepted A20 (destination is a person on the team) and W02 (verification code,
  then confirmation); retained A15 because the handoff already exists and is
  durably read back before the reply. Applied exactly two pt-BR string changes.
- Exact source replacement and normalized AST comparison confirmed no logic
  change. `git apply --check` passed before application. With
  `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 LLM_FINAL_RUN_STARTED=0`,
  `make checks` passed: six hooks, strict mypy, file policy, compilation,
  **174 tests passed / 13 database-dependent skips**, B1 **32/32**, interfaces
  and policy catalog. No paid calls, deployment, held-out access or reruns.
- Updated #45 from main with a history-preserving merge, retaining both
  progress-log entries. Fresh PR CI is required before merge.

### Done but not verified

- Fluent-human pt-BR review is still pending. The two strings have not been
  redeployed to Azure; final v2 remains tied to its original evaluated SHA.

### Next / blocked

- Complete #45's green-CI merge and check main. Sebastian then authorized
  handoff 13: merge the explain/offer/dispute and handoff/security/age/policy
  specification first, report its SHA, then implement lead-owned fixes on dev
  only. Never rerun v2 held-out cases or open suite-v3 rows. No release or v3 run
  is authorized by this step.

## AI lane — lead-owned pt-BR wording review, 2026-09-27 UTC

### Completed (verified)

- Reconciled the previously stated 34-string inventory to **35 active strings**, all found in current lead-owned API, workflow, handoff and staff source; Sebastian explicitly approved reviewing all 35 under the unchanged new $0.30 cap.
- Created and read back separate durable scope `pt-review/lead-strings` / run `lead-strings`, cap $0.30. Nine sequential Sonnet calls reviewed 35/35 in batches of at most four with 3072 maximum output tokens. All nine responses were valid and complete; scope readback was **$0.048878 known and charged, zero unknown-cost attempts**. No final-v2 budget scope was used.
- Rejected one model suggestion after checking the handoff packet's real creation/readback order. Proposed two wording changes only in [the lead-review patch](../ml/pt-review-lead-proposed.patch); `git apply --check` passed and lead-owned source files remain unchanged. [Before/after decisions](../ml/pt-review.md) are recorded.

### Done but not verified

- Model review is not a fluent-human pt-BR review. The proposed wording has not been applied or verified in an app build.

### Next / blocked

- Lead reviews the proposed patch after final v2 finishes, applies any accepted wording in the lead lane, and merges this documentation PR. Keep this PR unmerged during the freeze.

---
## 2026-09-27 — Final v2 COMPLETE; post-hoc analysis; STOP

### Completed (verified)

- Authorized v2 finished on release **`fd34c7dce11cf9db6f71e84ae4fbb2ccc19de415`**:
  700 system case-runs and 150 judge items, about 2h20m, no restart/resume.
  `final_program status`, the completion receipt and host process inspection
  confirmed COMPLETE and no remaining worker. The watchdog extension preserved
  the original start time and used 15-minute stale-progress / 3h30m limits.
- Main equaled origin/main and was clean after completion. Evaluation/runtime
  code, frozen suite and official results remained unchanged during the run.
  No abandoned-v1 artifact was opened or modified.
- Durable budget aggregate readback: v2 **$2.94519961**, 1,801 reservations,
  zero unknown costs; known cumulative **$3.06646189**, charged/reserved exposure
  **$3.07369789**, below $12. Older scope exposure was read only from aggregate
  Postgres budget accounting. The v2 scope limit remains $11.87.
- Official SAR: B1 **41/193**, Gemini **39/193**, Sonnet **26/98** on its fixed
  subset. Pass: **65/200, 63/200, 37/100**. **None passed all safety gates**;
  the report does not claim acceptance or improvement. Judge pairs: 143/150;
  seven ModelFailure items were not rerun. The human sheet has 20 blank items at
  `artifacts/final-program-v2/human-judge-20.csv`.
- Wrote [final v2 error analysis](../evaluation/final-v2-error-analysis.md),
  including all seven requested questions, headline metrics and cost. Ran the
  ignored offline `posthoc-analysis.py`, `posthoc-causes.py`, `posthoc-checks.py`
  and `posthoc-final-counts.py` under `artifacts/final-program-v2/`.
  Reads are logged through `evals.access`; SHA-256 checks confirmed **863 inputs
  unchanged**, including all result checkpoints, frozen metadata and official
  result/completion files. No model calls, reruns, rescoring or code fixes.
- `git diff --check` and staged `pre-commit run` passed: strict mypy, data-file,
  secret and large-file policies. Ruff hooks correctly skipped the Markdown-only
  change. No application tests or paid calls were rerun for documentation.
- Findings: category rates; fixture 85/84-day mismatch behind the forbidden
  filing; gold-target versus actual-action readback distinction; 15 absent and
  24 reason-mismatched Gemini transfers; 47 terminal-dispute gold conflicts
  with the inquiry label rule; confirmed presence/strict slice metric bug;
  dev/final contract and B1 numeric-merchant matching gaps. One intentional B1
  readback fault handed off without reporting successful filing.

### Done but not verified

- Human judge ratings and fluent-human Portuguese review remain pending.
  Post-hoc causes have not been tested by reruns, and no adjusted/improved
  held-out score is claimed. No live per-action database reconciliation was
  performed during this documentation-only analysis.
- #37's additional backend API work and the separate video redeploy remain
  deferred. The unchanged Azure deployment is not being re-released here.

### Next / blocked

- **STOP after reporting.** Sebastian reviews the human sheet and decides the
  next development task. V2 remains the official failed-gate result. Future
  fixes need fresh evaluation evidence; never reuse this analysis to claim a
  held-out improvement, and never access the abandoned v1 directory.
- No new cost or deployment approval is requested for this completed analysis.
  Later: **Continue from docs/status/progress-log.md. Next layer: [X]. Same rules.**

## 2026-09-27 — Option A re-release verified; STOP before final v2

### Completed (verified)

- Merged #39 first, followed by the cumulative-budget preparation (#42) and
  exact smoke-run Terraform allowlist fix (#43). Runtime smoke SHA:
  **`a52a8f3389a72e321c3b587a8063215a38383564`**. CI `36343084749`, safety
  `36343084792`, and external-access workflow `36343714530` all passed.
- Built and pushed both private images, set the ignored `image_tag`, reviewed
  both Terraform plans, and ran `python -m scripts.azure_dev apply` for mock
  and real stages. Ingress/capacity, database and storage stayed unchanged.
  `python -m scripts.azure_verify` passed in both stages: owner IPv4 HTTPS,
  internal API, app login, TLS database, approved Azure-services firewall
  exception, managed identity/Key Vault and $30/$50 budget alerts.
- `python -m scripts.azure_smoke` passed in mock mode: four personas, 15 scoped
  transaction projections, two cases, four handoffs, two claims/resolutions,
  and case recovery in the same session after an API replica replacement.
  All three surfaces used organizer serving; no model calls in this stage.
- `python -m scripts.azure_llm_smoke` passed all three real paths (ES dispute,
  PT ambiguity, fraud). `python -m scripts.serving_browser --target azure`
  passed customer chat, Agent Desk and Ops, with one handoff resolved.
  Combined durable smoke readback: **$0.00778471 / $0.10**, 11 attempts,
  four conversations, zero unknown-cost attempts. API cases had no fallback.
- Private evidence is under `artifacts/azure/`: `option-a-serving-smoke.json`,
  `option-a-release-smoke.json`, `option-a-browser.json`, image/plan receipts,
  and `jev-release.json`. The release receipt binds the final main SHA to the
  smoked digests and records any documentation-only retag, its fresh controls,
  no-model-call BFF readback, CI/safety and external-denial workflow.
- V2 budget prepared and read back with **zero attempts / $0**: scope
  `final-evaluation-v2`, run `final-program-v2`, cap **$11.87**. Prior scopes are
  closed without resetting history. V1 reserved exposure **$0.02058083** plus
  dev **$0.10791745** plus the v2 limit = **$11.99849828**, below $12.
  The unsettled v1 reserve is retained. No abandoned-v1 artifact was accessed.
  Preparation receipt: `artifacts/final-program-v2/prepared-budget.json`.
- Local Python tests, 15 Postgres integration tests, Ruff, strict mypy,
  Terraform formatting/validation and private-image import checks passed
  during release preparation. Live East US 2 estimate remains **$34.63/month**.

### Done but not verified

- No final-v2 evaluation, results, judge agreement or human ratings yet.
  V2 is prepared only; no launcher or worker was started.
- #37's optional backend API additions remain deferred until after v2 and a
  separate video deployment. The Azure-services database firewall exception
  remains the documented dev limitation; private access is future work.

### Next / blocked

- **STOP. Await Sebastian's separate final-v2 go after the release gates.**
  Start/resume commands and cumulative-cap enforcement are documented in
  [final-run-plan.md](../evaluation/final-run-plan.md). Never resume v1.
- Continue from docs/status/progress-log.md. Next layer: explicitly approved
  final-program-v2 execution. Same rules.
- Disclosure: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed.

## 2026-09-27 — Approved Option A re-release preparation

### Completed (verified)

- Merged #39 at its all-green head; merge `5608e6b73a68c69b562f9a9c897b3109e3f0b868`.
  Corrected its stale deployment/confirmation status in this follow-up.
- `python -m scripts.azure_prices`: live East US 2 estimate **$34.63/month**,
  below the approved $40 stop gate (no new resource class or public access).
- Aggregate Postgres budget readback: v1 exposure **$0.02058083**, including one
  unsettled reserve; dev **$0.10791745**. The earlier v1 $0.0119 figure omitted
  part of reserved exposure. No abandoned-v1 artifact was opened.
- `python -m scripts.test_postgres`: **15 passed**, including v2 preparation,
  cumulative cap, preserving unsettled reserves, closing prior budgets and
  refusing to re-enable a tripped breaker. Focused final-run tests passed;
  Ruff and strict mypy passed.
- Prepared the launcher/budget support for `artifacts/final-program-v2/`, scope
  `final-evaluation-v2`, run `final-program-v2`, **$11.87** cap. Combined maximum
  at current reserved exposure: **$11.99849828**. Runtime start/resume verifies
  the closed prior scopes and reduced cap; it cannot initialize/reset budgets.
- Fresh release smoke identity is `production/option-a-release-smoke`, **$0.10**
  across API and browser, maximum five attempted conversations. Old smoke
  accounting remains intact. Estimated new smoke usage: **$0.01–$0.03**.

### Done but not verified

- New image build/push, Terraform plan/apply, deployed smoke, browser, external
  access and release receipt remain pending the prepared main release SHA.

### Next / blocked

- Run the approved Step 4 release gates, update this log with evidence, report
  the exact SHA and **STOP**. Do not start v2 without Sebastian's separate go.
- Skip #37's backend API additions until after v2 and a separate video redeploy.

## 2026-09-27 — Option A Step 3 complete; STOP before re-release

### Completed (verified)

- Merged #40 after all four checks passed (CI `36340363242`, safety
  `36340363197`). Tested candidate: **`f6813279620feb1869498fcbcc40cc8c59ad53ae`**.
- Ran `LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.dev_gate real`
  once on the clean committed candidate; exit 0, all **52/52** checkpoints saved.
  **No-fault 20/20 (ES 10/10, PT 10/10); confirmation 20/20 (10/10 each);
  faults 12/12 (6/6 each), all triggers fired; zero observed unsafe outcomes in
  every category and zero forbidden actions.** No remaining failed gate cases.
- The route made 50 Gemini NLU + 17 Gemini phrasing + 50 Jev risk calls, all
  valid, with zero degraded NLU events or unknown-cost attempts. Known gate cost
  **$0.08043419**. Postgres readback: **$0.10791745 / $1.00**, 157 reservations,
  scope **`dev-gate/option-a`**, run **`option-a`**, enabled. This includes the
  AI lane's earlier diagnosis and conservative reservation rounding.
- Original B1 **32/32**, reactive B1 **32/32**, structured mock P **32/32**;
  local pytest, Ruff, strict mypy, interface/catalog checks, schema validation,
  and changed-file pre-commit checks passed. Details and commands are in the
  preceding preparation entry.
- [Acceptance report](../ml/dev-p-failure-analysis.md) and
  [aggregate JSON](../ml/dev-p-gate-results.json) record the tested SHA. Private
  evidence: `artifacts/option-a-dev/gate-real/`. No code, fixtures, prompts,
  thresholds or confirmation bytes changed after the real gate began.
- Frozen choice audit remains counts only: 200 explicit behaviors; 152 usable
  target-matching overlay references; 48 not statically proven (45 without a
  target, 3 with one); zero new fallback users. No outcome/text report or binding
  access. Abandoned v1 artifacts stayed untouched.

### Done but not verified

- No Azure verification of this new candidate: deployment, Azure smoke and
  browser checks are deliberately pending the next approval.
- No final v2 evidence, new judge agreement, or human ratings. Dev acceptance
  is one authored-fixture pass, not an organizer-ledger final evaluation.
- Optional glass-box API additions remain deferred.

### Next / blocked

- **STOP. Await Sebastian's re-release approval.** The later release must pass
  the Azure gates and return its exact SHA for a separate final-v2 start signal.
- V2 must enforce $12 minus preserved v1 spend and all Option A dev charges;
  no v2 budget/output run has been initialized in this step.
- Continue from docs/status/progress-log.md. Next layer: approved re-release and
  Azure verification, then stop before final v2. Same rules.
- Disclosure: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed.

## 2026-09-27 — Option A lead integration and dev gate preparation

### Completed (verified)

- Merged #36, #28, #24, #37 in order after all four checks passed on each
  updated head. Conflicting branches used history-preserving merge updates as
  requested. #37 merge: `b3e8f1501ab932970626478457d751e958a26cca`.
- Reviewed and merged #38, including the AI root-cause report and generic
  transaction-type normalization. Fresh CI: `36339767762`, safety:
  `36339767753`; merge `55cea748f539fa8589b008f75edccf1e748f6ae6`.
- Shared durable dev budget is **scope `dev-gate/option-a`, run `option-a`**,
  cumulative cap **$1.00**. Initial readback was zero; AI reports 40 attempts and
  $0.02748308 charged before lead acceptance. Every lane must share both names.
- Generic simulated customer selects its known target only when offered;
  explicit replies/refusals win. Corrected authored dispute/fault requests to
  explicit denial/filing, leaving gold outcomes, MATCH thresholds and policy
  unchanged. Faults without a gold transaction declare customer knowledge.
- `.venv/bin/python -m scripts.dev_gate mock`: structured P diagnostic **20/20**
  no-fault, **12/12** faults with all triggers reached; zero unsafe/forbidden
  actions. `.venv/bin/python -m evals.runner --system B1`: original **32/32**, safety
  guards passed. Direct `evals.reactive.execute(..., "B1")` on corrected v2:
  **32/32**, all 12 faults reached, zero unsafe. Receipts in ignored
  `artifacts/option-a-dev/`.
- `.venv/bin/pytest -q`: suite passed (Postgres-only tests skipped locally;
  their CI job passed on #38). `.venv/bin/ruff check .` and strict mypy passed.
- Confirmation metadata verified without reading conversation text: 20 cases,
  10 ES / 10 PT, no faults; bytes unchanged from pre-fix commit `88288a9`.
- Authorized static frozen choice audit, `.venv/bin/python -m
  scripts.audit_simulator_choices`: 200 explicit behaviors, 152 target-matching
  overlay references; 48 unproven explicit behaviors (45 without a target,
  3 with a target). Zero frozen cases use the new fallback. Counts only;
  suite hashes unchanged, no bindings/results accessed. These are structural
  counts, not executed path coverage. The abandoned v1 directory stayed untouched.

### Done but not verified

- Real Step 3 acceptance runner is prepared with per-case checkpoints,
  metadata-only/validated call journals, and the shared reserve-before-call
  Postgres cap. Paid acceptance and confirmation results are not yet available.
- Optional #37 backend glass-box additions are deferred to keep this layer
  focused on acceptance; no new deployed behavior is claimed.

### Next / blocked

- Run the committed candidate's real 20 dev + 12 fault + 20 confirmation cases
  under the approved shared $1 cap; report numbers and remaining failures.
- **Stop before re-release.** No cloud deployment or final v2 start is authorized.
  No changes based on confirmation results. The 3 target-bearing frozen explicit
  behaviors remain a disclosed static limitation; do not tune or edit suite bytes.
- Disclosure: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed.

## AI lane — Option A dev-P gate, 2026-09-27 UTC

### Completed (verified)

- Read handoff 12 and froze a fresh 20-case synthetic confirmation set (10 ES, 10 pt-BR) in the first commit of this branch **before** changing NLU. Schema and unique IDs passed; it has not been run or tuned.
- Reproduced the 9 original no-fault failures and 8 unreached fault fixtures on the mock path: 9/9 no-fault objectives passed and 8/8 faults fired. Traced all 17 real-P synthetic dev cases under the lead's existing shared Postgres `dev-gate/option-a` $1 scope; [per-case analysis](../ml/dev-p-failure-analysis.md) separates generic-type NLU extraction from choice/customer-simulator and conflicting fixture expectations.
- Tightened NLU v4 and normalized generic `cargo/cobro/cobrança/charge` out of `type_expr`; a matcher-backed dev regression passed. A single post-fix `pt.pending.v2` real-P check passed with the correct target and explanation. Scope readback: 40 settled attempts, $0.02748308 known and charged, zero unknown-cost attempts. The local `.env` approval flag was not changed; approval was process-local for the authorized calls.

### Done but not verified

- The complete 20-case no-fault and 20-case confirmation real-P acceptance gates have not run on the merged candidate. The original P study omitted intermediate slots, so the new trace is a same-case reproduction; the original `pt.pending.v2` slot cause remains a supported hypothesis rather than a recorded original fact. No NLG cause was found.

### Next / blocked

- Lead reviews the fixture/simulated-customer and matcher handoff in the analysis, merges the AI PR, then runs the full Step 3 gate under the same shared scope. Stop before re-release and final v2 until Sebastian's later signal. Never open the abandoned final-v1 artifacts or frozen held-out inputs in this diagnosis.

---

## Option A — dev gate before any re-release (in progress)

### Completed-verified

- Read handoff 12. The first final attempt is abandoned: a first final attempt was stopped at ~6/200 P cases after a dev-only finding; its results were never viewed. Its artifacts remain untouched; do not open or resume them.
- Initialized and read back the shared Option A Postgres budget: **scope `dev-gate/option-a`, run ID `option-a`, cumulative cap $1.00**, zero attempts and $0 charged at initialization. Both lead and AI lanes must use `PostgresSpendGate(store, scope="dev-gate/option-a", run_id="option-a")` before every provider attempt, including Jev, retries and fallbacks. Unknown usage retains its reservation. Never create separate run IDs, reset reservations, raise the cap, or re-enable a tripped breaker. Prior closed study budgets are excluded from this new allowance.

### Done-not-verified

- Merged #36 after rebase and green CI, then #28 and #24 after the owner-selected history-preserving updates and fresh green CI. #37 and the Step 3 real P dev gate remain in progress. No paid Option A dev run has been made by the lead.

### Next-blocked

- Obtain the AI lane's dev-only failure breakdown and previously authored 10 ES / 10 pt-BR confirmation set. Diagnose and fix only dev-supported causes, run the dev gate, report and stop before re-release. No final v2 run or deployment is authorized in this step.

---

## Frontend handoff 11 — historical PR refresh (freeze lifted by handoff 12)

### Completed (verified)

- Read the complete parallel-work handoff. Refreshed PR #28 against main `3ed98c9` while preserving published history under the no-force-push rule. Resolved documentation conflicts by retaining both the original human spot-check and v2 evidence; labels, measurements and private artifacts are unchanged.

### Done but not verified

- Updated PR #28 CI is pending. Submission refresh and frontend recording improvements are separate follow-ups in this handoff.

### Next / blocked

- Keep PRs open. Do not merge into main until Sebastian announces that the final run has finished; the lead merges afterward.

## 2026-09-27 — Frontend handoff 11: historical submission refresh (freeze lifted by handoff 12)

### Completed (verified)
- Refreshed PR #24 against main with history-preserving merge; retained the failed mock diagnostic.
- Updated six-slide pitch, narration and checklist with selected Gemini/Grok/Jev roles, measured development costs, matcher v2/human before-after and private real-model release evidence. Final-run metrics stay explicitly pending.
- Refreshed PR #28 separately; no paid inference, Azure change or frozen-suite execution.

### Done but not verified
- Exported slides/video and judge-access rehearsal remain unperformed.

### Next / blocked
- Keep these PRs open throughout Sebastian's merge freeze. Add frontend glass-box and recording helper on a separate branch; lead merges only after final-run completion.

## 2026-09-27 — Frontend handoff 11: historical recording helper and glass box

### Completed (verified)
- Refreshed open PRs #24 and #28 against main `3ed98c9` with history-preserving merges (no force push). Exact-head checks, web, Postgres and safety CI passed for both; PR #24 records current Gemini/Grok/Jev roles, matcher v2/human evidence and real-model deployment.
- Added precise per-call cost/latency/tokens and conversation known-subtotal/unknown-count rendering; additive allowlisted risk-union, retry/status and Grok-route display. Missing metadata stays unavailable, Gemini risk probabilities stay absent, and risk decisions come from the server.
- Added an authenticated recording helper using existing fixture reset plus read-back, then ES/PT/fraud persona shortcuts and Agent Desk. Prepared messages never auto-send or authorize actions. Live shortcuts require optional trusted persona bindings; existing live reset flags, fresh OTP, confirmation and scope remain enforced.
- Fixture Playwright suite: 12 passed; local B1/mock API customer suite: 6 passed; staff claim/resolve/OTP-reset suite: 1 passed. Production build, lint, TypeScript and repository pre-commit checks passed; final targeted glass-box rerun also passed after copy/mobile-table corrections. Authored-fixture phone screenshot inspected; no paid inference, organizer-row access, Azure changes or frozen-suite execution.

### Done but not verified
- Real-model/cloud recording of these changes is not performed. Current staff trace drops risk judgments/route and current personas omit story bindings; `apps/web/API-PROPOSAL.md` specifies the additive lead changes. Live reset remains disabled in cloud and cannot clear other personas' workspaces.

### Next / blocked
- [PR #37](https://github.com/sebastian-gm/bank-agent-lab/pull/37) is open; keep it and PRs #24/#28 unmerged until Sebastian announces final-run completion. Lead supplies reviewed trace/persona projections and decides any separately authorized bulk reset; UI does not widen RLS or bypass authentication.


## Jev release and final-program preparation — 2026-09-27 UTC (current)

### Completed-verified

- Read handoff 10 fully and verified the orchestrator's merges of #33/#34. Clean main runtime release **`07bccdc630e2b5eeb2dc746a7c3fe000718fd22c`** passed exact-main CI **36301043518** and safety **36301043504**. CI recorded **162 passed / 13 skips**, separate Postgres **14 passed**, B1 **32/32** with 12 readbacks, and browser suites **8 + 4 + 1 passed**. Earlier lead local checks passed 161 tests before the AI follow-up; its reported local total was 163.
- Reviewed PR #31's risk union and judges, integrated each Jev attempt with the durable shared Postgres reserve/settlement, and merged it after all four gates passed. Jev is a supporting risk opinion; Gemini retains intent/slots/phrasing, and deterministic code retains authorization and action authority. The same $12 cumulative gate covers final Gemini/Grok/Sonnet/Jev and restarts.
- `pytest tests/test_final_program.py`: independent authored fixtures passed interruption/resume, completed-case reuse, changed-pin rejection, duplicate-writer denial, deterministic judge selection, preservation of the 20-item human sheet and report metrics. `make checks` passed; no frozen input was opened or final model run started. Private input presence was checked without opening contents.
- Prepared the single detached `scripts.final_program start|resume|status` entry point. Exact commands are in [final-run-plan.md](../evaluation/final-run-plan.md). Atomic per-case/judge checkpoints and fsynced call journals preserve completed results and interrupted attempts; all retries/recovery retain spend. Outputs when authorized include `results.json`, `results.md`, all §15.4 outcomes/efficiency metrics and intervals/slices, repeat flips, paired B1/P comparison, Sonnet/Jev agreement, and `human-judge-20.csv`. This is implementation verification, not final evaluation evidence.
- TypeSafe key copied into `typesafe-api-key` in the approved Key Vault, equal-value readback verified in memory, then removed from local `.env`. Both model keys are absent locally; local provider remains mock/unapproved. The production API image independently passed imports for the SDK, API and six risk questions.
- `python -m scripts.azure_prices`: live East US 2 estimate **$34.63/month before tax**, checked **06:55 UTC**, below the $40 stop gate. Pushed both private ACR images using a temporary Docker config, then removed its token. `azure_dev plan` was reviewed: one TypeSafe-secret-only managed-identity grant and two app updates; ingress/capacity unchanged. `azure_dev apply`: **1 added / 2 changed / 0 destroyed**.
- `python -m scripts.azure_verify`: deployed SHA, owner-IP-only web HTTPS, internal-only API, replicas 0..1, Key Vault references/MI, Postgres TLS/firewall, private registry/state and existing approximate $30/$50 budget alerts passed. The prior Azure-services firewall limitation remains documented.
- `python -m scripts.azure_smoke` stopped at its intentional real-provider guard, before model calls. Equivalent no-model BFF checks in `artifacts/jev_readonly_smoke.py` passed **4 personas, 15 scoped organizer transactions, 4 customer-role denials**, OTP/logout and unchanged spend. Paid conversations used the capped helper below, not the uncapped generic smoke.
- `artifacts/jev_smoke_with_recovery.py` invokes `scripts.azure_llm_smoke` under **`jev-support-smoke`**, adding a replacement-replica GET before the ES dispute readback. ES normal explanation/denial/proposal/confirmation/readback, PT ambiguity/clarification/handoff and fraud handoff passed. Jev returned **5/5 valid** risk-call records across these three flows; recorded unions were checked, and no Grok fallback occurred. Original-session dispute recovery after a new API replica passed.
- `python -m scripts.serving_browser --target azure`: **3 surfaces**, **1 handoff claimed/resolved** passed. Across all four conversations: **14 paid calls, $0.00925008**, **zero unknown-cost attempts**, below the approved $0.10. The previous handoff-09 smoke ledger and exhausted allowance remain intact. Do not spend the remaining smoke allowance without a specific need under the owner's instructions.
- External workflow **36301783139** passed at the runtime SHA: non-allowlisted web **403**, internal API **404**. Required private receipt **`artifacts/azure/jev-release.json`** records the verified implementation SHA, controls/smoke/CI flags and evidence. A documentation-only release follow-up records final SHA/control/CI readbacks there; its application image contents must match the smoked runtime before acceptance.

### Done-not-verified

- No real frozen final evaluation, final subjective judge agreement or completed human judge sheet. The 20-item sheet is generated only when the authorized program runs. PT/MX/AR model-generated wording and lack of fluent-human PT review remain limitations. Standard-account TypeSafe ZDR and actual budget-alert email delivery remain unverified.
- The detached final command has been tested with authored fixtures; its full organizer workload remains deliberately unrun. The generic mock smoke is not a real-provider test; the capped release smoke and separate read-only/restart checks provide the deployed evidence above.

### Next-blocked

- **STOP for Sebastian's explicit final-run go.** The $12 ceiling is already approved; it is not a start signal. No new public ingress, cloud capacity or paid evaluation is authorized by this log.
- After the go, use the documented single start/resume command on the pinned verified main release. Do not independently rerun the 50 calibration items under the separate legacy judge command; they are already included in this program. Human validation remains a separate, unpaid review step.

---

## Handoff 09 integration — 2026-09-27 UTC (prior release)

### Completed-verified

- Reviewed and merged PR #12 (prompt v4, Gemini default, failure-only Grok, judge) and PR #29 (matcher v2), each with all four CI checks green. Matcher v2 is now the default MATCH artifact and is included in the API image; v1 remains available. Lane-authored training/human measurements below are their reported evidence, not lead reruns.
- Independent tests verify v2 scoped choices, rejection of all choices, explicit confirmation/readback, and denial of foreign or out-of-window candidates. No frozen inputs, labels, bindings or private matcher splits were opened during this layer.
- Added migration 0003 and Postgres reservations before every paid attempt. Production cap US$3/UTC day, smoke cumulative US$0.10, unknown costs retained, owner-only configuration; fallback/retries share the gate. A tripped reserve cannot trigger another model.
- Owner-authorized real-route final adapter uses fresh state, v4/v2, Gemini full/repeats and Sonnet subset; final system/judge clients share a cumulative US$12 database gate. Budget denial aborts. Journals save validated output/metadata only, never reasoning. Explicit final start gate tested without opening frozen inputs.
- `UV_CACHE_DIR=/tmp/aclara-uv-cache make checks`: **149 passed, 12 database skips**, six hooks, strict mypy, interfaces/catalog current; B1 **32/32**, **12 readbacks**. `python -m scripts.test_postgres`: **14 passed**, including concurrent reservations, restart/rollback exposure, cumulative cap and runtime privilege denial. `pnpm typecheck`, `pnpm lint`, `pnpm build`: passed.
- `python -m scripts.azure_prices`: live East US 2 **US$34.63/month before tax**, checked 05:33 UTC, below US$40 gate. OpenRouter public endpoint rates rechecked: Gemini standard $0.50/$3 per million input/output; Grok $1.25/$2.50. No model call in these price checks.
- `python -m scripts.azure_openrouter_key`: uploaded owner-supplied key to the approved vault, matching readback in memory, removed local entry and temporary file. No secret value printed or committed.

- Merged integration PR #30; all four PR gates and exact-main CI/safety passed. Runtime smoke release: `5b6e34e15908372d307042a01292201c3bbd8d8d`. Main CI `36297937359`, safety `36297937382`; PR CI `36297745728`, safety `36297745767`.
- `python -m scripts.azure_migrate_ops`: migration and non-owner TLS/RLS readback passed. `terraform -chdir=infra validate`: passed. Reviewed private plan: one API-identity grant limited to the OpenRouter secret, two app updates, no deletions or ingress/capacity changes. `python -m scripts.azure_dev apply`: **1 added / 2 changed / 0 destroyed**. API remains internal; web stays owner-IP-only HTTPS plus login.
- `python -m scripts.azure_verify`: passed deployed SHA, model flags, Key Vault/MI references, source serving, replica limits, Postgres firewall/TLS, private ACR/state and existing approximate US$30/50 alert settings. Budget alert delivery is still untested.
- Real Azure smoke: ES explanation → explicit denial → proposal → confirmation → case readback passed; PT ambiguity → clarification → ESC-04 handoff passed; fraud FRD-01 handoff passed. Staff claim/resolve readbacks and live Ops passed. Required flows used valid, non-degraded Gemini NLU v4 and matcher v2 on charge flows, with no fallback attempts. The first PT smoke failed a verifier assumption that every ambiguous input immediately gets choices. Its corrected verifier permits clarification only with a missing-expression or matcher no-match event; the retry measured v2 no-match, then safe handoff. No model, prompt, threshold or policy was tuned.
- `python -m scripts.serving_browser --target azure`: real browser **3 surfaces**, **1 handoff resolved**, organizer source label and measured workspace verified. Additional local `pnpm test:e2e --live`: **4/4 passed** on authored fixtures.
- **Five conversations attempted total** (including the failed verifier attempt); **10 paid calls, US$0.0107415**, **zero unknown-cost attempts**, all below the approved US$0.10. The allowance is exhausted: do not run another real smoke without new approval. Preserve `artifacts/azure/llm-smoke-conversations.json` and the database cost ledger.
- External access workflow **36298514693** passed: non-allowlisted web HTTP 403 and internal API HTTP 404.
- Aggregate receipts: `artifacts/azure/handoff09-smoke.json`, `verified.json`, and the final session release receipt `handoff09-final.json`. The smoke above is pinned to the runtime SHA; the follow-up changes only documentation and the smoke verifier. Final deployed SHA/control/CI readbacks are recorded in the final receipt and owner report.

### Done-not-verified

- The real final evaluation, judge agreement, human PT/MX/AR language review, broad model safety and actual final cost remain unverified. The prior frozen diagnostic remains failed acceptance.

### Next-blocked

- Runtime layer is verified on the SHA above. The final receipt identifies the documentation/verifier-only follow-up and its control checks. Next layer: AI-lane final evaluation after Sebastian's signal. No further real conversation is authorized in this layer.
- Sebastian must give the AI lane the separate final-run start signal. Public/judge ingress remains unapproved. No new paid evaluation or cloud capacity requested.

---

# Prior release and lane evidence

Session: handoff 08, 2026-09-26 America/Vancouver; continued 2026-09-27 UTC.
This summary supersedes earlier task lists. Earlier release evidence remains in Git history and linked reports.

## Frontend lane — submission kit (2026-09-27 UTC)

### Completed (verified)

- Read handoff `07-docs-submission.md` fully and followed its priority order. Interrupted docs for PR #17 when the lead shipped #21; integrated trusted roles, staff/trace/Ops endpoints, upstream revocation and gated reset with independent readbacks. Private PR #17 is mergeable at `3d63bca`; GitHub `ci` run `36291326889` and `safety` run `36291326877` passed all four jobs. Local evidence: eight fixture, four customer API and one staff API browser tests, accessibility checks, TypeScript, ESLint, production build and repository hooks. Lead owns Azure connectivity verification and shared browser CI.
- Authored the eleven requested submission documents on `docs/submission-kit`: README, R1–R14/seven-criterion traceability, system/state diagrams, STRIDE/OWASP test mapping, actual payload/provider/retention boundaries, trade-offs, projection sensitivity, limitations/readiness, six slides and the video draft. Corrected mock diagnostic aggregates remain explicitly failed-gate evidence; final model/human/deployment metrics retain visible `TODO(results)` entries.
- Read aggregate JSON and verified quoted headline, matcher and problem-analysis values. Corrected the brief's broad charge/fee automation claim and highest-handling-time claim against pipeline output. Read named implementation/tests and linked local restore/cold-start evidence; no outcome rerun, policy tuning or frozen-suite edit.
- A local documentation audit passed 241 link/fence/test-ID checks across the eleven documents; all requirement/criterion mappings, six-slide count and aggregate assertions passed. Narration is 297 words before rehearsal. `git diff --check` and the working-tree data/secret/size policy passed. Provider statements cite official sources; account-specific terms remain unverified. No organizer rows, credentials, Azure actions or model calls were used for this assignment.

- Private [PR #24](https://github.com/sebastian-gm/bank-agent-lab/pull/24) was opened and read back with only the assigned documents plus this log. All four CI jobs passed at `a98203a` (`ci` run `36291808092`, `safety` run `36291808097`); mypy and data/secret/size hooks also passed locally. This log-only follow-up records that evidence.

### Done but not verified

- Mermaid source is provided; final deck export and deployed video recording/rehearsal are not performed. The requested PT staff scene depends on an authorized deployed staff workspace. Judge access and a separate access-code gate are not established; the owner-IP boundary remains.
- Azure BFF-to-API connectivity, latest deployed browser behavior, native language/human label review, selected-provider account terms and real-model evaluation remain pending. The projection intentionally has no invented hours/savings.

### Next / blocked

- Lead review of PR #24 and PR #17. Keep the documentation PR review-ready only after the latest CI is green, and continue prioritizing PR #17 feedback. Lead owns release/network checks; owner approval is required for any future model spending, public submission or wider judge access. No new approval is needed for the completed local documentation work.

### Pitch pass on PR #24 — 2026-09-27 UTC

#### Completed (verified)

- Reworked the six slides into takeaway sentences, each with three short bullets and one table or diagram. Moved methods/caveats into collapsed speaker notes and kept one explicit production/limits slide. The final real-model scorecard uses only `TODO(results)` cells, with separate B1/P and planned Gemini 3 Flash/Claude comparisons and conversation-cost definitions.
- Rewrote the video as 248 spoken words with a customer hook, deployed product on screen at 0:10, separate stage directions and the final fifteen seconds reserved for limits. Added `docs/submission/checklist.md` for access/role/reset details, deadline confirmation, release/recording SHA, full-history Gitleaks/data review, owner-approved publication and email delivery. The sandbox remains private; checklist actions are not executed.
- Checked the priority PR #17: no new review beyond the previously addressed backend-contract review. Merged current main `6aa0cf7` into the published docs branch without rewriting history. New lead changes preserve endpoint schemas; no frontend implementation edit was needed for this pitch pass.
- Local structural/source audit passed: six slide headlines, three bullets and one visual each; 248 narration words; 44 links/reference targets; displayed pipeline/matcher values matched aggregate JSON. `git diff --check` passed. Checked official organizer date, Gitleaks syntax and GitHub visibility documentation; deadline time/zone still requires organizer confirmation. No Azure/model calls, credential reads, public release or email send.

#### Done but not verified

- Final held-out real-model B1/P and Gemini/Claude measurements, human review, actual recording duration and deployed rehearsal remain pending. The AI lane's comparison document still has no measured default; Gemini 3 Flash is explicitly a planned choice. Full-history Gitleaks and publication/access steps are checklist tasks, not completed audits.

#### Next / blocked

- Update PR #24 and verify final-head CI before reporting it ready. Lead review/deployed access verification and the AI lane's final model comparison remain release follow-ups. No permission is needed for this documentation edit; future spending, visibility changes and sending the submission need explicit owner authorization.

## Completed-verified

### Human es-CL spot-check — Data/ML follow-up, 2026-09-27 UTC

- Preserved Sebastian's nine recollections and intentional typos. Independently authored and hashed gold intent/slots before inference from brief §5.2/§9. Verified nine owned targets, nine distinct customers and no overlap with any v1 matcher benchmark split. No frozen scenario-suite access or policy execution.
- Ran the approved `google/gemini-3-flash-preview` NLU → unchanged v1 MATCH chain at `c8588f4fc39593ab60ab0bfe9eeaab6bb6309a84`: nine valid calls, zero fallbacks, **US$0.009933** provider-reported cost against the US$0.50 cap. Kept the worktree key private and process-local; no model thinking stored.
- Published aggregates in the [result review](../ml/result-review.md#human-spot-check-n9-es-cl) and [model card](../ml/model-card-charge-matcher.md#human-spot-check-n9-es-cl): intent 5/9, corrected core slots 7/9, top-1 6/9, recall@3 8/9, **nine no-match decisions**. A documented post-inference annotation serialization correction changes core-slot accuracy from 6/9 to 7/9; original frozen labels and predictions remain intact. No model, prompt or threshold changed.
- Wrote and read back all nine detailed intent/slot/transaction/decision reports, gold, billing, runner and manifests under ignored `artifacts/human-validation/spanish-40/spotcheck-es-cl-v1/`. Source recollection bytes remain unchanged. No card field values entered Git.
- Independent aggregate/billing recomputation, all artifact hash checks, verbatim recollection readback, 13 local documentation links, diff whitespace and staged-file policy passed. This change touches only the two requested ML documents plus this additive session entry.

### Matcher v2 follow-up — 2026-09-27 UTC

- Implemented versioned choice-first decisions while retaining v1 behavior; added deterministic sparse-language synthetic variants and a train/validation-only v2 training entry point. The [v2 protocol](../ml/matcher-v2-protocol.md) fixes noise, cost preferences, selection grids and test/human access order before fitting.
- Ten matcher/MatchState checks passed, including scoped retrieval, legacy behavior, low-existence choice fallback, all-low/empty abstention, literal-format noise and evaluator/export policy consistency. Ruff and strict mypy passed. No frozen held-out scenario-suite access or paid calls in this implementation stage.
- Trained v2 on 18,000 synthetic train / 9,000 validation queries using 20 seeded trials. Froze the model at 05:03:59 UTC before synthetic-test/human access; verified exact code/export hashes and v1 artifact bytes unchanged. Synthetic 3,000-case wrong proposals fell 30→13 under identical serving features and the v2 cost table. Sparse-language diagnostics and their generator limitations are in the [v2 model card](../ml/model-card-charge-matcher-v2.md).
- Ran the single authorized human after-check: nine valid Gemini calls, no retries/fallbacks, **US$0.009762**. On identical fresh NLU slots, v1 returned nine no-matches; v2 returned six correct proposals, two choices containing the target and one no-match. Target top-1 was 9/9 for v2 versus 6/9 for v1. No post-check tuning. Original gold plus the existing separator erratum, recollection bytes and v1 reports remain unchanged.
- Verified zero overlap between human customers and the actual v2 fitting splits; wrote and read back all nine private before/after cases, billing, frozen inputs and manifests under ignored artifacts. No frozen held-out scenario-suite access or card values in Git.
- Final local regression: **123 passed, 9 database-dependent skips**, including **11 matcher checks**; Ruff, strict mypy and all pre-commit hooks passed. Verified 15 local documentation links, serving-boundary loading/ownership denial, exact training/protocol hashes, v2 checksums and unchanged v1 artifact bytes.

### Safety and resolution (tasks 1–2)

- Read handoff 08 fully and followed its order. PR #25 merged after all four gates passed. No credential-bearing organizer document was opened, no organizer rows/secrets entered Git or CI, and no real-model call ran.
- Reduced saved run-01 observations to [aggregate taxonomy](../evaluation/dev-acceptance-fixes.md). Both B1/P had six forbidden dispute writes, all ESC-04: four ambiguous/unsupported and two human-required, ES 2/PT 4. The required-packet denominator is 54, not the additional 60 handoffs with no required-field rubric.
- Independently authored dev regressions fixed missing/contradictory identification, uncertain or negated choice, stale proposals, changed source facts and reopening terminal handoffs. Scoped status inquiry and existing-case status readback were repaired. Packets now include bounded redacted customer statements and preserve preferred language separately from fallback route.
- **50 independent dev checks passed**, including zero forbidden writes, two positive dispute/readback controls, ES/PT status recovery and packet redaction. **No suspected gold-label error was established** from aggregate evidence. System, adapter and unproven label causes are separated in the report.
- The original frozen result remains **failed acceptance**: 67/193 SAR, six forbidden writes per system, incomplete required handoffs. No new full diagnostic or paid model run was made. Every observation reduction and the metadata-only search touch is recorded in the [access log](../evaluation/test-access-log.md); future preflight/run entry points log hashes and started/completed/failed access automatically. The one remaining pre-final diagnostic remains reserved.

### Frontend and organizer serving (task 3 plus owner clarification)

- Integrated frontend PR #17 and its follow-ups: HTTP-only BFF authentication, trusted roles, live Customer Chat, scoped Agent Desk claim/resolve and measured Ops/traces. Added all three browser suites to shared CI. Reset remains disabled in Azure.
- Rebuilt and promoted organizer gold from `LOCAL_RAW_DIR` into persistent ignored `lake/`. Dataset hash matches the pinned `b86f445...97c9`; no source-version difference. Gold/serving counts: **150,000 customers, 400,000 products, 492,414 120-day transactions, 13,164 FX rows, 1,200 agents and 150,000 complaint aggregates**.
- Local serving load passed full sorted-row checksums and independent committed metadata readback. Four private personas bind to distinct development-partition organizer customers; 15 owned scoped transactions total. IDs remain private Postgres configuration. Two Ops personas can demonstrate all surfaces in their own workspace; two customer personas are denied staff routes. Shared demo password/OTP remain dev simulations.
- Runtime source reads use the non-owner pool, forced customer RLS, ownership join and half-open 120-day UTC window. Dataset/clock/build identity is pinned and refresh reads coordinate with the atomic loader. Missing serving state fails closed. No authored-ledger fallback in the deployed mode. See [serving runbook](../serving-demo.md) and [ADR 0004](../adr/0004-serving-isolation.md).
- Held-out adapter now requires that same serving source with RLS on every base read, plus only declared frozen counterfactual overlays in isolated memory. An independent authored dev case verified source-plus-overlay execution. Frozen inputs/labels and run-01 observations remain unchanged. The new adapter has not run the frozen suite.
- Local BFF smoke passed ES/PT normal/ambiguous/human flows: **4 personas, 15 scoped transactions, 2 cases, 4 handoffs, 2 claims, 2 resolutions and 80 audit entries**. Separate browser verification rendered all three surfaces on organizer-backed activity and verified a claimed/resolved handoff and organizer source label. No source screenshots, DOM dumps or browser traces were saved.

### Commands run

| Command | Observed result |
|---|---|
| `PRE_COMMIT_HOME=/tmp/aclara-precommit-cache UV_CACHE_DIR=/tmp/aclara-uv-cache make checks` | Six hooks, staged-file policy, compile, interfaces/catalog; **118 passed, 9 database-dependent skips**. B1 **32/32**, **12 readbacks**. |
| `.venv/bin/python -m scripts.test_postgres` | **9/9 passed** on a disposable local database, including serving RLS/ownership, identity realms, cross-customer denial, original-session restart recovery, build-change rejection and independent serving-plus-overlay execution. |
| `pnpm typecheck`, `pnpm lint`, `pnpm build` in `apps/web` | Passed. |
| `PLAYWRIGHT_BROWSERS_PATH=../../artifacts/frontend/browsers pnpm test:e2e` (`--live`, `--staff`) | **8 fixture**, **4 live customer**, **1 live staff** tests passed; authored test data only. |
| `.venv/bin/python -m aclara.data.cli build --lake lake --no-reports` | Pinned dataset promoted with the counts above; zero invalid silver rows. |
| `.venv/bin/python -m scripts.load_demo_serving --target local` | Full table checksum/commit readbacks and four private bindings passed. |
| `UV_CACHE_DIR=/tmp/aclara-uv-cache make up` | Compose images built; migration succeeded; Postgres, serving API and web healthy. |
| `.venv/bin/python -m scripts.local_smoke` | Organizer BFF three-surface counts above; no model calls. |
| `.venv/bin/python -m scripts.serving_browser --target local` | Real browser Chat/Agent Desk/Ops and resolved handoff passed. |
| `.venv/bin/python -m scripts.azure_prices` | **2026-09-27 04:00 UTC**, live East US 2 modeled **US$34.63/month before tax**, below US$40 gate; no capacity/resource additions. |

### Restricted Azure release

- Read-only probe from the existing Azure web container reproduced API HTTP 403 under the API's owner-IP rule. Deployed an **internal-only API in the same existing Container Apps environment** and retained owner-IP-only HTTPS on web plus login. No new resources, networking products, replicas or broader internet ingress. The web BFF keeps bearer tokens out of browser JavaScript.
- Azure full gold load was initially interrupted during slow small-batch checksum readback, rolling back its uncommitted transaction. Restarted with 5,000-row batches and the same full checks. The restarted Azure load passed full checksums and independent committed readback for all six tables, four private personas and 15 scoped transactions. The serving BFF smoke and replacement-replica recovery also passed.
- Existing approved PostgreSQL Azure-services firewall exception, Key Vault passwords, managed identities, TLS verify-full and approximate US$30/50-equivalent budget alerts remain required. [Network plan](../azure-private-dev-plan.md), [production limits](../production-readiness.md).

- PR #26 merged after all five gates passed; GitHub also marked frontend PR #17 merged. Main `c8588f4fc39593ab60ab0bfe9eeaab6bb6309a84` passed CI **36294472055** and safety **36294472075**. Built/pushed exact clean-main images to private ACR; temporary registry credentials were removed.
- Reviewed the saved Terraform plan in memory, including exact image SHA, internal API, owner-IP-only web, HTTPS, mock, non-owner DB role and unchanged sizing. Apply: **0 added, 2 changed, 0 destroyed**.
- `.venv/bin/python -m scripts.azure_smoke` passed organizer-backed ES/PT normal/ambiguous/human paths and all three surfaces: **4 personas, 15 scoped transactions, 2 cases, 4 handoffs, 2 claims/resolutions, 80 audit entries**. A replacement API replica recovered the original authenticated case; logout then revoked access.
- `.venv/bin/python -m scripts.azure_verify` passed exact-image, restricted ingress, single revision, min 0/max 1, managed pulls, Key Vault references, non-owner Postgres/TLS, approved firewall exception, state firewall and converted USD30/50 budget controls.
- `.venv/bin/python -m scripts.azure_dev plan` returned **No changes**. Credential-free external workflow **36294730475** passed: web **403**, internal API **404**. Consumed plans were removed.
- `.venv/bin/python -m scripts.serving_browser --target azure` passed actual browser Chat → handoff → Agent Desk claim/resolve → measured Ops with organizer provenance. No screenshots or row-level traces were recorded.
- This documentation-only follow-up is released through the same restricted process. Exact final main SHA and control/smoke receipts remain in ignored `artifacts/azure/verified.json` and `serving-smoke.json`, avoiding a self-referential commit SHA in this log.

## Done-not-verified

- Human es-CL spot-check: independent human gold review and agreement are unavailable. This is NLU → MATCH only, not full conversation/action or production validation; the remaining 31 private Spanish cards are blank.

- Matcher v2: application integration and final evaluation remain unverified. NLU intent errors and abbreviation parsing persist; one human target remains rejected by the preselected very-low-score floor. These small, synthetic-card diagnostics do not establish production accuracy or complete agent safety.
- Frozen acceptance after these fixes remains unknown; the preserved run-01 failure is the only full-suite result. Human labels, Spanish owner review and fluent Portuguese review remain pending. PT/dialect phrases are model-authored; prior cross-vendor authoring checks do not replace human review.
- No lead real-model comparison, selected default or different-vendor judge run. Keep `LLM_PROVIDER=mock`. Durable model spend accounting remains future work.
- Azure PITR/regional DR, realistic-volume restore, automatic retention, sustained concurrency, actual charges and budget-email delivery are unverified. Tiny local restore evidence remains in [recovery report](../ops-recovery.md).

## Next-blocked

- Human es-CL follow-up: review the private per-case report with Sebastian; investigate disputed-charge intent handling, abbreviated amounts, unrelated date binding and rejection by the frozen match-exists threshold on separate development examples. Preserve current gold/predictions and the frozen model; this session makes no tuning changes.

- Matcher v2: lead must integrate the new artifact and policy dispatch before the final run, preserving confirmation and rejection of all offered choices. Keep the frozen v1/v2 results; investigate remaining language gaps on independent development cases. This lane leaves orchestration and the frozen suite untouched.
- Next layer after this release: provider comparison on the independent dev suite, broader independently authored language cases and human review. Show the cost estimate and wait for Sebastian's go before any real-model run. No cloud expansion, access broadening or estimate above US$40/month is authorized.
- Reserve the one remaining full held-out diagnostic; log every access, preserve frozen bytes and publish only aggregates. The final evaluation must use organizer serving source and declared overlays.

## AI lane integration evidence

The following sections retain the AI lane’s historical reports; later dated decisions supersede earlier next steps. Lead production wiring and final-run adapter work are in progress under handoff 09. No lead real-model or frozen-suite run has started.

## AI lane — 2026-09-27 (label decision and round two)

### Completed (verified)

- Applied Sebastian's recognition-versus-denial rule to ten derived 32-case NLU labels. Kept the two explicit-denial cases as disputes. Added frozen v3 prompt and a matching deterministic P fallback; retained B1's legacy routing so its lead-owned end-to-end dispute readbacks remain intact. `charge_inquiry` ↔ `dispute_charge` is now graded as an intent error only when the authorized end state is correct. Stored v2 predictions regrade from 32/32 to 22/32 under the new labels for each of four models; old metrics are marked historical.
- Built a separate 150-case AI-authored, unreviewed hard NLU dev fixture: 30 each ES-MX, ES-CO, ES-AR, pt-BR and mixed, 219 scored slot annotations, slang/false-friend/pesos/vague-date and amount/code-switch/injection slices, and no exact-message overlap with the 32-case suites. The frozen held-out end-to-end suite was not used to tune or choose a model.
- Ran the six requested full-suite model IDs plus `anthropic/claude-opus-5` on a fixed 30-case sample: 930 scored model-case outcomes, 930 valid finals, 932 provider attempts. Five full-suite models scored 150/150 intent; Haiku scored 149/150; Opus 30/30. Intent remains saturated; slot, language-ID, injection-flag, latency and per-call cost differ. The table, 95% intervals, dialect slices and confusion matrix are in [model comparison](../ml/model-comparison.md). No default was selected.
- Response-cost ledger: $0.402383 round one, $0.034314 round-two pilot, $0.072047 archived Haiku first pass and $3.012058 scored round two = **$3.520801 known per-call spend**. Two Haiku interruptions had no response usage/cost and are excluded from per-case cost; a separate $0.30 guard keeps the run below Sebastian's $10 cap. Full Haiku results came from the schema-capable ZDR Amazon Bedrock global route after pacing. Production `.env` remains `LLM_PROVIDER=mock`, `LLM_REAL_CALLS_APPROVED=0`, with unique `COMPOSE_PROJECT_NAME=aclara-ai`.

### Done but not verified

- The 150 AI-authored labels lack human verification and ES/PT fluency ratings. Perfect observed intent macro-F1 gives degenerate bootstrap intervals; this set cannot decide among the five perfect full-suite models. The exact bill for the two no-usage Haiku interruptions cannot be assigned from per-call fields. B1's lead-owned explain-then-offer transition is still needed before its rules classifier can adopt the new NLU label without changing end-to-end behavior.

### Next / blocked

- Sebastian will decide a default after reviewing the aggregate trade-offs and obtaining stronger independent human-checked NLU evidence. Lead review of PR #12 and the B1 workflow transition remain. No further paid run is authorized by this section; keep production in mock mode.

## AI lane — 2026-09-27 (selected default and round three)

### Completed (verified)

- Configured Sebastian's selected `google/gemini-3-flash-preview` route for both NLU and phrasing. `LLM_PROVIDER=mock` still selects the mock entries; a lead-enabled `openai_compat` deployment selects the reviewed `default` route. The runtime NLU prompt now uses the evaluated v3 taxonomy. Persistent `.env` remains mock with its approval flag unchanged; the real-call gate was process-local for this approved comparison.
- Ran six cheap challengers on the same frozen 150-case unreviewed NLU dev suite and v3 prompt: GPT-5 nano/mini, Grok 4.20, Qwen3 Next 80B instruct, DeepSeek V4 Flash 0731, and Mistral Small 4. All 900 model-case outcomes are checkpointed under ignored `artifacts/ai-round-three/`. The [comparison](../ml/model-comparison.md) reports exact IDs, 95% intervals, all-attempt JSON validity, injection flags/false flags, latency, per-call cost and paired slot-F1 differences. No challenger matched Gemini 3 Flash's 10/10 injection flags and 95.7% slot F1.
- DeepSeek's `wafer/fast` ZDR route was fastest in a fixed three-case/provider probe: 2.65-second median versus 5.37 on DeepInfra and 7.08 on OpenInference. DeepSeek used `reasoning=none`; OpenAI required `minimal`; Mistral was pinned to `mistral/us` after an unpinned 429. The scored OpenAI failures were `content_filter` stops, four non-valid attempts and two missing finals per model, not output truncation.
- Known round-three per-call spend, including successful pilot and provider probes, was **$0.292253**. Known cumulative spend across rounds was **$3.813054**, below the $10 cap. Six initial HTTP 400/429 attempts had no usage/cost response and remain unassigned; a separate $0.12 guard plus $0.30 reserve protects the cap. No key-level account delta was used for model cost.
- `make checks` passed: six hooks, file policy, compilation, **76 tests passed and 7 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog. No model messages, model thinking, credentials, or organizer rows were committed.

### Done but not verified

- The 150-case dev set and ES/PT fluency judgments still lack independent human review. Ten synthetic injection cases measure suspicion flags, not arbitrary attack resistance. The chosen Gemini route has not been exercised in deployed production; deployment needs the lead's production key and activation.

### Next / blocked

- Superseded by Sebastian's later choice of Grok 4.20 as the failure-only fallback. Claude remains reserved for the independent final held-out frontier comparison and judge validation. A new approval is needed before additional paid model runs.

## AI lane — 2026-09-27 (fallback, judge and final-run plan)

### Completed (verified)

- Configured `x-ai/grok-4.20` on the ZDR `xai/zdr` route as Gemini 3 Flash's **failure-only** cross-vendor fallback. The structured client retries Gemini once before invoking Grok; the same run budget and approval gate cover both, and non-default frontier routes have no fallback. Persistent production settings remain `LLM_PROVIDER=mock`, `LLM_REAL_CALLS_APPROVED=0`; no production key or route was activated.
- Added [subjective judge rubric](../evaluation/judge-rubric.md), score-only Sonnet 5 OpenRouter harness, and quadratic-weighted κ/paired-agreement computation. The judge input excludes gold and objective outcomes; scoring is limited to language/register, clarity, empathy, and handoff-summary usefulness. Generated an ignored mode-0600, 50-row synthetic human sheet at `artifacts/judge/human-validation-50.csv` (SHA-256 `4f862e442d1cce88c8f90b38a22cb53691ed8efe9352bf4ca878c952520f5794`), with all human ratings blank and no frozen held-out cases.
- Sebastian authorized only a sub-$0.50 judge smoke. Sonnet 5 on ZDR `google-vertex/global` returned **3/3 valid** strict score-only responses; known per-call cost **$0.008042**. An advertised Bedrock route returned six no-usage provider errors and a diagnostic HTTP 404; all seven unknown-cost attempts are kept in ignored metadata with a conservative **$0.35** guard. Known spend plus guard is **$0.358042**, below the $0.50 limit. No 50-case judge calibration or final held-out real-model run was made.
- Wrote the [priced final-run plan](../evaluation/final-run-plan.md): B1 200; Gemini P 200 full plus two additional 100-case passes (three total subset runs, 400 P case-runs); Sonnet P once on the same 100; 50 human-calibration and 100 B1/Gemini judge assessments. It gives exact route/prompt settings, per-component token and cost estimates, a 5% Grok fallback sensitivity, a **$4.590 illustrative model-cost total**, a proposed **$12 future stop ceiling**, and **60–90 minutes** estimated serial machine time. It explicitly requires lead acceptance fixes and a separate approval before execution.
- `make checks` passed: six hooks, strict mypy, file policy, compilation, **81 tests passed / 7 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog.

### Done but not verified

- The human sheet has no ratings, so no judge agreement or weighted κ is claimed. The three-item smoke proves route/schema operation only; the 50-item judge run, human ES/PT wording review, final system costs/latency, and real-model safety remain unmeasured. The final-run cost and time are estimates using current public ZDR rates and conservative token assumptions.

### Next / blocked

- Sebastian to fill the 50 human scores and approve a fresh priced judge calibration/final run after the lead's independent acceptance fixes, frozen SHA, production-key deployment, and a cross-process spend breaker. The current `evals.heldout` adapter still hardcodes mock metadata/execution and needs the lead's real-route integration. Do not run the frozen real-model test or additional paid judge calls under this session's smoke approval.

## AI lane — 2026-09-27 (denial prompt v4 and final preflight)

### Completed (verified)

- Added [NLU prompt v4](../../prompts/nlu/v4.md) for explicit ES/PT denial cues, including Chilean informal speech and merchant nonattendance, while keeping recognition or uncertain memory as `charge_inquiry`. The runtime P NLU route now selects v4. No human spot-check utterance or frozen held-out label was added to development fixtures.
- Paired Gemini 3 Flash v3/v4 on 40 new synthetic, team-authored denial/inquiry cases. The first 24 were saturated (24/24 each); the 16 harder contrastive cases yielded v3 **11/16** versus v4 **16/16**, with five v3 explicit-denial→inquiry errors and zero v4 errors. Combined: v3 **35/40**, v4 **40/40**; all **80/80 attempts** valid schema JSON. The [comparison](../ml/model-comparison.md) reports aggregate evidence and limitations. Per-call cost **$0.106686**, no unknown-cost attempts, below the separately approved $0.49 cap. These authored cases do not establish independent production accuracy.
- Pinned selected Gemini and Sonnet frontier to ZDR `google-vertex/global` for the priced final configuration and updated Gemini's reserve rate to the standard $0.50/$3 per million. Production `.env` stays mock/unapproved. `make checks` passed six hooks, strict mypy, staged-file policy, compilation, **83 tests passed / 7 database-dependent skips**, B1 **32/32** with 12 readbacks, interfaces and policy catalog. PR CI follows this section.
- Sebastian pre-approved the [final-run plan](../evaluation/final-run-plan.md) with a $12 ceiling but withheld the start signal until lead acceptance fixes, matcher v2 and prompt v4 merge with green gates. The revised v4 token assumption raises the illustrative model estimate to **$4.692**, still within the approved ceiling. Read-only [preflight](../evaluation/final-preflight.md) verified the frozen 200-case manifest/counts but stopped on a missing private customer-binding artifact; it made no system/model run and wrote no final output.

### Done but not verified

- Human ES-CL and fluent PT review of v4 wording, independent validation, and final end-to-end behavior remain unverified. The current held-out adapter is still P/mock only; a durable cross-process spend gate is not wired in this branch. The private binding artifact is absent here.

### Next / blocked

- Lead supplies/verifies the frozen private binding, merges acceptance fixes and matcher v2, integrates the real-route final adapter and spend breaker, and reads back green gates. Merge prompt v4 without held-out tuning. Do **not** begin the $12 final program until Sebastian's explicit start signal.

## AI lane — 2026-09-27 (TypeSafe Jev challenger)

### Completed (verified)

- Read the live TypeSafe SDK/model/primitive and legal documents and the user-specified local SDK example. Added `typesafe-sdk` 0.7.2 to the optional LLM and dev dependencies, a separate typed-judgment-only adapter, versioned intent/risk and rubric questions, and a checkpointed cross-provider comparison. No Jev slot extraction, phrasing, identity, policy or write route was added. [Data provenance](../data-provenance.md) records TypeSafe's no-training claim, ordinary retention/US hosting, and unverified ZDR status; only synthetic text was sent.
- Under Sebastian's new **$1 combined** OpenRouter/TypeSafe cap, reran Gemini 3 Flash with v4 and Jev 1.13 on the same unreviewed 150-case NLU dev set. All 300 attempts returned valid finals. Gemini: **150/150 intent**, **9/10 injection flags**, **0/140 false flags**, p50 **1.897 s**, **$0.211601**. Jev: **146/150 intent**, **6/10 flags**, **0/140 false flags**, p50 **0.090 s**, **$0.005877**. The [comparison](../ml/typesafe-jev-comparison.md) includes ES/PT/mixed slices, ten-bin ECE, 95% intent intervals, risk-cue counts and limits. Jev's four intent misses include three inquiry→dispute errors under Sebastian's label rule.
- Scored the same three previously saved Sonnet synthetic judge-smoke items with four Jev rubric Scores, without any objective gold or new Sonnet call. Jev cost **$0.000124**; dimension-level exact agreement and weighted κ are in the report. New known per-call total **$0.217601**, no unknown-cost attempts or retries, under the $1 cap. Production remains mock; Gemini remains default, Grok remains failure-only fallback, and Sonnet remains judge candidate. No final frozen-suite run started.
- On this follow-up branch from current `main`, `make checks` passed six hooks, strict mypy, staged-file policy, compilation, **141 tests passed / 9 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog. The pinned-served-model validation test also passed. The ignored `.env` and TypeSafe checkpoints are excluded from Git.

### Done but not verified

- The 150-case development labels and ES/PT fluency still lack independent human review. The three-item Jev–Sonnet judge agreement is not human validation; the 50 human-sheet ratings are blank. Other risk-cue labels have no independent gold in this suite, so only injection flags were graded. TypeSafe standard-account zero retention is not verified and Jev was not selected for production.

### Next / blocked

- Sebastian decides whether any later Jev experiment is useful; this PR does not change the selected default or judge. Keep the $12 final program on hold until the lead's acceptance fixes, matcher v2, prompt v4 merge, private binding/preflight, spend breaker and green gates are read back, then wait for Sebastian's explicit start signal.

## AI lane — 2026-09-27 (Jev supporting roles)

### Completed (verified)

- Added risk-only Jev `Noul` second opinion in the NLU lane for selected Gemini 3 Flash calls. It runs concurrently, unions each cue at `>=0.5`, and records Gemini raw booleans, unavailable Gemini per-cue probabilities as `null`, Jev raw probabilities/flags, the union, usage/cost and degradation in the existing execution-record path. Ordinary Jev failure, timeout or missing key leaves Gemini flags intact; a durable final-budget denial aborts the program. No orchestrator or `NluFrame` interface changed. Mock and Sonnet frontier routes do not invoke Jev.
- Replayed the 150 saved paired development cases without new paid calls: Gemini injection **9/10**, Jev **6/10**, union **9/10**, all **0/140 false flags**. Jev adds two distress flags without independent distress gold. The paired max-of-two latency **proxy** is 1.897 s median / 2.224 s p95, unchanged from Gemini; live parallel latency is not measured. [Aggregate report](../ml/typesafe-jev-comparison.md).
- Integrated a gated [dual subjective judge helper](../../src/aclara/llm/dual_judge.py) into the full 50-item Sonnet judge command. It scores both on the same items, reserves Jev against the lead's merged durable Postgres gate, checkpoints raw Jev distributions, and supports Jev–Sonnet plus separate judge–human weighted κ once all human ratings exist. Its offline tests made no final or new judge paid calls. [Final plan](../evaluation/final-run-plan.md) prices 410 Jev risk calls and 150 Jev judge calls at $0.02583 and $0.01260 before rounding, for an illustrative **$4.730** total below the existing $12 ceiling. The final start is still withheld.
- After reconciling the lead's current final-route and durable-budget changes, `make checks` passed six hooks, strict mypy, staged-file policy, compilation, **159 tests passed / 12 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interfaces and policy catalog. The merged tests cover Jev reservation/settlement in the shared journal and budget store. No organizer rows, credentials, model thinking or paid-call artifacts were staged.

### Done but not verified

- Concurrent provider latency, Jev failure rate in production, the five non-injection risk-cue accuracies and 50-item judge–human agreement remain unmeasured. Gemini prompt v4 supplies Boolean risk flags, not per-cue probabilities. TypeSafe standard-account zero retention remains unverified. PR #31 merged while this branch was being reconciled; its follow-up integration and frozen private-binding preflight are not yet merged/verified together.

### Next / blocked

- PR #34 subsequently merged into the pinned `07bccdc` main before the merge freeze. The lead should read back `score_pair` on the 100 frozen reply assessments, TypeSafe payload terms, and both providers in the shared durable $12 gate. Keep production mock until the authorized deployment route is enabled, and do not begin frozen final evaluation until Sebastian's explicit start signal and all preflight gates are green.

## AI lane — 2026-09-27 (parallel development before final run; merge freeze)

### Completed (verified)

- Read handoff 11 in full and kept the merge freeze: work is on a new AI feature branch; no main merge or frozen held-out access occurred. PR #34 had already merged as the pinned `07bccdc` main commit; this branch follows it. PR #36 is open, targets main and passed all four CI checks without merging.
- Measured 20 synthetic no-fault dev conversations through the real local ASGI P path, including parallel Jev risk calls, Gemini phrasing and one forced no-network Gemini failure followed by a valid Grok fallback. Turn p50/p95 **1.782/4.354 s**, case-sum p50/p95 **2.002/8.126 s**, known per-call cost **$0.032765**, conservative cap charge **$0.052947/$0.50**. Full aggregate and limits: [live dev path study](../ml/live-dev-path-study.md).
- Compared templates with grounded LLM phrasing on **30 assessable dev conversations** (38 attempted, eight fault-trigger misses). Four replies changed; no grounding catch in four eligible phrase calls. Both Sonnet and Jev scored clarity/empathy; the aggregate score, marginal latency and cost are in the study. All 38 attempts charged **$0.166451/$0.50** from per-call costs/reserves, with no held-out access.
- Sonnet model-reviewed **17/17 active AI-lane pt-BR template and prompt-example strings** using only an explicit synthetic-string payload. Accepted three wording improvements in `agent/nlg` and `agent/ai`; [before/after log](../ml/pt-review.md) is labeled model-reviewed. Valid call cost **$0.044504**. An extra-scope lead-owned review returned two truncated responses; its $0.255 local reserve plus the valid call stayed below the separate $0.30 ceiling. No more Portuguese-review spend occurred.
- `make checks` passed six hooks, strict mypy, file/secrets policy, compilation, **163 tests passed / 12 database-dependent skips**, B1 dev harness **32/32** with 12 readbacks, interface and policy catalog checks. No organizer rows, credentials, model thinking, or row-level output were staged.

### Done but not verified

- The local ASGI timing excludes container/network and production database overhead. The dev wording labels and pt-BR naturalness lack human review; only four LLM drafts changed the final reply, so judge-score differences are exploratory. The 34 lead-owned pt-BR strings were not successfully model-reviewed after Sonnet truncation. The final held-out results remain pending Sebastian's start/completion signal.

### Next / blocked

- Open and keep this AI-lane PR unmerged until Sebastian announces the final run is finished. The lead can then merge it after review. No further paid development run is planned under these caps; a complete second-vendor review of lead-owned strings would need a separate cost authorization and coordinated lead-lane edits.

## Access and continuation

Restricted web: https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io/
Use `demo.es.mx` or `demo.pt.br` for the three-surface workspace; `demo.es.co` and `demo.es.ar` are customer-only. Retrieve `demo-password` from the authenticated Key Vault portal; never paste it into chat, Git or logs. OTP is simulated. Re-login after the identity-source migration; prior fixture sessions do not grant organizer access.

For later sessions, paste: **Continue from docs/status/progress-log.md. Next layer: final evaluation after Sebastian's explicit go. Same rules.**

## 2026-09-29 PDT — authorized startup preview and session-security review fix

### Completed (verified)

- Merged #63 into `fix/post-v3-analysis` at `dac38017d4ea9910afc3aa4851f661dd6608b7ce`
  and redeployed the explicitly approved PREVIEW. Only ignored `image_tag` changed;
  reviewed Terraform plan/apply: 0 added, 2 changed, 0 destroyed. Both image tags
  match. `python -m scripts.azure_verify` passed: owner-IP/login restriction,
  internal API, TLS/identity/firewall/budget controls and replicas 0..1 unchanged.
- `.venv/bin/python artifacts/preview-release/read_only.py`: new web/API revisions
  both reached zero naturally; authenticated cold me 200/86.059 s with clock,
  transactions 200/0.132 s (four projections), logout revocation readback passed.
  Sampled console logs contain no application exceptions. No model/banking calls.
  Detailed aggregate evidence is ignored under `artifacts/preview-release/`.
- Exact deployed-SHA `UV_CACHE_DIR=artifacts/uv-cache make checks`: 308 Python
  tests passed, 14 database-dependent skips; B1 32/32; interfaces/catalog,
  pre-commit and staged-file policy passed. Startup web checks from #63 remain
  the previously executed 55 browser checks and typecheck/lint/build.
- Finding #2: authored two-tab regression first reproduced missing ESC-02.
  Security cues now share the durable, session-scoped strike record; older
  conversation-only cues are preserved on upgrade. Another login stays isolated.
  `.venv/bin/pytest tests/test_workflow_api.py tests/test_post_v3_fixes.py`: 32 passed.
  `.venv/bin/python -m scripts.test_postgres`: 18 passed, including another-tab
  security termination after app/store restart. Strict mypy and Ruff passed.
  Fix-candidate `make checks`: 309 passed, 15 skips; B1 32/32; safety/hooks/schema green.

### Done but not verified

- GitHub Actions cannot start because the account Actions budget blocks jobs.
  Local checks do not claim a successful remote CI run.
- Paid preview chat has not been tested. The Azure checks exercise auth and reads.

### Next / blocked

- Open the security fix PR against `fix/post-v3-analysis`; retain main at `e12efc7`.
- Fix freeze-origin binding, exact-error harness renewal/new freeze confirmation,
  and wrong-code OTP retry with authored regressions, then open a second feature PR.
- AI lane owns review findings #1/#3. Main merge still needs billing recovery or
  Sebastian's explicit exception. No min replicas change, paid calls or v4 access.

## 2026-09-29 PDT — lead freeze provenance and OTP follow-up candidate

### Completed (verified)

- Security fix PR is [#67](https://github.com/sebastian-gm/bank-agent-lab/pull/67),
  head `5720cbe`, targeting `fix/post-v3-analysis`. The second fix branch includes
  it; merge #67 first to reduce the second PR's diff. No main merge or second
  Azure deploy was performed.
- Authorized PREVIEW remains `dac38017d4ea9910afc3aa4851f661dd6608b7ce`.
  Authenticated browser navigation also passed: login/OTP, visible bank clock,
  chat composer and sign-out; no message sent. Evidence is ignored
  `artifacts/preview-release/browser-final.jsonl`. Initial browser helper failures
  were its own persona/OTP-placeholder race and timeout setup; the helper now
  waits for the six-digit SMS before submission. They are not app failures.
- Findings #4/#5: explicit owned fraud-handoff origin, offered-card restriction,
  hash-bound conversation/reasons, refreshed freeze proposal returned to the
  simulated customer after exact-error OTP renewal; other 401s never renew.
  Updated API/BFF/UI/adapter callers and regenerated OpenAPI. Authored tests cover
  multiple conversations, tampered/wrong-session/unoffered-card origin and a
  customer declining the refreshed proposal. Wrong-code renewal preserves the
  pending dispute/challenge and permits retry; five-attempt limit remains enforced.
- `UV_CACHE_DIR=artifacts/uv-cache make checks`: 324 passed, 16 database-dependent
  skips; B1 32/32, hooks/staged-file policy/compile/interfaces/catalog passed.
  `.venv/bin/python -m scripts.test_postgres`: 19 passed, including originating
  fraud packet after a new conversation and app restart, and wrong OTP followed
  by correct OTP/dispute readback after app/store restart. No cloud database writes.
- `.venv/bin/python -m evals.runner --system B1 --scenarios evals/dev_scenarios_v2.yaml`:
  32/32. Ruff and strict mypy passed. Web typecheck/lint/build passed;
  `pnpm test:e2e`: 46/46; `pnpm test:e2e --staff`: 1/1. Live customer checks
  passed 12/12 including the final multi-conversation browser regression.
  A typecheck started alongside dev-server generation hit missing generated Next
  type files; sequential typecheck after browser teardown passed.

### Done but not verified

- Follow-up fixes are local/mock validated, not deployed or measured with real NLU.
- GitHub Actions is still blocked by the account Actions budget; no remote green
  claim. Main is unchanged; no v4 inputs, authoring tools or bindings opened.

### Next / blocked

- Second private feature PR is [#68](https://github.com/sebastian-gm/bank-agent-lab/pull/68),
  targeting `fix/post-v3-analysis`, with code commits `aa37227` / `f891584`.
  All 59 browser checks passed (46 fixture/startup + 12 live customer + 1 staff).
  Review/merge #67 first, then #68; neither is merged here.
- AI lane owns #1/#3. Review both lead PRs; main merge waits for billing recovery
  or Sebastian's explicit exception. Any later release follows its own gate.
- No paid calls, min replicas change, or new approval needed for the completed
  preview. No v4 start. Continue from this log under the same rules.
