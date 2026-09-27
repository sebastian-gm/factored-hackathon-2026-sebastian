# Production readiness

This synthetic-data development service is not ready for real customer data or real banking actions. Before production it needs:

- a real identity provider, private networking, and reviewed access policies;
- a core banking integration and a scheduled, monitored data pipeline;
- model-risk governance and regulatory review for each country;
- human review of Portuguese and load behavior at scale;
- backup, disaster recovery, and on-call ownership;
- verified storage recovery, retention enforcement, and incident procedures.

The owner-approved low-cost development deployment uses public HTTPS endpoints with owner-IP restrictions and application authentication. Treat that as a temporary development boundary. Before any production use, move the app and its dependencies behind private networking: private Container Apps ingress, PostgreSQL private access, private endpoints for Key Vault and the container registry/state storage, and controlled outbound access. Define and test the network rules, identity roles, and operational response for address and route changes before moving beyond synthetic data.

The same controlled workflow could later support fee disputes, card replacement, or payment-status questions after separate policy and safety review.

The development PostgreSQL firewall allows Azure service sources across subscriptions, plus the owner IP. Strong passwords in Key Vault, a restricted database role and verified TLS reduce the risk but do not establish app-only network isolation. Replace this exception with VNet integration and PostgreSQL private access before production. Simulated OTP is not independent MFA.

## Operational persistence follow-up

The dev API uses non-owner Postgres state, forced customer/run/session RLS, four pooled connections, transactional idempotency and post-commit readback. Alembic migrations use the owner credential separately. Verify backup restore and retention, sustained concurrency, bounded model spending across restarts, and independently anchored audit exports before production. A privileged owner can rewrite an entire unanchored hash chain. The card-state repository is durable; a customer-facing freeze/step-up workflow remains separate work. Simulated OTP still is not independent MFA.


## Staff authorization and reset (dev limitation)

Staff endpoints use a server-configured demo role and the existing customer/run/session
RLS. They expose only the current workspace. Production needs federated staff identity,
queue/task-scoped grants, assignment authorization across customer sessions, and an
independently reviewed administrative reset/retention design. Azure retains the customer
role and reset disabled; no RLS broadening or new cloud resource is implied.
