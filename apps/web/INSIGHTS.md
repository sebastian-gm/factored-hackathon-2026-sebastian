# Insights: judge story and numerical provenance

Session: 2026-09-30. Scope: `apps/web/`, private repository, aggregate data,
local fixtures, no model calls or system evaluation. The review follow-ups in
PR #76 are merged into the target; this PR builds on `fix/post-v3-analysis`.
Do not merge during the freeze.

## Completed (verified)

- ES/PT `/insights`, fourth navigation item and quickstart entry; native charts
  and keyboard-operated decision stages without a chart dependency. The page
  remains available when the bank is starting or unavailable.
- Authenticated chat drafts, pending proposals and identity survive opening
  Insights and returning, including browser back/forward. Opening the aggregate
  route directly does not create a chat session. Browsing it never confirms an
  action, prepares a new story, signs out or makes a bank write.
- Small aggregate snapshot in `src/data/insights.json`, reproducible with
  `node scripts/build-insights-snapshot.mjs`. The exporter reads an explicit
  allowlist of committed source files; it exports only selected aggregate
  fields. Source path, last-changing commit and full-file SHA-256 accompany
  each source. `--check` verifies the snapshot without rewriting it.
  It recomputes the measurement fields from committed sources and preserves
  historical pins across unrelated document edits; full pin digests are also
  checked when their historical Git objects are available (local full history,
  versus a shallow CI checkout).
- In-page citations link to the source registry and then to the pinned private
  repository file. The copied dbt lineage SVG has the same SHA-256 as its
  committed source. Neither the export nor the page reads `lake/`, evaluation
  suites, private bindings, raw organizer records, credentials or providers.
- v1 disclosed as abandoned, without scores. v2 preserves the official loss;
  v3 preserves the original independent-run result and explicitly notes its
  later retirement into development data. Versions are separate workloads,
  not a causal before/after experiment. The full v3 safety gate failed despite
  zero observed unauthorized actions. Safety, repeats and partial judging stay
  explicitly labeled **v3** while switching the v2/v3 comparison.
- Matcher comparisons are reused synthetic diagnostics, not an independent
  blind evaluation or real-NLU accuracy. Known-target denominators and wrong
  proposal counts remain visible. The MLflow description belongs to the
  original v1 experiment; it does not invent an MLflow run for v2.
- Local production build, TypeScript, ESLint, complete fixture Playwright
  coverage and ES/PT desktop/phone screenshot checks are recorded below.

## Audit and validation

`pnpm lint`, `pnpm typecheck`, `NEXT_TELEMETRY_DISABLED=1 pnpm build`, and
`FRONTEND_E2E_PRODUCTION=1 node scripts/e2e.mjs` are the local checks. The fixture
runner supplies an ephemeral test credential and never logs it. It runs the web
only; no Python bank, B1, P, NLU, policy or real model is invoked.

The screenshot set is ignored under `artifacts/ux-audit/insights/`. It covers ES
and PT at 1440×1000 and 390×844: overview, v2 comparison, original matcher
diagnostic with the Act stage selected, expanded source metadata, expanded dbt
lineage, publication error and an **invented aggregate publication example**.
Each view has full-page and viewport captures. The example is presentation test
data, not a v4 result; production ships only `status: pending`.

The final set contains **28 views / 56 PNGs**. All capture checks passed with
zero Axe violations, zero horizontal overflows and zero page errors. The local
suite includes **13 new Insights checks** covering numerical provenance,
schema rejection, ES/PT publication states, keyboard stages, source/lineage
access, read-only navigation and retention of pending chat decisions.

Every capture checks WCAG A/AA with Axe, horizontal overflow and skip-link
position; desktop captures also check that the sidebar starts at the top and
fills the viewport. The audit caught and fixed a nested link in the lineage
disclosure and low contrast in timeline version labels. Existing tests confirm
the login, OTP, story and chat actions still fit the phone's first viewport.
An older live-story fixture test now waits for the configuration's three story
buttons before inspecting them and removing its intercept, fixing a loading
race that previously allowed an empty list to pass.

## Source registry

The snapshot, rather than copied prose or a hardcoded score, supplies each
number displayed by the page. Percentages and units are formatted in the
selected language. Statistical confidence is confidence in the sample estimate,
not a production guarantee.

| Source                                           | Use                                                                                                                                   |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/data/problem-analysis-aggregates.json`     | Queja contact volume/time shares and FCR; unrecognized-charge complaint count, SLA breach share and recorded calendar resolution time |
| `docs/problem-analysis.md`                       | Interpretation and missing-value limits of the synthetic workload                                                                     |
| `contracts/interfaces/conversation-policy-v3.md` | Decision loop, autonomy and confirmation/readback/handoff boundaries                                                                  |
| `docs/status/progress-log.md`                    | Abandoned first final attempt disclosure; no abandoned scores are exported                                                            |
| `docs/evaluation/final-v2-error-analysis.md`     | Official B1/P pass, SAR, paired interval, cost and latency headlines only                                                             |
| `docs/evaluation/final-v3-results.md`            | Original independent run, pass/SAR, interval, unauthorized-action denominator/bound, repeats, partial judges, cost and latency        |
| `docs/ml/model-card-charge-matcher-v2.md`        | Training/validation sizes, frozen fitting procedure, diagnostic limitations                                                           |
| `models/charge_matcher/v2/metrics.json`          | Allowlisted v1/v2 overall diagnostic counts and rates only                                                                            |
| `docs/ml/model-card-charge-matcher.md`           | Original experiment's local private MLflow tracking                                                                                   |
| `docs/data/pipeline-runbook.md`                  | Bronze/silver/gold, contracts, DQ/tests and atomic serving lineage                                                                    |
| `docs/data/dbt-lineage.svg`                      | Committed manifest graph snapshot; not live bank state                                                                                |

The displayed cost is per primary workload conversation and **model inference
only**; infrastructure, repeats and judges are excluded. Evaluation latency
includes the workstation-to-Azure-Postgres network path and predates subsequent
optimizations. It is not a deployed chat latency measurement. The FCR is the
source workload's rate, not an improvement produced by Aclara.

Deliberate product/tool vocabulary retained in ES/PT: **Insights, Agent Desk,
Aclara, Charge matcher, LightGBM, Gemini 3 Flash, MLflow, dbt, Bronze, Silver,
Gold**, comparison identifiers **B1/P**, and the canonical **Understand → Decide
→ Act → Verify → Escalate** labels beneath their translated stage names. Source
paths, hashes and commits belong to the explicit provenance disclosure.

## Done but not verified

- Production hosting and the eventual v4 publication are not exercised here.
- Remote CI for the stacked PR is not a requested gate under the owner policy:
  PRs into `fix/post-v3-analysis` use rigorous local checks. Remote CI remains
  required for the lead's eventual PR into main.

## Next / blocked

- Owner/lead review and merge approval after the freeze. Leave this PR unmerged.
- After the final run, its authorized publisher can replace
  `public/insights-results.json` with an aggregate publication. The Zod contract
  in `src/lib/insights-results.ts` accepts `partial` or `complete` with B1/P pass
  and SAR count/denominator pairs, paired SAR difference with CI, unauthorized
  action count/denominator, full safety-gate status, and a committed
  `docs/evaluation/` source path with commit and SHA-256. Unknown fields, missing
  denominators, out-of-range counts and invalid intervals fail closed into a
  retryable read error. No scenario, utterance, binding or gold row is accepted.
  A pending publication has no metric fields and is never rendered as zero.
