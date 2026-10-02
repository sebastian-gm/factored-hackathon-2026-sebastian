# Restricted Azure development

Only run after explicit owner approval and a passing live-price gate. All commands run from this repository. Use `Seb Azure Sandbox` explicitly; never change the CLI default. Names omit hyphens only where Azure naming rules require it (ACR and storage).

## Bootstrap and foundation

```sh
uv run --no-sync python scripts/azure_prices.py
uv run --no-sync python scripts/azure_dev.py configure --email '<owner-email>' --owner-ip '<owner-ipv4>'
uv run --no-sync python scripts/azure_dev.py bootstrap
uv run --no-sync python scripts/azure_dev.py init
terraform -chdir=infra fmt -check
terraform -chdir=infra validate
uv run --no-sync python scripts/azure_dev.py plan
uv run --no-sync python scripts/azure_dev.py apply
uv run --no-sync python scripts/azure_dev.py seed
```

`configure` verifies the named sandbox, stores its identifiers in ignored `terraform.tfvars` (0600), and defaults to the workstation's current public IPv4 if none is supplied. The alert email must be the owner's chosen address or their signed-in Azure account mail. Keep the initial budget start date fixed. `bootstrap` registers the required providers, creates the approved resource group and state store, assigns owner Blob access and adds only the owner IP to its firewall. This CLI bootstrap is idempotent and has no Terraform state; runtime state is remote in its `tfstate` container. Do not delete the store while it holds active infrastructure state.

Terraform commands in the helper use a repository-local `az` wrapper that forces `--subscription Seb Azure Sandbox`. This avoids the Azure CLI multi-identity `--tenant` ambiguity without changing the global default account or copying credential files.

The first apply uses `deploy_apps = false`, creating the database, Key Vault secrets, managed identities, registry, environment and budget. Terraform output is captured only in ignored `artifacts/azure` because it includes resource IDs. Inspect failure logs with sensitive values redacted. Never upload plan/state/log files to CI artifacts or Git. The plan contains generated passwords; delete stale local plan files after use.

`seed` reads generated passwords directly from Key Vault into memory, initializes a CONNECT-only database login, revokes public create access, and verifies TLS. Then run `python -m scripts.azure_migrate_ops` for durable ops and `python -m scripts.load_demo_serving --target azure` to load promoted gold and bind private demo personas. These use separate owner credentials and verify non-owner access.

## Build and deploy main

Merge the deployment support PR only after CI is green. Fetch origin, fast-forward local main and use its full SHA as `image_tag`. Build only the two Dockerfiles below. The image context includes authored fixtures, never organizer data. Use a temporary Docker config under ignored `artifacts/azure` for ACR login, then remove its token after pushing.

```sh
git -C /absolute/path/to/bank-agent-lab fetch origin
git -C /absolute/path/to/bank-agent-lab switch main
git -C /absolute/path/to/bank-agent-lab merge --ff-only origin/main
docker build -f Dockerfile.api -t <registry-login-server>/aclara-api:<main-sha> .
docker build -f apps/web/Dockerfile.azure -t <registry-login-server>/aclara-web:<main-sha> apps/web
# Authenticate using az acr login --subscription 'Seb Azure Sandbox' and a private Docker config.
docker push <registry-login-server>/aclara-api:<main-sha>
docker push <registry-login-server>/aclara-web:<main-sha>
```

Set the ignored variables `image_tag` to that full SHA and `deploy_apps = true`; run plan/apply again. Never temporarily remove IP restrictions to troubleshoot. The web app retains the owner-only IP rule; the API has internal-only ingress in the same environment. Use `API_BASE_URL` at runtime; the same production image can be reused without embedding a hostname during its build.

```sh
uv run --no-sync python scripts/azure_dev.py plan
uv run --no-sync python scripts/azure_dev.py apply
uv run --no-sync python -m scripts.azure_smoke
uv run --no-sync python -m scripts.azure_verify
```

The smoke retrieves the demo password from Key Vault into memory and calls the web BFF. It verifies all four private organizer bindings, ES/PT normal/ambiguous/human paths, dispute/handoff readbacks, Agent Desk claim/resolve, measured Ops, audit chains, customer-role denials and original-session case recovery on a replacement API replica. It emits only aggregates. Control readback checks ingress, replicas, TLS, firewall, budget, identities and SHA. The credential-free `azure-access` workflow requires web HTTP 403 and internal API HTTP 404 from a non-allowlisted runner. Run `gh workflow run azure-access.yml --repo sebastian-gm/factored-hackathon-2026-sebastian`; configuration inspection alone is insufficient.

Operator targets are resolved lazily from the explicitly approved Azure sandbox.
Optional private inputs `AZURE_WEB_URL`, `AZURE_API_URL` and `AZURE_POSTGRES_HOST`
override inventory discovery; imports/local checks do not contact Azure. Configure
the workflow's repository variables `AZURE_WEB_URL` (web origin) and `AZURE_API_URL`
(API health URL) privately before dispatch. Concrete hosts are kept out of the tree.

## Operations and limitations

Passwords remain in Key Vault. Retrieve the `demo-password` secret through the authenticated Azure portal when signing in as `demo.es.mx`; do not paste it into Git, chat or deployment logs. The OTP panel is simulated, not independent MFA.

Azure budgets use the subscription billing currency. This subscription reports CAD. The ignored variables set `budget_currency = "CAD"` and `budget_usd_to_billing_rate = 1.3882`, derived from Microsoft retail references checked 2026-09-26. The C$69.41 budget has 60%/100% actual-spend alerts (about C$41.65/C$69.41), approximating the requested US$30/US$50. Review the rate monthly; future FX movement changes the USD equivalents. Budgets notify and do not stop resources. Check billing before increasing usage. Stopping PostgreSQL saves compute temporarily but Azure restarts it after seven days.

The owner approved the broad Azure-services PostgreSQL firewall exception for this dev environment. Other Azure tenants can reach the database network port; authentication and verified TLS remain mandatory. See [production readiness](../docs/production-readiness.md) for VNet/private access and durable-state work. App replicas scale to zero; sessions and operational records survive in Postgres. Session expiry remains enforced. Cold starts can require a retry of a read-only request. Never automatically retry unverified writes.

The local state firewall prevents GitHub-hosted apply runners from accessing state. Keep deployment local until a runner/network decision is approved. Any later GitHub OIDC/environment configuration must use this private repository alone.

## Submission-day preparation (OFF)

See [switches, private plan diff and cost](../docs/submission/infrastructure-switches.md).
Defaults keep `enable_submission_warm=false`, `min_replicas=0` and
`enable_judge_access=false`. Enablement needs Sebastian's submission-day approval.
The judge secrets are external Key Vault references, not Terraform values.

Local plan-only gate (both providers mocked, no Azure calls):

```sh
terraform -chdir=infra fmt -check
terraform -chdir=infra validate
terraform -chdir=infra test -filter=tests/submission.tftest.hcl
```

The ON plan is a preview, not an apply instruction or publication authorization.
Public web still requires login/OTP; API stays internal; model cap is global
USD 3 per UTC day. Recheck prices and the private plan after choosing dates.
