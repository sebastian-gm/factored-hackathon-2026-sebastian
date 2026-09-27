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
# Data provenance and model-provider handling

Reviewed 2026-09-27. This is a synthetic banking demonstration. The organizer's published data-use terms still need owner confirmation before any organizer-derived values are sent to a model. AI-lane paid development comparisons use only team-written synthetic fixture text; persistent deployment remains `LLM_PROVIDER=mock`.

| Input | Classification | Model exposure |
|---|---|---|
| Organizer ledger and dimensions | Organizer-provided synthetic data | Only contract-allowed, masked transaction facts after owner confirmation; never raw rows, direct identifiers, fraud labels, or scores |
| Fixture ledger, scenario and NLU utterances | Team-generated synthetic | Allowed for local mock checks; external calls still require approval |
| Preferred-language and demo-identity overlays | Team-generated synthetic | Language preference only; credentials and identity mapping never sent |
| LLM paraphrases | Model-generated | Record model and prompt versions; no model reasoning stored |
| Human-reviewed language labels | Team-generated human | Review status tracked with the evaluation set |

The intended provider payload is the customer's redacted message or an approved `ResponsePlan` with opaque handles and masked, contract-allowed facts. The AI lane strips patterns for card/document numbers, email addresses, and phone numbers before model calls. It wraps untrusted messages and records as escaped data blocks. Execution records contain provider, model, route, prompt hash/version, token counts, latency, cost, stop reason, and validation status. They omit prompts, completions, and model thinking.

| Provider path | Training and retention terms relevant to selection | Demo status |
|---|---|---|
| OpenRouter gateway | [OpenRouter says](https://openrouter.ai/support/) it logs request metadata but does not log prompts/completions by default. It forwards requests to a model provider. This adapter requests [`data_collection: deny` and `zdr: true`](https://openrouter.ai/docs/guides/get-started/sovereign-ai), so routing should fail if no compliant endpoint is available. Actual endpoint and account privacy settings must be checked before the public demo. | Selected future transport for Gemini default, Grok failure-only fallback and Sonnet judge; persistent production remains mock |
| Gemini API direct, free tier | [Google's terms](https://ai.google.dev/gemini-api/terms) permit submitted content and responses to improve Google products on unpaid service, with regional exceptions. [Paid service](https://ai.google.dev/gemini-api/docs/pricing) says content is not used to improve products. | Synthetic fixture development candidate only; free tier is not an accepted public default yet |
| DeepSeek direct | [DeepSeek's privacy policy](https://platform.deepseek.com/downloads/DeepSeek%20Privacy%20Policy.pdf) says information may be stored on servers in mainland China. Direct API training/retention specifics need further review. OpenRouter routing to a non-collecting endpoint is a separate path. | Candidate; direct path held for terms review |
| xAI direct | [xAI model documentation](https://docs.x.ai/developers/models/grok-4.3) covers API capability and pricing; API training, retention, and processing terms have not yet been verified here. OpenRouter's per-request privacy controls are used for its routed path. | Candidate; direct path held for terms review |
| Qwen via Alibaba Model Studio | [Alibaba says](https://www.alibabacloud.com/help/en/model-studio/privacy-notice) it does not use Model Studio customer data for model training and that it stores data generated from model/application calls. Processing region and retention need account-specific review. | Candidate; direct path held for terms review |
| Anthropic direct | [Anthropic says](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention) retained API data is not used for training without express permission. Standard retention and ZDR eligibility vary by feature/model. | Final test candidate only |
| TypeSafe Jev direct API | The [TypeSafe privacy policy](https://typesafe.ai/legal/privacy-policy) says submitted prompts and other input are **not used to train or fine-tune models** and are not disclosed beyond service providers. It also says input is collected, personal data may be retained as reasonably necessary, and services are hosted in the US. The [data-processing addendum](https://typesafe.ai/legal/data-processing) describes TypeSafe as processor for customer personal data and permits listed subprocessors. The [TypeSafe legal index](https://docs.typesafe.ai/legal) offers zero-data-retention only to enterprise customers; this worktree has **not** verified or claimed ZDR for its key. Jev's [model page](https://docs.typesafe.ai/models) lists English as its strongest language and $0.042/M input tokens, with output free. | Prior paid comparison used only synthetic dev and judge-smoke text. Sebastian subsequently selected Jev for supporting risk cues and subjective second-judge scoring. Runtime NLU sends only the redacted customer message, with no slots/phrasing or direct identifiers intentionally included; judge input has redacted message/reply/summary. Lead must verify account terms and payload scope before activating these routes. Persistent production remains mock. |

Sebastian selected Gemini 3 Flash for NLU/phrasing, Grok 4.20 as its failure-only fallback, Jev for parallel risk-cue second opinion, and Sonnet plus Jev for subjective judging. Production still uses mock until the lead's controlled real-key deployment. The AI lane has made separately approved, synthetic-only real-model development and smoke calls; their per-call usage/cost, model IDs and prompts are reported in the linked evaluation docs. The frozen final system run remains on hold pending Sebastian's explicit start signal and the [preflight gates](evaluation/final-preflight.md).
