# Round-two robustness and lean NLU protocol

**Frozen before any round-two product run or repair.** The
[60 authored conversations](../../src/aclara/llm/dev_robustness_round2_60.yaml),
[builder](../../src/aclara/llm/dev_robustness_round2_cases.py) and
[hash manifest](../../src/aclara/llm/dev_robustness_round2_60.manifest.json) contain
project-generated fixtures only. No organizer records, previous model output or
v4 input was consulted to author gold. The priority human-review/output-integrity
PR #77 is separate; any later paid baseline must pin its actual integration SHA.

## Frozen coverage and gold

Ten story families have six linguistic variants each: one es-CO, one es-AR,
one es-CL and three informal pt-BR voices. This yields 30 ES / 30 PT cases, not
sixty independent observations. Eighteen conversations have four scripted customer
messages, 42 have three. An independently confirmed write adds one turn; the
total limit is five. Reactive selection/clarification is available within that
same limit. Exhausting it remains a failed attempt, never an excluded case.

| Story family | Conversations | Independent expected outcome |
|---|---:|---|
| Amount/date corrected after an initial identification | 6 | File for the finally identified charge |
| Two unrelated charges in one message | 6 | Explain the known charge's status; file the denied one |
| Existing-case status plus a new unfamiliar charge | 6 | Read back the existing case; file only the new charge |
| Vague opening, then specific details, with typos | 6 | File after explicit denial and independent confirmation |
| Frustration without distress cues; embedded injection | 6 | Log the injection; ordinary dispute, no distress escalation |
| ES/PT switching, preference clarified, then recognition | 6 | Offer before recognition; explanation without a write |
| CO/AR/CL/BR slang, amounts in words, relative dates | 6 | File the stated charge after confirmation |
| Pesos/reais corrected to dollars; same-merchant currency twins | 6 | Ordinary pending-status explanation, no dispute offer |
| Polite refusal of the dispute offer | 6 | Cancellation, no write and no safe-resolution credit |
| Unsure after the offer, then a clear memory of the purchase | 6 | Explanation, no write |

Gold follows [ADR-0015](../adr/0015-post-v2-conversation-and-policy-contract.md)
and the [normative contract](../../contracts/interfaces/conversation-policy-v3.md):
36 filed, 18 explained, six cancelled. Explicit denial never substitutes for
confirmation/OTP/readback. A generic refusal is not recognition. Compound concerns
must satisfy both stated requests. Gold stays unchanged even when single-intent
or orchestration limitations prevent that; assign the failure to its owner.

ES-CL describes language only: its fixture uses MX banking rules, not a Chilean
policy implementation. Currency/FX rows, merchants and transaction twins are
explicitly authored; COP/ARS slang gets an explicit currency follow-up. Structural
validation checks all sixty against the frozen scenario interface, binds synthetic
identities and validates gold references, without running B1/P.

Freeze: case SHA-256
`8542b862d8af2439bfcf76968bbc52f7bce706aaf3977f5d0aff8cf336cd0904`;
materialized scenario SHA-256
`d90ddb883f5271569a343b42216206af2fb63fafeda1e10faf8010d35a70039d`.
The manifest also pins both builder files. Existing 40-case/confirmation fixtures
are untouched. Subsequent tests may protect the freeze; they must not revise it.

## Paid measurement and adoption gates

Paid work is **pending the orchestrator's exact durable scope/run confirmation**.
Expected scope is `dev-gate/pre-v4`, lifetime cap $1 shared with the lead; stop
when charged exposure plus a reservation would exceed $0.90. Every provider call,
retry, Grok fallback and Jev question must reserve under that same scope before
calling and settle with per-call cost/usage. Unknown costs retain their reserve.
No key-balance deltas, final-evaluation scopes or implicit deterministic recovery
after budget exhaustion may be used. Keys remain local and never enter output.

First measure current real P on all sixty and keep private per-case checkpoints
and all-attempt call records. Report overall/ES/PT/family pass, unsafe, required
and forbidden actions, injections/false flags, case/turn/NLU p50/p95 and measured
cost per attempted case. Diagnose AI-owned NLU/NLG vs lead-owned matching/state/
policy causes before repairs. Fix only the AI lane with new authored regressions.

Only then author v5.2 as a candidate: deduplicate instructions and shorten
examples without changing the intent/recognition/unfamiliarity contract. Compare
v5.1 and v5.2 on **dev no-fault 20, explain/offer confirmation 20, robustness 40,
round-two 60 and the now-development v3 100** (240 conversations per version).
Record immutable case hashes, implementation/config/prompt hashes, actual model
IDs/provider routes, temperature, timeout, retry settings and call token counts.
Keep every failed/timed-out attempt in cost and validity denominators.

Adopt only with complete comparable evidence: no per-set objective pass decrease,
no new unsafe outcome or loss of injection coverage, and lower pooled NLU-call
p50 **and** p95; disclose per-set and ES/PT latency changes as well. Incomplete
work or mixed historical/fresh timing cannot establish that gate. Keep v5.1 when
the candidate fails or the budget stops the comparison. Report all before/after
numbers as development results, with correlated-family caveats; never as v4.

Budget feasibility is uncertain. The previous study's post-fix NLU calls cost
about $0.00193 each ([source](nlu-robustness-post-v3.md)); 198 scripted new-set
messages alone imply roughly $0.38 NLU before phrasing/Jev/retries. A wholly fresh
two-version, 240-case comparison may exceed the shared allowance. This is an
estimate, not authorization to exceed it. Preregister actual coverage, stop
conservatively, and report incomplete comparisons without adopting v5.2.

## Current evidence

Structural freeze verified; zero product executions before the freeze and zero
paid calls. Mock execution and real before/after measurements are pending. No NLU
prompt or default model changed. No v4 input or result was opened.
