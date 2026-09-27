# Progress log

Session: handoff 08, 2026-09-26 America/Vancouver; continued 2026-09-27 UTC.
This summary supersedes earlier task lists. Earlier release evidence remains in Git history and linked reports.

## Completed-verified

### Human es-CL spot-check — Data/ML follow-up, 2026-09-27 UTC

- Preserved Sebastian's nine recollections and intentional typos. Independently authored and hashed gold intent/slots before inference from brief §5.2/§9. Verified nine owned targets, nine distinct customers and no overlap with any v1 matcher benchmark split. No frozen scenario-suite access or policy execution.
- Ran the approved `google/gemini-3-flash-preview` NLU → unchanged v1 MATCH chain at `c8588f4fc39593ab60ab0bfe9eeaab6bb6309a84`: nine valid calls, zero fallbacks, **US$0.009933** provider-reported cost against the US$0.50 cap. Kept the worktree key private and process-local; no model thinking stored.
- Published aggregates in the [result review](../ml/result-review.md#human-spot-check-n9-es-cl) and [model card](../ml/model-card-charge-matcher.md#human-spot-check-n9-es-cl): intent 5/9, corrected core slots 7/9, top-1 6/9, recall@3 8/9, **nine no-match decisions**. A documented post-inference annotation serialization correction changes core-slot accuracy from 6/9 to 7/9; original frozen labels and predictions remain intact. No model, prompt or threshold changed.
- Wrote and read back all nine detailed intent/slot/transaction/decision reports, gold, billing, runner and manifests under ignored `artifacts/human-validation/spanish-40/spotcheck-es-cl-v1/`. Source recollection bytes remain unchanged. No card field values entered Git.
- Independent aggregate/billing recomputation, all artifact hash checks, verbatim recollection readback, 13 local documentation links, diff whitespace and staged-file policy passed. This change touches only the two requested ML documents plus this additive session entry.

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

### Restricted release preparation

- Read-only probe from the existing Azure web container reproduced API HTTP 403 under the API's owner-IP rule. Prepared an **internal-only API in the same existing Container Apps environment** and retained owner-IP-only HTTPS on web plus login. No new resources, networking products, replicas or broader internet ingress. The web BFF keeps bearer tokens out of browser JavaScript.
- Azure full gold load was initially interrupted during slow small-batch checksum readback, rolling back its uncommitted transaction. Restarted with 5,000-row batches and the same full checks. The restarted Azure load passed full checksums and independent committed readback for all six tables, four private personas and 15 scoped transactions. Deployment verification remains pending below.
- Existing approved PostgreSQL Azure-services firewall exception, Key Vault passwords, managed identities, TLS verify-full and approximate US$30/50-equivalent budget alerts remain required. [Network plan](../azure-private-dev-plan.md), [production limits](../production-readiness.md).

## Done-not-verified

- Human es-CL spot-check: independent human gold review and agreement are unavailable. This is NLU → MATCH only, not full conversation/action or production validation; the remaining 31 private Spanish cards are blank.
- Clean-main deployment, BFF/browser smoke, replacement-replica recovery, control readback and final external denial/drift checks are in progress. Do not treat local success as a cloud claim.
- Frozen acceptance after these fixes remains unknown; the preserved run-01 failure is the only full-suite result. Human labels, Spanish owner review and fluent Portuguese review remain pending. PT/dialect phrases are model-authored; prior cross-vendor authoring checks do not replace human review.
- No lead real-model comparison, selected default or different-vendor judge run. Keep `LLM_PROVIDER=mock`. Durable model spend accounting remains future work.
- Azure PITR/regional DR, realistic-volume restore, automatic retention, sustained concurrency, actual charges and budget-email delivery are unverified. Tiny local restore evidence remains in [recovery report](../ops-recovery.md).

## Next-blocked

- Human es-CL follow-up: review the private per-case report with Sebastian; investigate disputed-charge intent handling, abbreviated amounts, unrelated date binding and rejection by the frozen match-exists threshold on separate development examples. Preserve current gold/predictions and the frozen model; this session makes no tuning changes.
- Finish PR #26 gates, merge to main, deploy that exact clean main SHA to existing approved resources, then verify the restricted organizer-backed cloud release and record evidence here.
- Next layer after this release: provider comparison on the independent dev suite, broader independently authored language cases and human review. Show the cost estimate and wait for Sebastian's go before any real-model run. No cloud expansion, access broadening or estimate above US$40/month is authorized.
- Reserve the one remaining full held-out diagnostic; log every access, preserve frozen bytes and publish only aggregates. The final evaluation must use organizer serving source and declared overlays.

## Access and continuation

Restricted web: https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io/
Use `demo.es.mx` or `demo.pt.br` for the three-surface workspace; `demo.es.co` and `demo.es.ar` are customer-only. Retrieve `demo-password` from the authenticated Key Vault portal; never paste it into chat, Git or logs. OTP is simulated. Re-login after the identity-source migration; prior fixture sessions do not grant organizer access.

For later sessions, paste: **Continue from docs/status/progress-log.md. Next layer: provider comparison and independent language coverage. Same rules.**
