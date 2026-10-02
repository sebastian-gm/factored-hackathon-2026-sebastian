# Post-v4 audit robustness evidence

**Post-v4 dev evidence, not held-out.** These fixes and measurements are not
reflected in official v4 numbers. No v4 rows were opened, rerun or rescored.

## Freeze and method

The [36-message inventory](../../src/aclara/llm/dev_post_v4_36.json) and
[SHA-256 manifest](../../src/aclara/llm/dev_post_v4_36.manifest.json) were committed
before measurement in [#113](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/113).
There are 18 ES messages (MX/CO/AR) and 18 pt-BR messages: benign trigger words,
family/self-ID mentions, code-switching, regional slang/amounts, ordinary
inquiries, unfamiliarity/denial, missing slots and reason-specific handoffs.
All messages, identifiers and ledger fixtures are team-authored synthetic data.
Gold was not edited after viewing outputs. The initial scorer falsely counted
the approved bilingual language-help question as an opposite-language error;
that check was corrected and all mock arms rescored identically.

The [harness](../../src/aclara/llm/dev_post_v4.py) uses authenticated local ASGI
P requests, the unchanged matcher/policy, scoped synthetic ledger facts and
one fixed scorer. Mock NLU responses supply authored extraction truth to isolate
code behavior; mock phrasing supplies a generic ES/PT question. Mock results
therefore measure controls and routing, not model quality. Historical code was
exported locally without held-out suites: pre-audit `6a221a4`; audits through
#113 at `2ee162b`; this follow-up at `df3e551`. No deployment was performed.

## Results

| Arm | Objective message pass | ES | PT | Observed unsafe¹ | Language errors² | Useful handoff summary³ |
|---|---:|---:|---:|---:|---:|---:|
| Pre-audit, mock | 21/36 | 11/18 | 10/18 | 0 | 1 | 0 |
| Audits through #113, mock | 34/36 | 17/18 | 17/18 | 0 | 0 | 12 |
| Plus monetary DLP fix, mock | 35/36 | 18/18 | 17/18 | 0 | 0 | 12 |
| One current Gemini real pass | 32/36 | 15/18 | 17/18 | 0 | 0 | 11 |

¹ Unexpected case writes or DLP leakage in customer replies; verified monetary
displays are distinguished from identifiers. These single-message cases do not
estimate conversation SAR or comprehensive safety rates.
² Confident opposite-language evidence; the intentional bilingual language-help
question is allowed. This is an automated check, not a fluent human review.
³ Packet contains the first safe quote in a non-generic rule-based summary.
The pre-audit arm produced 15 handoffs; later mock arms produced 12 each and
the real arm produced 11. Questions,
redaction, verified actions and conversation isolation have separate unit/API
regressions in [the item-6 tests](../../tests/test_post_v4_handoff_context.py).

The paired mock gain is **14 messages**: benign legal-word false handoffs (3),
self-ID false refusals (2), slot questions (6), bilingual language clarification
(2), and the newly exposed large-money DLP failure (1). The Portuguese spoken
cents expression remains unresolved. There was no paid pre-audit arm: comparing
21/36 mock with 32/36 real would conflate code changes and model behavior.

## Monetary DLP correction and remaining real failures

The CO amount normalized correctly after trusted-country wiring, but the
code-approved `2000000.00 COP` display matched the phone regex and raised an
error. The NLG template checks now exclude only the exact scoped monetary slot
rendered by code. Raw DLP and generated-draft checks remain strict. The last
matching occurrence is excluded so a merchant containing the same numeric
literal still receives DLP checks; independent phone numbers remain blocked.
[Regressions](../../tests/test_post_v4_verified_money.py) cover ES/PT large
amounts, canonical approved replies, offers, proposals and identifier controls.

The one real pass left four observable failures; no paid rerun followed:

| Dev ID | Observed behavior | Diagnosis / proposed follow-up |
|---|---|---|
| es03 | Ordinary own-statement inquiry entered the dispute offer. | Consistent with a false unfamiliarity cue; add family-assistance examples preserving own-account inquiries. This is an inference from the response, not a replay of saved extraction JSON. |
| pt05 | Asked for the amount instead of explaining. | The bounded whole-number parser rejects a reais-plus-centavos expression; add a complete, bounded fractional grammar with ambiguous-expression controls. |
| es14 | Asked for merchant or amount instead of only amount. | No normalized NLU clarification reached the missing-slot branch; preserve explicitly vague amount expressions and avoid asking again for an already supplied merchant. Exact extraction was not retained. |
| es18 | Asked for a date instead of routing the old pending charge. | Consistent with treating vague status age as a selection date; distinguish duration complaints from dates used to identify charges. Exact extraction was not retained. |

## Paid receipt and limits

Production-key and account credit preflight passed before inference. Dedicated
scope **`dev-gate/post-v4-audit`**, run **`post-v4-audit`**, has a durable
**$0.10 lifetime cap** and reserves before every call; final-evaluation and
production budget scopes were not used. Serial calls, one attempt, a 20-second
deadline, no retry/fallback, and no Jev. This dev deadline differs from the live
6-second first-attempt policy; these latencies are not live-app SLO measurements.

Read back from Postgres after completion: **$0.0543715 known/charged cost**,
**28 calls**, **0 unknown costs**. All 28 attempts returned valid structured
output: **100% JSON validity over all attempts**. Model:
`google/gemini-3-flash-preview`, existing ZDR/data-collection-denied route.
Per-call usage totals: **79,073 input / 4,945 output tokens**. Cost is from
per-call usage and the durable scope, never key-level deltas: $0.001510 per
tested message, $0.001942 per billable NLU call. Eight requests routed in code.

NLU call latency p50/p95: **2.007 / 2.355 s**. Local authenticated message
exercise p50/p95: **2.865 / 3.678 s**, including fixture/authentication setup.
Private checkpoints and the scope/preflight receipts remain ignored under
`artifacts/post-v4-audit/`, mode 0600; no credentials or model reasoning were
saved. The run refuses any second paid pass when prior reservations exist.

This small, synthetic, development-only sample has no fluent PT reviewer and
cannot replace human validation or held-out evaluation. Defaults are unchanged.
