# Data provenance

| Input | Class | Use and boundary |
|---|---|---|
| Organizer bank CSVs | Organizer synthetic | Read only from LOCAL_RAW_DIR; bronze/silver/gold and row-level diagnostics stay in the ignored local lake |
| Incremental fixture | Team-generated | Authored from the dictionary; fictional records committed under tests/fixtures/incremental |
| Existing demo ledger | Team-generated | Existing fixture API and mock evaluations |
| Matcher recollections | Team-generated from organizer synthetic transactions | Normalized noisy slots with known targets; private datasets/predictions under artifacts; aggregates and numeric model parameters only in Git |
| Source metadata and contracts | Schema/aggregate | Types, normalization, exposure tags, counts and checksums; no source rows |
| Spanish card sheet | Organizer synthetic fields; human writing pending | 40 cards under ignored artifacts; customers excluded from all benchmark splits |
| Portuguese recollections | Future model-generated | Must be labeled and cross-checked by a second model vendor; not yet generated |

The ten source tables used by this lane are customers, products, transactions, exchange rates,
service agents, complaints, call-center interactions, surveys, transcripts and digital events.
Marketing tables and branches are outside the workflow's processing scope. Transcript, survey
comment and complaint text are used only for aggregate degeneracy checks, never NLU or matcher
training. `affected_product_id` is used only to count ownership failures and is excluded from gold.

No organizer records are sent to external LLMs or tracking services by these commands. Published
data-use terms and any later external-model disclosure remain for Sebastian to confirm. This
register does not assert an approval that has not been given. The current lane uses no paid services.
