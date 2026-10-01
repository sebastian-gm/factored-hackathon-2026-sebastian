# Post-v4 product and instrumentation fixes

**These changes are not reflected in official v4 numbers.** The evaluated release
remains `1ec9c2f`, with product behavior frozen at `92994d9`. The
[official results](final-v4-results.md), including both failed safety gates and
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
  [safety analysis](final-v4-safety-analysis.md).
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
