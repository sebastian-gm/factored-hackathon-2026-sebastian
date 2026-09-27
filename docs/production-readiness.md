# Production readiness

This synthetic-data development service is not ready for real customer data or real banking actions. Before production it needs:

- a real identity provider, private networking, and reviewed access policies;
- a core banking integration and a scheduled, monitored data pipeline;
- model-risk governance and regulatory review for each country;
- human review of Portuguese and load behavior at scale;
- backup, disaster recovery, and on-call ownership;
- verified storage recovery, retention enforcement, and incident procedures.

The owner-approved low-cost development deployment uses an owner-IP-restricted HTTPS web endpoint, an internal API in the same managed Container Apps environment, and application authentication. Treat that as a temporary development boundary. Before any production use, move the app and its dependencies behind private networking: private Container Apps ingress, PostgreSQL private access, private endpoints for Key Vault and the container registry/state storage, and controlled outbound access. Define and test the network rules, identity roles, and operational response for address and route changes before moving beyond synthetic data.

The same controlled workflow could later support fee disputes, card replacement, or payment-status questions after separate policy and safety review.

The development PostgreSQL firewall allows Azure service sources across subscriptions, plus the owner IP. Strong passwords in Key Vault, a restricted database role and verified TLS reduce the risk but do not establish app-only network isolation. Replace this exception with VNet integration and PostgreSQL private access before production. Simulated OTP is not independent MFA.

## Operational persistence follow-up

The dev API uses non-owner Postgres state, forced customer/run/session RLS, four pooled connections, transactional idempotency and post-commit readback. Alembic migrations use the owner credential separately. The customer-facing card-freeze workflow now includes fresh simulated OTP, action-hash confirmation, committed readback and a Fraudes handoff. Simulated OTP still is not independent MFA.

The [local logical recovery rehearsal](ops-recovery.md) passed full-table checksums, session/case/handoff/trace recovery, audit verification and forced RLS on a tiny authored fixture. Azure PITR, regional DR, scheduled backup monitoring, retention and realistic-volume recovery remain unverified. Also verify sustained concurrency, bounded model spending across restarts, and independently anchored audit exports. A privileged owner can rewrite an entire unanchored hash chain.

Scale-to-zero [startup diagnostics](azure-startup-diagnosis.md) reproduced a first-request timeout; warm health checks succeeded. The smoke uses bounded health/readiness polling. Production needs an explicit availability target, measured startup/load behavior and a costed capacity decision.

## Evaluation acceptance

The frozen B1/P-mock [diagnostic](evaluation/heldout-run01.md) failed acceptance gates: SAR was 67/193 for each system, with six forbidden dispute writes and incomplete required handoffs. Unit, integration and deployment checks passing does not establish safe end-to-end behavior on broader language. Develop fixes on independent development fixtures; preserve the diagnostic and its pinned system/measurement SHAs. Later packet additions have not been evaluated on the frozen suite. Real-model comparison, human label validation and cross-vendor judge validation remain pending.


## Staff authorization and reset (dev limitation)

Staff endpoints use a server-configured demo role and the existing customer/run/session
RLS. They expose only the current workspace. Production needs federated staff identity,
queue/task-scoped grants, assignment authorization across customer sessions, and an
independently reviewed administrative reset/retention design. Four private organizer-backed demo personas have server-bound roles; two Ops personas can demonstrate their own workspace, and two remain customers. They share the owner-only demo credential; production needs individual staff credentials. Reset remains disabled. No cross-customer or cross-session RLS widening is introduced.
