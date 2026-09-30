# Private submission snapshot — 2026-09-30

The owner-authorized snapshot is **private**, at
[sebastian-gm/factored-hackathon-2026-sebastian](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian),
commit **890110119ee7af2386c766dcf8a82f1a4aafc125**. The personal sandbox
remains private with only `origin`; no history rewrite or second remote.
Publication still requires Sebastian's explicit submission-day approval.

## Source mapping and exclusions

Source: **d23fa5afed2a799f8578a78ec323bf2b4864786f**. Export uses a fresh
one-commit history and `snapshot@example.invalid`, not private author/coauthor
metadata. 104 product files under `src/aclara`, `prompts`, `config` are
byte-identical. Operational URLs are parameters/placeholders. Private links, cloud
hostnames, workstation paths and content contacts are scrubbed.

480 source files exported; 22 frozen suite/authoring files withheld. Ignored
artifacts/lake/raw data, bindings, human sheets, provider output, credentials and
Terraform private inputs/state/plans are absent. Authored fixture CSVs remain.
This is not an equality audit against private organizer records.

Evaluation chronology, original SHAs, official v2/v3 failures and limitations
remain in docs. V3's post-freeze snippet exposure and partial judging are disclosed;
later seen-suite checks are development results. **V4 is pending.** The export SHA
is not claimed as the evaluated or deployed revision. Its own
`docs/submission/snapshot-provenance.md` records portable reproduction and boundaries.

## Verified locally and after push

- Exported-code file policy and compilation passed; authored mock B1 **32/32**.
  Private editable-install path was checked to ensure the export code executed.
- Official Gitleaks **8.30.1** archive SHA-256
  `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb`;
  binary SHA-256 `88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509`.
- Default rules, empty ignore file, no custom exclusions/baseline, inline allowances
  ignored, decode depth 5/archive depth 3, redacted private reports.
- Exact pushed tree directory scan: **4 findings / exit 1**, individually triaged
  false positives. Three are AST-verified test `idempotency_key` literals; one
  is Terraform's Key Vault secret **name** mapping, not a password value.
- Explicit `git -C <export> log --all --full-history --root --diff-merges=first-parent -p`
  streamed to Gitleaks: 3 matching idempotency findings. Directory scan covers
  the Terraform rule restricted by filename. No actionable secret detected;
  this is not a zero-finding scan or proof of absence.
- Post-push scan archived the exact remote-matching commit; zero matches for
  cloud hostnames, workstation paths or private sandbox links.
- GitHub confirms PRIVATE, expected SHA, fictional metadata, Actions OFF and
  zero Actions runs. Workflow files are retained; no minutes spent on the new repo.

## Remaining

Follow-up snapshot commit **5cc68a8** adds the four individually scoped scanner
exceptions and their documentation. Configured Gitleaks 8.30.1 directory and
full-history scans exit 0 with zero findings. Authored negative controls detect
two different credentials in the same paths, plus the same allowed value in a
different path. The default-only results above remain the original measurements;
no broad exclusion, data or secret was added. Follow-up **bcdebe0** corrects the
README's no-data path and adds a fixture-only local smoke/cache default; no product
paths change. Two fresh clones were verified at zero model cost: mock checks
**454 passed / 20 skips**, B1 **32/32**, disposable database **23/23** and browsers
**80 fixture + 12 live + 1 staff**. The corrected clone's exact README setup,
Compose readiness and authenticated fixture smoke passed. See
[clean-clone reproduction](clean-clone-reproduction.md) for timings and limitations.
Final snapshot **3dbfc1d69fbc2fc8cabf270e532fe492afc2cdaf** matches origin. Fresh exact-tree and full-history
Gitleaks scans exit 0; private-link/home-path/cloud-host patterns have zero matches.
All commit emails are fictional, Actions are disabled and visibility stays PRIVATE.
This remains an export of d23fa5a, not the newly deployed Insights product.

Full frozen-suite reproduction and export-SHA deployment are unverified, because
private evaluation releases are deliberately withheld. No public endpoint or
visibility was enabled. Refresh and re-audit the snapshot after final feature
freeze before requesting publication approval. Private receipts are ignored in
`artifacts/submission-snapshot/audit/`; never attach them or their raw values.
