# Round-one OpenRouter comparison and error analysis

**No default model has been chosen.** Production remains `LLM_PROVIDER=mock`, and the persistent `.env` approval flag was not changed. Sebastian approved a **$5 cumulative cap** for the original comparison and follow-up. The original five-model run, v1 diagnostic repeat, and four-model v2 rerun together cost **$0.402383** from this lane's per-call response usage/cost fields, including the original probes.

The same **32 team-generated dev scenarios** from `evals/dev_scenarios.yaml` were sent to every model. The suite hash was `1078d9d591a4521281b8813fd303c8e5867030aefc46c8671f5f83eed0175676`. **The suite and the derived NLU labels are unreviewed.** Scenario IDs and expected outcomes supplied intent labels; only amount, currency, and merchant expression were scored as slots. The scenarios do not specify a country, so none was inferred. This is the current Layer 1 dev suite, not the planned 150-case human-reviewed NLU set. ES/PT quality ratings remain unreviewed and are not estimated from model prose.

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

The comparison is directional because labels were inferred from the baseline scenario suite, the sample is small, and no independent human ES/PT ratings or final test were run. Claude Haiku, Sonnet, and Opus remain reserved for the later test. Review the annotation set before selecting a production default.

## Revised prompt: four-model rerun

Prompt `prompts/nlu/v2.md` defines every intent, including the distinction between asking about a charge and denying a purchase, and separates bank-fee objections from merchant disputes. All four models used a 2,048-token requested output limit. DeepSeek also used low reasoning effort and `provider.only=["wafer/fast"]` with fallbacks disabled; ZDR, `data_collection=deny`, and `require_parameters=true` remained enforced. The [ZDR endpoint list](https://openrouter.ai/docs/api/api-reference/endpoints/list-endpoints-zdr) showed `wafer/fast` supporting `response_format`. A [generation metadata readback](https://openrouter.ai/docs/api/api-reference/generations/get-generation) confirmed the preflight ran on Wafer and that its `total_cost` matched the per-call response cost. [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection) documents this pin. The prompt, output limit, reasoning setting, and route changed, so latency differences cannot be attributed to the pin alone.

| Family | Exact OpenRouter model ID | Cases | Intent accuracy | Slot F1 | Valid JSON / all attempts | Valid final cases | ES / PT quality | p50 / p95 latency | Cost / case³ |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| DeepSeek, Wafer `wafer/fast` | `deepseek/deepseek-v4-flash-0731` | 32 | 100.0% | 100.0% | 32/32 (100.0%) | 32/32 | Pending / pending | 10.02 / 21.91 s | $0.000401 |
| Gemini Flash-Lite | `google/gemini-2.5-flash-lite` | 32 | 100.0% | 100.0% | 32/32 (100.0%) | 32/32 | Pending / pending | 1.08 / 1.85 s | $0.000140 |
| Gemini Flash | `google/gemini-3-flash-preview` | 32 | 100.0% | 100.0% | 32/32 (100.0%) | 32/32 | Pending / pending | 1.92 / 2.30 s | $0.001207 |
| Grok | `x-ai/grok-4.3` | 32 | 100.0% | 100.0% | 32/32 (100.0%) | 32/32 | Pending / pending | 4.54 / 6.83 s | $0.002589 |

The 128/128 result is on the **same unreviewed dev suite** used to diagnose and revise the prompt. It shows that the explicit taxonomy fixed these cases; it is not an independent production-accuracy estimate. Qwen 9B was removed from the rerun as requested. No default was selected.

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

These are the synthetic cases **at least three of five models missed** in the v1 repeat. Counts include no-final responses. The common valid mistake was `charge_inquiry` for an unrecognized purchase; the v1 prompt had not defined that boundary. The current gold label is supported if `dispute_charge` means reporting an unrecognized charge rather than explicitly asking to file a dispute. A separate output-limit failure affected DeepSeek or Qwen on some cases. V2 corrected all of these on the four retained models.

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

There were also isolated **model-specific v1 interpretations**: DeepSeek labeled `pt.normal.pending.unknown` as a dispute and `es.human.out.of.scope` as refund status, while other completed models got those labels right. Both were correct on v2. No clear gold-label error is proven by the opening text. **Gold-label review for Sebastian:** confirm whether `dispute_charge` includes reporting an unrecognized purchase without an explicit filing request. That definition affects all 12 currently labeled cases: `es.normal.dispute`, `pt.normal.dispute`, and the ten `*.ambiguous.*` cases, including `es.ambiguous.vague.purchase` and `pt.ambiguous.vague.purchase` that did not cross the most-missed threshold. These labels were inferred from scenario IDs/outcomes; the two `normal.dispute` scenarios also contain later confirmation turns. The labels have **not** been edited. The two bank-fee cases should likewise be confirmed as `fee_dispute`, though their wording supports that label.

³ The cumulative ledger is **$0.004537** original probes + **$0.135728** original full run + **$0.123333** v1 diagnostic repeat + **$0.138785** v2 rerun = **$0.402383**, below the approved $5 cap. Each case cost uses per-call response usage/cost, including retries, never the shared key-level delta. Both follow-up artifacts are ignored by Git and contain no customer messages or model thinking. Human review of label semantics, an independent annotated set, and ES/PT quality ratings are still required before a production model choice.
