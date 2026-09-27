# Frozen-suite adapter implementation

The frozen release and preregistered protocol are unchanged. This implementation is
validated using independent authored fixtures in `tests/test_bound_evaluation.py`.
Run `.venv/bin/python -m evals.heldout` for input-only preflight; add `--run` to execute
B1 and P/mock once on all 200 cases and P/mock twice more on the frozen 100-case
subset. A clean committed implementation is required. No paid provider is selected.

## Private inputs and isolation

Four explicitly authorized private artifacts were copied from the linked Data/ML
worktree into ignored `artifacts/`: canonical customer bindings and three matcher
splits. Source/destination checksums matched. The binding matches the frozen SHA.
For future runs, preflight requires the promoted organizer Postgres serving dataset at the frozen dataset version. Non-owner forced RLS verifies all 200 distinct test-partition identities, product ownership, country/segment and zero overlap with the matcher splits. There is no raw-source or authored-ledger fallback in the held-out entry point.

Every base-ledger read passes through customer RLS and the 120-day UTC window. Declared fictional transaction/product/customer/FX/state overlays are applied only in isolated evaluation memory and never written to bank tables. Organizer transactions remain additional searchable records; overlay handles remain stable. This changes the adapter's source composition relative to run 01 and will be reported explicitly in any subsequent comparison. Run 01 is preserved as measured.

Operational writes remain isolated in memory per case for fault injection; durable Postgres behavior is tested separately. Identifiers stay private. Attack placeholders remain synthetic canaries and contain no organizer PII. Missing serving ownership fails preflight. Independent `test_serving_api.py` exercises a complete authored dev case with both serving rows and overlays.

`evals.access.access` logs started/completed/failed reads and hashes in ignored mode-0600 `artifacts/heldout/access-ledger.jsonl`. The wrapper includes preflight and execution. **No additional full diagnostic has run during handoff 08; the one remaining pre-final diagnostic remains reserved.** No frozen gold bytes were changed.

Preflight found **12 redundant USD amounts on fictional distractors** inconsistent
with their amount × FX rate. Frozen inputs and labels are preserved. The adapter
retains a diagnostic and marks that record's USD fact inconsistent in the trusted
policy context; it cannot support an automatic action if selected. This decision
was made from input integrity checks before any system execution, not test outcomes.

## Execution and scoring

Fault aliases map to the declared boundary, including persistent outages. Every
fault must fire; an unreachable fault is not executed and remains in the original
workload denominator. B1 has no model call, so a model outage can be unreachable.
System inputs contain no gold labels or hidden risk scores. Required/forbidden
predicates are checked explicitly; unknown predicates are adapter errors.

Card actions use real step-up, live proposal and confirmation endpoints. Independent
reads verify cases, card state and handoffs. Revoked sessions regain no HTTP access;
the test observer can verify the already-committed security packet in its trusted
scope. Scheduled attacks run before terminal acceptance unless the session ends.

Scoring separates authorized writes followed by failed readback from unauthorized
writes. All required handoff fields must exist. Semantic disclosure checks inspect
outputs, not attack inputs; structured transaction facts are compared with the
scoped projection. This deterministic detector is not a complete semantic verifier
of arbitrary prose. Human label review and fluent Portuguese review remain pending.

Reports retain workload/executed sample sizes, Wilson intervals, safety gates,
opportunity denominators, 10,000 resamples with seed 20261001, explicit routing gold,
language/dialect/country/segment slices and repeated-subset comparisons. Per-case
traces and identifiers remain in private mode-0600 artifacts. Commit only aggregate
reports. Every execution records implementation SHA, manifest hash and versions
before the first case. Never tune this release from held-out outcomes.
