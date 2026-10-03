# Held-out diagnostic: B1 and P/mock

This is a controlled, model-free diagnostic with pending human labels. **Acceptance gates failed.** It is not a production-readiness or real-model quality claim.

System implementation `564f008cff952ffdd7c0eab7dda6255ce17f709d`; measurement correction `25c1c4fcd2d93bc9ed0a5ad2f4cc8f3fab850968`. Manifest `acf0f74156c938323dc2a5c752072b4fd5febc1aced81ad0aa2a670201d0683d`. Source, binding, model/prompt/policy versions and interval details are in the aggregate JSON files.

## Execution and results

`.venv/bin/python -m evals.heldout --run` attempted B1 200 + P/mock 200 + two P/mock repeats of the frozen 100-case subset. All 600 observations are preserved privately. Model cost: **US$0**. B1 had two unreachable NLU-outage boundaries (198 executed); P/mock executed all 200. Both headline denominators retain 200 workload cases.

| Metric | B1 | P/mock |
| --- | --- | --- |
| Passed workload cases | 67 | 67 |
| SAR / in scope | 67/193 (34.7%) | 67/193 (34.7%) |
| SAR / eligible | 67/134 (50.0%) | 67/134 (50.0%) |
| Automation attempts / in scope | 83/193 (43.0%) | 83/193 (43.0%) |
| Containment / workload | 86/200 (43.0%) | 86/200 (43.0%) |
| Correct escalation / must-escalate | 0/66 (0.0%) | 0/66 (0.0%) |
| Handoff presence / must-escalate | 54/66 (81.8%) | 54/66 (81.8%) |
| Unnecessary transfers | 60/134 (44.8%) | 60/134 (44.8%) |
| Routing accuracy (explicit gold) | 5/9 (55.6%) | 5/9 (55.6%) |

SAR/in-scope Wilson 95% interval: **28.36–41.67%**. Paired P−B1 SAR difference is 0 (95% interval [0, 0]); no improvement supported. Repeated-subset exact McNemar p=1; 0/100 outcome flips. Per-repeat mean/ranges and cluster intervals are in `heldout-run01-comparison.json`.

Local in-process turn p95: B1 2.18 ms; P/mock 2.42 ms. These exclude network/cloud and real-model latency. Case measurements include action verification. The monthly infrastructure estimate US$34.63 is separate and subject to usage.

## Safety and gaps

- Six cases per system executed a dispute where ESC-04 gold forbids it. No observed authentication/step-up bypass: these are routing/policy violations.
- Nine cases per system were flagged for materially incorrect outcomes.
- No observed unauthorized disclosure, confirmation/step-up bypass, unverified success claim, grounding flag or refund promise. Zero observed does not establish zero risk: upper bound 3/n is 1.52% for B1 and 1.50% for P/mock. Detectors have the limits documented in the adapter notes.
- Required readbacks: 123/140. Required complete handoffs: 0/54. Handoff presence is 54/66, but the full packet/route/reason requirement yields 0/66 correct transfers, including 0/11 fraud/regulator transfers. Report presence separately from successful transfer.
- The rule-based NLU missed many authored explanation/status/security phrasings. Mock P falls back to that baseline. All raw observations, including failures, remain preserved. No threshold/model/policy tuning or suite edits followed this diagnostic.

## Measurement correction and access history

The first `--run` invocation stopped in argument parsing before creating an access record or invoking a system. The subsequent run at the SHA above completed. Post-run audit found the adapter treated generic `created-state` as card-only and omitted explanation target observations. Separate dev fixtures reproduced the measurement errors. `evals.rescore` corrected only those measurements from the same saved API observations, with zero new system/model calls. Original aggregate files (`heldout-run01-original-*.json`) remain committed and explicitly superseded. Labels, suite bytes and system actions were unchanged. The original undercount was 11 passed; corrected count is 67. All failed safety gates remain failed.

## Slices

B1 and P/mock have identical SAR counts below. Full slices include Wilson intervals, escalation errors, unsafe categories, latency, category/rule composition and DSP-07/BRD-01/ESC-05 by segment in the aggregate JSON.

| Slice | Workload n | SAR / in scope |
| --- | ---: | ---: |
| language: es | 96 | 37/96 |
| language: mixed; insufficient sample | 17 | 8/17 |
| language: other; insufficient sample | 3 | 0/3 |
| language: pt | 84 | 22/77 |
| dialect: es-AR | 32 | 12/32 |
| dialect: es-CO | 32 | 12/32 |
| dialect: es-MX | 32 | 13/32 |
| dialect: mixed; insufficient sample | 17 | 8/17 |
| dialect: other; insufficient sample | 3 | 0/3 |
| dialect: pt-BR | 84 | 22/77 |
| segment: Basic | 50 | 19/48 |
| segment: Plus | 51 | 16/50 |
| segment: Premium | 51 | 18/50 |
| segment: Student | 48 | 14/45 |

Language/dialect and segment gaps exceed five percentage points. These slices have different rule/category mixes; mixed/unsupported groups and many rule-by-segment cells are small. The comparable ES dialect groups each have n=32, with SAR 12/32, 12/32 and 13/32. Portuguese has 35 must-escalate cases versus 25 Spanish cases despite its smaller workload, so headline automation is partly shaped by eligibility. These observations do not isolate a causal language/segment effect. No outcome-driven tuning was performed.

Spanish/mixed utterances are model-generated; PT was generated and cross-checked by different vendors before this session. Human dual labeling and fluent Portuguese review remain pending. No judge was run.
