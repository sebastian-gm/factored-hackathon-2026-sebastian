# Slide assets

PNG: 1920 × 1080. SVG: editable text. Both formats use the same zero-based charts,
explicit denominators and direct labels. No organizer rows or held-out case content.

| PNG / SVG pair | Caption | Committed source |
|---|---|---|
| `v4-outcomes` | P passes 88/100 versus B1 62/100. SAR is 32/100 versus 22/100 overall, and 32/47 versus 22/47 among eligible cases; paired overall difference +10 pp, 95% CI +5 to +16. | [Official primary results](../../evaluation/final-v4-results.md#primary-b1-versus-p-gemini) |
| `v4-escalation` | Strict correct escalation: P 49/53 versus B1 38/53. Missed transfers: 4/53 versus 15/53; unnecessary transfers: 2/47 versus 11/47. | [Official primary results](../../evaluation/final-v4-results.md#primary-b1-versus-p-gemini) |
| `v4-safety` | Both full safety gates failed. Unauthorized-action flags: B1 2/98, P 2/100; unverified-success flags: 2/98, 4/100. Missing confirmation/OTP: 0/98, 0/100. Categories overlap; zero observed flags do not establish zero risk. | [Official safety gates](../../evaluation/final-v4-results.md#safety-gates), [saved-flag interpretation](../../evaluation/final-v4-safety-analysis.md) |
| `v4-latency-cost` | P turn p50/p95: 2.125/3.776 s. Primary model spend $0.229766056: about $0.0023 per evaluated case, $0.0072 allocated per SAR-resolved case. Local serving plus remote models; excludes repeats, judges and infrastructure. | [Official latency and cost](../../evaluation/final-v4-results.md#cost-and-latency) |
| `controls-ablation` | Paired dev study, 20 synthetic cases per arm: P 0/20 versus naive Gemini 2/20 unverified write-success claims. Other observed failure counts were zero; correct escalation was 6/6 in both arms. This tests a bundle of controls, not each control separately, and does not establish safety. | [Committed dev study](../../evaluation/controls-ablation.md) |
| `architecture` | Language and retrieval feed code-controlled policy, confirmation/OTP, scoped writes and independent readback; uncertainty reaches a verified human packet. Current source design is post-v4, not reflected in v4 numbers. | [Architecture](../../architecture.md), [conversation contract](../../../contracts/interfaces/conversation-policy-v3.md), [ADR-0017](../../adr/0017-drop-jev-from-live-path.md) |

V4 charts describe the historical **Gemini + Jev** system. They do not measure
the current Gemini/Grok source path, Azure browser latency or production readiness.
The two unauthorized-action flags per system include frozen reactive-reply/gold
conflicts; the saved-flag analysis found no observed authority bypass and does
**not** change the official counts. The safety chart shows selected categories;
use the full gate table before making an overall safety claim.

Controls ablation is post-v4 authored dev evidence, not held-out; missing
verification is not proof that a write failed. No new paid study was run.

Regenerate without model calls:
`uv run --extra data-ml python analysis/export_slide_assets.py`.
SVG metadata records its primary source file's SHA-256. No deck is included.
