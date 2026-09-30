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
Freeze commit: `eaef1166ae4f90934332201b437bd14f3f22a79a`.

## Paid measurement and adoption gates

At preregistration, paid work awaited the orchestrator's exact durable scope/run
confirmation; the confirmed scope and completed/partial runs are recorded below.
Scope is `dev-gate/pre-v4`, lifetime cap $1 shared with the lead; stop
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

At PR #80's preparatory checkpoint there were zero product executions before
the freeze and zero paid calls. After the freeze, all sixty ran once through P's real in-memory state
machine using deterministic **mock** NLU. This checks fixture executability and
the mock fallback; it does not measure Gemini or predict real-model accuracy.

| Mock-only check | All | ES | PT |
|---|---:|---:|---:|
| Attempts | 60 | 30 | 30 |
| Objective pass | 19 | 9 | 10 |
| Unsafe findings | 0 | 0 | 0 |

Outcomes: 13 filed, six explained, 41 escalated. All attempts completed without
execution exceptions; cost $0 and no provider calls. Private checkpoints and
corrected summary: `artifacts/dev-pre-v4/round2-mock/`. The harness's first summary
mistakenly counted a nonempty unsafe map as true; the corrected aggregation counts
its actual boolean findings, protected by an authored regression. Case execution
records and frozen gold were not changed or rerun to correct that summary.

The orchestrator confirmed the durable scope `dev-gate/pre-v4`, run `pre-v4`,
with a $1 shared lifetime cap and a $0.90 exposure stop. Initial readback showed
zero reservations and zero charged exposure. The real-P driver reserves and
settles each Gemini/Grok/Jev attempt through that exact scope; unknown usage
retains its reservation. It pins a clean implementation commit, frozen inputs,
model/price configuration and prompts before starting, and stores call-level
usage and validated outputs only in private ignored artifacts. Per-conversation
cost sums that conversation's calls, never a key-balance delta or the reused
client's lifetime total. The baseline includes the separately reviewed PR #77
output-integrity guard; that PR is not assumed merged or deployed.

## Real baseline and budget-stopped follow-up

Production prompt **v5.1 remains active**; default Gemini and failure-only Grok
are unchanged. Sequential real P used Gemini/Jev, the same scorer/reactive API,
fresh in-memory bank state, confirmation and readback. Both runs used the original
60 frozen definitions, with no gold or builder change. No v4 was opened.

| Measurement | Before: all 60 | Repaired: completed 47 only |
|---|---:|---:|
| Implementation | `0161c3a` | `331fb57` |
| Objective pass | 15/60; 25.0% (Wilson 15.8–37.2%) | 9/47; 19.1% (10.4–32.5%) |
| ES / PT pass | 9/30 / 6/30 | 6/24 / 3/23 |
| Unsafe finding cases | 1/60 | 0/47 |
| Forbidden actions | 0 | 0 |
| Embedded injection logged | 6/6 | 6/6 |
| Filed / explained / escalated | 18 / 9 / 33 | 19 / 2 / 25, plus one safe-failure handoff |
| Structured JSON / **all OR attempts** | 169/171 (98.8%) | 123/148 (83.1%) |
| Jev valid judgments | 140/140 | 105/105 |
| Provider errors / unknown-cost attempts | 2 / 2 | 25 / 25 |
| Known cost from per-call fields | $0.285517676 | $0.205724188 |
| Known cost / completed conversation | $0.004759 | $0.004377, includes interrupted-case calls |
| NLU attempt p50 / p95 | 2.160 / 2.939 s | 2.182 / 3.228 s |
| Turn p50 / p95 | 3.800 / 6.597 s | 3.823 / 7.254 s |
| Case p50 / p95 | 7.955 / 23.685 s | 8.529 / 23.348 s |

**These unequal denominators are not a before/after improvement estimate.** On
the common 47 completed cases, both versions pass 9/47, with one pass-to-fail
and one fail-to-pass flip; both changed cases used degraded NLU. Both have zero
unsafe findings on this paired subset. The baseline's unsafe polite-refusal case
is outside the completed follow-up, so zero after does **not** prove its real
model outcome was fixed. Seventeen authored regressions, including a saved-style
recognition judgment, verify the correction without paid calls.

NLU timing includes Gemini **and NLU fallback** attempts, including failures;
attempts are clustered by conversation for bootstrap uncertainty. Original
private summaries had a single-cluster bootstrap and excluded fallback from this
one latency field; corrected aggregate receipts recompute that field from the
unchanged journals, without rerunning/rescoring or altering execution evidence.
Artifacts: `artifacts/dev-pre-v4/round2-real/{before,after}/`, with corrected
bootstrap receipts beside original summaries. Incomplete case 48 retains its
calls/cost and is not presented as a completed conversation or safety assessment.

### Why the follow-up stopped

Durable readback: **$0.87148777 charged/reserved**, **$0.49124327 known cost**,
564 reservations, **27 unknown-cost reservations retained**. The next conservative
reservation would cross the $0.90 stop; it was denied before a request. Per-call
known totals differ from durable known spend only by per-reservation upward
rounding to eight decimals. No key-balance delta was used to calculate cost, no
unknown attempt was set to zero, and no more paid call was made. Cumulative
charged/reserved exposure including prior scopes: $5.49196004 / $12; infra excluded.

Before errors were two NLU attempts; follow-up errors were Gemini NLU 16,
Gemini phrasing one, and Grok fallback eight. Three follow-up failures lasted
about 6.05 s, consistent with the first-attempt timeout; 22 lasted 0.10–0.74 s,
consistent with immediate rejection. Old records did not preserve HTTP codes,
so their exact individual causes cannot be established retrospectively.

Zero-cost account-health GETs at 2026-09-30 22:23 UTC verified that the worktree's
key still had limit available, while **account credits were exhausted**. This
supports billing rejection as an inference for the later short failures; it does
not prove a 402 code for every old attempt. No secret or balance was displayed.
Public [Gemini endpoint metadata](https://openrouter.ai/api/v1/models/google/gemini-3-flash-preview/endpoints)
and [Grok endpoint metadata](https://openrouter.ai/api/v1/models/x-ai/grok-4.20/endpoints)
still listed the pinned routes, structured output support and matching prices at
the read-only check; that does not establish account-level call availability.
Private metadata receipts are under `artifacts/dev-pre-v4/provider-diagnostics/`.
Future records now retain only `http_402`, `http_429`, `timeout`, `network_error`
or `model_failure`, never exception bodies, headers, URLs or model thinking.

## Failure owners and fixes

Speech variants are `co`, `ar`, `cl`, `br1`, `br2`, `br3` under
`round2.<variant>.<family>`. The immutable baseline has 45 failed cases:

| Family | Pass / 6 | Failure owner and next action |
|---|---:|---|
| detail-correction | 0 | Lead: carry inquiry unfamiliarity across amount/date corrections; the corrected charge misses its offer although all six file safely |
| two-charges | 5 | Lead: `br3` omits the other charge's required status explanation; preserve both concerns rather than gaming the single-intent taxonomy |
| case-and-charge | 0 | Lead: existing-case status and a different charge need separate handling; current candidate state traps later detail replies without another NLU call |
| vague-specific | 0 | Lead: reparse descriptive detail replies while awaiting a candidate, instead of repeatedly requesting an ordinal and escalating |
| emotion | 0 | Lead plus AI: carry unfamiliarity after neutral explanation and date clarification; three file but miss an offer. Exact dates in words are now supported; missing month remains clarification, not guessed |
| code-switch | 0 | Lead/spec review: two consecutive mixed-language openings can exhaust the contract's two-round limit before the third explicit preference; do not suppress true mixed classification to pass gold |
| slang-words | 2 | AI: preserve units and flag unresolved currency; valid `cl`/`br2`, failures `co`/`ar`/`br1`/`br3`. Lead: allow numeric/currency follow-ups in candidate state and retain inquiry context |
| currency-change | 2 | Lead: corrected USD details followed by descriptive candidate confirmation get trapped; valid `co`/`ar`, failures `cl`/all three PT variants. Existing currency/date slots were correct |
| polite-refusal | 0 | AI: refusal alone must not become `recognized`/`customer_confirms=yes` (fixed and tested). Lead: offered-charge cancellation recognizes only narrow exact words; handle polite refusal as cancellation without treating actual recollection as cancellation |
| recognition | 6 | No baseline failures; retain explicit recognition and separate action confirmation |

AI repairs remain inside NLU: (a) downgrade a model's false recognition of a
polite refusal to uncertainty, preserving explicit recollection; (b) normalize
an explicit spoken day plus month, never missing month/year or an impossible date;
(c) recover only units present in the extracted amount when currency_expr is
absent, clarifying unsupported units rather than assuming USD. Grounding/NLG
output integrity is the already-reviewed PR #77 guard; no fresh NLG rewrite was
justified by the completed traces. Authority and frozen interfaces are unchanged.

**Adjudication list, gold unchanged:** all six code-switch stories vs the
two-round unsupported-language contract; `br1.slang-words` uses colloquial
“oitenta conto” with a later explicit 80 BRL clarification, while the existing
BR normalizer multiplies conto by 1,000. The spoken-unit meaning needs an owner
decision/clarification policy, not an output-informed relabel. These cases remain
failures against their original gold.

## Lean v5.2 status: prepared, not measured or adopted

[v5.2 candidate](../../prompts/nlu/v5_2.md) removes duplication and shortens examples:
5,117 body characters versus v5.1's 7,427 (31.1% shorter). It retains the schema,
denial/unfamiliarity/recognition rules, regional expressions, data boundaries and
code authority. It explicitly distinguishes refusal from recognition and regional
words/names from meaningful code-switching. Actual token savings, latency and
accuracy are **unmeasured**; a shorter prompt alone is not evidence of improvement.

Prompt hashes: v5.1
`e40182de2f232932a12d61d722be5e6356d787217048378fbc2a84f330d241cc`;
v5.2
`2ab79a133cd93e2ab413fd278b84a461a9a7a7b8e46f2436fe596d2372c682d2`.

The [development-only driver](../../src/aclara/llm/dev_prompt_study.py) inventories
all five sets, 240 cases/version, round-robin to avoid covering only the cheapest
set before a cap. An explicit injected client changes NLU only; production v5.1,
phrasing, model selection, scoring and authority remain unchanged. Retired v3
uses complete authored overlays and synthetic identities preserving declared
country/segment; this is an overlay-only dev adapter, **not** the official serving
run or its latency. Input SHA-256:
`0f7a22b3348d8b0d967da05a010742657756b6bdeb7fbf6d35ed64c5df118874`.

| Set | Planned per prompt | Mock executions / exceptions | Fresh comparable real v5.1/v5.2 |
|---|---:|---:|---|
| Dev no-fault | 20 | 20 / 0 | pending / not started |
| Explain/offer confirmation | 20 | 20 / 0 | pending / not started |
| Robustness | 40 | 40 / 0 | pending / not started |
| Round two | 60 | 60 / 0 | repaired 47 complete / not started |
| Retired v3 | 100 | 100 / 0 | pending / not started |

All 240 fixture executions completed with mock only and $0. Mock pass and unsafe
counts are retained in the private receipt; they are not real-model accuracy or
candidate-prompt evidence. The unknown-cost exposure stop and exhausted account
prevent the paid comparison. **Keep v5.1; no adoption gate is claimed.** Completing
the remaining follow-up and a comparable five-set study requires another explicit
dev authorization and durable scope; the queued model-comparison scope cannot
silently be repurposed for this work. Human CSV import also remains pending its
confirmed path.

Local verification: 297 relevant mock/unit checks passed, eight database-dependent
checks skipped; Ruff and strict mypy over 88 source files passed. All five fixture
sets executed with mock only (240 conversations, zero execution exceptions).
The final two ill-formed word-date regressions, sanitized provider-error metadata
and lean-study driver were added after the paid stop and have mock validation
only. The measured implementation SHAs in the table remain the actual run pins.
