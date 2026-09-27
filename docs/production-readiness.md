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
| Banking integration | Authored ledger plus durable cases/cards/handoffs; eligible writes are synthetic. | Authorized core-bank adapters, reconciliation, failure semantics and independent policy/regulatory review per country. No refund/credit authority can be inferred from a demo case. | Bank owner + lead |
| Data platform | Local contracts, incremental silver, tested complete gold promotion, checksummed serving load. | Approved cloud lake, scheduled ingestion, freshness SLOs, source-change alerts and authorization review before binding organizer-derived serving data to runtime. | Data/ML + platform |
| Recovery | [Local logical restore](ops-recovery.md), session/case/trace read-back, forced RLS and audit checks. | Azure PITR, regional DR, realistic-volume RTO/RPO, key/identity recovery and monitored backup rehearsals. Local fixture timing is not a production recovery guarantee. | Platform + on-call |
| Model governance | Approval, schema/privacy flags, budget reservation, DLP and fallback are mock-tested. | Same-suite approved model comparison, account/route terms, durable shared spend limits, independent language/judge review, incident rollback and provider-change monitoring. | AI + model-risk owner |
| Language and fairness | Model-authored ES/PT workload, second-vendor PT cross-check, aggregate language/segment slices. | Human dual labels, fluent PT/Spanish review, matched workload analysis and actionable disparity review. Country cannot stand in for language. | Evaluation + language reviewers |
| Operations | Readiness, durable state, bounded pooling and local browser/DB checks; [cold-start diagnosis](azure-startup-diagnosis.md). | Sustained-load limits, deployment-specific latency and safe startup handling, alert thresholds, incident playbooks and staffed on-call. Retry idempotent health reads only; do not retry uncertain writes. | Lead + platform |
| Audit and retention | Restricted append-only hash chain; private turns/execution content. | Independent signed audit anchors, explicit retention ownership, verified purge/legal holds and backup deletion policy. A privileged owner can rewrite an unanchored chain. | Security + data owner |
| Frontend release | PR #17 integrates shipped customer/staff APIs with scoped read-backs and measured Ops. | Lead must verify the web-runtime-to-API hop under the owner-IP boundary, deployed browser flows and CI browser wiring. Native copy review and additional browser engines remain pending. | Frontend + lead |

## Known development network limitation

The approved PostgreSQL firewall enables **Allow public access from Azure services**
plus the owner's IP. It permits network sources across Azure subscriptions; it is
not app-only isolation. Strong separate app/admin credentials in Key Vault, a
non-owner role, forced RLS and `verify-full` TLS reduce risk but do not remove that
network limitation. Replace it with VNet integration and PostgreSQL private access
before production. Do not broaden ingress to make a frontend smoke pass.

Before releasing PR #17, the lead can run `node scripts/check-api-hop.mjs` inside
its web container with the existing server-side API URL. The probe emits only
health/persona status metadata. Local success does not prove the Azure hop. The
restricted cloud retains customer role and reset disabled; enabling local ops tests
does not authorize cloud staff access or reset.

Budget alerts are notifications, not a spending cap. Current provider accounting is
process-local and can reset across restarts. Real calls require a concrete approved
cost estimate; credit on a key does not supply permission. Judge access is also
pending approval and read-back; the repository and current demo remain private.

## Other applications

The same pattern can support fee disputes, card replacement and payment-status
inquiries after separate scope and safety review. Each needs its own data contract,
policy rules, exact action proposal, verification source and human escalation path.
Fees remain human-only in this release. Card replacement would require address and
fulfillment authorization absent here; payment status would require reconciled core
ledger/rail evidence. Reuse the control pattern, not the current synthetic eligibility
rules or outcome rates.
