# Temporal quality: policy and release plan

**Post-v4 change; official v4 results unchanged. No held-out rerun or new safety
rate claim. Sebastian approved the final smoke budget on October 2 within the
new $15 cumulative LLM ceiling (including reserves). Azure remains on v0.6.0.
Local rebuild/preflight is verified below; Azure commands are prepared only.**

## Local verification — October 2

- #131 (DQ-01/migration), #132 (budget) and refreshed #128 (data) merged on
  green remote gates. Combined authored `make checks`: **1330 passed / 32 DB
  skips**, B1 **32/32**; disposable Postgres **69 passed**.
- Ran the step-1 build command below with `--no-reports`, then
  `register_temporal_exports` / `validate_temporal_exports` on promoted local
  gold. Current fingerprint, no promotion-blocking checks, **zero source
  mismatches** for customers/products/transactions. Outputs remain ignored.
- **492,414** window rows retained; **60,920** flagged and **431,494** unflagged.
  Primary reasons: before product open **10,241**, product updated after clock
  **21,852**, customer updated after clock **28,827**, after bank clock **0**.
  **4** business-date mismatches remain warnings. Matches #128's aggregates.
- No Azure load/restart, model calls, key-limit change or held-out rerun.
  Private receipt: `artifacts/azure/temporal-organizer-preflight.json` (0600).

## Contract

Serving retains transactions. `temporal_quality_reason TEXT NULL`: NULL means
passed temporal checks; a flag or unavailable check blocks automated disputes.

| Flag | Open question in the localized handoff |
|---|---|
| `before_product_open` | Verify the product opening date against the movement date. |
| `after_bank_clock` | Verify why a movement date is after the data cutoff. |
| `product_updated_after_clock` | Verify the product status at the cutoff. |
| `customer_updated_after_clock` | Verify the customer status at the cutoff. |

DQ-01/policy v1.4.0 permits explanations, enforces ownership/120-day scope, and
preserves urgent fraud/security/restricted-product routing. Existing independent
case-status reads remain available. Confirmation re-evaluates eligibility: a new
flag becomes a verified handoff, not a write. The bounded anomaly detail uses the
existing `policy_evaluations` contract and survives refresh/readback/retries.
Unknown flag values also fail closed. NLU thresholds/model authority are unchanged.

An older schema gets a NULL read placeholder plus an explicit unavailable-check
bit. `/readyz` remains 200 with an automation-disabled warning. Column migration
runs only inside the loader's locked COPY/checksum transaction; failure rolls
back DDL and data together. An old row's new NULL is never committed as passed
without the fresh gold reload. Unexpected schemas/types still fail.

## Coordinated final release — approval required before Azure reload

1. Merge revised #128 and the lead policy/migration companion on green CI. Ship
   the new image and serving reload together. Preserve prior gold/marker/image
   receipts for rollback. Rebuild locally from configured `LOCAL_RAW_DIR`:

   ```bash
   ACLARA_TEMPORAL_LAKE="$PWD/artifacts/temporal-release-lake"
   LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 \
   .venv/bin/python -m aclara.data.cli build \
     --lake "$ACLARA_TEMPORAL_LAKE" --no-reports
   ```

   Require promotion, contracts/DQ and #128's source-equivalence preflight;
   stale gold/fingerprints are insufficient. Commit no rows or DSNs.
2. **Budget OK received; paired merges complete.** Prepare/push final SHA
   images first. In the coordinated maintenance window, deploy the new API
   before loading: an old missing-column schema must disable automated disputes
   and show the readiness warning. Verify that read-only state; keep paid smoke
   until both image and data are ready. An old API cannot enforce DQ-01 merely
   because the column has been added. Refresh prices and atomically load:

   ```bash
   .venv/bin/python -m scripts.azure_prices
   LAKE_DIR="$ACLARA_TEMPORAL_LAKE" \
   .venv/bin/python -m scripts.load_demo_serving --target azure
   ```

   Require checksum/count readback, restored FORCE RLS and non-owner scope tests.
   Verify each existing advertised demo/judge dispute story has an unflagged
   eligible target in its own scope. Stop if coverage is absent; do not silently
   rebind profiles or invent facts.
3. Securely populate `SERVING_VERIFY_DSN` using the existing private runtime
   connection helper (non-owner role; never print/pass the DSN on the CLI):

   ```bash
   .venv/bin/python -m scripts.verify_temporal_serving \
     --identity-file "$ACLARA_TEMPORAL_LAKE/_meta/current.json"
   ```

   Require both boolean checks true: correctly typed column and matching fresh
   promotion fingerprint. Missing columns/stale identity block release.
4. Restart the new image into the new serving identity, keeping all resource
   shape/access settings unchanged. Run `azure_smoke`, `azure_verify`, the newly approved capped
   `azure_llm_smoke`, owner-IP browser, `azure-access` and Jev-OFF release receipt.
   Readiness must have no temporal warning. Record SHA, spend, tag and Release.

A changed serving identity requires the API restart; coordinate that maintenance
window. CPU, replicas, ingress and model routes are unchanged. A failed atomic
load preserves the prior state. After commit, a failed gate requires the retained
compatible gold/schema/image rollback under owner review; operational cases are
not a ledger rollback. Do not leave a migrated column on old unchecked data or
reverse schema with an unreviewed DROP/TRUNCATE. Require fingerprint/RLS/access
readback before claiming recovery. Organizer rebuild/reload, image release and
paid smoke remain unverified until executed. Warm replicas, public/judge access
and the proposed $1/UTC-day judging cap still require submission-day approval.
