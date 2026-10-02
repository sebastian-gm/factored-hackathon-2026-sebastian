# Public-release readiness audit

**2026-10-01 owner decision supersedes the snapshot recommendation below.**
The original lab is now `factored-hackathon-2026-sebastian`, still private.
Sebastian accepts historical commit email and Azure hostname disclosure. The
former snapshot is privately archived as `factored-hackathon-2026-sebastian-snapshot-archive`.
A fresh full-history, PR/comment and Actions audit plus password rotation is
required before publication; the historical scan below does not satisfy it.

## October 2 original-repository readiness audit

The renamed original repository remains **private**. No visibility change,
history rewrite, organizer-data upload or new cloud resource was performed.
Sebastian's submission-day publication approval remains required. Historical
emails/cloud hosts are owner-accepted; concrete hosts and workstation paths are
removed from the current operational tree. The public judge link is added only
on submission day.

### Scope and scans actually run

- Initial frozen inventory: **547 reachable commits, 2,028 blobs, 60,966,843
  bytes**, largest blob 323,068 bytes. All 18 CSV paths are documented authored
  fixtures; no `.env`, private bindings, credentials, state/plan/tfvars, raw
  database or organizer delivery file was found in the reachable path inventory.
  Refreshed after the operator scrub commit: **550 commits / 2,040 blobs /
  61,353,588 bytes**, largest blob 326,076 bytes.
- Checksum-verified **Gitleaks 8.30.1**, default rules, all refs/full history/root
  and merge-parent differences. A patch-stream pass had 19 matches; the definitive
  native Git pass had **27** because filename-aware Terraform rules add eight
  matches. These are **seven release-SHA metadata occurrences, eight Key Vault
  secret-name mappings, and twelve authored idempotency-key occurrences**.
  No actionable credential detected. Do not call the default exit 1 a clean scan.
- `.gitleaks.toml` retains default rules and adds path-plus-exact-value/field
  exceptions for those inputs only. The configured native history scan exits
  **0 with zero findings**. Negative controls detect a different key/password
  in the allowed paths, an allowed test value in a different path and the release
  SHA in a different JSON field on the same path (four findings as expected).
- Refreshed **120 PR titles/bodies, one issue comment, zero inline comments/review
  bodies, all 599 available completed workflow-log archives** inspected automatically.
  Their separate default-rule Gitleaks scan exits **0**, with no owner/public
  IPv4 or signed/token URL detected. Repository Actions artifact inventory is
  **0**. No workflow deletion was necessary; none is claimed.
- Automatic exact-value comparison found **zero** matches for current Key Vault
  credentials or private subscription/tenant inputs in history/GitHub text after
  password rotation (seven values checked).
  No credential was printed or validated against another service. This is a
  detection result, not a proof of absence or raw-record equality comparison.

All Git invocations use `git -C`; the native scanner's process-local Git wrapper
enforces the same repository boundary. Raw scans/log archives stay in ignored
`artifacts/public-release-audit-2026-10-02/`, mode 0700/0600. No source excerpts,
keys, IP values, organizer row text, bindings or model thinking enter this report.
Frozen suite contents were processed by automatic scanners only, never opened
for semantic inspection or used for tuning. Scan boundaries are dated; new PRs,
commits or workflow runs must be included in the final submission-day scan.

### Current-tree scrub and operational hardening

Operator scripts resolve targets lazily from the explicitly selected sandbox or
private configuration. Imports/local fixture checks make no Azure call. The access
workflow obtains URLs from private repository variables. README/slides/progress
and evaluation/operator docs use portable paths or owner-supplied target placeholders.
Original history remains intact; the archived snapshot is retained privately.

Both Postgres passwords were rotated through Terraform's existing password
generators, Key Vault values and existing server. App SQL password was updated
from Key Vault without printing it. A same-image API revision loaded the new
credential; versionless managed references were restored and reconciled. TLS,
non-superuser/no-RLS-bypass/no-owner-membership and unscoped zero-row checks passed.
Authenticated BFF `me`, `config`, `transactions`, `ops/snapshot` all returned
**200**, the bank clock was available, and logout readback returned **401**.
These read-only checks made **zero model calls**. Resource shape/access is unchanged.

The owner-IP plus Azure-services PG firewall is retained. The consumption app's
dynamic egress has no demonstrated stable app-only allowlist; narrowing would risk
availability. The Azure-services sentinel admits other subscriptions and is **not
private networking**. TLS, strong rotated credentials, least-privilege runtime/RLS
remain required. VNet/private access remains future work in
[production readiness](../production-readiness.md).

Fresh README-only reproduction of original release `f5e128d` passed all 17 steps
in **724.10 s** with mock providers and no organizer data/cloud secrets; see
[reproduction evidence](clean-clone-reproduction.md#october-2-original-repository-clean-clone).
Branch protection remains prepared but unavailable on the private plan; apply it
after the explicit publication go. Publication and warm/judge activation are OFF.

## Historical September 30 audit and recommendations — superseded


**Decision: the private sandbox is not ready for a public mirror.** No actionable
credential leak was detected in the inspected Git history, but author/contact
metadata, deployment-specific locations and local paths need a publication
decision or scrub. Recommend an approved, cleaned snapshot in a separate
`factored-hackathon-2026-<team>` repository, with the honest evaluation chronology
retained in documentation. This audit authorizes no public release.

## Scope and evidence

The measured snapshot below predates the later integrated UX/v4-runner/submission
preparation changes. Those changes are not covered by its counts or secret-scan
claim; repeat the audit on the exact future sanitized export. The new Terraform
plan tests use explicitly fictional subscription/resource identifiers only.

Audit performed **2026-09-30 UTC / 2026-09-29 PDT**, with zero model/cloud spend.
Scanning and triage were local. No endpoint was probed, credential validated,
cloud resource changed, repository created, public remote configured or history
rewritten. The only authorized push is this audit-only PR to the existing private
origin, targeting `fix/post-v3-analysis`; the lead merges it.

| Boundary | Measured scope |
| --- | --- |
| Candidate target available locally | `6800ffd556716fbff2415175a9ef06333bcf8889` (`origin/fix/post-v3-analysis`), 473 tracked files |
| Worktree at scan start | `8026df72a3ffe5961f11e01112e061c0a24c9de5`, including the proposed README/projection refresh |
| Locally available main | `e12efc73be64f8355aa9f177f08a04337593616c` |
| History snapshot | Non-shallow; 165 local/remote-tracking refs, 94 distinct ref tips, 356 reachable commits; no tags |
| Complete content inventory | 1,315 distinct reachable blobs; 26,181,240 bytes; every reachable commit tree inventoried |
| Secret scan with merge diffs | 347 patch-bearing commits scanned; root and merge differences included; empty/no-difference commits produce no patch |
| Largest historical blob | 302,284 bytes; none over the repository's 512 KiB limit |

The snapshot covers **available local refs**, including branches that would not
belong in a public release. It is not a claim that remote-only/deleted/unreachable
objects, GitHub PR bodies, issues, Actions logs/artifacts, releases, deployment
images or ignored files were inspected. No fetch was used to expand scope.
Frozen v4 content was processed only by automatic detection/inventory; no v4 case
or authoring logic was opened for semantic inspection or used to tune the system.
Publication of frozen suites remains a separate lead decision.

Private evidence stays in ignored `artifacts/public-release-audit/`: frozen ref
inventory, redacted Gitleaks reports, value-free content inventories and triage.
The directory is mode 0700 and reports are mode 0600. They are **not PR attachments**
or public-release assets. Values, source records and model reasoning are absent
from this document.

## Secret-scan method and result

Used the official [Gitleaks v8.30.1 release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1),
downloaded into ignored `artifacts/tools/`. Before execution, the Linux x64 archive
was verified against the release's published SHA-256 checksum:

```text
551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
```

The verified binary reports `8.30.1`. Its SHA-256 is
`88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509`.
The minimal scan config extends the binary's embedded default rules, with no
repository-specific exclusions; its SHA-256 is
`27630a96d6c55755cc37620f3933d5cab94b1eb78a726a32e11212972525d76e`.
The repository config likewise only extends the default rules. The scan used an
empty ignore file, ignored inline `gitleaks:allow` comments, applied no baseline or
date cutoff, retained default decoding depth 5 and enabled archive depth 3. Built-in
Gitleaks rule allowlists still apply; a detector is not proof of absence.

The first `--all --full-history` pass detected three matches. The definitive pass
used **all 94 frozen tip hashes**, rather than moving branch names, with
`--full-history --root --diff-merges=first-parent`. That includes merge-introduced
changes and reproduces the available-history boundary. All repository Git commands
were run with `git -C <repo>`. The [Gitleaks usage documentation](https://github.com/gitleaks/gitleaks/tree/v8.30.1#usage)
describes the local Git scanner and redaction controls.

| Category | Definitive result | Triage |
| --- | --- | --- |
| `generic-api-key` | 12 findings across four commits, representing three distinct literals | False positives: authored `idempotency_key` request values in `tests/test_operational_store.py` and `tests/test_staff_api.py`; repeated by merges. These are replay-control test inputs, not authentication credentials. |
| Provider/cloud keys, private keys, credentialed connection strings, SAS tokens | No actionable finding | Supplemental byte-pattern review found no provider/access key, private-key block, signed Azure URL or credentialed DSN. No credential validity calls were made. |
| Other password-like literals | Two supplemental matches | A translated password field label in `apps/web/src/lib/messages.ts` and a deliberately wrong password in the negative-login test in `apps/web/tests/stories.spec.ts`; not deployed secrets. |

Gitleaks exited **1**, because the twelve findings remain in the report; it did not
produce a clean exit that can be described as “zero findings.” AST/source-context
triage verified every reported match is a literal test `idempotency_key`. Keep
that explanation, rather than broadly suppressing tests. If the later release
scan detects a real credential, stop, have the owner revoke/rotate it and sanitize
the publication candidate before rescanning. Nothing in this audit establishes a
credential that presently requires rotation.

## Personal, operational and organizer-data review

A separate value-free scanner inspected all reachable blobs and commit metadata.
It checked emails, IPv4 literals, contextual subscription/tenant UUIDs and Azure
resource paths, cloud hostnames, storage-bucket references, secret-like assignments,
private-key blocks, DSNs and signed URLs. It also inventoried file types/sizes and
searched for record-shaped JSON and customer/transaction identifiers in docs.
Counts below are distinct values across history, not occurrence counts.

| Category | Finding | Public-release treatment |
| --- | --- | --- |
| Email/identity metadata | Four distinct email addresses in author/committer/message metadata; three are non-placeholder/non-noreply under the scan classification | Treat these three as personal/contact metadata until owners consent. A history export must obtain consent or rewrite identifying author/committer/coauthor metadata and review names/message trailers. Values are retained only privately. |
| Emails in tracked content | One organizer submission contact in two files, and two example/test addresses in two files; no other email literal detected | Retain the organizer's submission contact only as supported by the [brief](../00-build-brief.md); retain explicitly fictional test/example addresses. Do not substitute private judge/persona contacts. |
| IPv4 allowlist values | No literal public IPv4 address detected; only loopback and wildcard bind/test constants | Retain generic bind/test constants. No owner/judge IP value was found in tracked history. Review external CI variables and private Terraform inputs separately. |
| Azure subscription/tenant/resource IDs | No literal subscription/tenant UUID or concrete `/subscriptions/.../resourceGroups/...` resource ID detected in blobs or commit messages | Keep Terraform references and variable names. Do not export state, plans, private tfvars or credentials; these were not tracked. |
| Key Vault values | No literal Key Vault credential/value detected; no vault URL literal detected | Environment lookups and secret-reference code are not secret values. This is a Git-content result, not a Key Vault/account audit. |
| Container Apps URLs | Four distinct URL literals in seven historical/current target files | Select at most the intended customer web demo URL for owner-approved publication; remove private API/preview/default operational targets. Locations below. |
| Other Azure service hostnames | Two distinct hostnames in three files | Parameterize the concrete registry/database names in `infra/README.md`, `scripts/azure_dev.py`, `scripts/azure_migrate_ops.py`; keep generic setup examples. Hostnames are infrastructure inventory, not credentials. |
| Local filesystem paths | Two distinct home-path prefixes across two historical files | Replace workstation-specific paths in `docs/evaluation/final-run-plan.md` and historical `docs/status/progress-log.md` with portable placeholders. |
| Organizer buckets/credentials | No organizer bucket URI, storage-bucket literal or credential detected | A bucket-shaped assignment in the historical v1 authoring tool is a language-allocation category, not a storage bucket. Retain source schemas/provenance, never private delivery locations or access material. |
| Organizer row-level data | No detected organizer row file or record-shaped JSON outside permitted fixtures; no customer/transaction identifier match in docs | All 18 CSV blob versions are confined to the authored incremental/ledger fixtures. Their [incremental provenance](../../tests/fixtures/incremental/README.md) and [ledger provenance](../../tests/fixtures/ledger/README.md) explicitly state they are fictional, not copied organizer rows. Aggregates/contracts/code are allowed; see limitations below. |
| Large/binary files | No blob over 512 KiB, no NUL-bearing binary blob, and no tracked database/archive/media binary detected | Four current SVGs are text assets. Keep allowed schemas, aggregates and fictional fixtures; never export ignored data, recordings or scan reports. |

**URL decision:** a customer web URL is suitable for the submission only after the
owner approves the exact public endpoint and confirms the intended access boundary.
A URL is not an access credential and must not be relied on as one. Do not publish
access codes, persona passwords, OTPs or URLs with credential/query tokens. The
existing [judge-access checklist](checklist.md#prepare-judge-access-and-rehearse-the-deployed-product)
still requires an approved external route. No ingress/access change was made or
tested here. API/preview URLs provide no necessary judge-facing benefit, so the
clean source should use configuration/placeholders for them.

Container Apps URL locations requiring the lead's selection/scrub:
`.github/workflows/azure-access.yml`, `README.md`, `docs/submission/slides.md`,
`scripts/azure_smoke.py`, `scripts/azure_llm_smoke.py`,
`scripts/serving_browser.py`, `docs/status/progress-log.md`.
The README finding is in the inspected target tree; the pending README refresh
uses owner-supplied access rather than embedding the deployed URL.

**Row-data limitation:** this was a tracked-history inventory, format/identifier
heuristic review and fixture-provenance check, not an equality comparison against
private organizer records. No `LOCAL_RAW_DIR`, ignored lake/artifact contents or
v4 cases were opened for that comparison. Free-text copying or identifiers outside
the tested patterns can escape detection. Accordingly, the result is “none
detected,” not proof that every historical byte is organizer-independent. The
release owner must resolve any uncertain file provenance before export, including
low-count aggregates and screenshots, without turning raw records into audit logs.

## Publication options

| Method | Benefit | Risk / work required |
| --- | --- | --- |
| History-preserving mirror | Original sequence and unchanged SHAs can show the genuine v1-to-v4 development process | A raw mirror includes every selected history/ref, author emails, old local paths and operational defaults, and can expose unintended/blind branches. The current mirror is not ready. Select release refs explicitly; obtain identity consent or sanitize history in an isolated export. Rewriting changes SHAs and invalidates existing tag signatures, so disclose the mapping and preserve evaluated-source provenance. Do not mirror all sandbox refs. |
| Clean squashed snapshot **(recommended)** | Smaller disclosure surface; reviewed tracked tree only; no inherited author emails or deleted historical files | Loses browsable development history. Preserve a sanitized chronology, original evaluation counts/gate failures and seen-suite disclosures, prompt/model hashes, and the mapping from private evaluated SHAs to the clean release tree. Never imply the new snapshot SHA itself was evaluated when the measured revision differs. |

Both methods keep this sandbox private permanently. Neither transfers GitHub PRs,
issues or Actions artifacts automatically; exporting those separately would need
its own review. The public repository should use the required name above. An
existing MIT license is tracked, but it does not grant rights to organizer records,
external media or people's identities. The team name, export method, final source
revision and exact public scope remain owner decisions.

For a snapshot, carry the reproducible implementation and allowed synthetic data,
plus sanitized [official v2](../evaluation/final-v2-error-analysis.md) and
[official v3](../evaluation/final-v3-results.md) reports and the subsequent
development disclosures. Preserve failures and v3's transition to development
data. V4 remains pending; this audit supplies no v4 result. If history is required
by the organizers, use a reviewed, scoped history export instead of changing the
visibility of `bank-agent-lab` or adding a public remote to it.

## Concrete scrub and release gate

These are proposed lead/owner actions, **not changes performed by this audit**.

1. Choose the final approved release tree and method. Do not export all local
   branches/tags, worktree administration, ignored files, or blind suite material
   merely because it is reachable. Keep suite release/provenance decisions with
   the lead; no v4 authoring/content review is delegated here.
2. For a history export, consent or rewrite all three non-placeholder contact
   addresses, associated identities and identifying message trailers; scan messages
   as well as patches. Review annotated-tag identity metadata if tags are added.
   Preserve an explicit original-to-sanitized SHA mapping. A snapshot uses an
   approved team identity and imports no private history.
3. Resolve the seven Container Apps URL locations above. Keep only the approved
   customer demo link; replace API/preview defaults with environment inputs. Scrub
   the two concrete Azure service hostnames from the three named files. Review
   nearby resource names and Azure access-workflow defaults for the same purpose.
4. Replace local home paths in the final-run plan and progress history. Review
   private-sandbox PR/repository links throughout docs: provide public evidence
   files or clearly labeled private-source provenance, not inaccessible judge links.
   Preserve the factual chronology when shortening internal progress/brief notes.
5. Export only contracts, aggregate reports, code and documented authored fixtures.
   Exclude `.env`, all raw/lake/artifact data, Terraform state/tfvars/plans, private
   reports, human sheets, recordings/screenshots with credentials or records,
   provider responses/thinking and organizer access locations. Check the exported
   tree, not only `.gitignore`; an ignored file can still be manually copied.
6. Rerun the checksum-pinned secret and value-free data/privacy scans on the exact
   sanitized candidate; triage every finding. Run mock reproduction and file policy
   locally, and require green remote CI for the lead's PR into `main`. Do not spend
   model/cloud money or change ingress as part of publication preparation.
7. Owner reviews the final repository name, tree/history, scan outcome, evidence
   links and disclosure scope, then explicitly approves creation/publication.
   Only after approval should a separate submission repository be created and
   populated. Read back its visibility and SHA and check signed-out access; this
   private sandbox stays private. GitHub's [visibility guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility)
   explains the consequences of exposing repository content and history.

Completed here: local scanning, private triage, publication comparison and this
audit-only document. Not completed: scrubbing, raw-record equality review, external
artifact/log review, final-source selection, clean-clone reproduction or public
release. The PR must remain unmerged for lead review; no release authorization is
implied by approving an audit document.
