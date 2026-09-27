# Evaluation results

Generated from `artifacts/evaluation/results.json`. No independent numbers.

- **workload**: "32 authored reactive ES/PT fixture scenarios with deterministic faults; mock only; language review pending."
- **system**: "B1"
- **model**: "mock"
- **prompt_versions**: "nlu@v1,phrase@v1"
- **tag**: "working-tree"
- **cost_assumptions**: "Mock calls cost USD 0; infrastructure excluded"
- **price_table_date**: "2026-09-26"
- **monthly_infrastructure_estimate_usd**: 34.63
- **policy_version**: "layer1"
- **matcher_version**: "rules"
- **dataset_version**: "authored-fixtures"
- **sample_size**: 64
- **independent_scenarios**: 32

Containment alone is not success. Synthetic mock workload; no model-quality claim.

| Metric | Aggregate |
|---|---|
| passed | `64` |
| sar_in_scope | `{"count": 36, "denominator": 60, "rate": 0.6, "wilson_95": [0.47366053492041094, 0.7143050946511716]}` |
| sar_eligible | `{"count": 36, "denominator": 36, "rate": 1.0, "wilson_95": [0.9035813714055411, 0.9999999999999999]}` |
| automation_attempt_share | `{"count": 36, "denominator": 60, "rate": 0.6, "wilson_95": [0.47366053492041094, 0.7143050946511716]}` |
| flagged_intakes | `0` |
| containment | `{"count": 40, "denominator": 64, "rate": 0.625, "wilson_95": [0.5025037868400484, 0.7333401982117511]}` |
| containment_note | `"Containment alone is not success."` |
| escalation_recall | `{"count": 24, "denominator": 24, "rate": 1.0, "wilson_95": [0.8620237953250264, 1]}` |
| missed_transfers | `{"count": 0, "denominator": 24, "rate": 0.0, "wilson_95": [0, 0.13797620467497365]}` |
| unnecessary_transfers | `{"count": 0, "denominator": 40, "rate": 0.0, "wilson_95": [6.938893903907228e-18, 0.08762160119728224]}` |
| routing_accuracy | `{"count": 16, "denominator": 16, "rate": 1.0, "wilson_95": [0.8063923194655722, 1]}` |
| routing_by_field | `{"queue": {"count": 16, "denominator": 16, "rate": 1.0, "wilson_95": [0.8063923194655722, 1]}, "language": {"count": 16, "denominator": 16, "rate": 1.0, "wilson_95": [0.8063923194655722, 1]}, "fallback_used": {"count": 16, "denominator": 16, "rate": 1.0, "wilson_95": [0.8063923194655722, 1]}}` |
| handoff_completeness | `{"n": 16, "mean": 1.0}` |
| handoff_rubric | `{"n": 24, "mean": 1.0, "kind": "deterministic four-field rubric; no LLM judge"}` |
| unsafe | `{"unauthorized_disclosure": {"count": 0, "denominator": 64, "rate": 0.0, "wilson_95": [0, 0.05662405979280239], "upper_95": 0.046875}, "unauthorized_action": {"count": 0, "denominator": 64, "rate": 0.0, "wilson_95": [0, 0.05662405979280239], "upper_95": 0.046875}, "missing_confirmation_or_step_up": {"count": 0, "denominator": 64, "rate": 0.0, "wilson_95": [0, 0.05662405979280239], "upper_95": 0.046875}, "reported_not_verified": {"count": 0, "denominator": 64, "rate": 0.0, "wilson_95": [0, 0.05662405979280239], "upper_95": 0.046875}, "materially_incorrect_outcome": {"count": 0, "denominator": 64, "rate": 0.0, "wilson_95": [0, 0.05662405979280239], "upper_95": 0.046875}, "grounding_violation": {"count": 0, "denominator": 64, "rate": 0.0, "wilson_95": [0, 0.05662405979280239], "upper_95": 0.046875}, "policy_violation": {"count": 0, "denominator": 64, "rate": 0.0, "wilson_95": [0, 0.05662405979280239], "upper_95": 0.046875}, "refund_or_credit_promise": {"count": 0, "denominator": 64, "rate": 0.0, "wilson_95": [0, 0.05662405979280239], "upper_95": 0.046875}}` |
| unsafe_note | `"0 observed in n cases does not establish zero risk; the 95% upper bound is 3/n (capped at 1). Repeats are correlated."` |
| latency | `{"turn": {"p50_ms": 0.6261763628572226, "p95_ms": 1.1313959257677197, "case_bootstrap_95": {"p50": [0.605810186243616, 0.6542361807078123], "p95": [0.9652390494011343, 1.4326365111628545]}}, "case": {"p50_ms": 0.8494815556332469, "p95_ms": 2.113012562040239, "case_bootstrap_95": {"p50": [0.6095876218751073, 1.2825762387365103], "p95": [1.810876234085299, 2.346159890294075]}}}` |
| cost | `{"total_usd": 0, "per_case_usd": 0.0, "per_attempted_case_usd": 0.0, "per_sar_usd": 0.0}` |
| components | `{"llm": 0, "api_other": 68.49908852018416}` |
| flip_rate | `{"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533]}` |
