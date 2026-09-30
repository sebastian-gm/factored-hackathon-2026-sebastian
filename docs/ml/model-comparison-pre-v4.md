# Queued development comparison: access preflight

**2026-09-30, zero inference calls / $0.** Gemini remains the production choice.
The new `dev-gate/model-compare` durable scope and exact run ID have **not** been
confirmed; no paid comparison may start. The pre-v4 robustness scope cannot be
reused. Read-only checks at 22:51–22:55 UTC used the public model/endpoint catalog
and authenticated metadata GETs only, never inference or a key-balance cost delta.
Private timestamped receipts: `artifacts/dev-model-compare/`.

## NLU / phrasing candidates

| Exact model ID | Confirmed ZDR provider tag | Input / output per 1M tokens | Access evidence |
|---|---|---:|---|
| `google/gemini-3-flash-preview` | `google-vertex/global` | $0.50 / $3.00 | Current pin; ZDR endpoint and user-model lists |
| `openai/gpt-6.1-sol` | `azure` | $2.00 / $10.00 | ZDR endpoint and user-model lists; structured outputs supported |

The [live model catalog](https://openrouter.ai/api/v1/models?zdr=true),
[ZDR endpoint list](https://openrouter.ai/api/v1/endpoints/zdr) and
[user-model listing documentation](https://openrouter.ai/docs/api/api-reference/models/list-models-filtered-by-user-provider-preferences-privacy-settings-and-guardrails)
support these metadata checks. Sol's ZDR list also includes `azure/us` and
`azure/eu` at $2.20 / $11.00. Its cheaper `openai/flex` route appears in the
unfiltered endpoint list but **not** in the ZDR list; exclude it from this study.
Catalog membership does not prove a successful request or that account credits
are available. The earlier health GET verified exhausted OpenRouter credits;
no paid probe was made to override that evidence.

Any candidate overlay must enforce `provider.only: [azure]`, `zdr: true`,
`data_collection: deny`, `require_parameters: true` and no provider spillover.
Use the existing code-authorized Grok failure fallback and report its rate
separately. Do not edit production config. Sol supports Chat Completions without
tools; lowest supported reasoning effort is `low`, not `none` or `minimal`.
Pin that setting, token/timeout limits and returned model snapshot, and never
store reasoning. These are documented model differences, not matched reasoning
budgets. [Official OpenAI model specifications](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
give the supported API and effort values.

Gemini 4 Argon is excluded per the owner's instruction; no general-availability
claim or benchmark was independently made here.

## Decisions challenger: no OpenAI access established

The authenticated `models/user?output_modalities=decisions` GET returned nine
listed decision models, **none `openai/*`**; the corresponding public modality
list agreed. The worktree has no direct `OPENAI_API_KEY` and no installed OpenAI
SDK. Official [OpenAI changelog](https://developers.openai.com/api/docs/changelog)
and documentation searches did not establish a callable Decisions API endpoint
or this account's preview entitlement. This is an access limitation, not proof
that a limited-preview product does not exist. The owner's approximate latency
and calibration claims are not measured evidence.

OpenRouter has its own `alpha.decisions` API serving third-party typed models,
including Jev; that is not evidence of an OpenAI Decisions model. See
[OpenRouter's Jev access example](https://openrouter.ai/blog/insights/what-is-jev/).
Do not substitute a different vendor or ordinary LLM-generated confidence.
Jev-versus-OpenAI recall, precision, ECE, latency and cost therefore remain
unmeasured pending actual preview access and approved scoped funding.

## Paired study and budget feasibility

The owner subsequently approved a **balanced paired sample under $1.50** instead
of full 240-case coverage. The same frozen dev 20, explain/offer confirmation 20,
robustness 40, round-two 60 and retired v3 100 form the source pool, with no v4.
The [frozen sample manifest](../../src/aclara/llm/dev_model_compare_50.manifest.json)
selects **50 pairs / 100 planned P case-runs**: ten per set, five ES/five PT in
each (25 ES/25 PT overall). Selection uses metadata-only stable SHA ordering,
dialect/category buckets, all ten round-two families once, alternating languages
and round-robin sets; it reads no saved model outcomes. Manifest SHA-256:
`40ef32671ff05617dc3246db38891a756b6d200cec48c368cc6e2483416b634c`.
The loader validates full-pool and per-case hashes before use. Equal set weighting
does not estimate pass on the original 240-case mix, and n=5 language/set cells
will have wide intervals. The separate lean-v5.2 adoption gate still needs all
240 cases per prompt; this approval changes only the model comparison.
Local verification: 299 relevant mock/unit checks passed with eight DB skips;
Ruff, format and strict mypy (88 source files) passed. No sample provider run.

Pin implementation,
v5.1 NLU / phrase v2, scenario/binding/scorer hashes and routing. Interleave paired
cases across the five sets; keep timeouts, provider errors, fallback and incomplete
cases in attempt/cost denominators. Compare objective pass, in-scope and eligible
SAR, strict escalation/unnecessary transfers, unsafe, slot F1, confident language
errors, p50/p95 NLU/turn/case latency, cost per conversation and ES/PT. Report
Wilson and case-cluster uncertainty, with synthetic/correlated-case caveats.
No comparison or replacement recommendation is yet supported.

**The original full study was unlikely to fit $1.50.** As a transparent cost estimate,
the saved round-two baseline's 169 valid Gemini calls used 409,438 input and
25,963 output tokens. Repricing those same tokens without caching at the confirmed
routes gives $0.282608 Gemini + $1.078506 Sol = **$1.361114 for that 60-case set
alone**, before Jev, retries, unknown costs, or Sol-specific reasoning. This is
not measured Sol usage and does not predict identical outputs. The other 180
cases would add cost. The approved smaller sample still needs conservative
reservations; it has no measured Sol cost or guarantee of complete coverage.
Once the lead confirms the new lifetime scope/run and credits,
reserve before every request and preserve the $1.50 / $12 cumulative caps. If
only partial coverage fits, disclose it and withhold a full-study conclusion;
changing coverage or enlarging funding requires the owner's decision.
