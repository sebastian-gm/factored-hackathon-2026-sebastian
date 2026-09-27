# Language-layer model card

**Status: development evidence; final-v2 results pending.** This card describes the selected language layer, not the transaction matcher ([separate card](model-card-charge-matcher-v2.md)). Persistent production configuration remains `LLM_PROVIDER=mock` until the lead enables a reviewed real route. The first final attempt was stopped after a dev-only finding; its results were not viewed. The final-v2 program has not run. [Architecture](../architecture.md), [final plan](../evaluation/final-run-plan.md), [Option A dev analysis](dev-p-failure-analysis.md).

## Intended use and boundaries

The language layer helps an authenticated customer understand a card charge in Spanish or Brazilian Portuguese. It extracts a structured intent and recollection slots, identifies possible risk cues, and may draft a short clarification or status explanation from an approved response plan. A separate subjective judge rates language/register, clarity, empathy and handoff-summary usefulness for evaluation; those scores cannot establish factual or action correctness. The supported workflow and its deterministic boundaries are documented in the [architecture](../architecture.md) and [judge rubric](../evaluation/judge-rubric.md).

It is **out of scope** for the models to establish identity or ownership, search outside the authenticated account, decide policy eligibility, authorize a dispute or card freeze, create or update a case, promise a refund or credit, route a human handoff as an authority decision, verify a write, or determine objective evaluation outcomes. Dates, amounts and currency expressions are normalized by code after extraction; MATCH ranks only code-scoped transactions. The server checks policy, server-issued proposal hash, expiry, fresh OTP, explicit confirmation, idempotency and committed readback before reporting an action. A model statement never grants access or authority. [Architecture](../architecture.md), [NLU normalization](../../src/aclara/agent/nlu/structured.py), [API implementation](../../src/aclara/api/app.py).

## Models and assigned roles

| Role | Exact model/route | Allowed output and limit |
|---|---|---|
| Selected P NLU and eligible phrasing | `google/gemini-3-flash-preview` through OpenRouter, pinned to `google-vertex/global` | Strict-schema `ExtractedNlu`; optional `ReplyDraft` only for clarification and explanation. Defaults to mock until controlled activation. |
| Parallel risk-cue second opinion | TypeSafe `jev-1.13.0` direct API | Six `Noul` probabilities: lost/stolen, regulator, legal, distress, injection suspicion and human request. A cue is unioned with Gemini's Boolean flag at Jev probability ≥0.5; Jev failure/timeout keeps Gemini-only flags and logs degradation. No Jev intent, slot, arithmetic or phrasing route in production. |
| Failure-only cross-vendor fallback | `x-ai/grok-4.20` through OpenRouter, pinned to `xai/zdr` | Same schema and grounding boundary, invoked only after the selected Gemini route exhausts bounded attempts. It is not a load-balancing default. |
| Subjective wording judges | `anthropic/claude-sonnet-5` through OpenRouter `google-vertex/global`, plus TypeSafe `jev-1.13.0` | Four rubric dimensions, 1–5; Jev uses one `Score` per applicable dimension. Judges receive blinded wording fields, never objective gold, policy facts or authorization state. Human agreement remains unmeasured. |

These assignments follow Sebastian's recorded selection and the checked [route configuration](../../config/models.yaml), [Jev supporting-role report](typesafe-jev-comparison.md), [judge rubric](../evaluation/judge-rubric.md) and [final plan](../evaluation/final-run-plan.md). Sonnet is also the planned frontier **system** comparison on a smaller final-v2 subset; that is not the selected customer-facing default. [Final plan](../evaluation/final-run-plan.md).

## Prompt and question pins

Hashes below are SHA-256 of the complete UTF-8 file, including front matter, matching the [runtime prompt loader](../../src/aclara/llm/prompts.py). The merged `main` base for this card is `55cea74`, including Option A [PR #38](https://github.com/sebastian-gm/bank-agent-lab/pull/38). These hashes identify source bytes, not a claim that a final provider served them. The final-v2 receipt must pin the implementation SHA and prompt hashes before any paid evaluation. [Final plan](../evaluation/final-run-plan.md).

| Purpose | Version and source | SHA-256 at merged `main` base |
|---|---|---|
| Structured NLU | [`nlu@v4`](../../prompts/nlu/v4.md) | `3797c7d30f34368c41f410ddfe0a0bf7455c3f99b9c47623bb9c6af89cf48960` |
| Constrained phrasing | [`phrase@v1`](../../prompts/phrase/v1.md) | `a243e16a2bbfaf472ae395a5af5e99ad4ee4caddf6c983891d31ec0c9c248b97` |
| Sonnet subjective judge | [`subjective-response-judge@v1`](../../prompts/judge/v1.md) | `8f62c925c51276da2420c42364ea38b0fbe47b8911286b0b1548feb79a19282e` |
| Jev risk and rubric questions | [`jev-questions-v1`](../../src/aclara/llm/typesafe_questions.py) | `d5291e12c56a7f0fbea2ca4f8aca70e7be6d32711df87bc702bbe339aeb5ba29` |

## Safety, injection and grounding

Customer messages, transaction text and response plans are untrusted data. Direct prompt-injection and cross-customer guards run before the P NLU path; indirect instructions embedded in merchant text are sanitized. The model prompt tells Gemini to ignore instructions inside customer and record blocks; the prompt loader escapes and length-bounds those blocks. Email, phone, card-number and document-number patterns are redacted before provider calls. Jev's injection cue is a second opinion, not permission to follow an instruction or change account scope. [API implementation](../../src/aclara/api/app.py), [prompt loader](../../src/aclara/llm/prompts.py), [NLU prompt](../../prompts/nlu/v4.md), [Jev report](typesafe-jev-comparison.md), [data provenance](../data-provenance.md).

The OpenRouter adapter requests strict JSON schema, `require_parameters=true`, `data_collection=deny` and `zdr=true`, with the selected provider pins and provider fallback disabled. Pydantic validates returned structure; retry/failure routing is bounded and recorded. A schema-valid answer can still be wrong, so deterministic rules remain authoritative. [Provider adapter](../../src/aclara/llm/providers.py), [client](../../src/aclara/llm/client.py), [route configuration](../../config/models.yaml).

For customer-facing text, the model can draft only `clarify` or `explain_status`. The [grounding verifier](../../src/aclara/agent/nlg/grounding.py) checks cited allowed fact IDs/sources, uncited numbers, dates, handles, case IDs, status and merchant claims, sensitive identifiers, injection echoes and prohibited promises. A failed draft gets at most one correction attempt, then an approved template; action and case-report wording always uses templates. This is a bounded fact/DLP check, **not** full semantic verification. Four live dev drafts changed delivered replies, and zero of those four tripped the verifier; that small sample cannot establish a zero violation rate. [Phrasing builder](../../src/aclara/agent/nlg/builder.py), [dev path study](live-dev-path-study.md).

## Development evidence, cost and latency

The 150-case, AI-authored and unreviewed NLU dev set is saturated and cannot independently select a model. With NLU v4 on that reused set, Gemini had 150/150 intent and 9/10 injection flags with 0/140 false flags; the Gemini–Jev union still had 9/10 and 0/140. Other risk cues lack independent gold. These are development measurements, not production safety or fairness estimates. [Model comparison](model-comparison.md), [Jev report](typesafe-jev-comparison.md).

The separate **20-conversation synthetic local real-P study** measured 39 API turns: turn p50/p95 **1.782/4.354 s**, sum-of-turns case p50/p95 **2.002/8.126 s**, and **$0.032765** known per-call provider cost in total (**$0.001638 mean per conversation**). Conservative cap charge was **$0.052947** because two forced, no-network Gemini failures retained reserves. One valid Grok fallback call was forced, so the sample does not estimate a natural fallback rate. The local ASGI path excludes deployed network, container and production database overhead; its objective pass was 11/20 before the subsequent Option A diagnosis. The phrasing comparison changed only 4/30 assessable final replies. [Live dev study](live-dev-path-study.md), [Option A analysis](dev-p-failure-analysis.md).

Before any real-route promotion, the lead must read back the deployed SHA, merged prompt hashes, provider pins, privacy terms, fresh prices and green acceptance gates. Every paid attempt, including Jev, retry and Grok fallback, reserves against a durable Postgres budget before the call; unknown usage retains its reservation. Operational review should track structured-output validity, Jev degradation, Grok fallback attempts and success, grounding/template fallback, per-language latency and cost, objective SAR, escalation and unsafe rates. The local timing above is not a production latency target. [Final plan](../evaluation/final-run-plan.md), [architecture](../architecture.md), [call accounting](../../src/aclara/llm/client.py).

## Known limitations and final-v2 slice plan

There is **no fluent-human pt-BR reviewer**: Sonnet reviewed 17 active AI-lane Portuguese strings, which is a model review. Sebastian's human **es-CL spot-check has n=9** from one author and single-annotator labels; it found 5/9 granular intent and 7/9 corrected core-slot exactness with the older v1 matcher. Those nine do not represent all Chilean Spanish, the broader Spanish variants, or current end-to-end P. The 150-case NLU labels and scenario texts are team-authored synthetic data; the 32-case dev suite was tuned and the newer confirmation set is still unused. Human judge calibration is incomplete. [PT review](pt-review.md), [es-CL review](result-review.md#human-spot-check-n9-es-cl), [Jev report](typesafe-jev-comparison.md), [dev analysis](dev-p-failure-analysis.md), [judge rubric](../evaluation/judge-rubric.md).

For final v2, report B1 and selected P on the same frozen cases. Slice first by **ES vs pt-BR**, then by tagged Spanish regional variant (**MX, CO, AR, CL where present**), and report mixed/code-switched language separately if present. For every slice, show case count and gold-based **SAR**, correct versus unnecessary **escalation**, and **any unsafe outcome** with its category; include both numerator/denominator and 95% intervals. Compare B1/P on paired cases, keep normal/ambiguous/human-required/security case mix visible, and flag small cells rather than interpreting a zero count as parity. Do not infer protected-group fairness from language alone, and do not change prompts or labels after seeing frozen outcomes. The plan's deterministic evaluator, repeat protocol and privacy rules govern the final report. [Final plan](../evaluation/final-run-plan.md), [evaluation harness](../evaluation/harness.md), [architecture](../architecture.md).

| Final-v2 slice | n and case mix | B1/P SAR | Correct / unnecessary escalation | Any unsafe rate and category | Interpretation |
|---|---|---|---|---|---|
| ES overall | TODO(results) | TODO(results) | TODO(results) | TODO(results) | TODO(results) |
| pt-BR overall | TODO(results) | TODO(results) | TODO(results) | TODO(results) | TODO(results) |
| ES-MX / ES-CO / ES-AR / ES-CL, where tagged | TODO(results) | TODO(results) | TODO(results) | TODO(results) | TODO(results) |
| Mixed/code-switched, if tagged | TODO(results) | TODO(results) | TODO(results) | TODO(results) | TODO(results) |

## Privacy and operational controls

Raw organizer rows, credentials and model reasoning are not committed or persisted in model-call records. The provider payload is a redacted customer message or allowlisted, masked facts from an approved response plan; metadata records contain route/model, prompt hash/version, usage, latency, cost and validation status, not raw prompts or completions. Private evaluation outputs, when authorized, remain under ignored `artifacts/`; data-use approval is required before organizer-derived facts are sent externally. [Data provenance](../data-provenance.md), [final plan](../evaluation/final-run-plan.md).

Gemini, Grok and Sonnet use OpenRouter routes that **request** ZDR and data-collection denial; the gateway still forwards to a provider, so endpoint/account settings must be verified at activation. Jev uses TypeSafe directly: its published terms say inputs are not used for training, but this standard account's **zero-data-retention status is unverified**. The Jev route receives only the redacted customer message for risk cues, and judges receive blinded redacted wording fields. No paid call or final-v2 result was created for this card. [Data provenance](../data-provenance.md), [Jev report](typesafe-jev-comparison.md).
