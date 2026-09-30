# Judge UX fixes — 2026-09-29

The judge quickstart makes the three demo stories available before and after
sign-in. Selecting a story prepares a draft using the existing trusted persona
binding; authentication, sending and action confirmation remain explicit.

The branch starts at `387d28d72ad1d9b45e618c5f7b79266759174358` on
`fix/freeze-origin-and-otp-renewal` (lead PR #68). The requested PR target is
`fix/post-v3-analysis`. This lane's commits change only `apps/web/`.

## Completed (verified)

| Audit priority              | Result                                                                                                                                                                                                                                                                                                                   | Browser coverage                                                                                                                       |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| 1. First-time clarity       | ES/PT quickstart explains the purpose and offers explain, choose and human-help stories. Missing live hints disable shortcuts; preparation errors preserve the current screen.                                                                                                                                           | Four locale/viewport onboarding checks; missing hints; failed logout; no automatic message posts.                                      |
| 2. Actions above the fold   | Compact login, OTP and chat. Code entry brings its form into view. Offers, transaction choices and verified receipts are brought into view without stealing input focus. Recording controls follow the workspace.                                                                                                        | Phone/desktop submit visibility; both offer decisions; all three phone choices; receipt heading visibility.                            |
| 3. Verification renewal     | The lead's wrong-code retry retains the pending dispute and challenge. Card verification now also clears a wrong code, explains the retry and retains its challenge.                                                                                                                                                     | Same challenge/hash before and after the explicit retry; no additional write on a wrong code.                                          |
| 4. Expiry and failed writes | Dismissing a proposal keeps it visibly pending. Expiry offers an explicit new review; dispute review creates a new conversation, card review requests fresh verification. Failed sends preserve drafts. Unknown write results offer status/help drafts. An ended session shows sign-in again, with a neutral status dot. | No expired hash submitted; new review only after a click; no write replay; recovery buttons prepare text only; ended-session recovery. |
| 5. Failed reads             | Queue and evidence failures have separate error states and safe read retries. A failed queue read shows an unknown count.                                                                                                                                                                                                | Error is distinct from successful empty state; no permanent loading state or mutation on read retry.                                   |
| 6. Desk trust cues          | Failed actions have warning icons and failure labels. Verified actions retain separate read-back markers. Primary reason precedes the other reasons.                                                                                                                                                                     | Icon, color/label and primary-reason order assertions.                                                                                 |
| 7. Startup consistency      | Warming and unavailable states use neutral connection cues. Failure stops the starting clock label and presents retry.                                                                                                                                                                                                   | ES/PT pending/error checks; no green readiness indicator.                                                                              |
| 8. Copy consistency         | Customer labels, banner, story choices, product types, rule families and handoff teams are localized. Unknown statuses have a localized fallback.                                                                                                                                                                        | ES/PT copy and absence of internal handles/rule IDs in the customer why drawer.                                                        |
| 9. Five-stage story         | Understand → Decide → Act → Verify → Escalate appears as a localized response guide, with one stage per assistant turn. It describes a phase; it does not fabricate execution or authorize a write.                                                                                                                      | Proposal, offer, choice, cancellation, verified receipt and handoff stage assertions, alongside message/confirmation boundaries.       |
| 10. Phone readability       | Larger fact text and action targets, wrapping navigation, compact choice cards, three-column Ops stages, a keyboard-scrollable risk table with its union beside the risk, and an enlarged-lineage link.                                                                                                                  | No page overflow; accessibility checks; sticky signal/union after horizontal scrolling; keyboard/modals; ES/PT at 390px.               |

`pnpm typecheck`, `pnpm lint`, `pnpm build` and
`FRONTEND_E2E_PRODUCTION=1 node scripts/e2e.mjs` pass. The complete fixture suite
has 63 checks, including 17 new UX checks. Existing live/staff test selectors were
updated to match the localized labels; those Python-backed runs remain a release
check for the lead.

The main-targeted PR #64 had its two budget-blocked workflows rerun after the cap
was confirmed unblocked. Its checks, Postgres, web and invariants jobs are green.
This stacked UX PR relies on local verification under the orchestrator's updated
CI rule; the eventual main merge still requires green remote CI.

## Before/after screenshots

Ignored local evidence:

- `artifacts/ux-audit/implementation-before/`: the exact lead-branch baseline.
- `artifacts/ux-audit/implementation-after/`: the final frontend UI.
- Each directory has `capture-index.json`, `index.html`, 21 contact sheets and
  328 PNGs: 41 states × ES/PT × desktop 1440×1000 / phone 390×844 × full/viewport.

The matrix covers login and code entry; explanation/why; dispute offer; transaction
choice; confirmation, dismissal and expiry; case receipt; handoff; refusal and
session end; cancellation; unknown writes; code renewal and incorrect-code retry;
Desk queue, multi-reason packet, evidence, failed action and read states; Ops,
risk degradation and read states; recording preparation and its error state.
Startup, loading, empty and error states are included. Native frontend fixtures
and new authored UI responses/HTTP faults supply the states. Password/code text is
masked. No organizer rows, frozen-suite rows, provider calls or backend evaluation
are involved. Automated WCAG 2.1 AA checks and visual review complement each other;
a clean automated scan is not a complete accessibility certification.

At 390×844, the initial login panel bottom moved from 959px to 839px in ES and
966px to 818px in PT. The empty-chat composer bottom moved from 1004px to 712px
in ES and 1011px to 698px in PT. The latter measurements include automatic
scrolling to the active form; final viewport captures retain that scroll position.
Tests separately assert that the login, code-entry and chat submit buttons are
fully within the viewport. All three review buttons also fit after a choice turn.
Both audit matrices have zero automated accessibility findings, page overflow and
browser exceptions. Model spend is $0.

Visual review retained the existing visual language and checked hierarchy,
localization, errors, focus, trust markers and phone layout across the contact
sheets. It also caught the clipped receipt heading and stale verified-session cue;
the final UI brings the latest receipt into view and changes ended-session cues.

## Customer terminology

Deliberate product names are **Aclara** and **Agent Desk**. SMS, UTC and ISO
currency codes remain standard notation. Proper merchant names stay as supplied
by the trusted response. Provider/model names and canonical execution/rule IDs
belong to staff evidence. The customer why drawer uses localized rule families;
transaction/product/proposal/handoff handles are not customer labels. An official
case reference remains available under its localized disclosure for follow-up.
Sign-in identifiers remain functional user inputs. Card ordinals identify the
choices currently displayed; they are not invented account masks.

## Done but not verified

Deployed live API behavior, serving-data story availability, real SMS delivery,
screen-reader usability and a manual production smoke test require the lead's
release gate. The UI does not infer those results from fixtures. The session note
is kept here to honor this assignment's `apps/web/` ownership boundary.

## Next / blocked

Leave the PR unmerged for lead review after PR #68. Preserve the final-run freeze.
Run the lead's live/staff checks and remote main CI before release. No backend,
NLU, policy, frozen interfaces or held-out suite changes are part of this lane's
commits.
