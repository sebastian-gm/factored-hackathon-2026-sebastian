# Evaluation results

Generated from `artifacts/evaluation-p/results.json`. No independent numbers.

- **workload**: "32 authored reactive ES/PT fixture scenarios with deterministic faults; mock only; language review pending."
- **system**: "P"
- **model**: "mock"
- **prompt_versions**: "nlu@v1,phrase@v1"
- **tag**: "working-tree"
- **cost_assumptions**: "Mock calls cost USD 0; infrastructure excluded"
- **price_table_date**: "2026-09-26"
- **monthly_infrastructure_estimate_usd**: 34.63
- **policy_version**: "layer1"
- **matcher_version**: "rules"
- **dataset_version**: "authored-fixtures"
- **sample_size**: 32
- **independent_scenarios**: 32

Containment alone is not success. Synthetic mock workload; no model-quality claim.

| Metric | Aggregate |
|---|---|
| passed | `32` |
| sar_in_scope | `{"count": 18, "denominator": 30, "rate": 0.6, "wilson_95": [0.4232036025332294, 0.754093718831978]}` |
| sar_eligible | `{"count": 18, "denominator": 18, "rate": 1.0, "wilson_95": [0.8241207763533505, 1]}` |
| automation_attempt_share | `{"count": 18, "denominator": 30, "rate": 0.6, "wilson_95": [0.4232036025332294, 0.754093718831978]}` |
| flagged_intakes | `0` |
| containment | `{"count": 20, "denominator": 32, "rate": 0.625, "wilson_95": [0.4525440735307791, 0.7706611269054546]}` |
| containment_note | `"Containment alone is not success."` |
| escalation_recall | `{"count": 12, "denominator": 12, "rate": 1.0, "wilson_95": [0.7575059933447693, 1]}` |
| missed_transfers | `{"count": 0, "denominator": 12, "rate": 0.0, "wilson_95": [0, 0.24249400665523077]}` |
| unnecessary_transfers | `{"count": 0, "denominator": 20, "rate": 0.0, "wilson_95": [1.3877787807814457e-17, 0.1611251580528119]}` |
| routing_accuracy | `{"count": 8, "denominator": 8, "rate": 1.0, "wilson_95": [0.6755924351161318, 1]}` |
| routing_by_field | `{"queue": {"count": 8, "denominator": 8, "rate": 1.0, "wilson_95": [0.6755924351161318, 1]}, "language": {"count": 8, "denominator": 8, "rate": 1.0, "wilson_95": [0.6755924351161318, 1]}, "fallback_used": {"count": 8, "denominator": 8, "rate": 1.0, "wilson_95": [0.6755924351161318, 1]}}` |
| handoff_completeness | `{"n": 8, "mean": 1.0}` |
| handoff_rubric | `{"n": 12, "mean": 1.0, "kind": "deterministic four-field rubric; no LLM judge"}` |
| unsafe | `{"unauthorized_disclosure": {"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533], "upper_95": 0.09375}, "unauthorized_action": {"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533], "upper_95": 0.09375}, "missing_confirmation_or_step_up": {"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533], "upper_95": 0.09375}, "reported_not_verified": {"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533], "upper_95": 0.09375}, "materially_incorrect_outcome": {"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533], "upper_95": 0.09375}, "grounding_violation": {"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533], "upper_95": 0.09375}, "policy_violation": {"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533], "upper_95": 0.09375}, "refund_or_credit_promise": {"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533], "upper_95": 0.09375}}` |
| unsafe_note | `"0 observed in n cases does not establish zero risk; the 95% upper bound is 3/n (capped at 1). Repeats are correlated."` |
| latency | `{"turn": {"p50_ms": 0.8070110343396664, "p95_ms": 1.1515805032104254, "case_bootstrap_95": {"p50": [0.7656939560547471, 0.9182715322822332], "p95": [1.0477335471659899, 14.528034423128664]}}, "case": {"p50_ms": 1.2237300397828221, "p95_ms": 3.0082768993452187, "case_bootstrap_95": {"p50": [0.8978304686024785, 1.6393640544265509], "p95": [1.956136373337358, 19.129683962091804]}}}` |
| cost | `{"total_usd": 0, "per_case_usd": 0.0, "per_attempted_case_usd": 0.0, "per_sar_usd": 0.0}` |
| components | `{"api_other": 60.61329320073128, "llm": 0}` |
| flip_rate | `{"count": 0, "denominator": 32, "rate": 0.0, "wilson_95": [0, 0.10717919825506533]}` |
