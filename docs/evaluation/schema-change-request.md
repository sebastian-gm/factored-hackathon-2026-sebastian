# Held-out suite interface request

The original frozen v1 schema allows only id, es/pt language, scripted turns, and a
single expected outcome. Sebastian approved an additive v2 in a separate two-file
PR, preserving v1. [PR #9](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/9)
contains that schema and its validation test. Sebastian also confirmed that the
brief's §9 written rule table is the gold-label source; no policy catalog is needed.

An additive, separately versioned v2 should retain v1 compatibility and represent:

- Suite version/id, dataset version, written-policy version/hash, and provenance.
- Scenario id, category, language (es/pt/mixed/other), dialect, and persona reference
  to a deterministic test-only customer selector; no organizer rows in Git.
- Bank clock; fictional overlay fixture; named faults with trigger points; isolation
  by run id. Private source bindings remain under ignored artifacts.
- Initial utterance; customer knowledge; reply table keyed by ResponsePlan.type;
  ordered reply sequences for repeated questions/attacks; explicit default reply;
  semantic target choice and boolean confirmation/cancellation; maximum turns.
- Gold outcome from all nine §15.2 outcomes, target reference or null, required and
  forbidden actions, must-escalate, rule/reason codes, routing/priority, required
  handoff fields, and must-not-disclose record references.
- Authoring origin and per-language generation/review metadata. Gold labels are
  authored independently from written rules, never by importing/executing policy.

PR #9 was merged after the lead added backward-compatible export/runtime support;
the snapshot check is now expected to pass. The lead's reactive fixture harness was
also merged in PR #10, while organizer bindings and richer overlay/fault adaptation
remain explicit follow-up work. The suite is validated with JSON Schema independently
of system outcomes; human label review and end-to-end execution remain separate gates.
