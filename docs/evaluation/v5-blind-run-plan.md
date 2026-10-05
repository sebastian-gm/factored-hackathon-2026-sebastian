# V5 blind evaluation — preparation only

Owner authorization: handoff 21, October 5, 2026. **Do not execute the run
sequence until the owner says “v5 suite merged”.** No v5 scenarios, families,
selections, bindings or authoring tool were opened during preparation. No v5
preflight or behavioral run has occurred. Official v4 remains the headline;
slides, video, deployment and the v1.0.0 tag remain unchanged.

## Exact v4 sequence and the v5 adaptation

The official v4 commands are preserved in
[the launch checklist](../history/evaluation/v4-launch-checklist.md#exact-local-serving-launch-commands).
With its `v4()` function setting the local serving DSN and pinned suite/bindings,
the actual sequence was:

```bash
FINAL_BUDGET_PREPARATION_APPROVED=1 .venv/bin/python -m scripts.final_budget \
  --prepare --suite test-v4 \
  --bindings artifacts/evaluation-v4/customer-bindings.json \
  --manifest-pin 309c3aa22c2eab51b3289075b733c52bb7934a879299762c3fb9ba16a3d9bec8
v4 prepare
.venv/bin/python -m scripts.openrouter_preflight
LLM_FINAL_RUN_STARTED=1 LLM_REAL_CALLS_APPROVED=1 v4 start
v4 status
```

That launcher detached its worker. `evals.final_program.execute` bound each
scenario with `evals.bindings.bind` and called `evals.bound_execution.execute_bound`.
The latter calls `evals.metrics.score`; `evals.final_report.write_report` uses
`evals.heldout_report.report` for strict gates and `comparison` for the paired
interval. There is no separate paid scoring call. V4 also ran repeats and dual
judges; **neither is authorized for v5**. The old final-program CLI accepts only
v3/v4, and its repeat comparison cannot handle an empty repeat subset.

The evaluation-only `scripts.v5_blind_evaluation` wrapper therefore uses the
same loader, binding, simulator, execution, scorer, strict report and private
checkpoint/journal primitives, with exactly B1 100 + P 100 and no repeats/judges.
Its paired SAR calculation copies v4's primary single-run calculation:
10,000 paired case bootstrap draws, seed 20261001, in-scope denominator,
2.5/97.5 percentiles. Wilson proportion intervals and case/turn p50/p95 come
from the unchanged v4 report. Case dependence is still a limitation; no new
family-aware uncertainty claim is made.

### Fixed system configurations

- **P:** repository `config/models.yaml` route `default`,
  `google/gemini-3-flash-preview` through OpenRouter, used for NLU and phrasing.
  This is the same primary route used by official v4. On the final v1.0.0 build,
  the configured fallback is `x-ai/grok-4.20`; retain its retry/timeout/provider
  settings and report actual fallback calls. Jev risk second opinion is OFF
  on the final build. No provider comparison or new default selection.
- **B1:** `execute_bound(..., system="B1", llm_client=None)` with the same
  scoped ledger/overlays, simulator, policy, confirmation, OTP, actions and
  readbacks. Deterministic mock/rules NLU and template wording; model cost $0.
- **Serving:** explicit loopback `aclara_app` DSN, loaded from ignored `.env`
  in memory; source FORCE RLS, promoted dataset/ownership verification and
  temporal-quality column. Local serving avoids workstation-to-Azure ledger
  hops. Remote provider and durable budget latency remain included; these
  timings are not deployed in-region latency measurements.
- **Scoring:** all-gold pass, in-scope SAR/attempted share, strict escalation,
  missed/unnecessary transfers, materially incorrect outcomes, every unsafe
  and forbidden predicate, required readbacks and handoff completeness. Do not
  substitute handoff presence for correct escalation. Failure IDs are retained
  in ignored aggregate results; no row text enters public reporting.

## Durable budget prepared now

Scope **`final-evaluation-v5`**, single run **`final-program-v5`**,
**$1.50 lifetime**, with the same reserve-before-call mechanism as v4.
Planning estimate for the one P pass: approximately **$0.25–$0.75** (the seen
100-case v4 regression cost $0.23745); new case lengths/fallbacks may differ.
The $1.50 cap is the hard stop, not a prediction or permission to start now.
Scope/run preparation uses insert-if-absent plus independent policy readback;
it never resets spend, changes an existing cap, closes old scopes or re-enables
a disabled breaker. Model retries and fallback share the same purse. Unknown
costs stay reserved and stop the worker.

Verified metadata-only preparation/readback:

```bash
V5_BUDGET_PREPARATION_APPROVED=1 .venv/bin/python -m scripts.v5_budget --prepare
.venv/bin/python -m scripts.v5_budget
```

Initial readback: **0 attempts, $0 known/charged, 0 v5 unknown costs**.
Conservative funding: **$15.76264898 prior + $1.50 v5 = $17.26264898 ≤ $18**.
The prior maximum retains 75 historical unknown reservations and unused funded
allowances. Paid use is not authorized by preparing the purse; it waits for the
suite-merged GO. Production's $1/UTC-day and provider-key limits remain unchanged.
Read back the live budget and provider balance before and after the future run;
do not treat this receipt as a cached launch-time gate.

## Commands AFTER the suite-merged GO only

Run from the repository root. Obtain the manifest SHA-256 from the suite owner's
release message, not by inspecting suite rows/tool. Copy only the separately
approved private binding artifact with mode 0600; its provenance checksum is
verified inside the authorized loader. Do not run the loader today.

```bash
umask 077
REPO="$PWD"
# Set this to the author's full 64-character MANIFEST.sha256 file hash:
: "${V5_MANIFEST_PIN:?Obtain the pinned manifest from the suite owner}"
test "$(git -C "$REPO" branch --show-current)" = main
test -z "$(git -C "$REPO" status --porcelain)"
test "$(git -C "$REPO" rev-parse HEAD)" = "$(git -C "$REPO" rev-parse origin/main)"
test -z "$(git -C "$REPO" diff --stat v1.0.0 HEAD -- src apps prompts config infra)"

# Stop/report if any runtime path differs. No deployment or release tag.
mkdir -m 700 -p artifacts/final-program-v5 artifacts/evaluation-v5-prep
.venv/bin/python -m scripts.v5_budget
.venv/bin/python -m scripts.v5_budget --credits before

# START ONCE. This wrapper obtains credentials in memory, checks pins and
# ownership, and refuses to replay an existing attempt's directory.
V5_SUITE_MERGED_GO=1 LLM_FINAL_RUN_STARTED=1 LLM_REAL_CALLS_APPROVED=1 \
  nohup .venv/bin/python -m scripts.v5_blind_evaluation start \
  --suite test-v5 \
  --bindings artifacts/evaluation-v5/customer-bindings.json \
  --manifest-pin "$V5_MANIFEST_PIN" \
  > artifacts/final-program-v5/worker.log 2>&1 < /dev/null &

# Periodic aggregate-only status and spend; no checkpoint/result row reads:
.venv/bin/python -m scripts.v5_blind_evaluation status \
  --suite test-v5 --manifest-pin "$V5_MANIFEST_PIN"
.venv/bin/python -m scripts.v5_budget

# Once COMPLETE (or after a stop), retain both budget and provider readbacks:
.venv/bin/python -m scripts.v5_budget
.venv/bin/python -m scripts.v5_budget --credits after
```

The worker saves mode-0600 checkpoints per case and `results.json/results.md`
under ignored `artifacts/final-program-v5/`. Watchdog: 15-minute progress stall,
three hours, budget or error. Exception output contains classes only. No
automatic resume/retry of an incomplete scenario: preserve artifacts and
report the sanitized failure. Only an owner-approved infrastructure recovery
before a decision may replay a case, with count and spend disclosed. Never
rerun completed cases or repair gold to improve the score.

## Preparation verification and pending work

Authored-only `LLM_PROVIDER=mock .venv/bin/pytest -q tests/test_v5_preparation.py`
checks approval before any Git/frozen read, cap arithmetic including retained
charges, and paired in-scope bootstrap behavior. Ruff checks the wrapper/budget
helper. These do not execute a v5 case or validate its material.

The v5 manifest, private bindings, schema compatibility, source ownership,
provider balance and full wrapper execution remain unverified until the GO.
Report results whatever they are, keep official v4 unchanged, and make no
product/prompt/config changes or result-informed reruns.
