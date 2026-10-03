# Trade-offs

The main decision is to automate a narrow charge workflow while keeping identity,
eligibility, writes and verification deterministic. The completed matcher experiment
is an offline normalized-slot comparison. It is not the final B1-versus-P evaluation,
a measurement of Portuguese understanding, or a production improvement.

## Autonomy and safety

The matcher can propose a candidate, request a choice or return no match. Customer
confirmation does not override policy. Missing facts, borderline eligibility and
mandatory-human cases remain review paths. Higher coverage can expose more customers
to a wrong proposal; lower coverage consumes more clarification and human attention.

Frozen matcher risk/coverage points and thresholds are in
[metrics.json](../models/charge_matcher/v1/metrics.json). Those points measure candidate
proposal errors, not end-to-end unsafe writes. Do not retune thresholds on the frozen
test suite. The [corrected mock diagnostic](history/evaluation/heldout-run01.md) reports
67/193 SAR/in-scope for both systems (34.7%, Wilson 95% interval 28.36–41.67%). Each
made six forbidden ESC-04 dispute writes and nine materially incorrect outcomes;
acceptance failed. P used rules fallback, so this does not measure a learned-system
gain. TODO(results): approved real-model operating-point comparison and risk/coverage.

## Learned matcher choice

These are pipeline outputs from the frozen matcher
[metrics](../models/charge_matcher/v1/metrics.json) and
[metadata](../models/charge_matcher/v1/metadata.json), rounded as in the
[model card](ml/model-card-charge-matcher.md). The test workload has 3,000 normalized
queries; ranking metrics use only queries with a true match. Cost is a synthetic
error penalty, **not dollars**. Proposal counts use each model's own operating point.

| Model | Test top-1 | Test expected cost/query | Wrong proposals / proposals | Validation policy cost |
| --- | ---: | ---: | ---: | ---: |
| Rules | 86.59% | 0.6197 | 29 / 1,684 | See frozen metadata |
| Logistic regression | 96.78% | 0.3980 | 41 / 1,958 | 0.2584 |
| LightGBM | 95.22% | 0.4717 | 10 / 1,871 | 0.1828 |

Logistic regression has lower test cost and better calibration. LightGBM made about
4× fewer wrong proposals, while proposing less often. The registered selection rule
chooses the simplest model within 0.02 of the best **validation** cost. Logistic's
validation gap is 0.0756, outside that tolerance, so LightGBM remains selected.
Switching after seeing test would turn test into another validation set. The
[result review](history/ml/result-review.md) preserves this unfavorable cost trade-off,
customer-clustered intervals, subgroup results and synthetic recency artifacts.
A new independent workload should revisit the choice.

## Language model choice

Gemini 3 Flash is the owner-selected default; Grok 4.20 is a bounded failure
fallback. [Measured development comparisons](history/ml/model-comparison.md) report intent,
slots, valid responses, latency and per-NLU-case cost. Claude Sonnet 5 is the frontier
comparator. [Jev](history/ml/typesafe-jev-comparison.md) adds a risk second opinion and a
second subjective judge; its small judge sample does not validate human agreement.
The private release verifies routing and durable spend settlement. Final-run
conversation costs and quality remain `TODO(results)`; per-call prices cannot fill them.

## Templates and model phrasing

Case, confirmation, freeze and policy-critical messages use deterministic wording.
Optional model phrasing is limited to clarification/explanation and must pass
citation, fact and DLP checks, otherwise the service uses a template. This trades
some flexibility for inspectable action claims. Templates can still be wrong or
awkward; human ES/PT review remains necessary. Additional model calls add latency,
cost and opportunities for error, even if they improve tone.

Pending development: templates-only versus guarded phrasing on the same preselected cases,
including clarity/language ratings, grounding failures, latency and cost. Do not
substitute a model's self-rating for the required independent/human review.

## Human workload

A correct mandatory handoff is a successful safety decision, but it still consumes
agent time. Unnecessary transfers, failed clarifications and repeated authentication
increase workload. A complete packet should reduce repetition; that reduction has
not been measured. Routing prefers active skill/language matches, then load, with
explicit fallback. The source directory is a staffing snapshot, not a live capacity
or availability feed.

In the frozen diagnostic, each system had 60/134 unnecessary transfers, 54/66
required handoffs present, but 0/54 required complete packets and 0/66 fully correct
transfers. Packet presence and a safety decision do not establish a useful human
handoff. These results predate later staff packet additions. Sources:
`unnecessary_transfers`, `handoff_presence_recall`, `safety_gates.required_handoff_fields` and
`escalation_recall` in [B1](evaluation/heldout-run01-B1.json) and
[P/mock](evaluation/heldout-run01-P-mock.json).

Pending human study: human-reviewed packet quality and agent-hours per 1,000. Agent-hours require an observed
handling-time assumption for the selected workflow; they cannot be inferred from
an escalation count alone. The [projection](history/evaluation/business-projection.md)
keeps those assumptions separate from offline outcomes.

## AI and rules

Structured language extraction and learned matching are appropriate experiments for
vague recollections. Rules are the authority for ownership, time windows, amounts,
thresholds and actions because their inputs and outcomes must be testable. The
pipeline rejected accent-based routing as unsupported by its descriptive comparison,
and the fraud-score discontinuity makes training a fraud predictor from that label
misleading. See [problem analysis](problem-analysis.md) and the
[AI/deterministic table](architecture.md).

A known B1 phrase gap found during frontend integration is the Spanish lost-card
wording “Perdí mi tarjeta”; the stolen-card wording exercises the implemented freeze
path. This is a limitation to investigate on development language cases, not a reason
to give the frontend or an LLM authority to force a freeze.

[Matcher v2](ml/model-card-charge-matcher-v2.md) changes the decision cost table to favor top-three choices under uncertainty; its synthetic stress cohort and nine-case human before/after are reported separately from v1.
