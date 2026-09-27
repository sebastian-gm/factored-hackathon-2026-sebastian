# TypeSafe Jev typed-judgment development comparison

**2026-09-27 synthetic dev check.** Sebastian asked for `jev-1.13.0` as an intent/risk-cue challenger and a second subjective judge. Gemini 3 Flash remains the selected NLU/phrasing default; Sonnet 5 remains the judge candidate; neither choice changed. The frozen 200-case held-out suite was not used or run. This was a separately approved **$1 maximum** across new OpenRouter and TypeSafe calls. New known usage-based cost was **$0.217601**: Gemini v4 **$0.211601**, Jev NLU **$0.005877**, and Jev judge smoke **$0.000124**. All 303 new calls returned usage; there were no unknown-cost attempts or retries. The prior Sonnet smoke cost **$0.008042** under its earlier separate approval and was reused without a new Sonnet call. No shared key-level balance delta was assigned to either provider.

## Protocol and typed scope

The same separate, team-authored **150-case unreviewed NLU dev set** (90 Spanish, 30 Brazilian Portuguese, 30 mixed) was used for both models. The Gemini baseline used exact ID `google/gemini-3-flash-preview`, [NLU prompt v4](../../prompts/nlu/v4.md), strict `ExtractedNlu` JSON schema, and OpenRouter ZDR `google-vertex/global` pinned. Jev used exact versioned ID `jev-1.13.0` through the TypeSafe Python SDK. One `Choice` over the nine §5.2 intents and six independent `Noul` questions for lost/stolen, regulator, legal, distress, injection suspicion, and explicit human request were asked together per case. The [typed question definitions](../../src/aclara/llm/typesafe_questions.py) encode Sebastian's denial-versus-recognition distinction. `Noul >= 0.5` was fixed as a flag before the run; unverified cues are reported as counts only. No amount/date/merchant slot, arithmetic, phrasing, policy decision, identity, authorization, or write action is delegated to Jev.

Intent accuracy counts missing finals as wrong; none occurred. Expected calibration error (ECE) uses ten fixed-width bins on valid finals. Jev contributes the selected `Choice` probability; Gemini contributes its self-reported `intent_confidence`, so the numerical ECE comparison is descriptive rather than proof that the two confidence scales are interchangeable. Injection truth is the ten pre-authored fixture tags; 140 other cases are negatives. Latency is measured per API call including network, excluding process setup. Costs use OpenRouter per-call billed usage/cost and Jev per-call input tokens at TypeSafe's published [$0.042 per million input tokens](https://docs.typesafe.ai/models), with free output. The checkpoints under ignored `artifacts/typesafe/` contain IDs, labels, typed probabilities/flags, usage, cost and timing, not messages, keys, completions or model reasoning.

| Model and language | n | Intent correct (Wilson 95%) | ECE, 10 bins | Injection TP / gold | False flags / negatives | p50 / p95 latency | Known USD/case |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemini v4, all | 150 | 150/150 (97.5–100%) | 0.0253 | 9/10 | 0/140 | 1.897 / 2.224 s | $0.001411 |
| Jev, all | 150 | 146/150 (93.3–99.0%) | 0.0171 | 6/10 | 0/140 | 0.090 / 0.150 s | $0.0000392 |
| Gemini v4, ES | 90 | 90/90 (95.9–100%) | 0.0229 | 6/6 | 0/84 | 1.916 / 2.224 s | $0.001405 |
| Jev, ES | 90 | 89/90 (94.0–99.8%) | 0.0210 | 4/6 | 0/84 | 0.090 / 0.138 s | $0.0000392 |
| Gemini v4, PT | 30 | 30/30 (88.6–100%) | 0.0263 | 1/2 | 0/28 | 1.877 / 2.180 s | $0.001408 |
| Jev, PT | 30 | 28/30 (78.7–98.2%) | 0.0457 | 1/2 | 0/28 | 0.088 / 0.164 s | $0.0000391 |
| Gemini v4, mixed | 30 | 30/30 (88.6–100%) | 0.0313 | 2/2 | 0/28 | 1.861 / 2.310 s | $0.001429 |
| Jev, mixed | 30 | 29/30 (83.3–99.4%) | 0.0300 | 1/2 | 0/28 | 0.094 / 0.152 s | $0.0000392 |

All **300/300 NLU provider attempts** returned valid typed or schema-conformant finals. Jev's four intent errors were all authored `charge_inquiry` cases: three were predicted `dispute_charge` (one each ES, PT and mixed), and one PT inquiry was predicted refund/reversal status. That boundary matters under Sebastian's label rule. Jev was about **36× cheaper** and **21× faster at the median** per NLU case here, but it missed four of ten injection flags versus Gemini v4's one. Gemini's v4 injection recall on this reused dev set is **9/10**, one lower than its historical v3 round-two result; neither small authored sample establishes broader attack resistance. The other Noul risk cues were emitted, but this suite has no independent gold labels for them, so their accuracy is not claimed. For context, Jev flagged 5 lost/stolen, 0 regulator, 0 legal, 3 distress and 5 explicit-human cases; Gemini flagged 7, 0, 0, 2 and 5 respectively.

## Jev as a second subjective judge

Jev received the **same three synthetic items** as the saved Sonnet 5 judge smoke: requested locale, customer message, delivered reply and handoff summary, without objective gold or action facts. Four independent `Score` questions use the [rubric's](../evaluation/judge-rubric.md) five descriptive anchors. TypeSafe returns a zero-based probability-weighted score; for ordinal agreement, code maps it to rubric scores 1–5 by adding one and rounding half-up, while preserving the fractional score privately. Sonnet's previously saved integer scores were reused. Objective outcomes were never judged by either model.

| Dimension | Exact agreement | Within one point | Quadratic-weighted κ | Paired n |
|---|---:|---:|---:|---:|
| Language/register | 2/3 | 3/3 | 0.667 | 3 |
| Clarity | 2/3 | 3/3 | 0.667 | 3 |
| Empathy | 3/3 | 3/3 | 1.000 | 3 |
| Handoff-summary usefulness | 1/3 | 3/3 | 0.8125 | 3 |

Jev's three judge calls cost **$0.000124** from input-token usage and had 0.132-second median API latency; Sonnet's prior three calls cost **$0.008042**. These three pairs are too few to validate a judge or interpret κ as stable, and Sonnet agreement is not human agreement. Sebastian's ignored 50-sample human sheet remains blank. Do not replace Sonnet or use Jev judge scores for objective acceptance without separate human validation and approval.

The [TypeSafe data-term record](../data-provenance.md) notes that its published policy says inputs are not used for training, while standard-account zero retention is not verified. TypeSafe's [model page](https://docs.typesafe.ai/models) identifies English as its strongest language, consistent with treating these ES/PT outcomes as a measured limitation rather than assuming parity. This task sent only team-authored synthetic fixtures. Jev is a typed-judgment challenger, not a selected provider or production route.
