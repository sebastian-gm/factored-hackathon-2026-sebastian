# Reactive evaluation

Run `uv run --extra dev python -m evals.runner --system B1 --scenarios evals/dev_scenarios_v2.yaml --repeats 2 --tag <git-sha>`.

The legacy 32 scripted v1 cases remain valid and run with the original command. V2 scored runs require independent gold labels. The authored v2 dev suite contains 32 ES/PT cases, including six fault types per language. Each execution gets a fresh runtime, identity session, conversation and run ID; systems and repeats share only immutable fixture input. Controls are injected through Python construction, never HTTP headers or customer messages.

The customer consumes initial scripted turns, then responds to `response_type` (the existing API spelling of `ResponsePlan.type`). The aliases `choose_txn` and `ask_clarification` are accepted. Reply tables repeat their last value; absent entries use `no sé` / `não sei`. A `choose_ref` only selects an actually displayed scoped candidate. Terminal API plans end the dialogue. Maximum turns bounds every run.

`customer_knowledge.transaction_refs` maps recollection aliases to authored fixture records or scoped handles. `protected_values` supplies literal values for disclosure checks. Each gold reference must resolve. Transaction overlays and record patches are supported. Organizer persona selectors and other overlay kinds require an explicit future binding adapter; the harness rejects them instead of silently substituting a customer. This dev suite uses only authored fixtures.

Fault triggers are explicit boundaries (`message`, `confirm_action`, `MATCH`, `create_dispute`, `read_back`), or `always` / `first_turn`. Unreached faults fail execution. Expiry, stale step-up, tampering and replay exercise real HTTP guards; dependency failures exercise the safe handoff path. Model-specific faults are added with P integration.

Private case JSONL and aggregate `results.json` are written under ignored `artifacts/`. `docs/evaluation/results.md` renders only that aggregate. It reports gold-based SAR denominators, attempts, containment, escalation errors, queue/language/fallback routing, handoff field completeness and a deterministic rubric, eight unsafe categories with bounds, case-clustered latency bootstrap intervals, and cost. Infrastructure is shown separately using the last verified deployment estimate. Mock charges are zero. No LLM judge or live quality claim is made. Gold code cannot import policy code (CI AST check).

Limits: safety detectors combine action traces, readbacks, gold targets, known forbidden values and conservative DLP. They do not establish complete semantic safety. Repeats are correlated; intervals and `3/n` on repeat counts must not be interpreted as independent production trials. Model-generated-language cross-vendor review and human Spanish review remain pending. This is development data, not held-out evaluation.
