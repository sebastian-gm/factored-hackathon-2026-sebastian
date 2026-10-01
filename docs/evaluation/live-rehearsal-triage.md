# Live rehearsal freeze blockers (2026-10-01 UTC)

The rehearsal used deployed `c32fd6429281a764ee33dd96622f237c7c0289c3`.
Diagnosis read the four explicitly identified conversations through the non-owner
Azure connection and their original customer/run/session RLS scopes. Unscoped
reads returned zero rows; no permissions or Azure configuration were changed.
Private references and traces are ignored, mode 0600, under
`artifacts/live-rehearsal-triage/`. No organizer row values or provider prose are
included in this document. No new model calls were made.

| Symptom | Verified cause | Owner / action |
| --- | --- | --- |
| ES corrupted word and English status | The chosen movement's response used Gemini phrase output, `used_template=false`, with no grounding violations. The lead fallback also inserted the raw English status. An authored corrupted draft passes the current guard. | Lead: localize fallback status. AI: generic corruption/status guard and safe fallback regressions. |
| PT clarification followed by ESC-04 | Both original MATCH events returned `none`. Persisted normalized slots retain Portuguese `type_expr=compra`; candidates use canonical transaction kinds. Same Azure scope replay returns `none` (exists 0.009804); canonical `Purchase` returns one proposal (exists 0.9888), policy eligible. | AI: normalize stated ES/PT kind aliases before MATCH. Thresholds stay unchanged. |
| Fresh Desk SLA spans months | Packet creation/deadline use wall time, but Desk subtracts the June ledger clock. Fixture timestamps hid the mismatch. | Lead: wall time for live operational deadlines, fixture clock only in fixture mode. |
| Empty facts/actions | Generic packet paths start with empty arrays. Desk previously projected only freeze outcomes; it omitted even independently verified handoff creation. | Lead: scoped identified-movement facts, committed/read-backed action evidence, and an explicit empty-facts explanation. |

The PT comparison uses **persisted final slots**, not a reconstructed per-turn raw
model frame. The two live MATCH events and the unchanged-model replay agree; the
alias-only replay is diagnosis, not a paid end-to-end receipt claim. A separate
plain PT inquiry in the same persona did reach three choices and an explanation.

The local serving projection for this PT persona has four movements, three blank
merchant names and one policy-eligible movement. Its `ambiguous` story hint is
absent under the current reviewed data gate. The frontend also rejects Ops-role
personas in live story selection, despite those sessions supporting customer chat.
These helper/binding limitations need coordinated frontend/data review; inventing
movement details or enabling an unsupported ambiguity story is not a fix.

## Lead fix boundaries

- Persist the identified handle in the conversation. Read its current scoped,
  120-day serving view for the packet; never treat unresolved candidates as facts
  and never borrow another tab's selected charge.
- Keep a proposal distinct from a completed action. Include a prior dispute only
  after reading its persisted case from this conversation's execution history.
  Record handoff creation after checking its committed packet; return 503 on
  missing/mismatched readback. Offered/declined/unavailable freezes are not writes.
- Desk displays verified handoff/dispute actions and existing freeze evidence.
  An unselected fraud or ambiguity handoff can legitimately have no transaction
  facts; it now says so explicitly in ES/PT.
- Confirmation, OTP, policy rules, MATCH thresholds and organizer bindings are
  unchanged. No Azure release has been performed for these fixes.

## Verification

Commands run from the repository with `LLM_PROVIDER=mock` and real calls disabled:

- `.venv/bin/pytest`: **503 passed / 22 skipped** at the lead-fix candidate before
  adding the independent OpenRouter preflight tests.
- `.venv/bin/python -m scripts.test_postgres`: **29 passed**, including authored
  serving promotion, non-owner RLS, packet facts/actions and restart. The additional
  missing-packet regression passed in the subsequent focused run.
- `pnpm --dir apps/web test:e2e`: **93 passed**.
- `pnpm --dir apps/web test:e2e --staff`: **1 passed**, through real local
  FastAPI/BFF: fresh SLA approximately 360 hours, verified handoff action and the
  empty-facts explanation. This is an authored local live-mode check, not Azure.
- Ruff, strict mypy (**88 files**) and web typecheck passed.
- Focused credit-gate plus handoff regressions: **21 passed / 1 Postgres skip**,
  using mocked HTTP and isolated operations.

Captured command receipts/logs are ignored under `artifacts/integration/checks/`.
AI NLG/type-alias fixes, combined remote CI and a new Azure receipt remain pending.
V4 is unstarted; its rows/selections/bindings remain unopened. Freeze is blocked.

## Round-two review: offer refusal (lead-owned)

The #85 failure breakdown identified a second state-machine issue independent of
live rehearsal: a polite explicit refusal of filing was accepted by NLU as
uncertainty, but orchestration recognized only four exact cancellation words.
A fresh authored mock replay on both B1 and P produced a dispute proposal in ES
and an out-of-scope handoff in PT, with zero writes. No frozen round-two or v4
row was inspected or changed to reproduce it.

The generic offered-charge guard now accepts explicit ES/PT filing refusals,
cancels without success credit, and clears the retained offer/slots. An actual
recollection in the same reply still ends in explanation; isolated yes/no or
uncertainty still needs clarification. Security and required human routing retain
precedence. No confirmation, OTP, write authority, policy or MATCH threshold was
relaxed. Authored B1/P ES/PT tests include the #85 false-recognition frame and
restart, and the existing recognition/denial checks remain in the gate.

`pytest tests/test_offer_refusal_state.py tests/test_nlu_round2_regressions.py
 tests/test_conversation_v3.py`: **50 passed**, mock only. This does not establish
a fresh real-model pass rate. The broader compound concerns, descriptive
candidate replies and two-round language-limit conflicts listed in the AI study
remain limitations; this small repair does not claim to solve them.
