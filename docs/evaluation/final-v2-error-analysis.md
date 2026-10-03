# Development record moved

Read the [complete archived record](../history/evaluation/final-v2-error-analysis.md).
The [final evaluation (v4)](final-v4-results.md) remains unchanged.

<details>
<summary>Compatibility excerpt for existing chart tools</summary>

# Final v2: official results and post-hoc error analysis

**POST-HOC — 2026-09-27.** Evaluated release:
`fd34c7dce11cf9db6f71e84ae4fbb2ccc19de415`.
V2 completed 700 system case-runs and 150 judge items in about 2h20m.
The owner authorized this subsequent, zero-call analysis after completion.
The official `artifacts/final-program-v2/results.json` and `results.md` remain
unchanged. No rescoring, held-out rerun, prompt/model/policy change, suite edit,
or improvement claim is made. The abandoned v1 directory was never accessed.
Only aggregates, case IDs and implementation explanations appear here.

## Official headline report

Primary pass only; repeats are excluded from the following tables. Sonnet used
the predefined 100-case subset, so its headline rate is not a comparison on all
200 cases. SAR below uses the in-scope denominator. Containment measures absence
of a handoff, including unsuccessful outcomes.

| Metric | B1 | P-Gemini | P-Sonnet |
|---|---:|---:|---:|
| Pass | 65/200 (32.5%) | 63/200 (31.5%) | 37/100 (37.0%) |
| SAR / in-scope | 41/193 (21.2%) | 39/193 (20.2%) | 26/98 (26.5%) |
| SAR Wilson 95% interval | 16.1–27.5% | 15.1–26.4% | 18.8–36.0% |
| Containment | 46/200 (23.0%) | 115/200 (57.5%) | 65/100 (65.0%) |
| Strict escalation recall | 24/66 (36.4%) | 27/66 (40.9%) | 11/30 (36.7%) |
| Missed transfers | 42/66 | 39/66 | 19/30 |
| Unnecessary transfers | 88/134 | 34/134 | 13/70 |
| Executed / workload | 187/200 | 187/200 | 94/100 |
| Unreached fault fixtures | 13 | 13 | 6 |
| Turn latency p50 / p95 | 0.988 / 1.985 s | 3.351 / 7.381 s | 7.326 / 14.627 s |
| Case latency p50 / p95 | 1.959 / 3.935 s | 6.043 / 11.009 s | 12.780 / 20.774 s |
| Primary-pass model cost | $0 | $0.391572 | $1.606960 |
| Model cost / workload case | $0 | $0.001958 | $0.016070 |
| Model cost / SAR | $0 | $0.010040 | $0.061806 |

**All three systems failed the safety gates.** Official executed-case unsafe
counts are below. These categories overlap; do not add them into a case count.
All other unsafe categories were zero, including missing confirmation/step-up,
reported-but-unverified actions, disclosure, grounding violations and refund
promises. Zero observed events do not establish zero risk.

| Unsafe category / forbidden action | B1 (n=187) | P-Gemini (n=187) | P-Sonnet (n=94) |
|---|---:|---:|---:|
| Unauthorized action | 0 | 1 | 1 |
| Policy violation | 0 | 1 | 1 |
| Materially incorrect outcome | 1 | 59 | 29 |
| Forbidden `create_dispute` | 0 | 1 | 1 |

The official materially-incorrect counts all coincide with the scorer's
explanation-versus-gold-outcome mismatch predicate. They are not independent
human judgments that the stated transaction facts were false. This does not
remove the failures; see the gold and metric limitations below.

### ES versus PT

These languages do not exhaust the suite: it also includes mixed/other cases.
Strict escalation below is reconstructed from the existing strict missed-transfer
counts because the published slice escalation field has the bug in section 6.

| System | Language | SAR / in-scope | Containment / workload | Strict escalation |
|---|---|---:|---:|---:|
| B1 | ES | 21/96 (21.9%) | 23/96 (24.0%) | 10/25 (40.0%) |
| B1 | PT | 13/77 (16.9%) | 15/84 (17.9%) | 14/35 (40.0%) |
| P-Gemini | ES | 21/96 (21.9%) | 59/96 (61.5%) | 9/25 (36.0%) |
| P-Gemini | PT | 12/77 (15.6%) | 41/84 (48.8%) | 15/35 (42.9%) |
| P-Sonnet | ES | 14/54 (25.9%) | 39/54 (72.2%) | 4/14 (28.6%) |
| P-Sonnet | PT | 7/30 (23.3%) | 16/32 (50.0%) | 5/12 (41.7%) |

Full-suite paired P-Gemini minus B1 SAR difference: **−1.04 percentage points**,
95% paired interval **−8.81 to +6.74 points**. On the repeated subset, McNemar
p=0.627. No supported automation improvement is established. Outcome, success
and SAR flip rates were each **0/100** across the three Gemini passes; the
Wilson upper bound is 3.70%. Stable results can still be consistently wrong.

### Judges, cost and human review

There were **143/150 valid judge pairs**: 46/50 calibration and 97/100 frozen
assessments. Seven items failed with `ModelFailure`; they were not rerun.
Frozen Sonnet-versus-Jev agreement:

| Dimension | Paired n | Exact agreement | Within one point | Weighted kappa |
|---|---:|---:|---:|---:|
| Language/register | 97 | 68.0% | 97.9% | 0.888 |
| Clarity | 97 | 26.8% | 93.8% | 0.117 |
| Empathy | 97 | 34.0% | 100% | 0.313 |
| Handoff usefulness | 53 | 100% | 100% | Undefined: no score variance |

V2 durable readback: **$2.94519961**, 1,801 reservations, **zero unknown costs**.
Known cumulative v1/dev/v2 cost: **$3.06646189**. Cumulative charged/reserved
exposure: **$3.07369789**, including the older unsettled reservation; this is
below the $12 ceiling. Old-scope totals came only from aggregate budget-table
readback, without opening abandoned artifacts. Infrastructure and release smoke
are separate from these evaluation scopes.

The completed, blank 20-item review sheet is
`artifacts/final-program-v2/human-judge-20.csv`. Human scores, judge–human
agreement and fluent-human PT review remain pending. Machine agreement is not
human validation. Full metric intervals and dialect/segment slices remain in
the unchanged official artifacts; small cells are not reliable population claims.

</details>
