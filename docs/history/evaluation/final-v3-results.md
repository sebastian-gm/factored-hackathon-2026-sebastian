# Final v3 results — after fixes, fresh suite; partial judging

**V2 remains the official prior result.** V3 is a separate independent 100-case evaluation after the v2-informed fixes, not a revision of v2. These are the saved v3 primary results at `e12efc73be64f8355aa9f177f08a04337593616c`. They predate PR #62 and its post-v3 fixes.

All **260 system runs** were checkpointed: B1 100, P-Gemini 100 primary plus two additional passes on 30 preselected cases. Sonnet frontier was **OFF**. Judging stopped at **28/60 paired conversation/system items**; the whole program is **PARTIAL**, not COMPLETE. The saved primary metrics do not depend on judge completion.

Source: ignored `artifacts/final-program-v3/results.json`, `results.md` and `PARTIAL.json`. No case or customer rows are reproduced here. Suite manifest SHA-256: `ecf3f6313f33359fed892de1b3537edc4ae8e854dd5bfa8da1fc8845daa41177`. Models: Gemini 3 Flash via OpenRouter, Jev 1.13.0 risk union; judges Sonnet via OpenRouter and Jev via TypeSafe. Organizer serving ledger uses a 120-day window, forced customer RLS and declared counterfactual overlays; operational state is isolated in memory per case.

## Primary results

Counts include all 100 workload cases. B1 executed 96; four fault fixtures did not reach their trigger and remain failures. P executed all 100. SAR measures successful automation; containment alone can include unsuccessful outcomes. Strict escalation requires the correct handoff, readback, reasons, required fields and routing. Percent intervals below are Wilson 95%.

| Metric | B1 | P-Gemini |
|---|---:|---:|
| Pass | 52/100 (52%) | 77/100 (77%) |
| SAR / in-scope (95% CI) | 28/100 (28.0%); 20.1–37.5% | 39/100 (39.0%); 30.0–48.8% |
| SAR / automation-eligible (95% CI) | 28/60 (46.7%); 34.6–59.1% | 39/60 (65.0%); 52.4–75.8% |
| Containment (95% CI) | 38/100 (38.0%); 29.1–47.8% | 49/100 (49.0%); 39.4–58.7% |
| Strict escalation recall (95% CI) | 20/40 (50.0%); 35.2–64.8% | 30/40 (75.0%); 59.8–85.8% |
| Missed transfers (95% CI) | 20/40 (50.0%); 35.2–64.8% | 10/40 (25.0%); 14.2–40.2% |
| Unnecessary transfers (95% CI) | 23/60 (38.3%); 27.1–51.0% | 11/60 (18.3%); 10.6–29.9% |

The paired P-minus-B1 **in-scope SAR difference is +11 percentage points (95% CI +5 to +17)**, from 10,000 paired bootstrap draws. This compares the systems on the same v3 cases; it is not a paired comparison with v2. Different suites and changed policy/gold semantics prevent a causal v2-to-v3 improvement claim.

## Safety and readbacks

**Both systems failed the full safety gate.** Zero observed critical unsafe events do not prove zero risk. Their per-category Wilson 95% upper bounds are 3.85% for B1 (n=96) and 3.70% for P (n=100). Categories overlap.

| Gate / observed category | B1 | P-Gemini |
|---|---:|---:|
| unauthorized_disclosure | 0/96 | 0/100 |
| unauthorized_action | 0/96 | 0/100 |
| missing_confirmation_or_step_up | 0/96 | 0/100 |
| reported_not_verified | 0/96 | 0/100 |
| refund_or_credit_promise | 0/96 | 0/100 |
| fraud_regulator_recall | 1/5 (FAIL) | 2/5 (FAIL) |
| required_readbacks | 58/74 (FAIL) | 67/74 (FAIL) |
| required_handoff_fields | 39/39 (pass) | 40/40 (pass) |
| materially_incorrect_outcome | 2/96 (2.1%) | 0/100 (0.0%) |
| grounding_violation | 0/96 (0.0%) | 0/100 (0.0%) |
| policy_violation | 0/96 (0.0%) | 0/100 (0.0%) |

## ES and PT

| System | Language | Pass | SAR / in-scope (95% CI) | Containment | Strict escalation | Missed | Unnecessary |
|---|---|---:|---|---:|---:|---:|---:|
| B1 | es | 22/48 | 11/48 (22.9%); 13.3–36.5% | 16/48 (33.3%) | 10/20 (50.0%) | 10/20 (50.0%) | 12/28 (42.9%) |
| B1 | pt | 27/48 | 15/48 (31.2%); 19.9–45.3% | 19/48 (39.6%) | 10/19 (52.6%) | 9/19 (47.4%) | 11/29 (37.9%) |
| B1 | mixed | 3/4 | 2/4 (50.0%); 15.0–85.0% | 3/4 (75.0%) | 0/1 (0.0%) | 1/1 (100.0%) | 0/3 (0.0%) |
| P-Gemini | es | 38/48 | 18/48 (37.5%); 25.2–51.6% | 23/48 (47.9%) | 16/20 (80.0%) | 4/20 (20.0%) | 5/28 (17.9%) |
| P-Gemini | pt | 35/48 | 19/48 (39.6%); 27.0–53.7% | 23/48 (47.9%) | 13/19 (68.4%) | 6/19 (31.6%) | 6/29 (20.7%) |
| P-Gemini | mixed | 4/4 | 2/4 (50.0%); 15.0–85.0% | 3/4 (75.0%) | 1/1 (100.0%) | 0/1 (0.0%) | 0/3 (0.0%) |

There are 48 ES, 48 PT and four mixed cases. Mixed-language estimates are descriptive only. No fluent-human PT review has been completed; PT and dialect wording was model-generated and reviewed by models. Full dialect, country and segment intervals and policy mixes remain in the aggregate artifact; small cells do not support population fairness claims.

## Repeats and judges

On the 30 preselected P-Gemini cases, outcome, success and SAR flip rates are each **0/30**, with Wilson 95% interval **0–11.35%**. Repeats are correlated, and stable failures are still failures.

Sonnet twice hit the **256-output-token length cap** on the next judge item, without a validated score; Jev was not reached for that item. No further paid retry was made. Agreement below describes only the 28 completed pairs (17 applicable handoffs), not all 60 planned items. Missing items may be systematic, so this is not a representative complete judge result.

| Dimension | Paired n | Exact agreement | Within one point | Weighted kappa |
|---|---:|---:|---:|---:|
| language_register | 28 | 42.9% | 100.0% | 0.051 |
| clarity | 28 | 39.3% | 96.4% | 0.315 |
| empathy | 28 | 35.7% | 85.7% | -0.027 |
| handoff_usefulness | 17 | 100.0% | 100.0% | Undefined (no variance) |

The owner review sheet is `artifacts/final-program-v3/human-judge-20.csv`. Its 20 items have not been human-scored. There was no v3 calibration workload, and no human agreement claim is made. Judge dimension intervals are in the saved aggregate artifact.

## Latency and cost

| Measurement | B1 | P-Gemini |
|---|---:|---:|
| Turn p50 / p95 | 1.999 / 4.038 s | 4.118 / 7.878 s |
| Case p50 / p95 | 3.023 / 5.921 s | 7.432 / 13.704 s |
| Primary-pass model cost | $0 | $0.237687544 |
| Model cost / workload case | $0 | $0.00237687544 |

Serving reads went from the workstation to **Azure Postgres**, so these latencies include that network hop; they are not measurements of an in-region Azure UI/API deployment or of the later request-cache optimization. Case-bootstrap intervals are retained in the aggregate. Interrupted attempts are retained in spend but not in completed-execution latency percentiles.

Durable v3 scope `final-evaluation-v3` / run `final-program-v3`: **$0.47321405 / $3**, 484 reservations and **zero unknown costs**, including repeats, partial judges and their failed attempts. Prior scopes plus v3 charged **$3.82358962**; including the earlier **$0.00802475** release smoke, the total at v3 stop was **$3.83161437 / $12**. Subsequent development spend is separate and does not change this run total. Infrastructure is excluded.

## Disclosures and current use

- V2-informed orchestration, policy/contract, harness and NLU fixes preceded the independently authored v3 suite. V2 remains unchanged and official; see [the v2 report](final-v2-error-analysis.md) and [the disclosed slice correction](final-v2-slice-correction.md).
- The accepted pre-v3 dev gate was 20/20 no-fault, 18/20 blind confirmation, 12/12 faults, zero unsafe/forbidden out of 52. The separately approved blank-merchant baseline correction passed authored regressions, B1 32/32 and mock P 20/20 + 12/12; it was disclosed before v3. This does not count as a blind confirmation rerun.
- **Two authoring-tool case-template snippets** were accidentally exposed by a broad search after the product had already frozen and deployed at `9f0bff0`. A later search exposed three generic forbidden-action handling lines. No frozen rows, selections, bindings or results were opened by those searches. Sebastian approved continuing with disclosure and a product-path freeze; [the release notes](v3-release-notes.md) preserve the timing and restrictions.
- Two startup attempts stopped before calls or completed cases, each at **$0**. The `cancelled` enum and `offer_dispute` observation predicate were repaired in evaluation contracts/code only. Product images stayed identical through evaluated SHA `e12efc7`. These repairs did not alter suite bytes or product behavior.
- The paid attempt stopped first on a budget-DB connectivity error at 212/260 published checkpoints. One authorized resume completed all system runs, then stopped during judging. Existing report code produced aggregates with no calls or tracked change; `PARTIAL.json` exists and `COMPLETE.json` does not. Historical artifacts were preserved; abandoned v1 was not accessed.
- **V3 is now retired to development data**, after owner-authorized post-hoc analysis. The orchestrator reports P 100/100 after PR #62 fixes on these now-seen cases. That is a regression check on seen data, **not** a new evaluation result; it does not replace 77/100 here. [Post-v3 development analysis](post-v3-fixes.md) describes that work. A new independent v4 is pending; this page neither opens nor runs it.
