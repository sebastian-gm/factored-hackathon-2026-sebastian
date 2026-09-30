# Privacy, Fairness and Safety

**Synthetic-bank evidence does not establish population fairness or real-data
readiness.** Code grades objective outcomes; Sonnet/Jev wording scores cannot
establish authorization, correctness or human satisfaction.
[Evaluation](evaluation/final-v3-results.md), [judge rubric](evaluation/judge-rubric.md).

## Minimize data; preserve authority

Models receive pattern-redacted text and code-approved fact projections with
opaque/masked handles. Projections exclude whole ledger rows, identity maps,
credentials and fraud scores. Free text can evade redaction; merchant/amount/date
can identify events. Masking is not anonymization. Organizer terms/disclosures
need owner confirmation.
[Actual payload/storage boundaries](security/privacy-and-retention.md#what-crosses-each-boundary).

OpenRouter requests `zdr=true`/`data_collection=deny`; verify endpoint/account
behavior. **Jev's standard-account ZDR is unverified.** Call metadata omits
prompts/completions/thinking, but private turns/execution records contain redacted
messages/responses. Expiry is not deletion; automated purge remains unverified.
[Terms/provenance](data-provenance.md),
[retention](security/privacy-and-retention.md#retention-target-policy-versus-enforcement).

Untrusted text is escaped/bounded; injection/cross-customer guards and merchant
sanitization precede interpretation. Gemini/Jev cues are unioned; Jev failure logs
degradation and keeps Gemini flags. Strict schemas, DLP and
grounding checks reject unsupported facts/citations, sensitive identifiers and
prohibited promises; invalid drafts fall back to approved text. State-specific
clarifications stay deterministic; confident opposite-language drafts are rejected.
These are bounded defenses, not semantic/injection guarantees.
[NLU](../src/aclara/agent/nlu/structured.py), [grounding](../src/aclara/agent/nlg/grounding.py),
[phrasing](../src/aclara/agent/nlg/builder.py), [regressions](ml/pr-62-ai-review-fixes.md).

Identity, ownership, policy, proposals, confirmation/step-up, writes and read-back
stay in code. Model prose cannot authorize an action or promise a refund.
[Authority boundary](architecture.md), [production gaps](production-readiness.md).

## Language evidence, not parity

P-Gemini primary runs. SAR is successful automation; strict escalation requires
the correct verified handoff. Denominators differ.

| Official run / language | Workload | SAR / in-scope | Strict escalation |
| --- | ---: | ---: | ---: |
| V2 ES | 96 | 21/96 (21.9%) | 9/25 (36.0%) |
| V2 pt-BR | 84 | 12/77 (15.6%) | 15/35 (42.9%) |
| V3 ES | 48 | 18/48 (37.5%) | 16/20 (80.0%) |
| V3 pt-BR | 48 | 19/48 (39.6%) | 13/19 (68.4%) |

[Official v2](evaluation/final-v2-error-analysis.md),
[corrected strict slices with 95% intervals](evaluation/final-v2-slice-correction.md),
[official v3, including B1 and unnecessary transfers](evaluation/final-v3-results.md).
V2 regional P recall: es-AR **4/9**, es-CO **2/8**, es-MX **3/8**; wide intervals
and policy mix prevent dialect rankings. V3 has four mixed cases; detailed dialect
intervals remain private, not a parity claim. Country is not language; changed
suites/policy prevent causal v2→v3 claims;
**v3 is now seen development data**.

Both runs failed full safety gates. V2 P had **1/187 unauthorized actions**; v3 P
had **0/100 observed critical unsafe events** (95% upper bound 3.70%) but failed
fraud/regulator recall (**2/5**) and required-readback coverage (**67/74**).
Zero observed events are not zero risk.

Human es-CL checking: **n=9**, one author/annotator, older pipeline;
there is **no fluent-human PT reviewer**. Synthetic/model-authored wording and
model copy review do not substitute for native review. Judge–human agreement is
unmeasured; v3 judging completed only 28/60 pairs.
[Human limits](ml/result-review.md#human-spot-check-n9-es-cl), [PT review](ml/pt-review.md).

**V4: TODO(results)** — report language/dialect SAR, correct/missed/unnecessary
transfers and unsafe rates with counts, 95% intervals and policy mix; no v4 opened.

## Report an issue

Request a human in the demo. Privately report defects to the owner through the
approved channel: execution ID, version, language, redacted summary; no public
credentials/OTPs/customer rows. Proposed response: owner triage, private evidence,
synthetic reproduction and reviewed rollback/fix. No staffed 24/7 SLA is claimed.
[Handoff boundary](handoff-routing.md), [release review](submission/checklist.md).
