# OpenRouter NLU comparisons and error analysis

**Sebastian selected `google/gemini-3-flash-preview` as the NLU and phrasing default.** The selected route is configured in `config/models.yaml`; production remains `LLM_PROVIDER=mock` until the lead enables it with a production key. The persistent `.env` approval flag was not changed. Sebastian approved a **$5 cumulative cap** for round one and a **$10 cumulative cap** for rounds two and three. Round one cost **$0.402383** from this lane's per-call response usage/cost fields, including the original probes. Later spend and results are reported below. Sebastian subsequently selected `x-ai/grok-4.20` as the failure-only cross-vendor fallback; mock production remains unchanged.

## Sebastian's 2026-09-27 label decision

“No reconozco esta compra” and “não reconheço essa compra” without an explicit denial or filing request mean **`charge_inquiry`**: explain the charge first, then offer a dispute. **`dispute_charge`** requires an explicit denial (“yo no hice”, “no fui yo”, “no autoricé”, and Portuguese equivalents) or an explicit request to file. `charge_inquiry` ↔ `dispute_charge` predictions are **intent errors**; they are not unsafe outcomes when the authorized, read-back end state is correct. This rule is applied to the opening utterance, independent of a later confirmation or filed case.

The derived labels for ten existing 32-case scenarios changed to `charge_inquiry`: `es.normal.dispute`, `pt.normal.dispute`, `es.ambiguous.amount.pesos`, `pt.ambiguous.amount.reais`, `es.ambiguous.amount.dollars`, `pt.ambiguous.amount.dollars`, `es.ambiguous.amount.comma`, `es.ambiguous.vague.charge`, `pt.ambiguous.vague.charge`, and `es.ambiguous.vague.payment`. `es.ambiguous.vague.purchase` (“No hice esta compra”) and `pt.ambiguous.vague.purchase` (“Não fiz essa compra”) remain `dispute_charge`. The source scenario file has no NLU intent field; the correction is in the AI lane's explicit `round_one._intent` mapping. The end-to-end expected outcomes are separate labels and were not rewritten.

Regrading the four stored v2 model predictions against these **current** labels gives **22/32 intent accuracy for each model**, down from the historical 32/32 shown below. There was no new paid 32-case run, and that regrade is not a v3 prompt result. The B1 rules classifier remains frozen to preserve the existing lead-owned explain/dispute workflow and its read-back tests; the P-system fallback and v3 prompt apply Sebastian's NLU rule. The lead workflow needs an explain-then-offer transition before B1 can use the new label without changing its end state.

The same **32 team-generated dev scenarios** from `evals/dev_scenarios.yaml` were sent to every model. The suite hash was `1078d9d591a4521281b8813fd303c8e5867030aefc46c8671f5f83eed0175676`. **The suite was unreviewed at the time of round one; Sebastian has since resolved the inquiry/dispute boundary below.** Scenario IDs and expected outcomes supplied intent labels; only amount, currency, and merchant expression were scored as slots. The scenarios do not specify a country, so none was inferred. This is the current Layer 1 dev suite, not the planned 150-case human-reviewed NLU set. ES/PT quality ratings remain unreviewed and are not estimated from model prose.

On 2026-09-26, IDs and rates were checked against [OpenRouter's live model catalog](https://openrouter.ai/docs/api/api-reference/models/get-models), filtered for `response_format` support and zero-data-retention endpoints. Batch routes and task-specific coding models were excluded. The order uses the planned 2,500 input / 300 output token mix; a different mix or provider route can change which ID is cheapest. All five requests required schema-capable, zero-retention routing.

| Family | Exact OpenRouter model ID | Catalog input / output, USD per 1M | Cases | Intent accuracy | Slot F1 | Valid JSON / all attempts¹ | ES / PT quality | p50 / p95 latency | Response cost / case² |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| DeepSeek | [deepseek/deepseek-v4-flash-0731](https://openrouter.ai/deepseek/deepseek-v4-flash-0731) | $0.0215 / $0.30 | 32 | 62.5% | 83.9% | Not retained per model | Pending / pending | 15.84 / 71.27 s | $0.000440 |
| Qwen | [qwen/qwen3.5-9b](https://openrouter.ai/qwen/qwen3.5-9b) | $0.10 / $0.15 | 32 | 25.0% | 48.0% | Not retained per model | Pending / pending | 20.59 / 171.43 s | $0.000453 |
| Gemini Flash-Lite | [google/gemini-2.5-flash-lite](https://openrouter.ai/google/gemini-2.5-flash-lite) | $0.10 / $0.40 | 32 | 62.5% | 100.0% | Not retained per model | Pending / pending | 1.03 / 1.49 s | $0.000098 |
| Gemini Flash | [google/gemini-3-flash-preview](https://openrouter.ai/google/gemini-3-flash-preview) | $0.25 / $1.50 | 32 | 65.6% | 100.0% | Not retained per model | Pending / pending | 1.86 / 2.35 s | $0.001048 |
| Grok | [x-ai/grok-4.3](https://openrouter.ai/x-ai/grok-4.3) | $1.25 / $2.50 | 32 | 68.8% | 100.0% | Not retained per model | Pending / pending | 4.71 / 6.66 s | $0.002203 |

¹ The original report's 100% figure used the **wrong denominator**: it excluded attempts stopped before parsing. The correct original-run rate is **130/200 = 65.0% valid JSON over all attempts**. There were 70 attempts in the adapter's combined refusal/truncation bucket, zero invalid-JSON or provider-error attempts, and 30 of 160 cases without a valid final response. The original aggregate lacks per-model attempt counts, so original-run all-attempt validity **cannot be recovered per model**. The diagnostic repeat below supplies separate, clearly labeled per-model counts. Failed cases count as incorrect intent and missed gold slots; no deterministic fallback received model accuracy credit.

² Cost per case sums per-call OpenRouter response usage/cost, including retries, divided by 32. The original full run reported $0.135728, and its five probes another $0.004537. The $0.599102 gap between those calls and the concurrent **key-level usage** increase is consistent with the data/ML lane's Portuguese generation on the same key, but has not been independently reconciled per generation. It is **not assigned to a model** and is no longer used for cost per case or the cap check. The ignored local run records are under `artifacts/ai-round-one/`; no customer messages or model thinking are in the report.

The round-one comparison is historical and directional because labels were inferred from the baseline scenario suite, the sample is small, and no independent human ES/PT ratings or final test were run. Claude Haiku, Sonnet, and Opus are included in round two below. Review the annotation set before selecting a production default.

## Revised prompt: four-model rerun

Prompt `prompts/nlu/v2.md` defines every intent, including the distinction between asking about a charge and denying a purchase, and separates bank-fee objections from merchant disputes. All four models used a 2,048-token requested output limit. DeepSeek also used low reasoning effort and `provider.only=["wafer/fast"]` with fallbacks disabled; ZDR, `data_collection=deny`, and `require_parameters=true` remained enforced. The [ZDR endpoint list](https://openrouter.ai/docs/api/api-reference/endpoints/list-endpoints-zdr) showed `wafer/fast` supporting `response_format`. A [generation metadata readback](https://openrouter.ai/docs/api/api-reference/generations/get-generation) confirmed the preflight ran on Wafer and that its `total_cost` matched the per-call response cost. [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection) documents this pin. The prompt, output limit, reasoning setting, and route changed, so latency differences cannot be attributed to the pin alone.

| Family | Exact OpenRouter model ID | Cases | Intent accuracy | Slot F1 | Valid JSON / all attempts | Valid final cases | ES / PT quality | p50 / p95 latency | Cost / case³ |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| DeepSeek, Wafer `wafer/fast` | `deepseek/deepseek-v4-flash-0731` | 32 | 100.0% | 100.0% | 32/32 (100.0%) | 32/32 | Pending / pending | 10.02 / 21.91 s | $0.000401 |
| Gemini Flash-Lite | `google/gemini-2.5-flash-lite` | 32 | 100.0% | 100.0% | 32/32 (100.0%) | 32/32 | Pending / pending | 1.08 / 1.85 s | $0.000140 |
| Gemini Flash | `google/gemini-3-flash-preview` | 32 | 100.0% | 100.0% | 32/32 (100.0%) | 32/32 | Pending / pending | 1.92 / 2.30 s | $0.001207 |
| Grok | `x-ai/grok-4.3` | 32 | 100.0% | 100.0% | 32/32 (100.0%) | 32/32 | Pending / pending | 4.54 / 6.83 s | $0.002589 |

The 128/128 result is on the **same unreviewed dev suite** used to diagnose and revise the prompt. It shows only that the explicit v2 taxonomy matched the **superseded** inferred labels; it is not an independent production-accuracy estimate. Qwen 9B was removed from the rerun as requested. No default was selected.

## V1 diagnostic repeat and failure attribution

The original aggregate did not retain case-level predictions, stop reasons, provider names, or generation IDs. To investigate its 30 missing final responses, the five models were run again on the **unchanged v1 prompt, schema, 1,024-token requested output limit, and 32 cases**, saving only synthetic case IDs, predictions, and call metadata under ignored `artifacts/ai-round-one/baseline-diagnostic.json`. This repeat independently reproduced the original totals: **130/200 valid attempts and 30/160 cases without a valid final response**. Every unsuccessful returned response had `finish_reason=length`; there were no provider errors, safety refusals, or invalid parsed JSON. [OpenRouter documents](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens) that reasoning tokens can consume the output budget before a JSON answer appears. The following by-model counts belong to the **repeat**, not to a recovered log of the original run.

| Model ID | V1 repeat intent accuracy | Valid final | Valid JSON / all attempts | `length` attempts | p50 / p95 latency | Cost / case³ |
|---|---:|---:|---:|---:|---:|---:|
| `deepseek/deepseek-v4-flash-0731` | 75.0% | 28/32 | 28/44 (63.6%) | 16 | 20.32 / 58.71 s | $0.000397 |
| `qwen/qwen3.5-9b` | 6.3% | 6/32 | 6/60 (10.0%) | 54 | 46.49 / 77.31 s | $0.000345 |
| `google/gemini-2.5-flash-lite` | 62.5% | 32/32 | 32/32 (100.0%) | 0 | 1.02 / 1.86 s | $0.000098 |
| `google/gemini-3-flash-preview` | 65.6% | 32/32 | 32/32 (100.0%) | 0 | 1.97 / 2.26 s | $0.001045 |
| `x-ai/grok-4.3` | 68.8% | 32/32 | 32/32 (100.0%) | 0 | 5.32 / 7.33 s | $0.001969 |

The repeat's **30 no-final cases were four DeepSeek and 26 Qwen**. Its 70 `length` attempts were 16 DeepSeek and 54 Qwen. Ten first-attempt length stops recovered on retry. The original run had the same aggregate totals, but its exact by-model attribution and provider routing remain unverified because those records were not saved.

This pooled **cross-model confusion matrix** counts model-case evaluations in the v1 repeat, not distinct messages. `No final` means neither of the two attempts yielded a valid response. The suite has no gold cases for duplicate-charge, dispute-status, or refund-status intents.

| Gold intent / predicted | Charge inquiry | Dispute charge | Human request | Fee dispute | Card lost / fraud | Out of scope | Refund / reversal status | No final | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Charge inquiry | 33 | 2 | 0 | 0 | 0 | 0 | 0 | 5 | 40 |
| Dispute charge | 33 | 14 | 0 | 0 | 0 | 0 | 0 | 13 | 60 |
| Human request | 0 | 0 | 15 | 0 | 0 | 0 | 0 | 5 | 20 |
| Fee dispute | 2 | 0 | 0 | 4 | 0 | 0 | 1 | 3 | 10 |
| Card lost / fraud | 0 | 0 | 0 | 1 | 16 | 0 | 1 | 2 | 20 |
| Out of scope | 0 | 0 | 0 | 0 | 0 | 7 | 1 | 2 | 10 |
| **Total** | **68** | **16** | **15** | **5** | **16** | **7** | **3** | **30** | **160** |

These are the synthetic cases **at least three of five models missed** in the v1 repeat. Counts include no-final responses. The common valid mistake was `charge_inquiry` for an unrecognized purchase; the v1 prompt had not defined that boundary. The old gold label depended on treating unrecognized-charge language as a dispute; Sebastian has now rejected that definition. A separate output-limit failure affected DeepSeek or Qwen on some cases. V2 matched all of these under the superseded inferred labels, several of which Sebastian has since corrected.

| Synthetic case ID | Gold label | Models missing / 5 | Primary fault |
|---|---|---:|---|
| `es.normal.dispute` | dispute_charge | 4 | V1 prompt/taxonomy; Qwen output limit |
| `pt.normal.dispute` | dispute_charge | 4 | V1 prompt/taxonomy; Qwen output limit |
| `es.ambiguous.amount.pesos` | dispute_charge | 4 | V1 prompt/taxonomy; Qwen output limit |
| `pt.ambiguous.amount.reais` | dispute_charge | 4 | V1 prompt/taxonomy; Qwen made the same semantic error |
| `es.ambiguous.amount.dollars` | dispute_charge | 5 | V1 prompt/taxonomy; DeepSeek and Qwen output limits |
| `pt.ambiguous.amount.dollars` | dispute_charge | 5 | V1 prompt/taxonomy; Qwen output limit |
| `es.ambiguous.amount.comma` | dispute_charge | 4 | V1 prompt/taxonomy; Qwen output limit |
| `es.ambiguous.vague.charge` | dispute_charge | 4 | V1 prompt/taxonomy; Qwen output limit |
| `pt.ambiguous.vague.charge` | dispute_charge | 4 | V1 prompt/taxonomy; Qwen output limit |
| `es.ambiguous.vague.payment` | dispute_charge | 5 | V1 prompt/taxonomy; DeepSeek and Qwen output limits |
| `pt.human.fee.dispute` | fee_dispute | 4 | V1 prompt/taxonomy; DeepSeek chose refund status and Qwen hit the output limit |

There were also isolated **model-specific v1 interpretations**: DeepSeek labeled `pt.normal.pending.unknown` as a dispute and `es.human.out.of.scope` as refund status, while other completed models got those labels right. Both were correct on v2 under the old labels. Sebastian has since resolved the suspected gold-label error: ten of the 12 recognition/denial cases change to inquiry, and the two explicit-denial cases stay disputes, as listed above. The two bank-fee labels remain unreviewed, though their wording supports `fee_dispute`.

³ The cumulative ledger is **$0.004537** original probes + **$0.135728** original full run + **$0.123333** v1 diagnostic repeat + **$0.138785** v2 rerun = **$0.402383**, below the approved $5 cap. Each case cost uses per-call response usage/cost, including retries, never the shared key-level delta. Both follow-up artifacts are ignored by Git and contain no customer messages or model thinking. Human review of label semantics, an independent annotated set, and ES/PT quality ratings are still required before a production model choice.

## Round two: harder NLU dev set

The new [150-case hard NLU dev set](../../src/aclara/llm/dev_150.yaml) is separate from the 32-case scenario suite and from any future frozen held-out NLU test. It has 30 utterances each from ES-MX, ES-CO, ES-AR, pt-BR, and mixed/code-switched language, with 219 explicit amount, currency, merchant, or date-expression annotations and no verbatim overlap with either 32-case scenario file. It covers lucas, palos, lana/varos, Brazilian contos/pila, Portuguese **cargo** and **esquisito**, Spanish **exquisito**, ambiguous pesos, vague amounts and dates, and ten direct prompt-injection attempts. Source and gold labels are **AI-lane-authored and unreviewed**; they are not human-verified as envisioned in brief §11.8. The suite SHA-256 was `d234931baccb1ebe4523d3a58c7e09d49fc15232322dc115ac47055559ed2d01`. The 30-case Opus sample was fixed by case ID before calls, six from each language group and spanning all nine gold intents. It must not be compared as if it had the same precision as a 150-case result.

All seven models received the same frozen [v3 NLU prompt](../../prompts/nlu/v3.md) (content SHA-256 `0a358ef723aefcbdefd65441f519455dc9da384ce6e2f0a03dff3bb19c387b03`), strict `ExtractedNlu` schema, 2,048-token requested output cap, two-attempt retry policy, ZDR and `data_collection=deny` OpenRouter routing, and `require_parameters=true`. The live [OpenRouter model catalog](https://openrouter.ai/docs/api/api-reference/models/get-models) was filtered for structured output and ZDR on 2026-09-27. It listed `google/gemini-3.5-flash-lite` as the newest eligible Flash-Lite model, alongside the requested 2.5 Flash-Lite and other exact IDs in the table below. The key used for this private run successfully routed 2.5 Flash-Lite; availability for another project is not inferred. The persistent `.env` approval flag remained unchanged; authorization was set only for these run processes.

Intent accuracy counts a missing final response as wrong. Slot micro-F1 counts every normalized predicted amount/currency/merchant and preserved date expression against explicit gold slots; missing finals contribute missed gold slots. JSON validity uses **all attempts**, including retries stopped before parsing. Language-ID accuracy includes `mixed`. Intent and JSON/final/language proportion intervals are two-sided 95% Wilson intervals; macro-F1, slot F1, p50/p95 case latency, and per-case cost use 2,000 deterministic case-cluster bootstrap resamples. Intervals describe sampling uncertainty for this **constructed, unreviewed** set, not uncertainty from its label errors or synthetic wording. ES/PT fluency quality remains pending human review. `out_of_scope` is the NLU abstention proxy; no-final responses are reported separately. Model outputs and messages were not retained in the run checkpoint—only synthetic IDs, labels, predictions, slot counts, stop reasons, timing, and per-call usage/cost. No key-level account delta contributes to the ledger.

## Round-two measured results

| Model (exact OpenRouter ID) | n | Intent accuracy, 95% CI | Macro-F1, 95% CI | Slot F1, 95% CI | Valid JSON / all attempts, 95% CI | Valid final, 95% CI | Language ID, 95% CI | ES / PT quality | p50 / p95 latency s, 95% CI | Cost / case USD, 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| `google/gemini-2.5-flash-lite` | 150 | 100.0% [97.5, 100.0] | 100.0 [100.0, 100.0] | 93.4 [90.3, 96.2] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 88.7% [82.6, 92.8] | Pending / pending | 1.02 [1.01, 1.03] / 1.39 [1.17, 1.78] | $0.0001524 [0.0001522, 0.0001526] |
| `google/gemini-3.5-flash-lite` | 150 | 100.0% [97.5, 100.0] | 100.0 [100.0, 100.0] | 94.3 [91.4, 96.9] | 150/152 (98.7% [95.3, 99.6]) | 150/150 (100.0% [97.5, 100.0]) | 94.7% [89.8, 97.3] | Pending / pending | 1.30 [1.29, 1.32] / 1.71 [1.54, 2.25] | $0.0009376 [0.0009299, 0.0009449] |
| `google/gemini-3-flash-preview` | 150 | 100.0% [97.5, 100.0] | 100.0 [100.0, 100.0] | 95.7 [93.2, 97.8] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 90.0% [84.2, 93.8] | Pending / pending | 1.88 [1.86, 1.93] / 2.36 [2.17, 2.69] | $0.0012650 [0.0012620, 0.0012689] |
| `x-ai/grok-4.3` | 150 | 100.0% [97.5, 100.0] | 100.0 [100.0, 100.0] | 93.7 [91.0, 96.4] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 95.3% [90.7, 97.7] | Pending / pending | 6.35 [6.12, 6.48] / 9.23 [8.95, 9.71] | $0.0025451 [0.0024374, 0.0026530] |
| `anthropic/claude-haiku-4.5` | 150 | 99.3% [96.3, 99.9] | 99.3 [97.5, 100.0] | 95.3 [92.8, 97.5] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 94.7% [89.8, 97.3] | Pending / pending | 2.43 [2.40, 2.47] / 3.09 [2.86, 3.27] | $0.0028673 [0.0028574, 0.0028769] |
| `anthropic/claude-sonnet-5` | 150 | 100.0% [97.5, 100.0] | 100.0 [100.0, 100.0] | 95.2 [92.7, 97.6] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 95.3% [90.7, 97.7] | Pending / pending | 3.53 [3.40, 3.65] / 6.38 [5.50, 6.80] | $0.0085705 [0.0084030, 0.0087583] |
| `anthropic/claude-opus-5` | 30 | 100.0% [88.6, 100.0] | 100.0 [100.0, 100.0] | 96.3 [90.0, 100.0] | 30/30 (100.0% [88.6, 100.0]) | 30/30 (100.0% [88.6, 100.0]) | 93.3% [78.7, 98.2] | Pending / pending | 2.89 [2.81, 3.09] / 5.64 [3.71, 6.71] | $0.0187125 [0.0185021, 0.0189775] |

Deterministic P fallback on the same 150 cases: intent 52.7% [44.7, 60.5], macro-F1 45.6 [39.6, 50.0], slot F1 61.0 [54.7, 66.8], language ID 68.7% [60.9, 75.5]. The frozen B1 legacy intent rule scores 39.3% [31.9, 47.3]; it retains the old recognition routing for its end-to-end workflow.

Round-two response spend: **$3.012058**; cumulative per-call spend including pilot and round one: **$3.520801**.

| Model | ES-MX correct / 30 | ES-CO correct / 30 | ES-AR correct / 30 | pt-BR correct / 30 | Mixed correct / 30 | Slang correct | False-friend correct | Injection intent correct | Out-of-scope precision / recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `google/gemini-2.5-flash-lite` | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 14/14 | 7/7 | 10/10 | 9/9 / 9/9 |
| `google/gemini-3.5-flash-lite` | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 14/14 | 7/7 | 10/10 | 9/9 / 9/9 |
| `google/gemini-3-flash-preview` | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 14/14 | 7/7 | 10/10 | 9/9 / 9/9 |
| `x-ai/grok-4.3` | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 14/14 | 7/7 | 10/10 | 9/9 / 9/9 |
| `anthropic/claude-haiku-4.5` | 30/30 | 30/30 | 30/30 | 29/30 | 30/30 | 14/14 | 7/7 | 9/10 | 9/10 / 9/9 |
| `anthropic/claude-sonnet-5` | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 14/14 | 7/7 | 10/10 | 9/9 / 9/9 |
| `anthropic/claude-opus-5` | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 2/2 | 2/2 | 1/1 | 2/2 / 2/2 |

Intent macro-F1 by dialect/language, with 95% case-bootstrap intervals:

| Model | ES-MX | ES-CO | ES-AR | pt-BR | Mixed |
|---|---:|---:|---:|---:|---:|
| `google/gemini-2.5-flash-lite` | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |
| `google/gemini-3.5-flash-lite` | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |
| `google/gemini-3-flash-preview` | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |
| `x-ai/grok-4.3` | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |
| `anthropic/claude-haiku-4.5` | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 97.3 [91.2, 100.0] | 100.0 [100.0, 100.0] |
| `anthropic/claude-sonnet-5` | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |
| `anthropic/claude-opus-5` | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |

Injection-suspected flag on the ten injection utterances (recall), followed by false flags on the other cases:

| Model | Flagged injection cases | False flags on non-injection cases |
|---|---:|---:|
| `google/gemini-2.5-flash-lite` | 4/10 | 0/140 |
| `google/gemini-3.5-flash-lite` | 8/10 | 0/140 |
| `google/gemini-3-flash-preview` | 10/10 | 0/140 |
| `x-ai/grok-4.3` | 10/10 | 0/140 |
| `anthropic/claude-haiku-4.5` | 10/10 | 0/140 |
| `anthropic/claude-sonnet-5` | 10/10 | 0/140 |
| `anthropic/claude-opus-5` | 1/1 | 0/29 |

Pooled confusion matrix, six full-suite models (900 model-case outcomes; Opus sample excluded):

| Gold / predicted | charge_inquiry | dispute_charge | duplicate_charge | refund_or_reversal_status | dispute_status | fee_dispute | card_lost_or_fraud | human_request | out_of_scope | no_final |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| charge_inquiry | 395 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| dispute_charge | 0 | 150 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| duplicate_charge | 0 | 0 | 60 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| refund_or_reversal_status | 0 | 0 | 0 | 60 | 0 | 0 | 0 | 0 | 0 | 0 |
| dispute_status | 0 | 0 | 0 | 0 | 30 | 0 | 0 | 0 | 0 | 0 |
| fee_dispute | 0 | 0 | 0 | 0 | 0 | 60 | 0 | 0 | 0 | 0 |
| card_lost_or_fraud | 0 | 0 | 0 | 0 | 0 | 0 | 60 | 0 | 0 | 0 |
| human_request | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 0 |
| out_of_scope | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 54 | 0 |

Most common completed intent confusions: charge_inquiry → out_of_scope: 1.

Non-valid attempts in the scored 930-case checkpoint: google/gemini-3.5-flash-lite invalid_json/error: 2.

Five of the six full-suite models were perfect on intent; Haiku missed only one pt-BR inquiry with an injection attempt, labeling it out of scope. The table therefore **does not discriminate those five models on intent** and does not justify a default. The handcrafted set remains too canonical despite broader coverage. Perfect observed macro-F1 produces a degenerate case-bootstrap interval of `[100, 100]`; the Wilson accuracy interval and the pending human label review are more honest about uncertainty. Slot F1, language identification, injection flags, latency, and cost distinguish behaviors, but the injected-message slice measures intent and suspicion flags only—not resistance to arbitrary prompt leakage or unauthorized action. No model choice was made.

The full scored Haiku run used the schema-capable, ZDR [`amazon-bedrock/global` endpoint](https://openrouter.ai/docs/api/api-reference/endpoints/list-endpoints-zdr) at the catalog rate of $1/M input and $5/M output; [generation metadata](https://openrouter.ai/docs/api/api-reference/generations/get-generation) readback for two calls showed Amazon Bedrock and matched their response costs. A prior unpinned 25-case pass cost **$0.072047** in known per-call charges and was archived privately, excluded from Haiku's accuracy/latency/cost-per-case row, but **included** in the cumulative ledger. It stopped on an attempt with no response usage/cost. A first pinned pass also had a no-usage interruption after 29 scored cases; those cases were resumed on the same endpoint with a three-second inter-request gap. The first parallel pass used a 20-second HTTP timeout; the pinned Haiku passes used 60 seconds. Pacing was outside measured call latency. The exact charges for the two no-usage interruptions are unknown and are **not assigned to any case or model cost estimate**; a separate $0.30 conservative cap guard covers potential billing. There were no no-final cases in the scored 930-case checkpoint. Gemini 3.5 Flash-Lite needed two extra attempts after invalid JSON and recovered both.

The known per-call cumulative ledger is **$0.402383** round one + **$0.034314** seven-model pilot + **$0.072047** archived Haiku first pass + **$3.012058** scored round two = **$3.520801**. Even including the $0.30 unknown-billing guard, this remains below Sebastian's $10 cumulative cap. The open questions are human verification of the new labels, human ES/PT quality ratings, and a genuinely independent NLU challenge set. The frozen end-to-end held-out suite was not used to tune the prompt or select a model.

## Round three: cheap cross-vendor challengers

Sebastian selected Gemini 3 Flash as the default before this run; round three did not reopen that choice. The same **frozen, AI-authored and unreviewed 150-case dev suite** (SHA-256 `d234931baccb1ebe4523d3a58c7e09d49fc15232322dc115ac47055559ed2d01`) and v3 prompt (SHA-256 `0a358ef723aefcbdefd65441f519455dc9da384ce6e2f0a03dff3bb19c387b03`) were used. No dev label or prompt was changed for these challengers. The table repeats the round-two Gemini baseline on the same cases. Intent and final-response intervals use 95% Wilson bounds; macro-F1, slot F1, latency and known per-call cost use 2,000 case-cluster bootstrap resamples. Paired slot differences resample matching case IDs. Injection-flag intervals are Wilson bounds on ten synthetic attempts. These intervals exclude label and authoring uncertainty. ES/PT fluency quality still needs human review.

Exact IDs and displayed catalog rate floors were checked on 2026-09-27 against the [OpenRouter live model catalog](https://openrouter.ai/docs/api/api-reference/models/get-models), filtered for `response_format` and [ZDR endpoints](https://openrouter.ai/docs/api/api-reference/endpoints/list-endpoints-zdr). The two canonical OpenAI GPT mini/nano IDs are the cheapest eligible non-batch models in those classes; [OpenAI lists those API families](https://developers.openai.com/api/docs/models/all). `x-ai/grok-4.20` is the current fast general-purpose Grok challenger; the cheaper `grok-build-0.1` is specialized for coding and was excluded from this NLU comparison. Qwen uses the non-thinking 80B instruct model, not the prior 9B route. Mistral Small 4 is cataloged as `mistralai/mistral-small-2603`. The catalog floors are for orientation; the actual per-case column sums each response's per-call usage/cost, including retries, and never uses the shared key-level account delta. A ZDR provider may bill above the floor. All scored calls required strict JSON schema, ZDR, `data_collection=deny`, `require_parameters=true`, and a 2,048-token output limit.

The OpenAI routes required `reasoning=minimal`: their ZDR endpoint rejected `reasoning=none` with HTTP 400 during the one-case preflight. Mistral Small's unpinned preflight returned HTTP 429, so the full run pinned `mistral/us`. DeepSeek used `reasoning=none` and `provider.only=["wafer/fast"]`, with provider fallback disabled. A separate three-case-per-provider probe found **3/3 valid** from Wafer, DeepInfra, and OpenInference; observed median latency was **2.65, 5.37, and 7.08 seconds**, respectively. This is a small route choice check, not proof Wafer is always fastest. The initial preflight produced six HTTP 400/429 attempts without per-call usage/cost. They are accounted for as unknown charges under a conservative guard, not assigned a billed cost.

| Exact OpenRouter model ID | Catalog input / output USD per 1M | n | Intent, 95% CI | Macro-F1, 95% CI | Slot F1, 95% CI | Valid JSON / all attempts, 95% CI | Valid final, 95% CI | Language ID, 95% CI | Injection flags / 10; false flags / 140 | ES / PT quality | p50 / p95 latency s, 95% CI | Known cost / case USD, 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| `google/gemini-3-flash-preview` | $0.25 / $1.5 | 150 | 100.0% [97.5, 100.0] | 100.0 [100.0, 100.0] | 95.7 [93.2, 97.8] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 90.0% [84.2, 93.8] | 10/10 [72.2, 100.0]%; 0/140 | Pending / pending | 1.88 [1.86, 1.93] / 2.36 [2.17, 2.69] | $0.0012650 [0.0012620, 0.0012689] |
| `openai/gpt-5-nano` | $0.025 / $0.2 | 150 | 89.3% [83.4, 93.3] | 92.6 [86.7, 96.7] | 88.7 [84.9, 92.3] | 148/152 (97.4% [93.4, 99.0]) | 148/150 (98.7% [95.3, 99.6]) | 70.0% [62.2, 76.8] | 1/10 [1.8, 40.4]%; 0/140 | Pending / pending | 1.26 [1.23, 1.30] / 2.57 [1.73, 2.97] | $0.0000735 [0.0000719, 0.0000749] |
| `openai/gpt-5-mini` | $0.125 / $1 | 150 | 97.3% [93.3, 99.0] | 99.2 [98.2, 99.9] | 93.6 [90.7, 96.2] | 148/152 (97.4% [93.4, 99.0]) | 148/150 (98.7% [95.3, 99.6]) | 88.7% [82.6, 92.8] | 6/10 [31.3, 83.2]%; 0/140 | Pending / pending | 2.02 [1.95, 2.06] / 3.90 [2.95, 4.35] | $0.0003494 [0.0003410, 0.0003568] |
| `x-ai/grok-4.20` | $1.25 / $2.5 | 150 | 99.3% [96.3, 99.9] | 99.4 [97.7, 100.0] | 93.2 [90.3, 95.9] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 92.0% [86.5, 95.4] | 9/10 [59.6, 98.2]%; 0/140 | Pending / pending | 1.60 [1.57, 1.63] / 1.94 [1.84, 2.03] | $0.0009640 [0.0008887, 0.0010403] |
| `qwen/qwen3-next-80b-a3b-instruct` | $0.1 / $1.1 | 150 | 98.0% [94.3, 99.3] | 98.4 [95.8, 100.0] | 93.0 [89.9, 95.8] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 88.0% [81.8, 92.3] | 4/10 [16.8, 68.7]%; 0/140 | Pending / pending | 1.56 [1.44, 1.70] / 5.14 [4.84, 5.60] | $0.0002881 [0.0002839, 0.0002926] |
| `deepseek/deepseek-v4-flash-0731` | $0.0215 / $0.3 | 150 | 99.3% [96.3, 99.9] | 99.4 [97.6, 100.0] | 94.0 [91.4, 96.4] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 88.7% [82.6, 92.8] | 8/10 [49.0, 94.3]%; 0/140 | Pending / pending | 2.41 [2.28, 2.56] / 3.66 [3.52, 3.80] | $0.0001122 [0.0001118, 0.0001126] |
| `mistralai/mistral-small-2603` | $0.15 / $0.6 | 150 | 94.7% [89.8, 97.3] | 94.4 [88.6, 98.1] | 94.3 [91.6, 96.8] | 150/150 (100.0% [97.5, 100.0]) | 150/150 (100.0% [97.5, 100.0]) | 87.3% [81.1, 91.7] | 6/10 [31.3, 83.2]%; 0/140 | Pending / pending | 1.17 [1.15, 1.19] / 1.49 [1.43, 1.73] | $0.0001337 [0.0001317, 0.0001359] |

Paired slot-F1 differences versus the selected Gemini 3 Flash baseline on the same 150 cases (2,000 case-pair bootstrap resamples; percentage points):

| Challenger | Difference, 95% CI | Injection flags and false flags match baseline? |
|---|---:|---:|
| `openai/gpt-5-nano` | -6.9 [-10.2, -3.8] | No |
| `openai/gpt-5-mini` | -2.1 [-4.1, -0.2] | No |
| `x-ai/grok-4.20` | -2.5 [-4.4, -1.0] | No |
| `qwen/qwen3-next-80b-a3b-instruct` | -2.7 [-5.0, -0.9] | No |
| `deepseek/deepseek-v4-flash-0731` | -1.6 [-3.7, +0.4] | No |
| `mistralai/mistral-small-2603` | -1.4 [-3.4, +0.5] | No |

Dialect and challenge-slice intent accuracy:

| Model | ES-MX / 30 | ES-CO / 30 | ES-AR / 30 | pt-BR / 30 | Mixed / 30 | Slang | False friends | Injection intent | Out-of-scope precision / recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `google/gemini-3-flash-preview` | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 14/14 | 7/7 | 10/10 | 9/9 / 9/9 |
| `openai/gpt-5-nano` | 27/30 | 28/30 | 25/30 | 26/30 | 28/30 | 13/14 | 7/7 | 5/10 | 7/7 / 7/9 |
| `openai/gpt-5-mini` | 29/30 | 30/30 | 29/30 | 29/30 | 29/30 | 14/14 | 7/7 | 6/10 | 9/9 / 9/9 |
| `x-ai/grok-4.20` | 30/30 | 30/30 | 30/30 | 29/30 | 30/30 | 14/14 | 7/7 | 10/10 | 9/9 / 9/9 |
| `qwen/qwen3-next-80b-a3b-instruct` | 30/30 | 30/30 | 29/30 | 28/30 | 30/30 | 14/14 | 7/7 | 8/10 | 9/10 / 9/9 |
| `deepseek/deepseek-v4-flash-0731` | 30/30 | 30/30 | 29/30 | 30/30 | 30/30 | 14/14 | 7/7 | 9/10 | 9/9 / 9/9 |
| `mistralai/mistral-small-2603` | 28/30 | 28/30 | 28/30 | 29/30 | 29/30 | 14/14 | 7/7 | 3/10 | 9/14 / 9/9 |

Cross-model intent confusions (challengers only):

| Gold / predicted | charge_inquiry | dispute_charge | duplicate_charge | refund_or_reversal_status | dispute_status | fee_dispute | card_lost_or_fraud | human_request | out_of_scope | no_final |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| charge_inquiry | 375 | 7 | 0 | 2 | 0 | 1 | 0 | 1 | 6 | 4 |
| dispute_charge | 9 | 141 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| duplicate_charge | 0 | 0 | 60 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| refund_or_reversal_status | 0 | 0 | 0 | 60 | 0 | 0 | 0 | 0 | 0 | 0 |
| dispute_status | 0 | 0 | 0 | 0 | 30 | 0 | 0 | 0 | 0 | 0 |
| fee_dispute | 0 | 0 | 0 | 0 | 0 | 60 | 0 | 0 | 0 | 0 |
| card_lost_or_fraud | 0 | 0 | 0 | 0 | 0 | 0 | 60 | 0 | 0 | 0 |
| human_request | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 29 | 0 | 0 |
| out_of_scope | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 52 | 0 |

Non-valid scored attempts: openai/gpt-5-nano refusal/content_filter: 4; openai/gpt-5-mini refusal/content_filter: 4.
Known round-three pilot, provider-probe, and scored-response spend: **$0.292253**; cumulative known per-call spend: **$3.813054**. There are 6 no-response attempts without per-call cost, including six initial preflight errors. They are excluded from cost per case; a separate $0.02/attempt guard plus a $0.30 reserve protects the cumulative $10 cap.

The OpenAI **scored** failures are provider `content_filter` stops, not output truncation: each of `gpt-5-nano` and `gpt-5-mini` lacked a final response on the same two cases after one retry, four non-valid attempts per model. They count against intent, slots, JSON validity over **all** attempts, and final-response rate. The six initial no-response preflight attempts are separate from the 900 scored model-case outcomes. Their actual charge is unknown because the provider returned no usage/cost; the $0.12 unknown-attempt guard and $0.30 reserve keep the approved $10 cumulative cap protected.

**No challenger meets the full parity goal.** Gemini 3 Flash recorded 95.7% slot F1 and 10/10 injection flags with zero false flags. The nearest observed slot results among the cheaper vendors were Mistral Small 4 (94.3%) and DeepSeek V4 Flash (94.0%), but they flagged only 6/10 and 8/10 injected utterances. Grok 4.20 flagged 9/10 with zero false flags, had 1.60/1.94-second p50/p95 latency and $0.000964 known cost/case, but its 93.2% slot F1 was 2.5 points below Gemini (paired 95% interval −4.4 to −1.0). The flags measure suspicion on this small authored slice, not arbitrary injection resistance.

On cost-first criteria, **DeepSeek V4 Flash was the cheapest strong cross-vendor alternative** at $0.0001122/case (about 91% below Gemini) with 99.3% intent, 94.0% slot F1, 8/10 injection flags and no false flags. Its p50/p95 latency was 2.41/3.66 seconds, slower than Gemini. Grok 4.20 had stronger flag recall and speed but cost about 8.6 times as much as DeepSeek per case. Sebastian selected **Grok 4.20 as the failure-only fallback** after the selected Gemini route exhausts its bounded attempts; DeepSeek remains unselected. Claude remains reserved for the independent final held-out frontier comparison and judge validation; no Claude calls were made in round three. The 150-case dev set has been reused for comparison and cannot establish independent production accuracy or safety.
