# Organizer-backed demo

> **superseded by v4 (2026-10-01)** — Earlier evaluation/release claims on this page are historical; use the [current summary](../README.md) and [official v4 results](evaluation/final-v4-results.md). [Post-v4 fixes](evaluation/post-v4-release-notes.md) are **not reflected in v4 numbers**.

## Source and runtime boundary

The promoted gold dataset is `b86f445cb468332bde984a788ef24f72f7070952b2d9292e0259e7b8f36397c9`, bank clock `2026-06-18T06:00:00Z`. Its six serving tables contain 150,000 customers, 400,000 products, 492,414 transactions, 13,164 FX rows, 1,200 service agents and 150,000 complaint aggregates. The rebuild matched the pinned dataset; no source-version difference was found.

`LEDGER_BACKEND=serving` reads Postgres `bank.*`, loaded only from the pipeline's promoted gold. It never opens raw files or falls back to authored transactions. The runtime is non-owner and cannot bypass RLS. Every customer query sets transaction-local customer context, checks scope, joins owned products and applies the half-open UTC 120-day window. Sorted source IDs produce stable opaque handles. Policy uses FX, status and supplied risk fields privately; public views expose masked contract fields only.

The loader verifies full sorted row hashes inside its atomic transaction and independently reads committed metadata. For Azure's non-superuser owner, FORCE RLS is suspended only inside the table-locking load transaction and restored before commit; rollback restores the prior schema/data. The app role never gains owner access. Customer tables keep forced SELECT RLS; runtime has no writes to source or persona-reference tables.

## Private identities and the three surfaces

Four stable aliases bind to distinct organizer customers in the development hash partition (`sha256(customer_id)` prefix below `b3`), excluding the held-out customer partition. Actual IDs are private Postgres reference data, never API/fixture/Git content.

| Alias | Locale | Trusted role |
|---|---|---|
| `demo.es.mx` | es-MX | Ops, including own Chat and Agent Desk |
| `demo.es.co` | es-CO | Customer |
| `demo.es.ar` | es-AR | Customer |
| `demo.pt.br` | pt-BR | Ops, including own Chat and Agent Desk |

The PT alias is a language preference for a source customer in Mexico; the dataset has no Brazilian customer country. All aliases share the owner-only demo credential from Key Vault (local `.env` for Compose). Simulated OTP is not independent MFA. Server bindings determine role, locale and customer; client input cannot grant a role. Opaque realm prefixes route hashed auth capabilities to the proper customer RLS context and remain stable across restarts. Modifying a prefix cannot authenticate a different capability.

Agent Desk and Ops observe activity in the same authenticated customer/run/session workspace. Claim/resolve mutations require expected versions and idempotency keys plus independent readback. Customer personas receive 403 on staff routes. Ops SAR/unsafe rate are null without gold; source kind is explicitly `organizer_serving`. Reset remains disabled in Azure. This is a solo demo, not a cross-customer staff queue.

## Run and verify

See the README for bootstrap order. Read organizer inputs only through `LOCAL_RAW_DIR`. This checkout uses persistent ignored `lake/`; the standalone pipeline CLI's fallback remains `~/aclara-lake`. Never put rows, IDs, secrets, lake files or per-case traces in CI artifacts.

```sh
python -m aclara.data.cli build --lake lake --no-reports
python -m scripts.load_demo_serving --target local
make up
python -m scripts.local_smoke
python -m scripts.test_postgres
```

Azure load requires a fresh passing `scripts.azure_prices` result and the existing approved sandbox. Use `scripts.load_demo_serving --target azure`, then deploy clean green main and run `scripts.azure_smoke` and `scripts.azure_verify`. No new resource is required.

The smoke compares all four API projections with separate RLS reads, exercises ES/PT normal/ambiguous/human flows, creates two cases and four handoffs, claims/resolves two handoffs, reads measured Ops/traces and verifies audit chains. Authenticated activity persists; it is not deleted as test cleanup. Each run has new session scope. The Azure smoke additionally verifies original-session case recovery on a replacement API replica.

## Evaluation and limits

The held-out entry point now requires this serving dataset and RLS for every base read, adding only the frozen release's declared fictional overlays in isolated memory. Authored-only ledgers remain for independent dev tests and fixtures. No frozen labels were changed and no new full diagnostic was run for this integration. See [adapter semantics](evaluation/adapter-implementation.md), [access log](evaluation/test-access-log.md) and [dev fixes](evaluation/dev-acceptance-fixes.md).

Organizer-backed transport/persistence checks are not evidence of broader language accuracy. The original frozen acceptance failure remains on record. Portuguese/dialect phrases are model-authored and lack fluent human review. Real-model selection, cross-vendor judge, production identity/queues, realistic load and recovery are still pending.
