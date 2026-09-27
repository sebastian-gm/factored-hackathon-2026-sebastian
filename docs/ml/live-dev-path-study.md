# Real-model development path and phrasing study

These are **synthetic, unreviewed dev** measurements from 2026-09-27. They do not open or score the frozen held-out suite. The runner uses the real P API/orchestrator/grounding code through the **local in-process ASGI stack**, with generated in-memory ledger fixtures and simulated OTP. It excludes container, deployed network, and production database overhead. Calls use `google/gemini-3-flash-preview` for NLU/eligible phrasing, parallel `jev-1.13.0` risk `Noul` questions, `x-ai/grok-4.20` only on a forced primary failure, and `anthropic/claude-sonnet-5` plus Jev for subjective-only wording scores. NLU v4, phrase v1, and judge v1 are unchanged. Production remains configured for mock unless the lead enables a real route.

## Live P-path latency, 20 conversations

The fixed sample is the 20 no-fault cases in `evals/dev_scenarios_v2.yaml` (10 ES, 10 pt-BR). One case injected two **no-network** Gemini failures to exercise the configured fallback route; Grok then made one valid real call. The 20 conversations produced 39 measured API turns, 20 valid Gemini NLU calls, five valid Gemini phrase calls, 21 valid parallel Jev risk calls, and one valid Grok fallback call. The two injected failures are recorded as unknown-cost attempts for conservative budget accounting but were not sent to OpenRouter.

| Measure | Result |
|---|---:|
| End-to-end API turn p50 / p95 | 1.782 / 4.354 s |
| Sum of turns per conversation p50 / p95 | 2.002 / 8.126 s |
| Known provider cost, all 20 | $0.032765 |
| Known provider cost per conversation, mean / p50 / p95 | $0.001638 / $0.001421 / $0.002770 |
| Conservative budget charged, including injected-failure reserves | $0.052947 of $0.50 cap |
| Dev scenario objective pass | 11/20; this was a latency exercise, not a held-out quality estimate |

The per-turn figures include real model waits, Jev parallelism, local policy/matcher work, and local API time. Case latency sums system turns and excludes synthetic customer think time. The p95 values are descriptive order statistics on only 20 cases; no confidence interval or production SLA claim is implied. The failure-only Grok route was exercised once, not assigned a production fallback-rate estimate.

## Phrasing ablation, 30 assessable dev conversations

The first pass attempted 30 existing dev scenarios. Eight fault-injection fixtures did not reach their scripted trigger on the real P path, so they produced no assessable final reply. We then added eight explicitly labeled synthetic paraphrases of no-fault fixture conversations, within the **same** ablation budget. This yielded **30 paired final replies from 38 attempted conversation runs**. The eight additions were chosen after seeing the fixture misses; this is an exploratory wording comparison, not a preregistered quality estimate. It does not use held-out data.

For each assessable conversation, the P NLU and response plan were held fixed. The template arm uses the delivered deterministic reply. The LLM arm calls the existing `build_reply` plus grounding verifier only for `clarify` or `explain_status`; on verifier failure it retains the approved template. Compliance-critical responses remain templates. Sonnet and Jev each scored clarity and empathy on the same blinded synthetic message/reply. Identical replies reused their template score, avoiding duplicate paid judging. Neither judge scored objective correctness.

| Measure | Template only | LLM phrase + verifier |
|---|---:|---:|
| Paired conversations scored by each judge | 30 | 30, including 26 identical-template fallbacks/noneligible replies |
| Replies actually changed | — | 4/30 |
| Grounding-violation catches on these live drafts | — | 0/4 eligible phrase calls |
| Product-call known cost per conversation, mean | $0.001371 | $0.001430 (includes $0.000058 mean marginal phrasing) |
| Case latency p50 / p95 | 1.900 / 4.096 s | 1.927 / 4.472 s **proxy** (template case plus measured phrase-call time) |
| Sonnet clarity mean, 1–5 | 3.133 | 3.167 |
| Sonnet empathy mean, 1–5 | 2.733 | 2.800 |
| Jev clarity mean, 1–5 | 3.400 | 3.433 |
| Jev empathy mean, 1–5 | 2.833 | 3.033 |

The four phrase calls added **$0.001744** known cost and 1.628/1.970-second p50/p95 provider latency; across 30 conversations they added 0.227 seconds of call time per case on average. The template arm has no extra provider call after the shared P path. The LLM case-latency row is a **constructed proxy**, since the phrase calls ran after the template conversation rather than as a second end-to-end API run. No live draft tripped the grounding verifier; existing offline verifier tests cover prohibited numbers, dates, identifiers, status claims, and promises. Zero catches in four calls does not establish a zero violation rate.

Only the four changed replies can identify a wording effect: Sonnet mean paired change was **+0.25 clarity / +0.50 empathy**, and Jev was **+0.25 clarity / +1.50 empathy**, on integer 1–5 scores. The full-sample means are diluted by 26 identical replies. The 30 paired conversations used **$0.041142** in shared P NLU/risk calls, **$0.001744** in phrase calls, and **$0.112225** in unique Sonnet/Jev judge calls. Eight unassessable fault-fixture attempts added other cost; total known and charged spend for all 38 runs was **$0.166451**, below the separate **$0.50** cap. All cost figures come from per-call usage/cost fields; no key-level balance delta is allocated to cases. Detailed synthetic cases and judge scores stay only in ignored `artifacts/`.

The small changed-reply count and authored workload do not justify changing the selected model, the phrasing policy, or the final evaluation. The observed 11/20 objective pass in the latency slice and fault-trigger misses warrant separate acceptance analysis; subjective judge scores cannot excuse those failures.
