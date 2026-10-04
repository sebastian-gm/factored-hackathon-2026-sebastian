# Gate C — final publication, prepared only

**Not approved or executed.** October 3 approval covers v0.9.0 and Gates A/B.
Sebastian must give a separate final go for the exact source SHA, deployed SHA,
reviewed release notes, public repository and v1.0.0 publication after reviewing
the completed slides/video. Email remains his separately reviewed action.

Retain the original history and the private archived snapshot. No force push,
new remote or deletion. Disclose post-v4 changes; official v4 stays unchanged
and repeat outcomes are **0/30**.

## Prerequisites

- [ ] Freeze main merges for the short publication window; clean main equals
  origin/main and GitHub main. Work only in this repository; Git always `git -C`.
  Fetch and push origin must each point only to this approved GitHub repository.
  GitHub CLI API/Release requests also pin `github.com` explicitly.
- [ ] Fresh 0600 `artifacts/azure/jev-release.json`: main, API/web image
  tags/digests, three acceptance flags and Gates A/B. Only docs may advance main
  after deployment; v1.0.0 targets the image SHA.
  Prep scripts/tests merged after `edd3070` require a later final image release;
  do not weaken this gate to permit undeployed code.
- [ ] Latest **ci, safety and azure-access** on both main and the deployed SHA
  succeeded. Audit current mode-aware external access, login/profile isolation,
  staff revocation, $1/UTC-day cap and remaining $15 cumulative allowance.
- [ ] Refresh [public-release audit](public-release-audit.md) on exact main,
  all refs, PR/issue/review text, all available workflow logs and artifacts.
  Review current-tree scrub, organizer-file exclusions, password rotation and
  README-only clean-clone reproduction. Retain negative-control evidence.
  Gitleaks extends defaults with documented narrow exceptions and exits 0.
- [ ] Slides/video complete, correct figures, signed-out accessibility, ≤3-minute
  video; exclude credentials/organizer rows/private recordings. Historical
  email/host disclosure follows the October 1 decision; inspect new material.

Inputs/receipts: ignored `artifacts/`, 0700 directories/0600 files. No public attachments.

## Evidence interface

Prepare `artifacts/submission-day/publication-audit.json` after the privacy audit:

```text
sha: exact clean main SHA
verified_at: timezone-aware ISO timestamp, no more than 24 hours old
git_refs_sha256: submission_gate_c.digest(git for-each-ref lines)
github_inventory_sha256: submission_gate_c.inventory() after auditing GitHub
gitleaks_findings: 0
gitleaks_binary_sha256, gitleaks_config_sha256: verified executable/config hashes
current_tree_scrubbed, full_history_scanned, github_text_and_logs_scanned,
actions_artifacts_reviewed, password_rotation_verified, clean_clone_verified,
organizer_files_absent, historical_metadata_disclosure_approved: true
```

`inventory()` hashes metadata; it does not scan content. Pin it after the
separate content audit. Ref/review/workflow drift invalidates the receipt. Scan
frozen suites automatically only; never open rows or use them for tuning.

Write reviewed aggregate release notes to
`artifacts/submission-day/submission-release-notes.md`. After Sebastian's explicit
go, record `gate-c-approval.json`: `gate: "C"`, `approved_by: "Sebastian"`, `sha`,
`deployed_sha`, `approved_on` (current UTC date), `publish_repo: true`,
`tag_and_release: true`, and `release_notes_sha256`. The receipt records approval;
creating it does not grant approval. Never store judge credentials in these notes.

## One command, default plan

Run from this repository; replace placeholders with the verified values:

```bash
.venv/bin/python -m scripts.submission_gate_c \
  --deployed-sha <deployed-image-sha> \
  --audit-receipt artifacts/submission-day/publication-audit.json
```

Expected: `PLAN verified ... No changes made.` Read-only: no spend, mutation or email.

**Only after explicit Gate C go**, add:

```text
--execute
--approval artifacts/submission-day/gate-c-approval.json
--notes artifacts/submission-day/submission-release-notes.md
--gitleaks <checksum-verified-gitleaks-executable>
```

Execution scans history/notes, publishes, activates and reads back a no-bypass
main ruleset (PRs + strict checks/invariants/postgres/web), pushes annotated
v1.0.0 on the deployed SHA, creates its Release, and checks repo/README/tag/Release
with unauthenticated GitHub requests. No email is sent.
The Release uses a mode-0600 snapshot of the exact approved/scanned notes.

## Stops and owner verification

- [ ] Expect `Gate C publication and signed-out verification complete` and
  receipts under `artifacts/submission-day/gate-c-*`. Check repo/PRs/README/Release
  signed out and deployed login from an independent network.
- [ ] Protection failure restores privacy and stops. Downloads cannot be
  retracted. Inspect receipts, tell Sebastian and obtain a recovery decision.
- [ ] Partial publication/existing v1.0.0/drift/readback failure stops. Reconcile
  with Sebastian; never blindly rerun, overwrite tags or change history.
- [ ] Sebastian reviews/sends the [email checklist](submission-day-runbook.md#5-submission-email--owner-sends-after-gate-e):
  repo + deployed link + slides/video + exact SHA; credentials privately. Preserve
  delivery confirmation; publication alone is not submission.
