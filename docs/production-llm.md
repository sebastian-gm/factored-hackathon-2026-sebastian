# Restricted real-model deployment

Handoff 09 authorizes the selected Gemini default, failure-only Grok fallback and a production OpenRouter key in the existing restricted Azure environment. It authorizes at most **five real smoke conversations and US$0.10 total**. It does not authorize judge access, a public endpoint, or a lead-run frozen evaluation.

## Configuration and accounting

- Local/default `LLM_PROVIDER=mock` remains unchanged. Deployment opt-in is `enable_real_llm=true`; the API then uses `AGENT_SYSTEM=P`, `LLM_PROVIDER=openai_compat`, `LLM_MODEL_ROUTE=default` and `LLM_REAL_CALLS_APPROVED=1`.
- The database owns the **US$3 per UTC day** production limit. Each attempted primary call, retry and failure-only alternate call must reserve its full bounded cost before contacting a provider. Unknown cost remains reserved across restarts and request rollbacks. A failed budget check never invokes another provider. See [ADR 0014](adr/0014-durable-model-budget.md).
- `llm_budget_run_id="handoff09-smoke"` adds the persistent **US$0.10 cumulative** smoke cap. It does not reset across processes, releases or midnight. The smoke/browser entry points share an ignored, locked conversation counter; interrupted work consumes its conversation allowance. No automatic POST retries.
- The normal production setting uses an empty run ID after smoke verification; the US$3 daily limit remains. Disable real calls with `enable_real_llm=false`. This does not erase prior spend or unknown reservations.
- Only the API managed identity receives access to `openrouter-api-key` in the existing Key Vault. Web has no model credential. Terraform references the secret URI and never reads/stores this owner-provided value.
- The daily model limit is separate from Azure infrastructure charges. It is not a monthly spending limit or an assurance about the provider invoice. Reconcile unknown charges before any owner-authorized adjustment.

## Release procedure

1. Review/merge prompt v4 and matcher v2, then run local checks, database tests, frontend checks and CI on the release commit. Do not read frozen cases or labels.
2. Recheck live infrastructure and model endpoint prices. The existing infrastructure estimate must remain below the approved US$40 gate. Use conservative standard endpoint rates and request-level price ceilings.
3. Run `.venv/bin/python -m scripts.azure_openrouter_key` after the owner adds `OPENROUTER_API_KEY` to the ignored `.env`. The script uploads through a mode-0600 temporary file, verifies matching readback in memory, then removes the local key entry. It retains the local entry if transfer/readback fails. It never prints a value or provider response.
4. Run `.venv/bin/python -m scripts.azure_migrate_ops` using the approved sandbox and a fresh price gate. The owner migration creates the global spending tables/functions. Runtime remains non-owner.
5. Build/push the exact clean `origin/main` images to private ACR. Set the ignored Terraform inputs `enable_real_llm=true` and `llm_budget_run_id="handoff09-smoke"`. Review the plan in memory: unchanged owner-only web ingress, internal API, resource sizes, Postgres firewall/TLS and existing identities; one secret-scoped role grant. Apply the reviewed plan.
6. Run `.venv/bin/python -m scripts.azure_verify`, then `.venv/bin/python -m scripts.azure_llm_smoke`. The three conversations check ES explanation/dispute/readback, PT top-three ambiguity/handoff and fraud handoff, including staff claim/resolve and measured Ops. The script requires real non-degraded NLU, prompt v4 and matcher v2 metadata. It prints aggregates only.
7. Use `.venv/bin/python -m scripts.serving_browser --target azure` for one additional counted conversation if the remaining allowance permits. The older broad `azure_smoke` refuses to run with real models enabled.
8. Record the exact SHA, results and measured/unknown-reserved cost. Set the run ID to empty only after the smoke passes; apply/read back that flag change. Verify external denial and no drift. Stop and give Sebastian the SHA for the AI lane's final evaluation.

Current verification status is in the [progress log](status/progress-log.md); scripts and a plan alone are not deployment evidence. Preserve the ignored smoke counter and cost records, including failed attempts.

## Failure behavior

Database or budget failure uses deterministic application behavior without a new paid attempt. Model failure follows the reviewed retry/fallback bound and then deterministic behavior. The breaker reserves one UTF-8 byte per possible input token plus a framing allowance and the configured maximum output count. OpenRouter requests enforce [maximum provider prices](https://openrouter.ai/docs/guides/routing/provider-selection#max-price), ZDR and denied data collection. A measured charge above its reservation disables further spending in that scope. Provider errors are not proof of zero billing.

The runtime gives each logical generation a 45-second deadline shared by primary/retry/fallback attempts. NLU and up to two grounded phrasing drafts fit within the BFF's 180-second message timeout; authentication and read endpoints retain their shorter timeout. Request cancellation is not a reason to release a committed reservation.
