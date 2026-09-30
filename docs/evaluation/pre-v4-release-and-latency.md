# Pre-v4 release, shared development and Azure latency

Sebastian's standing approval on **2026-09-30** covers integration #62 into main
after green remote CI, release of main, and spending within the $12 cumulative
ceiling. #76 joins the reviewed integration. Resources, replicas and access stay
unchanged; submission warm/public modes remain OFF. The separately approved
temporary smoke-run binding changes only `LLM_BUDGET_RUN_ID` alongside image tags.

**Feature freeze: 2026-10-02 12:00 COT (17:00 UTC).** The frozen v4 release and
single final program follow that freeze and a separate run GO. This document
does not authorize v4 input access, preparation or execution now.

## Shared dev purse

- Scope **`dev-gate/pre-v4`**, run ID **`pre-v4`**, **$1.00 lifetime** shared by
  every lane, vendor, risk check, fallback and retry. Never use a new run to reset it.
- `PRE_V4_BUDGET_PREPARATION_APPROVED=1 .venv/bin/python -m scripts.pre_v4_budget --prepare`
  runs only after release. Verify separately with
  `.venv/bin/python -m scripts.pre_v4_budget`; ignored receipt:
  `artifacts/pre-v4-dev/budget.json` (0600).
- Preparation locks/closes prior evaluation and dev policies, including post-v3,
  preserving actual charges and unknown reserves. Conflicting current policy,
  disabled breaker or extra run fails without resetting history. Failure rolls
  back the closure and insert. Calls commit their `PostgresSpendGate` reservations
  before provider calls; settlement is independent of customer transactions.
- AI adapters must use `PostgresSpendGate(store, scope="dev-gate/pre-v4", run_id="pre-v4")`.
  The lead runner accepts `--profile pre-v4`, using existing development inputs;
  no v4 scenario enters this path. Paid dev runs still need an estimate and the
  lane's authorization. This setup itself makes no provider call.

Read-only live ledger at **2026-09-30 18:01 UTC**:

| Exposure / allowance | USD |
| --- | ---: |
| Prior evaluation/dev charges with unknown reserves retained | 4.54283516 |
| Historical production charges, including earlier smokes | 0.03580104 |
| New shared pre-v4 dev maximum | 1.00 |
| V4 lifetime maximum | 3.00 |
| New release smoke maximum | 0.10 |
| New latency smoke maximum | 0.10 |
| **Maximum cumulative** | **8.77863620 ≤ 12.00** |

Margin **$3.22136380**. Every preparation rechecks live aggregates. V4 preparation
also closes/counts pre-v4 and counts production history; both smoke allowances
remain reserved conservatively even after some smoke spend. Four prior unknown
costs stay charged. These caps do not cover Azure infrastructure or Actions bills.

## Release purses and gates

After main is verified, let `RELEASE_SHA` be its full SHA (not a private identifier):

```bash
SMOKE_BUDGET_PREPARATION_APPROVED=1 .venv/bin/python -m scripts.release_smoke_budget release --sha "$RELEASE_SHA" --prepare
```

The registered production lifetime run is `pre-v4-release-<full-SHA>`, capped
at $0.10 beneath the existing global $3/day breaker. Set the private Terraform
smoke-run input to this ID. Plan/apply must show only existing image/release
identity changes and the approved binding; no resource creation, replica or
access change. Use the explicit sandbox subscription for every Azure operation.

Full gate: exact main CI/safety, pushed images, reviewed plan/apply,
`azure_smoke`, `azure_verify`, real `azure_llm_smoke`,
`serving_browser --target azure`, outside-network `azure-access`, and a new
`artifacts/azure/jev-release.json` at the implementation SHA with all three
acceptance flags true. Real smoke/browser share:

```bash
AZURE_RELEASE_SMOKE_RUN_ID="pre-v4-release-$RELEASE_SHA" .venv/bin/python -m scripts.azure_llm_smoke
AZURE_RELEASE_SMOKE_RUN_ID="pre-v4-release-$RELEASE_SHA" .venv/bin/python -m scripts.serving_browser --target azure
```

The existing five-conversation counter remains in force; no exhausted run or
checkpoint is reset. A successful release is reported before dev scope creation.

## In-region latency probe

Prepare `pre-v4-latency-<full-SHA>` with the same helper's `latency` kind, $0.10
lifetime, then temporarily bind that run through the reviewed existing-app plan.
Read controls back again. Estimated model spend **$0.03–$0.08**, hard stop **$0.10**.

```bash
SMOKE_BUDGET_PREPARATION_APPROVED=1 .venv/bin/python -m scripts.release_smoke_budget latency --sha "$RELEASE_SHA" --prepare
AZURE_LATENCY_PROBE_APPROVED=1 LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.azure_latency_probe
```

The probe requires clean main equal to origin/main, the accepted release SHA,
live serving and its new bound purse. Ten new authenticated conversations (five
ES, five PT) each request two explanations through deployed BFF. Owned transaction
facts exist in memory only. No confirmation, freeze, claim, resolve or reset is
sent. Each conversation must reach a valid real-model call; failures/budget denials
stop without a paid retry. An existing launch marker prevents duplicate runs.

The duration-only **`Server-Timing: aclara_bff;dur=<milliseconds>`** measures
handling inside Azure's BFF, including API/provider/accounting and read-back time.
The wrapper changes no auth, retry, action body or response data. Workstation-to-
Azure network time is excluded from this server measurement and reported separately
as client elapsed time. Ingress scheduling/module loading before the handler is
not included; client startup retains it. No artificial cold restart is triggered.

Report turn p50/p95 for all 20 turns and startup-excluded turns (exclude the entire
first conversation, leaving 18); configuration/auth/session setup is reported
separately and excluded from both turn groups. Quantiles use linear interpolation.
This small sample is a latency check, not evaluation accuracy or an SLO guarantee.
Private aggregate output: `artifacts/azure/pre-v4-latency-<SHA>/latency.json` and
`latency.md`, plus launch/progress checkpoints; no row text, credentials or model
thinking. Verify final charge and unknown-cost count from the durable ledger.

## Subsequent private snapshot export

After release, export a clean snapshot to a new **private**
`sebastian-gm/factored-hackathon-2026-sebastian`. Apply #71's scrub list (metadata
emails, URL literals, Azure hosts, workstation paths, private-repo links), retaining
honest v1→v4 chronology. Push the snapshot, scan its contents/history with Gitleaks,
and report. The personal sandbox remains private. Public visibility requires
Sebastian's explicit submission-day approval; no visibility change is authorized here.
