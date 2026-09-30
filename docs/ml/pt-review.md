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

## 2026-09-29 — post-v3 ES and pt-BR cross-vendor copy review

Status: **model-reviewed**, not fluent-human validated. Review model:
`anthropic/claude-sonnet-5`, OpenRouter `google-vertex/global`, strict JSON,
ZDR requested and data collection denied. The system remains Gemini 3 Flash;
this review changes neither the serving model nor the judges. V4 was not opened.

Compared active product source to `e12efc7`, including the PR #66 candidate
`b059920e78c6a299451b38b0860c78acdd704f48`. All eight added web translations
in that reviewed source snapshot are included. Later `otpRetry` translations
from PR #68 are outside this 134-item model review. To cover the requested templates, offer and recognition questions,
the audit also includes existing approved copy whose delivery changes under
phrase v2, plus the surrounding API/workflow copy for consistency. Status
variants and repeated source occurrences are counted separately. No customer
rows, human test messages, credentials or model thinking entered the review.

| Inventory IDs | Source | ES / pt-BR count | Coverage |
|---|---|---:|---|
| C001–C084 | `src/aclara/api/app.py` | 42 / 42 | Approved explanations, policy-reason wording/labels, handoff/refusal, language help, recognition question, search/choice prompts, proposals and verified/cancelled results |
| C085–C092 | `src/aclara/api/workflows.py` | 4 / 4 | Human handoff, freeze offer, confirmation and verified result |
| C093–C094 | `src/aclara/agent/ai.py` | 1 / 1 | Verified-case DLP fallback |
| C095–C126 | `src/aclara/agent/nlg/builder.py` | 16 / 16 | All templates; offer and explanation variants for all four supported statuses |
| C127–C134 | `apps/web/src/lib/messages.ts` | 4 / 4 | `starting`, `startupUnavailable`, `stepUpRequired`, `verifyAndConfirm` |
| **Total** | Five product source files | **67 / 67** | **134/134 reviewed** |

The source diff also covered the changed chat/workspace/BFF and language guard
paths in that reviewed snapshot: they introduce no additional ES/PT literals
outside this inventory. This is not an inventory of later integration/UX copy.
Private inventory SHA-256:
`ad8768b88d9d7f8617d0eba08232284781ed31ad0f24a60329a1e680caafd4ef`.
Inventory, validated final judgments and per-call metadata remain mode-0600 in
ignored `artifacts/copy-review-post-v3/`. No raw provider envelope or reasoning
is saved. Review checks naturalness, terminology and **tú/você**, preserving
placeholders, amounts, deadlines, confirmation conditions and action states.

### Accepted before/after proposals

The following is a **lead-owned strings-only proposal**. The ready-to-apply
[patch](copy-review-post-v3-proposed.patch) changes six source occurrences in
`api/app.py` and `api/workflows.py`; this AI PR does not edit those folders.
All AI templates, offer/recognition questions and the eight new web messages
were reviewed and retained. The patch needs lead review/application before
release; merging this documentation alone does not activate these changes.

| ID / status | Before | Proposed after | Decision |
|---|---|---|---|
| C062 / C068 / C074 — model-reviewed | `Disputa cancelada.` (PT) | `Contestação cancelada.` | Accept Sonnet's terminology correction in all three PT branches; Spanish remains `Disputa cancelada.`. |
| C087 — model-reviewed | `Puedes bloquear tu tarjeta con un nuevo OTP y confirmación.` | `Puedes bloquear tu tarjeta después de indicar un nuevo código de verificación y confirmar la acción.` | Accept plain-language expansion of OTP, matching the existing PT wording. Preserve the leading separator space, new-code requirement and separate confirmation. |
| C042 — model-reviewed; maintainer terminology follow-through | `Você confirma o registro de uma disputa de {amount} em {merchant}? Isso abrirá um caso; não garante reembolso.` | `Você confirma o registro de uma contestação de {amount} em {merchant}? Isso abrirá um caso; não garante reembolso.` | Sonnet kept this full sentence. Apply its accepted PT terminology correction consistently to the same workflow's proposal; this exact replacement is a maintainer decision. |
| C046 — model-reviewed; maintainer terminology follow-through | `Sua disputa {case_id} foi registrada e verificada. A próxima etapa é a análise; resposta em até 15 dias (SLA simulado).` | `Sua contestação {case_id} foi registrada e verificada. A próxima etapa é a análise; resposta em até 15 dias (SLA simulado).` | Sonnet kept this full sentence. Apply the same terminology correction to the verified result; keep readback and simulated SLA claims unchanged. |

Sonnet suggested seven changed occurrences. Four are accepted above; the other
three remain **model-reviewed, kept as written**:

| ID | Before = final after | Declined suggestion / reason |
|---|---|---|
| C022 | `Vou encaminhar sua solicitação para uma pessoa. O pacote de atendimento está preparado.` | Replacing `uma pessoa` with `um agente` is cosmetic; current wording makes the human destination clear and preserves the previously reviewed packet state. |
| C027 | `El cargo de {amount} en {merchant} figura como rechazado; no hubo movimiento de dinero.` | `figura` → `aparece` adds no clarity; both are natural. |
| C041 | `¿Confirmas que registre una disputa por {amount} en {merchant}? Esta acción abrirá un caso; no garantiza un reembolso.` | The first-person subjunctive is grammatical and expresses the assistant's proposed action. Keep it instead of a noun-phrase rewrite. |

Sonnet kept the other **127 occurrences**. Two of those receive the explicitly
marked maintainer terminology follow-through above. Final proposal totals:
**six changed source occurrences, 128 unchanged**, four distinct replacement
strings. No register change, policy condition, deadline, placeholder or flow
change is proposed. In particular, `stepUpRequired`, startup/retry text, both
recognition questions and all eight grounded offer status variants remain
**model-reviewed, before = after**.

### Accounting and validation

Owner authorization: **≤$0.10**, existing durable scope `dev-gate/post-v3`, run
`post-v3`, and **stop at $0.90 shared exposure including reserves**. Concurrency
was one, using this worktree's own OpenRouter key. Every attempt committed its
reservation before the provider call under the scope lock; the same lock checked
the unchanged $1 lifetime allowance and the $0.90 stop. No scope was created,
reset or increased; no final-evaluation scope was used.

Eight batches of ten used a 2048-token output ceiling. After 80 reviews, the
conservative reservation check stopped before another request. The remaining
54 used two compact batches of 27 with a 768-token output cap and optional
reasoning disabled, confirming every reviewed ID and returning only literal
edit spans. This changed only the private review process. Sonnet's public
catalog reported $2/M input, $10/M output and non-mandatory reasoning; the
[OpenRouter reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
document disabling optional reasoning. No hidden reasoning was read or saved
in either phase.

All **10/10 provider attempts** produced valid final JSON: **134/134 IDs**
accounted for, no truncation, retries, refusals or unknown costs. Usage totals:
**13,264 input / 5,940 output tokens** (billed output may include internal
reasoning in the first phase). Per-call cost fields sum to **$0.085928**;
readback of those ten durable reservations confirms **$0.085928 known and
charged**, zero unknown attempts. A reservation rejection incurred no paid call.
No key-level balance delta was used.

Shared scope readback: **689 reservations**, **$0.68326354 known**,
**$0.71924554 charged including reserves**, three unknown-cost reservations
that predate this review. Initial exposure was $0.63331754. Prior scopes plus
this scope read **$4.54283516**; this is budget metadata, not review cost.
Both the $0.10 review cap and $0.90 shared stop were respected.

The proposal applies cleanly to the target source (`git apply --check`), and
both shadow Python modules compile. AST comparison verifies string constants
are the only changes; original placeholders and numeric literals are preserved.
No runtime behavior or product-language accuracy claim follows from this review.

### Lead application and review boundary

The lead accepted all six proposed occurrences during integration. Five PT
changes consistently use `contestação`; the ES freeze sentence explains a new
verification code and separate confirmation. PR #68 had inserted provenance
code beside the freeze offer, so that hunk required a mechanical context update.
AST comparison confirmed exactly six string-constant changes, four distinct
replacements, and identical non-string code/placeholders/numbers. This does not
extend the paid review to later OTP retry or UX strings; those remain subject
to maintainer checks and the existing no-fluent-human-PT limitation.
