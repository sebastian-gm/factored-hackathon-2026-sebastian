# First-time receipt captures

Owner demo cases persist across reloads and logins. Before local receipt captures,
enable scoped reset on the isolated `make demo` stack:

```bash
make demo
umask 077
docker compose --env-file artifacts/demo/es/.env \
  -f docker-compose.yml -f docker-compose.demo.yml \
  -f apps/web/ci/demo-tour-reset.yml \
  up --build --detach --wait > artifacts/demo/es/tour-reset-setup.log 2>&1
node apps/web/scripts/judge-tour.mjs demo --grep 'six real BFF stories'
```

The tour requires localhost, demo mode, an authenticated owner Ops persona and
reset enabled. It verifies step-up, confirms the scoped reset, then independently
reads the reset receipt before starting a new conversation. Receipt captures must
show recognition, explicit denial, confirmation and a new verified `received`
case; an existing-case response fails the tour. Capture artifacts stay ignored.

Live runs never reset. A fresh judge password/OTP login creates a new visit;
switching profiles or reloading preserves the visit's cases. Healthy responses
must omit the basic-mode notice; only an explicit `degraded: true` shows it.

Re-running `make demo` restores its default disabled reset setting. This overlay
is for the local mock stack and is excluded from the deployment workflow.
