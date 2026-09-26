# Data provenance and model-provider handling

Reviewed 2026-09-26. This is a synthetic banking demonstration. The organizer's published data-use terms still need owner confirmation before any organizer-derived values are sent to a model. The current AI-lane checks use team-written fixture text and `LLM_PROVIDER=mock`.

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
| OpenRouter gateway | [OpenRouter says](https://openrouter.ai/support/) it logs request metadata but does not log prompts/completions by default. It forwards requests to a model provider. This adapter requests [`data_collection: deny` and `zdr: true`](https://openrouter.ai/docs/guides/get-started/sovereign-ai), so routing should fail if no compliant endpoint is available. Actual endpoint and account privacy settings must be checked before the public demo. | Candidate, not selected |
| Gemini API direct, free tier | [Google's terms](https://ai.google.dev/gemini-api/terms) permit submitted content and responses to improve Google products on unpaid service, with regional exceptions. [Paid service](https://ai.google.dev/gemini-api/docs/pricing) says content is not used to improve products. | Synthetic fixture development candidate only; free tier is not an accepted public default yet |
| DeepSeek direct | [DeepSeek's privacy policy](https://platform.deepseek.com/downloads/DeepSeek%20Privacy%20Policy.pdf) says information may be stored on servers in mainland China. Direct API training/retention specifics need further review. OpenRouter routing to a non-collecting endpoint is a separate path. | Candidate; direct path held for terms review |
| xAI direct | [xAI model documentation](https://docs.x.ai/developers/models/grok-4.3) covers API capability and pricing; API training, retention, and processing terms have not yet been verified here. OpenRouter's per-request privacy controls are used for its routed path. | Candidate; direct path held for terms review |
| Qwen via Alibaba Model Studio | [Alibaba says](https://www.alibabacloud.com/help/en/model-studio/privacy-notice) it does not use Model Studio customer data for model training and that it stores data generated from model/application calls. Processing region and retention need account-specific review. | Candidate; direct path held for terms review |
| Anthropic direct | [Anthropic says](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention) retained API data is not used for training without express permission. Standard retention and ZDR eligibility vary by feature/model. | Final test candidate only |

The public default is **undecided** until the same-case model table, provider terms, owner approval, and deployment checks are complete. No real provider call has been made by the AI lane as of this entry.
