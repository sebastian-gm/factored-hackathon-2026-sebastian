# Submission checklist — owner and release team

Working checklist, not a record of completed release actions. This pitch pass does
not authorize model spending, infrastructure changes, an email send or publication.
Keep access codes, passwords, private reports and recordings in approved private
storage outside Git. The judge-facing content is in [slides](slides.md) and the
[video script](video-script.md).

## Current release gate

- [ ] Handoff 12 lifted the merge freeze for Option A dev fixes. Complete its dev acceptance gate and wait for Sebastian before re-release. Latest deployed runtime: `07bccdc630e2b5eeb2dc746a7c3fe000718fd22c`, followed by documentation-only `3ed98c9`. Verify the actual recording revision separately. [Release evidence and abandoned-attempt disclosure](../status/progress-log.md).

## Timing and submission owner

- [ ] Sebastian confirms the exact cutoff and format from the official email or
  pinned organizer announcement. The [organizer FAQ](https://www.factored.ai/careers/ai-data-hackathon)
  is recorded in the brief as **October 5, 2026**, without a precise time/zone. The brief records
  ambiguous “midnight” wording; do not treat an interpretation as confirmation.
- [ ] Plan to send by the internal target **October 4, 2026, 18:00 COT (UTC−5)**.
  The brief's **22:00 COT** buffer is an internal latest target, not a verified
  organizer extension. Sources: [brief §§0, 2.3 and 17](../00-build-brief.md).
- [ ] Assign one sender and a backup; keep the deployed tool available through
  **October 16, 2026**, as required by [brief §2.3](../00-build-brief.md).

## Freeze the evidence before exporting the pitch

- [ ] Select the release candidate and verify CI. Record the source SHA, image
  digest, suite manifest, dataset/policy/matcher/prompt versions and actual provider
  model IDs in the release record. Preserve prior test-access history and diagnostic
  failures; do not silently replace them with later results.
- [ ] Run only the owner-approved final evaluation and model comparison. Populate
  slide 5 from aggregate exports, with safety counts/denominators, uncertainty,
  latency and measured cost per attempted conversation. Include failures, retries
  and fallbacks in cost accounting. Link the exact result files after they exist.
- [ ] Preserve the selected roles: Gemini 3 Flash default, Grok 4.20 failure fallback,
  Jev risk second opinion and second subjective judge, Claude Sonnet 5 frontier
  comparator. [Measured development comparison](../ml/model-comparison.md),
  [Jev evidence](../ml/typesafe-jev-comparison.md). Development NLU cost per case
  cannot be relabeled conversation cost. Keep `TODO(results)` only for final-run
  measurements. The AI lane's live latency, phrasing ablation and PT model review
  are separate development follow-ups, not final-suite result placeholders.
- [ ] Check every pitch number against its linked aggregate. If final evidence is
  still missing, submit an explicitly unfinished result; do not fill placeholders
  with mock results, list prices or estimates. Review language with human ES/PT
  reviewers and retain any pending-review limitation.

## Prepare judge access and rehearse the deployed product

- [ ] The release smoke verified the web-to-API hop, all three surfaces, and a handoff
  claim/resolve. Reverify the selected recording revision and connection. The current deployment permits the owner's IP; external judges are
  not yet covered by that boundary. Arrange explicitly approved judge access and
  test it from the judge's intended route. Do not broaden ingress to repair a proxy.
- [ ] Verify the separate access-code gate before describing it as implemented.
  Store the code and persona passwords privately; supply them only in the submission
  email through the owner's approved delivery process. No values in Git, slides,
  video, screenshots, CI output or public release notes.
- [ ] The deployed personas include two Ops and two customer roles; reset remains
  disabled. Staff APIs remain workspace-scoped. The recording helper must respect
  those server gates; it cannot grant a role or enable cloud reset. Local ops tests do not authorize changing cloud roles,
  reset or cross-customer access. Rehearse the real route and show any fallback.
- [ ] Rehearse the ES explanation, PT clarification/dispute, fraud/freeze/handoff,
  cancellation and refusal paths using only project-generated records. Verify the
  actual read-backs. A missing or failed path changes the pitch, not the evidence.

## Record and export

- [ ] Record from the deployed app. Read back its source SHA/image revision before
  recording and record that SHA alongside the final clip. If runtime or configuration
  changes, reverify the affected scenes and preserve the new release record.
- [ ] Keep narration near **250 words**, hook within **0:10**, live product on screen
  by **0:20**, and honest limits in the last **0:15**. These are Sebastian's pitch
  requirements; the video's **3:00 maximum** and the **six-slide** deliverable come
  from [brief §§16.3–16.4](../00-build-brief.md).
- [ ] Exclude passwords, OTP values, provider keys, organizer rows and model thinking
  from every frame. A labeled authentication transition may skip credential entry;
  never edit a failed action into a successful receipt. Keep raw captures private.
- [ ] Export only slide headlines, bullets and visuals; keep speaker notes separate.
  Rehearse and measure the final clip duration. Check audio, captions, readability,
  link permissions and the final limits segment on the exported files.

## Full-history secret/data review and repo-public flip

The [sandbox rule](../00-build-brief.md#23-deliverables-and-dates) keeps this working
repository private permanently. Prepare the owner-approved, sanitized submission
repository separately. **Do not flip the current sandbox or add another remote here.**
The public-flip task below applies only to the explicitly approved submission target.

- [ ] Inventory the candidate's complete history and all release branches/tags;
  confirm it is not a shallow checkout and all intended refs are present. Run a
  pinned Gitleaks version over full history, with no date range or new-findings-only
  baseline. Review configuration/allowlists so exclusions cannot hide secrets.
- [ ] Example command, **not executed by this pitch pass**; replace the path with
  the approved candidate, ensure `artifacts/` is ignored, and keep output private:

  ```bash
  gitleaks git "<approved-submission-repo>" \
    --log-opts="--all --full-history" --redact=100 \
    --report-format=json \
    --report-path="<approved-submission-repo>/artifacts/submission/gitleaks-history.json"
  ```

  The [Gitleaks documentation](https://github.com/gitleaks/gitleaks#usage) describes
  history selection and redaction. Record scanner version, config hash, refs, SHA,
  exit status and reviewed findings. Do not print the report or attach it publicly.
  Scanner flags shown here are settings, not measured results.
- [ ] Inspect organizer-data exposure across history, assets, releases, issues/PRs
  and Actions logs/artifacts as well. Secret scanning is not a row-data audit.
  Rotate any exposed credential and remediate before repeating the scan; deleting
  a current file alone does not clean its history. Run clean-clone reproduction
  and the repository data/secret checks on the release candidate.
- [ ] Owner reviews the exact repository, commit, scan evidence and publication
  scope, then explicitly authorizes publication. Perform the **repo-public flip**
  on that approved target through Settings → General → Danger Zone → Change visibility.
  Public visibility exposes code and Actions history/logs; review those consequences
  using [GitHub's visibility guide](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility).
- [ ] Read back public visibility and the published SHA, check the repository while
  signed out, and verify release/download links. Recheck branch protection, required
  checks and workflow permissions. Keep this private sandbox private.

## Submission email and receipt

- [ ] Confirm the recipient and format against the official instructions. The
  [brief §2.3](../00-build-brief.md) specifies `hackathon.admin@factored.ai`.
- [ ] Include team name/members/contact, a short Aclara description, the approved
  public repository URL and release tag/SHA, deployed tool URL, exported slides,
  video link, and concise judge steps for the ES/PT paths.
- [ ] Supply the access code, demo personas and passwords **only in the email**
  through the approved delivery process. Include simulated-OTP instructions and
  any approved access prerequisite; never include infrastructure or provider secrets.
- [ ] Test every attachment/link from outside the team's account, recheck the
  deployed login and record the final recording SHA. Sender reviews the completed
  package, sends before the internal target, then records timestamp and delivery
  confirmation privately. Do not mark submitted from a draft or an attempted send.

## Release record — references only, never secret values

| Item | Status / evidence reference |
| --- | --- |
| Confirmed organizer cutoff and source | TODO(release): owner confirmation |
| Approved public submission target | TODO(release): repository URL and authorization |
| Release / deployed / recording SHA | TODO(release): exact hashes and read-back |
| Final evaluation and model comparison | TODO(results): aggregate result paths |
| Gitleaks full-history scan and data review | TODO(release): private report reference and outcome |
| Judge access rehearsal | TODO(release): private verification reference |
| Final slide/video URLs and measured duration | TODO(release): exported artifacts |
| Submission email and delivery receipt | TODO(release): private confirmation |
