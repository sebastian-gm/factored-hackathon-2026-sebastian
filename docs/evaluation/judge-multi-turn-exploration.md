# A judge's multi-turn conversations

**What this shows:** Thirty authored Spanish/Portuguese conversations through the actual mock API.
**Result:** 15/30 met every scripted goal, with 75/109 passing turns; all checked write boundaries and receipt reads passed.
**Limits:** This tests supplied NLU observations and small synthetic ledgers, not live-model understanding or browser quality. Measured after the final evaluation; official v4 results are unchanged.

The unchanged base API (`5a1f574`) had 727/798 passing assertions, ES 9/15 and PT 6/15 conversations meeting every goal. Controls passed: 100 no-financial-write checks, 109 mock/zero-spend checks, 12 independent case reads and 21 handoff reads. Spend: **$0**. Fourteen turns missed workflow expectations and 23 missed UX expectations; these sets overlap. A missed goal is not automatically a safety or product defect.

## Each conversation

These are synthetic fixture IDs. “Met” means all authored checks passed, including continuity goals. The experience note distinguishes genuine loss of context from conservative matching or an incorrect authoring assumption. Unmet downstream steps can be consequences of the first divergence.

| Case | Language | Scripted goals | Observed experience |
|---|---|---|---|
| JE-01 | ES | Not met (turn 2) | Why/now/timing lose the charge; choices then transfer. |
| JE-02 | PT | Not met (turn 2) | Same follow-up loss in Portuguese. |
| JE-03 | ES | Not met (turn 2) | Follow-up rematches; valid recovery meets a choice loop. |
| JE-04 | PT | Not met (turn 2) | Reversal follow-ups require reselection. |
| JE-05 | ES | Not met (turn 3) | Recognition works; thanks triggers a terminal transfer. |
| JE-06 | PT | Met | Button cancellation consumes the proposal; new inquiry works. |
| JE-07 | ES | Met | Text cancellation and a different charge work. |
| JE-08 | PT | Not met (turn 3) | Recognition works; second charge meets a safe matcher choice. |
| JE-09 | ES | Met | Ordinal choice identifies the intended charge; cancellation works. |
| JE-10 | PT | Met | Competing choices stay unresolved; explicit selection works. |
| JE-11 | ES | Met | Amount correction produces the right proposal; cancellation works. |
| JE-12 | PT | Not met (turn 1) | Safe choice on wrong date; later correction needs an ordinal. |
| JE-13 | ES | Met | Changed amount produces a new target; verified case/status work. |
| JE-14 | PT | Not met (turn 1) | Explicit date uncertainty clarifies: initial expected choice was an authoring assumption; correction works. |
| JE-15 | ES | Met | Two verified cases work this run; older-case lookup failed in another unchanged run (fixed in held #161). |
| JE-16 | PT | Not met (turn 1) | Conservative matching asks choices; returning to the first charge gets stuck. |
| JE-17 | ES | Not met (turn 2) | Off-topic turn transfers permanently; later dispute cannot resume. |
| JE-18 | PT | Met | Scope response and explicit human request keep the same handoff. |
| JE-19 | ES | Not met (turn 1) | Greeting creates a terminal transfer before the charge question. |
| JE-20 | PT | Not met (turn 3) | Case files; thanks transfers; later status repeats the handoff. |
| JE-21 | ES | Met | Insult stays calm; explicit denial then cancellation work. |
| JE-22 | PT | Met | Frustration preserves the recognition question and explanation. |
| JE-23 | ES | Met | Human request supersedes a proposal; repeats retain the handoff. |
| JE-24 | PT | Met | Human request during choices supersedes selection. |
| JE-25 | ES | Not met (turn 3) | Natural next-step case question rematches; direct status wording works. |
| JE-26 | PT | Met | Missing case clarifies; filed case is subsequently readable. |
| JE-27 | ES | Met | ES to PT to ES switch preserves the explicit charge. |
| JE-28 | PT | Not met (turn 2) | Safe matcher choice blocks the new action; later status/language cannot complete. |
| JE-29 | ES | Met | Overlong input rejects; typos/emoji recover; text yes never files; button receipt verifies. |
| JE-30 | PT | Not met (turn 3) | Long valid input accepts and injection refuses; isolated “sim” creates a terminal transfer. |

## Five weaknesses a judge would notice

1. **Short follow-ups lose context.** “Why?”, “what now?” and “how long?” can restart selection, then trigger a transfer (JE-01–04).
2. **Everyday case questions miss status lookup.** “What happens now with the dispute?” rematches charges; direct “case status” works (JE-25).
3. **Greetings and thanks can end the chat.** The required scope transfer is terminal, so later valid banking questions repeat the handoff (JE-05, 17, 19, 20, 30). This complies with the current policy but feels robotic.
4. **Corrections are awkward inside choices.** A corrected date is not an ordinal choice and can keep the judge stuck (JE-12). Other matcher choices remain appropriately conservative; thresholds were unchanged.
5. **The newest case could be misidentified.** Random case-ID ordering sometimes selects the older of two cases (JE-15). The authorized one-line API fix and deterministic ES/PT × B1/P regressions are in [held PR #161](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/161), pending lead review and CI.

## Reproduce and read the limits

Run `LLM_PROVIDER=mock .venv/bin/python -m docs.evaluation.judge_exploration --output artifacts/judge-exploration/new-run`. The [runner](judge_exploration.py) exits **1 when scripted goals remain unmet**, without hiding failures. It refuses output overwrites and live mode. Inputs are [30 project-authored cases](judge-exploration-cases.json); all 93 message observations validate against the actual NLU schema. Each story has one or two relevant invented charges. The API owns matching, policy, scoped state, confirmation and verified writes; no authority is mocked.

An initial six-row fixture palette caused safe confidence-based choice cascades (3/30 goals met). Its receipt is preserved under `artifacts/judge-exploration/baseline-six-fixtures/`; the authoring correction changed only per-case fixtures, never thresholds or expected behaviors. Corrected unchanged-code runs scored **14/30 then 15/30** solely because JE-15 depends on random ID ordering; this is not an improvement claim. The held fix also scored 15/30, with a separate deterministic before/after regression proving the status correction. Remaining context/policy weaknesses are open; no broader API refactor was applied.

Private run/aggregate receipts are under `artifacts/judge-exploration/{baseline,controls-report,final-base-report,final-fixed-report}/`, mode 0600 and read back. Final receipts hash the suite, runner, API, NLU and store sources. A minimal `asyncio.to_thread` check hangs under the restricted shell sandbox but exits normally outside it; the exact zero-spend suite ran outside that sandbox, with no runtime workaround.

**Live pending:** Wait for Sebastian's judge-access signal. Use one separate durable server scope capped at **$0.30**, check the production key/account balance privately before and after, retain unknown-cost reservations, and stop on budget denial. Do not retry the paid suite or substitute owner sessions for judge sessions. Bind only scoped masked transactions in memory; missing story bindings must be marked skipped. The current runner intentionally has no paid/live path; the authenticated live adapter will be prepared after the access signal. Judge-browser checks and real-model coherence remain unverified. All PRs stay unmerged until Sebastian lifts the release hold.
