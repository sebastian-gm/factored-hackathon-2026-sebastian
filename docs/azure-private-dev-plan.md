# Azure private development plan

Status: proposal only. No Azure subscription was queried or changed, and no cloud resources have been created. Prices below are public list-price estimates checked on 2026-09-26, in USD, before tax, credits, exchange conversion, or subscription-specific discounts. Recheck the Azure Pricing Calculator against `Seb Azure Sandbox` before provisioning.

## Target and assumptions

- Subscription: `Seb Azure Sandbox`; region: East US 2 (`eastus2`); resource group: `rg-aclara-dev-eastus2`.
- Use names of the form `<type>-aclara-dev-eastus2` where Azure permits. Storage accounts cannot contain hyphens, so the remote-state account needs a short globally unique alphanumeric name instead.
- Solo developer, one VPN client, development traffic, synthetic in-app fixtures only. The organizer raw-data pipeline stays local under the shared `LAKE_DIR`; do not copy raw files, credentials, or organizer records to Azure.
- One Linux host runs the existing Docker Compose app and Postgres for development. The P1 DuckDB pipeline is not part of this host. This is not a production or high-availability design.
- Use mock LLM mode. Model usage, monitoring workspaces, backups, support plans, and taxes are outside this estimate.
- Always-on month means 730 provisioned hours. A smaller short-lived deployment is costed separately below.

## Recommended Azure-native shape

```text
Developer workstation
        │ Entra-authenticated P2S VPN
        ▼
VpnGw1AZ ── private VNet ── Linux B2ms VM
                                 ├─ Compose web (reachable only over VPN)
                                 ├─ API (Compose network only)
                                 └─ Postgres (Compose network only)
        │
        ├─ NAT Gateway: VM outbound package/image access; no unsolicited inbound
        └─ Private Endpoint: Terraform state Blob, public network access disabled
```

The VM has no public IP. The app has no public listener, DNS name, load balancer, or ingress gateway. Permit the web port only from the VPN client address pool; keep API and Postgres off the host network. Use Azure Run Command for VM administration when practical. The VPN gateway itself has a public IP because clients initiate P2S connections; that is a controlled VPN entry point, not public application access.

New virtual networks created with ARM API versions released after 2026-03-31 default to private subnets without automatic outbound access, so the VM needs an explicit outbound method. A NAT Gateway provides that path and rejects unsolicited inbound connections. The VM uses the NAT Gateway's static public IP only for outbound traffic.

Use Entra ID authentication for P2S, a non-overlapping VPN address pool, an NSG with the minimum required ports, and a managed identity for Azure resource access. Restrict the Storage account to the private endpoint, disable anonymous blob access and public network access, use Azure AD/RBAC data-plane access, and enable state blob versioning/deletion recovery. Keep `tfstate` in a separate bootstrap state from the runtime stack so destroying the dev environment does not destroy its own state.

Initially run Terraform from the developer workstation while connected to P2S. A GitHub-hosted runner cannot reach a private Blob endpoint directly. When deployment automation is approved, GitHub OIDC can call the Azure control plane to trigger VM Run Command; if CI must run Terraform against the private state endpoint, add an approved self-hosted runner inside the VNet and include its cost. Do not put subscription or tenant IDs in tracked files. Local Terraform values belong in gitignored `infra/terraform.tfvars`; use the explicitly selected `Seb Azure Sandbox` subscription in every Azure CLI and Terraform operation.

## Estimate: Azure-native P2S

One VM, one 64-GiB Standard SSD, one `VpnGw1AZ` gateway, one NAT Gateway, two Standard static public IPv4 addresses (VPN and NAT), one Storage private endpoint, one private DNS zone, and a small remote-state storage allowance.

| Meter | Assumption | Monthly estimate |
|---|---:|---:|
| Linux `Standard_B2ms` VM | $0.0832/hour × 730 | $60.74 |
| Standard SSD `E6 LRS` (64 GiB) | 1 provisioned disk | $4.80 |
| VPN Gateway `VpnGw1AZ` | $0.21/hour × 730 | $153.30 |
| Standard static IPv4 addresses | 2 × $0.005/hour × 730 | $7.30 |
| Standard NAT Gateway | $0.045/hour × 730 | $32.85 |
| NAT data processing | 25 GB × $0.045/GB | $1.13 |
| Blob private endpoint | $0.01/hour × 730, plus about 1 GB processing | $7.31 |
| Azure Private DNS zone | 1 zone | $0.50 |
| Terraform state storage and operations | 5 GB state allowance | $1.00 |
| **Estimated total** | **24/7 for a 730-hour month** | **about $269/month; budget at $270** |

The NAT data allowance is a planning assumption, not a traffic measurement. NAT data processing and Internet egress are separate meters. The first 100 GB/month of Internet egress is currently free; traffic beyond that is billed separately. One P2S client is within the included tunnel count for `VpnGw1AZ`.

The `VpnGw1AZ` rate is used because non-AZ `VpnGw1` gateways are no longer available for new deployments. The gateway and NAT hourly fees continue while those resources exist, even when idle. If the environment is needed for one 168-hour week and the VM, gateway, NAT, IPs, and endpoint are then destroyed, the same usage assumptions project to roughly **$64 for that week**, with the state storage left in place at under $1/month. Resource teardown would remove the dev database disk and its contents.

## Lower-cost access alternative

If Sebastian accepts an external VPN control plane, a single-user Tailscale Personal tailnet can replace Azure VPN Gateway and its public IP. The application VM still has no public IP, and the NAT Gateway remains for explicit outbound access. The Azure estimate falls to roughly **$112/month** at 730 hours. Tailscale currently lists Personal at $0 for personal, non-commercial use (up to six users); its control plane is an additional vendor dependency. Do not use this option without Sebastian's approval.

## Cost controls and exclusions

- Before provisioning, set an owner-approved monthly budget and alerts. Azure budget alerts notify; they do not stop resources. Use a scheduled/manual Terraform destroy for the hourly VPN and NAT resources when the environment is not needed.
- The $270 planning number uses public USD list rates, not the subscription's actual offer. It excludes taxes, possible egress above 100 GB, monitoring/log ingestion, backup/snapshots, additional VPN clients, support, and any size increase. Confirm the exact offer in the calculator before approval.
- Azure VPN is the recommended baseline when keeping access within Microsoft Entra/Azure is more important than monthly cost. The Tailscale option is cheaper but trades that for an external control plane.
- Do not provision until Sebastian explicitly approves a concrete option and a monthly cap. This estimate is not approval to spend or create resources.

## Pricing and technical references

Rates were read from Microsoft's public Retail Prices API on 2026-09-26. The API returns USD list prices and supports filtering by region and SKU.

- [Retail Prices API documentation](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)
- [East US 2 B2ms VM rate query](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=armRegionName%20eq%20%27eastus2%27%20and%20armSkuName%20eq%20%27Standard_B2ms%27%20and%20priceType%20eq%20%27Consumption%27)
- [East US 2 VPN Gateway rate query](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=serviceName%20eq%20%27VPN%20Gateway%27%20and%20armRegionName%20eq%20%27eastus2%27)
- [64-GiB Standard SSD rate query](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=armRegionName%20eq%20%27eastus2%27%20and%20meterName%20eq%20%27E6%20LRS%20Disk%27%20and%20priceType%20eq%20%27Consumption%27)
- [East US 2 Standard IPv4 rate query](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=armRegionName%20eq%20%27eastus2%27%20and%20meterName%20eq%20%27Standard%20IPv4%20Static%20Public%20IP%27)
- [Standard Private Endpoint rate query](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=productName%20eq%20%27Virtual%20Network%20Private%20Link%27%20and%20armRegionName%20eq%20%27Global%27%20and%20meterName%20eq%20%27Standard%20Private%20Endpoint%27)
- [Private DNS zone rate query](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=meterName%20eq%20%27Private%20Zone%27)
- [NAT Gateway rate query](https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=contains(productName%2C%20%27NAT%27))
- [VPN Gateway SKU consolidation](https://learn.microsoft.com/en-us/azure/vpn-gateway/gateway-sku-consolidation) and [P2S VPN overview](https://learn.microsoft.com/en-us/azure/vpn-gateway/point-to-site-about)
- [NAT Gateway pricing and billing](https://azure.microsoft.com/en-us/pricing/details/azure-nat-gateway/)
- [Private subnet outbound behavior](https://learn.microsoft.com/en-us/azure/virtual-network/ip-services/default-outbound-access), [Private Link pricing](https://azure.microsoft.com/en-us/pricing/details/private-link/), and [Azure bandwidth pricing](https://azure.microsoft.com/en-us/pricing/details/bandwidth/)
- [Tailscale Personal plan](https://tailscale.com/pricing)
