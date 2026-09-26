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

`seed` reads generated passwords directly from Key Vault into memory, initializes a CONNECT-only database login, revokes public create access, and verifies TLS. Current main stores cases and sessions in process memory; no bank records are written to PostgreSQL yet.

## Build and deploy main

Merge the deployment support PR only after CI is green. Fetch origin, fast-forward local main and use its full SHA as `image_tag`. Build only the two Dockerfiles below. The image context includes authored fixtures, never organizer data. Use a temporary Docker config under ignored `artifacts/azure` for ACR login, then remove its token after pushing.

```sh
git -C /absolute/path/to/bank-agent-lab fetch origin
git -C /absolute/path/to/bank-agent-lab switch main
git -C /absolute/path/to/bank-agent-lab merge --ff-only origin/main
docker build -f Dockerfile.api -t acraclaradeveastus2.azurecr.io/aclara-api:<main-sha> .
docker build -f apps/web/Dockerfile.azure -t acraclaradeveastus2.azurecr.io/aclara-web:<main-sha> apps/web
# Authenticate using az acr login --subscription 'Seb Azure Sandbox' and a private Docker config.
docker push acraclaradeveastus2.azurecr.io/aclara-api:<main-sha>
docker push acraclaradeveastus2.azurecr.io/aclara-web:<main-sha>
```

Set the ignored variables `image_tag` to that full SHA and `deploy_apps = true`; run plan/apply again. Never temporarily remove IP restrictions to troubleshoot. Both apps receive the owner-only rule on creation, and neither has an unrestricted revision. Use `BROWSER_API_BASE_URL` at runtime; the same production image can be reused without embedding a hostname during its build.

```sh
uv run --no-sync python scripts/azure_dev.py plan
uv run --no-sync python scripts/azure_dev.py apply
uv run --no-sync python -m scripts.azure_smoke
```

The smoke test reads the demo password from Key Vault into memory. It checks HTTPS liveness/readiness, login/OTP, all 32 authored ES/PT scenarios, scoped transactions, dispute/handoff readbacks, unauthenticated denial, CORS, and the web page's runtime API URL. It emits only counts. Separately read back Azure ingress, replica limits, firewall, TLS, budget notifications, identities and image SHA/digests. Verify denial from a non-allowlisted network when available; configuration inspection alone is not a network denial test.

## Operations and limitations

Passwords remain in Key Vault. Retrieve the `demo-password` secret through the authenticated Azure portal when signing in as `demo.es.mx`; do not paste it into Git, chat or deployment logs. The OTP panel is simulated, not independent MFA.

Budget USD 50 with 60% and 100% actual-spend notifications implements the requested $30/$50 alerts. Budgets notify and do not stop resources. Check billing before increasing usage. Stopping PostgreSQL saves compute temporarily but Azure restarts it after seven days.

The owner approved the broad Azure-services PostgreSQL firewall exception for this dev environment. Other Azure tenants can reach the database network port; authentication and verified TLS remain mandatory. See [production readiness](../docs/production-readiness.md) for VNet/private access and durable-state work. App replicas scale to zero, losing current in-memory sessions and cases. Re-login after a cold start.

The local state firewall prevents GitHub-hosted apply runners from accessing state. Keep deployment local until a runner/network decision is approved. Any later GitHub OIDC/environment configuration must use this private repository alone.
