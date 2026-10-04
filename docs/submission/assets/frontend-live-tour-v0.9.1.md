# Live frontend tour — v0.9.1

Post-v4 development evidence, October 4, 2026. The official v4 evaluation is
unchanged. Target: `0f0e12df13e281538d7b25800f56c55da0b8dc0b` (`v0.9.1`).
Fresh judge visits only; no owner or separate staff credentials were used.

The private live gallery is `artifacts/ux-audit/go-live/live/index.html`.
It contains **166 masked PNGs / 83 screen audits**, grouped under
`live/owner-workstation/{es,pt}-{desktop,phone}/`. Screenshots, raw responses,
credentials, customer facts and operator files are excluded from Git and CI.
Only aggregate evidence is published here.

## Verified coverage

| Surface / action | ES desktop | ES phone | PT desktop | PT phone |
| --- | --- | --- | --- | --- |
| Landing, keyboard/links, Insights and lineage | Verified | Verified | Verified | Verified |
| Password/OTP, judge picker, profile selection | Verified | Verified | Verified | Verified |
| Cookie expiry, fresh login, role access | Verified | Verified | Verified | Verified |
| Judge-side staff invitation | Verified | Verified | Verified | Verified |
| Handoff, fresh freeze OTP, freeze/read-back | Verified | Verified | Verified | Verified |
| Explicit human request and injection refusal/no write | Verified | Verified | Verified | Verified |
| Healthy replies omit basic-mode notice | Verified | Verified | Verified | Verified |
| Browser-simulated 429 feedback | Simulated | Simulated | Simulated | Simulated |
| Charge explanation, candidate selection, first case receipt | Unverified | Unverified | Unverified | Unverified |
| Delegated staff redemption / queue claim | Unverified | Unverified | Unverified | Unverified |

All captured screens have **zero axe violations and horizontal overflow**.
There were **zero application console errors and page exceptions** in the
browser tour. Expected authentication/step-up and simulated 429 network errors
are counted separately from application exceptions.

Visual review found no new defect in the captured picker, quick-start, invitation,
handoff or freeze screens. Cross-language disabled shortcuts are absent, and
healthy replies do not show the basic-mode notice. The transaction/case status
surfaces were not reached live; their existing mock regressions are separate proof.

## Findings and limits

- Precise merchant/amount/currency/date narratives returned clarification in
  the charge journeys; one PT explanation routed to human review. No first-time
  case receipt or candidate selection was obtained. Private preflight confirmed
  the selected charge was policy eligible and its amount was represented exactly.
  This requires AI/lead investigation; these outcomes do not prove all charge
  narratives fail. No classification success is inferred from a green UI check.
- The first ES-desktop story stopped on its explanation expectation after one
  known-cost response. The remaining five stories ran once in a fresh visit,
  explicitly skipping that explanation. No paid suite or original turn was replayed.
- Invitation creation is verified. The deployed redemption endpoint requires an
  existing non-judge staff sign-in; the requested delegated judge-session path
  was subsequently addressed by the lead's merged #178; deployment/live verification is pending. No owner credentials were substituted.
- Cookie removal tests expiry/re-login, not elapsed server TTL. The live 429 was
  fulfilled in the browser without upstream/model traffic, not provider stress.
- Guarded first/warm login readiness was **6.234–6.396s / 2.509–2.570s**. These
  measurements include private reservation/settlement overhead and do not isolate
  application latency. No cloud cold restart was forced.
- Lighthouse stopped when its HTTPS mediation could not be verified. Desktop
  scores, mobile Lighthouse and SEO remain unverified. Local HTTP calibration
  does not establish live HTTPS coverage; no weaker audit fallback ran.

## Cost and independent access

The fixed purse is `go-live/2026-10-03/frontend`, run ID `2026-10-03`, cap
**$0.20**. Every tour HTTP call was reserved before forwarding. The tour made
**12 model calls** and **1,191 HTTP reservations**. Known cost is **$0.02341700**;
eight failed static GET receipts retain **$0.00000008**, so charged exposure is
**$0.02341708**. The database read-back independently matches the private journal.
The operator halted; no further paid requests were made, and no purse was reset
or replenished. The database limit remains unchanged.

Production key/account balances were checked privately before and after and
remained healthy. Changes from concurrent lanes are not attributed to this tour.
No credentials or application DSN were sent to GitHub by this lane.

The owner's separate independent-network evidence is the lead's successful
[judge-access run 37193884747](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs/37193884747),
on the same deployed SHA. It covers judge authentication, logout/replay denial
and temporary-secret cleanup; it is not an independent browser/gallery matrix.
