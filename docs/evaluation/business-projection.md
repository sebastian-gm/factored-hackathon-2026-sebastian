# Business projection — illustrative capacity, not realized savings

> **superseded by v4 (2026-10-01)** — Historical evaluation/release status below; use the [current summary](../../README.md) and [official v4 results](final-v4-results.md). [Post-v4 fixes](post-v4-release-notes.md) are **not reflected in v4 numbers**.

For **10,000 charge-dispute intake conversations per month**, the base scenario
projects **3,900 safely automated intake outcomes**, **1,200 fewer unnecessary
transfers than B1**, **11,621 agent minutes released**, and **$58.77/month in model
plus infrastructure cost**. These are conditional calculations using the
assumptions below. They are not measured production benefits: v3 failed the full
safety gate, and traffic mix, dispute-specific handling time and production
capacity remain unvalidated. This is a **historical v3-based calculation**, not
an updated v4 forecast. [V4 results are complete](final-v4-results.md); their
measured cost and both SAR denominators are in the [current summary](../../README.md).

## Historical problem and addressable demand

All dataset facts below come from the committed
[pipeline aggregates](../data/problem-analysis-aggregates.json), explained in
[problem analysis](../problem-analysis.md). The source is synthetic historical
operations, not live bank traffic.

| Observed dataset fact | Value | Aggregate field / meaning |
|---|---:|---|
| Complaint-contact first-contact resolution proxy | **43.6%**, n=117,021 | `contact_reasons[Queja].fcr`; mean non-null `was_resolved`, not an audited issue-level recontact measure |
| Identified unrecognized-charge complaints | **12,297 / 67,095 = 18.33%** | `complaint_mix[Cargo no reconocido].n / tables.complaints.rows` |
| Transactional contacts | 240,056 | `contact_reasons[Transaccional].n`; includes more than charge disputes |
| Complaint-contact mean handle time | **434.606 s = 7.2434 min** | `contact_reasons[Queja].mean_duration_seconds`; broad complaint category |
| Transactional-contact mean handle time | **220.803 s = 3.6800 min** | `contact_reasons[Transaccional].mean_duration_seconds`; broad transactional category |
| Complaint-contact mean wait | 119.982 s ≈ 2 min | `contact_reasons[Queja].mean_wait_seconds`; excluded from agent work minutes |

The 18.33% identifies the labeled charge-dispute subset; fees and unlabeled
transaction complaints are not silently added. Historical counts are totals over
the delivered period, not monthly demand. Contact and complaint records may
represent the same issue and cannot be added without deduplication/overlap
analysis; broken complaint-to-product links prevent a reliable transaction-level
join. **10,000/month is an assumed planning volume**, not derived from those
counts. FCR 43.6% and evaluation SAR use different populations and definitions;
their difference is not an estimated FCR uplift.

## Official v3 evidence after v2-informed fixes

V3 evaluated a fresh 100-case suite at `e12efc7`, before post-v3 fixes. V2 remains
the official prior result. V3 is now **seen dev data**; later reported 100/100
checks do not replace these saved primary results. Sources:
[official v3](final-v3-results.md), [official v2](final-v2-error-analysis.md).

| Primary metric | B1 | P-Gemini |
|---|---:|---:|
| Conversation pass | **52/100** | **77/100** |
| Safe automation rate (SAR) / in-scope | **28/100 = 28%** | **39/100 = 39%** |
| Strict correct escalation / must-transfer | **20/40 = 50%** | **30/40 = 75%** |
| Unnecessary transfers / automation-eligible | **23/60 = 38.3%** | **11/60 = 18.3%** |
| Model cost / workload conversation | $0 | **$0.00237687544**, approximately **$0.002** at three decimal places |
| Case system-time p50 / p95 | 3.023 / 5.921 s | **7.432 / 13.704 s** |
| Turn system-time p50 / p95 | 1.999 / 4.038 s | **4.118 / 7.878 s** |

Paired P-minus-B1 SAR is **+11 percentage points (95% bootstrap CI +5 to +17)**.
The unnecessary-transfer difference is **12 per 100 workload cases**, or 20 pp
within the 60 eligible cases. Strict escalation includes correct routing,
reasons/fields and readback; handoff presence alone is insufficient. These
latencies include workstation-to-Azure Postgres reads, exclude customer think
time, and precede request caching; they are not deployed UI or completed
complaint-resolution timings. Exact per-call cost, not the rounded $0.002,
is used in the projection. Offline judges, repeats and infrastructure are
excluded from that measured serving-model cost. [V3 definitions and timing](final-v3-results.md).

**Both systems failed the complete safety gate**: fraud/regulator recall was
1/5 B1 versus 2/5 P; required readbacks 58/74 versus 67/74. P observed zero critical
unsafe predicates in 100 cases, with a 3.70% upper 95% bound, not proof of zero
risk. No deployment or realized savings claim follows from this projection.
“Safely automated resolution” here means the evaluator's correct explanation
or verified intake outcome, **not a refund or final adjudication of a dispute**.
[Safety evidence](final-v3-results.md#safety-and-readbacks).

## Assumptions and reproducible calculation

Compare P with **B1 on the same assumed workload**, not with an entirely manual
bank. Adopt v3's 60% eligible / 40% must-transfer mix solely as a planning
assumption. Real charge-intake traffic must be audited and reweighted before
using these rates operationally. Every issue not safely automated still needs
human handling or remediation; a missed transfer earns no time-saving credit.

Let `N=10,000`, baseline automation `r_B=0.28`, P automation `r_P`, baseline
human minutes `h_B`, assisted minutes `h_P`, review minutes per automated issue
`v`, remediation minutes per incoming issue `w`, reduction in unnecessary
transfers per incoming issue `d_u`, model cost `c`, and monthly infrastructure
allocation `I`.

```text
P automated intake outcomes       = N × r_P
Incremental automated versus B1   = N × (r_P − r_B)
Avoided unnecessary transfers     = N × d_u
B1 agent minutes                  = N × (1 − r_B) × h_B
P agent minutes                   = N × [(1 − r_P) × h_P + r_P × v + w]
Net agent minutes released        = B1 agent minutes − P agent minutes
Model plus infrastructure cost    = N × c + I
```

Avoided transfers can overlap incremental automation. They are reported
separately and **not added again** to agent minutes. The residual `(1−r_P)`
term assumes complete human follow-up of all nonautomated issues, including
failed intakes; it does not use the observed incomplete handoff count as a
shortcut. Review and remediation include post-intake rework overhead. These
unmeasured operating assumptions are explicit rather than treated as facts.

| Input | Low benefit | Base | High benefit | Evidence or assumption |
|---|---:|---:|---:|---|
| Monthly unique in-scope intake conversations `N` | 10,000 | 10,000 | 10,000 | Assumption; deduplicated issue volume, not dataset monthly volume |
| B1 automation `r_B` | 28% | 28% | 28% | V3 point estimate reused as an assumed traffic rate |
| P automation `r_P` | 33% | 39% | 45% | B1 28% + paired SAR uplift 5 / 11 / 17 pp; endpoint sensitivity, not marginal P confidence bounds |
| Transfer reduction `d_u` | 6% | 12% | 18% | Base: (23−11)/100; low/high assumed half / 1.5× that change, not confidence limits |
| Baseline human handling `h_B` | 7.2434 min | 7.2434 min | 7.2434 min | Exact Queja mean 434.6059149979648/60 reused as a **proxy assumption** for dispute intake |
| Assisted human handling `h_P / h_B` | 100% | 85% | 70% | Assumed packet-assisted efficiency; no measured agent time study |
| Review `v`, min / automated issue | 0.50 | 0.25 | 0.10 | Assumption: review/monitoring burden |
| Remediation `w`, min / incoming issue | 0.50 | 0.20 | 0.10 | Assumption: average recontact/catch-up burden, including nonautomated failures |
| Serving cost multiplier | 2.0× | 1.0× | 0.8× | Applied to measured $0.00237687544; retry/turn sensitivity assumptions |
| Monthly infra allocation `I` | $70 | $35 | $25 | Assumptions anchored to the historical dev plan below; not a production quote |

The [2026-09-27 Azure dev plan](../azure-private-dev-plan.md#live-east-us-2-price-check)
modeled **$34.63/month without free grants**, or roughly **$24.19–$29.19 with
available grants**, under its stated low-traffic configuration. Base $35 rounds
that plan; high-benefit $25 assumes available grants; low-benefit $70 doubles
the base for usage headroom. This does not validate capacity for 10,000
conversations or include production HA, staffed support, compliance, tax or labor.
These historical rates are a reference, not a fresh cloud price check or spending
authorization. The table allocates the whole assumed demo stack once; it does
not also charge that allocation per transfer.

## Monthly sensitivity outputs

Arithmetic uses the exact historical handle-time proxy and serving cost, then
rounds outputs. These scenarios vary assumptions together; they are **not a
joint confidence interval** or a traffic-weighted forecast.

| Output per 10,000 incoming issues | Low benefit | Base | High benefit |
|---|---:|---:|---:|
| P safely automated intake outcomes | **3,300** | **3,900** | **4,500** |
| Additional automated outcomes versus B1's 2,800 | 500 | 1,100 | 1,700 |
| Avoided unnecessary transfers versus B1 | **600** | **1,200** | **1,800** |
| B1 agent minutes | 52,153 | 52,153 | 52,153 |
| P agent minutes, including review/remediation | 55,181 | 40,532 | 29,337 |
| Net agent minutes released | **−3,028** | **11,621** | **22,815** |
| Net agent hours released | −50.5 | 193.7 | 380.3 |
| Serving-model cost | **$47.54** | **$23.77** | **$19.02** |
| Infrastructure assumption | $70.00 | $35.00 | $25.00 |
| Model + infrastructure | **$117.54** | **$58.77** | **$44.02** |
| Model + infrastructure / incoming conversation | $0.01175 | $0.00588 | $0.00440 |

The low case **adds work** despite automating more intakes. Even the base is
sensitive to using a broad complaint handle-time proxy: replacing only `h_B`
(and the proportional `h_P`) with the observed transactional-category mean
3.6800 min reduces base savings to **4,440 minutes**, with all other assumptions
held fixed. Neither mean is a measured charge-dispute handling time. Hours are
potential capacity, not guaranteed headcount, wage savings or customer-outcome
improvement. No labor rate or ROI percentage is invented.

## V4 evidence and operational validation

[V4 is complete](final-v4-results.md): P SAR was 32/100 in scope and 32/47
among eligible cases, versus B1 22/100 and 22/47. P model cost was
$0.002297661 per evaluated case and $0.007180189 allocated per safe automated
resolution. Both systems failed full safety gates. These observations replace
pending-result placeholders; the historical v3 sensitivity calculation above
is retained with its original assumptions, not silently recomputed.

Traffic weighting/deduplication, dispute-specific handling, packet review,
recontact burden, production capacity and current infrastructure prices still
need operational measurement. Time-to-verified-intake must separately include
authentication and customer think time; neither handle time nor historical
complaint-resolution days supplies that baseline. No paid call, new cloud
resource or evaluation execution was required for this documentation update.
