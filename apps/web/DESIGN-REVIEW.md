# Minimal evidence design

The Chat, Agent Desk, Ops and Insights views now use a single forest accent,
neutral surfaces, an 8-pixel spacing rhythm, and three type sizes: 24px headings
and metrics, 16px body text, and 14px labels. Whitespace separates information;
borders mark inputs, decisions and section boundaries. Decorative navigation,
packet and transaction icons are removed. Verification and failure cues keep
their explicit labels and meaningful icons.

On phones, duplicate headings remain available to screen readers while the
visible layout gives space to the story shortcuts and primary actions. Short
desktop windows scroll the sidebar internally. Login, confirmation, OTP retry,
expiry, write authorization and identity behavior are unchanged. Judge-login
features remain a separate task.

Deliberate product/technical names: **Agent Desk**, **Insights**, **Aclara**,
**Gemini**, **LightGBM**, **MLflow**, **dbt**, **Bronze / Silver / Gold**, and
the bilingual Understand → Decide → Act → Verify → Escalate labels in Insights.
“Mi chat / Meu chat” uses the common localized term. Technical reference IDs
remain secondary in staff views and are not introduced in customer copy.

## Charts and provenance

Lightweight SVG marks have zero origins, shared percent scales, sorted bars,
direct labels, denominators and units. ES/PT and historical B1/P comparisons
use small multiples. Confidence intervals use a thin range and a point with a
textual interval; nothing depends on hover, a legend or color alone. Labels
remain real HTML text. This follows the W3C guidance on
[graphical contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
and [text equivalents for complex images](https://www.w3.org/WAI/tutorials/images/complex/).

The exporter reads only committed aggregate documents. It exports the final
v4 figures from [final-v4-results.md](../../docs/evaluation/final-v4-results.md)
to the web snapshot and publication JSON, then verifies values and source pins
with `node scripts/build-insights-snapshot.mjs --check`. Historical v2/v3
results remain visible and are labeled as different suites, not a causal
improvement experiment. Both official v4 safety gates failed; post-v4 repairs
are explicitly outside those numbers. Local v4 and partial Azure latency are
separate measurements.

Ops charts aggregate the recorded trace only. Duplicate event references are
counted once. Bars exclude unknown costs and label known/total calls; an
all-unknown trace says “cost not recorded”. Authored fixture cost examples
remain labeled as examples. No new backend field or endpoint is required.

## Private screenshot review

The ignored local gallery is
`artifacts/ux-audit/minimal-design/index.html` at the repository root. It pairs
ES/PT desktop (1440px) and phone (390px) before/after views of Chat, Desk, Ops,
Insights and the evidence section. Full-page images include every packet and
chart section; additional after images cover language panels and partial
Ops cost traces. Directories are mode 0700 and screenshots/gallery mode 0600.
Only authored UI fixtures and committed aggregates appear; credential and OTP
fields are masked. No screenshot, held-out row, organizer value or secret goes
into Git or a CI upload.

Reproduce captures with `FRONTEND_DESIGN_CAPTURE_PHASE=after pnpm test:e2e
minimal-design.spec.ts`. The capture flag is optional; CI runs the assertions
without those screenshots. Checks cover every surface's three-size scale,
layout, zero bar origins, sorted values, aggregate denominators, unknown-cost
handling and all-rule axe accessibility. Existing tests cover focus, keyboard
navigation, authority boundaries and recovery states.

## Session verification

- Completed (verified): aggregate export, typecheck, lint, production build,
  118 fixture browser tests, 12 local mock-API customer tests and one staff test.
  The final phone adjustment passed 25 additional capture/recovery checks.
  ES/PT desktop and phone captures passed all-rule axe with zero violations;
  before/after screenshots are in the private gallery. Model spend was $0.
- Done but not verified: deployment; remote CI is required on the PR before
  merge and its check status is the authoritative receipt.
- Next / blocked: open a PR to main and leave deployment to the lead. No backend,
  NLU, policy, frozen suite or judge-login changes are part of this pass.
