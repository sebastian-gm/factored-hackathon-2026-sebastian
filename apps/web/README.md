# Aclara frontend

Three ES/PT surfaces share one accessible workspace: customer chat, Agent Desk and
Ops. The customer connection uses the frozen OpenAPI through a same-origin Next.js
backend-for-frontend. Missing staff/operations contracts use explicitly labeled,
opt-in, project-generated fixtures. There are no LLM calls in this application.

## Run and verify

From `apps/web/`, install with `pnpm install --frozen-lockfile`, then use
`pnpm dev --webpack --hostname 127.0.0.1 --port 3212`. The browser-test command uses
Webpack with `WATCHPACK_POLLING=1000` because the host exhausted native file watchers;
the production build also uses Next.js's supported Webpack mode because the
Turbopack CSS worker failed to bind its worker port in this environment.

Live mode is the default. Configure server-only `API_BASE_URL` to the private bank
API. The existing server-only `BROWSER_API_BASE_URL` is supported as a deployment
fallback. `WEB_APP_ORIGIN` is the exact external origin when behind a reverse proxy;
otherwise same-origin checks use the request protocol and Host header. `BANK_CLOCK`, if provided to the
web process, supplies the simulated date; an absent clock is shown as unavailable.
No browser environment variable or credential is needed. Never put credentials in
`NEXT_PUBLIC_*` variables.

To exercise the missing surfaces locally, set `FRONTEND_DEMO_MODE=fixtures` and
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
explanation and a confirmed dispute/read-back through the proxy. It requires the
repository's dev Python environment. Both modes force mock/B1 behavior and use a
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
expiry and ownership. Signing out removes browser credentials. The live API has no
revocation endpoint yet, so upstream session revocation remains a lead dependency.

Confirm and Cancel submit the exact server proposal hash and boolean. There is no
client-created proposal, ordinal-based authorization, optimistic receipt, automatic
write retry or password shortcut. A case/handoff receipt requires the API's verified
flag plus an additional same-session read-back. Uncertain write results are shown
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
The Ops `results.json` is explicitly illustrative, not a measured evaluation or a
held-out result. The lineage image is the existing aggregate dbt-manifest diagram
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
