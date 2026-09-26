# Azure restricted development deployment

Approved by Sebastian on 2026-09-26 for `Seb Azure Sandbox`, East US 2, resource group `rg-aclara-dev-eastus2`. Stop before provisioning if the live modeled monthly estimate exceeds USD 40. The earlier under-$30 target remains desirable. No use of the CLI default subscription is authorized.

## Approved configuration

- Two Azure Container Apps Consumption apps, each 0.25 vCPU / 0.5 GiB, min 0 / max 1, HTTPS only. The sole ingress allow rule on each is the owner's public IPv4 `/32`, applied at creation. Application login and simulated OTP remain enabled. Browser requests call the API directly, including health checks, so no extra ingress exception is needed for the web server.
- PostgreSQL Flexible Server 16, B1ms, 32 GiB, seven-day local backup, no HA, no storage autogrow. Require secure transport on the server; the client uses `verify-full` with the system CA bundle.
- The owner explicitly approved PostgreSQL's **Allow public access from Azure services** rule (`0.0.0.0` to `0.0.0.0`) plus their own IPv4. This replaces the earlier current-egress-IP approach.
- Generate separate 40-character database administrator, restricted application, and demo login passwords. Store them in Key Vault Standard. The API identity can read only the application and demo passwords; the web identity has no secret access. The app database role has CONNECT only because current main uses the database only for readiness.
- Authenticated ACR Basic, anonymous/admin access disabled, separate managed identities with AcrPull. Images are tagged with the complete verified main SHA.
- Terraform Blob state in Standard LRS storage, TLS 1.2+, owner-IP firewall, shared keys and anonymous access disabled, Entra RBAC, versioning and seven-day retention. The local CLI bootstrap creates only the resource group/state store; Terraform manages runtime resources. This bootstrap has no separate Terraform state.
- Resource-group monthly budget USD 50; actual-spend notifications at 60% ($30) and 100% ($50), sent to the owner. These are alerts, not a hard spending cap.
- No VPN, NAT Gateway, Private Link, private endpoint, dedicated compute profile, or planned-maintenance feature. Container logs have no paid ingestion destination configured; live log streaming remains available.
- Synthetic authored fixtures only, `LLM_PROVIDER=mock`. Organizer raw data and the DuckDB lake remain local. No model keys or real-model traffic.

## Known limitations

The PostgreSQL Azure-services firewall rule accepts network connections from Azure IPs in **other customers' subscriptions**, not just these apps. Database authentication, the restricted role, and verified TLS remain mandatory. This is an owner-approved development exception. VNet integration and PostgreSQL private access are future work in [production readiness](production-readiness.md). [Microsoft documents the cross-subscription scope of this rule](https://learn.microsoft.com/en-us/azure/postgresql/security/security-firewall-rules).

The browser's current public IPv4 is the app access boundary; an address change requires an allowlist update. The simulated OTP is not independent MFA. Sessions, disputes, proposals and handoffs remain in process memory, and can disappear on scale-to-zero or restart. The cloud deployment does not add durable banking storage. One replica keeps requests on the same process while it is active.

## Live East US 2 price check

Checked 2026-09-26 with `uv run --no-sync python scripts/azure_prices.py` against the [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices). The ignored aggregate result is `artifacts/azure/prices.json`. The script fails if required meters are missing or the modeled total exceeds $40.

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
