# Post-v3 authored NLU robustness study

## Preregistered protocol

The AI lane authored and structurally validated 40 entirely synthetic dev
conversations before running P or fixing language behavior. Gold comes from
[ADR-0015](../../adr/0015-post-v2-conversation-and-policy-contract.md), not model
outputs. Neither the inputs nor gold may change after this freeze. No v4 data
was opened. This is a development study, not a held-out evaluation.

The [manifest](../../../evals/studies/llm/dev_robustness_40.manifest.json) freezes
the authored YAML, builder and materialized ScenarioV2 hashes. ES has five
cases each of es-MX, es-CO, es-AR and es-CL; pt-BR has twenty. The shared
ScenarioV2 and bank-country enums have no Chile entry, so es-CL speech uses a
synthetic MX/USD banking fixture while its locale remains AI-owned metadata.
This measures language understanding, not Chilean banking policy.

Overlapping slices cover typos (11), es-CL slang (5), amounts in words (8),
relative dates (8), same-merchant twins (8), changing one's mind after an offer
(4), existing-case status (4), human request plus charge (4), embedded injection
(4), and mixed ES/PT (4). Outcomes are 16 filed disputes, 14 explanations,
two cancellations, four case-status reports and four human escalations.

Measure real P at baseline `32587c9`, then the same immutable conversations
after narrowly scoped NLU/NLG fixes. Use the existing bound ASGI execution path
and independently read back actions; no Azure customer or organizer rows.
Gemini 3 Flash remains primary, Jev risk union remains enabled, and Grok stays
failure-only fallback. No model-selection or judge experiment is authorized.

Every paid attempt, including retries and Jev, reserves against the existing
`dev-gate/post-v3` / `post-v3` durable scope. Before each new reservation,
atomically check that charged exposure plus that reserve is at most **$0.90**.
The scope's unchanged lifetime cap is $1, shared with the lead. Initial readback
was **$0.40238433** including retained reserves; known usage was $0.36640233.
Estimated additional exposure for both measurements is $0.25–$0.40.

Report all-case success with 95% Wilson intervals, ES/PT and feature slices,
unsafe predicates and injection-event coverage, case latency p50/p95, and
known per-call cost. Unknown provider usage retains its reserve but is never
reported as billed cost. Keep outputs and call evidence in ignored mode-0600
artifacts; commit aggregates only. Latency excludes production Postgres and
workstation-to-Azure serving reads but includes model and budget round trips.

## Results

The freeze had structural validation only; no B1/P execution or output-informed
changes preceded it. Results below use the unchanged inputs and gold.

## Completed measurements

Freeze commit: `31826c6`. Baseline execution: `2753ac136ba29d53ce86a7b33295e65e1583f6ae`
(P behavior from PR #62, `32587c9`). After execution:
`5bf198d8c3f6a35028351c635dc316948802725c`. All three manifest hashes read
back unchanged after both runs. Both launches used clean committed trees.

| Metric | Before | After |
|---|---:|---:|
| Full-conversation success | 39/40 (97.5%) | 39/40 (97.5%) |
| Success, Wilson 95% interval | 87.1–99.6% | 87.1–99.6% |
| ES success, 95% interval | 19/20; 76.4–99.1% | 19/20; 76.4–99.1% |
| pt-BR success, 95% interval | 20/20; 83.9–100% | 20/20; 83.9–100% |
| Unsafe / forbidden-action cases | 0 / 0 | 0 / 0 |
| Embedded injections logged and safely handled | 4/4 | 4/4 |
| Opening amount/date normalization failures | 9 | 0 |
| Clarification responses / all responses | 15/83 | 6/74 |
| Case latency p50 / p95 | 7.877 / 12.195 s | 5.423 / 12.273 s |
| Turn latency p50 / p95 | 4.025 / 7.462 s | 4.023 / 8.476 s |
| OpenRouter schema-valid / ALL OpenRouter attempts | 89/89 | 75/75 |
| Jev valid / ALL Jev attempts | 59/59 | 50/50 |
| Known per-call cost, all providers | $0.124548836 | $0.106383848 |
| Known cost / completed conversation | $0.003113721 | $0.002659596 |
| New unknown-cost attempts | 0 | 0 |

All feature slices have the same pass counts before/after: typos 11/11;
es-CL 5/5; amounts in words 8/8; relative dates 8/8; twins 8/8; mind change
3/4; case status 4/4; human-plus-charge 4/4; embedded injection 4/4; mixed
4/4. Features overlap. Successful outcomes often required clarification before
the fix: outcome success alone concealed the avoidable language-layer work.

The nine fewer clarification turns and nine fewer NLU/Jev pairs follow the
normalization fix. Median case latency fell by 31.2% and known cost by 14.6%
in these observations; p95 case latency did not improve and p95 turn latency
increased. These are single before/after runs, with provider variability and
no randomized repeats; do not interpret latency changes as causal estimates.
The 95% case-bootstrap ranges overlap: p50 6.544–10.147 s before versus
4.145–7.481 s after; p95 11.063–19.622 versus 10.045–19.444 s.

## Diagnosis and ownership

**AI lane — fixed:** the extractor preserved the right spoken expressions,
but `parse_amount` handled only small isolated words. Eight opening amounts
therefore failed normalization. Its earlier first-small-word search could also
silently truncate a composite expression. The new bounded ES/PT grammar
accepts a complete whole number through 999999 with an optional known unit;
it rejects ambiguous alternatives, malformed composites and unsupported
fractional/vague expressions instead of extracting a smaller token. Regional
currency and multiplier rules remain in the existing country-aware normalizer.
Forty-five authored parser checks cover supported forms and conservative
rejection, rather than copying gold from model outputs.

One further opening used the pt-BR previous-weekday expression: the parser
looked for Spanish `pasad` but missed Portuguese `passad`. Both now resolve
against the established bank business day. Stated ES/PT day/month expressions
also parse; without a year, only a valid date already reached in the current
bank year resolves. Future or incomplete dates still ask for clarification.
The saved baseline opening outputs replayed at zero cost go from nine slot
clarifications to zero, while retaining all four mixed-language clarifications.

**Lead lane — remains open:** `robust.co.cancels-after-offer` reaches the correct
cancellation with no write, but misses its required offer. The raw model flag
and postprocessed flag are both true and intent is `charge_inquiry`. MATCH
proposes the owned target at probability 0.9649. Then
[`selection.uncertain`](../../../src/aclara/agent/selection.py#L25) treats charge-origin
non-recognition as transaction-selection uncertainty and clears the match in
[`app.py`](../../../src/aclara/api/app.py#L1173). The authored customer's subsequent
clarification explicitly denies the purchase, so code proposes a dispute and
the customer cancels, bypassing the offer. A separate zero-cost replay reproduces
the guard returning true while NLU's unfamiliarity flag stays true.

Lead follow-up: extend the deterministic unfamiliarity exception narrowly for
charge-origin memory statements, while preserving genuine uncertainty about
which transaction the customer means. Add ES/PT conversation regressions for
that distinction. The AI PR does not edit the lead's guard or state machine,
or rewrite the frozen fixture to mask this failure. Gold follows ADR-0015 and
has no suspected error in this case.

**NLU prompt / NLG:** all 36 openings that reached real extraction had the
correct raw taxonomy label; four human requests followed code's early handoff
path. Keep `nlu@v5.1` and `phrase@v2`. No prompt patch is supported by these
observations. The existing phrasing verifier logged one language-mismatch
rejection before and seven after; it retried or used approved text. No unsafe
candidate reached the scored output. These rejection counts do not establish
human-reviewed language accuracy; no NLG outcome failure was found.

## Routes, evidence and budget

Both measurements used the unchanged selected routes in
[models.yaml](../../../config/models.yaml): `google/gemini-3-flash-preview` via
ZDR `google-vertex/global`, maximum 2048 output tokens, 6-second first-attempt
and configured 20-second retry timeout, 45-second total call deadline;
`jev-1.13.0` parallel risk-only union; and failure-only
`x-ai/grok-4.20` via `xai/zdr` (not invoked in either run). No judges ran.

- `nlu@v5.1` SHA-256: `e40182de2f232932a12d61d722be5e6356d787217048378fbc2a84f330d241cc`.
- `phrase@v2` SHA-256: `8c221fbe233fd14c91c092c2d80944517c6ad5d8308e0a0e276ff8f68e81171e`.
- Private mode-0600 evidence: `artifacts/nlu-robustness-post-v3/{before,after}/launch.json`,
  call journals, per-conversation results and aggregate summaries; separate
  `lead-guard-reproduction.json`. No organizer rows or model reasoning were used
  or persisted. Only aggregates and project-authored fixtures are committed.

Cost by route: before NLU $0.1140755, phrasing $0.0092655, Jev $0.001207836;
after NLU $0.0966785, phrasing $0.008685, Jev $0.001020348. Combined new known
usage cost is **$0.230932684**. Attribution comes only from per-call usage/cost
fields in the study journal, grouped by authored case ID. The bound harness's
case cost can repeat earlier metadata when a client is reused; that field was
not used for these cost estimates. No key-level balance delta was used.

Durable readback after both runs: scope **`dev-gate/post-v3`**, run **`post-v3`**,
**679 reservations**, known cost **$0.59733554**, charged exposure including
retained reserves **$0.63331754**. All three unknown-cost reservations predate
this study; their retained exposure is **$0.03598200**. The scope rose from
$0.40238433 to $0.63331754, including conservative eight-decimal rounding.
The requested $0.90 stop and unchanged $1 lifetime cap were respected; the
runner checks exposure plus every new reserve under the scope lock before
calling any provider. Prior scopes plus this scope read back **$4.45690716**;
no final evaluation scope was touched. No additional paid run is planned.

## Validation and limits

`make checks` passes: six hooks, strict mypy, compilation, staged-file policy,
**360 tests passed / 14 database-dependent skips**, B1 32/32 with 12 readbacks,
interfaces and policy catalog. Additional strict-mypy CLI and B1 reactive dev
32/32 pass. Runtime changes are confined to `agent/nlu`; the study harness is
in `llm`, with AI tests and docs. The progress log is the only shared-file edit.

This authored dev set is small and not independently human-reviewed. There is
no fluent human PT review; synthetic es-CL speech on an MX banking fixture does
not validate Chilean policy or population fairness. The simulator supplies
explicit information and confirmation, so a human may behave differently.
V4 remains blind and unexecuted by this lane. The lead owns the remaining guard
fix, merge and release. [PR #65](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/65) is open,
unmerged, targeting `fix/post-v3-analysis`. All four remote checks completed
with failure because jobs could not start: their annotations state that an
Actions budget prevents use. Local passing checks do not imply remote CI green.
