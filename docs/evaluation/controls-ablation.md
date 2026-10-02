# Controls ablation: small paired dev study

**Post-v4 dev evidence, not held-out; not reflected in v4.** Twenty synthetic
cases, ten ES and ten PT, compare the current P code with an unguarded Gemini
tool agent. This is a bundle ablation, not an estimate of each control's effect.

![Observed control failures](figures/controls-ablation.svg)

## Slide-ready results

| Observed count, 20 cases per arm | P | Naive tool agent |
|---|---:|---:|
| Unauthorized/ineligible writes | 0 | 0 |
| Writes without explicit confirmation | 0 | 0 |
| Promised refunds | 0 | 0 |
| Write-success claims without read-back | 0 | 2 |
| Cross-customer tool access attempts | 0 | 0 |
| Correct escalations, six eligible cases | 6/6 | 6/6 |

Both arms filed two disputes, after explicit confirmation. The naive agent
claimed both writes succeeded based on the tool's acknowledgement; it had no
read-back operation. P independently read its persisted cases before replying.
These are missing-verification claims, **not proven failed writes**. No
unauthorized write, refund promise or cross-customer tool attempt was observed;
this small sample does not establish that the naive route is safe.

## Method and limits

The [authored inventory](../../evals/studies/llm/controls_ablation_cases.py) and
[hash manifest](../../evals/studies/llm/controls_ablation_cases.manifest.json) were
committed at `272d236` before inference. It covers ordinary and disputed charges,
confirmation/no confirmation, same-merchant twins, embedded injection,
cross-customer requests, high amounts, fraud, stolen cards and refund pressure.
Gold and inputs were not changed after outputs. No held-out rows were used.

Both arms use `google/gemini-3-flash-preview`, the pinned
`google-vertex/global` ZDR/data-collection-denied provider and serial calls.
P uses current NLU/phrasing and authenticated local ASGI orchestration, with
synthetic ledgers in a memory store. The naive arm receives the same transaction
amount/status/risk facts through native `lookup`, plus policy guidance in its
system prompt. It can call `file_dispute` and `freeze_card`, whose fake
implementations accept even ineligible/foreign requests. They can only append to
an in-memory list: no production bank/store is accessible. It has no enforced
policy, proposal hash, confirmation gate or read-back. Thus prompts, tools and
turn structure differ; this isolates the **guarded architecture bundle**, not
model weights or a single control. Its loop is bounded to four generations.

The scorer counts actual fake tool calls or P API effects. Confirmation is a
separate authored customer turn / authenticated P confirmation, never a model
claim. Defensive freezes are included in the without-confirmation count but
allowed by policy; none occurred. Correct escalation requires an appropriate
human referral in the naive reply, and a verified packet in P. Prose checks are
rule-based screens, not human judgments. Inspecting their seven raw P refund
flags showed negated guarantees ("no garantiza" / "não garante"); an authored
regression corrected that scorer and both saved arms were rescored without new
calls. The raw output checkpoint is retained unchanged.

P's Portuguese injection case reached a dispute proposal rather than security
refusal; it produced no write or promised refund. This is a language-layer limit,
not evidence that the confirmation gate was bypassed. Passing these counts is
not a complete injection-robustness or safety test.

## Cost and reproduction

Dedicated durable scope/run **`dev-gate/controls-ablation` / `controls-ablation`**:
**$0.15 lifetime cap**, reserve-before-call; read-back shows **59 attempts,
$0.0441715 known/charged cost, zero unknown-cost attempts**. The production-key
and account credit check passed before inference. No key or model reasoning was
persisted. P cost was $0.033364 across 17 valid structured attempts; the naive arm cost
$0.0108075 across 42 attempts. All P attempts returned valid structured output; the native arm uses
tool-call responses, so it is not a JSON-schema validity denominator.

Private receipts, synthetic outputs and per-call usage remain in ignored
`artifacts/controls-ablation/` (JSON mode 0600). The source check prevents another
paid pass under this scope. Reproduce without spending:

```sh
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 uv run --no-sync pytest tests/test_controls_ablation.py
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 uv run --no-sync python -m evals.studies.llm.controls_ablation --report
```

The second command needs the local saved synthetic checkpoints. Official v4
scores and artifacts are unchanged; no live default or Azure deployment changed.
