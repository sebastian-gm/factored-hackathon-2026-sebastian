# Saved Azure latency probe: component attribution

Read-only analysis of the five completed conversations at runtime
`d23fa5afed2a799f8578a78ec323bf2b4864786f`. No provider call or paid replay.
The probe stopped at the first unknown cost; its purse stays disabled. We queried
only whitelisted execution metadata within its 54-second window, not request,
response, customer, transaction or model-output text. Ten primary execution records
match the saved ten turns in order; ten separate handoff-readback records were
excluded from the timing join.

| Conversation / first turn | BFF ms | Gemini attempt 1 ms | Gemini retry ms | Jev ms |
| --- | ---: | ---: | ---: | ---: |
| 1 / ES | 7941.01 | 4666.64 | — | 307.77 |
| 2 / PT | 5227.73 | 5038.31 | — | 223.05 |
| 3 / ES | 5670.18 | 5502.60 | — | 183.25 |
| 4 / PT | 2473.12 | 2313.52 | — | 154.48 |
| 5 / ES | 8394.98 | 6045.28 (provider_error) | 2100.06 | 231.53 |

The slowest turn explains the pooled **8190.69 ms p95**: its first Gemini attempt
failed at about the configured six-second deadline, followed by a successful
second attempt. The record says `provider_error`; deadline attribution is an
inference from timing, not a recorded exception class. No phrasing calls occurred.
Jev was at most 308 ms. Provider durations are not a complete disjoint wall-clock
profile: small overlap/timer differences produce up to 34 ms of negative residual.

The first conversation has about 2967 ms outside the recorded providers. Its
cause is uninstrumented: these records cannot distinguish replica startup,
matcher setup, connection setup or durable accounting. Other first-turn residuals
are small. Read/auth setup p95 was 86.10 ms; no forced cold restart occurred, so
this sample cannot establish a cold-start distribution or exclude one first-turn
initialization effect.

All five second turns are terminal replies (89–127 ms), with no provider calls.
Pooling those with the five active first turns yields the reported 1300.26 ms
p50; it does not represent a typical active model turn. Startup-excluded p95 is
7441.30 ms over eight turns. This is a small, partial, mixed-workload check, not
an SLO or independent evaluation result.

## Proposed next measurement

Use the already approved development comparison to test a shorter NLU prompt and
alternate provider, keeping accuracy, risk coverage and every failed attempt in
the comparison. Gemini's first attempt dominates the measured tail; skipping Jev
or optimizing phrasing would not address this sample. Do not shorten the timeout
without dev evidence: extra retries could increase cost and latency. Add duration-only
spans for initialization and budget/DB work in a future reviewed instrumentation
change if the first-turn residual remains material. No timing or product change
is implemented here.

Private metadata receipt: the probe directory's `component-latency.json` under
ignored `artifacts/azure/`; the original latency result and spend stay unchanged.
