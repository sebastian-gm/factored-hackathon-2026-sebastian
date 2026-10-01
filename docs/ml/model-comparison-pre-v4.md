# Development model comparison: partial results and budget stop

**2026-09-30 PDT / 2026-10-01 UTC. Paid work stopped; no rerun.** Thirty of the
planned fifty pairs completed. Gemini and the Sol route both passed **25/30**,
with the same five failed conversations. This is a partial integration replay,
not a fair model-equivalence or replacement result: Sol inherited the serving
route's short first timeout, had unresolved provider failures, and used Grok
fallback in six completed conversations. **Gemini remains the default.**
Only the five approved dev sets were used; held-out v4 was never accessed.

## Budget readback and failure diagnosis

Every request, retry, fallback and Jev call reserved against
`dev-gate/model-compare` / `model-compare`, **$1.50 lifetime**. Postgres readback
at **00:41:56 UTC** after the stop:

| Accounting quantity | USD |
|---|---:|
| Returned per-call costs, rounded by Postgres | $0.20973001 |
| Retained reserves for 31 unknown-cost attempts | $1.28198000 |
| Charged exposure including those reserves | $1.49171001 |
| Remaining below the $1.50 cap | $0.00828999 |
| All scopes' charged exposure at readback | $7.04653079 |

The unrounded journal sum is $0.209729548; the difference is per-call money
rounding. Reserves are **not billed-cost estimates**. No key/account delta was
used, no reserve was released, and no unknown bill was set to zero. A fair
restart cannot fit the remaining scope; paid work stops here. The separate
pre-v4 scope remains at $0.87148777 exposure against its $0.90 stop, with only
$0.02851223 left. It cannot fund the remaining round-two follow-up or complete
240-case-per-prompt latency study; see [round-two evidence](nlu-robustness-round2.md).

There were **239 attempts**: Gemini 61 valid, Sol 49 valid + 31 provider errors,
Grok 8 valid, Jev 90 valid. All unknown bills belong to Sol, across 17 attempted
conversations (15 ES attempts / 16 PT attempts). They returned in
**0.409–4.033 s**; 29/31 returned before 0.7 s. All have the saved diagnostic
`model_failure`, with no generation ID, usage or error-envelope code. None is
identified as a timeout. Their cause cannot be recovered from the journal:
provider routing, capacity, schema rejection and server-side deadlines remain
unverified explanations. A longer timeout alone is not a demonstrated fix.

Both original candidate specs inherited **6 s first attempt / 20 s subsequent**
and a 45 s logical-call budget. That was inappropriate for an ability comparison
with a reasoning model and is withdrawn as the future protocol. `urlopen`'s
timeout is a socket/read setting, not a strict elapsed-time deadline: one valid
Sol first attempt took 6.827 s. Recorded failures are latency observations, never
zero-duration parses or semantic errors.

Zero-cost corrections now prepare **both candidates at 30 s per attempt**, no
shortened first attempt, and a 65 s logical-call budget. Production's 6/20 s
settings stay unchanged. The comparison stops on its **first unknown-cost
response**, before another retry/fallback/conversation, while retaining that
reserve and settling the parallel Jev result. Settlement occurs before callbacks
that can stop execution. HTTP and HTTP-200 envelope codes 401/402/403/429
also stop even with known zero/positive billing (credentials, credits, forbidden
budget/entitlement, quota/rate limits). Timeout codes/durations, generic failures, and first
attempts exceeding the serving 6 s are reported separately. No paid measurement
has used this corrected protocol, and its changed pins prohibit resuming the old
run under new settings.

The adapter now handles HTTP-200 error envelopes separately from normal output:
it keeps only numeric error category, normalized usage/cost and generation ID,
discarding provider prose, raw bodies and reasoning. Missing/malformed choices
also preserve valid returned billing. This closes a diagnostics/reconciliation
gap; it cannot retrospectively recover discarded metadata. OpenRouter documents
[errors after HTTP 200 and possible charges without content](https://openrouter.ai/docs/api_reference/errors-and-debugging).

## Completed paired results

Execution head: `60f3bfa982ff547e4d1dbd74d6500bbe790d976c`. Same NLU **v5.1**,
phrase **v2**, orchestration, scorer, Jev risk union and failure-only Grok fallback.
Six paired cases per dev set, three ES/three PT per set: **15 ES / 15 PT**.
Gemini completed one additional unpaired case; Sol's matching case was interrupted
by the reservation guard. It is excluded from quality, included in attempted cost.

| Exact candidate model ID | ZDR provider | Input / output per 1M | Objective pass, Wilson 95% | Opening-slot F1, bootstrap 95% | Grok fallback, completed cases |
|---|---|---:|---|---|---|
| `google/gemini-3-flash-preview` | `google-vertex/global` | $0.50 / $3.00 | 25/30, 83.3% [66.4–92.7] | 97.64% [93.81–100] | 0/30 |
| `openai/gpt-6.1-sol` | `azure` | $2.00 / $10.00 | 25/30, 83.3% [66.4–92.7] | 99.21% [97.03–100] | 6/30 |

Sol uses supported `low` reasoning effort and `max_completion_tokens: 2048`;
Gemini uses `max_tokens: 2048`. Returned model IDs match the candidate IDs.
Grok is `x-ai/grok-4.20`; its eight calls cost $0.0188027, already included below.
The Sol arm therefore measures a **Sol/Jev/Grok route**, not pure Sol performance.

| Objective metric | Gemini route | Sol route | Wilson 95% for either route |
|---|---:|---:|---|
| In-scope safe automated resolution (SAR) | 19/28, 67.9% | 19/28, 67.9% | 49.3–82.1% |
| Eligible SAR | 19/25, 76.0% | 19/25, 76.0% | 56.6–88.5% |
| Strict escalation recall | 3/3 | 3/3 | 43.9–100% |
| Unnecessary transfers | 5/27 | 5/27 | 8.2–36.7% |
| Each of the eight unsafe classes | 0/30 | 0/30 | 0–11.4% |
| Confident opposite-language reply cases | 0/30 | 0/30 | 0–11.4% |

All five failures are in round two: `ar.case-and-charge`, `br1.detail-correction`,
`br2.code-switch`, `br3.polite-refusal`, `cl.emotion` (each prefixed `round2.`).
Both arms pass **1/6 round-two cases** and 6/6 from each other set. The
[owner-grouped round-two diagnosis](nlu-robustness-round2.md) still applies;
changing model did not resolve these shared flow/action failures. Zero observed
unsafe cases in this small sample is not a safety certification.

| Language | Candidate | Pass, Wilson 95% | In-scope SAR | Strict escalation | Unnecessary transfer | Slot F1, bootstrap 95% |
|---|---|---|---|---|---|---|
| ES | Gemini | 13/15, 86.7% [62.1–96.3] | 9/14 | 2/2 | 2/13 | 100% [100–100] |
| ES | Sol | 13/15, 86.7% [62.1–96.3] | 9/14 | 2/2 | 2/13 | 100% [100–100] |
| PT | Gemini | 12/15, 80.0% [54.8–93.0] | 10/14 | 1/1 | 3/14 | 95.89% [89.28–100] |
| PT | Sol | 12/15, 80.0% [54.8–93.0] | 10/14 | 1/1 | 3/14 | 98.63% [94.11–100] |

Opposite-language errors are a conservative lexical proxy, not fluent human
review. Replies with uncertain language evidence: Gemini 16 (ES 13 / PT 3), Sol
17 (ES 13 / PT 4). Both have 0/15 confident error cases in each language, Wilson
upper bound 20.4%. The degenerate ES slot bootstrap reflects no observed errors,
not certainty about unseen cases. Synthetic families and reused dev data limit
all interval interpretations; this is not held-out evidence.

## Latency and cost over all attempts

| Candidate | NLU attempt p50 / p95 | Paired turn p50 / p95 | Paired conversation p50 / p95 | Known cost / attempted conversation | Unknown bills |
|---|---|---|---|---:|---:|
| Gemini | 1.922 / 2.650 s | 3.558 / 6.574 s | 5.403 / 14.784 s | $0.003075 (31 attempted; $0.095315656 total) | 0 |
| Sol | 2.317 / 4.432 s | 4.395 / 10.870 s | 6.424 / 27.307 s | ≥$0.003691 (31 attempted; $0.114413892 known) | 31 |

NLU attempts include failures and Grok fallback; case/turn times are local real-P
replay, not deployed in-region latency. Case-cluster bootstrap 95% for paired
conversation p50/p95: Gemini **3.832–7.328 / 10.086–20.176 s**; Sol
**5.587–10.700 / 14.121–33.651 s**. Retry-inclusive serial NLU/phrase request
p50/p95 is **1.864/2.430 s** Gemini and **2.914/5.320 s** Sol. Sol has 22 logical
requests with retry/fallback; Gemini has none. Sol's unresolved costs prevent a
complete cost comparison, even though its returned-cost lower bound is higher.

| Language | Candidate | NLU attempt p50 / p95 | Paired conversation p50 / p95 | Known cost / attempted case | Unknown bills |
|---|---|---|---|---:|---:|
| ES | Gemini | 1.829 / 2.416 s | 6.256 / 14.321 s | $0.002934 (16 attempted) | 0 |
| ES | Sol | 2.384 / 4.348 s | 7.679 / 20.222 s | ≥$0.003906 (16 attempted) | 15 |
| PT | Gemini | 1.971 / 2.961 s | 4.856 / 16.420 s | $0.003225 (15 attempted) | 0 |
| PT | Sol | 2.312 / 4.489 s | 5.978 / 25.191 s | ≥$0.003461 (15 attempted) | 16 |

Schema-valid final responses over **all OpenRouter attempts**, including failures
and the interrupted case: Gemini **61/61 (100%, Wilson 94.1–100)**; Sol route
**57/88 (64.8%, 54.4–73.9)**, including eight Grok successes. Primary Sol alone
is 49/80 (61.25%). Jev is valid 90/90. This is schema-valid response availability;
provider errors are not evidence of syntactically invalid model JSON.
No concurrent hedge was run or adopted; the
[3–4 s retry replay](nlu-robustness-round2.md#sequential-retries-and-the-hedge-question)
remains a timing-only counterfactual with unmeasured duplicate billing.

## Frozen protocol, provenance and access

The owner approved a balanced sample under $1.50 instead of full 240-case pairs.
[Manifest](../../src/aclara/llm/dev_model_compare_50.manifest.json): fifty planned
pairs, ten per set, five ES/five PT each, selected using metadata-only stable
ordering and dialect/category buckets, never saved outcomes. SHA-256:
`40ef32671ff05617dc3246db38891a756b6d200cec48c368cc6e2483416b634c`.
Full pool/per-case/code/prompt/scorer/binding hashes were checked. The incomplete
prefix is balanced but not the whole sample or original 240-case mix.

[Opening-slot annotations](../../src/aclara/llm/dev_model_compare_slots.json) were
authored by **Codex, not a human reviewer**, and frozen before paid calls. The
immutable JSON's `method` mistakenly says `Human-authored`; this provenance
correction does not change annotations or their SHA-256:
`2d63ee91e925b2f2a0df75801813b571ab23c23575ca56d78fb1c99c98d3b8c1`.
Forty-eight single-target openings score amount/currency/date bounds/merchant;
two multi-target openings are excluded from slot F1 only. Twenty-nine of the
thirty completed pairs are slot-scored. Wrong values count FP+FN; null/null is
not TP; unreached/invalid extraction misses populated slots. This is opening F1,
not reactive-turn F1. Bootstrap resamples conversations, 2,000 draws, seed 61;
it does not correct correlated synthetic families or lack of human validation.

Fresh preflight at 00:10 UTC and paid launch verified the
[ZDR endpoint list](https://openrouter.ai/api/v1/endpoints/zdr), provider pins,
schema/token parameter support and price ceilings. Sol's cheaper `openai/flex`
route was absent from ZDR and excluded. Both arms enforce `zdr: true`,
`data_collection: deny`, strict schemas and no provider spillover. Sol's effort
support follows [official model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol).
Reasoning is never saved. Gemini 4 Argon was skipped per owner instruction.

No OpenAI Decisions access was established: authenticated Decisions model list
had nine entries, none `openai/*`; no direct OpenAI credential/SDK or confirmed
preview endpoint. OpenRouter's third-party Decisions API is not an OpenAI model.
Jev-versus-Decisions recall/precision/ECE/latency/cost remain unmeasured; no paid
probe or replacement was made. See the
[OpenRouter Jev example](https://openrouter.ai/blog/insights/what-is-jev/).

Private immutable evidence: `artifacts/dev-model-compare/paired/{launch.json,
calls.jsonl,summary.json}`, plus `stopped-analysis.json` and
`stopped-scope-readback.json`. Call journal SHA-256:
`7a48ddd933ab5ac310157584afdf6fe8131a54272a849d394bcf8b22a579bac4`.
No customer rows, secrets, prose errors or reasoning are published here.
The [paired driver](../../src/aclara/llm/dev_model_compare.py) has resume/pin and
unknown-cost protections; **do not rerun it under this exhausted scope**.
Local verification: 318 mock/unit/API checks passed with eight disposable-DB
skips; final focused provider/comparison rerun 28 passed, including concurrent
Jev settlement. Ruff, format, strict mypy and interface snapshots passed. All
100 corrected mock case-runs completed at $0; original paid artifact hashes match.
The separate v5.2 full-dev adoption gate remains unmeasured/unadopted.
Recommendation: keep the existing Gemini default; no model-choice conclusion
from this partial, fallback-contaminated comparison. Disparity evidence is in
[PR #86](https://github.com/sebastian-gm/bank-agent-lab/pull/86), green and awaiting
the lead's merge. No v4 or final run by this lane.
