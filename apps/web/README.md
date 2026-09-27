# Aclara frontend

ADR-0015: customer chat renders `offer_dispute / awaiting_dispute_decision` as an
explained charge plus explicit ES/PT recognition and dispute-request buttons.
Both buttons use the messages endpoint; a separate server proposal is required
before exact-hash action confirmation. Free text stays available. Cancellation
has its own neutral notice. Agent Desk shows the supplied primary reason first,
then every other reason, with actions and verified evidence kept distinct.

`tests/conversation-contract.spec.ts` supplies new authored UI response fixtures
for these additive fields while backend integration proceeds. It covers ES/PT
message-only actions, separate confirmation/cancellation, free text, mobile and
keyboard access, multi-reason ordering, missing primary values, invalid mixed
offer/write plans and live story-hint selection. It does not use held-out rows,
gold labels, provider calls or organizer records. See API-PROPOSAL.md for producer
dependencies; these browser tests do not establish deployed backend readiness.

Three ES/PT surfaces share one accessible workspace: customer chat, Agent Desk and
Ops. The customer connection uses the frozen OpenAPI through a same-origin Next.js
backend-for-frontend. The live connection includes trusted roles, Agent Desk and measured workspace Ops.
An opt-in fixture mode remains for isolated UI regression tests. There are no LLM calls in this application.

## Run and verify

From `apps/web/`, install with `pnpm install --frozen-lockfile`, then use
`WATCHPACK_POLLING=1000 pnpm dev --webpack --hostname 127.0.0.1 --port 3212`.
The browser-test command uses Webpack with `WATCHPACK_POLLING=1000` because the host exhausted native file watchers;
the production build also uses Next.js's supported Webpack mode because the
Turbopack CSS worker failed to bind its worker port in this environment.

Live mode is the default. Configure server-only `API_BASE_URL` to the private bank
API. The existing server-only `BROWSER_API_BASE_URL` is supported as a deployment
fallback. `WEB_APP_ORIGIN` is the exact external origin when behind a reverse proxy;
otherwise same-origin checks use the request protocol and Host header. `BANK_CLOCK`, if provided to the
web process, supplies the initial simulated date; authenticated `/me.bank_clock`
is authoritative. An absent clock is shown as unavailable.
No browser environment variable or credential is needed. Never put credentials in
`NEXT_PUBLIC_*` variables.

To exercise isolated UI fixtures locally, set `FRONTEND_DEMO_MODE=fixtures` and
supply a nonempty `FRONTEND_FIXTURE_PASSWORD` through the process environment or an
ignored local environment file. No default password is committed. All fixture
personas still require password and a six-digit OTP. Their aliases appear in the
picker. Agent and Ops logins authorize their own surfaces on the server. Use the
same browser when changing accounts to follow a customer's handoff into Agent Desk.
This mock is a UI contract demonstrator, not an implementation of bank policy.

`pnpm test:e2e` generates an ephemeral credential and starts its own fixture server
on port 3212. It never reads the worktree `.env`. Install Chromium first with
`pnpm exec playwright install chromium`. Screenshots and test outputs go to ignored
`artifacts/frontend/`; videos/traces are disabled to avoid recording credentials.
Only team-generated fixtures appear in these browser runs. `pnpm typecheck`,
`pnpm lint`, and `pnpm build` are the ordinary CI checks.

`pnpm test:e2e --live` additionally starts the existing Python B1 API against its
team-generated fixture ledger on port 8212, then verifies login, a pending-charge
explanation, duplicate-case status, confirmed dispute/read-back, and both card-freeze
confirmation and cancellation with fresh OTP through the proxy. It requires the
repository's dev Python environment. `pnpm test:e2e --staff` configures a separate local ops identity and enabled reset
to exercise live handoff claim/resolve, measured Ops/trace, and fresh-OTP reset.
The customer run also verifies refusal, session revocation and upstream logout.
All modes force mock/B1 behavior and use a
fresh process credential; neither loads the local provider key.

Eight fixture browser tests cover the three stories, cancellation, phone layouts,
ES-MX/CO/AR and PT-BR, keyboard/modal behavior, automated WCAG 2.1 AA checks, cookie
visibility, role/CSRF rejection, confirmation replay, cross-browser ownership and
OTP lockout/restart. Browser checks currently run locally; adding them to the shared
CI workflow is a lead-owned follow-up.

## Identity and writes

Pre-auth and access tokens are server-set HTTP-only, SameSite=Strict cookies. They
are Secure in production; localhost HTTP development is the documented exception.
Tokens are never returned to JavaScript or stored in browser storage. Mutations
require an exact same-origin Origin header and JSON body. The proxy allowlists
frozen routes, validates outgoing inputs and incoming plans, strips unknown response
fields, and returns generic errors rather than raw bank errors or validation input.
The server-side cookie lifetime is bounded; the upstream remains the authority for
expiry and ownership. Signing out revokes the upstream capability, verifies that `/me` rejects it, and
removes browser credentials. A failure is shown without claiming verified logout.

Confirm and Cancel submit the exact server proposal hash and boolean. There is no
client-created proposal, ordinal-based authorization, optimistic receipt, automatic
write retry or password shortcut. A case receipt requires the API's verified flag plus an additional same-session
read-back. Handoff receipts require the backend verified flag and an additional scoped GET; freeze success also
requires an independently read Frozen card and matching verified handoff outcome. Uncertain write results are shown
as unverified; the user is not invited to blindly repeat the write. Plan expiry is
measured against real time; transaction dates and demo SLA use the simulated clock.
The UI doesn't infer a product mask when the live response omits that field.

The fixture adapter additionally enforces challenge expiry/five attempts, session
expiry, role separation, proposal expiry/ownership, fresh OTP, cancellation and
idempotent replay. Each browser has an unguessable workspace cookie. Switching
roles preserves that workspace; reset affects only that workspace and invalidates
its customer sessions. In-memory fixture state expires after an hour and is not a
production persistence solution. There is no fallback from a live error to fixtures.

## Scope and evidence

The API gap proposal is in [API-PROPOSAL.md](API-PROPOSAL.md). The customer-safe
“why” drawer displays response records, fired rule IDs and read-back status, never
model thinking. Staff-only traces contain execution records and call metadata.
Live Ops shows current-workspace counts and observed model cost. SAR and unsafe
rates remain unmeasured because operational records have no gold labels. Missing
freshness thresholds are displayed as unknown. Fixture Ops alone shows an
explicitly illustrative `results.json`; it is not a held-out result. The lineage image is the existing aggregate dbt-manifest diagram
from `docs/data/dbt-lineage.svg`, copied unchanged for standalone web packaging;
it is labeled as a snapshot rather than live lineage.

The UI follows the installed Next.js version (16), preserving the existing app
rather than downgrading to the brief's earlier version. It uses Tailwind, local
shadcn-style Button/Dialog components over Radix, and next-intl. Reference docs:
[Next.js cookies](https://nextjs.org/docs/app/api-reference/functions/cookies),
[route handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route),
[next-intl configuration](https://next-intl.dev/docs/usage/configuration),
[shadcn Dialog](https://ui.shadcn.com/docs/components/radix/dialog),
[Tailwind Next.js setup](https://tailwindcss.com/docs/installation/framework-guides/nextjs),
and [Playwright web servers](https://playwright.dev/docs/test-webserver).

Customer API follow-up: the proxy accepts the shipped status/security plans and
validates owned products. Fraud offers now use the live fresh-OTP and freeze APIs,
with exact-hash confirmation/cancellation. A revoked session shows the refusal
without claiming a handoff read-back. No freeze is simulated in the UI fixture adapter.
Agent Desk and Ops now use the shipped typed endpoints. Trusted `/me.role` controls
the interface; the API enforces authorization and current-workspace scope. Claim
and resolve submit version/idempotency fields and independently read back the
result. Staff access does not provide a global customer queue.

Live reset defaults to disabled. It requires both `FRONTEND_ALLOW_DEMO_RESET=true`
in the web process and `ALLOW_DEMO_RESET=true` in the API, a trusted ops identity,
fresh OTP and exact-hash confirmation. The receipt is independently read back;
authentication and audit records are retained. Azure keeps customer role and reset
disabled. Do not enable either through browser input.

Before deployment, the lead must run `node scripts/check-api-hop.mjs` **inside the
web container** with its configured server-side API URL. It checks `/healthz` and
`/personas`, prints only pass/status metadata and exits nonzero on failure. A
local fixture test verifies this probe; the Azure web-to-API hop is still unverified.
Preserve owner-IP ingress and fix private connectivity through the lead's release
process; this change does not authorize broader ingress.

### Recording and call evidence

Open **Preparar grabación / Preparar gravação** above the conversation. In fixture
mode, sign in as the supplied Ops persona and choose **Restablecer demo y abrir ES**.
The existing reset clears this browser workspace and is read back before opening
the ES login. Use the ES, PT and fraud buttons in sequence; they preselect the
persona and prepare the opening message. Password/OTP, sending, transaction choice
and exact action confirmation remain explicit. **Abrir Agent Desk** prepares the
staff login to inspect the same fixture handoff. No browser storage retains secrets.

Ops shows each recorded provider/model/prompt, tokens, latency and precise USD cost,
plus a conversation subtotal and unknown-cost count. It displays risk union and
Grok fallback metadata when the staff API supplies the optional projection. Missing
metadata is labeled unavailable. Fixture screenshots remain illustrative.

Live recording retains the existing reset flags, OTP and workspace scope. Current
cloud reset is disabled, and live story shortcuts need trusted persona bindings.
See [the additive API proposal](API-PROPOSAL.md#handoff-11-recording-glass-box-additive-proposal-merge-freeze).
No frontend fallback fabricates those fields or widens access. PRs stay open during
the final-run merge freeze; no real model calls are needed to test these features.
