# Language-layer model card

**What this shows:** What the language models can do and where code keeps control.<br>
**Result:** AI interprets customer language; code controls access, eligibility and bank actions.<br>
**Limits:** Development studies are separate from the final evaluation, and fluent-human Portuguese review is incomplete.

<details>
<summary>Technical details and evidence</summary>

> **superseded by v4 (2026-10-01)** — Earlier evaluation/release claims on this page are historical; use the [current summary](../../README.md) and [official v4 results](../evaluation/final-v4-results.md). [Post-v4 fixes](../evaluation/post-v4-release-notes.md) are **not reflected in v4 numbers**.



**Post-v4 update:** live Jev risk union is disabled in production config; Gemini
risk cues and deterministic guards remain. The next Azure release is pending.
Historical Jev study/judge evidence below is retained; v4 was measured with Jev.
[ADR-0017](../adr/0017-drop-jev-from-live-path.md). Status explanations are now
template-only; blank-plan clarifications retain guarded generation. These are
**post-v4 fixes, not reflected in v4 numbers**. The older dev measurements below
describe their pinned releases, not the current source configuration.

Historical dev status: **post-v3 development candidate**, including AI PRs [#65](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/65) and [#66](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/66). This card describes their behavior; it does not attest to a deployed release. The official v3 result remains pinned to `e12efc73be64f8355aa9f177f08a04337593616c`. V3 has since become dev data; this older study preceded v4. Current official v4 scores remain unchanged by the post-v4 note above. [Official v3 report](../evaluation/final-v3-results.md), [post-v3 development analysis](../evaluation/post-v3-fixes.md).

## Intended use and authority

The language layer interprets authenticated customers' charge questions and optionally rephrases code-approved explanations in Latin American Spanish and Brazilian Portuguese. It extracts expressions and intent, observes risk cues, and supports explain → offer → recognition/denial conversations. Subjective judges assess wording offline. It is out of scope for general financial advice, unsupported languages, other customers' records, autonomous banking actions or production fairness certification. [Architecture](../architecture.md), [ADR-0015](../adr/0015-post-v2-conversation-and-policy-contract.md).

**Authority stays in code.** Models cannot authenticate a customer, grant access, select an account scope, decide policy eligibility, authorize a dispute or card block, promise a refund, verify a write or grade objective outcomes. Code normalizes dates/amounts/currencies, matches only scoped transactions, and checks policy, proposal hash, expiry, fresh OTP, explicit confirmation, idempotency and committed readback. `recognition` and `customer_confirms` are observations, never write confirmation. [NLU normalization](../../src/aclara/agent/nlu/structured.py), [API](../../src/aclara/api/app.py), [workflows](../../src/aclara/api/workflows.py).

## Models and roles

| Role | Exact model and route | Boundary |
|---|---|---|
| Main NLU and eligible phrasing | `google/gemini-3-flash-preview`, OpenRouter `google-vertex/global` | Strict-schema `ExtractedNlu` and grounded `ReplyDraft`; mock remains the default activation mode. |
| Historical risk second opinion; disabled live | TypeSafe `jev-1.13.0` | Retained opt-in study code uses six `Noul` questions and Gemini OR Jev ≥0.5. It is no longer enabled by the production config or implicitly by the Gemini model ID. Historical records retain flags/probabilities and degradation. |
| Failure-only fallback | `x-ai/grok-4.20`, OpenRouter `xai/zdr` | Same schema/grounding boundary, only after Gemini exhausts bounded attempts. |
| Subjective judges | `anthropic/claude-sonnet-5`, OpenRouter `google-vertex/global`, plus `jev-1.13.0` | Language/register, clarity, empathy and applicable handoff-summary usefulness, each 1–5. Jev uses one `Score` per dimension. Blinded redacted wording only; objective gold and authorization are excluded. |

The Gemini route has a **6 s first-attempt timeout**, a configured **20 s retry timeout**, maximum **2048 output tokens**, and a **45 s total generation deadline** in the durable runtime. These are model-call bounds, not an end-to-end conversation SLA. The current Sonnet judge cap is **1024 output tokens**, increased after v3's 256-token cap truncated two attempts. Sonnet frontier system comparison was **off** in v3; it is not the customer-facing default. [Routes](../../config/models.yaml), [AI boundary](../../src/aclara/agent/ai.py), [client](../../src/aclara/llm/client.py), [judge cap](../../evals/studies/llm/final_run.py), [Jev report](typesafe-jev-comparison.md), [rubric](../evaluation/judge-rubric.md), [v3 report](../evaluation/final-v3-results.md).

## Prompt pins and language handling

SHA-256 below covers complete UTF-8 source bytes, including prompt front matter. Source pins do not establish which code is deployed. [Prompt loader](../../src/aclara/llm/prompts.py).

| Purpose | Version/source | SHA-256 |
|---|---|---|
| NLU | [`nlu@v5.1`](../../prompts/nlu/v5.md) | `e40182de2f232932a12d61d722be5e6356d787217048378fbc2a84f330d241cc` |
| Phrasing | [`phrase@v2.1`](../../prompts/phrase/v2.md) | `96089ad7985a334b8c6b974298856d939e554d431f04c6c1e7a434d75ec71fd9` |
| Sonnet judge | [`subjective-response-judge@v1`](../../prompts/judge/v1.md) | `8f62c925c51276da2420c42364ea38b0fbe47b8911286b0b1548feb79a19282e` |
| Jev questions | [`jev-questions-v1`](../../src/aclara/llm/typesafe_questions.py) | `d5291e12c56a7f0fbea2ca4f8aca70e7be6d32711df87bc702bbe339aeb5ba29` |

NLU v5.1 distinguishes bare non-recognition (`charge_inquiry`, `unfamiliar_charge=true`) from explicit denial/request to file (`dispute_charge`, flag false). Neutral what/why/status questions, including named-charge suffixes and ES/PT articles, have flag false. Other semantic unfamiliarity judgments are preserved rather than erased by a keyword list. Recognition is interpreted only in the code-supplied waiting context; isolated yes/no stays unsure. [Explain/offer implementation](dev-explain-offer-v5.md), [NLU implementation](../../src/aclara/agent/nlu/structured.py).

Phrase v2.1 receives the **actual approved `plan.reply`** for explanations. Code-supplied clarifications, including bilingual language help and recognition questions, remain deterministic and exact; the existing recognition guard remains. A blank clarification can use the generic template and optional phrasing. The same approved text is the fallback for explanations. [Builder at PR #66](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/blob/b059920e78c6a299451b38b0860c78acdd704f48/src/aclara/agent/nlg/builder.py), [21 authored language/clarification regressions](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/blob/b059920e78c6a299451b38b0860c78acdd704f48/docs/ml/pr-62-ai-review-fixes.md).

The v2.1 source candidate sends localized status/type labels to the phrase model while preserving canonical source facts for grounding. Model drafts with word-internal digit corruption or English status/machine enums fall back after bounded correction; exact cited merchant names, verified case IDs and masked suffixes retain their existing boundaries. NLU postprocessing also maps stated ES/PT transaction kinds to the six ledger types, with fees grouped under Adjustment and unknown kinds missing. These are zero-cost mock/replay fixes, not a deployment attestation or new official pass rate. [Diagnosis and dev replay](live-language-failure-analysis.md).

Contextual language evidence returns **es / pt / uncertain**, excluding domains/URLs and supplied trusted merchant names. Shared `com` and `sim` cannot determine language; short valid PT such as “Informe valor e moeda.” is recognized. Missing or conflicting evidence is uncertain, and NLG rejects only confident opposite-language evidence. The existing two-language NLU wrapper retains its ES default for uncertain input. This is a conservative heuristic, not calibrated language confidence or fluency assessment. [Detector at PR #66](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/blob/b059920e78c6a299451b38b0860c78acdd704f48/src/aclara/agent/nlu/rules.py), [mock evidence](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/blob/b059920e78c6a299451b38b0860c78acdd704f48/docs/ml/pr-62-ai-review-fixes.md).

## Injection, grounding and privacy

Direct injection/cross-customer guards run before NLU; merchant instruction text is sanitized. Prompt blocks are escaped and length-bounded, and customer/record/response-plan content remains untrusted data. Sensitive identifiers are redacted before provider calls. Jev injection suspicion cannot expand scope or override controls. Strict JSON and Pydantic validate structure, not truth. [API](../../src/aclara/api/app.py), [prompt loader](../../src/aclara/llm/prompts.py), [NLU prompt](../../prompts/nlu/v5.md).

The grounding verifier checks allowlisted cited fact IDs/sources, uncited numbers/dates/identifiers/status/merchant claims, sensitive identifiers, injection echoes and prohibited promises. Unsafe drafts get at most one correction, then approved text/template. Actions, case reports and the grounded ES/PT dispute offer use deterministic wording. This is a bounded fact/DLP verifier, not complete semantic verification. [Verifier](../../src/aclara/agent/nlg/grounding.py), [builder](../../src/aclara/agent/nlg/builder.py).

No raw organizer rows, credentials or model thinking enter committed evidence or model-call journals. Normal execution stores usage, cost, latency, prompt hashes, validation status and necessary structured decision metadata, including risk flags/probabilities; raw row data and reasoning are not journaled. Authorized validated evaluation outputs remain in ignored private `artifacts/`. Provider inputs are redacted messages or allowlisted masked facts; organizer-derived external use requires data approval. Gemini/Grok/Sonnet requests specify strict provider pins, `data_collection=deny`, `zdr=true`, `require_parameters=true` and no gateway provider fallback. These request ZDR; activation must verify endpoint/account terms. TypeSafe says inputs are not used for training, but this standard account's ZDR status remains **unverified**. [Provider adapter](../../src/aclara/llm/providers.py), [call journal](../../evals/studies/llm/final_run.py), [provenance](../data-provenance.md), [Jev report](typesafe-jev-comparison.md).

## Evidence, cost and latency

The official **v3 primary result is P 77/100 versus B1 52/100**. In-scope SAR is **39% versus 28%**, a paired **+11 pp (95% bootstrap CI +5 to +17)**. Neither system passed the complete safety gate: fraud/regulator recall was 2/5 P versus 1/5 B1, and required readbacks 67/74 versus 58/74. P had zero observed critical unsafe predicates in 100 cases (95% upper bound 3.70%), which is not proof of safety. Judges completed only 28/60 planned pairs; human calibration remains unscored. These official numbers precede later development fixes. V3 is now **seen dev data**; the reported post-hoc 100/100 is a regression result and does not replace 77/100. [Official v3 report](../evaluation/final-v3-results.md).

PR #65's **40-conversation synthetic robustness set was frozen before fixes** (20 ES, 20 PT). It covers typos, slang, spoken amounts, relative dates, twins, mind changes, case status, human-plus-charge, embedded injection and mixed ES/PT. [Committed robustness study](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/blob/5ec47ce145c72e4bee09d80c74deef53dbfccf6b/docs/ml/nlu-robustness-post-v3.md).

| Robustness measurement | Before | After |
|---|---:|---:|
| Conversation success, 95% Wilson interval | 39/40; 87.1–99.6% | 39/40; 87.1–99.6% |
| ES / pt-BR success | 19/20 / 20/20 | 19/20 / 20/20 |
| Opening amount/date normalization failures | 9 | 0 |
| Clarification responses | 15/83 | 6/74 |
| Unsafe / forbidden cases | 0 / 0 | 0 / 0 |
| Embedded injection safely handled and logged | 4/4 | 4/4 |
| JSON valid over all OpenRouter attempts | 89/89 | 75/75 |
| Valid Jev attempts | 59/59 | 50/50 |
| Case p50 / p95 | 7.877 / 12.195 s | 5.423 / 12.273 s |
| Turn p50 / p95 | 4.025 / 7.462 s | 4.023 / 8.476 s |
| Known per-call cost / conversation | $0.003113721 | $0.002659596 |
| Total known provider cost | $0.124548836 | $0.106383848 |

Code fixed eight spoken amounts and a PT previous-weekday normalization defect; success was already achieved via clarification. The remaining failure was a lead-owned selection guard bypassing the required offer. Injection inputs were intercepted by code, so 4/4 is not model injection-classification accuracy. These single before/after runs do not establish causal latency improvement: p95 did not improve. Local ASGI timings include model/budget round trips but exclude production serving reads. Grok was not invoked. [Robustness diagnosis and bounds](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/blob/5ec47ce145c72e4bee09d80c74deef53dbfccf6b/docs/ml/nlu-robustness-post-v3.md).

For comparison, official v3 P case p50/p95 was **7.432/13.704 s**, turn **4.118/7.878 s**, and primary-pass cost **$0.00237687544/case**. That run included workstation-to-Azure Postgres serving reads and preceded request caching; it is not directly comparable to the local study. Cost always comes from per-call usage/cost fields, never key-level balance changes. Every paid attempt reserves in durable Postgres; unknown costs retain reserves. Track validity, Jev degradation, Grok fallback, grounding fallback, per-language latency/cost and objective outcomes before promotion. [V3 cost/timing](../evaluation/final-v3-results.md), [accounting](../../src/aclara/llm/client.py).

## Limits and fairness slices

There is **no fluent-human PT reviewer**; cross-vendor copy reviews are model-reviewed. The human es-CL spot-check was **n=9**, one author/annotator, with older-matcher intent 5/9 and core slots 7/9; it is not current population accuracy. Data and gold are synthetic, the 32/150-case NLU sets were tuned, v3 is now dev, and the 40 robustness cases were authored by this lane. Five successful es-CL robustness cases use an MX/USD banking fixture, not Chilean policy. Human judge calibration remains incomplete. [Copy review](pt-review.md), [es-CL spot-check](result-review.md#human-spot-check-n9-es-cl), [NLU comparisons](model-comparison.md), [v3 limitations](../evaluation/final-v3-results.md).

Existing v3 language slices are descriptive evidence, not a fairness certification:

| Slice | n | B1 / P SAR (95% CI) | Correct escalation B1 / P | Unnecessary escalation B1 / P |
|---|---:|---|---|---|
| ES | 48 | 22.9% (13.3–36.5) / 37.5% (25.2–51.6) | 10/20 / 16/20 | 12/28 / 5/28 |
| pt-BR | 48 | 31.2% (19.9–45.3) / 39.6% (27.0–53.7) | 10/19 / 13/19 | 11/29 / 6/29 |
| Mixed | 4 | Both 50.0% (15.0–85.0) | 0/1 / 1/1 | 0/3 / 0/3 |

Both systems observed zero critical unsafe predicates across their completed v3 cases; B1 nevertheless had two materially incorrect outcomes overall. The committed report does not give per-language counts for every unsafe category. Small mixed/dialect cells and unreviewed PT do not support claims of parity. [V3 slices and unsafe categories](../evaluation/final-v3-results.md).

For v4, preserve the independent freeze and report paired B1/P counts, policy mix and 95% intervals for ES, pt-BR, mixed and tagged MX/CO/AR/CL variants. Report per-language **SAR**, correct/missed/unnecessary escalation, **any unsafe outcome and each category**, cost and latency. Interpret small cells explicitly; language is not a proxy for protected-group fairness. Do not tune on frozen outcomes. [Evaluation protocol](../evaluation/harness.md), [architecture](../architecture.md).

| Pending independent slice | Counts/mix | SAR | Escalation | Unsafe categories | Cost/latency |
|---|---|---|---|---|---|
| V4 ES / pt-BR / mixed | TODO(results) | TODO(results) | TODO(results) | TODO(results) | TODO(results) |
| V4 regional variants, where tagged | TODO(results) | TODO(results) | TODO(results) | TODO(results) | TODO(results) |

</details>
