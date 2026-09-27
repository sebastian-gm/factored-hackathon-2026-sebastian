# Aclara

Aclara helps a signed-in customer understand an unrecognized charge, file an eligible
dispute, or reach a human with verified context, in Spanish and Brazilian Portuguese.
It is a **synthetic-data demonstration**, not a bank or a real dispute service.

The scoped bank API, deterministic policy, durable operational state, calibrated
charge matcher and guarded language adapters are implemented. The runtime defaults
to `LLM_PROVIDER=mock`; an unconfigured proposed-system mock falls back to rules.
The redesigned customer, Agent Desk and Ops frontend is in
[PR #17](https://github.com/sebastian-gm/bank-agent-lab/pull/17). Customer APIs include
fresh-OTP card freeze; staff/Ops views still use explicitly enabled fixtures because
their APIs are pending. A source merge does not establish deployed behavior.

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

The Agent Desk and Ops demonstration must be labeled as fixtures until the lead's
staff APIs are integrated. The [video draft](docs/submission/video-script.md) includes
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

## Headline evaluation — awaiting held-out results

The [current report](docs/evaluation/results.md) is a development mock run. It does
not establish real-model quality. Final cells below must be populated from the
approved held-out run's aggregate `results.json`, with its workload, tag, dataset,
policy, matcher, model, prompts, price date and repeat counts. Do not use the UI's
illustrative `results.json` or historical operations as this comparison.

| Metric / JSON source | B1 | P |
| --- | --- | --- |
| Cases executed / `header.sample_size` plus missing-case report | TODO(results): B1 held-out sample | TODO(results): P held-out sample |
| SAR / in-scope, with interval / `sar_in_scope` | TODO(results): B1 SAR/in-scope | TODO(results): P SAR/in-scope |
| SAR / eligible / `sar_eligible` | TODO(results): B1 SAR/eligible | TODO(results): P SAR/eligible |
| Automation attempted / `automation_attempt_share` | TODO(results): B1 attempts | TODO(results): P attempts |
| Containment / `containment` | TODO(results): B1 containment | TODO(results): P containment |
| Missed / unnecessary transfers and routing / `missed_transfers`, `unnecessary_transfers`, `routing_accuracy` | TODO(results): B1 escalation quality | TODO(results): P escalation quality |
| Unsafe events: per type, count/denominator/upper bound / `unsafe` | TODO(results): B1 unsafe outcomes | TODO(results): P unsafe outcomes |
| Turn and case p50/p95 with intervals / `latency` | TODO(results): B1 latency | TODO(results): P latency |
| Cost per attempt / per SAR / `cost` | TODO(results): B1 cost | TODO(results): P cost |
| Language/segment outcomes and repeat flip rate | TODO(results): B1 slices | TODO(results): P slices and variability |

Containment alone is not success. Zero observed unsafe events would not establish
zero risk. Inference cost, authoring cost and infrastructure cost are separate.
Paired uncertainty, missing executions and human label-review status must accompany
any final comparison. The [trade-offs](docs/tradeoffs.md) distinguish the completed
normalized-slot matcher experiment from end-to-end evaluation.

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
