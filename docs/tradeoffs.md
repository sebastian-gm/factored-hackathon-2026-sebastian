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
test suite. TODO(results): paired B1/P SAR, unsafe outcomes and escalation load across
pre-registered operating points, with intervals and denominators.

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
[result review](ml/result-review.md) preserves this unfavorable cost trade-off,
customer-clustered intervals, subgroup results and synthetic recency artifacts.
A new independent workload should revisit the choice.

## Language model choice

No application model default has been selected. The
[model-comparison protocol](ml/model-comparison.md) requires shared labeled cases,
invalid-output accounting, latency, cost and separate language ratings. The current
mock fallback proves control flow, not that the proposed language system beats B1.
Provider data terms and durable spend accounting are release constraints alongside
accuracy and price. Portuguese **scenario authoring** with a second vendor is not a
system-model comparison and does not authorize inference spending.

TODO(results): measured model accuracy/latency/cost Pareto with actual response model
IDs, prompt versions, provider route, sample sizes and invoice reconciliation.

## Templates and model phrasing

Case, confirmation, freeze and policy-critical messages use deterministic wording.
Optional model phrasing is limited to clarification/explanation and must pass
citation, fact and DLP checks, otherwise the service uses a template. This trades
some flexibility for inspectable action claims. Templates can still be wrong or
awkward; human ES/PT review remains necessary. Additional model calls add latency,
cost and opportunities for error, even if they improve tone.

TODO(results): templates-only versus guarded phrasing on the same preselected cases,
including clarity/language ratings, grounding failures, latency and cost. Do not
substitute a model's self-rating for the required independent/human review.

## Human workload

A correct mandatory handoff is a successful safety decision, but it still consumes
agent time. Unnecessary transfers, failed clarifications and repeated authentication
increase workload. A complete packet should reduce repetition; that reduction has
not been measured. Routing prefers active skill/language matches, then load, with
explicit fallback. The source directory is a staffing snapshot, not a live capacity
or availability feed.

TODO(results): handoffs per 1,000 attempted cases, missed/unnecessary transfers,
packet completeness and agent-hours per 1,000. Agent-hours require an observed
handling-time assumption for the selected workflow; they cannot be inferred from
an escalation count alone. The [projection](evaluation/business-projection.md)
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
