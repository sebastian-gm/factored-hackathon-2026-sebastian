# Final evaluation preflight — execution held

Sebastian approved the priced [final-run plan](final-run-plan.md) with a **$12 cumulative ceiling** on 2026-09-27, and explicitly withheld the start signal until the lead's acceptance fixes, matcher v2, and NLU prompt v4 are merged with green gates. This packet is read-only preparation. No B1, P/Gemini, P/Sonnet, or final judge system run was started here; no final-run output directory was created.

| Gate | Current readback in this AI worktree | Required at start |
|---|---|---|
| Frozen suite integrity | `python -m evals.heldout` without `--run` verified the committed manifest and 200-case aggregate structure (70 normal, 40 ambiguous, 40 human-required, 50 security) before stopping on a missing private binding file. No row-level result was printed or saved. | Re-run the read-only preflight against the final clean implementation and verify all 200 persona bindings, ownership, suite/binding hashes, and overlay renders. |
| Private binding | `artifacts/evaluation-authoring/customer-bindings.json` is absent in this worktree. | Lead supplies the already frozen private artifact under ignored mode-0600 storage, verifies its frozen hash, and reruns preflight. Do not create or edit bindings from model outcomes. |
| Lead fixes and matcher v2 | PR #30 merged matcher v2 and the lead's final route/budget integration; the separate acceptance fix merge also landed in `main`. This AI worktree has not rerun a frozen preflight against their combined SHA. | Verify merged SHAs, matcher version/artifact, acceptance fixes, and green CI gates on the final frozen implementation. |
| NLU prompt | `prompts/nlu/v4.md` and its runtime route merged through PR #12; v4 has only synthetic development evidence. | Record its unchanged content hash. No frozen-suite tuning. |
| Model routes | `config/models.yaml` pins Gemini and Sonnet to ZDR `google-vertex/global`; Grok remains the failure-only `xai/zdr` fallback. The NLU lane prepares direct Jev `jev-1.13.0` risk-cue second opinion for Gemini only; the paired judge helper prepares Jev beside Sonnet. | Recheck exact served IDs, route health, TypeSafe account terms/payload scope and current per-provider prices before any paid case. |
| Final runner | `evals.heldout --run --final` now implements real-route selection and isolated state; ordinary `--run` stays mock. The AI lane's paired-judge selection/reporting remains PR #31 work. | Verify the final adapter on the frozen SHA, bind the private personas, and run the preselected paired judge sample only after the start signal. |
| Spend control | The lead merged a Postgres cumulative reservation gate. PR #31 routes Jev NLU and judge calls through that same gate; this merge integration is under validation here. | Verify one durable OpenRouter **and TypeSafe** budget stops before **$12**, including unknown-cost reserves, across cases/processes and readbacks. |
| Key and activation | Persistent `.env` remains mock/unapproved; no production real-model route was enabled. | Keep credentials process-local and out of artifacts/Git; enable only for the explicit final start under the approved ceiling. |
| Human judge calibration | The ignored 50-row sheet is blank; prior Sonnet and Jev smoke items were paired 3/3. The dual-judge helper has offline tests only. | Human ratings and same-item Sonnet/Jev scoring are required before judge-vs-human claims; report both judges' agreement and their mutual agreement. Never delegate objective outcomes to either judge. |

The read-only `evals.heldout` invocation returned `FileNotFoundError` for the private binding after manifest verification. This is a **preflight blocker**, not an evaluation failure. It did not enter `run()` or write `access.json`. The next attempted final command must be a fresh read-only preflight; `--run` remains prohibited until Sebastian supplies the start signal and every gate above passes. Keep the 200 frozen cases, labels, bindings, repeat IDs, and final prompt fixed after the freeze.

## Lead integration update

PR #12 and #29 have been merged. The real-route adapter and shared Postgres
reservation gate are implemented and tested on independent authored fixtures;
see the current [progress log](../status/progress-log.md) for release verification.
The table above preserves the AI lane's earlier preflight, including its missing
private binding. No lead frozen preflight or final run was performed in this layer.
Follow the adapter instructions in [final-run-plan.md](final-run-plan.md) only
after Sebastian supplies the start signal.

## Jev release update — handoff 10

The current release has merged #31, #33 and #34. The TypeSafe key is in Key Vault,
with no local key left. Production risk unions, the durable shared budget and the
restricted Azure release passed the checks in the current progress-log section.
The private final bindings/splits are present in the lead checkout; their contents
were not reopened during this release. Frozen preflight and execution still await
Sebastian's go and run inside the gated single command. The required accepted-SHA
receipt is `artifacts/azure/jev-release.json`. Its flags and exact SHA are checked
by the launcher before any frozen read or paid final call. The historical table
above describes the AI lane's earlier worktree, not current release readiness.
