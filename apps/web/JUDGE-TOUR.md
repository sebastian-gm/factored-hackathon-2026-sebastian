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
No screenshots, traces, videos, DOM snapshots or request bodies go to CI artifacts.

Seven checks per project cover entry/keyboard/links, Insights, OTP/expiry/re-login,
six stories and their facts drawer, Desk claim, Ops, and resilience feedback.
The local basic-mode and 429 responses are explicitly simulated. Other local
journeys use the bank API and verified receipts. Existing fixture regressions
independently cover actual admission limits, judge profiles and staff isolation.

The local demo has one Ops persona. A separate browser signs in independently
with that same identity and joins through an API-created invitation. This proves
the queue/claim UI and read-back; it does not prove independent staff identities
or the customer invitation UI. The default demo has no judge picker. Missing
candidate or fresh-freeze paths are recorded as unverified, never silently counted
as tested. Browser-cookie expiry checks re-login, not elapsed server TTL.

## Live run after the lead opens access

The merge hold and access-open signal remain prerequisites. First use the
lead's deployed SHA, exact HTTPS web origin and private credentials. The owner
launcher accepts `JUDGE_TOUR_CREDENTIALS_FILE`, pointing to an ignored 0600 JSON
file under this checkout's `artifacts/`. Its keys are environment variable names:
`JUDGE_TOUR_URL`, `JUDGE_TOUR_RELEASE_SHA`, `JUDGE_TOUR_USERNAME`,
`JUDGE_TOUR_PASSWORD`, and optional `JUDGE_TOUR_STAFF_USERNAME` /
`JUDGE_TOUR_STAFF_PASSWORD`. Never pass secrets in command arguments.

```sh
node apps/web/scripts/judge-tour.mjs live
```

This defaults to zero messages/model turns. Paid story/queue checks are skipped
and named in the summary. Do not treat a green read-only run as a complete tour.
The lead owns the BFF correction accepting trusted Ops-backed judge profiles.
Selected MX/PT profiles must be checked after that correction is deployed.

For the paid journeys, the lead must first read back the account/key balances
and bind a dedicated durable frontend budget scope capped at **$0.20 total**,
including both networks. Reserve unknown costs, stop on exhaustion, and read back
balances and scope charges afterward. A turn count alone is not a dollar limit.
The launcher additionally requires `JUDGE_TOUR_PAID=1`, a
`JUDGE_TOUR_BUDGET_SCOPE` identifier and `JUDGE_TOUR_MAX_TURNS` (1–40), with
`JUDGE_TOUR_PAID_PROJECT` selecting one of the four projects. A private 0600
`.mjs` `JUDGE_TOUR_BUDGET_ADAPTER` under ignored `artifacts/` is mandatory;
a scope label alone cannot enable paid execution. The private durable
turn ledger counts message/confirmation attempts before execution and retains failures.
Its cap cannot be raised by a later run. Never reset it to retry paid checks.
Run each project sequentially inside the same scope; no automatic retries.

The lead-owned adapter exports `scope`, `capUsd=0.20`, async `reserve(request)`,
`settle(token, request)` and `halt(token)`. Requests contain method/path and an
access token only in memory; settlement also receives HTTP status. `reserve`
resolves the trusted customer/run/session scope, records an execution-ID baseline,
reserves a conservative request maximum through
`scripts.go_live_budget.lane_gate(store, "frontend")`, and returns
`{token, maximumUsd}`. `settle` independently reads the new scoped execution
records, uses `settle_calls`, reads the reservation back and returns
`{verified: true, costUsd}`. An authenticated Ops/Agent profile can read its own
BFF trace; terminated/customer sessions require the lead's scoped operator reader.
No browser-supplied costs or aggregate production deltas establish settlement.

Every potentially paid message and confirmation is intercepted before forwarding;
the browser receives the response only after settlement verifies. Unknown cost,
missing/ambiguous receipts or timeouts retain the reserve and stop the lane.
`halt` disables further use of that shared scope, preserving accounting history;
`reserve` must reject a scope with unresolved prior attempts. Adapter code and
its dollar bound need lead review. The current freeze/proposal/claim routes are
deterministic; recheck that fact against the exact deployed SHA before paid runs.

## Independent GitHub runner

[ci/judge-tour.yml](ci/judge-tour.yml) is ready for lead review and installation
as `.github/workflows/judge-tour.yml`. Workflow ownership stays with the lead.
It uses the repository web URL variable and separately configured private secrets,
runs the four live projects, and uploads no customer artifacts. The default
`paid_project=none` sends no messages. Dispatch only after Gate B. A paid
dispatch selects one project and an attempt cap, requires the private
`JUDGE_TOUR_BUDGET_SCOPE` and lead-reviewed `JUDGE_TOUR_BUDGET_ADAPTER_SOURCE`
secrets, and must use the same externally enforced
$0.20 scope as the owner runs. GitHub's ephemeral attempt ledger cannot enforce
a cap across dispatches; the lead's durable scope must do that.
The adapter source contains no embedded credentials; the lead supplies any
operator connection through the private `JUDGE_TOUR_OPERATOR_DSN` secret.
Paid dispatches install the existing Python operator dependencies; the adapter
must use that scoped connection and the same shared purse as the owner.
Owner and runner evidence must record network and exact deployed release SHA.

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
Repository source links need repository access while Gate C remains closed.
