# Limitations

Aclara is a synthetic development service. Its current frozen mock diagnostic
**failed acceptance gates**. See the [corrected report](evaluation/heldout-run01.md),
[B1 aggregate](evaluation/heldout-run01-B1.json) and
[P/mock aggregate](evaluation/heldout-run01-P-mock.json). Engineering tests and the
latest frontend integration establish narrower properties than safe end-to-end
banking operation.

## Application and evaluation

- The runtime serves an authored ledger, simulated identity and simulated SMS OTP.
  Organizer gold/serving transactions are available locally but are not bound to
  chat. A minimal contract-allowed routing projection is separate from the ledger.
  No real bank action, refund or customer protection guarantee is provided.
- Dispute and card-freeze workflows now include scope/policy rechecks, fresh OTP,
  exact confirmation, persistence and read-back. Implementation coverage is not
  acceptance: the frozen diagnostic found six forbidden ESC-04 disputes per system,
  nine materially incorrect outcomes and incomplete required handoffs. Those policy
  failures were not observed authentication/step-up bypasses.
- Mock P fell back to B1. Both recorded SAR 67/193; there is no measured AI gain.
  B1's unreachable fault cases remain in the workload denominator. Corrected scores
  reuse saved observations; no system rerun or label/suite edits were made. Later
  staff packet/API additions are outside the evaluated implementation SHA.
- [Development provider comparison](ml/model-comparison.md) informed the selected
  Gemini default and Grok fallback; [Jev](ml/typesafe-jev-comparison.md) supports
  risk union and a second judge. Final acceptance remains pending. Development
  NLU timings/costs and deployment smoke are not full-conversation benchmarks.
  TODO(results): final real-model quality, latency, cost and variability.
- Held-out ES/mixed text is model-authored; PT was generated and cross-checked by a
  second vendor. Human dual labels, Spanish review, fluent PT review and catalog
  translation review remain pending. Model cross-checking is not human validation.
- Language/segment outcome gaps include unequal policy/category mixes and small
  cells. They do not isolate causal bias or establish parity. Detectors, lexical DLP,
  grounding checks and the deterministic handoff rubric have bounded coverage.
- A local frontend probe found B1 does not recognize every lost-card wording. Fix
  language coverage with independent development cases; do not tune on frozen test
  outputs. The frontend cannot override policy to compensate.

## Data and matcher

- Organizer rows, private traces and recollection cards stay outside Git/CI/public
  artifacts. Approved aggregates and numeric model artifacts do not authorize
  external processing of organizer field values.
- Matcher v1 evaluates synthetic normalized slots. Logistic regression had lower
  test expected cost; LightGBM made about four times fewer wrong proposals at lower
  proposal coverage. The pre-registered validation rule still selects LightGBM.
  See [trade-offs](tradeoffs.md) and the [model card](ml/model-card-charge-matcher.md).
  Neither result establishes human language performance.
- [Matcher v2](ml/model-card-charge-matcher-v2.md) was fitted on synthetic
  train/validation only. Nine human es-CL recollections were an OOD before/after
  check, not a tuning set or broad language validation. Both v1 and v2 are retained.
  Human Portuguese review remains pending; model cross-check is separate evidence.
- Silver is incremental by source object; gold rebuilds as a complete tested
  snapshot. Promotion and serving load have separate freshness timestamps. Cloud
  scheduling, live-source freshness and full regeneration comparison remain gaps.
- [DQ findings](data-quality-report.md) preserve null transcript durations with a
  warning and exclude unsafe complaint/product links and text after a field-level
  failure. Do not repair these by guessing or claim the delivered data is clean.
- The app-error/contact comparison is descriptive, with activity confounding and
  repeated customers. Accent does not justify routing. The supplied fraud-score
  step reflects generator structure; no independent fraud predictor was trained.
- Marketing/branch ingestion remains out of scope. The serving loader has fixture
  RLS/checksum/rollback evidence, not complete production serving authorization.

## Frontend, deployment and operations

- PR #17's live Agent Desk and Ops consume typed APIs for the current workspace.
  They are not a global staff queue. Trusted demo roles are not federated staff
  identity. Two cloud demo identities have Ops roles and two are customers; reset stays disabled. Local tests cannot widen those boundaries.
- Live Ops counts operations. SAR/unsafe stay null without gold labels; daily cost
  history and freshness SLA are absent. Explicit fixture mode alone displays
  illustrative results. The displayed dbt lineage is a static aggregate snapshot.
- Local browser tests cover authored fixtures; the private real-model release
  also verified deployed browser flows and the web-to-API hop. Reverify the recording
  revision. Owner-IP access excludes unapproved judges; the separate access-code
  gate is not implemented. [Release evidence](status/progress-log.md).
- Postgres persistence, RLS, restart and [local logical restore](ops-recovery.md) are
  tested. Azure PITR/regional DR, realistic-volume recovery, automatic retention,
  sustained load and on-call readiness are unverified. Scale-from-zero can delay
  first requests; see the [bounded diagnosis](azure-startup-diagnosis.md).
- PostgreSQL's approved Azure-services firewall exception allows sources across
  subscriptions. TLS and restricted roles do not replace private networking.
  Infrastructure alerts do not stop spending; durable Postgres model reservations enforce separate approved caps.
  A privileged owner can rewrite an unanchored audit chain.
- Proposed savings remain a [projection framework](evaluation/business-projection.md)
  with missing inputs. No production agent-hours, time-to-case or customer-outcome
  improvement is claimed. See [production gates and other applications](production-readiness.md).
