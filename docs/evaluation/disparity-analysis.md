# Outcome disparities: saved v2 and v3 evidence

**Offline, zero-call investigation; official scores are unchanged.** V3 P's ES/PT
pass gap is three cases: 38/48 versus 35/48. Two additional PT security-packet
failures and one additional unfamiliarity/selection failure account for that
observed gap. It is not evidence that Gemini is generally worse in Portuguese.
Broad category composition barely changes the gap; smaller scenario/policy mixes
and shared code defects matter. V3 is now development data, not a reusable
independent evaluation. No v4 input or result was accessed.

Sources: [official v2 analysis](final-v2-error-analysis.md),
[corrected v2 escalation slices](final-v2-slice-correction.md),
[official v3 report](final-v3-results.md), and
[post-v3 cause analysis](post-v3-fixes.md). This investigation reads primary repeat
0 P-Gemini checkpoints only: 200 v2 and 100 v3. It recomputes aggregates from
saved observations, never reruns or rescores a case. All 300 checkpoint files and
two official reports were hashed before/after and remained unchanged. Private
aggregate receipt: `artifacts/disparity-analysis/aggregates.json`, SHA-256
`164f8e52437bc54a7757c792b052eb35d34ecc95a2dbbf27efb6ebea10c29cb4`.
No source/customer rows or transcripts are reproduced.

## Language: different metrics tell different stories

Pass intervals below are Wilson 95%. SAR uses the in-scope denominator; strict
transfer requires committed readback, correct reasons, fields and routing.
Presence alone is not correct escalation.

| Snapshot / language | Pass (95% CI) | SAR / in-scope | Strict escalation | Unnecessary transfer / eligible |
|---|---|---|---|---|
| V2 ES | 30/96, 31.3% (22.9–41.1%) | 21/96 | 9/25 | 18/71 |
| V2 PT | 27/84, 32.1% (23.1–42.7%) | 12/77 | 15/35 | 15/49 |
| V3 ES | 38/48, 79.2% (65.7–88.3%) | 18/48 | 16/20 | 5/28 |
| V3 PT | 35/48, 72.9% (59.0–83.4%) | 19/48 | 13/19 | 6/29 |

V2 includes 17 mixed and three other-language cases; v3 includes four mixed.
Unreached fault fixtures remain failures: v2 ES seven / PT six, v3 zero. V2 PT
has more mandatory-human cases (35/84 versus ES 25/96), so its lower workload
SAR cannot by itself establish unequal model quality. V3 PT has slightly higher
SAR despite lower pass and strict transfer recall. Suites, semantics and release
code differ; these are not causal before/after or population comparisons.

Category standardization uses the pooled ES/PT frequencies of the four workload
categories as weights: adjusted pass = sum(weight × language-specific category
pass). ES-minus-PT pass is −0.89 pp raw / −1.08 pp adjusted in v2, and +6.25 pp
raw / +6.37 pp adjusted in v3. Broad category mix does not explain the v3 gap.
This coarse adjustment cannot remove within-category template, policy, country
or segment differences, and does not establish a causal language effect.

Country and segment counts are also balanced by language in v3: each language
has 16 cases per AR/CO/MX and 12 per segment. Standardizing on either leaves
the +6.25 pp gap unchanged. Separate v2 adjustments leave its gap near zero
(country −0.88 pp, segment −0.92 pp). These are separate one-factor checks,
not a multivariable causal model. Additional private composition receipt:
`artifacts/disparity-analysis/composition-check.json`.

## What actually fails

| V3 saved failure cause | ES | PT | Evidence and implication |
|---|---:|---:|---|
| Unfamiliarity treated as uncertain selection | 5 | 6 | Correct inquiry NLU and confident MATCH discarded by shared selection logic |
| Security handoff language / legal-cue retention | 1 | 3 | PT routing/cue behavior contributes two extra failures; authorization refusal still holds |
| Distress handoff reason | 1 | 1 | Shared deterministic cue parsing, not a PT-only pattern |
| Lost-card / declined-freeze handoff reasons | 1 | 1 | Shared classification/packet preservation |
| Outage with unsuccessful fallback | 1 | 1 | Shared failure routing |
| Stale OTP simulator did not renew | 1 | 1 | Evaluation adapter, not language quality |

The six groups exhaust the 23 failures. In v2, failed terminal explanations
occurred in 36 ES and 29 PT cases; missing dispute creation in 33 ES and 26 PT
cases. These overlap: the dominant problem was the old unfamiliarity/denial
workflow and contract, not evidence of less natural PT prose. Official
materially-incorrect outcome flags remain as reported; they are scorer predicates,
not independent human factual judgments. See the v2 gold/clock and metric caveats.

Over executed cases, v2's recorded materially-incorrect flags are ES 36/89
(Wilson 95% 30.9–50.8%) and PT 28/78 (26.1–47.0%). The one ES unauthorized-action
and policy flag is the documented fixture-clock mismatch; official flags remain.
In v3 each recorded unsafe category is 0/48 in both languages (Wilson upper
bound 7.4% per category). P still failed mandatory recall/readback safety gates.
These caveats prevent interpreting a raw unsafe-language gap as model bias or
zeros as a safety guarantee.

The v3 fixes already have an owner-reported 100/100 **seen-data** regression,
linked above. That does not replace 77/100. Wrong-language phrasing can also
escape objective pass metrics: [the saved human-review item and verifier
fix](judge-human-validation.md) are separate evidence. Neither pass parity nor
zero recorded grounding violations proves fluent, safe language quality.

## Segments and countries

| Slice | V2 pass (Wilson 95%) | V3 pass (Wilson 95%) |
|---|---|---|
| Basic | 15/50 (19.1–43.8%) | 16/25 (44.5–79.8%) |
| Plus | 18/51 (23.6–49.0%) | 21/25 (65.3–93.6%) |
| Premium | 15/51 (18.7–43.0%) | 19/25 (56.6–88.5%) |
| Student | 15/48 (19.9–45.3%) | 21/25 (65.3–93.6%) |
| AR | 20/65 (20.9–42.8%) | 29/33 (72.7–95.2%) |
| CO | 22/71 (21.4–42.5%) | 28/33 (69.1–93.3%) |
| MX | 21/64 (22.6–45.0%) | 20/34 (42.2–73.6%) |

V3 MX contains nine of eleven unfamiliarity failures, compared with CO two / AR
zero. Basic contains six; Plus three; Student two. Premium's six failures are
security/handoff/outage issues, not unfamiliarity. Workload composition differs:
Basic has 13 normal cases and six required-human cases; Premium has six normal
and fourteen required-human cases. Segment-dependent policy is intentional;
compare equivalent policy opportunities, not equal raw automation rates.
V3 eligible SAR is Basic 10/19, Plus 10/16, Premium 11/11, Student 8/14. Country
strata describe bank policy/source selection, not the spoken language or inferred
nationality: PT occurs across AR/CO/MX. There is no BR country stratum here.

## Concrete follow-up and limits

- Preserve unfamiliarity across clarification/candidate selection; reparse corrected
  details. Keep regression pairs for semantic ES and PT equivalents.
- Preserve PT language and legal/distress cues through security and freeze handoffs;
  assert strict packet/readback correctness, not just handoff presence.
- Keep short PT prompt examples distinguishing bare unfamiliarity, explicit denial,
  recollection and polite refusal, plus units/dates and mixed-language clarification.
  Validate on authored dev cases before adoption; examples cannot repair routing code.
- Recruit a fluent pt-BR reviewer for the same blinded rubric and dialect variants.
  Current limits are es-CL human spot-check n=9, no fluent PT reviewer, synthetic
  templated language and small/correlated slice cells. Human scoring is pending.
- For the next independently executed evaluation, report language/country/segment
  pass, eligible/in-scope SAR, strict transfer, unnecessary transfer and unsafe
  rates with denominators and Wilson intervals; also matched policy/case-mix slices.
  TODO(results): v4 only, populated by the independent executor after completion.

Intervals quantify binomial sampling uncertainty only; shared templates, selection
bias and missing human validation limit them further. The data establish neither
population inequity nor equivalence. No protected demographic attributes were
inferred, no new model calls were made, and no prompt/policy change follows from
this analysis alone.
