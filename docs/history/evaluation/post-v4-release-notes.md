# Post-v4 product and instrumentation fixes

**These changes are not reflected in official v4 numbers.** The evaluated release
remains `1ec9c2f`, with product behavior frozen at `92994d9`. The
[official results](../../evaluation/final-v4-results.md), including both failed safety gates and
**0/30** repeat flips, remain unchanged. McNemar p=0.004 compares majority pass
on that repeated subset. No held-out replay, rescoring or improved evaluation
claim accompanies this release.

## Owner-approved scope

- Preserve concurrent `ESC-01` on early fraud/legal handoffs. The existing reason
  union is retained; the deterministic request detector accepts a bounded single
  insertion/deletion/substitution on staff nouns after a positive ES/PT contact
  request, plus the common `kiero` spelling. Negations, third-party mentions and
  merchant mentions are negative authored controls. This is not unrestricted
  fuzzy matching or a guarantee for every misspelling.
- Distinguish uncertainty about recognizing/authorizing a described charge from
  inability to select it. Remove only recognition-memory clauses from the broad
  uncertainty test. Later uncertainty about amount, date or which charge remains
  active. An accepted scoped MATCH proposal following a denial survives this
  guard; policy, fresh OTP and separate confirmation still govern filing.
- Emit `verify_readback` for status reports only after the existing fresh,
  independently scoped, post-commit case read succeeds. Compare the complete
  typed public receipt and owner, then persist the event in the originating
  execution record. A failed read returns 503 and emits no verification event.
- Correct the evaluator's existing-case alias measurement: successful independent
  authenticated reads retain the precise fixture reference and the generic
  existing/new-case receipt alias. This is an instrumentation correction, not a
  revision of saved v4 metrics. Frozen fixtures, gold and simulator replies are
  unchanged, including the contradictory choice behavior discussed in the
  [safety analysis](../../evaluation/final-v4-safety-analysis.md).
- Integrate AI commit `ca8fe2c`: offline v4 human review, version-specific page and
  autosave, unchanged wording validation and descriptive agreement tooling. No
  scores are invented; human ratings and fluent-human PT review remain pending.

## Validation boundary

All repair regressions use authored ES/PT fixtures and mock providers. Tests cover
concurrent reasons, misspellings and negative controls, accepted MATCH after a
prior clarification and denial, persistent status events, rejected readbacks,
precise existing-case aliases and local Postgres restart/session isolation.
No model comparison or paid development gate is rerun. Release smokes have their
own $0.10 durable purse and do not enter official evaluation results.

The README now records the official v4 figures and an executable no-organizer-data
path. That path uses an explicitly selected authored ledger and mock models;
omitted private suites cannot be treated as passing. The private submission
snapshot retains the chronological disclosures and excludes organizer rows,
bindings, human sheets, provider traces and frozen evaluation releases.

Local/remote CI and the deployed release SHA are recorded in the latest
[progress log](../status/progress-log.md). Publication, submission-day warm
replicas and judge access remain off pending separate owner approval.

## Delivered release — 2026-10-01 UTC

Merged combined PR #101 after its single candidate CI/safety run passed. Delivered
main is **b8c13059e1332f974279ffd61ecb2e6b19c35876**; automatic main CI
36888960606 and safety 36888960892 passed. Azure runs both SHA-tagged images:

- API: `sha256:c6232ec6adc4568eeeb1125065c0dc7fcfdbbe10f76aad98bb4a4f73a24d972f`
- Web: `sha256:9f7ebee079a92fd3dc127db893d9668ca861051f8a700563702d7660e7e2bd85`

Reviewed Terraform plan/apply changed only the two existing apps' images/release
identity and the approved temporary smoke budget binding: **0 added, 2 changed,
0 destroyed**. Min replicas remain 0, max 1; the owner-IP allowlist, app login,
internal API, TLS/managed identity and submission-day modes are unchanged. Live
East US 2 price readback estimated **$34.63/month**, below the $40 stop threshold;
this is an estimate, not an invoice or an approved warm-replica change.

`scripts.azure_verify`, the capped `scripts.azure_llm_smoke` exercise with authored
post-v4 assertions, `scripts.serving_browser --target azure`, GET-only story-hint
checks and azure-access run **36890629027** passed. The smoke independently checked
the persisted status `verify_readback` and concurrent fraud/legal/human reasons.
All three story hints were available. Nine model calls were valid, with no fallback
or unknown costs; charged smoke cost **$0.00827475** under its $0.10 lifetime purse.
The standard mock-only `scripts.azure_smoke` refuses a real-provider deployment
and was not run or claimed as passing; the capped real and browser gates cover
this release. The new ignored `jev-release.json` has all three release flags true.

All-scope charged/reserved cumulative exposure is **$7.61889734**. Including
retained reserves, remaining dev/comparison allowances, the full v4 cap and
remaining smoke allowances, the conservative maximum is **$11.90208298 ≤ $12**.
This broader accounting includes $0.048878 of older scopes outside the legacy
release helper's named-scope list. No reserve was discarded. Official v4 cost
**$0.54532659** and its historical completion cumulative **$7.56174459** are unchanged.

Local candidate verification: **834 Python passed / 23 optional skips**, strict
mypy on 93 files, Ruff/hooks/compile/contracts; **31 disposable Postgres** tests,
**124 browser** checks (111 fixture + 12 live API + 1 staff), and B1 dev **32/32**
on both baseline and reactive authored suites. The initial sandbox TestClient run
stalled and was stopped; the complete host-capable rerun is the passing evidence.
SHA-256 checks confirmed **855 official/frozen/input files unchanged**, with no
held-out replay or rescoring. These are repair/release checks, not v4 improvements.
