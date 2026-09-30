# Post-v3 authored NLU robustness study

## Preregistered protocol

The AI lane authored and structurally validated 40 entirely synthetic dev
conversations before running P or fixing language behavior. Gold comes from
[ADR-0015](../adr/0015-post-v2-conversation-and-policy-contract.md), not model
outputs. Neither the inputs nor gold may change after this freeze. No v4 data
was opened. This is a development study, not a held-out evaluation.

The [manifest](../../src/aclara/llm/dev_robustness_40.manifest.json) freezes
the authored YAML, builder and materialized ScenarioV2 hashes. ES has five
cases each of es-MX, es-CO, es-AR and es-CL; pt-BR has twenty. The shared
ScenarioV2 and bank-country enums have no Chile entry, so es-CL speech uses a
synthetic MX/USD banking fixture while its locale remains AI-owned metadata.
This measures language understanding, not Chilean banking policy.

Overlapping slices cover typos (11), es-CL slang (5), amounts in words (8),
relative dates (8), same-merchant twins (8), changing one's mind after an offer
(4), existing-case status (4), human request plus charge (4), embedded injection
(4), and mixed ES/PT (4). Outcomes are 16 filed disputes, 14 explanations,
two cancellations, four case-status reports and four human escalations.

Measure real P at baseline `32587c9`, then the same immutable conversations
after narrowly scoped NLU/NLG fixes. Use the existing bound ASGI execution path
and independently read back actions; no Azure customer or organizer rows.
Gemini 3 Flash remains primary, Jev risk union remains enabled, and Grok stays
failure-only fallback. No model-selection or judge experiment is authorized.

Every paid attempt, including retries and Jev, reserves against the existing
`dev-gate/post-v3` / `post-v3` durable scope. Before each new reservation,
atomically check that charged exposure plus that reserve is at most **$0.90**.
The scope's unchanged lifetime cap is $1, shared with the lead. Initial readback
was **$0.40238433** including retained reserves; known usage was $0.36640233.
Estimated additional exposure for both measurements is $0.25–$0.40.

Report all-case success with 95% Wilson intervals, ES/PT and feature slices,
unsafe predicates and injection-event coverage, case latency p50/p95, and
known per-call cost. Unknown provider usage retains its reserve but is never
reported as billed cost. Keep outputs and call evidence in ignored mode-0600
artifacts; commit aggregates only. Latency excludes production Postgres and
workstation-to-Azure serving reads but includes model and budget round trips.

## Results

Pending baseline measurement. The freeze has structural validation only;
no B1/P execution or output-informed changes preceded it.
