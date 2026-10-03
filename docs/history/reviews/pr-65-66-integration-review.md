# PRs #65/#66 and combined preview review

Reviewed 2026-09-29 PDT. Local integration candidate:
`2b41886aa98667129540215d51959832c83c8ac2`, on `fix/post-v3-analysis`.
Main and origin/main remain `e12efc73be64f8355aa9f177f08a04337593616c`.
No v4 inputs were opened, no v4 execution occurred, and no paid model call was made.

## Commit dispositions

| PR | Commit | Review |
| --- | --- | --- |
| #65 | `31826c6` | Authored 40-case dev freeze and deterministic materializer. No organizer records; immutable source, builder and materialized hashes verified by structural tests. |
| #65 | `2753ac1` | Study command requires approval and a clean tree; refuses overwriting a stage. Reservations lock the shared scope and commit before requests; retained unknown-cost reserves count toward the $0.90 stop. Accounting failures abort instead of silently becoming model fallback. No paid execution during review. |
| #65 | `5bf198d` | Complete, bounded ES/PT spoken-number parsing replaces partial small-word extraction. Unsupported composites remain unresolved. Calendar parsing preserves bank-day conventions, rejects impossible dates and future dates without a year. Currency and matcher thresholds unchanged. |
| #65 | `3bba2f5`, `09f0e3c` | Reports accurately distinguish unchanged 39/40 dev outcomes from fewer normalization failures; p95 did not improve. Remaining guard failure assigned to lead; billing failures disclosed. |
| #65 | `5ec47ce` | Parent update preserves additive progress entries. No extra product behavior. |
| #66 | `61f8d90` | Code-approved clarification questions stay exact; actual approved explanation reaches phrasing. DLP, fact citations and grounding remain in place. Domain/merchant exclusion applies to language evidence, not action authority. Insufficient evidence stays uncertain; only confident opposite-language drafts are rejected. |
| #66 | `5de60a0`, `b059920` | Documentation and parent update; progress entries retained. No hidden prompt, policy or interface change. |

No new blocking defect was confirmed in the AI changes. The language heuristic
is conservative rather than a calibrated classifier: uncertain drafts can pass
the language check, and these authored tests do not establish human fluency.
The study is development evidence, not independent accuracy or a causal latency
comparison. Neither limitation is upgraded into a production claim here.

## Confirmed lead-owned offer gap

The #65 failure `robust.co.cancels-after-offer` is genuine. A valid unfamiliarity
flag and confident match were overridden by `selection.uncertain()` for a
statement about remembering a charge's origin. Zero-cost ES/PT reproductions
confirmed that guard before the change; it is not an NLU or gold defect.

Commit `02d6bcc` narrowly extends the existing unfamiliarity exception: an origin
verb must refer to a charge noun. It removes only that phrase from the selection
uncertainty scan; a following inability to choose or recall the amount remains
effective. No matcher threshold or dev fixture was changed.

The new authored regressions produced **10 failures / 10 passes before** and
**20/20 passes after**. They include B1 and mock P offer → filing request →
cancel flows with no write, ES/PT origin forms, unrelated amount memory, and
separate transaction-selection uncertainty. The reported frozen *dev* case also
passes a bound replay with authored mock extraction: cancellation, required
offer present, no missing actions, no forbidden action or unsafe predicate.
This is not a new real-model result or a v4 measurement.

## Integration and conflicts

- #63 was already merged at `dac3801` before this session.
- Reviewed #65 merged into the private feature base at `b9dabfb`; #66 at `6800ffd`,
  under the preceding authorization while Actions was blocked.
- Updating #66 for #65 produced **one progress-log conflict only**. Both complete
  entries were kept in a history-preserving merge (`7308648`); no force push.
- #67, then dependent #68, then the charge-origin correction are integrated
  **locally** on `fix/post-v3-analysis`. No product conflict or local regression
  appeared. Their GitHub PRs remain open until the combined update is published.
- After the owner restored a $5 Actions budget, the latest #67/#62 runs were
  rerun once each for CI and safety. Attempt 2 still started zero steps: the fresh
  annotation says an Actions budget prevents use. No further reruns or pushes
  were made after the orchestrator's hold.
- Per Sebastian's subsequent minute-saving decision, `2b41886` restricts
  `pull_request` CI/safety to base `main`, retains main pushes, and cancels
  superseded runs by workflow/ref. Parsed YAML assertions verify both filters
  and concurrency settings. Stacked PRs use documented local gates; #62 still
  requires green remote checks before a main merge. The $5 spending cap is an
  account billing setting; workflow filters do not enforce that cap themselves.

Sebastian subsequently confirmed billing is unblocked and required a **single
combined-head remote run**, after PRs #69/#70 and the pending frontend UX PR.
Stacked PRs now rely on rigorous local checks; only main-target merges require
remote green. Publication is held for the UX PR, avoiding an intermediate #62
run. Main merge remains unauthorized in this session.

## Added review: #69 and #70

Reviewed #69 commits `442ef60`, `3c86e27` and parent reconciliation `a570f96`.
Prompt pins match all four source hashes; official v3 counts and language slices
match the saved aggregates. The paid review itself was not rerun. Accepted the
six copy changes in `ea34060`: five PT occurrences consistently say
`contestação`, and one ES freeze offer describes a new verification code plus
separate confirmation. The workflow patch's context was stale after #68;
mechanically updating that hunk preserved the exact approved replacement.
AST comparison confirmed six string-only changes, four distinct replacements,
unchanged placeholders/numbers and identical non-string structure.

**Documentation finding corrected:** the 134-item inventory predates #68's
`otpRetry` translations. The review log now pins its coverage to the reviewed
source snapshot and does not imply model validation of later OTP/UX copy. No
new paid call was made to expand it. The model card's conservative language and
human-review limitations remain explicit.

Reviewed #70 commits `5506fd8`, `6dd2333`, `8026df7`: projection/README followed
by billing-policy handoffs. Read only official v3 aggregate objects, committed
pipeline aggregates and v2 report figures. Independently recomputed:

- Pass **52/100 vs 77/100**, SAR **28% vs 39%**, strict escalation **20/40 vs
  30/40**, unnecessary transfers **23/60 vs 11/60**, paired **+11 pp, 95% CI
  +5 to +17**, per-case P cost **$0.00237687544** and all cited case/turn timing.
- FCR **43.6%**, complaint mix **12,297/67,095 = 18.33%**, category handle means
  **434.6059149979648 s / 220.8028237231492 s**, wait and contact denominators.
- Every low/base/high projection output using Decimal arithmetic. Base savings
  **11,621 minutes**, low **−3,028**, high **22,815**; base costs **$58.77**.
  Transactional-time sensitivity **4,440 minutes**.

Numbers agree. Traffic volume/mix, assisted handling, review/remediation and
infrastructure allocations are explicitly assumptions. The projection compares
P with B1, not an all-manual bank, and avoids double-counting transfers. Full
safety failures, partial judging and seen-v3 limitations remain visible. The
historical cloud estimate matches its dated plan and is not a current quote.
README bootstrap commands were checked against source; no new organizer load
or fresh-install execution is claimed. Local evidence links resolve.

Both PRs are integrated locally. #70 added a second **progress-log-only conflict**;
all entries were preserved. No product conflict. A local gate accidentally
started during that unresolved index stopped at the staged-file scanner;
verification was restarted only after the history-preserving merge completed.
The completed gate through #70 at `95332e0e7d8a500ac5f1b400b908d21978e66168`
passed **417 tests / 16 DB skips**, all hooks, B1 **32/32** with 12 readbacks,
and interface/catalog checks. Its only product difference from the preceding
full browser/Postgres-tested candidate is the six AST-verified copy changes.

## Executed local gates

| Command | Observed result |
| --- | --- |
| `UV_CACHE_DIR=$PWD/artifacts/uv-cache make checks` | Six hooks, file policy, compilation, **417 passed / 16 DB skips**, B1 **32/32**, **12 readbacks**, interface and policy snapshots current. Repeated successfully on committed integration `2b41886`. |
| `.venv/bin/ruff check .` | Passed. |
| `.venv/bin/mypy --strict src/aclara` | Passed, 84 source files. |
| `.venv/bin/python -m evals.runner --system B1 --scenarios evals/dev_scenarios_v2.yaml` | **32/32** reactive cases. |
| `.venv/bin/python -m scripts.test_postgres` | **19/19**: disposable local Postgres, migrations/RLS/restart and serving load. |
| `pnpm typecheck`, `pnpm lint`, `pnpm build` in `apps/web` | All passed, sequentially. |
| `pnpm test:e2e`, then `pnpm test:e2e --live`, then `pnpm test:e2e --staff` | **46 + 12 + 1 = 59** browser checks passed. |

Postgres/browser checks ran against the combined product tree before the
documentation and CI-only commits; their product-tree diff is empty. Generated
`next-env.d.ts` and B1 aggregate documentation were restored after verification.
Ignored receipts are under `artifacts/startup-profile/`; no row output is committed.

Remote CI on the final integration, publication of the local merges, and an
Azure release of that candidate remain unverified. The deployed preview is still
`dac3801`; [startup profiling](../evaluation/preview-startup-profile.md) made no
Azure changes. Main merge and v4 remain on hold.
