# Production Thinking

**A restricted synthetic-bank demo runs; a production bank service does not.**
Official [v2](evaluation/final-v2-error-analysis.md) and
[v3](evaluation/final-v3-results.md) failed full safety gates. This summarizes
recorded evidence; no new cloud check or approval.

## What runs today

- Azure Container Apps hosts web/BFF and internal API: restricted HTTPS ingress,
  **min 0 / max 1** replicas. Managed identities pull private images; Key Vault
  supplies secret-scoped API credentials.
  [Deployment boundary](azure-private-dev-plan.md), [last preview verification](status/progress-log.md).
- PostgreSQL uses a non-owner role, verified TLS and forced customer/run/session
  RLS. Sessions, proposals, cases, cards and handoffs persist.
  Code controls eligibility, confirmation, fresh step-up and idempotency;
  **success requires committed read-back**. Audit privileges are append-only with
  a hash chain, which has no independent external anchor.
  [Architecture](architecture.md), [local recovery evidence](ops-recovery.md).
- Gemini 3 Flash performs NLU/phrasing; Jev adds risk-cue union; Grok 4.20 is
  failure-only fallback. Gemini's first attempt is limited to 6 seconds.
  Durable reservations cover paid calls, retries, Jev and
  fallback: **$3 per UTC day**, plus configured lifetime run caps. Unknown costs
  retain reserves; budget/DB failure stops calls. Azure's approximately $50 monthly
  budget **alerts, rather than caps**, spending. [Routes](../config/models.yaml),
  [budget ADR](adr/0014-durable-model-budget.md).

The preview verified warm reads, not paid-chat acceptance. Cold config failed after
**50.560 s**. The locally tested startup fix is not recorded as deployed: bounded
GET retries, no POST replay. [Diagnosis](evaluation/preview-startup-diagnosis.md).

## Work before real use

**Planning assumptions, not quotes:** pilot engineer-days and incremental monthly
USD allowances, excluding labor, tax, staffing and contracts. Overlapping tasks
are not additive. The dated dev plan modeled **$34.63/month before models**;
networking/HA/traffic need fresh pricing and approval.
[Price assumptions](azure-private-dev-plan.md#live-east-us-2-price-check).

| Gap | Required work | Rough effort / cost assumption |
| --- | --- | --- |
| Private network | VNet/private DB, Key Vault/registry endpoints, DNS/egress. Today's Azure-services DB firewall admits other subscriptions; not app-only isolation. | 4–8 days; +$40–150/month |
| Identity/MFA | Real customer/staff IdP, independent MFA, reviewed assignment grants and revocation. Simulated OTP is not a second factor. | 3–7 days; +$0–100/month, license-dependent |
| Observability/SLOs | Redacted telemetry, failure/budget/queue alerts, on-call; establish availability, latency and freshness SLOs from measured load. | 2–5 days; +$10–50/month |
| Scaling/recovery | Load-test beyond max 1, pool/backpressure limits, Azure PITR and RTO/RPO rehearsals; price HA/DR separately. | 3–7 days; +$20–100/month |
| Cold starts | Verify fix; choose scale-to-zero versus approved warm replicas. Two-app compute: $11.83–39.42/month before grants/other charges; replaces existing compute. | 0.5–1 day; [dated estimate](submission/checklist.md#prepare-judge-access-and-rehearse-the-deployed-product) |
| Data scheduling | Approved cloud lake, scheduled contracts/DQ/promotion, freshness/source-change alerts and serving authorization. | 2–4 days; +$5–25/month |
| Human queue operations | Assignment grants, aging/routing alerts, staffed escalation/feedback; workspace roles are not staffing. | 3–5 days; +$0–30/month; staffing unpriced |
| Bank/privacy/audit | Authorized bank adapters and country policy review; scoped purge/backups/legal holds, signed audit anchors and retention ownership. | 2–6 weeks; +$5–30/month audit storage; integration/security contracts unpriced |

Release requires independent safety acceptance, verified provider/account terms,
real identity and recovery evidence, approved costs and green CI for promotion to
`main`. **V4: TODO(results)**; no v4 case was opened here.
[Privacy/fairness](responsible-ai.md), [retention gaps](security/privacy-and-retention.md),
[release/access gates](submission/checklist.md).
