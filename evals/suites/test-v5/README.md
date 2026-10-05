# Independent held-out v5 — blind author material

100 cases; 35 normal, 20 ambiguous/unsupported, 20 human-required,
25 security/robustness. Languages: 48 ES, 48 PT, 4 mixed. Four separate Claude
author agents wrote the families blind, one per category, from the v5 authoring
kit (docs/evaluation/v5-authoring-kit.md), ADR-0015 and the written conversation
contract only. Human and second-vendor language review are pending.

**Implementers (lead, AI, fix author): do not open scenario rows, family files,
subset IDs, or the authoring tool.** Review this aggregate metadata only. No
B1/P runs or paid provider calls were made during authoring.

The four `families-*.json` files are the authors' source of truth, frozen here
byte-for-byte. `evals/suites/tools/author_test_v5.py` compiles them without
policy, runtime or scorer imports; `verify` re-renders every case from these
files and requires byte-equal gold. Its contract lint reported zero findings;
the lint reports only and never edits gold. A customer who cannot tell charges
apart never has a reply that chooses, confirms or describes a charge.

The schema wire version remains 2; the evaluation release version is 5. Actual
es-CL dialect metadata uses the schema's `other` encoding. The charge overlays
are entirely fictional. Authenticated test-split customer/product bindings are
outside Git at `artifacts/evaluation-v5/customer-bindings.json`, created with
mode 0600. Exclusions are every inventory v4 excluded (hash-identical inputs)
plus all 100 v4 customers. Wording and template IDs have zero normalized exact
overlap with v1, v3 and v4.

MANIFEST.sha256 freezes every release file except itself. Do not edit frozen
bytes or regenerate gold to fit execution. Structural-only preflight does not
certify behavioral success.

The fixed 30-case repeat and dual-judge subsets were selected before execution
(two mixed cases, then 11/6/6/7 by category split evenly ES/PT). They are
protected alongside scenarios; no case IDs belong in PR text or logs.

Only a later explicit owner go may authorize a run. See
docs/evaluation/eval-protocol-v5.md for the aggregate-only protocol.
