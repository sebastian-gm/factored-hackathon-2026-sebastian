# Aclara

Aclara helps a signed-in customer understand an unrecognized charge, file an eligible
dispute, or reach a human with verified context, in Spanish and Brazilian Portuguese.
It is a **synthetic-data demonstration**, not a bank or a real dispute service.

Customer Chat, Agent Desk and Ops run against promoted organizer serving data and
durable Postgres activity. B1 uses rules; P uses Gemini 3 Flash, failure-only Grok
4.20 fallback, Jev risk-cue union, guarded phrasing and matcher v2. Local defaults
remain `LLM_PROVIDER=mock`. The private real-model release and browser smoke are
verified in the [progress log](docs/status/progress-log.md); final held-out acceptance
is pending. See [model comparison](docs/ml/model-comparison.md),
[Jev evidence](docs/ml/typesafe-jev-comparison.md), and
[matcher v2](docs/ml/model-card-charge-matcher-v2.md).

## Architecture in 60 seconds

**Understand → Decide → Act → Verify → Escalate.** Understand extracts language and
transaction clues. Matching searches only the authenticated customer's candidates.
Code decides eligibility and escalation from versioned rules. An action requires an
exact server proposal and explicit confirmation; sensitive actions require fresh OTP.
The service commits, reads the result back, and only then reports success. A human
receives verified facts, actions, reasons and unresolved questions when required.

The LLM has no identity, policy or write authority. PostgreSQL uses a non-owner role
and forced customer/run/session row-level security. Model failure has a deterministic
fallback. Explanations show sources and rule IDs, never model thinking. See the
[architecture and state machine](docs/architecture.md),
[policy catalog](docs/policy-catalog.md) and [threat model](docs/security/threat-model.md).

## Judge quickstart — submission draft

Open the [restricted deployed demo](https://ca-web-aclara-dev-eastus2.lemonbeach-1b769de0.eastus2.azurecontainerapps.io/).
**Access code and demo personas provided in the submission email.** Credentials are
never included in this repository. Use the provided password and the simulated SMS
OTP; the SMS panel is part of the demo, not independent MFA. Do not enter real data.

**Access is not judge-ready yet:** the deployment currently permits the owner's IP.
A judge outside that allowlist receives a denial. The lead must arrange approved
judge access and verify the deployed revision before sending the submission. A
separate access-code gate is not implemented. No access expansion is implied here.

Use the fixture details supplied with the personas for these guided scenarios:

| Try | What to inspect |
| --- | --- |
| ES: ask about the supplied recent pending charge | A status explanation, its transaction record and rule in “¿Por qué?”. No promised settlement date. |
| PT: describe the supplied ambiguous charge | Candidate selection and clarification; confirm the exact eligible dispute, then inspect the verified case receipt. |
| ES/PT: report the supplied stolen-card scenario | Human routing, fresh OTP and a separate freeze confirmation. A freeze is claimed only after read-back. |
| Cancel a proposed action | Cancellation must not create a dispute or freeze. Required fraud review still continues. |
| Ask for another customer's transactions | Refusal with no other-customer records. Do not use real names or identifiers. |

Live Agent Desk and Ops are limited to the trusted identity's current workspace.
Two deployed demo personas have Ops roles; two are customers. Cloud reset is disabled.
Judge access, recording and publication steps are in the [checklist](docs/submission/checklist.md).

## Local quickstart

1. Copy `.env.example` to ignored `.env`; set local Postgres/demo passwords and `LOCAL_RAW_DIR`. Use persistent ignored `LAKE_DIR=./lake` in this checkout.
2. Run `uv sync --extra dev --extra data-ml`, `python -m scripts.local_ops`, then `docker compose up -d --wait postgres` and `docker compose run --rm migrate`.
3. Run `python -m aclara.data.cli build --lake lake --no-reports`, then `python -m scripts.load_demo_serving --target local`.
4. Run `make up`, open <http://localhost:3000>, then run `make checks` and `python -m scripts.local_smoke`. Four server-bound personas share the configured demo password; the UI displays simulated OTP.

Organizer inputs are never required for CI. Isolated browser and database tests use authored fixtures. Runtime serving mode fails closed if its promoted dataset, clock or persona bindings are missing; it never falls back to the authored ledger.

Run `uv run --no-sync python -m scripts.test_postgres` for isolated database integration tests. For reactive evaluation, use `uv run --no-sync python -m evals.runner --system P --scenarios evals/dev_scenarios_v2.yaml`. See the [harness guide](docs/evaluation/harness.md) for repeats, faults and aggregate outputs.

Compose project names and host ports are set in ignored `.env`. The default pipeline lake is persistent `~/aclara-lake`; this session uses ignored `./lake` to honor repository-only writes. Source records are read only through `LOCAL_RAW_DIR`. Generated bronze/silver/gold/manifest files and serving reports remain ignored; no organizer rows are CI inputs or artifacts.


## Headline evaluation — mock diagnostic, acceptance failed

The controlled held-out diagnostic used implementation `564f008c` on 2026-09-27.
P's unconfigured mock fell back to B1. It provides **no evidence of real-model
improvement**, and later staff/API/frontend changes were not evaluated in that run.
The table is derived from the corrected aggregate `results.json` exports:
[B1](docs/evaluation/heldout-run01-B1.json) and
[P/mock](docs/evaluation/heldout-run01-P-mock.json). Their headers record the dataset,
policy, matcher, prompts, prices and measurement correction. See the
[report](docs/evaluation/heldout-run01.md) for access and rescore history.

| Metric / JSON field | B1 | P/mock |
| --- | --- | --- |
| Executed / workload (`execution`; `header.sample_size`) | 198/200 | 200/200 |
| SAR / in scope (`sar_in_scope`) | 67/193 (34.7%) | 67/193 (34.7%) |
| SAR / eligible (`sar_eligible`) | 67/134 (50.0%) | 67/134 (50.0%) |
| Automation attempts / in scope (`automation_attempt_share`) | 83/193 (43.0%) | 83/193 (43.0%) |
| Containment / workload (`containment`) | 86/200 (43.0%) | 86/200 (43.0%) |
| Correct complete transfer / must transfer (`escalation_recall`) | 0/66 (0.0%) | 0/66 (0.0%) |
| Handoff present / must transfer (`handoff_presence_recall`) | 54/66 (81.8%) | 54/66 (81.8%) |
| Unnecessary transfers / eligible (`unnecessary_transfers`) | 60/134 (44.8%) | 60/134 (44.8%) |
| Routing accuracy / explicit gold (`routing_accuracy`) | 5/9 (55.6%) | 5/9 (55.6%) |
| Forbidden actions (`unsafe.unauthorized_action`) | 6/198 (3.0%) | 6/200 (3.0%) |
| Materially incorrect outcomes (`unsafe.materially_incorrect_outcome`) | 9/198 (4.5%) | 9/200 (4.5%) |
| Local turn p50 / p95 ms (`latency.turn`) | 1.43 / 2.18 | 1.59 / 2.42 |
| Local case p50 / p95 ms (`latency.case`) | 2.55 / 4.14 | 2.53 / 4.65 |
| Model cost per attempted case / per SAR (`cost`) | US$0.00 / US$0.00 | US$0.00 / US$0.00 |

Both SAR/in-scope Wilson 95% intervals are 28.36–41.67%. Two B1 fault boundaries
were unreachable; the workload denominator retains them. Handoff presence alone is
not successful escalation. Six forbidden ESC-04 dispute writes per system caused
policy/action safety failures; these were not observed authentication bypasses.
The same events appear in both unsafe categories and must not be added together.

The disclosure, confirmation/step-up, unverified-success, grounding and refund-promise
detectors each observed 0/198 B1 and 0/200 P/mock cases. Their rule-of-three upper
bounds are 1.52% and 1.50%, respectively; zero observed does not mean zero risk.
Detector limitations and opportunity denominators are in the JSON/report. Latency
is local in-process system time, excluding network, cloud, models and customer think
time; bootstrap intervals are in `latency`. Model cost excludes prior authoring
and infrastructure. It is not a forecast of real-model operating cost.

The [paired/repeat comparison](docs/evaluation/heldout-run01-comparison.json) reports
SAR difference 0 with a 95% interval [0, 0], exact McNemar p=1 and 0/100 repeat flips.
[Language and segment slices](docs/evaluation/heldout-run01.md#slices) include sample
sizes and unequal policy mix; they do not isolate causal fairness effects. Independent held-out human labels and fluent Portuguese review remain pending. A separate [nine-case human es-CL check](docs/ml/model-card-charge-matcher-v2.md) is available.

| Still required for final claims | Status |
| --- | --- |
| Approved real-model B1/P comparison and independent judge | TODO(results): real-model SAR, safety, repeat variability and judge validation |
| Deployed latency, cost and operational limits | TODO(results): evaluation p50/p95 and per-attempt/per-SAR cost; sustained capacity remains unmeasured |
| Language review, human workload and phrasing ablation | Pending development/human review: phrasing ablation, fluent language review and agent handling time |

Containment alone is not success. The [trade-offs](docs/tradeoffs.md) distinguish the
completed normalized-slot matcher experiment from end-to-end evaluation.

## Evidence and limits

- [Problem analysis](docs/problem-analysis.md), [DQ report](docs/data-quality-report.md),
  [provenance](docs/data-provenance.md) and [matcher model card](docs/ml/model-card-charge-matcher.md).
- [Requirements and judging criteria](docs/requirements-traceability.md),
  [privacy and retention](docs/security/privacy-and-retention.md),
  [limitations](docs/limitations.md) and [production readiness](docs/production-readiness.md).
- [Business projection](docs/evaluation/business-projection.md),
  [slide draft](docs/submission/slides.md) and [verified progress](docs/status/progress-log.md).

Organizer rows, credentials, private evaluation traces and model thinking do not
belong in a submission. This repository remains private.
