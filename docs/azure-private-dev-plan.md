# Azure restricted development deployment

Approved by Sebastian on 2026-09-26 for `Seb Azure Sandbox`, East US 2, resource group `rg-aclara-dev-eastus2`. Stop before provisioning if the live modeled monthly estimate exceeds USD 40. The earlier under-$30 target remains desirable. No use of the CLI default subscription is authorized.

## Approved configuration

- Two Azure Container Apps Consumption apps, each 0.25 vCPU / 0.5 GiB, min 0 / max 1, HTTPS only. The web endpoint's sole ingress allow rule is the owner's IPv4 `/32`. Login and simulated OTP remain enabled. Handoff 08 routes browser calls through the web BFF to an **internal-only API** in the same managed environment; there is no direct internet API ingress.
- PostgreSQL Flexible Server 16, B1ms, 32 GiB, seven-day local backup, no HA, no storage autogrow. Require secure transport on the server; the client uses `verify-full` with the system CA bundle.
- The owner explicitly approved PostgreSQL's **Allow public access from Azure services** rule (`0.0.0.0` to `0.0.0.0`) plus their own IPv4. This replaces the earlier current-egress-IP approach.
- Generate separate 40-character database administrator, restricted application, and demo login passwords. Store them in Key Vault Standard. The API identity can read only the application and demo passwords; the web identity has no secret access. The app login inherits the non-owner `aclara_api` role for scoped `ops.*` access. Alembic migrations use a separate owner connection; the API refuses owner or RLS-bypass logins.
- Authenticated ACR Basic, anonymous/admin access disabled, separate managed identities with AcrPull. Images are tagged with the complete verified main SHA.
- Terraform Blob state in Standard LRS storage, TLS 1.2+, owner-IP firewall, shared keys and anonymous access disabled, Entra RBAC, versioning and seven-day retention. The local CLI bootstrap creates only the resource group/state store; Terraform manages runtime resources. This bootstrap has no separate Terraform state.
- Resource-group monthly budget at the billing-currency equivalent of USD 50; actual-spend notifications at 60% (USD 30 equivalent) and 100% (USD 50 equivalent), sent to the confirmed owner email. Azure readback showed CAD billing. On 2026-09-26 the Microsoft B1ms retail references were USD 0.017/hour and CAD 0.0236/hour, giving an approximate reference rate of 1.3882 CAD/USD. The configured budget is C$69.41 with alerts at approximately C$41.65/C$69.41. Review the fixed conversion monthly; these are approximate USD equivalents, not live FX-linked thresholds. These are alerts, not a hard spending cap.
- No VPN, NAT Gateway, Private Link, private endpoint, dedicated compute profile, or planned-maintenance feature. Container logs have no paid ingestion destination configured; live log streaming remains available.
- Promoted organizer customer/product/transaction and contract-allowed reference projections in Postgres, `LLM_PROVIDER=mock`. Organizer raw files and the DuckDB lake remain local. No model keys or real-model traffic. Authored ledgers are test fixtures only.

## Known limitations

The PostgreSQL Azure-services firewall rule accepts network connections from Azure IPs in **other customers' subscriptions**, not just these apps. Database authentication, the restricted role, and verified TLS remain mandatory. This is an owner-approved development exception. VNet integration and PostgreSQL private access are future work in [production readiness](production-readiness.md). [Microsoft documents the cross-subscription scope of this rule](https://learn.microsoft.com/en-us/azure/postgresql/security/security-firewall-rules).

The browser's current public IPv4 is the app access boundary; an address change requires an allowlist update. The simulated OTP is not independent MFA. Sessions, disputes, proposals, handoffs and execution records persist in Postgres with forced customer/run/session RLS and a hash-chained audit log. Restart recovery and a tiny local backup-restore rehearsal were tested. Azure PITR, retention and production recovery remain unverified. Card freeze requires fresh OTP, confirmation and readback.

## Live East US 2 price check

Rechecked 2026-09-27 04:00 UTC with `uv run --no-sync python scripts/azure_prices.py` against the [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices). The ignored aggregate result is `artifacts/azure/prices.json`. The script fails if required meters are missing or the modeled total exceeds $40.

| Item | Live USD rate / assumption | Monthly USD |
|---|---|---:|
| PostgreSQL B1ms | $0.017/hour × 730 | 12.41 |
| PostgreSQL storage | $0.115/GB-month × 32 | 3.68 |
| ACR Basic | $0.1666/day × 30 | 5.00 |
| ACA active CPU + memory | Both apps active together 100 hours; no free grant assumed | 5.40 |
| ACA requests | $0.40/million × 100,000; no free grant assumed | 0.04 |
| Key Vault operations | Low-volume allowance | 0.10 |
| State Blob storage and operations | Small-state allowance | 1.00 |
| Logs, transfer, backup overage, usage margin | Allowance | 7.00 |
| **Approval-gate total** | **No ACA free grant; before tax** | **34.63** |

With available ACA free grants, the same low-traffic plan is approximately $24.19–$29.19 including a $2–$7 usage margin. These are usage assumptions, not a maximum bill. Continuous app activity would cost more. Retail rates do not include taxes, subscription credits, discounts, or currency conversion.

The live feed also contains $0.10/hour environment-management meters. This plan does not enable the dedicated profiles, private endpoints or planned maintenance features to which management fees apply. [Container Apps billing](https://learn.microsoft.com/en-us/azure/container-apps/billing) and [pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/) describe those conditions and the shared monthly free grants.

## Deployment procedure

See [infra/README.md](../infra/README.md). Use explicit sandbox subscription selection for every Azure command and provider. Keep subscription/tenant IDs, owner IP, and alert email only in ignored `infra/terraform.tfvars`; never print credentials. Terraform state and plans contain generated secrets and must remain in the protected backend or ignored local files.

Run plan/apply from the approved workstation. GitHub-hosted runners do not match the state firewall; automated deployment remains a later workflow decision. The private GitHub repository and origin remain the only source. A later judge demo requires a separate access decision.

## Handoff 08 BFF integration

A read-only probe from the existing web container returned HTTP 403 from the API's owner-IP rule. The revised route makes the API internal to the existing managed environment and retains the owner's IP rule on the web boundary. No new resource, paid networking feature, extra replica or broader internet access is introduced. API login/OTP and customer RLS remain mandatory. The web server uses `API_BASE_URL`; browser bearer tokens remain in HTTP-only cookies. This follows [Container Apps same-environment communication](https://learn.microsoft.com/en-us/azure/container-apps/connect-apps). Verify actual reachability through the BFF smoke and external denial after deployment. This is environment-scoped ingress, not VNet/private-endpoint isolation for Postgres or Key Vault.
