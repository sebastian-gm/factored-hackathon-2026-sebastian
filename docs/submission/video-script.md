# Aclara — product pitch video draft

**Historical draft, superseded for filming:** use the
[v0.8.1 shot list and current narration cues](video-shot-list.md). This draft
predates final v4, the released staff queue and the live Jev-OFF configuration;
its pending-results, pending-charge and live-Jev narration is not current.

Target: no more than **3:00**, per [brief §16.4](../00-build-brief.md).
Narration and directions are separate below. Follow the [submission checklist](checklist.md)
before recording; only the deployed app appears as the live product.

## Narration

**N1 · 0:00–0:10 — Hook**

> You spot a charge you don’t recognize. You want an answer—and confidence that the next action is the right one.

**N2 · 0:10–0:20 — Meet Aclara**

> In our synthetic data, just 43.6% of complaint contacts resolve first time. Meet Aclara: a verified next step, in Spanish or Portuguese. All in one conversation.

**N3 · 0:20–0:45 — Explain**

> Here, a customer asks about a pending charge. Aclara finds the customer’s transaction and explains its status. Open “Why?” and the supporting record and policy rule are right there. The customer can see why the answer fits.

**N4 · 0:45–1:15 — Clarify and confirm**

> Now the description is ambiguous. Aclara asks which transaction fits. The customer reviews the amount, confirms the request, and receives a case number only after the system reads it back. Nothing moves forward until that choice is clear.

**N5 · 1:15–1:45 — Bring in a person**

> A stolen-card report takes a different path. The customer confirms the freeze after fresh verification. A human receives the facts, completed actions, and unanswered questions, with language and specialty routing visible. The conversation continues with context.

**N6 · 1:45–2:10 — Show the architecture**

> Gemini handles language, Grok backs up failures, and Jev adds a risk second opinion. Code controls identity, policy, and writes. Understand, decide, act, verify, escalate: inspect the calls, risk flags, and verified actions in Ops.

**N7 · 2:10–2:45 — Show the scorecard**

> Human recollections exposed a matching gap. After synthetic retraining, target-first matches rose from six to nine in nine checks. Gemini costs less than Claude on our development NLU workload. The final scorecard measures safety, resolution, latency, and conversation cost.

**N8 · 2:45–3:00 — Honest limits**

> This is a synthetic demo. Nine human checks are small evidence. The earlier mock run failed safety gates; final acceptance, broader language review, and production integration remain unfinished.

## Stage directions — not narrated

| Segment | What the judge sees |
| --- | --- |
| N1 | A project-generated unfamiliar charge and the customer's question. Start with the problem, without a title-card delay. |
| N2 | Cut to the **live deployed product at 0:10**. Briefly overlay the sourced FCR figure; retain the synthetic-bank label. |
| N3 | Authenticated ES persona asks about the supplied pending charge. Open the evidence drawer and point to the supporting record/rule. |
| N4 | Use the recording helper to rehearse the supplied PT ambiguous case. The release smoke reached clarification/handoff, so verify the choice path before recording; do not present that smoke as a dispute receipt. Show clarification and candidate selection, then the exact proposal and confirmation. Show the actual read-back receipt. Leave space for the product interaction. |
| N5 | Use the rehearsed fraud fixture. Show the fresh-verification transition without credentials, explicit freeze confirmation, then the authorized Agent Desk packet and actual route/fallback. |
| N6 | Trace the response through the execution stages. Briefly show the architecture visual from slide 3 and a harmless authored bypass request being refused. No thinking or raw prompt payloads. |
| N7 | Show slide 5's B1-versus-real-P and Gemini-versus-Claude scorecard. Until the approved final run exists, the `TODO(results)` cells stay visible. After results arrive, replace both scorecard and narration from their aggregate sources; keep this time slot and the total narration length. Never substitute mock timings or token prices. |
| N8 | Show slide 6: limits and production path. End on Aclara and the demo link. Put credentials only in the submission email. |

## Sources and edit rules — not narrated

The **43.6%** figure is `contact_reasons[Queja].fcr`, rounded from the
[pipeline aggregate](../data/problem-analysis-aggregates.json). The product paths and
control boundary come from the [API contract](../../contracts/interfaces/openapi.json)
and [architecture](../architecture.md). The six-to-nine result comes from the [v2 human check](../ml/model-card-charge-matcher-v2.md), using identical fresh NLU outputs for both matchers; no human case was used for training. Development NLU costs and model selection come from [model-comparison.md](../history/ml/model-comparison.md); Jev roles from [its comparison](../history/ml/typesafe-jev-comparison.md). Real-model deployment evidence is in the [release progress log](../history/status/progress-log.md). Final measurements must come from the approved aggregate
exports under the [evaluation protocol](../evaluation/eval-protocol.md).
The prior failure statement is supported by the
[corrected mock diagnostic](../history/evaluation/heldout-run01.md); remaining production
work is in [readiness](../production-readiness.md).

Timings are editorial targets, not measured latency. Rehearse the actual clip and
keep the limit segment to the final **15 seconds**. If final results change the
limit statement, update it with its source; retain every unresolved material limit.
A failed or unavailable live path must be represented honestly. Recording/export,
release SHA and access tasks belong in the [checklist](checklist.md).
