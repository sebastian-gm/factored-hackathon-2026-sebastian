# Prompt status

The serving defaults are explicit paths in the
[NLU adapter](../src/aclara/agent/nlu/structured.py) and
[phrasing builder](../src/aclara/agent/nlg/builder.py). Filenames are not an
automatic version selector; the version and SHA-256 come from each prompt file.

| Prompt | Status | Use |
|---|---|---|
| [nlu/v5.md](nlu/v5.md), version **v5.1** | **Live** | Intent and slot interpretation; code retains authority. |
| [phrase/v2.md](phrase/v2.md), version **v2.1** | **Live** | Approved-text phrasing with localized facts, language and grounding guards. |
| [judge/v1.md](judge/v1.md) | **Offline evaluation only** | Subjective rubric scores; never grants authority or scores objective outcomes. |
| nlu/v1.md, v2.md, v3.md, v4.md | **Historical, not serving defaults** | Retained at their original paths for pinned studies and prompt regressions. |
| [phrase/v1.md](phrase/v1.md) | **Historical, not serving default** | Retained for earlier study evidence. |
| [Archived nlu/v5_2.md](../evals/studies/prompts/nlu/v5_2.md), version **v5.2** | **Unadopted development candidate** | Outside the API image; no comparable real measurement or adoption gate was completed. |

Archival preserves prompt bytes and hashes. Historical prompts require explicit
selection by an offline study; retaining them is not permission to spend money.
See the [language model card](../docs/ml/model-card.md),
[v5.2 study status](../docs/ml/nlu-robustness-round2.md#lean-v52-status-prepared-not-measured-or-adopted)
and [offline tools](../evals/studies/README.md).
