# Final v4 results — after fixes, fresh suite; COMPLETE

**Official v4 result, completed 2026-10-01 UTC.** Evaluated release:
`1ec9c2f3a2307f8a5e26fcdc8fefd36ae48a019b`. Product behavior was frozen and
deployed at `92994d933e7e4d4cddbbf988fb4cc748d3cd5db1`; subsequent suite,
documentation and selection-interface integration preserved identical images.
This page renders the saved aggregates. The official JSON, Markdown, checkpoints,
frozen suite and private bindings remain unchanged.

Sources: ignored `artifacts/final-program-v4/results.json`, `results.md`,
`COMPLETE.json` and the durable budget receipt. Suite manifest SHA-256:
`309c3aa22c2eab51b3289075b733c52bb7934a879299762c3fb9ba16a3d9bec8`.
No customer utterance, organizer value, binding or model prose is reproduced.

The completed attempt ran from **04:52:04 to 05:19:04 UTC**, about 27 minutes,
without a resume: B1 100, P-Gemini 100 primary plus two extra passes on 30
preselected cases, **260 system runs**, and **60 paired judge items** covering
both systems on 30 independently preselected cases. Sonnet frontier was OFF;
Sonnet judge output was capped at 1024 tokens. B1 used deterministic rules and
templates; P used Gemini 3 Flash Preview plus Jev 1.13.0 risk-cue union, NLU
v5.1, phrase v2, policy 1.3.0 and MATCH v2. Exact hashes/routes are in the JSON.
Across all 160 P executions, the saved call events are 199 Gemini and 184 Jev,
all 383 marked valid, with no fallback model observed. The other 120 budgeted
calls are the two judges on 60 items.

Serving used the promoted **local** organizer identity/product/transaction
projection with forced customer RLS and a 120-day window. Suite identities came
from organizer data, while declared transaction/case/FX overlays were fictional
and project-generated. Each execution had fresh isolated in-memory operational
state; production Postgres durability was tested separately.

## Primary B1 versus P-Gemini

First pass only; repeats and judges do not enter these denominators. All 100
cases are in scope, and 47 are automation eligible. B1 executed 98; two fault
boundaries were not reached and remain failures in the workload denominator.
P executed 100. SAR requires correct terminal automation and all gold/safety
checks. Containment includes unsuccessful paths. Strict escalation requires
readback, fields, reason set and routing, rather than handoff presence alone.
Percent intervals below are Wilson 95%.

| Metric | B1 | P-Gemini |
| --- | ---: | ---: |
| Pass | 62/100 (62%) | 88/100 (88%) |
| SAR / in-scope (95% CI) | 22/100 (22%); 15.0–31.1% | 32/100 (32%); 23.7–41.7% |
| SAR / automation-eligible | 22/47 (46.8%) | 32/47 (68.1%) |
| Automation attempted | 41/100 (41%) | 51/100 (51%) |
| Containment | 41/100 (41%) | 47/100 (47%) |
| Strict escalation recall | 38/53 (71.7%) | 49/53 (92.5%) |
| Missed transfers | 15/53 (28.3%) | 4/53 (7.5%) |
| Unnecessary transfers | 11/47 (23.4%) | 2/47 (4.3%) |
| Materially incorrect outcome | 7/98 (7.1%) | 0/100 (0%) |

The paired P-minus-B1 **in-scope SAR difference is +10 percentage points,
95% interval +5 to +16**, using 10,000 paired case-bootstrap draws on all 100
cases. The stored McNemar exact two-sided **p=0.00390625 (approximately 0.004)**
is a different comparison: majority **pass** on the 30 repeated cases versus
B1, with nine P wins and zero B1 wins. It is not a full-100-case McNemar test or
a test of the primary SAR difference.

## Safety gates

**Both systems failed the full safety gate.** The counts below are official and
are not corrected by the subsequent [post-hoc analysis](final-v4-safety-analysis.md).
Categories overlap. Zero observed failures do not establish zero risk; Wilson
upper 95% bounds for a zero category are 3.77% at n=98 and 3.70% at n=100.

| Gate / observed category | B1 | P-Gemini |
| --- | ---: | ---: |
| Unauthorized disclosure | 0/98 (pass) | 0/100 (pass) |
| Unauthorized action | 2/98 (FAIL) | 2/100 (FAIL) |
| Missing confirmation or step-up | 0/98 (pass) | 0/100 (pass) |
| Reported without verification | 2/98 (FAIL) | 4/100 (FAIL) |
| Refund or credit promise | 0/98 (pass) | 0/100 (pass) |
| Fraud/regulator strict recall | 7/8 (FAIL) | 7/8 (FAIL) |
| Required readbacks | 66/80 (FAIL) | 77/80 (FAIL) |
| Required handoff fields | 48/48 (pass) | 51/51 (pass) |
| Policy violation | 5/98 | 6/100 |
| Grounding violation | 0/98 | 0/100 |
| Materially incorrect outcome | 7/98 | 0/100 |

The materially-incorrect predicate is a deterministic outcome/target/critical
handoff check, not an independent human fact judgment. Required readbacks
measure completion of gold-required references, including workflows that were
never performed; they are not a conditional verification rate for actual writes.
No production-readiness or zero-unsafe claim follows from the higher pass rate.

## ES/PT and segments

| System | Language | Pass | SAR / in-scope | Attempted | Containment | Strict escalation | Missed | Unnecessary |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B1 | ES | 28/48 | 10/48 | 19/48 | 18/48 | 17/25 | 8/25 | 7/23 |
| B1 | PT | 30/48 | 9/48 | 19/48 | 20/48 | 20/27 | 7/27 | 4/21 |
| B1 | Mixed | 4/4 | 3/4 | 3/4 | 3/4 | 1/1 | 0/1 | 0/3 |
| P-Gemini | ES | 43/48 | 16/48 | 25/48 | 23/48 | 23/25 | 2/25 | 1/23 |
| P-Gemini | PT | 41/48 | 13/48 | 23/48 | 21/48 | 25/27 | 2/27 | 1/21 |
| P-Gemini | Mixed | 4/4 | 3/4 | 3/4 | 3/4 | 1/1 | 0/1 | 0/3 |

| System | Segment | Pass | SAR / in-scope | Attempted | Containment | Strict escalation | Missed | Unnecessary |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B1 | Basic | 15/25 | 4/25 | 7/25 | 6/25 | 10/13 | 3/13 | 6/12 |
| B1 | Plus | 17/25 | 5/25 | 9/25 | 9/25 | 12/13 | 1/13 | 3/12 |
| B1 | Premium | 15/25 | 7/25 | 13/25 | 13/25 | 8/13 | 5/13 | 1/12 |
| B1 | Student | 15/25 | 6/25 | 12/25 | 13/25 | 8/14 | 6/14 | 1/11 |
| P-Gemini | Basic | 22/25 | 8/25 | 12/25 | 11/25 | 12/13 | 1/13 | 1/12 |
| P-Gemini | Plus | 21/25 | 7/25 | 12/25 | 11/25 | 13/13 | 0/13 | 1/12 |
| P-Gemini | Premium | 23/25 | 9/25 | 14/25 | 13/25 | 12/13 | 1/13 | 0/12 |
| P-Gemini | Student | 22/25 | 8/25 | 13/25 | 12/25 | 12/14 | 2/14 | 0/11 |

Full language/dialect/country/segment intervals, unsafe counts and rule/category
mixes are retained in the aggregate JSON. Mixed n=4 and segment n=25 estimates
are descriptive; unequal rule/category composition prevents causal fairness or
language claims.

## Repeats, machine judges and human review

Outcome, pass and SAR flips were each **0/30 preselected cases** across three
executions, with Wilson 95% interval **0–11.35%**. The denominator is 30, not
100: the latter was v2's repeated subset. Stable failures remain failures.

All 60 blinded conversation/system items have Sonnet and Jev ratings: zero
failed or unpaired items. Handoff usefulness applies to 31 of those items.

| Dimension | Exact agreement | Within one point | Quadratic weighted kappa |
| --- | ---: | ---: | ---: |
| Language/register | 34/60 (56.7%) | 59/60 (98.3%) | 0.159 |
| Clarity | 28/60 (46.7%) | 51/60 (85.0%) | 0.102 |
| Empathy | 21/60 (35.0%) | 58/60 (96.7%) | 0.179 |
| Handoff usefulness | 29/31 (93.5%) | 31/31 (100%) | 0.000 |

Machine agreement is not human validation. The blank 20-item owner sheet is
`artifacts/final-program-v4/human-judge-20.csv`, verified at mode 0600 and 20
records. Human scores, judge–human agreement and calibration remain pending.

## Cost and latency

| Measurement | B1 | P-Gemini |
| --- | ---: | ---: |
| Turn p50 / p95 | 0.007 / 0.021 s | 2.125 / 3.776 s |
| Case p50 / p95 | 0.010 / 0.037 s | 2.253 / 7.271 s |
| Primary-pass known model cost | $0 | $0.229766056 |
| Cost / evaluated workload case | $0 | $0.002297661 |
| Allocated primary cost / automation attempt | $0 | $0.004505217 (51 attempts) |
| Allocated primary cost / SAR-resolved case | $0 | $0.007180189 (32 resolutions) |

The JSON's `per_attempted_case_usd` field divides by all 100 evaluated cases.
The automation-attempt figure above instead allocates the same primary cost
over the 51 cases marked attempted. Neither figure includes repeats, judges or
infrastructure. Full latency and cost bootstrap intervals remain in the JSON.

Local serving removes workstation-to-Azure serving SQL hops; remote providers
and durable budget calls remain included. These are not Azure browser timings
and are not directly comparable infrastructure latencies to v2/v3. Deployed
in-region probes are reported separately in [the latency study](pre-v4-latency-components.md).

Durable scope **`final-evaluation-v4`**, run **`final-program-v4`**: **503 paid-call
attempts, $0.54532659 known and charged, zero unknown costs**, including system
repeats and both judges. The $3 lifetime cap held. Prior exposure of $7.016418
plus v4 gives **$7.56174459 cumulative charged exposure**, including retained
historical reserves, below $12. The launch's conservative full-cap calculation
was **$7.016418 + $3 + $0.10 + $0.10 = $10.216418 <= $12**. Infrastructure is
separate; the contemporaneous monthly estimate was $34.63 before tax.

## Full evaluation chronology and disclosures

1. **Earlier mock access:** the original 200-case release had B1/P-mock
   diagnostics before paid final evaluation, with saved-observation measurement
   corrections disclosed separately. The [access ledger](test-access-log.md)
   records this prior exposure; it was not a fresh real-model blind comparison.
2. **V1 abandoned:** the original paid final program was stopped at approximately
   six P cases after dev evidence showed 11/20 no-fault passes and eight unreached
   fault fixtures. Sebastian chose Option A, abandoning v1 rather than using its
   outcomes for tuning. Its directory remains untouched and its results were
   never inspected. The early progress spend was $0.0119; subsequent aggregate
   budget accounting found **$0.02058083 charged/reserved exposure**, including
   an unsettled reservation. The revised figure was carried forward without
   reading abandoned artifacts or forgiving reserves.
3. **Before v2:** fixes followed dev evidence: generic charge words were removed
   from the transaction-type slot; the simulator could choose a declared known
   target if actually offered, with explicit replies/refusals taking precedence;
   dispute/fault dev fixtures gained explicit denial/request semantics. Frozen
   bytes and MATCH thresholds were unchanged. The static frozen audit found all
   200 cases already had explicit choices, so none used the new implicit fallback.
   The accepted dev gate was 20/20 + 20/20 + 12/12, B1 32/32, zero unsafe out of
   52. Dev success did not predict held-out success.
4. **V2 complete:** release `fd34c7dce11cf9db6f71e84ae4fbb2ccc19de415` completed
   700 system runs and 150 judge items in about 2h20m. Primary pass was B1
   65/200, Gemini 63/200 and Sonnet frontier 37/100; all failed safety gates.
   Seven judge items failed; 143 pairs were valid. V2 spent $2.94519961 and
   remained the official result. Its time limit was extended to 3h30 with a
   15-minute stall watchdog; it completed without a restart or resume.
   The [post-hoc report](final-v2-error-analysis.md)
   disclosed workflow/gold/calendar conflicts and readback artifacts; the
   [separate slice correction](final-v2-slice-correction.md) fixed presentation
   of strict escalation from saved observations, without rerunning or changing
   the original official files. Human calibration remained incomplete.
   In particular, the forbidden age-boundary write was 84 days under the
   documented bank-date anchor while frozen gold used 85; many gold disputes
   expected filing from bare unfamiliarity despite the then-current CI label
   rule. Materially-incorrect flags included explanation-versus-gold mismatches;
   the readback gate mixed unmet expected workflows with verification, including
   one existing-case alias artifact. Original slice recall counted presence
   while missed transfers used strict correctness. These disclosures do not
   remove official failures or establish an improved v2 score.
5. **Before v3:** Sebastian adopted ADR-0015's explain→offer→dispute contract;
   implementation used dev and v2 post-hoc evidence. A newly frozen confirmation
   set stayed out of tuning. The accepted gate was 20/20 no-fault, blind 18/20,
   12/12 faults, zero unsafe out of 52. A separately approved post-gate blank-
   merchant baseline correction passed B1 32/32 and mock P 20/20 + 12/12 and
   was disclosed. The deterministic-fraud smoke assertion was corrected without
   changing behavior or making further paid calls; combined release smoke was
   $0.00802475. See [v3 release notes](v3-release-notes.md).
6. **V3 preflight attempts:** attempt 1 stopped on the missing `cancelled`
   scenario enum; attempt 2 stopped on the missing `offer_dispute` forbidden
   predicate. Each completed zero cases and spent $0. Both directories were
   preserved; owner-authorized evaluation-only repairs required new SHAs and
   identical-image release verification, without editing gold or product paths.
   After product freeze, a broad search accidentally exposed two v3 author-tool
   case-template snippets; a later search exposed three generic forbidden-action
   handling lines. No frozen rows, selection contents, binding values or results
   were exposed by those searches. Sebastian approved continuation with factual
   disclosure and frozen product behavior; explicit search exclusions followed.
7. **V3 paid attempt:** evaluated SHA `e12efc73be64f8355aa9f177f08a04337593616c`
   stopped on budget-DB connectivity at 212/260; one authorized resume completed
   all 260 system runs. Sonnet twice exhausted its 256-token judge cap on the
   next item; judging stopped at 28/60. Existing report code finalized primary
   aggregates as PARTIAL with no paid retry or code change. Official pass was
   B1 52/100, P 77/100; v3 cost $0.47321405, zero unknown costs. These
   [v3 results](final-v3-results.md) remain unchanged.
8. **After v3, before v4:** v3 was explicitly retired to dev data for fixes;
   the reported 100/100 P seen-v3 regression is not a held-out improvement.
   Orchestration, guards, NLG, kind aliases, OTP/simulator and live-rehearsal
   defects were corrected and disclosed. The model comparison stayed partial
   after quota failure; its prepared lean prompt was not adopted. A retired-v3
   mock [runner rehearsal](final-program-rehearsal.md) exercised SIGTERM/resume,
   DB failure, bounded judge failure and a $0 durable cap. It made no real calls
   and did not inspect v4. Independent v4 authoring used the written contract;
   behavioral and human/second-vendor language validation were not completed
   before freeze. Live rehearsal passed at frozen product 92994d9 before v4 GO.
9. **V4 attempt 1:** suite/docs integration reached
   `791e774a518292e0cc143d4d3bdb69f5056bf461`. Structural and identity/ownership
   preflight passed, then the legacy selection parser raised `KeyError` because
   v4 declares `case_ids`/`purpose`/`selection` rather than v3's
   `scenario_ids`/`method`/`n`. **Zero cases, zero paid attempts, $0.** The first
   outer nohup shell exited before Python entered; the corrected synchronous
   launcher created the actual detached attempt. An automatic approval review
   rejected a standalone selection-parser probe; it never executed. The author
   supplied field names/types only, with zero IDs. The stopped directory was
   preserved as `final-program-v4-attempt1`; product, prompt, config, frozen
   suite and binding contents were unchanged.
10. **V4 attempt 2, official complete attempt:** the owner authorized the
    eval-only validated dual-schema adapter, authored tests and a fresh-start
    exception under the SAME $3 lifetime scope. First recovery CI exposed an
    incomplete authored legacy fixture; its schema/count correction passed
    55 targeted and 791 full Python checks (22 optional DB skips). Exact final
    SHA 1ec9c2f passed CI/safety/access and identical-image verification; a fresh
    release receipt reused real/browser smoke on identical product 92994d9,
    without new paid calls. Fresh credits/key limits and local RLS serving
    passed. Attempt 2 completed all phases without a resume, watchdog stop,
    budget denial or unknown-cost attempt. Both v4 attempts are disclosed in
    the official header; the second attempt supplies every v4 number above.
11. **After v4:** the owner authorized this zero-spend documentation and
    read-only safety analysis. V4 now has post-hoc case inspection; any future
    fixes must be labeled **not reflected in v4 numbers**. No result, gold,
    model, prompt, product or deployed-release changes occurred in this analysis.

## Limitations

- V1 was abandoned; v2/v3/v4 used different suites, workloads and semantics.
  Later fixes used seen earlier evidence. Cross-version rates are historical
  descriptions, not paired or causal improvement estimates.
- ES/PT variants share authored interaction families. The saved ordinary case
  bootstrap does not cluster by family and may understate dependence. Segment
  n=25 and mixed n=4 do not establish population fairness or dialect quality.
- V4 wording and gold lack independent human validation; PT/dialect text was
  model-generated, and v4 second-vendor review remains pending. Fixture/reply
  contradictions and metric artifacts are disclosed in the separate analysis;
  official failures are retained without rescoring.
- Fictional overlays on scoped organizer identities do not establish performance
  on natural transaction narratives, real customer recollections or bank outcomes.
  Matcher ranking and NLU slot gold are absent from this suite; use separate dev
  reports for those metrics.
- Safety gates failed. Higher pass/SAR, zero materially-incorrect P flags and
  stable repeats do not establish safety, correctness on untested inputs or
  production readiness. Human judge calibration and PT review remain pending.
- Runtime operational state was isolated in memory; local serving latency excludes
  the Azure serving hop. Durable production, browser UX, infrastructure cost and
  cold starts have separate evidence and are not proven by this evaluation.
