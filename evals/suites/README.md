# Held-out suite authoring and freeze

`test/` is the immutable `heldout-e2e-v2` release, using scenario schema version 2.
See [the preregistered protocol](../../docs/evaluation/eval-protocol.md) for execution
semantics, metrics, thresholds, safety definitions and limitations. No B1/P test run
is performed by these authoring tools.

The four category YAML files are independently schema-valid suites whose disjoint
union contains 200 scenarios. Load all four for the full workload. `MANIFEST.sha256`
pins each release file; `provenance.json` additionally pins the protocol, schema,
templates and authoring tools. References identify fictional overlay entities and
privately selected test customers; source rows and bindings are never committed.
Private bindings are serialized in canonical persona-reference order. Membership,
ownership and the exact original binding checksum can be checked after materialization.

```bash
uv run --with jsonschema --no-sync python evals/suites/tools/validate_release.py
```

The lead's v2 fixture harness and exporter are merged. The full held-out release still
needs organizer bindings, richer overlays and fault adaptation; see the protocol's
adapter handoff. These authoring tools do not change or bypass the harness.

Authoring used these ordered steps (not commands to rerun against a frozen release):

1. `tools/author_test_v1.py`: instantiate explicitly labeled fictional templates from
   brief §9. It needs the privately extracted, hashed §9 rule table.
2. `tools/bind_test_customers.py`: select 200 unique SHA-256 test-bucket customers,
   excluding every matcher-benchmark customer; write only private bindings.
3. `tools/portuguese_authoring.py`: `generate`, `review`, then `review_protected`.
   Google generates PT; Anthropic cross-checks every opening/reply. The final pass
   protects merchant names against localization. The ledger reserves cost before
   requests and stops before the approved $3 cap. No raw responses or thinking are
   persisted. Existing matching batch files resume without new calls.
4. `tools/assemble_release.py`: check reviewed facts, schema, coverage and provenance
   in ignored staging. `--freeze` creates `test/` and refuses to overwrite it.
5. `tools/validate_release.py`: read back hashes and semantic invariants. Any later
   content or protocol change requires a new suite version. Revision 2 supersedes the
   local revision-1 freeze solely for merged-schema/status metadata and deterministic
   binding serialization; all 200 scenario bodies and gold labels are unchanged.

The customer selector is recorded in each case. A binding points to a real test-group
customer and owned product, but transaction/operational overlays are project-generated
and isolated per run. The suite measures controlled policy/robustness behavior, not
the natural organizer-ledger distribution. No organizer record is sent to OpenRouter.

Independent human double labeling of the selected 40 cases and fluent-human PT
validation remain pending. The model cross-check is not human validation. The separate
100-case repeat selection is fixed before any system outcomes are observed.
