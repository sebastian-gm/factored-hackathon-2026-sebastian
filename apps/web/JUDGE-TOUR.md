# Judge browser tour

Handoff 19, items 8–9. ES/PT, desktop 1440×1000 and phone 390×844.
This is development evidence measured after the final evaluation; v4 is unchanged.

## Local preparation

From the repository root:

```sh
make demo
node apps/web/scripts/judge-tour.mjs demo
node apps/web/scripts/lighthouse-tour.mjs demo
node apps/web/scripts/tour-gallery.mjs
```

Install the existing web dependencies and Chromium first (`pnpm install
--frozen-lockfile`, then `pnpm exec playwright install chromium` from `apps/web`).
The launcher reads this checkout's ignored 0600 demo configuration without
printing the password. It uses the real web BFF, mock bank API and Postgres.
It starts no UI fixture server and loads no organizer data or provider key.

Private gallery: `artifacts/ux-audit/go-live/index.html`. Full-page and viewport
PNGs are under `demo/{es,pt}-{desktop,phone}/`, with per-screen axe/overflow counts,
first/warm visit timings, console/request counts and a test summary. Credentials
are masked. Live captures also mask customer statements, facts and references.
Screenshots and operator files stay private on the owner network. No traces,
videos, DOM snapshots, request bodies or customer facts go to CI artifacts.

Nine checks per project cover entry/keyboard/links, Insights, OTP/expiry/re-login,
six stories and their facts drawer, the judge invitation, local Desk claim, Ops,
and local/live simulated resilience feedback.
The local basic-mode and 429 responses are explicitly simulated. Other local
journeys use the bank API and verified receipts. Existing fixture regressions
independently cover actual admission limits, judge profiles and staff isolation.

The local demo has one Ops persona. A separate browser signs in independently
with that same identity and joins through an API-created invitation. This proves
the queue/claim UI and read-back; it does not prove independent staff identities
or the customer invitation UI. The default demo has no judge picker. Missing
candidate or fresh-freeze paths are recorded as unverified, never silently counted
as tested. Browser-cookie expiry checks re-login, not elapsed server TTL.

## Authorized live run

Use the lead's deployed SHA, exact HTTPS origin and fresh judge visits only.
The launcher accepts `JUDGE_TOUR_CREDENTIALS_FILE`, an ignored 0600 JSON file
under this checkout's `artifacts/`, with `username`, `password`, `url` and optional
`otp`. The legacy environment-variable keys remain supported. Set the full
`JUDGE_TOUR_RELEASE_SHA` separately. Never put credentials in command arguments.

```sh
node apps/web/scripts/judge-tour.mjs live
```

This defaults to zero model turns. Paid stories are skipped and named in the
summary; a green read-only pass does not establish complete coverage. Live
screens are saved under `live/{owner-workstation,github-runner}/{project}/`.
`JUDGE_TOUR_SUMMARY_NAME` preserves each phase/project summary separately.
`node apps/web/scripts/tour-gallery.mjs live` builds the standalone live index at
`artifacts/ux-audit/go-live/live/index.html`.

After the lead's own-visit staff change is deployed, Agent Desk offers
**Abrir la cola de esta visita / Abrir a fila desta visita**. Generate and redeem
the one-use invitation in the existing judge session, then inspect and claim the
masked packet with independent read-back. No separate staff login is needed.
Reloading or changing a profile recovers membership; logout revokes it. The
[staff access guide](../../docs/submission/judge-staff-access.md) describes this
path. The v0.9.1 gallery records the earlier deployed invitation-only behavior.

The authorized tour uses the durable **$0.20 total** purse,
`go-live/2026-10-03/frontend`, run ID `2026-10-03`. Check production key/account
balances privately before and after. Reserve conservative costs before HTTP,
settle only independently read executions in the captured judge scope, retain
unknown reserves, and stop on any denial. Never refill the purse or retry a paid
suite. Production balance changes can include other lanes and cannot establish
this tour's cost.

Paid stories require `JUDGE_TOUR_PAID=1`, `JUDGE_TOUR_PAID_PROJECT`, a finite
`JUDGE_TOUR_MAX_TURNS` (1–112), the fixed scope and a private 0600 `.mjs`
`JUDGE_TOUR_BUDGET_ADAPTER` under ignored `artifacts/`. The durable attempt ledger
cannot raise an earlier cap. Retries are disabled and a failed paid check stops
the remaining suite. `JUDGE_TOUR_RESERVE_ALL_HTTP=1` also reserves deterministic
reads, authentication and assets without counting them as model-turn attempts.

The private adapter exports `scope`, `capUsd=0.20`, async `reserve(request)`,
`settle(token, request)` and `halt(token)`. Cookies and chat drafts stay in memory.
`reserve` validates the selected judge capability, captures its trusted
customer/run/session scope and execution-ID baseline, and reserves a conservative
maximum through the durable lane gate. `settle` independently reads only new
executions in that captured scope and verifies cost with `settle_calls`. The
browser receives a response only after its receipt verifies. Missing receipts,
timeouts and unknown cost stop the lane with reservations preserved.

The judge-side Agent Desk invitation was captured independently without a model
turn on v0.9.1. Its deployed redemption required a preauthenticated non-judge
staff session. The lead's [own-visit fix #178](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/178)
is merged; its deployment/live claim verification is separate and remains pending
in this gallery. Never substitute owner/Ops credentials or count a local claim as
live evidence.

## Independent network evidence

The owner chose to keep judge credentials and application connection data on the
owner network. Never send the application DSN to GitHub. This lane runs the
browser matrix only from the owner network; it does not claim an independent
runner browser/gallery matrix.

Cite the lead's [independent-network judge access run 37193884747](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs/37193884747)
for judge authentication, logout/replay denial and temporary-secret cleanup.
That access check is separate from this lane's ES/PT desktop/phone browser tour.
No temporary Actions secrets or remote gallery artifacts were created by this lane.

## Interpreting evidence

First/warm timings measure time to the usable login screen, including bootstrap.
They do not force a cloud restart or establish cold-start latency. Capture an
observed cold visit separately if the lead can establish the app was cold.
Lighthouse audits unauthenticated `/insights` on desktop and mobile and saves
only score/metric aggregates; no authentication or model calls occur. The local
demo uses a development server, so its performance score is not production
evidence. [Lighthouse CLI reference](https://github.com/GoogleChrome/lighthouse/blob/main/readme.md).
Signed-out `/me` 401s and intentionally tested 403/429s are expected network
console messages. Application exceptions are checked separately; raw strings
and bodies are discarded. Internal anchors and images are checked locally.
The repository is public with owner approval; merges remain held for lead review.
