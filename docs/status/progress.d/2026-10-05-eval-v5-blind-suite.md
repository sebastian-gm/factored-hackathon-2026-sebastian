# Eval v5 blind suite — 2026-10-05

## Completed (verified)

- Built `evals/suites/tools/author_test_v5.py`, which compiles four blind
  kit-format family files. It imports no product, policy or scorer code.
  Ruff check and format pass, and full pytest passes locally.
- `check-families` on the final author files after the gold review: 0 findings,
  51 families, 100/100 schema-valid cases.
- `stage`, `freeze` and `verify` passed. The suite is
  `heldout-e2e-v5-blind-20261005` and `MANIFEST.sha256` hashes to
  `f6e7b15bcef3766b4933c1eb2ef95eb3118bdf46ffef6a9de6d2c1709a3ccaef`.
- Preflight results:
  - Composition: categories 35/20/20/25; languages 48 ES, 48 PT, 4 mixed.
  - 100 unique test-bucket customers; inventory overlap 0.
  - 11,837 excluded customers: v4's hash-identical set plus v4's 100.
  - Prior wording/template overlap with v1, v3 and v4: 0. Contract lint
    findings: 0. Native IDs in the release: 0.
  - `verify` re-rendered all gold identically from the frozen family files.
- The private binding and audit are mode 0600 and stay outside Git.
- The v4 harness loader accepts the release with both 30-case selections.
  Spend $0, no system or model runs.
- Added the [authoring kit](../../evaluation/v5-authoring-kit.md) as a byte copy,
  plus the [v5 protocol](../../evaluation/eval-protocol-v5.md).

## Done but not verified

- Remote CI on the PR.

## Next / blocked

- The v5 P/B1 run needs the owner's separate go. Its label is "independent v5
  check on the final build, post-fixes". Official v4 is unchanged.
