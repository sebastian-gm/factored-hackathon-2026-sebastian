# Production readiness

**This is a private synthetic-data development service, not a real bank deployment.**
The [frozen mock diagnostic](evaluation/heldout-run01.md) failed acceptance gates.
A successful build, local restore or smoke test does not override those failures.
The lead's verified release history is in the [progress log](status/progress-log.md);
this document does not claim a new deployment or approve wider access.

## Release gates and accountable work

| Area | Implemented / verified evidence | Required before real use | Owner |
| --- | --- | --- | --- |
| Outcome safety | Deterministic rules, scoped proposals, explicit confirmation and committed read-back; [workflow tests](../tests/test_workflow_api.py). | Fix policy/NLU/handoff failures on independent development cases; freeze a new version and follow the evaluation protocol. Passing the original diagnostic is not claimed. | Lead + AI, independent evaluator |
| Identity and staff | Password/simulated OTP, opaque expiring capabilities, revocation and fresh step-up; typed staff roles limited to the current workspace. | Real customer/staff IdP and independent MFA; task-scoped cross-customer grants, assignment authorization and access review. Simulated SMS is not a second factor. | Lead + identity/security owner |
| Network | Owner-IP HTTPS ingress, app login, non-owner database role, required verified TLS and Key Vault secrets. | Private app ingress, VNet/Postgres private access, private Key Vault/registry/state endpoints, controlled egress and tested DNS/route changes. | Lead + platform owner |
| Banking integration | Checksummed organizer serving ledger plus durable cases/cards/handoffs; eligible writes are synthetic. | Authorized core-bank adapters, reconciliation, failure semantics and independent policy/regulatory review per country. No refund/credit authority can be inferred from a demo case. | Bank owner + lead |
| Data platform | Local contracts, incremental silver, tested complete gold promotion, checksummed serving load. | Approved cloud lake, scheduled ingestion, freshness SLOs, source-change alerts and ongoing serving authorization review. | Data/ML + platform |
| Recovery | [Local logical restore](ops-recovery.md), session/case/trace read-back, forced RLS and audit checks. | Azure PITR, regional DR, realistic-volume RTO/RPO, key/identity recovery and monitored backup rehearsals. Local fixture timing is not a production recovery guarantee. | Platform + on-call |
| Model governance | Gemini/Grok routing, Jev union, durable Postgres spend limits and private real-call settlement are verified. | Same-suite approved model comparison, account/route terms (including unverified Jev standard-account ZDR), independent language/judge review, incident rollback and provider-change monitoring. | AI + model-risk owner |
| Language and fairness | Model-authored ES/PT workload, second-vendor PT cross-check, nine human es-CL OOD cases and aggregate language/segment slices. | Human dual labels, fluent PT/Spanish review, matched workload analysis and actionable disparity review. Country cannot stand in for language. | Evaluation + language reviewers |
| Operations | Readiness, durable state, bounded pooling and local browser/DB checks; [cold-start diagnosis](azure-startup-diagnosis.md). | Sustained-load limits, deployment-specific latency and safe startup handling, alert thresholds, incident playbooks and staffed on-call. Retry idempotent health reads only; do not retry uncertain writes. | Lead + platform |
| Audit and retention | Restricted append-only hash chain; private turns/execution content. | Independent signed audit anchors, explicit retention ownership, verified purge/legal holds and backup deletion policy. A privileged owner can rewrite an unanchored chain. | Security + data owner |
| Frontend release | Merged PR #17 and the real-model release verify customer/staff APIs, read-backs and measured Ops. | Latest release verified the web-to-API hop and deployed browser flows; reverify the recording revision. Native copy review and additional browser engines remain pending. | Frontend + lead |

## Known development network limitation

The approved PostgreSQL firewall enables **Allow public access from Azure services**
plus the owner's IP. It permits network sources across Azure subscriptions; it is
not app-only isolation. Strong separate app/admin credentials in Key Vault, a
non-owner role, forced RLS and `verify-full` TLS reduce risk but do not remove that
network limitation. Replace it with VNet integration and PostgreSQL private access
before production. Do not broaden ingress to make a frontend smoke pass.

The private release smoke verified the web-to-API hop and workspace-scoped Ops
roles. Reset remains disabled. Local recording tests cannot enable cloud reset.
Infrastructure budget alerts notify; model spend is separately capped through
durable Postgres reservations, including retries, fallback and Jev calls. See the
[budget ADR](adr/0014-durable-model-budget.md). Judge access still requires the
owner's approved route and read-back; the repository remains private.

## Other applications

The same pattern can support fee disputes, card replacement and payment-status
inquiries after separate scope and safety review. Each needs its own data contract,
policy rules, exact action proposal, verification source and human escalation path.
Fees remain human-only in this release. Card replacement would require address and
fulfillment authorization absent here; payment status would require reconciled core
ledger/rail evidence. Reuse the control pattern, not the current synthetic eligibility
rules or outcome rates.

## Latest release boundary

The [release progress log](status/progress-log.md) records runtime `07bccdc630e2b5eeb2dc746a7c3fe000718fd22c`:
Gemini default, Grok fallback, Jev risk support, matcher v2 and durable per-attempt
budget reservations. The capped smoke used four conversations and fourteen calls,
$0.00925008 total; this is not a capacity or final-acceptance result. Two demo Ops
identities and two customer identities retain customer/run/session scope; reset
remains disabled. Production needs federated individual credentials and reviewed
cross-customer assignment grants. Handoff 12 lifted the merge freeze for Option A
dev fixes. Re-release remains blocked on the dev gate and Sebastian's confirmation.
