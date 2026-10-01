# Live language integrity and transaction-kind correction

Zero-spend AI-lane diagnosis, 2026-09-30 PDT. Only saved **retired v3 and authored robustness dev** outputs were replayed. No held-out v4 rows, model calls, serving reads, thresholds, shared interfaces or production configuration changed. The lead must review/merge and deploy; local evidence does not establish a live Azure fix.

## NLG: corrupted words and untranslated enums

The reported authored reproduction returned `safe=True` before this change:

```python
verify_draft("La operaci3n figura como approved.", ["status"],
             (AllowedFact("status", "Approved", "scoped_transaction_read"),))
```

It now returns unsafe with `text_corruption` and `unlocalized_enum`. The context-aware [grounding verifier](../../src/aclara/agent/nlg/grounding.py) rejects letters–digits–letters in ordinary words, the existing mojibake/punctuation signatures, and English status/type or machine-state enums in ES/PT drafts. Cited source-backed merchant literals, verified DSP/HO case references and masked-card literals are excluded **only from the prose-quality scan**. Original DLP, citation, number/date, promise and authorization checks still inspect the complete draft; citing an internal handle cannot authorize displaying it. Separate corrupt prose or raw status words remain rejected beside a legitimate merchant, including a merchant named `Approved`.

The verified prompt-boundary defect was that the [builder](../../src/aclara/agent/nlg/builder.py) sent `status=Approved` and `transaction_type=Purchase` to the phrase model. It now sends localized display labels (`aprobada`/`aprovada`, `compra`, etc.), retaining canonical source facts for grounding. Unknown display enums become “no disponible”/“indisponível”. The actual approved `plan.reply`, recognition/clarification guards, confident-opposite-language rejection, one correction and approved-text fallback remain in place.

[Phrase v2.1](../../prompts/phrase/v2.md) explicitly requires localized labels and ordinary spelling. SHA-256: `96089ad7985a334b8c6b974298856d939e554d431f04c6c1e7a434d75ec71fd9`. NLU stays v5.1. UTF-8/JSON roundtrip regressions preserve ES/PT accents; source inspection found no digit-substitution transform. This does **not** establish why the particular live generation emitted corruption: no provider generation was rerun or encoding incident inferred.

The initial 36 authored NLG checks were written before the fix: **26 failed / 10 passed**. The expanded 39 now pass, including all four statuses in both languages, model correction → fallback, legitimate `Studio3D`/`B2B Market`, amounts, localized dates, case IDs and masked card suffixes. Existing handle/mojibake/language regressions also pass. The context-free `scan_dlp` retains its existing checks; merchant-aware spelling/enum validation runs in `verify_draft` before accepting a model draft.

## NLU: canonical ledger kinds before MATCH

The [transaction contract](../../contracts/transactions.yaml) has exactly **Purchase, Withdrawal, Payment, Transfer, Deposit, Adjustment**. Previously only generic charge words were dropped; `compra` and other localized kinds remained literal strings. MATCH compares exact kinds, so this could suppress a correct candidate. The lead supplied an unchanged live-ledger replay showing `compra` → no match versus `Purchase` → propose; that live replay was not independently repeated here.

[Normalization](../../src/aclara/agent/nlu/transaction_types.py) now handles case, accents, spacing and stated ES/PT aliases: compra/consumo → Purchase; retiro/saque → Withdrawal; pago/pagamento → Payment; transferencia/transferência/pix/envío → Transfer; depósito/consignación → Deposit; ajuste and fee/comisión/tarifa/taxa → **Adjustment**, as confirmed by Sebastian under DSP-03. Unknown, generic and ambiguous expressions become `None`. No fuzzy inference from arbitrary prose is used. The raw `ExtractedNlu.type_expr` remains auditable; only `NormalizedSlots.type_expr` changes. Intent, product hints and MATCH thresholds stay intact.

The 61 original authored tests were written before the fix: **45 failed / 16 passed**. All 71 expanded checks now pass, including serving-shaped ES/PT inputs for the six kinds, unknown/ambiguous kinds, contract-vocabulary agreement, and a two-candidate example where raw `compra` yields a choice and canonical `Purchase` yields the correct proposal. These are synthetic fixtures, not organizer rows.

## Saved dev impact, no new conversations

[Replay harness](../../src/aclara/llm/dev_kind_replay.py): first freeze pre-fix slots and MATCH decisions, then change **only** the type slot and replay the same matcher/candidates. Journals align by generation ID with actual non-degraded NLU → MATCH events; repeated `llm_call` events are not extra attempts. Only P repeat 0 is selected from v3. Original files are unchanged; masked reconstruction data and per-case diagnostics remain in ignored `artifacts/nlu-kind-replay/`.

| Saved dev run | Original pass | Aligned MATCH / baseline action agrees with saved action | Cases with changed type (ES/PT) | Action or target changes | Correct proposals gained / lost | Failed cases with a gain and agreeing baseline action |
|---|---:|---:|---:|---:|---:|---:|
| V3 primary | 77/100 | 89 / 89 | 11 (10/1) | 2 | 2 / 0 | 0 |
| Robustness 40 before | 39/40 | 37 / 37 | 13 (7/6) | 0 | 0 / 0 | 0 |
| Robustness 40 after | 39/40 | 37 / 37 | 8 (4/4) | 0 | 0 / 0 | 0 |
| Round two before | 15/60 | 90 / 80 | 26 (15/11) | 13 | 9 / 0 | **5** |
| Round two partial after | 9/47 | 63 / 52 | 23 (14/9) | 9 | 5 / 0 | **0** |

V3's saved valid outputs contain generic `transacción`, `transação` and ambiguous `débito`, **no `compra`**. Removing these unknown kinds gains two direct proposals in conversations that already passed. One failed v3 case has a changed type, but its decision does not improve. The robustness-40 failure also has a changed type with no decision change. Thus this replay explains **no observed v3/robustness-40 failed outcome**.

Round-two before has `compra` on 50/140 valid NLU calls; partial after has it on 41/98. Eighteen originally failed before cases have a changed MATCH type; nine gain a correct proposal in reconstruction, but only **five** also reproduce the saved baseline action. Those five are plausible type-driven contributors, **not proven rescued conversations**. All five proposal gains in partial-after occur where baseline reconstruction disagrees with the saved action, so none is credited as an explained failure. No correct proposal is lost in the replay. Before/after runs overlap; do not sum them as independent cases.

Limits: saved snapshots lack `process_date`, so reconstruction uses the transaction day, with authored surrogate customer/product IDs. Prior sticky slots, active-product state, subsequent decisions, writes and readbacks are not replayed. Action agreement alone does not prove identical ranked candidates or probabilities. **No new pass rate, SAR or unsafe rate is claimed.** The original v3 result remains 77/100. The 40-case decision stability is a regression observation, not evidence that this boundary defect is harmless on the serving ledger.

Private baseline SHA-256: `f3ab2b76f89d723d7b7fff8df37d3c449b13065b6555acd336f7ec6e2cb3cc73`; source digest: `e24d7c78e80b856958a3f9c8eced0ce0e86bbcc0273aa1118968e9acb7803766`. Pinned unchanged MATCH v2 files: model `9b5c36d4405fc117b1cf31bc37c754aff039f8f17ecb67e475ee5b874bfe3cea`, metadata `f57f9875c951acbe3bdabf842b96a4f5233cf6d91f77e8b000a5b78c697a41ca`, LightGBM `8de9ee586478824860e7c9dc2ef8e8d1fa3e18d0b1e2fea43d835bc15dd9f602`.

Reproduce with `LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 python -m aclara.llm.dev_kind_replay`: `freeze` takes explicit `--source` retired-dev directories and a new private `--baseline`; `compare --baseline artifacts/nlu-kind-replay/baseline.json --report artifacts/nlu-kind-replay/new-report.json` applies current canonicalization to the original frozen baseline. A newly frozen baseline on fixed code will naturally show no type change. Both phases have no provider or database call path, refuse other source directory names and never overwrite baseline/report data.

**Owner handoff:** AI owns the NLG guard, display-fact localization and type normalization. Lead owns merge, deployment and any later live acceptance check; no new paid run is authorized here. The separate [partial comparison PR #85](https://github.com/sebastian-gm/bank-agent-lab/pull/85) stops on HTTP and provider credit/quota codes, including HTTP-200 `provider_402`; it remains partial, with no further comparison spending.

Local validation: **293 focused mock tests passed**, covering NLG integrity, NLU normalization/recognition, language/clarification handling, degraded operation, integration, unchanged MATCH and interfaces. Ruff, strict mypy (90 source files), compilation, frozen-interface and policy-catalog checks pass. Remote main-target CI is required before lead merge.
