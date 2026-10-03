# Independent label review — pending

The frozen `review-selection.json` identifies 40 cases (20%) for two independent
human labelers. The selection is fixed by category before any B1/P outcome is seen.
Each reviewer should use brief §9 and the fixture facts, without executing or reading
the policy implementation and without seeing the other reviewer's answers.

Private blank worksheets are prepared at
`artifacts/evaluation-authoring/label-review/reviewer-a.yaml` and `reviewer-b.yaml`.
They contain case facts and customer turns/replies with expected outcomes and gold
labels removed. Each person fills `reviewer`, `outcome`, `must_escalate`, `reason_codes`
and optional notes. Do not consult the frozen gold while doing the independent pass.

After both passes, report raw agreement and Cohen's κ separately for outcome and
must-escalate. Log disagreements and written-rule adjudications. If adjudication
changes a frozen label, produce a new suite version and manifest before final runs;
retain the old version and record any prior test accesses.

No human labels, agreement scores or fluent-human Portuguese review have been
collected yet. The Google/Anthropic text cross-check is separate language evidence
and must not be counted as a second human labeler.
