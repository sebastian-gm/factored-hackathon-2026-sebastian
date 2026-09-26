# AI model comparison protocol

No default model has been chosen. Round 1 compares Gemini Flash-Lite/Flash, DeepSeek, Qwen, and Grok on the **same labeled dev cases**, cheapest first. Round 2 reserves Claude Haiku/Sonnet/Opus for the final test. `src/aclara/llm/comparison.py` computes intent accuracy, slot F1, valid JSON rate, p50/p95 call latency, and cost per case from metadata-only call records. ES/PT quality requires separate human ratings on a 1–5 rubric; it is never inferred from the model's own claims. Invalid structured output is counted before the one retry; fallback output is not credited as model accuracy.

| Model | Intent accuracy | Slot F1 | Valid JSON | ES quality | PT quality | p50 / p95 latency | USD/case |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemini Flash-Lite | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Gemini Flash | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DeepSeek | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Qwen | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Grok | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Claude Haiku | Final test | Final test | Final test | Final test | Final test | Final test | Final test |
| Claude Sonnet | Final test | Final test | Final test | Final test | Final test | Final test | Final test |
| Claude Opus | Final test | Final test | Final test | Final test | Final test | Final test | Final test |

The [dated price table](../../config/pricing.yaml) is for pre-run cost estimates. OpenRouter routing can change the endpoint and billed price; reconcile recorded usage/cost with its invoice before reporting measured cost. Direct DeepSeek and Qwen entries are intentionally unpriced and cannot pass the real-call gate until their own rates are verified. Gemini free-tier cost is $0 within its quota, but its data terms differ from paid service.

Before the first paid-model run, Sebastian receives the planned case count, token/cost estimate, per-run budget, and this table. The real-call gate requires `LLM_REAL_CALLS_APPROVED=1`, an API key in the local `.env`, and a positive per-run budget. The default `LLM_PROVIDER=mock` remains in place until Sebastian has reviewed the measured table.
