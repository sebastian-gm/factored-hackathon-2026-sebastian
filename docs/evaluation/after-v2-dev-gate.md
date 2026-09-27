# After-v2 dev validation

This layer implements [ADR-0015](../adr/0015-post-v2-conversation-and-policy-contract.md).
V2 remains the official result. Fixes were informed by its disclosed post-hoc analysis;
there is no held-out rerun or improvement claim. Lead/AI implementers do not open
suite-v3 scenarios, selections, bindings or its authoring tool. PR #50 stays unmerged
until the dev gate passes and Sebastian separately authorizes it.

## Changes under test

Runtime policy version is **1.3.0**, distinguishing these routing/control semantics
from the official v2 release while retaining the numerical policy thresholds.

- Persist the selected offer handle, recognition count and prior intent. Re-read the
  owned transaction; pass `awaiting_recognition` and masked facts to prompt v5.
  Recognition ends in explanation. Denial reviews policy and proposes; confirmation,
  fresh OTP and committed readback still gate filing. Isolated yes/no is not consent.
- Preserve dispute intent through clarification. Changing the target clears the old
  offer. Cross-customer attempts clear pending decisions across the authenticated
  session; the second attempt creates/verifies a security handoff and revokes it.
- Carry all evidenced review/control reasons with deterministic primary routing.
  Known adjustment/transfer causes survive missing intake data; age and amount
  bands carry their underlying policy reasons. Dependency failures retain causes.
- Strict escalation recall and missed transfers use the same predicate per slice.
  Verified `existing-case` and product reads support the legacy `created-state`
  alias. An intermediate explanation/offer is not a terminal resolution claim;
  pending offers and cancellations never count as successful automation.
- **Baseline changes disclosed:** B1 ignores known merchant names and date tokens
  when extracting an amount, and follows the accepted explain/offer flow. Its two
  original dispute fixtures now include an explicit denial after the offer.
  Authorization/readback regression fixtures start with explicit denial where that
  is their precondition. No frozen suite bytes or gold were changed.
- Deferred #37 API additions expose call route/status/attempt and allowlisted risk
  flags/probabilities, preserving nulls and failed-call costs. Approved story hints
  map `demo.es.mx` to explain/fraud and `demo.pt.br` to ambiguity only when their
  trusted scoped projections support those stories. This grants no role/access.

The separate [v2 slice correction](final-v2-slice-correction.md) reads saved observations
only and leaves official files unchanged. It is a reporting correction, not a rerun.

## Cost and commands

Shared Postgres **scope `dev-gate/after-v2`, run ID `after-v2`, lifetime cap $1.00**.
All lead and AI paid dev runs use these same identifiers and reserve before calling.
Prior scopes are closed without resetting accounting. Prior charged/reserved exposure
is $3.07369789; including this dev cap and the prospective $3 v3 cap gives $7.07369789,
below $12. This step does not authorize release or v3 execution.

Sebastian approved the dev gate estimate of **$0.15–$0.30**, under the shared cap.
Run only on the clean merged candidate.

```bash
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 .venv/bin/python -m scripts.dev_gate mock --profile after-v2
LLM_REAL_CALLS_APPROVED=1 .venv/bin/python -m scripts.dev_gate real --profile after-v2
```

Outputs: ignored `artifacts/after-v2-dev/gate-structured-mock/` and `gate-real/`.
The command refuses to overwrite an existing run directory. Each case and progress
update is checkpointed; no automatic repeat of the confirmation set is authorized.
The confirmation adapter verifies the pre-fix hash from #47 before execution.
A budget denial stops the run and retains reservations. No credentials enter the
journal; it contains call accounting and schema-validated dev observations.

Acceptance: no-fault ≥18/20, frozen new confirmation ≥17/20, faults12/12 reached and
correct, zero unsafe/forbidden, B1 unchanged or better. Record measured results and
candidate SHA in the progress log, then stop. PT/dialect wording remains
model-generated; fluent-human review remains a limitation.
