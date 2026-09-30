# PR #62 AI review follow-up: approved questions and language evidence

Addresses findings **1 and 3** in the lead's
[review on `fix/preview-startup-review`](https://github.com/sebastian-gm/bank-agent-lab/blob/fix/preview-startup-review/docs/reviews/pr-62-review.md).
This is a separate PR targeting `fix/post-v3-analysis`; robustness PR #65 stays
independently reviewable. All examples are newly authored mocks. No v4 input
was opened, no paid measurement was made, and no budget scope was modified.

## Approved reply semantics

The phrasing builder previously generated a generic template and sent that as
`approved_text`, losing the code-approved `plan.reply`. A mock API test reproduced
unsupported-language help being replaced by a safe but irrelevant amount/date
question. The prompt could not preserve a question absent from its input.

Code-supplied clarification text now remains deterministic and exact, including
bilingual language help and recognition questions. The existing API recognition
guard is retained. A blank clarification plan can still use the generic template
and grounded phrasing. For rephrased explanations, the actual approved reply is
sent as `approved_text` and retained as fallback. DLP, fact citations, grounding,
wrong-language rejection and code's authorization checks remain active.

## Language evidence

The old two-language detector treated any one PT token as decisive and otherwise
returned ES. Mock regressions reproduce the `.com` and Spanish SIM-card collisions,
and rejection of short valid PT wording.

A separate `detect_language_evidence` returns **es / pt / uncertain**. It removes
domains/URLs and explicitly supplied trusted merchant names before counting
language evidence. Distinctive lexical evidence has greater weight than weak
function words; `com` and `sim` cannot decide language. Insufficient or conflicting
evidence returns uncertain. The existing two-language `detect_language` wrapper
keeps its ES default for uncertain cases, preserving the frozen interface.

NLG supplies known merchant names from its scoped plan/facts and rejects a draft
only on confident opposite-language evidence. Ambiguous short text no longer
causes an automatic opposite-language verdict. This is a conservative ES/PT
heuristic, not a calibrated probability or a human fluency judgment. Unknown
merchant names cannot be reliably inferred from prose; NLG uses trusted metadata
rather than guessing named entities.

## Verification

Before changing behavior, authored mock checks reproduced eleven failing cases:
API language help, code-supplied clarification questions, domain/SIM routing,
short PT and ambiguous drafts, approved-text input, and trusted merchant names.
The expanded 21-case regression file also tests an ES SIM-request handoff,
explicit uncertainty, conflicting cues and confident opposite-language rejection.
The existing recognition tests still run through the API and assert no phrasing
call and no write for uncertain replies.

Targeted checks: **90 passed**. `make checks` passes six hooks, Ruff, strict mypy,
compilation, file policy, **329 passed / 14 database-dependent skips**, B1
**32/32**, interfaces and policy catalog. Remote CI readback is recorded in
the progress log and PR. No paid-call,
latency, human-review or population-accuracy claim is made for this follow-up.
