# Portuguese wording review (model-reviewed, development only)

On 2026-09-27, `anthropic/claude-sonnet-5` via OpenRouter reviewed **all 17 active AI-lane pt-BR customer templates and Portuguese prompt/example groups**. The input was an explicit list of synthetic strings and intent examples, not source files, customer records, or hidden prompt bodies. It covered `agent/nlg/builder.py`, the DLP fallback in `agent/ai.py`, the Portuguese examples in NLU v4, and the terms in the Jev typed questions. Phrase and judge prompts are English instructions with no additional Portuguese sentence. This is **model review, not human pt-BR validation**. The one valid review attempt cost **$0.044504** from its per-call cost field and covered 17/17 IDs.

| Location / situation | Before | After | Decision |
|---|---|---|---|
| `builder.py`, unknown transaction status | “A transação de {amount_date} tem estado indisponível.” | “O status da transação de {amount_date} não está disponível.” | Accepted the unnatural-phrasing finding, but kept the claim about **status availability** rather than saying the transaction itself is unavailable. |
| `builder.py`, out-of-scope human offer | “Posso ajudar com cobranças não reconhecidas. Posso encaminhar você a uma pessoa.” | “Posso ajudar com cobranças não reconhecidas ou encaminhar você a uma pessoa da equipe.” | Accepted; removes repetition and identifies the destination. |
| `agent/ai.py`, verified-case DLP fallback | “Consulte o status verificado do caso.” | “Consulte o status verificado do seu caso.” | Accepted; clearer possession without changing action claims. |

Sonnet found the remaining active AI-lane examples and templates natural enough to leave unchanged. It noted that “foi recusada” sounds more definitive than “aparece como estornada/aprovada”; we retained the difference because the strings describe distinct recorded transaction statuses. The NLU prompt’s denial/uncertainty examples preserve Sebastian's intent-label rule; no taxonomy or gold label changed.

An earlier **extra-scope** attempt on lead-owned strings returned two `length`/truncation failures and no usable review. Its per-call costs were not persisted by that failed helper, so the full **$0.255** local reserve remains conservatively treated as exposed. With the valid $0.044504 AI-lane review, this was at most **$0.299504** against the original $0.30 cap. That attempt stopped without source changes.

## Lead-owned strings: completed model review and proposed patch

Sebastian separately approved a **new $0.30 cap** for the lead-owned review and then explicitly approved all **35** strings after the saved inventory, previously described as 34, was recounted. The inventory contains 28 active `api/app.py` strings, four `api/workflows.py` strings, one `handoff/packet.py` string and two `api/staff.py` strings. Each was checked against current source. The input contained only these synthetic wording strings and short context labels, with no customer rows, secrets or source files. This is **model review, not human pt-BR validation**.

`anthropic/claude-sonnet-5` reviewed **35/35** under durable Postgres scope `pt-review/lead-strings`, run ID `lead-strings`. Nine sequential calls used groups of at most four and `max_output_tokens=3072`; all nine returned valid complete responses with no truncation or retry. Scope readback: **$0.30 cap, nine attempts, $0.048878 known and charged, zero unknown-cost attempts**. The running `final-evaluation-v2` scope was not used. Detailed synthetic checkpoints remain in ignored `artifacts/`.

After final v2 completed and the owner lifted the freeze, the lead accepted and applied **only A20 and W02** below. The [original proposal patch](pt-review-lead-proposed.patch) remains as the review record. A20 clarifies the handoff destination; W02 names the verification-code and confirmation steps already enforced by the workflow. An exact source comparison and normalized AST comparison verified that these are the only source changes; control flow and policy are unchanged.

| ID / location | Before | After lead acceptance | Model finding and decision |
|---|---|---|---|
| A20, `api/app.py` out-of-scope reply | “Posso ajudar com cobranças não reconhecidas. Para outro assunto, posso encaminhar você para uma pessoa.” | “Posso ajudar com cobranças não reconhecidas. Para outro assunto, posso encaminhar você a uma pessoa da equipe.” | Sonnet flagged destination terminology. Accepted the finding; aligned the final phrase with the existing AI-lane wording. |
| W02, `api/workflows.py` card-freeze option | “Você pode bloquear seu cartão com um novo OTP e confirmação.” | “Você pode bloquear seu cartão após informar um novo código de verificação e confirmar a ação.” | Sonnet flagged awkward phrasing. Accepted the finding; expanded user-facing “OTP” and stated the two required steps plainly. |
| A15, `api/app.py` human handoff | “Vou encaminhar sua solicitação para uma pessoa. O pacote de atendimento está preparado.” | **Unchanged.** | Sonnet proposed “Estou preparando o pacote de atendimento” for a suspected premature completion claim. Rejected: the packet is already created before this reply, and the response is returned after the durable handoff readback. The suggestion would make the state less accurate. |

Sonnet marked the other **32** strings as keep: A01–A14, A16–A19, A21–A28, W01, W03–W04, H01 and S01–S02. With A15's rejected change, **33/35 remain unchanged**. The applied patch changes only wording. It changes no workflow behavior, policy, authorization or action state. A15 remains unchanged after the lead independently checked packet creation and durable readback before the response. This follow-up used no paid calls and did not rerun or change final v2.

Lead verification: `make checks` with `LLM_PROVIDER=mock`, real calls disabled,
and the final-run start flag disabled passed **174 tests / 13 skips**, B1
**32/32**, all pre-commit checks, compilation, interfaces and policy catalog.
Fresh PR CI gates the merge; no new paid review or Azure deployment was made.
