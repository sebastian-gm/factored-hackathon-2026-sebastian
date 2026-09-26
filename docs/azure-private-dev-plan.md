# Azure low-cost development proposal

Status: proposal only. No Azure subscription was queried or changed, and no cloud resources have been created. The owner set a target below USD 30/month and deferred provisioning pending a separate approval. Estimates use public Microsoft list-price references checked on 2026-09-26; they exclude tax, subscription credits or discounts, and currency conversion. Verify the current East US 2 rates and the subscription offer in the Azure Pricing Calculator before approval.

## Scope and constraints

- Subscription: `Seb Azure Sandbox`; region: East US 2 (`eastus2`); resource group: `rg-aclara-dev-eastus2`.
- Personal, low-traffic development and reviewer preparation only. The current endpoint is HTTPS on the public internet but allows only Sebastian's current public IPv4 `/32`; app login remains required.
- No VPN Gateway, NAT Gateway, Private Link, or private endpoint in this plan. Private networking is recorded as future production-readiness work.
- Use synthetic application fixtures only. Keep organizer raw files, credential material, and source rows on the workstation in `LOCAL_RAW_DIR`; do not copy them to Azure. Keep the DuckDB P1 lake local at `~/aclara-lake`.
- `LLM_PROVIDER=mock`; no external model traffic or model keys.
- This is a small, non-HA dev setup. The 1-vCore PostgreSQL tier and scale-to-zero app are for a solo low-traffic demo, not production.

## Proposed shape

```text
Browser at Sebastian's current public IPv4
        │ HTTPS; ACA ingress allowlist /32; Aclara login still required
        ▼
Azure Container Apps (public endpoint)
  ├─ Next.js web app: Consumption, min replicas 0, max 1
  └─ FastAPI app:     Consumption, min replicas 0, max 1
        │ app managed identity (Entra token, TLS)
        ├──────────────► Azure Database for PostgreSQL Flexible Server
        │                 public endpoint; firewall: current ACA egress IPs
        │                 plus Sebastian's current public IPv4 /32 for admin
        ├──────────────► Key Vault Standard public endpoint, RBAC
  └─ image pull ─► authenticated ACR Basic registry (public endpoint), managed identity

Terraform state: small Blob Storage account, public HTTPS endpoint, Entra RBAC,
                 no anonymous blob access, network ACL restricted to owner IP
```

Deploy both app containers to an Azure Container Apps Consumption environment with scale-to-zero, no always-on replicas, and a maximum of one replica per app. Set the current public IPv4 address as the sole inbound allow rule; do not add a catch-all rule. Keep Aclara's login and OTP enabled as a second gate. If the owner's public address changes, update the rule before access is needed again. This owner-only proposal does not configure or authorize the later judge demo; add the agreed judge-access gate in that later layer.

Use an authenticated ACR Basic registry for the images through its public service endpoint. Grant the Container Apps managed identity pull-only access. Grant the app identity access only to the secrets it needs in Key Vault and use Microsoft Entra authentication for PostgreSQL where the application driver supports it; do not store a database password in Git or plain app settings. Require TLS for database connections. Keep the database's public access mode but add firewall rules only for the app's reported outbound addresses and the owner's current address for direct administration. Do not use the PostgreSQL rule that allows all Azure services.

### Egress limitation to accept for development

Azure Container Apps Consumption outbound public IPs can change over time. The app resource reports its current outbound IP list, which can be used to create PostgreSQL firewall `/32` rules, but the list is not a stable app identity. Refresh the firewall rules after app/environment recreation and check them before deployment; a later address change can interrupt database connections. These egress addresses may also be shared platform addresses, so the IP firewall alone cannot prove that traffic came from this one app. PostgreSQL Entra authentication and least-privilege database grants provide the identity check. If strict, stable app-only network access is required, this plan is insufficient without changing the networking constraint; use the private-networking design in `docs/production-readiness.md` in a later phase. [Container Apps networking documents that outbound IPs may change](https://learn.microsoft.com/en-us/azure/container-apps/networking?tabs=workload-profiles-env%2Cazure-cli#ports-and-ip-addresses); [PostgreSQL firewall rules match source public IP addresses](https://learn.microsoft.com/en-us/azure/postgresql/security/security-firewall-rules).

### Remote state and deployment access

Keep Terraform bootstrap state in a separate storage account/container from the runtime state, in the same subscription. Use the public Blob endpoint with TLS, Entra/RBAC data-plane access, anonymous access disabled, and a storage firewall rule for Sebastian's current IP. Run Terraform plan/apply locally from the approved workstation at first. A GitHub-hosted runner will not match a single-owner IP firewall rule for state access; remote CI can validate Terraform files, while automated plan/apply needs a later runner/network-access decision. Keep subscription/tenant IDs and the owner IP in ignored `infra/terraform.tfvars`, never tracked. Every Azure CLI call and Terraform provider configuration must select `Seb Azure Sandbox` explicitly.

## Monthly estimate

Planning case: database stays provisioned all month; both Container Apps use 0.25 vCPU and 0.5 GiB per replica, have zero minimum replicas and one maximum replica, and together stay within the subscription's remaining monthly free grant (roughly 100 hours with both replicas active concurrently). Request count remains below 2 million. The grants are shared across the subscription and might already be consumed by other workloads.

| Meter | Assumption | Monthly estimate |
|---|---:|---:|
| PostgreSQL Flexible Server `B1ms` | 1 vCore/2 GiB, 730 hours | ~$12.41 |
| PostgreSQL storage | 32 GiB minimum planning size, about $0.115/GiB-month | ~$3.68 |
| Azure Container Registry Basic | One registry, 30 days, within included storage | ~$5.00 |
| Container Apps Consumption | Scale to zero, low traffic within available free grant | ~$0.00 expected; variable above grant |
| Key Vault Standard operations | Low-volume secret reads/writes | ~$0.10 allowance |
| Terraform state Blob Storage | Small state and low operation volume | ~$1.00 allowance |
| Logs, network transfer, and usage margin | Low-traffic allowance | ~$2–$7 |
| **Modeled total** | **Low-traffic month, before tax** | **about $24–$29** |

The PostgreSQL and registry line items contribute about $21.10/month before state, secrets, app usage, logs, and transfer. Microsoft's public pricing guidance shows a B1ms plus 32 GiB storage example near $16.09/month and ACR Basic near $5/month; confirm the exact East US 2 rates against the current retail price feed/calculator before approval. [PostgreSQL pricing](https://azure.microsoft.com/en-us/pricing/details/postgresql/flexible-server/) bills provisioned compute and storage; backup storage is included up to the provisioned storage amount. [ACR Basic pricing](https://azure.microsoft.com/en-us/pricing/details/container-registry/) includes 10 GB of storage. [Container Apps Consumption pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/) currently includes 180,000 vCPU-seconds, 360,000 GiB-seconds, and 2 million requests per subscription per month, and charges no app usage while scaled to zero. [Key Vault pricing](https://azure.microsoft.com/en-us/pricing/details/key-vault/) is operation-based for Standard secrets.

This estimate assumes a quiet solo dev workload, unused Container Apps free grant, small logs, and no sustained traffic. It is not a hard spending cap. Azure budgets notify on thresholds but do not stop consumption. Configure a resource-group budget with alerts at $24 and $28, cap app replicas at one, keep minimum replicas at zero, and stop PostgreSQL when not needed. A stopped server still has storage cost and automatically restarts after seven days, so it must be stopped again if continuing to defer use. If the current calculator estimate or measured usage cannot stay below $30/month, stop and bring back a lower-cost option for approval before provisioning.

## Cost and security controls

- Do not create anything until Sebastian gives separate explicit provisioning approval. This document and its estimate are not authorization to spend.
- Do not enable the PostgreSQL “allow public access from any Azure service” rule. Apply only current ACA outbound `/32` rules plus Sebastian's owner `/32`; refresh them as described above.
- Use Container Apps ingress allow rules for the owner's current `/32`, HTTPS only, plus the app's login. Store the address only in ignored local Terraform variables.
- Use managed identity for ACR pull, Key Vault access, and PostgreSQL Entra authentication; assign only `AcrPull`, `Key Vault Secrets User`, and the minimum PostgreSQL roles required.
- Use TLS, no anonymous Blob access, no tracked credentials or identifiers, mock LLM mode, no organizer data in Azure, one max replica per app, and scale-to-zero.
- Configure budget alerts, while recognizing they do not enforce a hard cap. Review actual subscription charges before raising the traffic or resource limits.

## References

- [Microsoft Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)
- [Microsoft Azure pricing guidance: PostgreSQL, ACR, Container Apps, and Azure Monitor](https://github.com/microsoft/azure-skills/blob/main/skills/azure-app-onboard/prepare/references/pricing-guide-services.md)
- [Container Apps IP ingress restrictions](https://learn.microsoft.com/en-us/azure/container-apps/ip-restrictions)
- [Container Apps networking and outbound IP behavior](https://learn.microsoft.com/en-us/azure/container-apps/networking?tabs=workload-profiles-env%2Cazure-cli#ports-and-ip-addresses)
- [Container Apps resource API outbound IP field](https://learn.microsoft.com/en-us/rest/api/resource-manager/containerapps/container-apps/list-by-subscription?view=rest-resource-manager-containerapps-2026-01-01)
- [PostgreSQL firewall rules](https://learn.microsoft.com/en-us/azure/postgresql/security/security-firewall-rules)
- [PostgreSQL managed identity authentication](https://learn.microsoft.com/en-us/azure/postgresql/security/security-connect-with-managed-identity)
- [Container Apps managed identities](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity)
- [Pull private ACR images with managed identity](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull)
- [Cost Management budgets and alerts](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets)
- [Stop PostgreSQL Flexible Server compute](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/how-to-stop-server)
