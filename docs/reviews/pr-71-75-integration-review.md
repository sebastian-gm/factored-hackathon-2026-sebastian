# Final feature integration review: #71–#75

## September 30 follow-up: #76 and standing release approval

#76 (`4436729`) reviewed commit-by-commit and merged locally without conflict.
Its own diff changes no BFF/action handlers: localized reason/evidence labels,
recording opt-in, skip-link/rail geometry and authored country-currency fixtures.
The current-account selection and pending-card locks survive the merge. The
fixture currency change does not transform live serving currencies.

Lead's additive BFF instrumentation reports elapsed handling only, with existing
response/auth/action data unchanged. Authored refusal tests preserve 403/no-store;
the paid probe requires exact released main and a new $0.10 durable purse.
Pre-v4 budget code closes prior dev scopes, preserves reserves, and cannot reset
or re-enable an exhausted/disabled cap. Disposable DB regressions cover rollback,
restart and both dev/smoke lifetime limits.

Final combined local verification: **449 Python passed / 20 DB skips**, B1
**32/32**, disposable Postgres **23/23**, strict mypy **85 files**, Ruff,
web typecheck/lint/build, **80 fixture + 12 live + 1 staff = 93 browsers**.
A second fixture race was fixed by waiting for three shortcuts before unroute
(avoiding a vacuous empty `.all()` check); both bootstrap tests passed **6/6**
in CI's dev-server mode. Logs: ignored `artifacts/integration/pr76-*`.

Owner's September 30 standing approval supersedes the earlier main/release hold
below. Publish one full corrected head, require remote green, then merge/release.
Temporary smoke-run binding separately approved. Resources/minimum replicas/access
remain unchanged. V4 remains blind/unstarted. See
[live budget math and release plan](../evaluation/pre-v4-release-and-latency.md).

## Dispositions

- **#71**, audit document only: retains the exact historical scan boundary,
  Gitleaks exit 1/12 false positives, detector limitations and the separate
  owner publication decision. Added a cutoff note: later UX/eval/infra changes
  are outside that scan; the exact sanitized export requires another audit.
  No history/export/cloud change was performed or scanner result relabeled.
- **#72**, commits `66e8129`, `9d690a5`, `d4979e5`: presentation, authored
  coverage and phone-receipt refinement reviewed. Its own changes do not modify
  the BFF compared with already-reviewed #68 (the PR comparison included #68's
  ancestral BFF work). Desk claim/resolve payloads, versions/idempotency keys
  and committed read-back checks remain identical.
- Customer recognition sends a message only after the explicit choice; action
  hashes and confirmation POSTs still originate in bank proposals. Wrong OTP
  retains challenge/proposal; expiry starts an explicitly requested new review
  without submitting an old hash. GET recovery and editable status/help drafts
  do not replay writes. Stage labels are response guides, not execution evidence.
  Customer labels hide handles; canonical reason/evidence stays in Desk.
- **Two integration gaps fixed in `8513b9d`:** prefer the already signed-in
  eligible account when choosing a story, so a future judge alias is not logged
  out into the owner account; include pending card OTP/proposal/unknown-write
  state in the quickstart lock, including the recording helper's common story
  entry point. These changes neither add confirmation nor change action/OTP
  request bodies. An authored alias test observes **zero POSTs** while preparing
  a draft; the card test asserts every story shortcut disabled through retry
  and fresh review, with **zero freeze writes**.
- One live test still expected the old `Usar otra cuenta` button after revocation;
  corrected it to the implemented localized `Volver a acceder`. The final live
  run passes all twelve, including revoked bearer, upstream logout, multi-tab
  strikes, wrong OTP renewal and originating freeze handoff across conversations.
  Earlier failed/stale-selector attempts remain in ignored logs.
- **#73**, `c328553`: pinned v4 program configuration/local RLS serving and
  distinct durable $3 lifetime scope; no input access or real run. Budget math
  and explicit future commands in [readiness](../evaluation/v4-program-readiness.md).
- **#74**, `27a6324` documentation branch: production/privacy evidence, official
  aggregate language/safety counts and assumption-labeled pilot ranges retained.
  Corrected its stale undeployed-startup statement to the recorded `dac3801`
  read-only preview/86.059 s cold chain. The checklist now reflects the recovered
  $5 Actions cap and main-target gate. Neither implies paid-chat acceptance.
- **#75**, `aaa2a97`: independent OFF switches, external Key Vault judge
  references, existing trusted persona alias and ordinary $3/day accounting.
  Reviewed no-op OFF plan and minimal ON plan. Credentials/roles cannot be
  supplied by clients. [Plan, cost and future approval](../submission/infrastructure-switches.md).

## Integration and verified local gates

#73, #75, #71, #72, #74 integrated into `fix/post-v3-analysis` after #63/#65–#70.
Two progress-log conflicts preserved each additive entry and the existing history;
no product conflict or force push. The following passed on the combined code:

| Command | Observed result |
| --- | --- |
| `LLM_PROVIDER=mock make checks` (repository UV cache) | 442 passed / 17 DB skips; six hooks, file policy, compile, B1 32/32, snapshots/catalog |
| `.venv/bin/ruff check .` / strict mypy | Passed / 85 source files |
| `python -m scripts.test_postgres` | 20/20, disposable local DB; includes judge RLS/restart and v4 budget/reserves |
| B1 reactive `evals/dev_scenarios_v2.yaml` | 32/32 |
| `pnpm typecheck`, `pnpm lint`, `pnpm build` | Passed, sequential |
| `FRONTEND_E2E_PRODUCTION=1 pnpm test:e2e` | 64/64 fixture checks |
| Same `--live` / `--staff` | 12/12 / 1/1; **77 total browser checks** |
| Terraform fmt/validate / mocked plan-only tests | Passed / 5/5; no Azure apply |

Ignored receipts/logs: `artifacts/submission-prep/combined-*`,
`browser-stories.log`, `browser-live-verified.log`, `browser-staff.log`.
Generated B1 aggregate Markdown was restored after testing.

## Remote gate and limits

Published the complete #62 head `00246eb083121d8234c7ef45a076c7fb78801145`
once. Its automatic [CI run 36672780834](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs/36672780834)
passed `checks` and `postgres`, but failed one of 64 fixture browser checks;
the chained live/staff runs were not reached. [Safety run 36672780958](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs/36672780958)
passed. All runs are attempt 1; no manual rerun.

The failing authored startup test changed the locale on server-rendered HTML
before hydration installed React's change handler: Portuguese was expected,
Spanish remained displayed. The existing startup regression already synchronizes
on the client bootstrap request. Applied the same synchronization to this test,
with a locale-selection assertion. **Test only: no product/BFF/OTP/action change,
no longer timeout or weakened expectation.** CI's development-server mode now
passes the targeted check three consecutive times and all 64 fixture checks:
`FRONTEND_E2E_PRODUCTION=0 pnpm test:e2e --grep 'startup and unavailable states' --repeat-each=3`
and `FRONTEND_E2E_PRODUCTION=0 pnpm test:e2e`.

Aggregate receipt: ignored `artifacts/integration/pr62-remote-gates.json`;
logs: `pr62-web-remote-failure.log`, `pr62-hydration-targeted.log`,
`pr62-hydration-fixtures.log` in the same directory. The test correction is
prepared locally. A second paid automatic CI cycle (~$0.06, owner estimate)
requires owner approval after the authorized single cycle; it has not run.
Read the receipt and GitHub for the actual tested SHA. Remote green remains
required before main promotion.

Main/origin/main remain `e12efc73be64f8355aa9f177f08a04337593616c`.
No v4 scenario/selection/authoring/binding was opened, no v4 program prepared or
started, v1 untouched. No paid model call or Azure change occurred. Current Azure
is the earlier approved preview, not this candidate. Public judge/warm modes stay
OFF. Main merge/release need Sebastian's separate confirmation after remote green.
The newer UX strings have browser/localization coverage, not new paid cross-vendor
or fluent-human PT validation; that limitation remains.
