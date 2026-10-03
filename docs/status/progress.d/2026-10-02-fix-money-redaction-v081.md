# 2026-10-02 — Money input redaction (AI lane, v0.8.1)

## Completed (verified)

- Authored CO/CL/AR/MX/BR money/privacy regressions before the fix: 43 failed and 23 passed, including grouped truncation and raw-slot recovery. Expanded controls cover single amounts, missing/truncated mock extraction, phone/CPF/DNI/RUT/cédula/card precedence, slang/scales, merchant digits, multiple amounts and serving-shaped twins.
- Incoming redaction classifies original spans before replacement. Currency/unit or explicit amount cues are required, including for grouped numbers. Phone/contact/identifier cues, plus/dashed phones and card-shaped runs retain precedence. Outbound DLP/grounding checks remain unchanged.
- NLU normalizes a single unambiguous numeric monetary expression from original local customer text, independently of provider redaction. Fallback keeps complete separators and excludes identifiers; multiple amounts require disambiguation. Numeric mil/million scales and CL palos/lucas retain their multiplier. No interface, MATCH threshold, prompt, model default or shared orchestration edits.
- Existing privacy/grounding/NLU focused checks: 408 passed; strict mypy passed. No model spend and no held-out/v4 rows accessed.
- Added the exact lead-reported smoke format `1000000.00 COP` plus CLP/ARS/MXN/BRL variants and unseparated forms to redaction, raw-slot recovery and fallback regressions.
- Prior-head full local mock checks: 1,463 passed / 40 DB skips, B1 32/32. All 125 authored controls, including later exact-formatter variants, passed; prior-head remote Python/Postgres/invariants passed. The existing matcher may still request a choice for large same-merchant twins.
- Lead review BLOCKED #149 for grouped contact-phone leaks and a shared-unit list incorrectly forcing its last amount. Nineteen ES/PT mock regressions reproduced those findings. The correction requires monetary context, masks extended contact cues, and propagates a shared unit to distinct preceding numeric tokens without selecting one. Leading-plus phones and malformed card-like groups are also covered. Expanded authored controls: 161; focused privacy/NLU/grounding checks pass.

## Done but not verified

- Corrected-head full mock suite, B1 smoke and required remote CI remain pending.

## Next / blocked

- #149 needs the lead's security re-review and corrected-head green CI for v0.8.1 alongside #138/#147. Keep it unmerged while the release-window merge hold remains active.
