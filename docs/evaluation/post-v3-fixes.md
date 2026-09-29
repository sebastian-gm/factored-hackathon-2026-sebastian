# Post-v3 analysis and fixes (2026-09-28)

**Post-hoc.** V3 (release `e12efc7`, fresh 100-case suite, after-fixes) is a
reported result: P-Gemini passed 77/100 vs B1 52/100, SAR +11 pp (95% paired
CI +5 to +17), with judging partial (28/60). After its report, the v3 suite
and traces were opened for failure analysis. **V3 is therefore retired to
development data**: its numbers below are regression checks on seen data, not
evaluation results. Any new claim needs a fresh, independently authored suite
(v4) that the fix author has not seen.

## The 23 P-Gemini failures: six causes

| # | Cause (cases) | Where | Fix |
|---|---|---|---|
| 1 | "no recuerdo qué es" / "não lembro do que se trata" treated as *uncertainty*, which discarded a confident MATCH (top probability 1.0) and asked a vague clarification; two clarifications then ended in `ESC-04` (11) | `agent/selection.py` | Not knowing what an identified charge *is* now counts as unfamiliarity (ADR-0015 §1 offer), not uncertainty about which charge; real uncertainty ("no recuerdo el monto", "no sé cuál") is unchanged |
| 2 | Distress with an intensifier ("estoy **muy** angustiado") missed; packet had only `ESC-01` (2) | `policy/rules/guards.py` | Distress pattern allows intensifiers and common forms; never infers protected attributes |
| 3 | Spanish lost-card phrase ("Perdí mi tarjeta") not recognized; a freeze decline rebuilt the packet with `FRD-01` only, dropping `ESC-02` (2) | `agent/nlu/rules.py`, `api/workflows.py` | Spanish lost/stolen phrases route to fraud; freeze results reuse the session's latest fraud-packet reasons |
| 4 | LLM outage whose deterministic fallback could not classify → out-of-scope abstention (2) | `api/app.py` | Model outage + unsuccessful fallback is a safe failure (`COM-01`, `ESC-04`), per ADR-0015 §3 |
| 5 | Stale OTP: the simulated customer never renewed step-up (2) | `evals/bound_execution.py` (harness) | A customer whose scenario says `provides_new_step_up: true` renews once and confirms the same proposal; the API already rechecks it. Declining customers (v1, dev fixtures) keep the refusal path |
| 6 | Cross-customer attempts routed Portuguese handoffs as Spanish and dropped a legal cue (4) | `api/app.py`, `agent/nlu/rules.py` | Language taken from the message when no conversation language exists; legal/distress cues retained in the security handoff |

Also found and fixed:

- **Wrong-language phrasing.** The phrase model received only type/language/facts,
  invented a generic clarification and once answered a Spanish customer in
  Portuguese. Prompt `phrase@v2` rephrases the approved text; a draft whose
  detected language differs is rejected and the template is used.
- **Judge truncation.** Sonnet judge output was capped at 256 tokens and stopped
  v3 judging; the cap is now 1024.
- **Web: stale OTP logged the customer out.** The BFF treated the step-up 401 as
  a dead session and cleared the cookie. It now maps it to `step_up_required`,
  keeps the session, and the confirmation dialog renews OTP and confirms the
  same proposal once.

## Latency

- The official v2/v3 runs read the serving ledger from **Azure Postgres over the
  internet from the workstation** (`EVAL_SERVING_DSN` = the Azure DSN). B1, with
  no model calls, measured ~2.0 s p50 per turn that way versus 11–51 ms against a
  local serving database. Deployed containers read Postgres in-region, so the
  reported turn latencies overstate deployed latency. The v3 limitation stands as
  reported.
- A chat turn re-read the customer's 120-day projection ~4 times. A
  request-scoped snapshot memo cuts serving queries by ~30%.
- The p95 tail was single Gemini calls of 9–20 s. The first attempt now times out
  at 6 s and the existing bounded second attempt keeps the full timeout.

## Verification (dev scope `dev-gate/post-v3`, $1 cap)

| Check | Result |
|---|---|
| Unit/API tests, Ruff, strict mypy, interfaces, policy catalog | pass |
| B1 authored dev harness | 32/32 |
| Browser tests (fixtures 20, live 8, staff 1) | 29/29 |
| B1 on v3 (seen; local, $0) | 52 → 65/100 (shared orchestration fixes) |
| **Real P-Gemini on all 100 v3 cases (seen)** | **100/100**: 23/23 prior failures fixed, 0/77 regressions |
| Real P dev gate (`scripts.dev_gate real --profile post-v3`) | **passed**: no-fault 20/20, frozen confirmation 18/20 (ES 10/10, PT 8/10), faults 12/12 all triggered, 0 unsafe/forbidden |

Spend: $0.40 of the $1 `dev-gate/post-v3` allowance ($0.27 v3 regression, $0.13
dev gate). Cumulative charged across all scopes ≈ $4.23 of the $12 ceiling.
