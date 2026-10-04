# Private judge tour harness — 2026-10-03

## Completed (verified)

- Prepared a separate external-stack Playwright configuration for ES/PT desktop
  and phone. Default live mode sends no messages; no automatic retries.
- Added durable pre-send attempt reservations that fail closed and cannot raise
  an existing cap. Four guard regressions pass. Dollar enforcement remains the
  lead's shared durable budget scope, not this attempt counter.
- Captures mask credentials and live customer facts. Reports retain static check
  names, counts and timings only; traces, videos and DOM/error bodies are disabled.
  Diagnostic CLI overrides are rejected; failed OTP captures are removed.
- Verified with the companion tour against this checkout's real make demo stack:
  28/28 mock checks, then eight affected story/Desk checks after stronger read-back
  assertions. No provider spend, cloud changes, organizer data or public artifacts.

## Done but not verified

- Exact-head remote CI pending. The separate companion PR adds the journey suite.
- Live judge picker, independent staff identities, candidate selection and both
  deployed networks remain unverified; the default demo cannot prove these.

## Next / blocked

- Keep all frontend PRs unmerged during the user release hold.
- Live runs wait for the user's access-open signal, deployed release SHA,
  private credentials and the lead's dedicated $0.20 frontend scope.
