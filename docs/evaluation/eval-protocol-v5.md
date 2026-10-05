# Independent v5 held-out protocol

**Label for every v5 result: "independent v5 check on the final build, post-fixes".**
Official v4 remains the headline result. Its numbers, suite and bindings are
unchanged. V5 is a supplementary check of the unchanged `v1.0.0` product code.
That code contains fixes informed by earlier v2, v3 and v4 results. V5 is the
first suite written after those fixes.

## Blind authorship

Four separate Claude (Anthropic) author agents each wrote one category, without
seeing each other's work. Each author read **only**
[the v5 authoring kit](v5-authoring-kit.md), the
[written conversation contract](../../contracts/interfaces/conversation-policy-v3.md)
and, optionally, [ADR-0015](../adr/0015-post-v2-conversation-and-policy-contract.md).
Authors could not open `src/`, `evals/`, `tests/`, `prompts/`, `docs/evaluation/`,
`artifacts/` (except their own output file) or Git history. They ran no product
and no model. Each author chose the facts, wrote the messages, picked one kit
path and wrote the minimum reason set required by the contract.

A separate toolsmith agent wrote `evals/suites/tools/author_test_v5.py` from the
kit and the v4 tool, without reading product code. It compiles the four family
files into schema-valid scenarios. It imports no policy, runtime or scorer code;
the action vocabulary is parsed from `evals/observations.py` without importing it.
A final gold-review pass against the written contract came before the freeze.

## Contract lint and structural checks

`check-families` checks kit keys, enums and types, and the 35/20/20/25 category
and 48 ES / 48 PT / 4 mixed language counts. It also checks contract consistency:

- Filing and cancellation require eligible facts.
- Age, amount band, unsupported type, data/FX defects and stale Pending each
  require their contract reasons.
- Fraud requires `AUTH-02` and no OTP.
- Refusal and failure paths use their exact reason sets.
- Every reason is a contract code.

The lint only reports. It never changes gold. The frozen families had zero
findings. A customer who cannot tell two charges apart never gets a reply that
chooses, confirms or describes a charge. This fixes the v4.039/040 fixture
contradiction.

Exact matches of normalized wording or template IDs with v1, v3 and v4 count as
overlap; there is none. All 100 authenticated identities are new test-split
customers. Exclusions cover everything v4 excluded, with hash-identical
inventories, plus all 100 v4 customers. Bindings stay outside Git in a 0600
file. All charge facts are fictional overlays.

## Freeze

`evals/suites/test-v5/` holds the scenarios, the four family files
(byte-for-byte), provenance, the structural preflight, the pre-registered
30-case subsets and a README. `MANIFEST.sha256` hashes every file except itself.
`verify` re-checks the manifest, the pinned inputs and the private binding. It
also re-renders all 100 cases from the frozen family files, and they must match
exactly. Frozen bytes are never edited, and gold is never regenerated to fit a
result.

## Planned run

The run starts only after the owner's go. It is a single P pass and a single B1
pass over all 100 cases, with no repeats and no judges. Both use unchanged
`v1.0.0` product code, v4's loader, simulator, scorer and strict gates, and a
capped, reserve-before-call budget. The results report the label above. They
contain aggregates only: no case text, case IDs or rows in public documents.
No product, prompt or config change follows from v5 results under this label.

## Limitations

- Wording and gold were written by models. Human and second-vendor review are
  pending.
- Authors, the toolsmith and the product's development assistants share a model
  family.
- ES/PT pairs share one design each. Uncertainty estimates must account for that
  family clustering.
- The lint is a structural cross-check. It does not prove that the labels are
  correct.
- Fallback replies are tool-written templates.
- Fictional overlays test the contract, not the realism of organizer data.
