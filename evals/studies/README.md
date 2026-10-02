# Offline language studies

Development comparisons, fixture builders, reports, offline judges and the human
scoring-page tools live in `evals/studies/llm/`. Run them from a development
checkout with the dev dependencies installed, for example:

```sh
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 uv run --no-sync python -m evals.studies.llm.dev_post_v4 after-mock
uv run --no-sync python -m evals.studies.llm.human_review --help
uv run --no-sync python -m evals.studies.llm.dev_kind_replay --help
```

No move grants permission to run paid studies or open held-out inputs. Existing
approval, durable-budget, data-access and private-output checks remain in place.
Historical real results are unchanged.

The installed runtime package keeps only the structured client, configuration,
providers, prompts, types and optional TypeSafe adapter/questions. The API image
copies `src/`, not this tree; `.dockerignore` also excludes these studies from the
build context. No runtime code imports this package.

All fifteen data/manifest files and both source-hashed robustness builders were
moved byte-for-byte. The three-level directory depth preserves their repository
root calculation. The offline package installs one legacy module alias for the
round-two builder's frozen import; it is absent from a fresh API process. This
preserves the original builder, dataset and materialized-scenario hashes without
rewriting a freeze or weakening its checks. The path printed in the historical
explain/offer checksum file remains its original source location; its loader
validates the unchanged hash against the relocated dataset.

The model comparison's source-pin guard still hashes every relocated Python
module as well as serving code. Historical checkpoints are not rewritten;
resuming any paid comparison still requires its original approval and pins.
