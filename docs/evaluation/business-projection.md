# Business projection — not a measured production improvement

Status: calculation framework with visible missing inputs. The
[held-out mock diagnostic](heldout-run01.md) failed safety gates; its SAR cannot
support a deployable-benefit claim. No savings estimate is reported until an
acceptable approved result and workflow-specific operating assumptions are available. Historical synthetic operations, controlled scenario
results and this projection are three different workloads.

## Historical base and exclusions

The [pipeline aggregate](../data/problem-analysis-aggregates.json) records 12,297
“Cargo no reconocido” complaints out of 67,095 complaints: **18.33%** (rounded from
that ratio). It also records 240,056 Transaccional contacts. The latter category
includes more than charge questions; its entire volume is not automatable demand.
These are delivered-history totals, not monthly volume. Fees remain a human workflow.

Sources: `complaint_mix`, `tables[complaints].rows` and `contact_reasons` in the
aggregate; definitions are in [problem analysis](../problem-analysis.md). Complaint
and contact counts cannot simply be added: the same customer issue can appear in both.
Broken complaint-to-product links also preclude a trustworthy transaction-level join.

For a chosen common period H, define:

- `C_H`: deduplicated unrecognized-charge complaint issues in H.
- `T_H`: deduplicated charge-question issues in Transaccional contacts in H.
- `O_H`: overlap between those issue sets; `A_H = C_H + T_H - O_H`.
- `r`: offline SAR/in-scope from the approved, traffic-reweighted held-out result.
- `q`: observed handoff share on that same eligible workload definition; do not
  replace `r` with containment or treat a correct handoff as automation.
- `h_before`: observed human handling seconds per selected issue before deployment.
- `h_after`: measured handling seconds for an assisted handoff, including packet review.
- `h_review`: human review/monitoring seconds per safely automated issue.
- `h_rework`: expected recontact/remediation seconds per incoming issue, measured separately.

The controlled test suite's safety/category mix is intentionally not historical
traffic. Reweight only after validating a compatible traffic taxonomy and sufficient
sample sizes. Where an input is unavailable, keep it missing rather than borrowing an
unrelated contact-category average.

## Calculations and sensitivity

Projected safely automated issues in H: `A_H × r`.

Projected baseline agent hours: `A_H × h_before / 3600`.

Projected assisted agent hours: `A_H × (q × h_after + r × h_review + h_rework) / 3600`.

Projected net hours released: baseline hours minus assisted hours. Include any
unresolved/non-transferred cases in remediation assumptions; otherwise the formula
would reward unsafe containment. Negative savings are a valid result. The unit
conversion is arithmetic, not a measured parameter.

| Input/output | Low benefit | Base | High benefit |
| --- | --- | --- | --- |
| Addressable issues | Audited lower bound on unique issues | Audited central count | Audited upper bound; no extra workflow |
| SAR | Lower paired/clustered interval bound after traffic weighting | Point estimate | Upper bound, capped by eligible share |
| Handoff and rework burden | Upper observed burden | Central observed burden | Lower observed burden |
| Assisted handling/review time | Slower observed estimate | Central observed estimate | Faster observed estimate |
| Projection | TODO(results): low projected agent-hours | TODO(results): base projected agent-hours | TODO(results): high projected agent-hours |
| Time to verified intake | TODO(results): conservative intake time | TODO(results): central intake time | TODO(results): favorable intake time |

For transparency, the current **unweighted, failed-gate diagnostic** gives a SAR
point estimate of 34.72% and Wilson bounds 28.36–41.67% for both systems
([B1 `sar_in_scope`](heldout-run01-B1.json), [P/mock](heldout-run01-P-mock.json)).
Those are measured diagnostic inputs, not traffic-weighted low/base/high production
assumptions. We do not turn them into savings while safety and operating inputs
remain unresolved.

These sensitivity directions define scenarios, not invented numerical assumptions.
They are not a joint confidence interval; correlation between SAR, handoffs and case
mix must be retained when joint case-level evidence becomes available.

## Time-to-case and input register

Define time-to-case as elapsed time from the first charge request to a **verified
case intake**, including authentication, customer think time and system work. The
harness's summed system-time latency excludes think time, so it is only a component.
Historical complaint resolution duration is not a valid baseline for intake time.

| Required input | Source / status |
| --- | --- |
| Period H, charge taxonomy, deduplication and overlap | TODO(results): audited addressable issue count and period from pipeline outputs |
| SAR, transfers and unsafe rates with uncertainty | Mock diagnostic exists but fails safety gates; TODO(results): accepted B1/P result and workload reweighting |
| Human handling, packet review and rework times | TODO(results): workflow-specific measured assumptions; historical category means are context only |
| System latency and verified-intake subset | TODO(results): `results.json` and private per-case aggregation |
| Authentication, think time and prior intake baseline | TODO(results): observed intake timing; no imputation from resolution days |
| Projected net hours, agent-hours per 1,000 and time-to-case | TODO(results): low/base/high outputs after the above inputs are available |

No headcount reduction, currency savings or customer-outcome improvement is claimed.
A monetary projection would additionally need approved labor and infrastructure
assumptions. Fraud/regulator safety gates must hold before discussing efficiency.
