# V4 program readiness (not started)

V4 is independent of the seen v3 suite. This preparation reads no v4 rows,
selections, authoring tool or private binding contents, and makes no model call.
The suite PR and bindings must be integrated only under the release approval.
Existing v1 artifacts stay untouched. V2/v3 official figures are unchanged.

## Explicit configuration and immutable resume

`--suite test-v4 --bindings artifacts/evaluation-v4/customer-bindings.json
--manifest-pin 309c3aa22c2eab51b3289075b733c52bb7934a879299762c3fb9ba16a3d9bec8`
resolves the release, private bindings, output directory `artifacts/final-program-v4`,
scope `final-evaluation-v4` and lifetime run `final-program-v4`. The CLI defaults
to v4; v3 is retained only through an explicit `--suite test-v3` for compatibility,
not as authorization to run it again. Unknown suites, changed pins and bindings
outside ignored repository artifacts are rejected without reading files.

Prepare checks only pinned manifest/provenance and opaque binding bytes (0600).
Start requires the owner signal, clean main equal to origin/main and accepted
`jev-release.json` at the implementation SHA. The detached child receives the
same arguments. Prepare, launch and checkpoints pin suite, bindings, manifest,
SHA, local endpoint/role, serving dataset identity and every release-file hash.
Resume cannot reset spend or replace those pins. It skips completed cases and
preserves partial journals/reservations. The watchdog stops at 15 minutes without
progress, three hours total wall-clock, or budget/error. No automatic resume loop.

Inside the authorized start gate only, `repeat-selection.json` and
`judge-selection.json` supply the 30 frozen selections each; no resampling.
B1 executes 100, P-Gemini 100 plus two extra passes on 30 (160), frontier OFF.
The two judges score both systems for 30 scenarios (60 blinded paired items),
without extra calibration. Sonnet's existing 1024-output-token cap also feeds
its price reservation. Risk Jev, fallbacks, retries and both judges share the
same durable lifetime scope. Outputs retain aggregate JSON/Markdown, slices,
paired intervals, repeats, judge agreement and the private 20-item human sheet.

## Local serving, remote durable accounting

Set `EVAL_SERVING_DSN` privately to the promoted **local** organizer serving DB,
using `aclara_app`. Never put the DSN/password in argv, Git or a log. The runner
requires loopback (including any hostaddr), a named DB and the non-owner role;
remote endpoints, owner roles and service indirection fail before provider/key
access. The child preserves this environment variable instead of overwriting it
with the Azure budget DSN. Source reads still enforce customer RLS, the 120-day
window and dataset identity; overlays remain isolated authored counterfactuals.

This removes workstation-to-Azure **serving** SQL hops from case/turn latency.
Provider latency and remote durable budget reservations remain included. These
measurements are not Azure end-user latency or directly comparable infrastructure
latency to v3. Budget accounting remains in the existing Azure Postgres ledger,
so a new local database cannot reset cumulative history.

## $3 lifetime and $12 cumulative ceiling

**2026-09-30 update:** [pre-v4 release and latency plan](pre-v4-release-and-latency.md)
adds shared pre-v4 development ($1) and a distinct latency smoke ($0.10), counting
historical production charges too: live prior **$4.57863620 + $1 + $3 + $0.10 +
$0.10 = $8.77863620 ≤ $12**. V4 preparation closes/counts `dev-gate/pre-v4` in
addition to prior scopes. The earlier snapshot below is preserved as chronology;
it is superseded for the future allowance calculation.

Read-only ledger aggregate at **2026-09-30 04:08 UTC** (retained reserves included):

| Prior scope | Charged USD |
| --- | ---: |
| final-evaluation (abandoned original, ledger only) | 0.02058083 |
| dev-gate/option-a | 0.10791745 |
| final-evaluation-v2 | 2.94519961 |
| dev-gate/after-v2 | 0.27667768 |
| final-evaluation-v3 | 0.47321405 |
| dev-gate/post-v3 | 0.71924554 |
| **Prior total** | **4.54283516** |

**$4.54283516 + $3.00 v4 + $0.10 release-smoke allowance = $7.64283516 ≤ $12.00**;
remaining margin $4.35716484. Four prior unknown-cost attempts remain charged,
not forgiven. This is evaluation/dev accounting with the declared release-smoke
allowance, not total Azure infrastructure or all historical production-model billing.

After release approval, budget preparation locks/closes all six prior scopes,
keeps every reserve, inserts only the new $3 daily policy and single $3 lifetime
run, and verifies the cumulative inequality in the same transaction. A changed,
disabled, duplicate-run or overspent current scope fails; conflict handling never
resets or re-enables it. Calls commit reservations before requests; settlement is
independent of customer transactions. The lifetime limit spans UTC days/restarts.
Start/resume and progress verify accounting and fail on history regression.
Preparation rechecks live exposure: this snapshot is not a future spend guarantee.

**No Azure scope was created or enabled in this preparation session.** Only local
mock/disposable-Postgres tests may write a test scope. The future commands are in
[the final-run plan](final-run-plan.md); neither preparation nor start was executed.
