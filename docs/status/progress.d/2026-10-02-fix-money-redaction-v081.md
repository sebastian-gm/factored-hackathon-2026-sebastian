# 2026-10-02 — Money input redaction (AI lane, v0.8.1)

## Completed (verified)

- Authored CO/CL/AR/MX/BR money/privacy regressions before the fix: 43 failed and 23 passed, including grouped truncation and raw-slot recovery. Expanded controls cover single amounts, missing/truncated mock extraction, phone/CPF/DNI/RUT/cédula/card precedence, slang/scales, merchant digits, multiple amounts and serving-shaped twins.
- Incoming redaction now classifies original spans before replacement. Currency/unit cues and consistent thousands groups preserve monetary evidence; explicit identifiers, plus/dashed phones and card-shaped runs retain precedence. Outbound DLP/grounding checks remain unchanged.
- NLU normalizes a single unambiguous numeric monetary expression from original local customer text, independently of provider redaction. Fallback keeps complete separators and excludes identifiers; multiple amounts require disambiguation. Numeric mil/million scales and CL palos/lucas retain their multiplier. No interface, MATCH threshold, prompt, model default or shared orchestration edits.
- Existing privacy/grounding/NLU focused checks: 408 passed; strict mypy passed. No model spend and no held-out/v4 rows accessed.
- Added the exact lead-reported smoke format `1000000.00 COP` plus CLP/ARS/MXN/BRL variants and unseparated forms to redaction, raw-slot recovery and fallback regressions.
- All 125 final authored controls pass, including canonical-slot equivalence through the unchanged learned matcher. The existing matcher may still request a choice for large same-merchant twins.

## Done but not verified

- Full mock suite, B1 smoke and final-head remote CI remain pending.

## Next / blocked

- Open the v0.8.1 fix PR for lead review after full mock validation. Keep it unmerged while the release-window merge hold remains active.
