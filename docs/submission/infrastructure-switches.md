# Submission-day switches — prepared, OFF

Sebastian must approve the exact activation date, account, plan and spend before
any enablement. Testing stays scale-to-zero and owner-IP-only. No setting was
applied, no judge secret created and no Azure resource changed in this preparation.

## Variables and planned effect

| Variable | Default | Effect only after approval |
| --- | --- | --- |
| `enable_submission_warm` | `false` | Authorizes setting the separate replica variable to 1 |
| `min_replicas` | `0` | Both existing API/web apps; allowed values 0/1 only |
| `enable_judge_access` | `false` | Public HTTPS web without the owner-IP rule, with login/OTP retained |

Warm replicas do not open ingress. Judge ingress does not enable warm replicas.
The API remains internal HTTPS in every combination; max replicas stays 1 and
resources stay 0.25 vCPU / 0.5 GiB per app. No network, DB, registry, logs or
resource group is added by these options. No API or model key goes to the web.
Judge mode rejects smoke-run budgeting and retains the existing global durable
`production` USD 3/day model cap, shared by owner/judge sessions, retries,
fallbacks and Jev risk calls. Terraform keeps `LLM_DAILY_BUDGET_USD=3` as well.
Azure billing alerts notify; the model's reserve-before-call breaker stops calls.

## Key Vault account definition

After approval only, store two separate secrets in `kv-aclara-dev-eastus2`:

- `judge-password`: independently generated random password (at least 32
  characters), distinct from the owner demo password.
- `judge-persona`: for the single-login picker, a JSON object with exactly
  `username` and `profiles`. `profiles` maps `mx-es`, `co-es`, `ar-es`, `pt` to
  existing reviewed serving persona usernames, with respective locales `es-MX`,
  `es-CO`, `es-AR`, `pt-BR` and **four distinct customers**. The username uses the
  `judge.` prefix. Values are supplied privately, not through Terraform/Git.
  The earlier `username` / `source_username` single-alias format remains
  compatible, without picker endpoints.

The app inherits the selected trusted source's customer, locale, role and already-gated
guided-story hints; the secret cannot
supply a role, customer ID, nonexistent source or collision with an existing login.
Sebastian must choose/review all four sources on submission day. Selecting an Ops
source enables its existing workspace-scoped Desk/Ops access; a customer source
retains customer-only permissions. No implicit new privilege is created. Only
one judge account is configured. Password/OTP yields a picker-only grant;
server-side profile selection rotates the capability and independently verifies
activation. No unrestricted registration or arbitrary-customer lookup exists.
See [judge API](../api/judge-profile-entry.md) and
[ADR-0016](../adr/0016-judge-profile-sessions.md) for replay, multi-tab, reset and
restart boundaries. Each selection starts a fresh workspace; reset is forbidden
for judge sessions. Logout revokes all of that login's selected capabilities.

Terraform references the two versionless secret URIs and grants API managed
identity access at **only those secret scopes**. No secret data source, literal
value, password variable or generated judge credential enters plan/state.
Authoritative account/credential configuration remains in Key Vault; derived
username/role and authenticated session metadata are persisted by the existing
Postgres session mechanism. Passwords/secret JSON are not persisted there.

Login checks the judge password only for its alias and the owner password only
for existing owner personas. Both use the existing OTP/session path. Anonymous
banking/Desk/Ops calls still fail. The alias's username realm isolates its own
run and owner operational receipts, with serving customer RLS unchanged. Bad or
missing enabled configuration fails startup; OFF ignores all judge material.
The runtime also rejects a smoke budget or a real-provider daily setting other
than 3. No confirmation, write, policy or OTP semantics were changed.

## Plan-only verification

Local `terraform fmt -check`, `terraform validate` and five mocked **plan-only**
Terraform tests cover OFF, warm, judge, forbidden warm-without-switch and
judge-with-smoke. Both providers are mocked; no test applies real infrastructure.
[Terraform mocking documentation](https://developer.hashicorp.com/terraform/language/tests/mocking).

Read-only plans against the existing sandbox used the subscription-forcing CLI
wrapper plus `-refresh=false -lock=false`; no apply, provider registration,
backend initialization, lease or tfvars enablement. Private plans/JSON are 0600
under ignored `artifacts/submission-prep/`. Summarized diff:

| Plan | Create | Update | Delete |
| --- | --- | --- | --- |
| Both options OFF | 0 | 0 | 0 |
| Warm 1 + judge ON (normal daily budget) | 2 secret-scoped RBAC assignments | API and web apps | 0 |

The ON plan opens only web HTTPS, keeps API internal and sets min=1/max=1. It
references, but does not create, the future judge secrets. Image tag is unchanged.
The OFF plan is a no-op. This plan is a preparation artifact, not approval or a
fresh refresh/drift audit; replan normally on submission day against the approved
release and account, with private outputs and live rates checked again.

## Estimated cost and approval window

East US 2 USD retail API checked **2026-09-30 04:17 UTC**: active CPU
$0.000024/vCPU-second, idle CPU $0.000003/vCPU-second, memory
$0.000003/GiB-second. Two current replicas together cost **$0.3888/day idle to
$1.296/day continuously active**, before free grants, requests, logs, tax and
models. For Oct 3–16 inclusive (14 days), app compute is **$5.4432–$18.144**.
Warm idle/active billing depends on real activity; these are total app compute,
not an addition to already counted active usage. Sources:
[retail API](https://prices.azure.com/api/retail/prices),
[Container Apps billing](https://learn.microsoft.com/en-us/azure/container-apps/billing).

Using the prior verified fixed DB/storage/registry estimate **$21.09/month** and
an explicit **$8.10** state/KV/log/egress margin plus **$0.10** request allowance,
a 14-day window gives about **$34.73–$47.43/month** before free grants/tax/models
and any app use outside that window. The upper scenario exceeds the $40 approval
gate; do not enable based on a low-idle assumption alone. A fully warm 730-hour
month is $11.826–$39.42 app compute, so extended availability needs another cost
review. Fixed services/margin are historical assumptions, not newly repriced here.

Judge mode adds no dedicated infrastructure SKU. Model spending is bounded at
**$3 per UTC day**, not $3 for the entire availability window: 14 days could add
**$42** of model spend. This is separate from the final evaluation's $3 lifetime
scope. Public traffic also consumes request/log/egress allowances, which are not
hard cloud caps. Sebastian must approve the combined monthly/model exposure,
start/end dates and daily model allowance before enabling public web ingress.

## Submission-day approval and verification

1. Review a green main release and four approved source personas; create secrets
   privately in the named sandbox using explicit subscription selection.
2. Inspect global production budget disabled status/cap and disable any smoke
   run override. Choose public-judge/warm toggles and exact end date privately.
3. Recheck live prices and full monthly estimate; obtain Sebastian's approval
   if above $40, including the separate $3/day model exposure.
4. Generate/review a fresh private plan. Apply only that approved plan. Verify
   API remains internal, login/OTP/role/RLS still enforced, judge credentials
   cannot sign into owner accounts, and no unauthenticated banking access.
5. Rehearse from outside the owner allowlist with an authorized test spend cap;
   prepare a judge-mode access check rather than claiming the current owner-only
   `azure-access` workflow's expected 403 is valid for public web ingress.
6. On the approved end date, disable judge/warm switches and return min=0.
   Rotate/revoke the judge credential and verify public access is blocked again.

Public access and this live rehearsal are **not verified** by preparation.
