# PR #72 review follow-ups — 2026-09-29

This frontend-only follow-up starts at PR #72's head
`d4979e5d2baee3fb6f317b28735126656672baba` and targets
`feat/judge-ux-polish`. It changes presentation and project-authored web fixtures.

## Completed (verified)

| Review item          | Result                                                                                                                                                                                                                                                                                                                                                                                                            |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sidebar / skip link  | The skip link is an absolute, focus-only overlay. Enter moves focus to the main content without shifting the sidebar. The fixed desktop sidebar stays at viewport top; its dark rail continues through long pages. Phone navigation retains its responsive header layout.                                                                                                                                         |
| Handoff reasons      | ES/PT human labels appear in the queue and packet. The primary reason is first and shares one outlined card with its “Motivo principal” label. Canonical codes remain secondary. Unrecognized codes receive a localized fallback with their exact code preserved. Labels follow brief §9 and conversation-policy-v3 §3; they do not supply routing or authority.                                                  |
| Action evidence      | Actions have localized labels and “Verificado en registros / Verificado nos registros” markers only when their recorded status is verified. Failed actions use attempt wording and warning cues. Canonical action names and evidence references are available in a technical disclosure.                                                                                                                          |
| Recording visibility | The helper is absent by default, including server-rendered HTML. `?grabar=1` enables visibility; `?grabar=0` does not. The flag grants no permissions: existing role, OTP, confirmation and read-back checks still apply. Ordinary judge story shortcuts remain available.                                                                                                                                        |
| Country currencies   | Mexico fixtures use USD, Colombia COP and Argentina ARS. The legacy `demo.pt.br` alias represents a Portuguese speaker in Mexico and uses USD. No fixture uses BRL or MXN. Persona labels and opening prompts no longer imply Brazilian bank data or reais. The language selector identifies Brazilian Portuguese as a language. Currency follows the authored persona country, independently of ES/PT rendering. |

`pnpm typecheck`, `pnpm lint`, `pnpm build` and
`FRONTEND_E2E_PRODUCTION=1 node scripts/e2e.mjs` pass. The complete fixture suite
has **78 checks**, including **15 new checks** for keyboard focus, layout, Desk
labels/evidence, recording opt-in and country currencies. CO and AR charge choices
retain their currency in both languages and after changing the language selector.
Existing recording tests opt in explicitly. Live recording test URLs were also
updated; their backend-backed execution remains the lead's release check.

## Recaptured audit

The corrected evidence is local and ignored under
`artifacts/ux-audit/review-followups/`: `index.html`, `capture-index.json`,
`verification-summary.json`, 21 contact sheets and **336 screenshot PNGs**.
The matrix has **42 states × ES/PT × 1440×1000 / 390×844 = 168 views**, each
with a full-page and viewport image. It retains all 41 states from the previous
audit and adds the focused skip link. Recording captures explicitly opt in;
every other capture asserts that the helper is absent. Password and OTP text
are masked. The parent audit remains under `implementation-after/` for comparison.

All 168 views have zero automated WCAG 2.1 AA findings, horizontal overflow and
browser exceptions. Sidebar bounds and skip-link positioning/clipping are asserted
at capture time, before the full-page image and after restoring the active scroll.
For every desktop state, the sidebar has `x=0`, `y=0` and viewport height. A pixel
check of the entire left edge of all **168 desktop images** found a continuous
dark rail; legitimate modal dimming is allowed. Visual review covered all 21
contact sheets and the reported desktop offer/packet surfaces.

The original full-page screenshots translated fixed elements by the current
scroll position, exposing the negative-top skip link and moving the rail down in
the image. The new capture tool starts full-page images at document origin and
restores automatic scrolling for the separate viewport image. The skip link now
uses focus clipping instead of a negative top offset, and the rail background
covers the document height. Browser tests separately verify real layout while
scrolling, so screenshot framing cannot stand in for that check.

These are authored UI states and HTTP faults. No organizer data, held-out rows,
backend evaluation or provider calls were used. Model spend is **$0**.

## Done but not verified

Deployed live behavior, the Python-backed live/staff checks and manual assistive
technology testing remain release checks for the lead. Automated accessibility
checks and fixture images do not establish those results.

## Next / blocked

Leave this stacked PR unmerged for review after #72. Under the orchestrator's
current CI policy, stacked PRs use rigorous local checks; a merge into main still
requires green remote CI. This session note stays in `apps/web/` to respect the
assignment's ownership boundary.
