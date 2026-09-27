# Aclara

Aclara helps a signed-in customer understand an unrecognized charge, file an eligible
dispute, or reach a human with verified context, in Spanish and Brazilian Portuguese.
It is a **synthetic-data demonstration**, not a bank or a real dispute service.

The scoped bank API, deterministic policy, durable operational state, calibrated
charge matcher and guarded language adapters are implemented. The runtime defaults
to `LLM_PROVIDER=mock`; an unconfigured proposed-system mock falls back to rules.
The redesigned customer, Agent Desk and Ops frontend is in
[PR #17](https://github.com/sebastian-gm/bank-agent-lab/pull/17). Customer APIs include
fresh-OTP card freeze. Typed staff/Ops APIs are shipped and PR #17 integrates them,
including versioned claims, measured workspace counts and gated reset. A source merge does not establish deployed behavior.

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

Live Agent Desk and Ops are limited to a trusted identity's current workspace.
The cloud defaults to customer role with reset disabled; a global staff queue and
production staff identity are not implemented. The [video draft](docs/submission/video-script.md) includes
release checks before recording; these instructions do not claim the latest UI has
been deployed.

## Local quickstart

Requirements: Docker Compose, Python/uv and Node/pnpm, using the versions pinned in
[CI](.github/workflows/ci.yml) and [the web package](apps/web/package.json).

1. Copy `.env.example` to ignored `.env` if it does not already exist. Set your own
   local Postgres and demo login passwords. Keep `LLM_PROVIDER=mock` and real calls
   disabled. Never overwrite an existing worktree's credentials.
2. Run `uv sync --extra dev`, then `make up`. This prepares the non-owner app role,
   migrates Postgres and waits for healthy services.
3. Open `http://localhost:3000`, or your configured `WEB_HOST_PORT`. Sign in with
   the local `DEMO_USERNAME`/`DEMO_PASSWORD`, then the simulated OTP.
4. Run `make checks`, `uv run --no-sync python -m scripts.local_smoke`, and
   `uv run --no-sync python -m scripts.test_postgres` for application, smoke and
   isolated Postgres checks.

Every worktree needs its own `COMPOSE_PROJECT_NAME` and host ports. Keep the shared
absolute `LAKE_DIR` outside the checkout. Organizer inputs may be read only from
local `LOCAL_RAW_DIR`; they are not needed for the fixture demo or CI. See the
[data runbook](docs/data/pipeline-runbook.md) for approved local pipeline work.

For the new UI and its fixture/live browser commands, use
[PR #17's frontend guide](https://github.com/sebastian-gm/bank-agent-lab/blob/feat/frontend/apps/web/README.md).
`pnpm test:e2e --live` uses a local mock bank and project-generated records, not a
paid model or Azure. Do not execute the frozen test suite as a development smoke;
follow the [evaluation protocol](docs/evaluation/eval-protocol.md).

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
sizes and unequal policy mix; they do not isolate causal fairness effects. Human
labels and fluent Portuguese review remain pending.

| Still required for final claims | Status |
| --- | --- |
| Approved real-model B1/P comparison and independent judge | TODO(results): real-model SAR, safety, repeat variability and judge validation |
| Deployed latency, cost and operational limits | TODO(results): cloud p50/p95, per-attempt/per-SAR cost and sustained capacity |
| Language review, human workload and phrasing ablation | TODO(results): reviewed language scores, agent handling time and template comparison |

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
